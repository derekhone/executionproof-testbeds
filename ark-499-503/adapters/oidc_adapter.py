"""
adapters/oidc_adapter.py — ARK-501 REAL external OIDC/IAM identity boundary.

Stands up a REAL identity provider and a REAL protected resource server, both
over HTTP on loopback (Flask + werkzeug):

  * Issuer      : a real RSA-2048 keypair; issues real RS256-signed JWTs with
                  sub / roles / exp / jti claims.
  * JWKS        : GET /.well-known/jwks.json publishes the issuer's PUBLIC key
                  in JWK form (real key distribution).
  * Resource    : POST /protected requires an Authorization: Bearer <jwt>. The
                  resource server INDEPENDENTLY re-validates the token
                  (RS256 signature via the published key, exp, jti-revocation,
                  and the 'deploy' role) and only then records a real access
                  grant to an on-disk access log. It trusts nothing the caller
                  asserts.

The enforcement layer's identity pre-check (validate_token) mirrors the same
checks so a rejected token never even reaches the resource server. The resource
server's independent re-validation is the audit ground-truth: a leak is any
access-log entry that does not correspond to an ALLOW ProofRecord.

Explicitly NOT claimed: this is NOT Okta / Azure AD / Auth0 / any commercial
IdP, and NOT a certified OIDC deployment. It is a real, self-hosted RS256
issuer + JWKS + bearer-protected resource used to test the identity boundary.
"""
import os
import json
import time
import base64
import shutil
import socket
import logging
import threading

logging.getLogger("werkzeug").setLevel(logging.ERROR)

import jwt  # PyJWT
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from flask import Flask, jsonify, request
from werkzeug.serving import make_server

ROOT = "/tmp/ark501_oidc"
ACCESS_LOG = os.path.join(ROOT, "access_log.jsonl")
ISSUER = "https://issuer.remnantfieldworks.local"
KID = "rf-ark501-key-1"
REQUIRED_ROLE = "deploy"


def _b64url_uint(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class OIDCAdapter:
    tool_id = "T4"                       # privileged resource access
    _TOOL_NAME = "privileged_resource_access"

    def __init__(self):
        self._blocked = 0
        self._down = False
        self._revoked = set()            # revoked jti values (shared issuer+server)
        self._server = None
        self._thread = None
        self.port = None
        self.base_url = None
        # primary issuer keypair
        self._priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._pub = self._priv.public_key()
        # a DIFFERENT ("foreign") keypair for the forged-signature arm
        self._foreign_priv = rsa.generate_private_key(public_exponent=65537,
                                                       key_size=2048)
        self._priv_pem = self._priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        self._pub_pem = self._pub.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        self._foreign_priv_pem = self._foreign_priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())

    # ---- JWK for the public key ------------------------------------------
    def _jwk(self):
        nums = self._pub.public_numbers()
        return {"kty": "RSA", "use": "sig", "alg": "RS256", "kid": KID,
                "n": _b64url_uint(nums.n), "e": _b64url_uint(nums.e)}

    # ---- server lifecycle -------------------------------------------------
    def setup(self):
        shutil.rmtree(ROOT, ignore_errors=True)
        os.makedirs(ROOT)
        app = Flask("ark501_oidc")

        @app.get("/health")
        def health():
            return jsonify({"status": "ok"})

        @app.get("/.well-known/jwks.json")
        def jwks():
            return jsonify({"keys": [self._jwk()]})

        @app.post("/protected")
        def protected():
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"granted": False,
                                "reason": "missing bearer token"}), 401
            token = auth[len("Bearer "):]
            ok, info, reason = self._server_validate(token)
            if not ok:
                return jsonify({"granted": False, "reason": reason}), 403
            entry = {"ts": time.time(), "sub": info["sub"], "jti": info["jti"],
                     "roles": info["roles"], "resource": "prod-secret-store"}
            with open(ACCESS_LOG, "a") as fh:
                fh.write(json.dumps(entry) + "\n")
            return jsonify({"granted": True, "resource_id": "prod-secret-store",
                            "jti": info["jti"]}), 200

        # bind a free port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        self._server = make_server("127.0.0.1", self.port, app, threaded=True)
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)
        self._thread.start()
        # wait until healthy
        for _ in range(50):
            try:
                if requests.get(self.base_url + "/health", timeout=1).ok:
                    break
            except requests.RequestException:
                time.sleep(0.1)

    def teardown(self):
        if self._server is not None:
            self._server.shutdown()

    # ---- token issuance / revocation -------------------------------------
    def issue_token(self, sub, roles, ttl_seconds=300, jti=None, forged=False,
                    issued_offset=0):
        now = int(time.time())
        jti = jti or f"jti-{sub}-{now}-{os.urandom(3).hex()}"
        claims = {"iss": ISSUER, "sub": sub, "roles": roles,
                  "iat": now + issued_offset, "nbf": now + issued_offset,
                  "exp": now + issued_offset + ttl_seconds, "jti": jti}
        key = self._foreign_priv_pem if forged else self._priv_pem
        token = jwt.encode(claims, key, algorithm="RS256",
                           headers={"kid": KID})
        return token, jti

    def revoke_jti(self, jti):
        self._revoked.add(jti)

    # ---- validation (shared logic; server + enforcement pre-check) -------
    def _decode(self, token):
        # fetch the published key via JWKS (real key distribution round-trip)
        jwks = requests.get(self.base_url + "/.well-known/jwks.json",
                            timeout=2).json()
        signing_key = jwt.PyJWKSet.from_dict(jwks).keys[0]
        return jwt.decode(token, signing_key.key, algorithms=["RS256"],
                          issuer=ISSUER,
                          options={"require": ["exp", "iat", "jti", "sub"]})

    def _server_validate(self, token):
        try:
            claims = self._decode(token)
        except jwt.ExpiredSignatureError:
            return False, None, "token expired"
        except jwt.InvalidSignatureError:
            return False, None, "invalid signature (untrusted key)"
        except jwt.InvalidTokenError as exc:
            return False, None, f"invalid token: {exc}"
        if claims["jti"] in self._revoked:
            return False, None, "token revoked (jti in revocation list)"
        if REQUIRED_ROLE not in claims.get("roles", []):
            return False, None, f"missing required role '{REQUIRED_ROLE}'"
        return True, {"sub": claims["sub"], "jti": claims["jti"],
                      "roles": claims["roles"], "kid": KID}, "valid"

    def validate_token(self, token, required_role=REQUIRED_ROLE):
        """Enforcement-layer identity pre-check (mirrors server validation)."""
        if not token:
            return False, {"kid": None, "jti": None}, "no token presented"
        ok, info, reason = self._server_validate(token)
        if ok:
            return True, info, "valid"
        return False, {"kid": KID}, reason

    # ---- adapter contract -------------------------------------------------
    def tool_name(self, tool_id):
        return self._TOOL_NAME

    def healthy(self):
        if self._down:
            return False
        try:
            return requests.get(self.base_url + "/health", timeout=1).ok
        except requests.RequestException:
            return False

    def perform(self, action):
        """ALLOW side effect: call the REAL protected resource with the bearer
        token. The resource server independently re-validates before granting."""
        token = action.get("access_token")
        resp = requests.post(self.base_url + "/protected",
                             headers={"Authorization": f"Bearer {token}"},
                             timeout=3)
        body = resp.json()
        return ("access-" + os.urandom(8).hex(),
                {"http_status": resp.status_code, "granted": body.get("granted"),
                 "resource_id": body.get("resource_id")})

    def record_blocked(self, action, decision):
        self._blocked += 1
        return f"oidc-blocked-{decision}-{self._blocked}"

    # ---- independent inspection ------------------------------------------
    def access_count(self):
        if not os.path.exists(ACCESS_LOG):
            return 0
        with open(ACCESS_LOG) as fh:
            return sum(1 for line in fh if line.strip())

    def access_entries(self):
        if not os.path.exists(ACCESS_LOG):
            return []
        with open(ACCESS_LOG) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def probe_protected(self, token):
        """Directly probe the resource server (independent of the gate)."""
        resp = requests.post(self.base_url + "/protected",
                             headers={"Authorization": f"Bearer {token}"},
                             timeout=3)
        return resp.status_code, resp.json()

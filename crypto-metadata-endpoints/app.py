"""
app.py — EXPERIMENTAL software-simulation Flask server for the ExecutionProof
crypto metadata endpoints requested in GitHub issue #25.

    *** EXPERIMENTAL / SOFTWARE SIMULATION / TESTBED ONLY ***
    *** NOT a live AWS KMS / HSM deployment. No FIPS/certified claims. ***

Routes (all GET, read-only):
  /                           -> index describing the simulation + routes
  /health                     -> {"status": "ok", "simulation": true}
  /v2/version                 -> API/algorithm version metadata (simulated)
  /v2/crypto-manifest         -> full crypto metadata manifest (simulated)
  /v2/crypto/pq-public-key    -> active + retired ML-DSA-65 public keys (simulated)

This server reproduces the metadata contract documented in
docs/crypto-api-metadata-contract.md so routing, schema shape, and the
verification tooling can be exercised locally. It performs NO signing and
touches NO hardware. See metadata.py and README.md for the full disclaimer.

Run (local only):
    python crypto-metadata-endpoints/app.py            # default 127.0.0.1:8088
    python crypto-metadata-endpoints/app.py --port 9000
"""
from __future__ import annotations

import argparse

from flask import Flask, jsonify

import metadata as md

app = Flask(__name__)
# Keep JSON key order stable and readable for a metadata/testbed service.
app.config["JSON_SORT_KEYS"] = False


@app.after_request
def _mark_simulation(resp):
    """Stamp every response with a header making the simulation boundary
    visible even to clients that only inspect headers."""
    resp.headers["X-ExecutionProof-Simulation"] = "true"
    resp.headers["X-ExecutionProof-Experimental"] = "true"
    return resp


@app.route("/")
def index():
    return jsonify(
        {
            "service": "ExecutionProof crypto metadata endpoints (SIMULATION)",
            "experimental": True,
            "simulation": True,
            "notice": md.SIMULATION_NOTICE,
            "routes": sorted(list(md.ENDPOINTS.keys()) + ["/health"]),
            "issue": "https://github.com/derekhone/executionproof-testbeds/issues/25",
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "simulation": True, "experimental": True})


@app.route("/v2/version")
def version():
    return jsonify(md.build_version())


@app.route("/v2/crypto-manifest")
def crypto_manifest():
    return jsonify(md.build_crypto_manifest())


@app.route("/v2/crypto/pq-public-key")
def pq_public_key():
    return jsonify(md.build_pq_public_key())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EXPERIMENTAL simulation of ExecutionProof crypto metadata "
        "endpoints (issue #25). Not a live AWS KMS/HSM deployment."
    )
    parser.add_argument("--host", default="127.0.0.1",
                        help="bind host (default: 127.0.0.1, loopback only)")
    parser.add_argument("--port", type=int, default=8088,
                        help="bind port (default: 8088)")
    args = parser.parse_args()

    print("=" * 72)
    print("ExecutionProof crypto metadata endpoints — EXPERIMENTAL SIMULATION")
    print("NOT live AWS KMS / HSM. No FIPS/certified claims. Testbed only.")
    print(f"Serving simulated {md.API_VERSION} endpoints on "
          f"http://{args.host}:{args.port}")
    print("=" * 72)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()

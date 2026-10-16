"""
generate_snapshots.py — write static JSON snapshots of the simulated crypto
metadata endpoints into ./snapshots/.

    *** EXPERIMENTAL / SOFTWARE SIMULATION / TESTBED ONLY ***

These snapshots let the documented contract be reviewed (and the endpoint shapes
consumed) without running the Flask server, e.g. if a static-hosting path is used
to route /v2/* metadata. They are generated artifacts and carry the same
simulation disclaimers as the live-server responses.
"""
from __future__ import annotations

import json
import os

import metadata as md

_HERE = os.path.dirname(os.path.abspath(__file__))
_SNAP_DIR = os.path.join(_HERE, "snapshots")

# route path -> snapshot filename
_FILES = {
    "/v2/version": "v2_version.json",
    "/v2/crypto-manifest": "v2_crypto-manifest.json",
    "/v2/crypto/pq-public-key": "v2_crypto_pq-public-key.json",
}


def main() -> None:
    os.makedirs(_SNAP_DIR, exist_ok=True)
    index = {
        "experimental": True,
        "simulation": True,
        "notice": md.SIMULATION_NOTICE,
        "snapshots": {},
    }
    for route, fname in _FILES.items():
        payload = md.ENDPOINTS[route]()
        out_path = os.path.join(_SNAP_DIR, fname)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
        index["snapshots"][route] = {
            "file": fname,
            "content_sha256_stable": md.payload_sha256(payload),
        }
        print(f"wrote {out_path}")

    with open(os.path.join(_SNAP_DIR, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)
        fh.write("\n")
    print(f"wrote {os.path.join(_SNAP_DIR, 'index.json')}")


if __name__ == "__main__":
    main()

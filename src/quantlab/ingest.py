"""Download data and store it as an untouched RAW snapshot.

Rules:
* The bytes we receive are written exactly as received.
* Every snapshot gets its own file (timestamp + hash in the name). A file is
  never overwritten: opening with mode "xb" fails if the file already exists.
* Files are made read-only, and each snapshot is logged in a manifest CSV.

Yahoo Finance is an UNOFFICIAL, personal-use-only source whose history is
revised between requests (see docs/04). It is used here for limited test pulls
only and is not suitable as a basis for reliable long-term research.
"""
from __future__ import annotations

import csv
import hashlib
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_FIELDS = ["pulled_at_utc", "source", "symbol", "interval", "range",
                   "path", "sha256", "bytes"]


def fetch_yahoo_raw(symbol: str, interval: str = "5m", rng: str = "60d") -> bytes:
    """Download the raw JSON bytes from Yahoo's public chart endpoint."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?interval={interval}&range={rng}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def save_raw_snapshot(raw: bytes, *, source: str, symbol: str, interval: str,
                      rng: str, raw_dir: Path, manifest_path: Path,
                      now: datetime | None = None) -> Path:
    """Write `raw` as a new read-only file and record it in the manifest.

    Raises FileExistsError rather than ever replacing an existing file.
    """
    now = now or datetime.now(timezone.utc)
    sha = hashlib.sha256(raw).hexdigest()
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    folder = Path(raw_dir) / source / symbol
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{stamp}_{interval}_{rng}_{sha[:12]}.json"

    with open(path, "xb") as f:          # "x" = create, fail if it exists
        f.write(raw)
    os.chmod(path, 0o444)                # read-only for everyone

    manifest_path = Path(manifest_path)
    is_new = not manifest_path.exists()
    with open(manifest_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "pulled_at_utc": now.isoformat(), "source": source, "symbol": symbol,
            "interval": interval, "range": rng, "path": str(path),
            "sha256": sha, "bytes": len(raw),
        })
    return path


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

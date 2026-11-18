"""Verify every frozen SHA-256 manifest under outputs/ without needing `shasum` (works on macOS, Linux and CI).

    python scripts/verify_manifests.py            # exit 0 = every listed file matches, 1 = a mismatch or a missing file

A manifest line is `<sha256>  <path relative to the repository root>`. Any changed or missing file is reported and fails the check."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifests = sorted((ROOT / "outputs").rglob("*.sha256"))
    bad, files = 0, 0
    for m in manifests:
        for line in m.read_text().splitlines():
            if not line.strip():
                continue
            h, _, rel = line.partition("  ")
            p = ROOT / rel.strip()
            files += 1
            if not p.exists():
                print(f"MISSING   {rel}   (listed in {m.relative_to(ROOT)})")
                bad += 1
            elif hashlib.sha256(p.read_bytes()).hexdigest() != h:
                print(f"MISMATCH  {rel}   (listed in {m.relative_to(ROOT)})")
                bad += 1
    print(f"{len(manifests)} manifests, {files} file entries, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

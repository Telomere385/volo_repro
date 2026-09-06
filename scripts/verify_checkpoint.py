"""Compare downloaded checkpoint files against public GCS object sizes."""
import json
from pathlib import Path
import gcsfs

root = Path(__file__).resolve().parents[1]
prefix = "openpi-assets-simeval/pi05_droid_jointpos"
fs = gcsfs.GCSFileSystem(token="anon")
objects = fs.find(prefix, detail=True)
bad = []
total = 0
count = 0
for name, info in objects.items():
    if info["type"] != "file":
        continue
    count += 1
    total += info["size"]
    path = root / "cache/openpi" / name
    if not path.is_file() or path.stat().st_size != info["size"]:
        bad.append(name)
report = {"objects": count, "bytes": total, "missing_or_wrong_size": bad,
          "verification": "public GCS object sizes; not cryptographic hashes"}
(root / "results/checkpoint-integrity-current.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
assert count > 0 and not bad, "Incomplete checkpoint"

import hashlib
import json
import sys
from pathlib import Path

game = Path(sys.argv[1])
print("== game dir files ==")
for p in sorted(game.rglob("*")):
    if p.is_file():
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"  {p.name:<28} {p.stat().st_size:>8}B  sha256:{sha}")
m = game / "ra2forge_install.json"
if m.is_file():
    data = json.loads(m.read_text(encoding="utf-8"))
    print("== manifest ra2forge_install.json ==")
    print(f"  package: {data.get('package')}")
    print(f"  version: {data.get('version')}  installed_at: {data.get('installed_at')}")
    for e in data.get("files", []):
        print(f"  entry: {e.get('name'):<18} action={e.get('action'):<9} "
              f"backup={e.get('backup')} original_absent={e.get('original_absent')} "
              f"sha256={str(e.get('sha256'))[:16]}")
    if "removed_orphans" in data:
        print(f"  removed_orphans: {data['removed_orphans']}")
else:
    print("== manifest: (none) ==")

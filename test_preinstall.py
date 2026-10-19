import sys
sys.path.insert(0, 'D:/Project/ra2-campaign-forge')
from ra2forge.install import preinstall_plan
import json
from pathlib import Path

def default_serializer(obj):
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} not serializable")

try:
    plan = preinstall_plan('out/demo_package/Example Operation', 'ra2youli')
    print(json.dumps(plan, ensure_ascii=False, indent=2, default=default_serializer))
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
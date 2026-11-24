import json
from pathlib import Path
root=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd")
d=json.loads((Path(r"D:\Project\ra2-campaign-forge\demo_campaign.json")).read_text(encoding="utf-8-sig"))
p=root/"sandbox"/"compat_design.json"
p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
print(d["campaign"]["name"], len(d["missions"]))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd\ra2forge_patched_v11")))
from ra2forge import mapselmd as ms
design={"package":{"id":"org.ra2forge.w34probe"},"campaign":{"name":"MS Probe","side":"soviet","id":"RA2F1"}}
missions=[{"name":"MS01"},{"name":"MS02"},{"name":"MS03"}]
chain=["MS02.MAP","MS03.MAP",""]
data,rep=ms.build_mapselmd(design,missions,chain)
print("report",rep)
Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd\sandbox\probe_out.ini").write_bytes(data)
txt=data.decode("latin-1")
print("--- tail ---")
print("\n".join(txt.split("\r\n")[-40:]))
print("--- faction ---")
for line in txt.split("\r\n"):
    if line.strip().startswith(("8=","9=","10=","[Nod]","1=","2=","7=")): print(repr(line))

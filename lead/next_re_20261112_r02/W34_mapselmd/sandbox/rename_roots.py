from pathlib import Path
p=Path(r"regress_dlc_v11.py")
s=p.read_text(encoding="utf-8")
print("W30_ROOT occurrences before:",s.count("W30_ROOT"))
s=s.replace("W30_ROOT", "W34_ROOT")
print("W30_ROOT occurrences after :",s.count("W30_ROOT"))
s=s.replace('W34_ROOT_NAME = "W30_csf_capability"','W34_ROOT_NAME = "W34_mapselmd"')
s=s.replace("W30 regression summary (regress_dlc_v10.py)","W34 regression summary (regress_dlc_v11.py)")
p.write_text(s,encoding="utf-8")

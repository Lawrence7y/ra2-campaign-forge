from pathlib import Path
b=Path(r"ra2forge_patched_v11\ra2forge\builder.py").read_bytes().split(b"\n")
for i in (807,808,809,810,811):
    print(i+1, repr(b[i]))

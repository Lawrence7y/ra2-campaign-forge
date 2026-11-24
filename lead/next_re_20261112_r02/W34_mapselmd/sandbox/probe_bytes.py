from pathlib import Path
p=Path(r"ra2forge_patched_v11\ra2forge\builder.py")
b=p.read_bytes()
print("crlf",b.count(b"\r\n"),"lf",b.count(b"\n"),"cr",b.count(b"\r"))
i=b.find(b"byte-for-byte identical to v0.9")
print(repr(b[i-80:i+80]))

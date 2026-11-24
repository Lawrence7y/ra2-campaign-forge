from pathlib import Path
import hashlib, difflib, json
REPO=Path(r"D:\Project\ra2-campaign-forge")
V10=REPO/"lead"/"next_re_20261112_r02"/"W30_csf_capability"/"ra2forge_patched_v10"/"ra2forge"
V11=Path(r"ra2forge_patched_v11"/"ra2forge").resolve() if False else Path(r"ra2forge_patched_v11\ra2forge").resolve()
out=Path(r".")
old=sorted(p.name for p in V10.glob("*.py"))
new=sorted(p.name for p in V11.glob("*.py"))
patch=[]
manifest=[]
for name in sorted(set(old)|set(new)):
    a=V10/name; b=V11/name
    if not a.is_file():
        data=b.read_bytes()
        patch.append(f"--- /dev/null\n+++ b/ra2forge_patched_v11/ra2forge/{name}\n"+"".join(difflib.unified_diff([],data.decode("utf-8").splitlines(True),fromfile="/dev/null",tofile=f"b/ra2forge_patched_v11/ra2forge/{name}",n=3)))
        manifest.append((name,"NEW",len(data),hashlib.sha256(data).hexdigest()))
    elif not b.is_file():
        manifest.append((name,"DELETED",0,""))
    else:
        da,db=a.read_bytes(),b.read_bytes()
        if da==db:
            manifest.append((name,"IDENTICAL",len(db),hashlib.sha256(db).hexdigest()))
        else:
            patch.append("".join(difflib.unified_diff(da.decode("utf-8").splitlines(True),db.decode("utf-8").splitlines(True),fromfile=f"a/ra2forge_patched_v10/ra2forge/{name}",tofile=f"b/ra2forge_patched_v11/ra2forge/{name}",n=3)))
            manifest.append((name,"MODIFIED",len(db),hashlib.sha256(db).hexdigest()))
# data resource
res=V11/"data"/"MAPSELMD.OFFICIAL.INI"
manifest.append(("data/MAPSELMD.OFFICIAL.INI","NEW",res.stat().st_size,hashlib.sha256(res.read_bytes()).hexdigest()))
(out/"PATCH_RELATIVE.diff").write_text("".join(patch),encoding="utf-8")
lines=["W34 v11 file manifest (sha256 of the delivered bytes)","","file | status | bytes | sha256"]
for n,s,z,h in manifest: lines.append(f"{n} | {s} | {z} | {h}")
(out/"V11_FILES.sha256.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("\n".join(f"{n:34s} {s:10s} {z:8d} {h[:16]}" for n,s,z,h in manifest))
print("patch bytes",(out/"PATCH_RELATIVE.diff").stat().st_size)

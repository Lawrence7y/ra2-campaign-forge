import sys, os, hashlib, shutil, subprocess
from pathlib import Path
ROOT=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd")
V11=ROOT/"ra2forge_patched_v11"
PKG=ROOT/"sandbox"/"compat"/"out_v11_mapselmd"/"Example Operation"
def run(args,cwd=V11):
    env=dict(os.environ); env["PYTHONDONTWRITEBYTECODE"]="1"; env["PYTHONIOENCODING"]="utf-8"
    p=subprocess.run([sys.executable,"-B","-X","utf8","-m","ra2forge",*args],cwd=str(cwd),env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
    return p.returncode,(p.stdout+p.stderr).strip()
def game(name):
    g=ROOT/"sandbox"/"install_probe"/name/"game"
    if g.parent.exists(): shutil.rmtree(g.parent)
    g.mkdir(parents=True)
    (g/"gamemd.exe").write_bytes(b"INERT - NEVER EXECUTED\n")
    (g/"RA2MD.INI").write_bytes(b"[General]\n")
    (g/"BATTLEMD.INI").write_bytes(b"[Battles]\n1=ALL1\n")
    (g/"USERMAP1.MAP").write_bytes(b"user\n")
    return g
mapsel=PKG/"MAPSELMD.INI"
original=b"; FOREIGN MAPSELMD.INI - another mod\r\n[GDI]\r\n1=ALL01\r\n"
# A: fresh install
g=game("A")
rc,out=run(["install","--package",str(PKG),"--game",str(g)])
print("A install exit",rc); print(out[:900])
print("A MAPSELMD.INI installed:",(g/"MAPSELMD.INI").read_bytes()==mapsel.read_bytes())
m=__import__("json").loads((g/"ra2forge_install.json").read_text(encoding="utf-8"))
print("A recorded:",[e["name"] for e in m["files"]])
rc,out=run(["verify","--game",str(g)]); print("A verify exit",rc, out.splitlines()[:6])
rc,out=run(["uninstall","--game",str(g)]); print("A uninstall exit",rc); print(out[:600])
print("A MAPSELMD.INI removed:",not (g/"MAPSELMD.INI").exists())
# B: install with a pre-existing OURS backup (restore path)
g=game("B")
(g/"MAPSELMD.INI").write_bytes(original)
rc,out=run(["install","--package",str(PKG),"--game",str(g)])
print("B install (foreign present) exit",rc); print(out[:800])
print("B foreign bytes intact:",(g/"MAPSELMD.INI").read_bytes()==original)
print("B no manifest:",not (g/"ra2forge_install.json").exists())
# C: same with --allow-content-conflict (must STILL refuse)
rc,out=run(["install","--package",str(PKG),"--game",str(g),"--allow-content-conflict"])
print("C install +allow exit",rc); print(out[:800])
print("C foreign bytes intact:",(g/"MAPSELMD.INI").read_bytes()==original)
# D: legit upgrade (ours recorded) -> allowed
g=game("D")
rc,out=run(["install","--package",str(PKG),"--game",str(g)]); print("D install1",rc)
rc,out=run(["install","--package",str(PKG),"--game",str(g)]); print("D install2 (upgrade)",rc); print(out[:400])
# E: uninstall restores original when one existed and was allowed explicitly? need no foreign file: simulate user original then force backup by pre-creating as ours? skip

import sys,os,json,shutil,subprocess
from pathlib import Path
ROOT=Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W34_mapselmd")
V11=ROOT/"ra2forge_patched_v11"
def run(args,cwd=V11):
    env=dict(os.environ); env["PYTHONDONTWRITEBYTECODE"]="1"; env["PYTHONIOENCODING"]="utf-8"
    p=subprocess.run([sys.executable,"-B","-X","utf8","-m","ra2forge",*args],cwd=str(cwd),env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
    return p.returncode,(p.stdout+p.stderr)
def design(names,name):
    return {"package":{"id":"org.ra2forge.w34-ms","version":"1.0"},"campaign":{"name":name,"description":"W34","side":"soviet","id":"RA2F1"},"missions":[{"name":n,"title":n,"briefing":"W34","theater":"TEMPERATE","size":[60,60],"player":{"house":"Russians"},"structures":[{"owner":"Russians","type":"NACNST","row":40,"col":30},{"owner":"Americans","type":"GACNST","row":15,"col":30,"tag":"hq"}],"objectives":[{"type":"destroy_building","structure_tag":"hq"}]} for n in names]}
sb=ROOT/"sandbox"/"ms5probe"
if sb.exists(): shutil.rmtree(sb)
sb.mkdir(parents=True)
for tag,names in (("P1",["MS01","MS02"]),("P2",["MS03","MS04"])):
    d=sb/f"d_{tag}.json"; d.write_text(json.dumps(design(names,tag)),encoding="utf-8")
    rc,out=run(["build","--design",str(d),"--out",str(sb/f"out_{tag}"),"--mapselmd"])
    print(tag,"build",rc,out.strip().splitlines()[-1] if out.strip() else "")
p1=sb/"out_P1"/"P1"; p2=sb/"out_P2"/"P2"
print("mapsel p1 sha",__import__("hashlib").sha256((p1/"MAPSELMD.INI").read_bytes()).hexdigest()[:12],"p2",__import__("hashlib").sha256((p2/"MAPSELMD.INI").read_bytes()).hexdigest()[:12])
g=sb/"game"; g.mkdir()
(g/"gamemd.exe").write_bytes(b"INERT\n"); (g/"RA2MD.INI").write_bytes(b"[General]\n"); (g/"BATTLEMD.INI").write_bytes(b"[Battles]\n1=ALL1\n"); (g/"USERMAP1.MAP").write_bytes(b"u\n")
rc,out=run(["install","--package",str(p1),"--game",str(g)]); print("install p1",rc)
m=json.loads((g/"ra2forge_install.json").read_text(encoding="utf-8"))
print("p1 mapsel entry",[e for e in m["files"] if e["name"]=="MAPSELMD.INI"])
orig=b"; ORIGINAL USER MAPSELMD.INI (pre-install)\r\n"
(g/"MAPSELMD.INI.ra2forge.bak").write_bytes(orig)
rc,out=run(["install","--package",str(p2),"--game",str(g)]); print("install p2 (upgrade)",rc, out[:400])
m=json.loads((g/"ra2forge_install.json").read_text(encoding="utf-8"))
print("p2 mapsel entry",[e for e in m["files"] if e["name"]=="MAPSELMD.INI"])
print("installed p2 bytes ok:",(g/"MAPSELMD.INI").read_bytes()==(p2/"MAPSELMD.INI").read_bytes())
rc,out=run(["uninstall","--game",str(g)]); print("uninstall",rc,out[:500])
print("after uninstall MAPSELMD.INI == orig:",(g/"MAPSELMD.INI").read_bytes()==orig if (g/"MAPSELMD.INI").exists() else "MISSING")
print("bak still there:",(g/"MAPSELMD.INI.ra2forge.bak").exists())

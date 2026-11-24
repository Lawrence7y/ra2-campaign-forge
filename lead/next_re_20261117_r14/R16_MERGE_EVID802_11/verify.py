# -*- coding: utf-8 -*-
"""Re-runnable verification for the R16-EVID802-11 (M95) merge.

Runs all 8 checks:
  (1) coverage byte-level reversibility
  (2) invariants 18,498 / {8:18498} / 1,654 / 1,648 / 6
  (3) only 11 rows' column 6 changed
  (4) new PROOF pointers isfile & non-empty
  (5) resolve.py rerun: R_OK 852->863, R_MISSING 0, R_TRACE_ONLY 802->791
  (6) PANEL reversibility
  (7) 达标未翻转 (nominal S15,S16,S17 / strict S17)
  (8) line endings not mixed

All tool outputs go under OUT (this dir), never the original script dirs.
"""
import hashlib, json, os, re, shutil, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
REPO = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
OUT = os.path.join(ROOT, "R16_MERGE_EVID802_11")
COV_BEFORE = os.path.join(OUT, "_coverage_before.tsv")
PANEL_BEFORE = os.path.join(OUT, "_panel_before.md")
DELTA = os.path.join(ROOT, "R16_EVID802_11", "coverage_delta.tsv")
RESOLVE_SRC = os.path.join(ROOT, "EVID_RESOLVE", "resolve.py")
STRICT_SRC = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

TARGETS = ["0045A560","0045A610","0053C6A0","005514B0","00551560","00557090",
           "00557140","006B1850","006B1900","006B8660","006B8710"]

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def readb(p):
    with open(p,"rb") as f: return f.read()
def split_lines(raw):
    parts = raw.split(b"\n")
    trail = raw.endswith(b"\n")
    if trail: parts = parts[:-1]
    return parts, trail

results = {}
def rec(k, ok, detail):
    results[k] = {"status": "PASS" if ok else "FAIL", "detail": detail}
    print("[%s] %s" % ("PASS" if ok else "FAIL", k))
    for d in detail: print("     " + d)

cov_before = readb(COV_BEFORE)
cov_after = readb(COV)
panel_before = readb(PANEL_BEFORE)
panel_after = readb(PANEL)

# ---------- (1) coverage byte-level reversibility ----------
bl, btrail = split_lines(cov_before)
al, atrail = split_lines(cov_after)
# map entry -> (line index, orig col6)
orig = {}
for i in range(1, len(bl)):
    f = bl[i].split(b"\t")
    if len(f)==8 and f[0].decode("ascii").upper() in TARGETS:
        orig[f[0].decode("ascii").upper()] = (i, f[5])
# reconstruct: after -> restore col6 back
recon_lines = al[:]  # copy
for e in TARGETS:
    i, oldc6 = orig[e]
    f = recon_lines[i].split(b"\t")
    assert len(f)==8
    f[5] = oldc6
    recon_lines[i] = b"\t".join(f)
recon = b"\n".join(recon_lines)
if atrail: recon += b"\n"
ok1 = (sha(recon)==sha(cov_before))
rec("1_coverage_byte_reversible", ok1, [
    "recon_sha=%s" % sha(recon), "before_sha=%s" % sha(cov_before),
    "after_sha=%s" % sha(cov_after),
    "11 rows col6 restored; all other bytes taken from after file"])

# ---------- (2) invariants ----------
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e,16)
    except ValueError: return e
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

def invariants(raw):
    lines,_ = split_lines(raw)
    data = lines[1:]
    col_dist = {}
    proved = atlas_in = atlas_out = 0
    for ln in data:
        if not ln.strip(): continue
        f = ln.split(b"\t")
        col_dist[len(f)] = col_dist.get(len(f),0)+1
        if len(f)>=5 and f[4] == "[已证]".encode("utf-8"):
            proved += 1
            if len(f)>=1:
                if ne(f[0].decode("utf-8","replace")) in atlas: atlas_in += 1
                else: atlas_out += 1
    return {"data_rows":len(data),"col_dist":col_dist,"proved":proved,
            "atlas_in":atlas_in,"atlas_out":atlas_out}
inv = invariants(cov_after)
exp = {"data_rows":18498,"col_dist":{8:18498},"proved":1654,"atlas_in":1648,"atlas_out":6}
ok2 = (inv["data_rows"]==exp["data_rows"] and inv["col_dist"]==exp["col_dist"] and
       inv["proved"]==exp["proved"] and inv["atlas_in"]==exp["atlas_in"] and
       inv["atlas_out"]==exp["atlas_out"])
rec("2_invariants", ok2, ["after_invariants=%s" % json.dumps(inv,ensure_ascii=False,default=str),
                          "expected=%s" % json.dumps(exp)])

# ---------- (3) only 11 rows col6 changed ----------
assert len(bl)==len(al)
diff_lines = []
for i in range(len(bl)):
    if bl[i]!=al[i]:
        bf = bl[i].split(b"\t"); af = al[i].split(b"\t")
        if len(bf)!=len(af):
            diff_lines.append((i+1,"COLCOUNT",len(bf),len(af)))
        else:
            changed_cols = [j for j in range(len(bf)) if bf[j]!=af[j]]
            diff_lines.append((i+1, bf[0].decode("ascii","replace"), changed_cols))
expected_lines = {1388,1389,4982,5286,5287,5387,5388,8877,8878,8983,8984}
got_lines = {d[0] for d in diff_lines}
ok3 = (got_lines==expected_lines and all(len(d)==3 and d[2]==[5] for d in diff_lines))
rec("3_only_11_rows_col6", ok3, ["diff_line_count=%d" % len(diff_lines),
    "diff_lines=%s" % sorted(got_lines),
    "all_diffs_only_col6=%s" % all(len(d)==3 and d[2]==[5] for d in diff_lines),
    "diff_detail=%s" % json.dumps(diff_lines,ensure_ascii=False,default=str)])

# ---------- (4) new pointer isfile & non-empty ----------
base_names = [("r14",ROOT),("lead",os.path.dirname(ROOT)),("repo",REPO)]
ptr_ok=[]
for e in TARGETS:
    # take from after file col6
    for i in range(1,len(al)):
        f = al[i].split(b"\t")
        if f[0].decode("ascii").upper()==e:
            c6 = f[5].decode("utf-8"); break
    segs = c6.split(";")
    proof = segs[1] if len(segs)>1 else ""
    rel = proof.replace("\\",os.sep).split("#",1)[0]
    hit=None
    for bn,base in base_names:
        p=os.path.join(base,rel)
        if os.path.isfile(p):
            hit=(bn,p,os.path.getsize(p)); break
    ptr_ok.append((e,proof,hit))
ok4 = all(h and h[2]>0 for _,_,h in ptr_ok)
rec("4_new_pointer_isfile_nonempty", ok4,
    ["%s -> %s (%s)" % (e,proof,("%s size=%d"%(h[0],h[2]) if h else "NOT FOUND")) for e,proof,h in ptr_ok])

# ---------- (5) resolve.py rerun (outputs to OUT only) ----------
resolve_copy = os.path.join(OUT,"resolve.py")
shutil.copyfile(RESOLVE_SRC, resolve_copy)
def run_resolve(cov_path, tag):
    out_dir = os.path.join(OUT,"_resolve_"+tag)
    os.makedirs(out_dir, exist_ok=True)
    r = subprocess.run([sys.executable, resolve_copy, "--repo",REPO,
                        "--coverage",cov_path,"--out",out_dir],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    sm = {}
    with open(os.path.join(out_dir,"summary.tsv"),encoding="utf-8") as f:
        next(f)
        for line in f:
            k,v,_ = line.rstrip("\n").split("\t")
            sm[k]=int(v)
    return sm, r.stdout
sm_before, out_before = run_resolve(COV_BEFORE,"before")
sm_after, out_after = run_resolve(COV,"after")
ok5 = (sm_before.get("R_OK")==852 and sm_before.get("R_MISSING")==0 and sm_before.get("R_TRACE_ONLY")==802 and
       sm_after.get("R_OK")==863 and sm_after.get("R_MISSING")==0 and sm_after.get("R_TRACE_ONLY")==791 and
       sm_after.get("R_EMPTY",0)==0)
rec("5_resolve_rerun", ok5, [
    "before: R_OK=%s R_MISSING=%s R_TRACE_ONLY=%s R_EMPTY=%s" % (sm_before.get("R_OK"),sm_before.get("R_MISSING"),sm_before.get("R_TRACE_ONLY"),sm_before.get("R_EMPTY")),
    "after : R_OK=%s R_MISSING=%s R_TRACE_ONLY=%s R_EMPTY=%s" % (sm_after.get("R_OK"),sm_after.get("R_MISSING"),sm_after.get("R_TRACE_ONLY"),sm_after.get("R_EMPTY")),
    "outputs: %s" % os.path.join(OUT,"_resolve_before"),
    "outputs: %s" % os.path.join(OUT,"_resolve_after")])

# ---------- (6) PANEL reversibility ----------
pl_before, ptrail_b = split_lines(panel_before)
pl_after, ptrail_a = split_lines(panel_after)
# find inserted block: 5 lines beginning with '> ✅ **M95 补记' in after
m95_idx = None
for i,l in enumerate(pl_after):
    if l.startswith("> ✅ **M95 补记".encode("utf-8")):
        m95_idx=i; break
ok6a = m95_idx is not None
if ok6a:
    # block is 5 lines; reconstruct by removing them
    recon_panel_lines = pl_after[:m95_idx] + pl_after[m95_idx+5:]
    recon_panel = b"\n".join(recon_panel_lines)
    if ptrail_a: recon_panel += b"\n"
    ok6 = (sha(recon_panel)==sha(panel_before))
    p6detail = ["inserted_at_1based_line=%d"%(m95_idx+1),
                "inserted_lines=%d"%5,
                "recon_sha=%s"%sha(recon_panel),"before_sha=%s"%sha(panel_before),
                "after_sha=%s"%sha(panel_after)]
else:
    ok6=False; p6detail=["M95 header not found in after PANEL"]
rec("6_panel_reversible", ok6, p6detail)

# ---------- (7) 达标未翻转 ----------
# copy strict_panel.py twice, redirect COV + OUT to this dir only
strict_src_text = open(STRICT_SRC, encoding="utf-8").read()
def make_strict(tag, cov_path):
    out_dir = os.path.join(OUT,"_strict_"+tag)
    os.makedirs(out_dir, exist_ok=True)
    txt = strict_src_text
    txt = re.sub(r'^COV\s*=.*$', 'COV  = r"%s"' % cov_path.replace("\\","\\\\"), txt, count=1, flags=re.M)
    txt = re.sub(r'^OUT\s*=.*$', 'OUT  = r"%s"' % out_dir.replace("\\","\\\\"), txt, count=1, flags=re.M)
    p = os.path.join(OUT,"_strict_panel_"+tag+".py")
    with open(p,"w",encoding="utf-8") as f: f.write(txt)
    r = subprocess.run([sys.executable,p],capture_output=True,text=True,encoding="utf-8",errors="replace")
    j = json.load(open(os.path.join(out_dir,"strict_panel.json"),encoding="utf-8"))
    nom = [x["S"] for x in j["rows"] if x["dod_nominal"]]
    st  = [x["S"] for x in j["rows"] if x["dod_strict"]]
    return nom, st, r.stdout
nom_b, st_b, so_b = make_strict("before", COV_BEFORE)
nom_a, st_a, so_a = make_strict("after", COV)
ok7 = (nom_b==["S15","S16","S17"] and st_b==["S17"] and nom_a==nom_b and st_a==st_b)
rec("7_dod_no_flip", ok7, ["before nominal=%s strict=%s"%(nom_b,st_b),
                           "after  nominal=%s strict=%s"%(nom_a,st_a),
                           "expected nominal=['S15','S16','S17'] strict=['S17']"])

# ---------- (8) line endings not mixed ----------
le = {}
for name, raw in [("coverage_before",cov_before),("coverage_after",cov_after),
                  ("panel_before",panel_before),("panel_after",panel_after)]:
    lf=raw.count(b"\n"); crlf=raw.count(b"\r\n"); cr=raw.count(b"\r")
    le[name]={"lf":lf,"crlf":crlf,"lone_cr":cr-crlf}
ok8 = all(v["crlf"]==0 and v["lone_cr"]==0 for v in le.values())
rec("8_line_endings_not_mixed", ok8, ["%s: %s"%(k,json.dumps(v)) for k,v in le.items()])

# ---------- summary ----------
all_pass = all(r["status"]=="PASS" for r in results.values())
summary = {
    "all_pass": all_pass,
    "results": results,
    "coverage": {"before_bytes":len(cov_before),"after_bytes":len(cov_after),
                 "before_sha":sha(cov_before),"after_sha":sha(cov_after)},
    "panel": {"before_bytes":len(panel_before),"after_bytes":len(panel_after),
              "before_sha":sha(panel_before),"after_sha":sha(panel_after)},
    "resolve": {"before":sm_before,"after":sm_after},
    "dod": {"before":{"nominal":nom_b,"strict":st_b},"after":{"nominal":nom_a,"strict":st_a}},
}
with open(os.path.join(OUT,"verify_result.json"),"w",encoding="utf-8") as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)
print("\nALL PASS" if all_pass else "\nSOME FAILED")
print(json.dumps(summary["coverage"],ensure_ascii=False))
print(json.dumps(summary["panel"],ensure_ascii=False))

# -*- coding: utf-8 -*-
"""R16-MERGE-EVID9 verify.py — re-runs all 6 verifications from card §4.
Read-only on coverage.tsv / PANEL.md. resolve.py & strict_panel.py outputs go to THIS dir only."""
import os, sys, hashlib, json, csv, shutil, subprocess, re
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RESOLVE = os.path.join(R14, "EVID_RESOLVE", "resolve.py")
STRICT = os.path.join(R14, "RULING_R15_20261119", "work", "strict_panel.py")
OUT = os.path.join(R14, "R16_MERGE_EVID9")
COV_BEFORE = os.path.join(OUT, "coverage_before.tsv")
PANEL_BEFORE = os.path.join(OUT, "PANEL_before.md")

BEFORE_COV_SHA = "325158B588636AA3AA170B74B6F4F0E7E5020CA0AC3960232C1DFEAD42CFCEA2"
BEFORE_PANEL_SHA = "ADDA58E2AC5DE3E330D47E352D21D59455A933EFC2410D5D347428148F7C8DEC"
NINE = ["004E0E80", "006B6EA0", "006B6FA0",
        "004DF320", "004DF3A0", "004DFB70", "004DFCB0", "004DFE00", "006F4960"]

results = {}
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def rec(name, ok, detail):
    results[name] = {"result": "PASS" if ok else "FAIL", "detail": detail}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

raw_before = open(COV_BEFORE, "rb").read()
raw_after = open(COV, "rb").read()
praw_before = open(PANEL_BEFORE, "rb").read()
praw_after = open(PANEL, "rb").read()

def split_lines(b): return b.split(b"\n")
def col6_of(ln): return ln.split(b"\t")[5]

# ---------- 1. byte-level restorability ----------
old6 = {}
new6 = {}
for ln in split_lines(raw_before)[1:]:
    c = ln.split(b"\t")
    if len(c) == 8 and c[0].decode("utf-8") in NINE:
        old6[c[0].decode("utf-8")] = c[5]
for ln in split_lines(raw_after)[1:]:
    c = ln.split(b"\t")
    if len(c) == 8 and c[0].decode("utf-8") in NINE:
        new6[c[0].decode("utf-8")] = c[5]
restored = split_lines(raw_after)
for i, ln in enumerate(restored):
    c = ln.split(b"\t")
    if len(c) == 8 and c[0].decode("utf-8") in NINE:
        c[5] = old6[c[0].decode("utf-8")]
        restored[i] = b"\t".join(c)
rebuilt = b"\n".join(restored)
ok1 = (sha(rebuilt) == sha(raw_before) == BEFORE_COV_SHA)
rec("1_coverage_byte_restore", ok1,
    f"rebuilt_sha={sha(rebuilt)[:8]} before_sha={sha(raw_before)[:8]} equal={rebuilt==raw_before}")

# ---------- 2. invariants ----------
def col_stats(b):
    lines = split_lines(b)
    rows = [ln.split(b"\t") for ln in lines[1:] if ln.strip()]
    from collections import Counter
    cd = Counter(len(c) for c in rows)
    proved = sum(1 for c in rows if len(c)==8 and c[4].decode("utf-8").strip()=="[已证]")
    return len(rows), dict(cd), proved

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

rows8 = [ln.split(b"\t") for ln in split_lines(raw_after)[1:] if ln.strip()]
data_rows = sum(1 for c in rows8 if len(c)==8)
col_dist = {}
for c in rows8: col_dist[len(c)] = col_dist.get(len(c),0)+1
proved_all = 0; proved_in = 0; proved_out = 0
for c in rows8:
    if len(c)==8 and c[4].decode("utf-8").strip()=="[已证]":
        proved_all += 1
        if ne(c[0].decode("utf-8")) in atlas: proved_in += 1
        else: proved_out += 1
nine_grades = {}
for c in rows8:
    if len(c)==8 and c[0].decode("utf-8") in NINE:
        nine_grades[c[0].decode("utf-8")] = c[4].decode("utf-8").strip()
ok2 = (data_rows==18498 and col_dist=={8:18498} and proved_all==1654
       and proved_in==1648 and proved_out==6
       and len(nine_grades)==9 and all(g=="[已证]" for g in nine_grades.values()))
rec("2_invariants", ok2,
    f"data_rows={data_rows} col_dist={col_dist} proved={proved_all} atlas_in={proved_in} atlas_out={proved_out} nine_grades_all_proved={all(g=='[已证]' for g in nine_grades.values())}")

# ---------- 3. only 9 rows, col6 only ----------
lb = split_lines(raw_before); la = split_lines(raw_after)
ok3a = (len(lb) == len(la))
diff_lines = []
for i in range(min(len(lb), len(la))):
    if lb[i] != la[i]:
        cb = lb[i].split(b"\t"); ca = la[i].split(b"\t")
        diffs = [j for j in range(min(len(cb),len(ca))) if cb[j]!=ca[j]]
        diff_lines.append((i+1, ca[0].decode("utf-8") if ca else "?", diffs))
ok3 = ok3a and len(diff_lines)==9 and all(e in NINE and d==[5] for _,e,d in diff_lines)
rec("3_only_9_col6_changed", ok3,
    f"line_count_equal={ok3a} n_diff_lines={len(diff_lines)} all_entry_in_NINE_and_only_col6={all(e in NINE and d==[5] for _,e,d in diff_lines)} details={[(ln,e,d) for ln,e,d in diff_lines]}")

# ---------- 4. resolve.py rerun (output to own dir) ----------
copy_cov = os.path.join(OUT, "coverage_after_copy.tsv")
shutil.copyfile(COV, copy_cov)
resolve_out = os.path.join(OUT, "_resolve_out")
os.makedirs(resolve_out, exist_ok=True)
p = subprocess.run([sys.executable, RESOLVE, "--coverage", copy_cov, "--out", resolve_out],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
# parse summary.tsv produced in resolve_out
klass = {}
sumpath = os.path.join(resolve_out, "summary.tsv")
with open(sumpath, encoding="utf-8") as f:
    rd = csv.DictReader(f, delimiter="\t")
    for row in rd: klass[row["class"]] = int(row["count"])
k4 = [klass.get("R_OK",0), klass.get("R_MISSING",0), klass.get("R_TRACE_ONLY",0), klass.get("R_EMPTY",0)]
ok4 = (k4 == [852,0,802,0])
rec("4_resolve_reclassify", ok4,
    f"R_OK={k4[0]} R_MISSING={k4[1]} R_TRACE_ONLY={k4[2]} R_EMPTY={k4[3]} (resolve rc={p.returncode})")

# ---------- 5. PANEL restorability (robust prefix/suffix diff) ----------
plb = split_lines(praw_before); pla = split_lines(praw_after)
marker = "> ✅ **M85 补记：9 行歧义证据指针全部落定".encode("utf-8")
ins_idx = [i for i,ln in enumerate(pla) if ln.startswith(marker)]
ok5a = len(ins_idx)==1
if ok5a:
    # locate inserted block as middle slice between common prefix and common suffix
    i = 0
    while i < len(plb) and i < len(pla) and plb[i] == pla[i]:
        i += 1
    j = 0
    while j < (len(plb)-i) and j < (len(pla)-i) and plb[len(plb)-1-j] == pla[len(pla)-1-j]:
        j += 1
    inserted = pla[i:len(pla)-j]
    rebuilt_panel = b"\n".join(pla[:i] + pla[len(pla)-j:])
    ok5 = (rebuilt_panel == praw_before and sha(rebuilt_panel)==sha(praw_before)==BEFORE_PANEL_SHA
           and len(inserted)==4 and all(ln.startswith(b"> ") for ln in inserted))
    detail5 = (f"inserted_at_line={i+1} n_insert_lines={len(inserted)} "
               f"rebuilt_sha={sha(rebuilt_panel)[:8]} before_sha={sha(praw_before)[:8]} "
               f"equal={rebuilt_panel==praw_before} marker_at={ins_idx[0]+1}")
else:
    ok5 = False; detail5 = f"marker_found={len(ins_idx)}"
rec("5_panel_restore", ok5, detail5)

# ---------- 6. strict_panel.py rerun (copy script, OUT redirected to own dir) ----------
strict_copy = os.path.join(OUT, "strict_panel_copy.py")
src = open(STRICT, encoding="utf-8").read()
src2 = re.sub(r'^OUT\s*=.*$', 'OUT = r"' + OUT.replace("\\","\\\\") + r'\\_strict_out"',
              src, flags=re.M)
assert src2 != src, "OUT line not replaced"
with open(strict_copy, "w", encoding="utf-8") as f: f.write(src2)
p6 = subprocess.run([sys.executable, strict_copy], capture_output=True, text=True, encoding="utf-8", errors="replace")
out6 = p6.stdout
m_nom = re.search(r"名义达标:\s*([^\s]*)", out6)
m_str = re.search(r"严格达标:\s*([^\s]*)", out6)
nom = m_nom.group(1) if m_nom else ""
strict = m_str.group(1) if m_str else ""
ok6 = (nom == "S15,S16,S17" and strict == "S17")
rec("6_dod_not_flipped", ok6, f"nominal={{{nom}}} strict={{{strict}}} (rc={p6.returncode})")
results["_stdout6"] = out6

# ---------- write after_state.json ----------
def stat(path):
    b = open(path,"rb").read()
    st = os.stat(path)
    return {"path":path,"mtime":st.st_mtime,"bytes":len(b),"sha256":sha(b),
            "line_count_lf":b.count(b"\n"),"crlf_count":b.count(b"\r\n"),
            "bom_utf8":b.startswith(b"\xef\xbb\xbf")}
after_state = {"coverage":stat(COV),"panel":stat(PANEL),
               "target_rows":{e:{"col6":new6[e].decode("utf-8")} for e in NINE},
               "resolve_classes":{"R_OK":k4[0],"R_MISSING":k4[1],"R_TRACE_ONLY":k4[2],"R_EMPTY":k4[3]},
               "dod":{"nominal":nom,"strict":strict},
               "verifications":results}
with open(os.path.join(OUT,"after_state.json"),"w",encoding="utf-8") as f:
    json.dump(after_state,f,ensure_ascii=False,indent=1)

all_ok = all(results[k]["result"]=="PASS" for k in results if not k.startswith("_"))
print("\nALL PASS" if all_ok else "\nSOME FAIL")
sys.exit(0 if all_ok else 1)

#!/usr/bin/env python3
# Generate S21-DIRECT deliverables: coverage_delta.tsv, VIRTUAL_SKIPPED.tsv, EVIDENCE files.
import os,sys,io,json
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S21_DIRECT")
WK=os.path.join(OUT,"work");EV=os.path.join(OUT,"EVIDENCE")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
def norm(a):return a.upper().replace("0X","")
# coverage semantics/name map
semmap={};namemap={}
for l in open(COV,encoding="utf-8").read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split("\t")
    if len(f)<8:continue
    semmap[norm(f[0])]=f[3];namemap[norm(f[0])]=f[2]
V=json.load(open(os.path.join(EV,"verify_direct.json"),encoding="utf-8"))["verified"]
virt=json.load(open(os.path.join(EV,"virtual_reachable_rows.json"),encoding="utf-8"))
base=json.load(open(os.path.join(EV,"baseline_final.json"),encoding="utf-8"))

# ---- EVIDENCE/direct_call_sites_clean.tsv ----
with open(os.path.join(EV,"direct_call_sites_clean.tsv"),"w",encoding="utf-8",newline="\n") as f:
    f.write("entry\tgrade_old\tname\tsite\tbytes\traw_rel32\tcomputed_target\texpected_target\tis_call\tcaller_owner\tcaller_owner_subs\tself_loop\tatexit_push\tOK\n")
    for rec in V:
        for s in rec["sites"]:
            f.write("\t".join([rec["entry"],rec["grade_old"],rec["name"],s["site"],s.get("bytes",""),
                str(s.get("rel","")),s.get("target",""),rec["entry"],str(s.get("callok",False)).lower(),
                str(s.get("owner") or ""),",".join(s.get("owner_subs",[])),
                str(s.get("selfloop",False)).lower(),str(s.get("atexit_push",False)).lower(),
                str(s.get("ok",False)).lower()])+"\n")
nsites=sum(len(r["sites"]) for r in V)
nok=sum(1 for r in V for s in r["sites"] if s.get("ok"))
print("direct_call_sites_clean.tsv:",len(V),"entries",nsites,"sites",nok,"OK")

# ---- coverage_delta.tsv (8 cols, direct rows only, grade only) ----
with open(os.path.join(OUT,"coverage_delta.tsv"),"w",encoding="utf-8",newline="\n") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t旧grade→新grade\n")
    for rec in V:
        e=rec["entry"];nm=namemap.get(e,rec["name"]);sem=semmap.get(e,rec["name"])
        old=rec["grade_old"];nk="placeholder" if nm.startswith("sub_") else "symbolic"
        f.write("\t".join([e,"S21",nm,sem,"[已证]",
            "EVIDENCE/direct_call_sites_clean.tsv#"+e,nk,old+"→[已证]"])+"\n")
print("coverage_delta.tsv:",len(V),"rows")

# ---- VIRTUAL_SKIPPED.tsv (only-virtual rows) ----
onlyv=virt["only_virtual_skipped"]
with open(os.path.join(OUT,"VIRTUAL_SKIPPED.tsv"),"w",encoding="utf-8",newline="\n") as f:
    f.write("entry\tname\tone_line_semantics\tgrade\tevidence_path\trdata_dword_refs\t环123(盘上既有)\t环4状态\t本卡处置\n")
    for v in onlyv:
        ring123="盘上%s: entry在atlas(环1); name/semantics=%s(环2/3)"%(v["grade"],v["name"])
        f.write("\t".join([v["entry"],v["name"],v["sem"],v["grade"],
            "EVIDENCE/virtual_reachable_rows.json",
            "%d@%s"%(v["nvrefs"],",".join(v["vrefs"][:4])),ring123,
            "无direct call(全.text E8边界扫0命中),仅虚表可达",
            "保留原grade,不升格"])+"\n")
print("VIRTUAL_SKIPPED.tsv:",len(onlyv),"rows")

# ---- EVIDENCE/summary.json ----
s=dict(direct_rows=len(V),direct_entries=[r["entry"] for r in V],
    direct_sites_total=nsites,direct_sites_ok=nok,
    grade_split={g:sum(1 for r in V if r["grade_old"]==g) for g in ("[未证]","[静态推断]")},
    virtual_skipped=len(onlyv),virtual_all=len(virt["virtual_all"]),overlap_direct_virtual=len(virt["overlap"]),
    coverage_pct=json.load(open(os.path.join(EV,"scan_stats.json"),encoding="utf-8"))["raw"]["coverage_pct"],
    instructions_raw=json.load(open(os.path.join(EV,"scan_stats.json"),encoding="utf-8"))["raw"]["instructions"],
    instructions_virtualsize=json.load(open(os.path.join(EV,"scan_stats.json"),encoding="utf-8"))["virtualsize"]["instructions"],
    e8_true=json.load(open(os.path.join(EV,"scan_stats.json"),encoding="utf-8"))["raw"]["true_rel32_calls"],
    proved_before=26,proved_after=26+len(V))
json.dump(s,open(os.path.join(EV,"summary.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("summary.json:",json.dumps(s,ensure_ascii=False)[:300])
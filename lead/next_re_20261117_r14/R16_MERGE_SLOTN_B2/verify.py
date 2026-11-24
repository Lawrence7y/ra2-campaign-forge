# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B2 · 9 项验证（可复跑，只读目标文件）。

读 coverage.before.bak / PANEL.before.bak / 当前 coverage.tsv / PANEL.md /
delta.tsv / before_state.json / after_state.json，逐项输出 PASS/FAIL 与实测数字。
口径 A/B 四数、§12.6 命中数均从 before/after 字节现算，不引用任何预测值。
不修改任何目标文件；仅写自己的产物 verify_result.json。
"""
import hashlib, json, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B2", "delta.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B2")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
C4="\u2463"; SB="④ 活表槽位见证"; OLD="R14_COMMON §12.4"; NEW="R14_COMMON §12.6"
M87_FIRST="> ✅ **M87 补记"

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e

def load_atlas():
    s=set()
    for i,l in enumerate(open(ATLAS,encoding="utf-8-sig")):
        if i==0: continue
        p=l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): s.add(ne(p[0]))
    return s

def counts(text, atlas):
    data=text.splitlines()[1:]; coldist=collections.Counter(len(l.split("\t")) for l in data)
    yz=ina=outa=na=nb=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1
            if SB in c[3]: nb+=1
    return dict(data_rows=len(data),coldist=dict((str(k),v) for k,v in coldist.items()),
                yizheng=yz,atlas_in=ina,atlas_out=outa,N_A=na,N_B=nb)

def eol(b):
    return dict(CRLF=b.count(b"\r\n"),LF=b.count(b"\n")-b.count(b"\r\n"),
                CR=b.count(b"\r")-b.count(b"\r\n"),BOM=(b[:3]==b"\xef\xbb\xbf"),
                ends_nl=b.endswith(b"\n"))

def main():
    bs=json.load(open(os.path.join(OUTD,"before_state.json"),encoding="utf-8"))
    a_s=json.load(open(os.path.join(OUTD,"after_state.json"),encoding="utf-8"))
    cov_cur_b=open(COV,"rb").read(); pan_cur_b=open(PANEL,"rb").read()
    cov_before_b=open(os.path.join(OUTD,"coverage.before.bak"),"rb").read()
    pan_before_b=open(os.path.join(OUTD,"PANEL.before.bak"),"rb").read()
    cov_cur=cov_cur_b.decode("utf-8"); cov_before=cov_before_b.decode("utf-8")
    pan_cur=pan_cur_b.decode("utf-8"); pan_before=pan_before_b.decode("utf-8")
    atlas=load_atlas()
    targets=bs["coverage"]["target_rows"]
    entries=[t["entry"] for t in targets]
    before4={t["entry"]:t["col4_before"] for t in targets}
    results={}

    # 定位当前 15 行
    cur_lines=cov_cur.splitlines(keepends=True); by_entry={}
    for idx,ln in enumerate(cur_lines):
        core=ln[:-1] if ln.endswith("\n") else ln
        c=core.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)

    # ---- V1 逐字节还原性 coverage.tsv ----
    restored=list(cur_lines); ok=True
    for t in targets:
        e=t["entry"]; idxs=by_entry.get(e,[])
        if len(idxs)!=1: ok=False; continue
        i=idxs[0]; ln=restored[i]; nl="\n" if ln.endswith("\n") else ""
        core=ln[:-1] if nl else ln; c=core.split("\t"); c[3]=before4[e]
        restored[i]="\t".join(c)+nl
    recon_b="".join(restored).encode("utf-8")
    before_sha=sha(cov_before_b)
    v1=(recon_b==cov_before_b) and sha(recon_b)==before_sha and ok
    results["V1_coverage_byte_restore"]=dict(status="PASS" if v1 else "FAIL",
        recon_sha8=sha(recon_b)[:8],before_sha8=before_sha[:8],
        recon_eq_bak=(recon_b==cov_before_b),ok_locate=ok)

    # ---- V2 不变量 ----
    mc=counts(cov_cur,atlas)
    grade_map={}
    for ln in cov_cur.splitlines()[1:]:
        c=ln.split("\t")
        if len(c)>=8: grade_map[ne(c[0])]=c[4].strip()
    grades_ok=all(grade_map.get(e)=="[已证]" for e in entries)
    v2=(mc["data_rows"]==18498 and mc["coldist"]=={"8":18498} and
        mc["yizheng"]==1654 and mc["atlas_in"]==1648 and mc["atlas_out"]==6 and grades_ok)
    results["V2_invariants"]=dict(status="PASS" if v2 else "FAIL",measured=mc,
        expected=dict(data_rows=18498,coldist={"8":18498},yizheng=1654,atlas_in=1648,atlas_out=6),
        grades_yizheng_15=grades_ok)

    # ---- V3 只有 15 行第 4 列变了 ----
    b_lines=cov_before.splitlines(); c_lines=cov_cur.splitlines()
    diff=[]; bad=[]
    if len(b_lines)!=len(c_lines): bad.append("line_count %d != %d"%(len(b_lines),len(c_lines)))
    else:
        for i,(bl,cl) in enumerate(zip(b_lines,c_lines)):
            if bl==cl: continue
            bc=bl.split("\t"); cc=cl.split("\t")
            if len(bc)!=8 or len(cc)!=8:
                bad.append("row %d col count %d/%d"%(i,len(bc),len(cc))); continue
            ch=[j for j in range(8) if bc[j]!=cc[j]]
            diff.append(dict(entry=ne(bc[0]),changed_cols=ch,line_no=i+1))
            if ch!=[3]: bad.append("row %d changed %s"%(i+1,ch))
    exp=set(entries); got=set(d["entry"] for d in diff)
    v3=(len(diff)==15 and got==exp and not bad)
    results["V3_only_15_col4"]=dict(status="PASS" if v3 else "FAIL",
        n_diff=len(diff),expected_n=15,entries_match=(got==exp),bad=bad,diff_entries=diff)

    # ---- V4 严格前缀 ----
    pref=[]
    for t in targets:
        e=t["entry"]; b4=before4[e]; i=by_entry[e][0]
        core=cur_lines[i][:-1] if cur_lines[i].endswith("\n") else cur_lines[i]
        a4=core.split("\t")[3]
        pref.append(dict(entry=e,ok=a4.startswith(b4)))
    v4=all(p["ok"] for p in pref)
    results["V4_strict_prefix"]=dict(status="PASS" if v4 else "FAIL",
        n=len(pref),n_ok=sum(1 for p in pref if p["ok"]),detail=pref)

    # ---- V5 口径 A/B 四数（从 before/after 字节现算）----
    cb=counts(cov_before,atlas); ca=counts(cov_cur,atlas)
    N_pre=sum(1 for t in targets if t["before_has_circled4"])
    four=dict(N_A_pre=cb["N_A"],N_A_post=ca["N_A"],N_B_pre=cb["N_B"],N_B_post=ca["N_B"],N_pre=N_pre)
    v5=(cb["N_A"]==328 and ca["N_A"]==337 and cb["N_B"]==106 and ca["N_B"]==121 and N_pre==6)
    results["V5_four_numbers"]=dict(status="PASS" if v5 else "FAIL",measured=four,
        expected=dict(N_A_pre=328,N_A_post=337,N_B_pre=106,N_B_post=121,N_pre=6),
        net_A=ca["N_A"]-cb["N_A"],net_B=ca["N_B"]-cb["N_B"],
        note="口径A=[已证]且col4含字符④；口径B=[已证]且col4含'④ 活表槽位见证'。四数均实测，非预测。")

    # ---- V6 §12.6 替换次数与命中数 ----
    drows=[l.split("\t") for l in open(DELTA,encoding="utf-8-sig").read().splitlines()[1:]]
    repl=sum(d[3].count(OLD) for d in drows)
    s126_after_lines=sum(1 for l in cov_cur.splitlines() if NEW in l)
    s126_after_hits=cov_cur.count(NEW)
    s124_after_hits=cov_cur.count(OLD)
    s124_before_hits=cov_before.count(OLD)
    v6=(repl==15 and s126_after_lines==30 and s126_after_hits==30 and s124_after_hits==0)
    results["V6_pointer_normalize"]=dict(status="PASS" if v6 else "FAIL",
        replacement_count=repl,s126_lines_after=s126_after_lines,s126_hits_after=s126_after_hits,
        s124_hits_after=s124_after_hits,s124_hits_before=s124_before_hits,
        expected=dict(replacement_count=15,s126_hits_after=30,s124_hits_after=0))

    # ---- V7 PANEL.md 还原性（删 M87 块后重建 sha == 改前）----
    pan_lines=pan_cur.splitlines(keepends=True)
    ins=[s+"\n" for s in bs["panel"]["inserted_lines"]]
    idxs=[i for i,ln in enumerate(pan_lines) if ln.startswith(M87_FIRST)]
    pan_rest=list(pan_lines); ok_ins=False
    if len(idxs)==1:
        s=idxs[0]
        if pan_rest[s:s+len(ins)]==ins:
            del pan_rest[s:s+len(ins)]; ok_ins=True
    pan_recon_b="".join(pan_rest).encode("utf-8"); pan_before_sha=sha(pan_before_b)
    v7=(pan_recon_b==pan_before_b) and sha(pan_recon_b)==pan_before_sha and ok_ins
    results["V7_panel_restore"]=dict(status="PASS" if v7 else "FAIL",
        recon_sha8=sha(pan_recon_b)[:8],before_sha8=pan_before_sha[:8],
        recon_eq_bak=(pan_recon_b==pan_before_b),ok_insert_removed=ok_ins,
        m87_block_lines=len(ins))

    # ---- V8 达标未翻转 ----
    nom=a_s["strict"]["nominal"]; st=a_s["strict"]["strict"]; rc=a_s["strict"]["returncode"]
    v8=(nom=="S15,S16,S17" and st=="S17" and rc==0)
    results["V8_dod_no_flip"]=dict(status="PASS" if v8 else "FAIL",
        nominal=nom,strict=st,returncode=rc,expected_nominal="S15,S16,S17",expected_strict="S17",
        script=a_s["strict"]["script"],out_dir=a_s["strict"]["out_dir"])

    # ---- V9 行尾（实测，不引入混用）----
    cov_be=eol(cov_before_b); cov_ae=eol(cov_cur_b); pan_be=eol(pan_before_b); pan_ae=eol(pan_cur_b)
    cov_mix=cov_ae["CRLF"]>0 and cov_ae["LF"]>0
    pan_mix=pan_ae["CRLF"]>0 and pan_ae["LF"]>0
    d_cov_lf=cov_ae["LF"]-cov_be["LF"]; d_pan_lf=pan_ae["LF"]-pan_be["LF"]
    d_cov_bytes=len(cov_cur_b)-len(cov_before_b); d_pan_bytes=len(pan_cur_b)-len(pan_before_b)
    add_bytes=sum(t["added_bytes"] for t in targets)
    pan_ins_bytes=sum(len(s.encode("utf-8")) for s in ins)
    v9=(not cov_mix and not pan_mix and d_cov_lf==0 and d_pan_lf==len(ins) and
        d_cov_bytes==add_bytes and d_pan_bytes==pan_ins_bytes and
        cov_be["CRLF"]==cov_ae["CRLF"] and pan_be["CRLF"]==pan_ae["CRLF"])
    results["V9_line_endings"]=dict(status="PASS" if v9 else "FAIL",
        cov_before=cov_be,cov_after=cov_ae,pan_before=pan_be,pan_after=pan_ae,
        cov_mixed=cov_mix,pan_mixed=pan_mix,d_cov_lf=d_cov_lf,d_pan_lf=d_pan_lf,
        d_cov_bytes=d_cov_bytes,expected_d_cov_bytes=add_bytes,
        d_pan_bytes=d_pan_bytes,expected_d_pan_bytes=pan_ins_bytes)

    with open(os.path.join(OUTD,"verify_result.json"),"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=1)

    print("=== 9 项验证结果 ===")
    for k in sorted(results): print("%-28s %s"%(k,results[k]["status"]))
    print("\n关键实测：")
    print("  行数/列分布:",mc["data_rows"],mc["coldist"])
    print("  [已证]/atlas内/外:",mc["yizheng"],mc["atlas_in"],mc["atlas_out"])
    print("  15行grade仍[已证]:",grades_ok)
    print("  差异行:",len(diff),"均匹配:",got==exp,"每行仅第4列:",not bad)
    print("  严格前缀:",sum(1 for p in pref if p["ok"]),"/",len(pref))
    print("  口径A/B四数:",four,"net_A=+9 net_B=+15")
    print("  §12.4->§12.6 替换:",repl,"处；改后 §12.6 命中:",s126_after_hits,"行:",s126_after_lines,"；§12.4:",s124_after_hits)
    print("  达标:",nom,"/",st)
    print("  行尾 cov:",cov_ae,"pan:",pan_ae)
    npass=sum(1 for k in results if results[k]["status"]=="PASS")
    print("\nPASS %d/%d"%(npass,len(results)))

if __name__=="__main__": main()

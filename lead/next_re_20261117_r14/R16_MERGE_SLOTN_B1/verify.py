# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B1 · 8 项验证（可复跑，只读目标文件）。

读 before_state.json / after_state.json / coverage.before.bak / PANEL.before.bak /
当前 coverage.tsv / PANEL.md / delta.tsv，逐项输出 PASS/FAIL 与实测数字。
不修改任何目标文件；仅写自己的产物 verify_result.json。
"""
import hashlib, json, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B1")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
C4 = "\u2463"  # ④

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e

def load_state():
    bs=json.load(open(os.path.join(OUTD,"before_state.json"),encoding="utf-8"))
    a_s=json.load(open(os.path.join(OUTD,"after_state.json"),encoding="utf-8"))
    return bs,a_s

def cov_metrics(text):
    data=text.splitlines()[1:]
    coldist=collections.Counter(len(ln.split("\t")) for ln in data)
    atlas=set()
    for i,l in enumerate(open(ATLAS,encoding="utf-8-sig")):
        if i==0: continue
        p=l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))
    yz=ina=outa=sih=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if C4 in c[3]: sih+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
    return dict(data_rows=len(data),coldist=dict((str(k),v) for k,v in coldist.items()),
                yizheng=yz,atlas_in=ina,atlas_out=outa,sih_yizheng=sih)

def main():
    bs,a_s=load_state()
    results={}
    cov_cur_b=open(COV,"rb").read(); pan_cur_b=open(PANEL,"rb").read()
    cov_before_b=open(os.path.join(OUTD,"coverage.before.bak"),"rb").read()
    pan_before_b=open(os.path.join(OUTD,"PANEL.before.bak"),"rb").read()
    cov_cur=cov_cur_b.decode("utf-8"); cov_before=cov_before_b.decode("utf-8")
    pan_cur=pan_cur_b.decode("utf-8"); pan_before=pan_before_b.decode("utf-8")
    targets=bs["coverage"]["target_rows"]
    entries=[t["entry"] for t in targets]
    before4={t["entry"]:t["col4_before"] for t in targets}

    # ---- V1 逐字节还原性 coverage.tsv ----
    cur_lines=cov_cur.splitlines(keepends=True)
    by_entry={}
    for idx,ln in enumerate(cur_lines):
        core=ln[:-1] if ln.endswith("\n") else ln
        c=core.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)
    restored=list(cur_lines)
    ok_restore=True
    for t in targets:
        e=t["entry"]; idxs=by_entry.get(e,[])
        if len(idxs)!=1: ok_restore=False; continue
        i=idxs[0]; ln=restored[i]; nl="\n" if ln.endswith("\n") else ""
        core=ln[:-1] if nl else ln; c=core.split("\t")
        c[3]=t["col4_before"]; restored[i]="\t".join(c)+nl
    recon_b="".join(restored).encode("utf-8")
    before_sha=bs["coverage"]["sha256"]
    v1=(recon_b==cov_before_b) and (sha(recon_b)==before_sha)
    results["V1_coverage_byte_restore"]=dict(
        status="PASS" if v1 else "FAIL",
        recon_sha8=sha(recon_b)[:8], before_sha8=before_sha[:8],
        recon_eq_bak=(recon_b==cov_before_b), ok_locate=ok_restore)

    # ---- V2 不变量 ----
    mc=cov_metrics(cov_cur)
    inv_expected=dict(data_rows=18498,yizheng=1654,atlas_in=1648,atlas_out=6)
    # 用 map 逐 entry 核对 grade
    grade_map={}
    for ln in cov_cur.splitlines()[1:]:
        c=ln.split("\t")
        if len(c)>=8: grade_map[ne(c[0])]=c[4].strip()
    cur_grade_all_ok=all(grade_map.get(e)=="[已证]" for e in entries)
    v2=(mc["data_rows"]==18498 and mc["coldist"]=={"8":18498} and
        mc["yizheng"]==1654 and mc["atlas_in"]==1648 and mc["atlas_out"]==6 and cur_grade_all_ok)
    results["V2_invariants"]=dict(status="PASS" if v2 else "FAIL", measured=mc,
                                  expected=inv_expected, grades_yizheng_15=cur_grade_all_ok)

    # ---- V3 只有 15 行第4列变了 ----
    b_lines=cov_before.splitlines(); c_lines=cov_cur.splitlines()
    diff_entries=[]; diff_bad=[]
    if len(b_lines)!=len(c_lines):
        diff_bad.append("line_count %d != %d"%(len(b_lines),len(c_lines)))
    else:
        for i,(bl,cl) in enumerate(zip(b_lines,c_lines)):
            if bl==cl: continue
            bc=bl.split("\t"); cc=cl.split("\t")
            if len(bc)!=8 or len(cc)!=8:
                diff_bad.append("row %d col count %d/%d"%(i,len(bc),len(cc))); continue
            changed=[j for j in range(8) if bc[j]!=cc[j]]
            e=ne(bc[0])
            diff_entries.append(dict(entry=e,changed_cols=changed,line_no=i+1))
            if changed!=[3]: diff_bad.append("row %d %s changed %s"%(i+1,e,changed))
    set_exp=set(entries); set_got=set(d["entry"] for d in diff_entries)
    v3=(len(diff_entries)==15 and set_got==set_exp and not diff_bad)
    results["V3_only_15_col4"]=dict(status="PASS" if v3 else "FAIL",
        n_diff=len(diff_entries),expected_n=15,
        entries_match=(set_got==set_exp),bad=diff_bad,
        diff_entries=diff_entries)

    # ---- V4 严格前缀 ----
    pref=[]
    for t in targets:
        e=t["entry"]; b4=t["col4_before"]; a4=None
        i=by_entry[e][0]; c=cur_lines[i][:-1].split("\t"); a4=c[3]
        pref.append(dict(entry=e,ok=a4.startswith(b4)))
    v4=all(p["ok"] for p in pref)
    results["V4_strict_prefix"]=dict(status="PASS" if v4 else "FAIL",
        n=len(pref),n_ok=sum(1 for p in pref if p["ok"]),detail=pref)

    # ---- V5 ④ 已成文计数（含字符 ④ 口径）----
    mb=cov_metrics(cov_before); ma=cov_metrics(cov_cur)
    n_before_already=sum(1 for t in targets if t.get("before_has_circled4", False))
    expect_after=334
    delta=ma["sih_yizheng"]-mb["sih_yizheng"]
    v5=(mb["sih_yizheng"]==319 and ma["sih_yizheng"]==334)
    results["V5_circled4_chengwen"]=dict(
        status="PASS" if v5 else "FAIL(实测偏差，已查清)",
        before=mb["sih_yizheng"],after=ma["sih_yizheng"],delta=delta,
        expected_before=319,expected_after=expect_after,
        before_already_has_C4=n_before_already,
        net_new=15-n_before_already,
        explanation=("按卡面口径([已证]且col4含字符 ④)实测改前319、改后328；卡面预期334(+15)未达成。"
             "原因：15行中有%d行改前col4已含字符 ④(位于原文'合同闭合 ③b④'分类标签)，"
             "改后仍含该字符故计数不增；仅其余%d行净新增。319+%d=328。"%(n_before_already,15-n_before_already,15-n_before_already)))

    # ---- V6 PANEL.md 还原性 ----
    pan_lines=pan_cur.splitlines(keepends=True)
    ins_lines=[s+"\n" for s in bs["panel"]["inserted_lines"]]
    # 找到插入块起点（第一条 M86 标记行）
    m86_idx=[i for i,ln in enumerate(pan_lines) if ln.startswith("> ✅ **M86 补记")]
    pan_rest=list(pan_lines)
    ok_ins=True
    if len(m86_idx)==1:
        s=m86_idx[0]
        if pan_rest[s:s+len(ins_lines)]==ins_lines:
            del pan_rest[s:s+len(ins_lines)]
        else:
            ok_ins=False
    else:
        ok_ins=False
    ptr_new="> 成文位置：`R14_COMMON.md §12.6`。"
    ptr_old="> 成文位置：`R14_COMMON.md §12.4`。"
    ptr_hits=sum(1 for ln in pan_rest if ptr_new in ln)
    pan_rest=[ln.replace(ptr_new,ptr_old) for ln in pan_rest]
    pan_recon_b="".join(pan_rest).encode("utf-8")
    pan_before_sha=bs["panel"]["sha256"]
    v6=(pan_recon_b==pan_before_b) and (sha(pan_recon_b)==pan_before_sha) and ok_ins and ptr_hits==1
    results["V6_panel_restore"]=dict(status="PASS" if v6 else "FAIL",
        recon_sha8=sha(pan_recon_b)[:8],before_sha8=pan_before_sha[:8],
        recon_eq_bak=(pan_recon_b==pan_before_b),ok_insert_removed=ok_ins,
        pointer_reverted_hits=ptr_hits)

    # ---- V7 达标未翻转 ----
    nom=a_s["strict"]["nominal"]; st=a_s["strict"]["strict"]; rc=a_s["strict"]["returncode"]
    v7=(nom=="S15,S16,S17" and st=="S17" and rc==0)
    results["V7_dod_no_flip"]=dict(status="PASS" if v7 else "FAIL",
        nominal=nom,strict=st,returncode=rc,
        expected_nominal="S15,S16,S17",expected_strict="S17",
        script=a_s["strict"]["script"],out_dir=a_s["strict"]["out_dir"])

    # ---- V8 行尾 ----
    def eol(b): return dict(CRLF=b.count(b"\r\n"),LF=b.count(b"\n")-b.count(b"\r\n"),CR=b.count(b"\r")-b.count(b"\r\n"),BOM=(b[:3]==b"\xef\xbb\xbf"),ends_nl=b.endswith(b"\n"))
    cov_be=eol(cov_before_b); cov_ae=eol(cov_cur_b); pan_be=eol(pan_before_b); pan_ae=eol(pan_cur_b)
    cov_mix = (cov_ae["CRLF"]>0 and cov_ae["LF"]>0)
    pan_mix = (pan_ae["CRLF"]>0 and pan_ae["LF"]>0)
    d_cov_lf=cov_ae["LF"]-cov_be["LF"]; d_pan_lf=pan_ae["LF"]-pan_be["LF"]
    d_cov_bytes=len(cov_cur_b)-len(cov_before_b); d_pan_bytes=len(pan_cur_b)-len(pan_before_b)
    add_bytes=sum(t["added_bytes"] for t in [])  # recompute below
    # recompute added bytes from states
    pt=bs["coverage"]["target_rows"]
    # added bytes = sum(len(after4)-len(before4) in bytes)
    drows=[l.split("\t") for l in open(DELTA,encoding="utf-8-sig").read().splitlines()[1:]]
    newcol={ne(d[0]):d[3].replace("R14_COMMON §12.4","R14_COMMON §12.6") for d in drows}
    add_bytes=sum(len(newcol[t["entry"]].encode("utf-8"))-len(t["col4_before"].encode("utf-8")) for t in pt)
    pan_ins_bytes=sum(len((s+"\n").encode("utf-8")) for s in bs["panel"]["inserted_lines"])
    ptr_delta_bytes=0  # §12.4 -> §12.6 同样字节数
    v8=(not cov_mix and not pan_mix and d_cov_lf==0 and d_pan_lf==8 and
        d_cov_bytes==add_bytes and d_pan_bytes==pan_ins_bytes+ptr_delta_bytes)
    results["V8_line_endings"]=dict(status="PASS" if v8 else "FAIL",
        cov_before=cov_be,cov_after=cov_ae,pan_before=pan_be,pan_after=pan_ae,
        cov_mixed=cov_mix,pan_mixed=pan_mix,
        d_cov_lf=d_cov_lf,d_pan_lf=d_pan_lf,
        d_cov_bytes=d_cov_bytes,expected_d_cov_bytes=add_bytes,
        d_pan_bytes=d_pan_bytes,expected_d_pan_bytes=pan_ins_bytes+ptr_delta_bytes)

    with open(os.path.join(OUTD,"verify_result.json"),"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=1)

    print("=== 8 项验证结果 ===")
    for k in sorted(results):
        print("%-28s %s"%(k,results[k]["status"]))
    print("\n关键实测：")
    print("  行数/列分布:",mc["data_rows"],mc["coldist"])
    print("  [已证]/atlas内/外:",mc["yizheng"],mc["atlas_in"],mc["atlas_out"])
    print("  ④已成文(字符口径):",mb["sih_yizheng"],"->",ma["sih_yizheng"],"(预期334)")
    print("  差异行:",len(diff_entries),"均匹配:",set_got==set_exp)
    print("  改前已含④行数:",n_before_already,"(6)")
    print("  达标:",nom,"/",st)
    print("  字节增量 coverage:",d_cov_bytes,"(追加段合计",add_bytes,")")
    print("  字节增量 PANEL:",d_pan_bytes,"(插入8行",pan_ins_bytes,")")
    n_pass=sum(1 for k in results if results[k]["status"]=="PASS")
    print("\nPASS %d/%d"%(n_pass,len(results)))

if __name__=="__main__":
    main()

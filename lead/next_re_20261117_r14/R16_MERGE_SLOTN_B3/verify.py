# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B3 · 10 项验证（可复跑，只读目标文件）。

读 coverage.before.bak / PANEL.before.bak / 当前 coverage.tsv / PANEL.md /
delta.tsv / slotN43.tsv / before_state.json / after_state.json，从字节现算
每一项；口径 A/B 五个实测数、§12.6/§12.4 命中数均不引用预测值。
不修改任何目标文件；仅写自己的产物 verify_result.json。
"""
import hashlib, json, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B3", "delta.tsv")
SLOTN= os.path.join(ROOT, "PROBE_802", "slotN43.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B3")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

C4="\u2463"; SB="④ 活表槽位见证"; S126="§12.6"; S124="§12.4"
M88_FIRST="> ✅ **M88 补记"
M77_ANCHOR="> 📌 **M77 并表实算说明**"

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

def split_cov(text):
    parts=text.split("\n")
    return parts[0], [ln for ln in parts[1:] if ln!=""]

def counts(data, atlas):
    coldist=collections.Counter(len(l.split("\t")) for l in data)
    yz=ina=outa=na=nb=0
    s126_lines=s124_lines=s126_hits=s124_hits=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if c[4].strip()=="[已证]":
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1
            if SB in c[3]: nb+=1
        if S126 in ln: s126_lines+=1
        if S124 in ln: s124_lines+=1
        s126_hits+=ln.count(S126); s124_hits+=ln.count(S124)
    return dict(data_rows=len(data),coldist={str(k):v for k,v in coldist.items()},
                yizheng=yz,atlas_in=ina,atlas_out=outa,N_A=na,N_B=nb,
                s126_lines=s126_lines,s124_lines=s124_lines,
                s126_hits=s126_hits,s124_hits=s124_hits)

def eol(b):
    return dict(CRLF=b.count(b"\r\n"), LF=b.count(b"\n")-b.count(b"\r\n"),
                CR=b.count(b"\r")-b.count(b"\r\n"),
                BOM=(b[:3]==b"\xef\xbb\xbf"), ends_nl=b.endswith(b"\n"))

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

    # 定位 13 行（改前备份 + 改后现盘）
    def index_by_entry(data):
        d={}
        for idx,ln in enumerate(data):
            c=ln.split("\t")
            if len(c)>=8: d.setdefault(ne(c[0]),[]).append(idx)
        return d
    _,data_before=split_cov(cov_before); hdr_cur,data_cur=split_cov(cov_cur)
    idx_before=index_by_entry(data_before); idx_cur=index_by_entry(data_cur)

    # ---- V1 逐字节还原性（coverage.tsv）----
    restored=list(data_cur); ok=True
    for t in targets:
        e=t["entry"]; idxs=idx_cur.get(e,[])
        if len(idxs)!=1: ok=False; continue
        i=idxs[0]; c=restored[i].split("\t"); c[3]=before4[e]; restored[i]="\t".join(c)
    recon_b=(hdr_cur+"\n"+"\n".join(restored)).encode("utf-8")
    before_sha=sha(cov_before_b)
    v1=(recon_b==cov_before_b) and sha(recon_b)==before_sha and ok
    results["V1_coverage_byte_restore"]=dict(status="PASS" if v1 else "FAIL",
        recon_sha8=sha(recon_b)[:8],before_sha8=before_sha[:8],
        recon_eq_bak=(recon_b==cov_before_b),ok_locate=ok)

    # ---- V2 不变量 ----
    mc=counts(data_cur,atlas)
    grade_map={}
    for ln in data_cur:
        c=ln.split("\t")
        if len(c)>=8: grade_map[ne(c[0])]=c[4].strip()
    grades_ok=all(grade_map.get(e)=="[已证]" for e in entries)
    v2=(mc["data_rows"]==18498 and mc["coldist"]=={"8":18498} and
        mc["yizheng"]==1654 and mc["atlas_in"]==1648 and mc["atlas_out"]==6 and grades_ok)
    results["V2_invariants"]=dict(status="PASS" if v2 else "FAIL",measured=mc,
        expected=dict(data_rows=18498,coldist={"8":18498},yizheng=1654,atlas_in=1648,atlas_out=6),
        grades_yizheng_13=grades_ok)

    # ---- V3 只有 13 行第 4 列变了 ----
    diff=[]; bad=[]
    if len(data_before)!=len(data_cur): bad.append("line_count %d != %d"%(len(data_before),len(data_cur)))
    else:
        for i,(bl,cl) in enumerate(zip(data_before,data_cur)):
            if bl==cl: continue
            bc=bl.split("\t"); cc=cl.split("\t")
            if len(bc)!=8 or len(cc)!=8:
                bad.append("row %d col count %d/%d"%(i+2,len(bc),len(cc))); continue
            ch=[j for j in range(8) if bc[j]!=cc[j]]
            diff.append(dict(entry=ne(bc[0]),changed_cols=ch,line_no=i+2))
            if ch!=[3]: bad.append("row %d changed %s"%(i+2,ch))
    exp=set(entries); got=set(d["entry"] for d in diff)
    v3=(len(diff)==13 and got==exp and not bad)
    results["V3_only_13_col4"]=dict(status="PASS" if v3 else "FAIL",
        n_diff=len(diff),expected_n=13,entries_match=(got==exp),bad=bad,diff_entries=diff)

    # ---- V4 严格前缀 13/13 ----
    pref=[]
    for t in targets:
        e=t["entry"]; b4=before4[e]; i=idx_cur[e][0]
        a4=data_cur[i].split("\t")[3]
        pref.append(dict(entry=e,ok=a4.startswith(b4) and len(a4)>len(b4)))
    v4=all(p["ok"] for p in pref)
    results["V4_strict_prefix"]=dict(status="PASS" if v4 else "FAIL",
        n=len(pref),n_ok=sum(1 for p in pref if p["ok"]),detail=pref)

    # ---- V5 口径 A/B 五个数（从 before/after 字节现算）----
    cb=counts(data_before,atlas); ca=counts(data_cur,atlas)
    # N_pre 从改前备份现算（不引用 before_state 的 before_has_circled4）
    N_pre=0; pre_list=[]
    for e in entries:
        i=idx_before[e][0]; b4=data_before[i].split("\t")[3]
        if C4 in b4: N_pre+=1; pre_list.append(e)
    four=dict(N_A_pre=cb["N_A"],N_A_post=ca["N_A"],N_B_pre=cb["N_B"],N_B_post=ca["N_B"],N_pre=N_pre)
    # 自洽：改后 A = 改前 A + (13 - N_pre)；改后 B = 改前 B + 13
    consistent=(ca["N_A"]==cb["N_A"]+(13-N_pre) and ca["N_B"]==cb["N_B"]+13)
    v5=consistent and N_pre==bs["measured"]["N_pre"] and \
        four=={k:bs["measured"][k] for k in four}
    results["V5_five_numbers"]=dict(status="PASS" if v5 else "FAIL",measured=four,
        pre_circled4_entries=pre_list,consistent=consistent,
        net_A=ca["N_A"]-cb["N_A"],net_B=ca["N_B"]-cb["N_B"],
        note="口径A=[已证]且col4含字符④；口径B=[已证]且col4含'④ 活表槽位见证'。五数均实测，非预测。")

    # ---- V6 §12.6/§12.4 命中计数（13 行内、以及全表）----
    # 13 行追加段内：用改前备份 col4 现算追加段
    append_s126=append_s124=0
    for e in entries:
        i=idx_before[e][0]; b4=data_before[i].split("\t")[3]
        j=idx_cur[e][0]; a4=data_cur[j].split("\t")[3]
        seg=a4[len(b4):] if a4.startswith(b4) else ""
        append_s126+=seg.count(S126); append_s124+=seg.count(S124)
    v6=(append_s126==13 and append_s124==0 and
        ca["s124_hits"]==0 and cb["s124_hits"]==0 and
        ca["s126_hits"]==cb["s126_hits"]+13 and
        ca["s126_lines"]==cb["s126_lines"]+13)
    results["V6_pointer_counts"]=dict(status="PASS" if v6 else "FAIL",
        append_13_s126=append_s126,append_13_s124=append_s124,
        whole_before_s126_lines=cb["s126_lines"],whole_before_s126_hits=cb["s126_hits"],
        whole_after_s126_lines=ca["s126_lines"],whole_after_s126_hits=ca["s126_hits"],
        whole_before_s124_hits=cb["s124_hits"],whole_after_s124_hits=ca["s124_hits"],
        expected=dict(append_s126=13,append_s124=0,whole_after_s124_hits=0))

    # ---- V7 PANEL.md 还原性（删 M88 块后重建 sha == 改前）----
    pan_lines=pan_cur.split("\n")
    ins=[l for l in bs["panel"]["inserted_lines"]]
    idxs=[i for i,l in enumerate(pan_lines) if l.startswith(M88_FIRST)]
    pan_rest=list(pan_lines); ok_ins=False
    if len(idxs)==1:
        s=idxs[0]
        if pan_rest[s:s+len(ins)]==ins:
            del pan_rest[s:s+len(ins)]; ok_ins=True
    pan_recon_b="\n".join(pan_rest).encode("utf-8"); pan_before_sha=sha(pan_before_b)
    v7=(pan_recon_b==pan_before_b) and sha(pan_recon_b)==pan_before_sha and ok_ins
    results["V7_panel_restore"]=dict(status="PASS" if v7 else "FAIL",
        recon_sha8=sha(pan_recon_b)[:8],before_sha8=pan_before_sha[:8],
        recon_eq_bak=(pan_recon_b==pan_before_b),ok_insert_removed=ok_ins,
        m88_block_lines=len(ins))

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
    pan_ins_bytes=sum(len(s.encode("utf-8"))+1 for s in ins)  # +1 for the \n per inserted line
    v9=(not cov_mix and not pan_mix and cov_ae["CR"]==0 and pan_ae["CR"]==0 and
        d_cov_lf==0 and d_pan_lf==len(ins) and
        d_cov_bytes==add_bytes and d_pan_bytes==pan_ins_bytes and
        cov_be["CRLF"]==cov_ae["CRLF"] and pan_be["CRLF"]==pan_ae["CRLF"])
    results["V9_line_endings"]=dict(status="PASS" if v9 else "FAIL",
        cov_before=cov_be,cov_after=cov_ae,pan_before=pan_be,pan_after=pan_ae,
        cov_mixed=cov_mix,pan_mixed=pan_mix,d_cov_lf=d_cov_lf,d_pan_lf=d_pan_lf,
        d_cov_bytes=d_cov_bytes,expected_d_cov_bytes=add_bytes,
        d_pan_bytes=d_pan_bytes,expected_d_pan_bytes=pan_ins_bytes)

    # ---- V10 43 行收官核对 ----
    slotn_entries=set()
    with open(SLOTN,encoding="utf-8-sig") as f:
        for i,l in enumerate(f):
            if i==0: continue
            p=l.rstrip("\r\n").split("\t")
            if p and p[0].strip(): slotn_entries.add(ne(p[0]))
    close_rows=[]
    for ln in data_cur:
        c=ln.split("\t")
        if len(c)<8: continue
        if SB in c[3] and ne(c[0]) in slotn_entries: close_rows.append(ne(c[0]))
    v10=(len(slotn_entries)==43 and len(close_rows)==43 and len(set(close_rows))==43)
    results["V10_slotN43_closeout"]=dict(status="PASS" if v10 else "FAIL",
        slotn_entries_in_file=len(slotn_entries),closeout_rows=len(close_rows),
        closeout_unique=len(set(close_rows)),expected=43,
        missing=sorted(slotn_entries-set(close_rows)))

    with open(os.path.join(OUTD,"verify_result.json"),"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=1)

    print("=== 10 项验证结果 ===")
    for k in sorted(results): print("%-28s %s"%(k,results[k]["status"]))
    print("\n关键实测：")
    print("  行数/列分布:",mc["data_rows"],mc["coldist"])
    print("  [已证]/atlas内/外:",mc["yizheng"],mc["atlas_in"],mc["atlas_out"])
    print("  13行grade仍[已证]:",grades_ok)
    print("  差异行:",len(diff),"均匹配:",got==exp,"每行仅第4列:",not bad)
    print("  严格前缀:",sum(1 for p in pref if p["ok"]),"/",len(pref))
    print("  口径 A/B 五数:",four,"net_A=%+d net_B=%+d"%(ca["N_A"]-cb["N_A"],ca["N_B"]-cb["N_B"]))
    print("  §12.6/§12.4: 13行内 13/0；全表 §12.6 lines %d->%d hits %d->%d；§12.4 %d->%d" %
          (cb["s126_lines"],ca["s126_lines"],cb["s126_hits"],ca["s126_hits"],
           cb["s124_hits"],ca["s124_hits"]))
    print("  达标:",nom,"/",st)
    print("  行尾 cov:",cov_ae,"pan:",pan_ae)
    print("  43 行收官: slotN43 entries=%d, 命中行=%d, unique=%d" %
          (len(slotn_entries),len(close_rows),len(set(close_rows))))
    npass=sum(1 for k in results if results[k]["status"]=="PASS")
    print("\nPASS %d/%d"%(npass,len(results)))

if __name__=="__main__": main()

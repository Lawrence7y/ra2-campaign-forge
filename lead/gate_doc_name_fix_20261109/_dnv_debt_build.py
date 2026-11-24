# 独立复核员脚本 ⑤-A：从 payload 忠实还原指定发的 GATE_CODE（一字不改），落盘为纯 .py 供 Bash 直接跑
# 本脚本不 exec、不 eval、不调用子进程
import json, re, pathlib, hashlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WF = ROOT / ".zcode/workflow-runs"
OUTDIR = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_replay"
OUT = ROOT / "lead/gate_doc_name_fix_20261109/_dnv_debt_out.json"
GATE_HEAD = re.compile(r"const\s+GATE_CODE\s*=\s*\[")

def decode_js(s):
    out=[];i=0;mp={"n":"\n","t":"\t","r":"\r","b":"\b","f":"\f","v":"\v","\\":"\\",'"':'"',"'":"'","0":"\0"}
    while i<len(s):
        if s[i]=="\\" and i+1<len(s):
            c=s[i+1]
            if c=="u" and i+5<len(s):
                try: out.append(chr(int(s[i+2:i+6],16)));i+=6;continue
                except ValueError: pass
            out.append(mp.get(c,c));i+=2
        else: out.append(s[i]);i+=1
    return "".join(out)

def split_top_level(s):
    elems=[];buf=[];i=0;in_str=None
    while i<len(s):
        c=s[i]
        if in_str:
            buf.append(c)
            if c=="\\" and i+1<len(s): buf.append(s[i+1]);i+=2;continue
            if c==in_str: in_str=None
            i+=1;continue
        if c=='"' or c=="'": in_str=c;buf.append(c);i+=1;continue
        if c==",": elems.append("".join(buf));buf=[];i+=1;continue
        buf.append(c);i+=1
    if "".join(buf).strip(): elems.append("".join(buf))
    return elems

def reconstruct(e, vars_map):
    out=[];i=0
    while i<len(e):
        c=e[i]
        if c=='"' or c=="'":
            q=c;j=i+1;buf=[]
            while j<len(e):
                if e[j]=="\\" and j+1<len(e): buf.append(e[j:j+2]);j+=2;continue
                if e[j]==q: break
                buf.append(e[j]);j+=1
            out.append(decode_js("".join(buf)));i=j+1
        elif c=="+":
            k=i+1
            while k<len(e) and (e[k].isspace() or e[k]=="+"): k+=1
            st=k
            while k<len(e) and (e[k].isalnum() or e[k] in "_$"): k+=1
            out.append(vars_map.get(e[st:k], "0"*64)); i=k
        else: i+=1
    return "".join(out)

def gate_lines(lowered, vars_map):
    m=GATE_HEAD.search(lowered)
    if not m: return None
    st=m.end(); j=re.search(r"\]\s*\.join\s*\(",lowered[st:])
    if not j: return None
    return [reconstruct(e,vars_map) for e in split_top_level(lowered[st:st+j.start()])]

targets = {
 "dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs": ("counterpart_fix_20261109","COUNTERPART_FIX.md"),
 "dwfrun-15585c14-eff5-46e5-a910-1288e8310bc0.mjs": ("strict_exposure_20261109","STRICT_EXPOSURE.md"),
}
if OUTDIR.exists():
    import shutil; shutil.rmtree(OUTDIR)
OUTDIR.mkdir(parents=True)
rows=[]
for fname,(dom,main) in targets.items():
    text=(WF/fname).read_text(encoding="utf-8",errors="replace")
    m=re.search(r"export\s+const\s+payload\s*=\s*",text)
    obj,_=json.JSONDecoder().raw_decode(text,m.end())
    lowered=obj.get("lowered","")
    probe=gate_lines(lowered,{})
    vars_map={}
    tup=re.search(r"for\s+lbl,rel,pre\s+in\s*\[(.*?)\]\s*:", "\n".join(probe), re.S)
    if tup:
        for label,rel,var in re.findall(r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*([A-Za-z_]\w*)\s*\)",tup.group(1)):
            f=ROOT/rel
            vars_map[var]=hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
    lines=gate_lines(lowered,vars_map)
    src="\n".join(lines)
    py=OUTDIR/("replay_"+fname[:20]+".py")
    py.write_text(src,encoding="utf-8")
    compile(src,str(py),"exec")
    rows.append({"file":fname,"domain":dom,"main":main,"gate_py":py.as_posix(),
                 "gate_lines":len(lines),"has_docmax":any("DOC=max(" in ln for ln in lines),
                 "wd_line":next((ln for ln in lines if ln.startswith("wd=")),None),
                 "docmax_line":next((ln for ln in lines if "DOC=max(" in ln),None)})

# (b) mtime 对齐：36 处 run mtime vs 主件 mtime（只读 stat）
import datetime
meta=json.loads((ROOT/"lead/gate_doc_name_fix_20261109/_dnv_safe_and_names_out.json").read_text(encoding="utf-8"))
timing=[]
for r in meta["rows"]:
    run=WF/r["file"]; main=ROOT/"lead"/r["domain"]/(r["main"] or "?")
    rmt=run.stat().st_mtime if run.is_file() else 0
    mmt=main.stat().st_mtime if main.is_file() else 0
    timing.append({"file":r["file"],"domain":r["domain"],"main":r["main"],
                   "run_mtime":datetime.datetime.fromtimestamp(rmt).isoformat(sep=" ",timespec="seconds"),
                   "main_mtime":datetime.datetime.fromtimestamp(mmt).isoformat(sep=" ",timespec="seconds"),
                   "run_before_main":rmt<mmt})

# (c) 现值大小 / bare 计数 / 大小差
sizes=[]
for r in meta["rows"]:
    wd=ROOT/"lead"/r["domain"]
    mds=list(wd.glob("*.md")) if wd.is_dir() else []
    bare=[p for p in mds if not p.name.startswith("_")]
    mb=(wd/(r["main"] or "?")).stat().st_size if (wd/(r["main"] or "?")).is_file() else 0
    largest=max((p.stat().st_size for p in mds),default=0)
    side=max(((p.stat().st_size,p.name) for p in mds if p.name!=r["main"]),default=(0,""))
    sizes.append({"domain":r["domain"],"main":r["main"],"main_bytes":mb,"md_count":len(mds),
                  "bare_count":len(bare),"main_is_largest":mb==largest and mb>0,
                  "biggest_side_name":side[1],"biggest_side_bytes":side[0],"side_minus_main":side[0]-mb})

out={"replay_builds":rows,
     "timing_summary":{"sites":len(timing),"run_before_main":sum(1 for t in timing if t["run_before_main"])},
     "timing":timing,
     "size_summary":{"sites":len(sizes),
                     "main_is_largest_false":[s for s in sizes if not s["main_is_largest"]],
                     "bare_gt1":[{"domain":s["domain"],"bare_count":s["bare_count"]} for s in sizes if s["bare_count"]>1],
                     "max_side_minus_main":max(s["side_minus_main"] for s in sizes),
                     "min_side_minus_main":min(s["side_minus_main"] for s in sizes)},
     "sizes":sizes}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"replay_builds":rows,"timing_summary":out["timing_summary"],
                  "size_summary":{k:v for k,v in out["size_summary"].items() if k!="sites"}|{"sites":len(sizes)}},
                 ensure_ascii=False,indent=2))

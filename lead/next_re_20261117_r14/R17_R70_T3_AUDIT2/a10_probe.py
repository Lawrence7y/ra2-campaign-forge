import io,os,re
ROOT=r"D:\Project\ra2-campaign-forge"; R14=os.path.join(ROOT,"lead","next_re_20261117_r14")
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read(); lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
v513={r["fact_id"]:r for r in load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))}
f8=v513["F08"]; f9=v513["F09"]
print("F08 evidence_paths =", f8["evidence_paths"])
blob8=""
for it in f8["evidence_paths"].split(";"):
    f=re.sub(r"\([^()]*\)$","",it.strip())
    ap=os.path.join(ROOT,f.replace("\\","/"))
    if os.path.isfile(ap): blob8+=io.open(ap,encoding="utf-8",errors="replace").read().lower()
print("  'addref' in F08 pool ?", "addref" in blob8)
print("  '0x449440' in F08 pool ?", "0x449440" in blob8)
print("  '0x6f322f' in F08 pool ?", "0x6f322f" in blob8)
print()
print("F09 evidence_paths =", f9["evidence_paths"])
blob9=""
for it in f9["evidence_paths"].split(";"):
    f=re.sub(r"\([^()]*\)$","",it.strip())
    ap=os.path.join(ROOT,f.replace("\\","/"))
    if os.path.isfile(ap): blob9+=io.open(ap,encoding="utf-8",errors="replace").read().lower()
print("  'addref' in F09 pool ?", "addref" in blob9)
print()
print("=== 举例：F08 里 AddRef 是降级/误用对象吗 ===")
print("F08 lim:", f8["limitations"])
print()
print("=== 把 C1 的 4 条正则作用到 F08 / F09 / F40，结果 ===")
DP=[r"[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)",
    r"不得写成[「『]?([^，。；」』]{2,30})",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用"]
for fid in ("F08","F09","F40","F12","F31"):
    r=v513[fid]; out=[]
    for p in DP:
        for m in re.finditer(p, r["limitations"]): out.append((p[:18], m.group(1)))
    print(" ", fid, "->", out)
    print("     stmt[:150]:", r["statement"][:150].replace("\n"," "))

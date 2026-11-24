import io,os,re
ROOT = r"D:\Project\ra2-campaign-forge"
R14 = os.path.join(ROOT,"lead","next_re_20261117_r14")
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read()
    lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
def strip_anchor(item):
    if not item or item[-1] not in ")）": return item, None
    depth=0
    for i in range(len(item)-1,-1,-1):
        c=item[i]
        if c in ")）": depth+=1
        elif c in "(（":
            depth-=1
            if depth==0:
                if i==0: return item,None
                return item[:i], item[i+1:-1]
    return item,None
def split_items(ev):
    out,depth,cur=[],0,""
    for ch in ev:
        if ch in "（(": depth+=1
        elif ch in "）)": depth=max(0,depth-1)
        if ch==";" and depth==0: out.append(cur); cur=""; continue
        cur+=ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]
rows=load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
print("=== 全部 54 行的锚逐条解析 ===")
unresolved_all=[]
for r in rows:
    items=split_items(r["evidence_paths"])
    for it in items:
        f,a=strip_anchor(it)
        ap=os.path.join(ROOT,f.replace("\\","/"))
        ok=os.path.isfile(ap)
        if not ok: unresolved_all.append((r["fact_id"],f))
        print("  %-4s %s  file=%r ok=%s" % (r["fact_id"], "OK " if ok else "MISS", f, ok))
print()
print("unresolved:",unresolved_all)
print()
print("=== 关键：check_C3 只扫 statement，statement 里的 0x地址 vs 锚 pool ===")
print("   且：解析失败一律 return ([], unresolved) —— 只要有一个锚 miss，全行地址检查被跳过")
print()
# 统计每行锚数
import collections
cnt=collections.Counter(len(split_items(r["evidence_paths"])) for r in rows)
print("每行锚数分布:", dict(cnt))

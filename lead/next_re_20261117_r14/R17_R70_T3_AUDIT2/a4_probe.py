import io,os,re
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read()
    lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
rows=load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
DP = [
    r"[「『]([^」』]{2,40})[」』]\s*(?:是|属)[^。；]{0,20}(?:推断措辞|单源归因|行动裁决|推断)",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,40}(?:不随数字一并作已证|不入本条证据|未经字节证实|未经[^。；]{0,4}证实)",
    r"不得写成[「『]?([^，。；」』]{2,30})",
    r"[「『]([^」』]{2,40})[」』][^。；]{0,20}不得当[^。；]{0,10}用",
]
print("=== 逐模式统计 v5.13 命中 ===")
for k,p in enumerate(DP,1):
    n=0; where=[]
    for r in rows:
        for m in re.finditer(p, r["limitations"]):
            n+=1; where.append((r["fact_id"], m.group(0)[:70], m.group(1)))
    print("  P%d 命中 %d 次" % (k,n))
    for w in where: print("     ",w)
print()
print("=== 反例：这些 limitations 明显在给 'X 是推断措辞' 类信息，但 P1/P2 抓不到 ===")
cases = {
 "F40":"limitations 写 \"引用单源推断须与 F16 同引并带推断强度标注，不得写成事实。\"  + statement 里用了 token '事实'",
 "F06":"lim \"语义定性属静态推断、非已证\" —— 无引号、无「是/属 ... 推断措辞」形态",
 "F29":"lim \"0x6C2AC0 的「InterlockedIncrement」原先只是 §13.3 的推断措辞（...），现已由导入表证实\"  —— P1 要求「」后紧接 是/属，此处是「的」",
}
for fid,note in cases.items():
    r=[x for x in rows if x["fact_id"]==fid][0]
    print(" --",fid)
    print("   lim =", r["limitations"][:200])

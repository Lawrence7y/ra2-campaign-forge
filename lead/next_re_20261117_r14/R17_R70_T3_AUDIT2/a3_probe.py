import io,os,re
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read()
    lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
rows=load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
print("=== F12 limitations 全文中出现 '推断'/'已证'/引号 的次数 ===")
f12=[r for r in rows if r["fact_id"]=="F12"][0]
print("  '推断' in lim:", f12["limitations"].count("推断"))
print("  '已证' in lim:", f12["limitations"].count("已证"))
print()
def has_downgrade_semantics(lim):
    # 人工判据：limitations 是否在说「某短语属推断/未证实/快照」之类，即 C1 想抓的东西
    return bool(re.search(r"(推断措辞|推断|未证|未经|快照|不构成|不得写成|不是已证|非已证|不入本条证据)", lim))
n=sum(1 for r in rows if has_downgrade_semantics(r["limitations"]))
print("=== 按'宽松语义判据'看，limitations 里存在降级语义的行数 =", n, "/ 54 ===")
for r in rows:
    if has_downgrade_semantics(r["limitations"]):
        m=re.findall(r"(推断措辞|推断|未证|未经|快照|不构成|不得写成|不是已证|非已证|不入本条证据)", r["limitations"])
        print("  %-4s %s" % (r["fact_id"], sorted(set(m))))

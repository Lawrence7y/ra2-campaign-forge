import io,os,re,sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T3_AUDIT2")
import importlib.util
spec = importlib.util.spec_from_file_location("aud", r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T3_AUDIT2\a1_probe.py")
# reuse by re-defining (a1_probe prints on import) -> instead re-exec functions only via source split
src = io.open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T3_AUDIT2\a1_probe.py", encoding="utf-8").read()
head = src.split('V510=os.path.join')[0]
ns = {}
exec(head, ns)
load=ns["load"]; check_C1=ns["check_C1"]; check_C2=ns["check_C2"]; downgraded_tokens=ns["downgraded_tokens"]; is_duty_sentence=ns["is_duty_sentence"]; stmt_uses_hedged=ns["stmt_uses_hedged"]; key=ns["key"]
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
rows = load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
print("total rows:", len(rows))
print("grades:", collections_ := __import__("collections").Counter(r["grade"] for r in rows))
print()
print("=== D1. F12 token 取证 ===")
r12=[r for r in rows if r["fact_id"]=="F12"][0]
toks=downgraded_tokens(r12["limitations"])
print("  F12 downgraded_tokens =", toks)
for t in toks:
    print("  token %r -> duty=%s ; stmt_uses_hedged=%s" % (t, is_duty_sentence(r12["limitations"],t), stmt_uses_hedged(r12["statement"],t)))
print()
print("=== D2. F08 静默跳过取证 ===")
r8=[r for r in rows if r["fact_id"]=="F08"][0]
print("  F08 downgraded_tokens =", downgraded_tokens(r8["limitations"]))
print("  F08 is_duty_sentence('[已证]') =", is_duty_sentence(r8["limitations"],"[已证]"))
for seg in re.split(r"[；;。]", r8["limitations"]):
    if "[已证]" in seg: print("  containing seg:", seg)
print("  F08 statement contains '[已证]'? ", "[已证]" in r8["statement"])
print()
print("=== D3. C2 实测：把 HEDGE 词表换回 v1 的 4 词，看 v5.13 全表 C2 差异 ===")
for r in rows:
    if r["grade"]!="[已证]": continue
    hits=check_C2(r)
    if hits: print("   C2 hit:", r["fact_id"], hits)
print("  (以上为空则该谓词在 v5.13 上 0 命中)")
print()
print("=== D4. F06 是否为 C2 豁免路径的第 1 个 continue（强度标注） ===")
r6=[r for r in rows if r["fact_id"]=="F06"][0]
st=r6["statement"]
i=st.find("疑似")
ctx=st[max(0,i-30):i+30]
print("  ctx =", ctx)
print("  强度标注正则命中 =", bool(re.search(r"(静态|中等|偏强|偏弱|待裁|推断强度)", ctx)))
print("  paired spans =", ns["paired_quote_spans"](st))
print("  inside spans?  =", ns["inside_spans"](i, ns["paired_quote_spans"](st)))
print()
print("=== D5. C1 在 54 行上的完整中间量（逐 token） ===")
for r in rows:
    for t in downgraded_tokens(r["limitations"]):
        used,hedged,ctx=stmt_uses_hedged(r["statement"],t)
        print("  %s tok=%r used=%s hedged=%s duty=%s" % (r["fact_id"], t, used, hedged, is_duty_sentence(r["limitations"],t)))
print()
print("=== D6. limitations 里'是/属推断措辞'类句式的原文计数（说明闭集合漏了什么） ===")
pat_count=0
for r in rows:
    lim=r["limitations"]
    for m in re.finditer(r"(推断|推测|疑似|未经|未证|不构成|快照|历史|caption)", lim):
        pat_count+=1
print("  rough 提及数 =", pat_count)

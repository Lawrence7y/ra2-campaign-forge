import io,os,re
ROOT=r"D:\Project\ra2-campaign-forge"; R14=os.path.join(ROOT,"lead","next_re_20261117_r14")
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read(); lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
rows=load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
r8=[r for r in rows if r["fact_id"]=="F08"][0]
print("F08 GRADE  =", repr(r8["grade"]))
print("F08 statement 含 '0x' :", re.findall(r"0x[0-9A-Fa-f]{4,8}", r8["statement"]))
print("F08 '0x449440' in lim ?", "0x449440" in r8["limitations"])
print()
r24=[r for r in rows if r["fact_id"]=="F24"][0]
print("F24 statement 含 '0x' :", re.findall(r"0x[0-9A-Fa-f]{4,8}", r24["statement"]))
print()
print("=== D8 构造判别力实验：给 F29 注入一个不存在的地址，C3 会不会报 ===")
import sys
src=io.open(os.path.join(R14,"R17_R70_T3_AUDIT2","a1_probe.py"),encoding="utf-8").read()
# 用 checkC2.py 原样 check_C3
code=io.open(os.path.join(R14,"_r37","checkC2.py"),encoding="utf-8").read()
body=code.split("# ---------------- 判别力自证 ----------------")[0]
ns={}; exec(body, ns)
r29=[r for r in rows if r["fact_id"]=="F29"][0]
print("  F29 原样 :", ns["check_C3"](r29))
inj=dict(r29); inj["statement"]=r29["statement"]+" 另一个地址 0xDEADBEEF。"
print("  注入 0xDEADBEEF :", ns["check_C3"](inj))
inj2=dict(r29); inj2["evidence_paths"]=r29["evidence_paths"]+";lead\\NO_SUCH_FILE_XYZ.md(§1)"
print("  注入一个不存在的锚 :", ns["check_C3"](inj2))

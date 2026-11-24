import io,os,re
ROOT=r"D:\Project\ra2-campaign-forge"; R14=os.path.join(ROOT,"lead","next_re_20261117_r14")
def load(p):
    raw=io.open(p,encoding="utf-8",newline="").read(); lines=raw.split("\n"); h=lines[0].split("\t")
    return [dict(zip(h,l.split("\t"))) for l in lines[1:] if l.strip()]
rows=load(os.path.join(R14,"R17_R69_FACTINDEX_V513","FACT_INDEX.tsv"))
v510={r["fact_id"]:r for r in load(os.path.join(R14,"R17_R65_FACTINDEX_V510","FACT_INDEX.tsv"))}
print("=== F24 v5.10 limitations（正控来源）===")
print(v510["F24"]["limitations"])
print()
print("=== F24 v5.10 grade:", v510["F24"]["grade"])
print("=== F24 v5.10 statement 含 token '改指针无解、不再投卡' ?", "改指针无解、不再投卡" in v510["F24"]["statement"])
i=v510["F24"]["statement"].find("改指针无解")
print("      ctx:", v510["F24"]["statement"][max(0,i-40):i+80] if i>=0 else "(not found)")
print()
print("=== F29 v5.10 limitations ===")
print(v510["F29"]["limitations"])
print("=== F29 v5.10 statement 含 'InterlockedIncrement' ?", "InterlockedIncrement" in v510["F29"]["statement"])
i=v510["F29"]["statement"].find("InterlockedIncrement")
print("      ctx:", v510["F29"]["statement"][max(0,i-60):i+120] if i>=0 else "(not found)")

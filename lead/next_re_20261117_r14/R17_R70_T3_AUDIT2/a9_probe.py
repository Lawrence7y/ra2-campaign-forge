import io,os,re
ROOT=r"D:\Project\ra2-campaign-forge"; R14=os.path.join(ROOT,"lead","next_re_20261117_r14")
lines=io.open(os.path.join(R14,"R14_COMMON.md"),encoding="utf-8").read().split("\n")
print("=== 全文件检索 '救了我' / '当场' ===")
for i,l in enumerate(lines):
    if "救我" in l or "当场" in l: print("  ",i+1,l[:180])
print()
print("=== 检索 '五份' ===")
for i,l in enumerate(lines):
    if "五份" in l: print("  ",i+1,l[:180])

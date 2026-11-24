import io,os,re
ROOT=r"D:\Project\ra2-campaign-forge"; R14=os.path.join(ROOT,"lead","next_re_20261117_r14")
p=os.path.join(R14,"R14_COMMON.md")
lines=io.open(p,encoding="utf-8").read().split("\n")
print("R14_COMMON.md 行数 =", len(lines))
print("§2.24 出现行号:", [i+1 for i,l in enumerate(lines) if "2.24" in l][:10])
import hashlib
print("SHA256 =", hashlib.sha256(io.open(p,"rb").read()).hexdigest())
print()
for kw in ["反控当场救了我一次","五份里没有一份是空的","不是检查器错，是我引入了列间矛盾","判别力 FAIL"]:
    hits=[i+1 for i,l in enumerate(lines) if kw in l]
    print(kw, "-> 行", hits)
    for h in hits: print("   ", lines[h-1][:200])
print()
print("=== 检索 '判别力 FAIL' / '反控 = 1' 在本轮任何落盘文件里是否有第二处佐证 ===")
import glob
for f in glob.glob(os.path.join(R14,"_r3*","*.md"))+glob.glob(os.path.join(R14,"_r3*","*.txt"))+glob.glob(os.path.join(R14,"_r3*","*.py")):
    try: t=io.open(f,encoding="utf-8",errors="replace").read()
    except Exception: continue
    if ("判别力" in t and "FAIL" in t) or "反控 = 1" in t:
        print("  candidate:", os.path.basename(f), f)

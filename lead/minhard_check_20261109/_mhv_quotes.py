# -*- coding: utf-8 -*-
# 独立复核 ②：三组硬项原句逐字摘录（不采信撰写人摘录），并核对行号/逐字同文
import os, re, hashlib
ROOT = r"D:\Project\ra2-campaign-forge"
def lines(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")

TARGETS = [
 ("组①-a 处8", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
 ("组①-b 处9", "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
 ("组②-a #C1", "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
 ("组②-b #C2", "lead/ledger_appendix_20261108/_lad_tpl.md", 151),
 ("组③ #A3", "lead/s604_attribution_20261108/S604_ATTRIBUTION.md", 171),
]
cache = {}
print("== 1. 指定行原文（repr 逐字，含前后各一行） ==")
for tag, rel, ln in TARGETS:
    if rel not in cache:
        cache[rel] = lines(rel)
    L = cache[rel]
    print(f"--- {tag}: {rel}:{ln} ---")
    for k in (ln-1, ln, ln+1):
        if 1 <= k <= len(L):
            print(f"  [{k}] {L[k-1]!r}")
    print(f"  EXACT_LINE[{ln}] = {L[ln-1]!r}")

print("== 2. 两对逐字同文实算 ==")
a = cache[TARGETS[0][1]][122]
b = cache[TARGETS[1][1]][24]
c = cache[TARGETS[2][1]][214]
d = cache[TARGETS[3][1]][150]
e = cache[TARGETS[4][1]][170]
print("组① LEDGER:123 == _la_draft3:25 ?", a == b, " len:", len(a), len(b), " sha256:", hashlib.sha256(a.encode()).hexdigest())
print("组② LEDGER:215 == _lad_tpl:151 ?", c == d, " len:", len(c), len(d), " sha256:", hashlib.sha256(c.encode()).hexdigest())
print("组③ 单行 sha256:", hashlib.sha256(e.encode()).hexdigest(), "len:", len(e))

print("== 3. 与被核回件 _mh_MINHARD_CHECK.md 中的三段引文比对 ==")
rep = os.path.join(ROOT, "lead", "minhard_check_20261109", "_mh_MINHARD_CHECK.md")
R = open(rep, "r", encoding="utf-8", newline="").read().split("\n")
QUOTES = {
 "组①": 49,
 "组②": 66,
 "组③": 80,
}
for tag, ln in QUOTES.items():
    raw = R[ln-1]
    print(f"回件 :{ln} 原始 = {raw!r}")
    m = re.match(r"^> `(.+)`\s*$", raw)
    if m:
        q = m.group(1)
    else:
        print("  !! 引文行不服从预期格式，改用去首尾反引号")
        q = raw.lstrip("> ").strip().strip("`")
    src = {"组①": a, "组②": c, "组③": e}[tag]
    print(f"  摘录长度={len(q)} 原文长度={len(src)}  逐字相同? {q == src}")
    if q != src:
        # 逐字符定位首个差异
        for i, (x, y) in enumerate(zip(q, src)):
            if x != y:
                print(f"  首个差异 @{i}: 引文 {x!r} vs 原文 {y!r}")
                break
        else:
            qtail = repr(q[len(src):]) if len(q) > len(src) else ""
            stail = repr(src[len(q):]) if len(src) > len(q) else ""
            print("  前缀相同，长度差异：引文尾部", qtail, " 原文尾部", stail)

print("== 4. 行号错指检查：三句在各自文件内的全部出现位置 ==")
for tag, rel, ln in TARGETS:
    L = cache[rel]
    key = {"组①": "不能定位当年错误步骤", "组②": "不能定位当年错误步骤", "组③": "三选一**不可定谳**"}[tag[:2]]
    hits = [i for i, s in enumerate(L, 1) if key in s]
    print(f"{tag} 关键短语 {key!r} 在 {rel} 命中行 = {hits}；指定行 {ln} 命中? {ln in hits}")

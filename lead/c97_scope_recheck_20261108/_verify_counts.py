# _verify_counts.py — 复核员独立复算：supplement 四档计数 / 26 档点名 / 13 档分类 / 7b 对账
# 只读；不引用被核脚本 _c97_check.py 的任何输出；13 档名单取自上游 _dC_out.txt:80 实文。
import json
import re

BASE = "D:/Project/ra2-campaign-forge"
SUPP = BASE + "/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt"
DCOUT = BASE + "/lead/dtrigger_round2_20261107/_dC_out.txt"
CDBP = BASE + "/lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md"
CMP = BASE + "/lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md"
MJ = BASE + "/lead/dtrigger_compare_20261107/CRITERIA_METRICS.json"
FOUR = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r8"]


def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8", errors="replace")


print("== A. 26 档权威名单（CRITERIA_METRICS.json 顶层键，滤除非判据 R/U 项）==")
metrics = json.load(open(MJ, encoding="utf-8"))
all_keys = sorted(metrics.keys())
names26 = sorted(k for k in all_keys if re.match(r"^C[1-5]", k))
extra = [k for k in all_keys if k not in names26]
print("顶层键数 =", len(all_keys), "；判据键数 =", len(names26), "；非判据键 =", extra)
print("26 判据名单 =", ", ".join(names26))

print("== B. supplement 原件独立解析 ==")
rows = {}
dups = []
for i, line in enumerate(read(SUPP).split("\n"), 1):
    if "|" not in line:
        continue
    f = [z.strip() for z in line.split("|")]
    if len(f) >= 12 and re.match(r"^C[1-5]", f[0]) and f[1].isdigit():
        if f[0] in rows:
            dups.append(f[0])
        rows[f[0]] = (i, int(f[1]), int(f[6]), int(f[8]), f[9])
print("表行数 =", len(rows), "重复 id =", dups if dups else "无")
for t in FOUR:
    i, n, g50, g100, pct = rows[t]
    print("  %-10s :%2d nTrig=%2d >50=%2d >=100=%2d 占比=%s -> ge100==nTrig = %s"
          % (t, i, n, g50, g100, pct, g100 == n))
print("  四档 4/4 全部 ge100==nTrig =", all(rows[t][3] == rows[t][1] for t in FOUR))

print("== C. 26 档全集 × CRITERIA_COMPARE.md:146（原始 / 斜杠展开两形态）==")
cmp_lines = read(CMP).split("\n")
l146 = cmp_lines[145]
l146x = l146.replace("`C3-r4/r8`", "`C3-r4` `C3-r8`")
raw_named = [t for t in names26 if t in l146]
exp_named = [t for t in names26 if t in l146x]
print("  原始点名 =", raw_named, "数 =", len(raw_named))
print("  展开后点名 =", exp_named, "数 =", len(exp_named), "恰为四档 =", sorted(exp_named) == sorted(FOUR))

print("== D. 13 档名单取 _dC_out.txt 实文 + 分类 vs CD_BREAKPOINTS.md:80-82 ==")
dc = read(DCOUT).split("\n")
m80 = None
for idx, line in enumerate(dc, 1):
    mm = re.search(r"71 格涉及的判据 = (\d+) 档[:：]\s*(.+)$", line)
    if mm:
        m80 = (idx, int(mm.group(1)), [x.strip() for x in mm.group(2).split(",")])
thirteen = m80[2]
print("  _dC_out.txt:%d 名单数 = %d，唯一 = %s" % (m80[0], m80[1], len(set(thirteen)) == len(thirteen)))
full, partial, norow = [], [], []
for t in thirteen:
    if t not in rows:
        norow.append(t)
    elif rows[t][3] == rows[t][1]:
        full.append(t)
    else:
        partial.append(t)
print("  全部 =", len(full), full)
print("  部分 =", len(partial), partial)
print("  无行 =", len(norow), norow)
cdbp = read(CDBP).split("\n")
cell_full = cdbp[79].split("|")[3].strip()
cell_partial = cdbp[80].split("|")[3].strip()
cell_norow = cdbp[81].split("|")[3].strip()
row_full = dict((a.strip("、"), (int(b), int(c))) for a, b, c in
                re.findall(r"([A-Za-z0-9][\w.-]*)\((\d+)/(\d+)\)", cell_full))
row_partial = dict((a.strip("、"), (int(b), int(c))) for a, b, c in
                   re.findall(r"([A-Za-z0-9][\w.-]*)\((\d+)/(\d+)\)", cell_partial))
row_norow = [x.strip().strip("|").strip() for x in cell_norow.split("、")]
mine_full = dict((t, (rows[t][3], rows[t][1])) for t in full)
mine_partial = dict((t, (rows[t][3], rows[t][1])) for t in partial)
print("  CD_BREAKPOINTS.md:80 全部档 =", row_full, "↔ 本算一致 =", row_full == mine_full)
print("  CD_BREAKPOINTS.md:81 部分档 ↔ 本算一致 =", row_partial == mine_partial)
print("  CD_BREAKPOINTS.md:82 无行档 ↔ 本算一致 =", sorted(row_norow) == sorted(norow))

print("== E. _dC_out.txt 7b 段 ↔ supplement 原件对账 ==")
seven_b = {}
for idx, line in enumerate(dc, 1):
    mm = re.match(r"^\s{4}(\S+)\s+supplement_out\.txt:\s*(\d+)\s+nTrig=\s*(\d+)\s+>50=\s*(\d+)（(.+?)）\s+>=100=\s*(\d+)\s*$", line)
    if mm:
        seven_b[mm.group(1)] = (idx, int(mm.group(2)), int(mm.group(3)), int(mm.group(4)), int(mm.group(6)))
bad = []
for t, (oi, si, n, g50, g100) in sorted(seven_b.items()):
    if t not in rows:
        bad.append((t, "supplement 缺行"))
    else:
        i, n2, g502, g1002, pct = rows[t]
        if (i, n2, g502, g1002) != (si, n, g50, g100):
            bad.append((t, rows[t], (si, n, g50, g100)))
print("  7b 可解析行数 =", len(seven_b), sorted(seven_b))
print("  逐档不一致 =", bad if bad else 0)

print("== F. 锚口径自报（supplement :33/:44-45）==")
s = read(SUPP).split("\n")
print("  supp:33 =", s[32].strip())
print("  supp:44 =", s[43].strip())
print("  supp:45 =", s[44].strip())
print("  :44-45 合并含「无法从语料测得」 =", "无法从语料测得" in (s[43] + s[44]),
      "；:45 含「下界」 =", "下界" in s[44])

print("== G. _dC_out.txt:147/:148 实文 ==")
print("  :147 =", dc[146].strip())
print("  :148 =", dc[147].strip())

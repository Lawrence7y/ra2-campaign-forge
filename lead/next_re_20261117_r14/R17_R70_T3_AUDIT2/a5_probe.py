def strip_anchor(item):
    if not item or item[-1] not in ')' : 
        if not item or item[-1] not in ")）": return item, None
    depth = 0
    for i in range(len(item)-1, -1, -1):
        c = item[i]
        if c in ")）": depth += 1
        elif c in "(（":
            depth -= 1
            if depth == 0:
                if i == 0: return item, None
                return item[:i], item[i+1:-1]
    return item, None
def split_items(ev):
    out, depth, cur = [], 0, ''
    for ch in ev:
        if ch in "（(": depth += 1
        elif ch in "）)": depth = max(0, depth-1)
        if ch == ";" and depth == 0:
            out.append(cur); cur = ""; continue
        cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]
tests = [
 "lead/next_re_20261117_r14/R14_COMMON.md(§2.10 / 一 / (a′))",
 "lead/LEAD_LOCK(追加·2026-11-20 14:1x·r15 第 70-78 轮 段)",
 "lead/next_re_20261117_r14/COVERAGE/PANEL.md(M71 披露)",
 "lead/next_re_20261117_r14/BOARD_ARCHIVE.md(R17 第 16 轮 段)",
 "lead/next_re_20261117_r14/R14_COMMON.md(§16.1 判据)",
 "lead/next_re_20261117_r14/R14_COMMON.md(§2.9一/§2.10一/二)",
 "lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md",
 "lead/next_re_20261117_r14/COVERAGE/PANEL.md",
]
for t in tests:
    f,a = strip_anchor(t)
    print(repr(t))
    print("   -> file=%r anchor=%r" % (f,a))
print()
print("=== 边界：锚里本身含 ';' 或含 ')' 的怪例 ===")
for t in ["a.md(§2.9; 二)", "a(1)(2)", "a.md(f(x))"]:
    print(repr(t), "->", strip_anchor(t))

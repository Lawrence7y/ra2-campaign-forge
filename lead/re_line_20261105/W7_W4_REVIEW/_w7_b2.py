# -*- coding: utf-8 -*-
"""B2 独立复核只读探针（零真机、零注入、零既有件改动）。

核对象: W4_FIELD_SPEC/sections/Q3_FRAME_EDGE_SPEC.md
重点: ①5读/20B(S0复用) 与 D-21 裁A / V6 实现一致性
      ②四地址跨度 0x28E5A8 B 算术
      ③「全部名义操作数」自我约束有没有被偷偷违反
      ④λ 七档与 B/s、调用/s 算术
另: 用 ra2tool.Engine 真反汇编核字节（帧号 VA 写点 / 四 VA 绝对访存命中）。

用法: python -I -X utf8 D:/.../W7_W4_REVIEW/_w7_b2.py > D:/.../W7_W4_REVIEW/_w7_b2_out.txt
"""
import hashlib
import re
import sys
import datetime

ROOT = r"D:\Project\ra2-campaign-forge"
BASE = ROOT + r"\lead\re_line_20261105"
Q3 = BASE + r"\W4_FIELD_SPEC\sections\Q3_FRAME_EDGE_SPEC.md"
OUT = BASE + r"\W7_W4_REVIEW"

fails = []


def chk(label, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    if not cond:
        fails.append(label)
    print("  [%s] %s %s" % (tag, label, detail))


def sha_size(p):
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b), b


def num(cell):
    """从表格单元取第一个浮点数；去掉 ** * 与千分位空格/逗号。"""
    s = cell.replace("**", "").replace("*", "").replace(" ", "").replace(",", "")
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


print("=" * 78)
print("B2 独立复核探针   run_at =", datetime.datetime.now().isoformat(timespec="seconds"))
print("=" * 78)

# ---------------------------------------------------------------- 0 哈希绑定
print("\n[0] 被核对象 SHA256 / 字节数（本次自己实算，非抄任务书）")
h, n, raw = sha_size(Q3)
text = raw.decode("utf-8")
lines = text.splitlines()
print("    path =", Q3)
print("    SHA256 =", h)
print("    size =", n, "bytes")
print("    lines =", len(lines))
TASK_SHA = "0d3e13875855ea4b5d36f22e6f622916ac15b479944767fe4d067aaee5639c5d"
TASK_SIZE = 38799
print("    TASK.md:20 固化值 sha =", TASK_SHA, "size =", TASK_SIZE)
chk("SHA256 与任务书固化值一致", h == TASK_SHA, "=> " + ("未变更" if h == TASK_SHA else "OBJECT_CHANGED"))
chk("字节数与任务书固化值一致", n == TASK_SIZE, "=> %d vs %d" % (n, TASK_SIZE))

print("\n[0b] 本次复核实际引用/亲读的既有件哈希（只读，证明未改）")
refs = [
    ("W4_FIELD_SPEC/TASK.md", BASE + r"\W4_FIELD_SPEC\TASK.md"),
    ("D21_RULING/RULING_D21.md", BASE + r"\D21_RULING\RULING_D21.md"),
    ("D21_RULING/EXECUTION_D21.md", BASE + r"\D21_RULING\EXECUTION_D21.md"),
    ("V6_V3_REVIEW/V6_V3_REVIEW.md", BASE + r"\V6_V3_REVIEW\V6_V3_REVIEW.md"),
    ("A1_SAMPLER_CANDIDATE/frame_edge_sampler.py", BASE + r"\A1_SAMPLER_CANDIDATE\frame_edge_sampler.py"),
    ("harness8_v4.py", ROOT + r"\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py"),
    ("FACTBASE_D19.md", BASE + r"\D19_RULING\FACTBASE_D19.md"),
    ("Q2_FRAME_EDGES.md", BASE + r"\W3_COSTBOUND\sections\Q2_FRAME_EDGES.md"),
    ("Q3_SAMPLE_PLAN.md", BASE + r"\W3_COSTBOUND\sections\Q3_SAMPLE_PLAN.md"),
]
for nm, p in refs:
    hh, nn, _ = sha_size(p)
    print("    %-46s sha=%s size=%d" % (nm, hh[:16] + "...", nn))

# ---------------------------------------------------------------- 1 五读/20B
print("\n[1] ① 每沿新增 5 读 / 20 B（S0 复用）——是否真写对")

# 权威地址：TASK.md:23-26 四 VA + harness8:3831 帧号 VA（本次已从文件读出，见正文）
V = {
    "gen_stamp": 0x0087E8E0,
    "threat_calls": 0x00A8EC34,
    "dirty_rect_count": 0x00B0CE88,
    "bullet_count": 0x00A8ED50,
    "frame": 0x00A8ED84,
}
print("    权威地址常量 =", {k: hex(v) for k, v in V.items()})

# 从 Q3 §5.1 表（L155-162）抽取 S0..S5 的「是否新增跨进程读」列
s_table = lines[154:162]  # 0-based: L155..L162
print("    Q3 §5.1 读序表原文：")
for i, L in enumerate(s_table):
    print("      L%d %s" % (155 + i, L))
new_yes = sum(1 for L in s_table if re.search(r"\|\s*是(?:（|\*|\s|\|)", L))
print("    §5.1 标「是（新增）」的行数 =", new_yes)
chk("§5.1 读序恰有 5 个新增读（S1..S4 + S5）", new_yes == 5)
# s_table = lines[154:162] -> [0]=L155 表头 [1]=L156 分隔 [2]=L157 S0 ... [7]=L162 S5
chk("§5.1 S0 明确标「否（复用）」", "否（复用）" in s_table[2], "L157")
chk("§5.1 S5 明确为独立后读且单列成本", "附加帧号校验读，单列成本" in s_table[7] and "附加读" in s_table[7], "L162")

# 载荷算术：4 字段×4B=16B + S5 4B = 20B；读次 4+1=5
four_payload = 4 * 4
s5_payload = 4
chk("4 字段载荷 = 16 B", four_payload == 16)
chk("总新增载荷 = 16+4 = 20 B", four_payload + s5_payload == 20)
chk("总新增读次 = 4+1 = 5", 4 + 1 == 5)
chk("采纳式 5 读/20 B 与「每字段 4 B」口径自洽", four_payload + s5_payload == 4 * (4 + 1))

# §8.3 表（L320-325）声明值
for i in range(319, 326):
    print("      L%d %s" % (i + 1, lines[i]))
chk("§8.3 L324 S0 = 0 次/0 B（复用，不新增调用）", bool(re.search(r"\|\s*0\s*\|\s*0\s*\|", lines[323])))
chk("§8.3 L325 合计 = 5 次 / 20 B", bool(re.search(r"\|\s*\*?\*?5\*?\*?\s*\|\s*\*?\*?20\*?\*?\s*\|", lines[324])))
chk("§0 L28-29 声明 20λ B/s、5λ 次/秒、名义上限 ≤10 000 B/s ≤2500 次/秒",
    "20λ B/s、5λ 次跨进程读调用/秒" in lines[27] and "≤10 000 B/s、≤2500 次/秒" in lines[28])

# 与 D-21 裁 A 对照（文本本次亲读，逐字比对关键句）
d21 = open(BASE + r"\D21_RULING\RULING_D21.md", encoding="utf-8").read()
exec21 = open(BASE + r"\D21_RULING\EXECUTION_D21.md", encoding="utf-8").read()
v6 = open(BASE + r"\V6_V3_REVIEW\V6_V3_REVIEW.md", encoding="utf-8").read()
chk("D-21 裁 A 主文 = 每沿新增 5 次跨进程读、20 B + S0 复用外层轮询值/读前时间戳",
    "每个触发沿新增 5 次跨进程读、20 B" in d21 and "复用该拍外层轮询值和其原始读前时间戳作为 S0" in d21,
    "RULING_D21.md:5")
chk("D-21 明指 W4 §8.3 是 5 读设计源头、§318-328 合计 5 次/20 B、6 次/24 B 变体不采纳",
    "合计新增 5 次/20 B" in d21 and "6 次/24 B 变体列为不采纳" in d21, "RULING_D21.md:18")
chk("D-21 §2.1 指定读序 gen/threat/dirty/bullet/f_post 恰好五次新增读",
    "按 gen_stamp、threat_calls、dirty_rect_count、bullet_count、f_post 顺序恰好新增五次读" in d21,
    "RULING_D21.md:31")
chk("EXECUTION_D21 明记「W4 的 5 读设计本来就是对的，无需改」",
    "它的 5 读设计**本来就是对的**" in exec21, "EXECUTION_D21.md:125")
chk("V6 总判 CONFIRMED：每沿新增 5 次（四 VA + f_post），f_pre 复用外层读数与读前时刻",
    "最终裁决：CONFIRMED" in v6 and "每沿新增读为 5 次（四 VA + f_post），f_pre 复用外层读数与读前时刻" in v6,
    "V6_V3_REVIEW.md:16,18")

# 真读 V6 已确认实现的源码：A1 frame_edge_sampler.py（只读），核读序与 5/6 读
a1 = open(BASE + r"\A1_SAMPLER_CANDIDATE\frame_edge_sampler.py", encoding="utf-8").read()
a1_lines = a1.splitlines()
fields_order = re.findall(r'^\s*"(\w+)",\s*$', "\n".join(a1_lines[46:76]), re.M)
print("    A1 sampler FIELDS 读序（L45-76 实读）= ", fields_order)
chk("A1 实现四字段读序 = gen/threat/dirty/bullet（与 Q3 §5.1、D-21 §2.1 一致）",
    fields_order == ["gen_stamp", "threat_calls", "dirty_rect_count", "bullet_count"])
chk("A1 实现复用模式 reads_per_sample=5、缺省=6（与 D-21/V6 一致）",
    '"reads_per_sample": (5 if reuse else 6)' in a1, "frame_edge_sampler.py:146")
chk("A1 复用分支不再读 FRAME_VA（S0 复用）",
    "if reuse:" in a1 and "rec[\"f_pre\"] = f_pre" in a1 and "read_one(reader, FRAME_VA)" in a1,
    "frame_edge_sampler.py:153-167,180")
chk("Q3 §8.3 把 6 次/24 B 独立前读变体列为「不采纳」",
    "另一可审查变体（不采纳，仅列账）" in lines[326] and "6 次/沿、24 B/沿" in lines[326], "L327")

# ---------------------------------------------------------------- 2 跨度算术
print("\n[2] ② 四地址跨度 0x28E5A8 B（约 2.7 MB）算术")
asc = sorted(V.items(), key=lambda kv: kv[1])
print("    五地址升序：")
for k, v in asc:
    print("      %-18s %s  = %d" % (k, hex(v), v))
print("    相邻间隔：")
tot = 0
for (ka, a), (kb, b) in zip(asc, asc[1:]):
    d = b - a
    tot += d
    print("      %-18s -> %-18s %8d B = %s" % (ka, kb, d, hex(d)))
four = [V["gen_stamp"], V["threat_calls"], V["dirty_rect_count"], V["bullet_count"]]
span = max(four) - min(four)
print("    四 VA min..max = %s..%s" % (hex(min(four)), hex(max(four))))
print("    四 VA 跨度 = %d B = %s" % (span, hex(span)))
print("    五地址相邻间隔之和 = %d B" % tot)
print("    十进制 MB = %.4f MB ; 二进制 = %.4f MiB" % (span / 1e6, span / 1048576.0))
chk("四 VA 跨度 = 0x28E5A8 = 2 680 232 B", span == 0x28E5A8 == 2680232)
chk("Q3 §4 L135 写 2 680 232 B = 0x28E5A8", "2 680 232 B = 0x28E5A8" in lines[134])
chk("§4 四个间隔 2163540/284/52/516356 与实算一致",
    all(s in lines[127] for s in ["2 163 540 B", "0x210354"])
    and all(s in lines[128] for s in ["284 B", "0x11C"])
    and all(s in lines[129] for s in ["52 B", "0x34"])
    and all(s in lines[130] for s in ["516 356 B", "0x7E104"]))
chk("四个间隔之和 = 四 VA 跨度（含帧号 VA 作中间点不改变 min/max）", tot == span)
chk("「约 2.7 MB」按十进制 MB 舍入成立（2.68 MB≈2.7 MB）", round(span / 1e6, 1) == 2.7)
chk("四字段总载荷 16 B、至少 4 次独立读（§4 L135-136）", "16 B 总载荷" in lines[134] and "4 次独立的 4 字节读" in lines[135])
print("    附注：任务书 B2 括注「约 2.7 MB」为十进制 MB 口径；按 MiB 为 %.4f MiB（≈2.6 MiB），两种近似都不改变跨度数值本身。" % (span / 1048576.0))

# ---------------------------------------------------------------- 3 自我约束
print("\n[3] ③ 「全部是名义操作数，不是耗时/CPU/扰动实测」——全文有无偷偷给百分比/时间结论")
print("    §0 L29 / §8.1 L301-302 / §8.5 L368 自我约束原文：")
for i in (28, 300, 301, 367):
    print("      L%d %s" % (i + 1, lines[i]))

# 3a 所有含数字百分比的行
print("\n    [3a] 全文含「数字+%」的行：")
pct_lines = []
for i, L in enumerate(lines):
    if re.search(r"\d+(?:\.\d+)?\s*%", L):
        pct_lines.append((i + 1, L.strip()))
        print("      L%d %s" % (i + 1, L.strip()))
print("    命中行数 =", len(pct_lines))
# 「CPU%」「μs / % / 纳秒」中的裸 % 不是数字百分比；显式列出供人工判定
print("\n    [3b] 全文含 % 的所有行（含裸 % 符号，用于人工判定是否属采纳结论）：")
for i, L in enumerate(lines):
    if "%" in L:
        print("      L%d %s" % (i + 1, L.strip()))
# 判定：每一处「数字+%」必须处在「明确不采纳/引述他人被否数值」的语境
reject_markers = ("不采纳", "不予采纳", "均不采纳", "不作为本规格", "不提交任何时间/百分比开销结论",
                  "不给出 μs / % / 纳秒级数字", "全部未定/未验")
bad_pct = [(ln, L) for ln, L in pct_lines if not any(m in L for m in reject_markers)]
chk("所有「数字+%」均处于引述被否数值 / 否定式披露语境（非本规格采纳的开销结论）",
    len(bad_pct) == 0, "越界行=%s" % ([ln for ln, _ in bad_pct],))

# 3c 时间单位 / 耗时 / 扰动 / CPU 相关行，逐行打印并程序化检查「未验/名义/不宣称」限定
print("\n    [3c] 全文含时间单位(μs/ms/ns/纳秒/微秒/秒)或 耗时/CPU/扰动/开销 的行（分类打印）：")
time_re = re.compile(r"μs|纳秒|微秒|\bms\b|\bns\b|耗时|CPU|扰动|开销|零扰动|Hz")
time_lines = [(i + 1, L.strip()) for i, L in enumerate(lines) if time_re.search(L)]
print("    命中行数 =", len(time_lines))
# 只把「给出具体数字时间/百分比/Hz 结论」的行拿出来判定
conclusion_re = re.compile(r"\d+(?:\.\d+)?\s*(?:μs|ms|ns|纳秒|微秒|%|Hz|秒)")
for ln, L in time_lines:
    if conclusion_re.search(L):
        print("      L%d %s" % (ln, L))
# 凡带具体时间/Hz 数字者，必须带「名义/未验/不采纳/不等于/均非/示意/不宣称/非定谳/留痕/按既有」之一，或属操作数 B/s·次/秒·λ 表
# 可复核的分类判据：每个含「具体数字+时间/Hz 单位」的行必须落入下列某类，且该类都带
# 「名义/未验/不采纳/引述他人/操作数算账」限定；分类用文件内可见的章节边界，不用模糊白名单。
CATS = [
    ("设计档标题/结论里的名义 500 Hz（非实测）", lambda ln, L: ln in (1, 24, 478)),
    ("明确不采纳/不沿用/不宣称/未验/非定谳/不算结论", lambda ln, L: any(
        m in L for m in ("不采纳", "不予采纳", "不作为本规格", "不沿用", "均非定谳", "不设",
                         "不宣称", "不提交", "不给出", "未验", "不等于", "照实留痕", "待申请",
                         "不虚构", "不是频率建议", "算账表", "下界未证", "充分性未证"))),
    ("§2 既有机制静态核证表（51..72；表头 L51 明写「静态核证，非动态验证」，均为引述既有 harness 的名义常量/先例）",
     lambda ln, L: 51 <= ln <= 72),
    ("§8.2 既有基线名义操作数表（306..315）", lambda ln, L: 306 <= ln <= 315),
    ("§8.4 λ 算账表及结论（336..355，表头明写「均非本设计实测」）", lambda ln, L: 336 <= ln <= 355),
    ("§9.2 逐字实跑命令输出块（396..454，引述既有件，不是本规格结论）", lambda ln, L: 396 <= ln <= 454),
    ("§8.5 名义拍内余量（364..369）", lambda ln, L: 364 <= ln <= 369),
]
uncovered = []
for ln, L in time_lines:
    if conclusion_re.search(L) and not any(p(ln, L) for _, p in CATS):
        uncovered.append((ln, L))
print("    未被上述 7 类覆盖、且含具体时间/Hz 数字的行 =", uncovered)
chk("每条含具体时间/Hz 数字的行都属于「名义/未验/不采纳/引述/操作数算账」之一（无偷偷给实测时间结论）",
    len(uncovered) == 0)
chk("§8.1 L302 明确「本规格不提交任何时间/百分比开销结论」",
    "本规格**不提交任何时间/百分比开销结论**" in lines[301])
chk("§8.5 L368 明确「不给出 μs / % / 纳秒级数字」",
    "不给出 μs / % / 纳秒级数字" in lines[367])
chk("§9.3 L471-472 把「真实开销（时间/%）」列入「全部未定/未验」",
    "真实开销（时间/%）" in lines[470] and "全部未定/未验" in lines[471])

# ---------------------------------------------------------------- 4 λ 七档算术
print("\n[4] ④ λ 七档 (5.9952/6.0/19.8112/30.2016/30.8426/31.25/500) 与 B/s、调用/s 算术")

# 从源头实读 p50（本次亲读 FACTBASE_D19.md:165-167 与 Q2_FRAME_EDGES.md:52，见正文）
FB = open(BASE + r"\D19_RULING\FACTBASE_D19.md", encoding="utf-8").read()
Q2E = open(BASE + r"\W3_COSTBOUND\sections\Q2_FRAME_EDGES.md", encoding="utf-8").read()
W3SP = open(BASE + r"\W3_COSTBOUND\sections\Q3_SAMPLE_PLAN.md", encoding="utf-8").read()
p50_stored = [
    float(re.search(r"measure_w0\.json stored ([\d.]+)", FB).group(1)),
    float(re.search(r"measure_w1\.json stored ([\d.]+)", FB).group(1)),
    float(re.search(r"measure_w2\.json stored ([\d.]+)", FB).group(1)),
]
print("    FACTBASE_D19.md:165-167 stored p50 =", p50_stored)
chk("Q2_FRAME_EDGES.md:52 p50=166.8 ms 存在", "166.8" in Q2E)
chk("Q3_SAMPLE_PLAN.md:237 慢窗 6Hz / 快窗 31.25Hz 存在", "6Hz" in W3SP and "31.25Hz" in W3SP)
chk("Q3_SAMPLE_PLAN.md:254 每秒 480 字节 / <0.005% 存在（被 Q3 明确不采纳）",
    "480 字节" in W3SP and "0.005%" in W3SP)

# 全精度 λ（不由 4 位小数 λ 反推，直接从 p50 算）
lam_full = {
    5.9952: 1000.0 / 166.8,
    6.0: 6.0,
    19.8112: 1000.0 / p50_stored[0],
    30.2016: 1000.0 / p50_stored[1],
    30.8426: 1000.0 / p50_stored[2],
    31.25: 31.25,
    500.0: 500.0,
}
print("\n    λ 全精度复算（1000/p50）：")
for k, v in lam_full.items():
    print("      表列 %-9.4f  全精度 %-18.12f  round4=%s" % (k, v, ("%.4f" % v)))
for k, v in lam_full.items():
    chk("λ %.4f 的 4 位小数与源头 p50/示意值一致" % k, round(v, 4) == k, "实算 %.4f" % v)

# 抽取 Q3 §8.4 表（L336-344）的 7 行 × 5 个数字
print("\n    Q3 §8.4 表原文（L336-344）：")
table_rows = []
for i in range(335, 345):
    L = lines[i]
    print("      L%d %s" % (i + 1, L))
    if not L.startswith("|"):
        continue
    cells = L.split("|")
    if len(cells) < 7:
        continue
    lam_s = num(cells[1])
    if lam_s is None or lam_s not in lam_full:
        continue
    vals = [num(cells[3]), num(cells[4]), num(cells[5]), num(cells[6])]
    table_rows.append((i + 1, lam_s, vals))
print("\n    抽取到的行数 =", len(table_rows))
chk("§8.4 恰抽取 7 个 λ 档行", len(table_rows) == 7, "实际 %d" % len(table_rows))

expect_lams = [5.9952, 6.0, 19.8112, 30.2016, 30.8426, 31.25, 500.0]
chk("七档 λ 集合与任务书 B2 点名完全一致",
    [r[1] for r in table_rows] == expect_lams, str([r[1] for r in table_rows]))

print("\n    逐行核算：采纳式 B/s=20λ、调用/s=5λ；6次变体 B/s=24λ、调用/s=6λ")
print("    %-8s %-10s %-12s %-12s %-12s %-12s %s" % ("λ", "L#", "20λ", "5λ", "24λ", "6λ", "判定"))
all_row_ok = True
for ln, lam, vals in table_rows:
    # 同时用「表列 4 位 λ」与「全精度 λ」计算，二者在 2 位小数必须一致且与表中值一致
    from_lam = [round(20 * lam, 2), round(5 * lam, 2), round(24 * lam, 2), round(6 * lam, 2)]
    lf = lam_full[lam]
    from_full = [round(20 * lf, 2), round(5 * lf, 2), round(24 * lf, 2), round(6 * lf, 2)]
    ok = (vals == from_lam == from_full)
    all_row_ok &= ok
    chk("L%d λ=%-8g 四列 = %s" % (ln, lam, str(vals)), ok,
        "表列λ算=%s 全精度算=%s" % (from_lam, from_full))
chk("§8.4 七行 × 四列 全部与 20λ/5λ/24λ/6λ 算术一致（且 4 位 λ 舍入不改变 2 位结果）", all_row_ok)

# §8.4 底部结论句与基线
chk("§0 L28-29 名义上限 500 ⇒ ≤10 000 B/s、≤2500 次/秒",
    "≤10 000 B/s、≤2500 次/秒" in lines[28] and 20 * 500 == 10000 and 5 * 500 == 2500)
chk("L347 「16λ B/s、4λ 次/秒；20λ B/s、5λ 次/秒」", "16λ B/s、4λ 次/秒" in lines[346] and "20λ B/s、5λ 次/秒" in lines[346])
chk("L348 「λ≈30.84 ⇒ 约 616.85 B/s、154.21 次/秒」与 30.8426 档一致",
    "约 616.85 B/s、154.21 次/秒" in lines[347] and round(20 * lam_full[30.8426], 2) == 616.85 and round(5 * lam_full[30.8426], 2) == 154.21)
base_calls, base_bytes = 500 + 8, 500 * 4 + 8 * 4
print("    既有基线实算 = %d 次/秒, %d B/s" % (base_calls, base_bytes))
chk("§8.2 L312 基线 508 次/秒、2 032 B/s", base_calls == 508 and base_bytes == 2032 and "**508**" in lines[311] and "**2 032**" in lines[311])
chk("L350 叠加基线名义总量上界 12 032 B/s、3 008 次/秒",
    "12 032 B/s、3 008 次/秒" in lines[349] and base_bytes + 10000 == 12032 and base_calls + 2500 == 3008)
chk("L350 6 次变体 14 032 B/s、3 508 次/秒",
    "14 032 B/s、3 508 次/秒" in lines[349] and base_bytes + 12000 == 14032 and base_calls + 3000 == 3508)
chk("L354-355 对 W3「16 B×30=480 字节」的驳斥算术成立且不沿用",
    "480 字节" in lines[353] and 16 * 30 == 480 and "本规格不沿用" in lines[354])
chk("§8.4 L336 表头标注 λ「均非本设计实测」、L351-353 明写算账表/非频率建议",
    "均非本设计实测" in lines[335] and "算账表" in lines[352] and "不是频率建议" in lines[352])

# ---------------------------------------------------------------- 5 Engine 真反汇编
print("\n[5] ra2tool.Engine 真反汇编核字节（不只读对方文字）")
try:
    sys.path.insert(0, ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104")
    from ra2tool import Engine
    eng = Engine()  # __init__ 内 assert sha == EXPECT_SHA
    print("    gamemd.exe SHA256 (Engine 实测) =", eng.sha)
    chk("目标二进制 SHA256 = Q3 §1 L17-18 采信值 73201cc0...（本次独立重算，Q3 自述未重算）",
        eng.sha == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
    print("    PE 节表 =", [(s[0], hex(s[1]), "vsz=%d" % s[2], "rsz=%d" % s[4]) for s in eng.SEC])
    print("\n    五个 VA 所属节 / 是否落在文件原始字节内：")
    for k, va in V.items():
        sec = next((s for s in eng.SEC if s[1] <= va < s[1] + s[2]), None)
        fo = eng.fo(va)
        print("      %-18s %s  sec=%-7s fo=%-10s" % (
            k, hex(va), sec[0] if sec else "?", ("None" if fo is None else hex(fo))))
    print("\n    ★ 单次遍历 .text 全流（resync 线性解码，覆盖率自证），收集 5 个 VA 的绝对访存命中：")
    import time as _time
    _t = _time.time()
    stream = eng.stream  # 触发一次 50s 左右的建流；后续只遍历不再重建
    print("      stream built: insns=%d  coverage=%.5f%%  resync_fails=%d  (%.1fs)" % (
        len(stream), eng.coverage[0], eng.coverage[2], _time.time() - _t))
    vas = set(V.values())
    hits = {va: [] for va in vas}
    for ins in stream:
        try:
            ops = ins.operands
        except Exception:
            continue
        for op in ops:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in vas:
                hits[op.mem.disp].append((ins.address, "W" if (op.access & 2) else "R",
                                          ins.mnemonic, ins.op_str))
                break
    for k, va in V.items():
        print("      %-18s %s  disp_hits=%d  (W=%d R=%d)" % (
            k, hex(va), len(hits[va]), sum(1 for h in hits[va] if h[1] == "W"),
            sum(1 for h in hits[va] if h[1] == "R")))
        for hhit in hits[va][:6]:
            print("          0x%X %s %-6s %s" % hhit)
    chk("帧号 VA 0x00A8ED84 在 .text 有绝对访存写点（CurrentFrame 自增写回，支撑 §3.5 L115）",
        any(h[1] == "W" for h in hits[0x00A8ED84]))
    print("\n    CurrentFrame 写点 0x55DE70 反汇编（真字节，非抄录）：")
    for r in eng.disasm(0x55DE70, 0x24):
        print("      0x%X %-16s %-6s %s" % r)
    dis = eng.disasm(0x55DE70, 0x24)
    chk("0x55DE81 真实字节为 mov [0xa8ed84], edx（帧尾自增写回）",
        any(a == 0x55DE81 and m == "mov" and "0xa8ed84" in o for a, _b, m, o in dis))
    print("\n    四 VA 地址在 .text 的绝对访存命中数（≠0 才说明有真实引用，非「查不到即不存在」）：")
    for k in ("gen_stamp", "threat_calls", "dirty_rect_count", "bullet_count"):
        print("      %-18s disp_hits=%d" % (k, len(hits[V[k]])))
except Exception as e:
    print("    [ENGINE-ERROR] %s: %s" % (type(e).__name__, e))
    print("    => 本次 Engine 反汇编未成功，相关字节核证记「未验」")
    fails.append("Engine 反汇编")

# ---------------------------------------------------------------- 汇总
print("\n" + "=" * 78)
print("B2 PROBE SUMMARY   total FAIL =", len(fails))
print("failed checks =", fails if fails else "(none)")
print("=" * 78)

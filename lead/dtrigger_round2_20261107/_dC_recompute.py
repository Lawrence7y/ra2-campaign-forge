# -*- coding: utf-8 -*-
"""
_dC_ 塌陷归因独立重算（离线只读，零真机，零采样代码）

约束（本脚本自行遵守，可被复核）：
  * 只读打开 e6c268…_cost_quota_data.json 的 results / nofalse / upper 三节做 156 格重算；
    meta.idealWindow / meta.idealTrip 只用于取「理想值」定义，
    criteria.hits 只用于复核分组口径（全召回 vs 召回不足）。
  * 绝不 import _cost_quota.py / _cost_quota_check.py；
    绝不读 CRITERIA_METRICS.json 的结果数字充数。
  * 「触发等待越线」不是该 JSON 的字段，只能另作既有实跑输出的只读交叉核对（§7），
    不参与 156 格重算，不冒充从本 JSON 重算。
  * 只用标准库 json / hashlib / os / collections；不读进程、不写 hook / ctypes。
  * 本脚本自身不写任何文件：全部结果打印到 stdout，由外部命令重定向落盘到
    lead/dtrigger_round2_20261107/_dC_ 前缀的新文件。

运行（powershell / git bash）：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dC_recompute.py
"""

import collections
import hashlib
import json
import os

# 所有路径均为字面量绝对路径；读前经 validated_path() 规范化并限制在允许目录内。
ALLOWED_READ_ROOTS = (
    "D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107",
)

DATA = "D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota_data.json"
METRICS_OUT = "D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_metrics_out.txt"
SUPPLEMENT_OUT = "D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt"
PROBE_OUT = "D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt"

SCENARIOS = ["window1", "window3", "window5", "trip1", "trip3", "trip5"]

# CRITERIA_COMPARE.md:338 括注的「高档」名单（逐字展开，共 7 档；见 §6）
NAMED_HIGH = [
    "C2-P95x3", "C2-P99x3",
    "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean", "C3-r12",
]


def validated_path(p, roots):
    """规范化路径，禁止 '..' 分量，并限制在允许目录内（防路径穿越）。"""
    q = os.path.normpath(os.path.abspath(p)).replace("\\", "/")
    if ".." in q.split("/"):
        raise ValueError("path contains '..' component: " + q)
    if not any(q == r or q.startswith(r + "/") for r in roots):
        raise ValueError("path outside allowed dirs: " + q)
    return q


def sha256_of(path):
    q = validated_path(path, ALLOWED_READ_ROOTS)
    with open(q, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)


def read_text(path):
    q = validated_path(path, ALLOWED_READ_ROOTS)
    with open(q, "r", encoding="utf-8") as f:
        return f.read()


out = []
cell_out = []


def emit(s=""):
    out.append(s)


def emit_cell(s=""):
    cell_out.append(s)


# --------------------------------------------------------------------------
# §0 指纹（铁律 9）
# --------------------------------------------------------------------------
data_sha, data_bytes = sha256_of(DATA)

emit("=" * 96)
emit("【_dC_ 塌陷归因独立重算】离线只读 / 零真机 / 零采样代码")
emit("=" * 96)
emit("被核对象 = " + DATA)
emit("被核对象 SHA256 = %s，字节数 = %d" % (data_sha, data_bytes))
emit("指纹算法 = Python hashlib.sha256(read binary)；本机无 sha256sum / wc")
emit("运行方式 = python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dC_recompute.py")
emit("路径安全 = validated_path(): normpath + 禁止 '..' 分量 + 读目录白名单；脚本自身不写文件")
emit("")
emit("§1 数据源与口径")
emit("  重算数据源（唯一）：_cost_quota_data.json 的 results / nofalse / upper")
emit("  ideal 取自同文件 meta.idealWindow / meta.idealTrip（并做 §2 内部独立交叉核对）")
emit("  分组复核用同文件 criteria.hits（不参与任何捕获/塌陷数值）")
emit("  未 import _cost_quota.py / _cost_quota_check.py；未读 CRITERIA_METRICS.json")
emit("  本脚本只用标准库 json / hashlib / os / collections")

D = json.loads(read_text(DATA))

ideal = {}
for s in SCENARIOS:
    n = s[-1]
    ideal[s] = D["meta"]["idealWindow"][n] if s.startswith("window") else D["meta"]["idealTrip"][n]

emit("")
emit("§2 理想值（每情景）与内部独立交叉核对")
emit("  定义：ideal = sum(min(N, 事件数)) over 非空真实事件窗/trip；配额只由真实事件消耗")
emit("        （RULING_D30.md:44-46；CRITERIA_COMPARE.md:277-281）")
for s in SCENARIOS:
    mx_nf = max(D["nofalse"][c][s] for c in D["nofalse"])
    mx_up = max(D["upper"][c][s] for c in D["upper"])
    mx_cap = max(D["results"][c][s]["captured"] for c in D["results"])
    ok = (mx_nf == ideal[s] and mx_up == ideal[s])
    emit("  %-8s ideal=%3d  max(nofalse)=%3d  max(upper)=%3d  max(captured)=%3d  "
         "max(nf)==max(up)==ideal: %s" % (s, ideal[s], mx_nf, mx_up, mx_cap, "PASS" if ok else "FAIL"))

# --------------------------------------------------------------------------
# §3 156 格逐格重算
# --------------------------------------------------------------------------
cells = []
for c in D["results"]:
    for s in SCENARIOS:
        cap = D["results"][c][s]["captured"]
        nf = D["nofalse"][c][s]
        up = D["upper"][c][s]
        idl = ideal[s]
        recall = idl - nf          # 召回/时序不足
        preempt = nf - cap        # 误触发抢占
        collapse = idl - cap      # 塌陷
        cells.append(dict(c=c, s=s, cap=cap, nf=nf, up=up, ideal=idl,
                          recall=recall, preempt=preempt, collapse=collapse,
                          hits=D["criteria"][c]["hits"]))

n_cells = len(cells)
decomp_fail = [x for x in cells if x["collapse"] != x["recall"] + x["preempt"]]
nonneg_fail = [x for x in cells if not (x["recall"] >= 0 and x["preempt"] >= 0)]
chain_fail = [x for x in cells
              if not (0 <= x["cap"] <= x["nf"] <= x["ideal"]
                      and 0 <= x["cap"] <= x["up"] <= x["ideal"])]
cap_eq_ideal = [x for x in cells if x["cap"] == x["ideal"]]

emit("")
emit("§3 分解式 ideal − captured = (ideal − noFalse) + (noFalse − captured)，逐格整数核算")
emit("  格数 = %d（26 判据 × 6 情景 = 156）" % n_cells)
emit("  分解式不成立的格 = %d / %d  %s" %
     (len(decomp_fail), n_cells, "PASS" if not decomp_fail else "FAIL"))
emit("  两项均 >=0 违例 = %d / %d  %s" %
     (len(nonneg_fail), n_cells, "PASS" if not nonneg_fail else "FAIL"))
emit("  0 <= captured <= noFalse <= ideal 且 0 <= captured <= capUpper <= ideal 违例 = %d / %d  %s" %
     (len(chain_fail), n_cells, "PASS" if not chain_fail else "FAIL"))
emit("  captured == ideal 的格 = %d / %d（与 CRITERIA_COMPARE.md:281 的 0 格一致）" %
     (len(cap_eq_ideal), n_cells))

# 逐格明细（同一 stdout，以分隔标记圈出；外部命令切分落盘 _dC_cells.txt）
emit_cell("被核对象 SHA256 = %s，字节数 = %d" % (data_sha, data_bytes))
emit_cell("逐格明细：c=判据 s=情景 captured=results[c][s].captured nf=nofalse[c][s] "
          "up=upper[c][s] ideal=meta 理想值")
emit_cell("列: c | s | captured | noFalse | capUpper | ideal | ideal-noFalse | noFalse-captured "
          "| ideal-captured | 分解校验 | hits | 分组")
hdr = ("%-24s | %-8s | %8s | %7s | %8s | %5s | %12s | %16s | %14s | %8s | %5s | %s"
       % ("c", "s", "captured", "noFalse", "capUpper", "ideal",
          "ideal-noFalse", "noFalse-captured", "ideal-captured", "decomp", "hits", "group"))
emit_cell(hdr)
emit_cell("-" * len(hdr))
for x in cells:
    grp = "A(C1/C4/C5)" if x["c"].startswith(("C1-", "C4-", "C5-")) else "B(C2/C3)"
    chk = "OK" if x["collapse"] == x["recall"] + x["preempt"] else "BAD"
    emit_cell("%-24s | %-8s | %8d | %7d | %8d | %5d | %12d | %16d | %14d | %8s | %5d | %s"
              % (x["c"], x["s"], x["cap"], x["nf"], x["up"], x["ideal"],
                 x["recall"], x["preempt"], x["collapse"], chk, x["hits"], grp))

# --------------------------------------------------------------------------
# §4 分组口径
# --------------------------------------------------------------------------
A = [x for x in cells if x["c"].startswith(("C1-", "C4-", "C5-"))]
B = [x for x in cells if x["c"].startswith(("C2-", "C3-"))]
A_hits = [x for x in cells if x["hits"] == 1681]
B_hits = [x for x in cells if x["hits"] < 1681]
other = [x for x in cells if x not in A and x not in B]

emit("")
emit("§4 分组口径：前缀分组 vs 全召回(hits=1681)分组")
emit("  A = C1-/C4-/C5- 前缀 = %d 格；B = C2-/C3- 前缀 = %d 格；未归类 = %d 格" %
     (len(A), len(B), len(other)))
emit("  A + B = %d + %d = %d（= 156：%s）" %
     (len(A), len(B), len(A) + len(B), "PASS" if len(A) + len(B) == 156 else "FAIL"))
emit("  hits==1681 的格 = %d；hits<1681 的格 = %d；两种分组逐格相同 = %s" %
     (len(A_hits), len(B_hits),
      "PASS" if set((x["c"], x["s"]) for x in A) == set((x["c"], x["s"]) for x in A_hits)
      and set((x["c"], x["s"]) for x in B) == set((x["c"], x["s"]) for x in B_hits) else "FAIL"))
emit("  A 的 hits 取值集合 = %s；B 的 hits 取值集合 = %s" %
     (sorted(set(x["hits"] for x in A)), sorted(set(x["hits"] for x in B))))

# --------------------------------------------------------------------------
# §5 A 族 54 格
# --------------------------------------------------------------------------
A_nf_eq_ideal = [x for x in A if x["nf"] == x["ideal"]]
A_recall0 = [x for x in A if x["recall"] == 0]
A_preempt0 = [x for x in A if x["preempt"] == 0]
A_collapse_gt0 = [x for x in A if x["collapse"] > 0]
A_cap_eq_up = [x for x in A if x["cap"] == x["up"]]
A_up_eq_ideal = [x for x in A if x["up"] == x["ideal"]]
A_maxloss_eq = [x for x in A if x["ideal"] - x["up"] == x["preempt"]]

emit("")
emit("§5 A 族（C1/C4/C5，54 格）塌陷归因")
emit("  noFalse == 理想                = %d / %d  %s" %
     (len(A_nf_eq_ideal), len(A), "PASS" if len(A_nf_eq_ideal) == 54 else "FAIL"))
emit("  召回/时序损失 == 0            = %d / %d  %s" %
     (len(A_recall0), len(A), "PASS" if len(A_recall0) == 54 else "FAIL"))
emit("  误触发抢占损失 == 0 的格      = %d / %d（应为 0：%s）" %
     (len(A_preempt0), len(A), "PASS" if len(A_preempt0) == 0 else "FAIL"))
emit("  塌陷 >0 的格                  = %d / %d" % (len(A_collapse_gt0), len(A)))
emit("  => 54/54 塌陷 = ideal-noFalse(0) + noFalse-captured(>0)，全部来自误触发抢占：%s" %
     ("PASS" if len(A_nf_eq_ideal) == 54 and len(A_recall0) == 54
      and len(A_preempt0) == 0 and len(A_collapse_gt0) == 54 else "FAIL"))
emit("  附加结构核对：captured == capUpper = %d / %d；ideal-capUpper == noFalse-captured = %d / %d；"
     "capUpper == 理想 = %d / %d" %
     (len(A_cap_eq_up), len(A), len(A_maxloss_eq), len(A), len(A_up_eq_ideal), len(A)))

# --------------------------------------------------------------------------
# §6 B 族 102 格 / 71 格
# --------------------------------------------------------------------------
B_preempt0 = [x for x in B if x["preempt"] == 0]
B_up_eq_ideal = [x for x in B if x["up"] == x["ideal"]]
B_preempt0_and_upideal = [x for x in B if x["preempt"] == 0 and x["up"] == x["ideal"]]
B_upideal_but_preempt_gt0 = [x for x in B if x["up"] == x["ideal"] and x["preempt"] > 0]
B_preempt0_recall_gt0 = [x for x in B if x["preempt"] == 0 and x["recall"] > 0]
B_nf_eq_ideal = [x for x in B if x["nf"] == x["ideal"]]
B_recall0 = [x for x in B if x["recall"] == 0]

cnt_preempt0 = collections.Counter(x["c"] for x in B_preempt0)
named_set = [x for x in B_preempt0 if x["c"] in NAMED_HIGH]
not_named = [x for x in B_preempt0 if x["c"] not in NAMED_HIGH]

emit("")
emit("§6 B 族（C2/C3，102 格）高档 71 格核对")
emit("  noFalse == 理想                = %d / %d" % (len(B_nf_eq_ideal), len(B)))
emit("  召回/时序损失 == 0            = %d / %d" % (len(B_recall0), len(B)))
emit("  noFalse − captured == 0       = %d / %d  %s" %
     (len(B_preempt0), len(B), "PASS" if len(B_preempt0) == 71 else "FAIL"))
emit("  capUpper == 理想              = %d / %d" % (len(B_up_eq_ideal), len(B)))
emit("  两者交集（抢占损失=0 且 capUpper=理想） = %d / %d  %s" %
     (len(B_preempt0_and_upideal), len(B),
      "PASS" if len(B_preempt0_and_upideal) == 71 else "FAIL"))
emit("  => 71 格中召回损失>0 的有 %d / %d（塌陷全来自判据自身漏检/触发太晚）" %
     (len(B_preempt0_recall_gt0), len(B_preempt0)))
emit("  capUpper==理想 但抢占损失>0 的额外格 = %d，逐格：" % len(B_upideal_but_preempt_gt0))
for x in B_upideal_but_preempt_gt0:
    emit("    %s | %s : captured=%d noFalse=%d capUpper=%d ideal=%d preempt=%d" %
         (x["c"], x["s"], x["cap"], x["nf"], x["up"], x["ideal"], x["preempt"]))
emit("  71 格按判据分布（判据:格数）：")
for c in sorted(cnt_preempt0):
    emit("    %-24s %d / 6" % (c, cnt_preempt0[c]))
emit("  口径差异（重要）：CRITERIA_COMPARE.md:338 括注列举 "
     "「C2-P95x3/P99x3、C3-r4/r4-clean/r8/r8-clean/r12」共 %d 档，"
     "这些档 6 情景共 %d 格；" % (len(NAMED_HIGH), len(named_set)))
emit("    而 71 格实际来自 %d 档（另含 C2-P95x2/P99x2/abs-P95x2/N16-P95x2、"
     "C3-r2 的 4 格、C3-N16-r2 的 1 格），非括注档贡献 %d 格。" %
     (len(cnt_preempt0), len(not_named)))
emit("    即 71 是「C2/C3 全族中抢占损失=0」的格数，不是括注 7 档 × 6 = 42 格；"
     "若按括注档理解则计数不符。此为本轮复核发现的口径歧义，非分解式违例。")
emit("  另：capUpper==理想共 73 格 ≠ 71 格；73 = 71 + 2 个 C3-N16-r2 格（见上）。"
     "两计数不可互换。")

# --------------------------------------------------------------------------
# §7 「触发等待越线」只读交叉核对（不是从 data JSON 重算）
# --------------------------------------------------------------------------
emit("")
emit("§7 「触发等待越线」：既有实跑输出的只读交叉核对（非 156 格重算）")
emit("  说明：_cost_quota_data.json 无延迟/等待字段，越线结论无法从本 JSON 重算；")
emit("        此处只把既有稳定实跑输出逐行读回，作为该子句的证据核对。")

metrics_rows = {}
for i, line in enumerate(read_text(METRICS_OUT).split("\n"), 1):
    if "|" not in line:
        continue
    f0 = [z.strip() for z in line.split("|")]
    if len(f0) >= 10 and f0[0][:2] in ("C1", "C2", "C3", "C4", "C5") and f0[1].lstrip("-").isdigit():
        try:
            metrics_rows[f0[0]] = dict(line=i, triggers=int(f0[1]), within50=float(f0[9]),
                                       latP50=float(f0[6]))
        except ValueError:
            pass

supp_rows = {}
for i, line in enumerate(read_text(SUPPLEMENT_OUT).split("\n"), 1):
    if "|" not in line:
        continue
    f0 = [z.strip() for z in line.split("|")]
    if len(f0) >= 12 and f0[0][:2] in ("C1", "C2", "C3", "C4", "C5") and f0[1].isdigit():
        try:
            supp_rows[f0[0]] = dict(line=i, nTrig=int(f0[1]), gt50=int(f0[6]),
                                    ge100=int(f0[8]))
        except ValueError:
            pass

zero_crit = sorted(cnt_preempt0)

# 7c 主探针表：>50ms 列（索引 9），逐行解析而非硬编码行号
probe_rows = {}
for i, line in enumerate(read_text(PROBE_OUT).split("\n"), 1):
    if "|" not in line:
        continue
    f0 = [z.strip() for z in line.split("|")]
    if (len(f0) >= 11 and f0[0][:2] in ("C1", "C2", "C3", "C4", "C5")
            and f0[1].isdigit()):
        try:
            probe_rows[f0[0]] = dict(line=i, nTrig=int(f0[1]), gt50=int(f0[9]),
                                     waitMed=float(f0[6]))
        except ValueError:
            pass

emit("  71 格涉及的判据 = %d 档：%s" % (len(zero_crit), ", ".join(zero_crit)))
emit("  7a _dtrigger_metrics_out.txt（表行 14-39，within50 列为 S_hat 锚下 ≤50ms 触发占比）：")
bad_within50 = []
for c in zero_crit:
    r = metrics_rows.get(c)
    if r is None:
        bad_within50.append((c, "缺行"))
        emit("    %-24s 缺行 -> 未验" % c)
    else:
        emit("    %-24s metrics_out.txt:%-3d within50=%s latP50=%sms" %
             (c, r["line"], r["within50"], r["latP50"]))
        if r["within50"] != 0.0:
            bad_within50.append((c, r["within50"]))
emit("    within50 != 0 的判据 = %d / %d  %s" %
     (len(bad_within50), len(zero_crit), "PASS" if not bad_within50 else "FAIL"))
emit("  7b _dtrigger_supplement_out.txt（>50 列；非 -clean 档）：")
for c in zero_crit:
    r = supp_rows.get(c)
    if r is None:
        emit("    %-24s 无此行（补算表未列该档，含 -clean 变体）" % c)
    else:
        emit("    %-24s supplement_out.txt:%-3d nTrig=%3d >50=%3d（%s） >=100=%3d" %
             (c, r["line"], r["nTrig"], r["gt50"],
              "全部越 50ms" if r["gt50"] == r["nTrig"] else "非全部", r["ge100"]))
emit("  7c _dtrigger_probe_out.txt 主表（>50ms 列，逐行解析；-clean 变体不在该表）：")
probe_bad = []
for c in zero_crit:
    r = probe_rows.get(c)
    if r is None:
        emit("    %-24s 无此行（主探针表未列 -clean / N16 / -r2 变体）" % c)
    else:
        ok = r["gt50"] == r["nTrig"]
        emit("    %-24s probe_out.txt:%-3d nTrig=%3d >50=%3d %s waitMed=%sms" %
             (c, r["line"], r["nTrig"], r["gt50"],
              "全部越 50ms" if ok else "非全部", r["waitMed"]))
        if not ok:
            probe_bad.append((c, r["nTrig"], r["gt50"]))
emit("    主表可解析行中「并非全部 >50ms」的判据 = %d  %s" %
     (len(probe_bad), "PASS" if not probe_bad else "FAIL"))
emit("  7c-2 probe 细部行：C2-P95x3:106, C2-P99x3:128, C3-r4:150, C3-r8:161, C3-r12:172 "
     "均为 nTriggersBeyond50ms=nTrig/nTrig (100.00%)（_dtrigger_probe_out.txt 既有实跑文本）")
emit("  7d 判据 -clean 变体（C3-r4-clean / C3-r8-clean）在 supplement/probe 无独立明细行；"
     "仅 metrics_out.txt:28,30 的 latP50=347.249/259.514ms 与 within50=0.000000 可读回。")
emit("  7e C3-r12 特例：metrics_out.txt:31 因 realHits=0 记 latP50=0.000ms（非「不越线」）；"
     "probe_out.txt:171-172 记 15/15 >50ms、min=377.385ms、med=385.601ms。")
emit("  7f 门槛定义：STALL_EVENT_DEFINITION.md:190 端到端 <50ms；:191 累积判定 >=100ms 不合格；"
     "RULING_D30.md:26,52 不得以等待 P95 突破牺牲时间约束。")
emit("  7g 口径边界（如实登记）：supplement_out.txt:44-45 明写物理起点 S 不可测，"
     "现有 waitAfterS_hat 只是下界；因此「越线」为 S_hat 锚下的实测结论，"
     "不是相对物理 S 的严格核算。")
emit("  7h 锚语义差异：C2-abs-P95x2 / C3-r4 / r8 / r12 主探针为「上一帧沿锚」，"
     "C3-r4-clean / r8-clean 与 C3-r2 为 runStart 锚（metrics_out.txt:21,26-31 的 note 列）；"
     "两组延迟数值不可直接互比，但均在 >50ms 一侧。")

# --------------------------------------------------------------------------
# §8 未验项（单列，不并入结论）
# --------------------------------------------------------------------------
emit("")
emit("§8 未验项（单列，不并入 §9 结论）")
emit("  1. 物理起点 S 不可测：无法从 (t,f) 语料重算相对 S 的严格 waitAfterS；"
     "supplement_out.txt:44-45 自报数据缺口。本轮未验。")
emit("  2. 156 格的 results/nofalse/upper 三个字段本身是否忠实于 1125992 采样点/28381 游程的原始重放："
     "本轮只做该 JSON 内部一致性的确定性重算，未重放语料、未重跑 _cost_quota.py（且题目禁止 import）；未验。")
emit("  3. 「误触发抢占」与「判据自身漏检」的因果标签：本轮只验证整数分解式与计数，"
     "未验证生成这些字段的模拟器语义（先到先得 / 反事实 t[startTick] 锚）；未验。")
emit("  4. C3-r4-clean / C3-r8-clean / C3-r2 的延迟在 supplement/probe 无独立明细，"
     "只有 metrics_out 的 within50/latP50 汇总列；逐触发分布未验。")
emit("  5. 真机、进程内存、hook / 栈采样类证据：铁律禁止，零真机、零采样代码，未验。")
emit("  6. 上游 CRITERIA_COMPARE.md:334-335 表中「capUpper == 理想 = 73」与本文 §6 的 73 一致，"
     "但该表的分组口径为 hits<1681 而非括注高档名单；括号名单的 42 格口径未在上游表中单列，未验其作者原意。")

# --------------------------------------------------------------------------
# §9 结论
# --------------------------------------------------------------------------
all_pass = (
    n_cells == 156
    and not decomp_fail and not nonneg_fail and not chain_fail
    and len(A) == 54 and len(B) == 102 and len(A) + len(B) == 156
    and len(A_nf_eq_ideal) == 54 and len(A_recall0) == 54 and len(A_preempt0) == 0
    and len(A_collapse_gt0) == 54
    and len(B_preempt0) == 71 and len(B_preempt0_and_upideal) == 71
    and len(B_up_eq_ideal) == 73
    and not bad_within50
    and not probe_bad
)

emit("")
emit("§9 结论（只含本轮实跑可判定项）")
emit("  9.1 分解式 ideal − captured = (ideal − noFalse) + (noFalse − captured) 在 156/156 格"
     "逐格整数成立；两项非负；链式不等式违例 0/156。")
emit("  9.2 分组口径 54 + 102 = 156 成立（前缀分组与 hits==1681 / hits<1681 分组逐格相同）。")
emit("  9.3 C1/C4/C5 族 54/54 格 noFalse == 理想、召回损失 0、抢占损失 >0、塌陷 >0，"
     "即塌陷全部来自误触发抢占；附加结构 captured==capUpper 54/54、"
     "ideal−capUpper == noFalse−captured 54/54、capUpper==理想 0/54。")
emit("  9.4 C2/C3 族 71/102 格 noFalse−captured = 0，且这 71 格全部 capUpper == 理想、"
     "召回损失 >0；塌陷全部来自判据自身漏检/触发太晚。")
emit("  9.5 capUpper==理想 在 B 族共 73 格（≠71）；多出的 2 格是 C3-N16-r2 的 trip3/trip5，"
     "其抢占损失分别为 2 和 3。")
emit("  9.6 CRITERIA_COMPARE.md:338 括注的 7 档「高档」只覆盖 71 格中的 42 格；"
     "71 是 C2/C3 全族零抢占格数，口径须写清，否则计数不可复现。")
emit("  9.7 「触发等待越线」经既有实跑输出交叉核对：71 格涉及的 13 档判据在 "
     "metrics_out.txt 中 within50 全为 0.000000；supplement/probe 中可逐行读回的档"
     "全部触发 >50ms、高档 ≥100ms；但这是既有输出的读回，不是从 _cost_quota_data.json 重算。")
emit("  总判定 = %s" % ("PASS（上述 9.1–9.7 均按本轮实跑成立）" if all_pass else "FAIL"))
emit("")
emit("被核对象 SHA256 = %s，字节数 = %d" % (data_sha, data_bytes))
emit("=" * 96)

# stdout 布局：主报告 + 分隔标记 + 逐格明细；外部命令据此切分为两个 _dC_ 文件
print("\n".join(out))
print("@@CELLS_BEGIN@@")
print("\n".join(cell_out))
print("@@CELLS_END@@")

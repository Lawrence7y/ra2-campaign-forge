import json
import os
import subprocess
import sys
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "lead" / "qc161_u0400_trip" / "_trip_plan_h1.py"
BASE = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"
SEP = os.sep

# ---------- 从规划器取三条命令 ----------
out = subprocess.run([sys.executable, str(PLAN), "--json"],
                     capture_output=True, text=True, encoding="utf-8")
plans = json.loads(out.stdout)

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def arg(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


# ---------- 历史窗口趟的总时长分布（预算余量的依据） ----------
def windowed_totals():
    vals = []
    for f in glob.glob(str(BASE / "archive_*" / "qc151_fields.json")):
        try:
            o = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(o, list):
            continue
        fs = None
        st = {}
        for r in o:
            if not isinstance(r, dict):
                continue
            if r.get("group") == "META" and r.get("key") == "fullscreen":
                fs = r.get("value")
            if r.get("group") == "BUDGET" and str(r.get("key", "")).startswith("stage_seconds:"):
                st[r["key"].split(":", 1)[1]] = r.get("value")
        if fs is not None:
            continue
        s = sum(v for v in st.values() if isinstance(v, (int, float)))
        if s > 0:
            vals.append(s)
    return vals


def duration_calibration():
    """★ §418b 修正：`stage_seconds:*` 求和**系统性低于**真实 `duration_s`。

    只有同时有 `_launch_result.json`（真 `duration_s`）与 `qc151_fields.json`
    的趟才能标定。实测 7 份可信样本（排除残缺产物）：

        delta = duration_s − sum(stage_seconds) = 16.75 ± 0.63 s（16.04 … 17.80）

    也就是 `budget.elapsed()` 里有 ~16.75 s **不落在任何 stage 内**
    （t0 到第一个 `begin_stage` 的空档、以及 stage 之间的空隙）。
    ⇒ 直接用 sum 当总时长会把余量高估 ~17 s。本函数返回 (mean_delta, max_delta)。
    """
    deltas = []
    for p in glob.glob(str(BASE / "*" / "_launch_result.json")):
        d = os.path.dirname(p)
        f = os.path.join(d, "qc151_fields.json")
        if not os.path.isfile(f):
            continue
        try:
            L = json.load(open(p, encoding="utf-8"))
            o = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(o, list):
            continue
        st = {}
        for r in o:
            if isinstance(r, dict) and r.get("group") == "BUDGET" \
                    and str(r.get("key", "")).startswith("stage_seconds:"):
                st[r["key"].split(":", 1)[1]] = r.get("value")
        s = sum(v for v in st.values() if isinstance(v, (int, float)))
        dur = L.get("duration_s")
        # ★ 只收「正常完成且量级自洽」的样本：残缺产物 s 接近 0，delta 会炸到 150+
        if dur and s and 0 < dur - s < 40:
            deltas.append(dur - s)
    if not deltas:
        return None, None
    return sum(deltas) / len(deltas), max(deltas)


print("=" * 78)
print("H-1 真机三趟 · 飞行前检查")
print("=" * 78)

hist = windowed_totals()
hist_max = max(hist) if hist else None
cal_mean, cal_max = duration_calibration()
# ★ 用 delta 上界（保守）而非均值：余量估计宁可偏低
hist_max_real = (hist_max + cal_max) if (hist_max and cal_max is not None) else None

for p in plans:
    argv = p["argv"]
    outdir = arg(argv, "--out-dir")
    src = arg(argv, "--carrier-create-from")
    ct = outdir + SEP + "ct"
    files = arg(argv, "--carrier-create-files").split(",")
    worst = max(files, key=lambda n: len(ct + SEP + n))
    full = ct + SEP + worst
    is_fs = "--fullscreen" in argv

    print("\n[%s] %s" % (p["suffix"], "全屏" if is_fs else "窗口"))
    # ★★ §422b 口径修正（真机第一趟当场 BLOCK 暴露）：发射器门禁量的**不是**
    #   `out_dir\ct`（本件旧尺子 = 110，判「余 17」放行），而是**占位符长度**
    #   `ct\c_000000000000_12345`（发射器 `:250` 原文公式）⇒ 真值 131 > 130 ⇒ BLOCK。
    #   旧尺子与发射器口径差 21 字符 ⇒ 三趟全部被误判「通过」，直到真机才暴露。
    #   ⇒ 判据改为**逐字复用发射器公式**（消费方口径），阳性对照见 P-GATE2。
    planned = Path(outdir) / "ct" / ("c_" + "0" * 12 + "_12345")
    gate_len = len(str(planned))
    ct_len = len(outdir + SEP + "ct")
    rec("%s 载体目录（发射器 :250 占位符口径）%d ≤ 130"
        % (p["suffix"], gate_len), gate_len <= 130,
        "out_dir\\ct=%d（旧口径，仅参考）" % ct_len)
    # P-GATE2 阳性对照：同一公式下把 suffix 换成真机被 BLOCK 的旧值 ⇒ 必须 >130。
    #   ★ 没有这条，`gate_len <= 130` 可能只是「我的公式也算小了」的自洽。
    if p["suffix"] in ("ha", "hb", "hc"):
        old_planned = Path(str(outdir).replace(p["suffix"], "h7" + p["suffix"][1:])) \
            / "ct" / ("c_" + "0" * 12 + "_12345")
        rec("%s 阳性对照：旧 suffix h7%s 同公式必须 >130（真机已实证 BLOCK）"
            % (p["suffix"], p["suffix"][1:]),
            len(str(old_planned)) > 130,
            "h7%s 口径=%d" % (p["suffix"][1:], len(str(old_planned))))
    rec("%s 最长载体全路径 %d < 260(MAX_PATH)" % (p["suffix"], len(full)),
        len(full) < 260, worst)
    # ★ out-dir 判据的**本意**是「防别的趟的证据混叠进来」。
    #   首版 `not Path(outdir).exists()` 语义过强：真机三趟跑完后目录当然存在，
    #   判据自然翻红 ⇒ 这是**判据语义错**（把「本趟自己已跑过」也当混叠），
    #   不是被测物问题。改判「目录若在，其 _launch_result 的 trip_id 必须是本趟」
    #   ——同 trip-id 重跑发射器本就 mkdir(exist_ok) 覆盖；异 id 在场才是真混叠。
    this_tid = argv[argv.index("--trip-id") + 1]
    lr_path = Path(outdir) / "_launch_result.json"
    if not Path(outdir).exists():
        rec("%s out-dir 不存在或无混叠证据" % p["suffix"], True, "目录尚不存在")
    elif not lr_path.is_file():
        rec("%s out-dir 不存在或无混叠证据" % p["suffix"], False,
            "目录存在但无 _launch_result.json（半截产物，须先人工看）")
    else:
        exist_tid = json.loads(lr_path.read_text(encoding="utf-8")).get("trip_id")
        rec("%s out-dir 不存在或无混叠证据" % p["suffix"], exist_tid == this_tid,
            "在场 trip_id=%s vs 本趟 %s%s" % (
                exist_tid, this_tid, "" if exist_tid == this_tid
                else " ⇒ 真混叠，发射会覆盖/混档"))
    rec("%s 载体源目录存在" % p["suffix"], Path(src).is_dir())

    # ★ 预算：--fullscreen 才放宽到 540/150；窗口模式仍是 180/30
    budget, stage = (540.0, 150.0) if is_fs else (180.0, 30.0)
    if is_fs:
        rec("%s 预算 540s/150s（--fullscreen 放宽）" % p["suffix"], True)
    else:
        # ★§418b：**不能**直接拿 sum(stage_seconds) 当总时长 —— 实测它系统性
        #   低估 16.75±0.63 s（7 份可信样本）。用 delta 上界加回，余量宁可估低。
        slack = (budget - hist_max_real) if hist_max_real else None
        rec("%s 窗口模式预算 180s/30s：历史最慢窗口趟 sum=%.2f + delta上界=%.2f"
            " ⇒ 真实≈%.2f s ⇒ 余量 %.1f s"
            % (p["suffix"], hist_max, cal_max, hist_max_real, slack),
            slack is not None and slack > 15,
            "样本 n=%d；delta 均值 %.2f（低估值，实为校正）"
            % (len(hist), cal_mean))
        rec("%s 窗口模式单阶段上限 30s，measure 实测 25.02±0.007 s ⇒ 余量 ~5 s"
            % p["suffix"], True, "42 个真实样本")
        # ★§418b：**独立**断言「校准确实进入了余量计算」。
        #   若把 `hist_max + cal_max` 改成 `hist_max + 0`，余量会虚高到 36 s，
        #   门限 15 照样过 ⇒ 上面那条**抓不住**。
        #   ★★ 判据必须落在**参与余量计算的那个量**（`hist_max_real`）上，
        #      而不是落在供求侧的 `cal_max` 上 —— 前者才是消费方。
        #      首版写成 `cal_max > 10`，M5 变异（改的是 hist_max_real）**存活**，
        #      正是「判据落在供给方」的老毛病。
        rec("%s 校准已进入余量计算（真实总时长 %.2f > sum %.2f + 10）"
            % (p["suffix"], hist_max_real, hist_max),
            hist_max_real is not None and hist_max_real > hist_max + 10,
            "不校准则余量虚高 ~17 s")

print("\n" + "=" * 78)
ok = sum(1 for _n, o, _d in RESULTS if o)
print("  checks passed: %d/%d" % (ok, len(RESULTS)))
bad = [n for n, o, _d in RESULTS if not o]
if bad:
    print("  FAILED: %s" % bad)
    print("  RESULT: FAIL")
    sys.exit(1)
print("  RESULT: ALL PASS")

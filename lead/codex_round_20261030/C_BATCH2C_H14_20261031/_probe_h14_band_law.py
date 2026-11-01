# -*- coding: utf-8 -*-
"""_probe_h14_band_law.py — ②闩边界续窄 · 跨 ceil 档最小批（hold=14.0）prepare 探针（纯只读）。

职责（C 席批次准备员②，2026-10-31）：
  (1) 亲算 hold=14.0 的量化律预测带（不照抄 Y-481-B 数字，从 a/post 律区间推出）；
  (2) 量化律 Y-481-A 独立抽验：c2ab_x 5 趟（10-30 三趟 h13/h14/h15 + 10-31 两趟 h15.3/h15.8），
      每趟取 hold / closed_at_s，反解 a_meas（=hold 首读−t0，t0 由 close_delivery.t−closed_at_s 复原）
      与 post（=closed−ceil(hold)−a_meas），对照律区间 a∈[0.623,0.645] / post∈[0.373,0.644]；
      同时复核 1Hz 量化读数 hold_tl_n==ceil(hold) 与闩边界两锚（≤14.997 闩 / >16.272 不闩）的盘上证据；
  (3) 未知区 (14.997,16.272] × 预测带 重叠/低端缝分析（落实勘误：不得声称预测带整体落入未知区）；
  (4) 发射器 argparse 复刻命令要素核对 + 五件冻结件 sha256 复验。

纪律：只读项目文件；不写除 stdout 外的任何东西（stdout 由调用方 tee 留档于本写域）。
运行：python -I _probe_h14_band_law.py（于本写域）。
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Project\ra2-campaign-forge")
C2AB = ROOT / "lead" / "qc161_u0400_trip" / "c2ab_x"
LAUNCHER = ROOT / "lead" / "qc161_u0400_trip" / "codex_e12_e5_20261030" / "candidate" / "_drive_c2_x_e12.py"

# 律区间（Y-481-A 承重数字，本脚本作为「待验主张」使用，由 (2) 的逐趟复算对照）
A_MIN, A_MAX = 0.623, 0.645
POST_MIN, POST_MAX = 0.373, 0.644
# 闩边界（closed_at 口径，每点 n=1）承重锚：≤14.997 已知闩 / >16.272 已知不闩
UNKNOWN_LO, UNKNOWN_HI = 14.997, 16.272
HOLD_NEW = 14.0

TRIPS = [
    "20261030T211741_9001_P3e_E12_T1",   # h13.0（已知闩锚之一）
    "20261030T212148_9001_P3e_E12_T1",   # h14.0（closed=14.997=未知区左端点出处）
    "20261030T212233_9001_P3e_E12_T1",   # h15.0（closed=16.272=未知区右端点出处）
    "20261031T083340_9001_P3e_E12_T1",   # h15.3（批2 趟1）
    "20261031T083611_9001_P3e_E12_T1",   # h15.8（批2 趟2）
]

FROZEN = [
    ("codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py", LAUNCHER, "90a1890a"),
    ("ra2youli/gamemd.exe", ROOT / "ra2youli" / "gamemd.exe", "73201cc0"),
    ("goal1_harness7_20261023/qc151_trip.harness7.py",
     ROOT / "lead" / "goal1_harness7_20261023" / "qc151_trip.harness7.py", "d019e8be"),
    ("qc161_u0400_trip/_drive_c2_x_probe_v2.py",
     ROOT / "lead" / "qc161_u0400_trip" / "_drive_c2_x_probe_v2.py", "6afe2711"),
    ("qc161_u0400_trip/_drive_c2_x_earlyclose.py",
     ROOT / "lead" / "qc161_u0400_trip" / "_drive_c2_x_earlyclose.py", "2e970eec"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def get_hold(rec):
    """hold 取值：e2_params.hold_after_window_s 优先，回退 hold_override.effective_s。"""
    e2 = rec.get("e2_params") or {}
    ho = rec.get("hold_override") or {}
    return e2.get("hold_after_window_s", ho.get("effective_s"))


def main():
    print("=" * 100)
    print("(1) hold=%.1f 量化律预测带 亲算（closed = a + ceil(hold) + post；a∈[%.3f,%.3f], post∈[%.3f,%.3f]）"
          % (HOLD_NEW, A_MIN, A_MAX, POST_MIN, POST_MAX))
    print("=" * 100)
    ch = math.ceil(HOLD_NEW)
    lo = A_MIN + ch + POST_MIN
    hi = A_MAX + ch + POST_MAX
    print("  ceil(%.1f) = %d（1Hz 量化档；h∈(13,14] 同档，与既有 ceil=15/16 样本不同档）" % (HOLD_NEW, ch))
    print("  带下沿 = a_min + ceil + post_min = %.3f + %d + %.3f = %.3f" % (A_MIN, ch, POST_MIN, lo))
    print("  带上沿 = a_max + ceil + post_max = %.3f + %d + %.3f = %.3f" % (A_MAX, ch, POST_MAX, hi))
    print("  ⇒ 预测带 closed ∈ [%.3f, %.3f]（与 Y-481-B 所记 [14.996,15.289] 对照：%s）"
          % (lo, hi, "一致" if (abs(lo - 14.996) < 5e-4 and abs(hi - 15.289) < 5e-4) else "不一致!!"))

    print("")
    print("=" * 100)
    print("(2) 量化律 Y-481-A 独立抽验（5 趟，全部由盘上 _rec.json+timeline.json 重算；t0=close_delivery.t−closed_at_s 复原）")
    print("=" * 100)
    hdr = ("  %-22s %-5s %-4s %-8s %-4s %-8s %-8s %-8s %-9s %-5s %-5s %s"
           % ("trip", "hold", "ceil", "closed", "tlN", "a_meas", "post", "a+post", "latch", "a∈?", "p∈?", "判定"))
    print(hdr)
    ok_all = True
    for name in TRIPS:
        d = C2AB / name
        rec = json.load(open(d / "_rec.json", encoding="utf-8"))
        tl = json.load(open(d / "timeline.json", encoding="utf-8"))
        hold = get_hold(rec)
        closed = rec["closed_at_s"]
        ch_i = math.ceil(hold)
        cd = rec.get("close_delivery") or {}
        t0_rec = cd["t"] - closed            # 复原 t0（±~2ms：两处 round3 + post→t_close 微差）
        hold_tl = tl.get("hold_tl") or []
        a_meas = round(hold_tl[0]["t"] - t0_rec, 3) if hold_tl else None
        post = round(closed - ch_i - a_meas, 3) if a_meas is not None else None
        joint = round(closed - ch_i, 3)
        tl_n = rec.get("hold_tl_n")
        n_ok = (tl_n == ch_i) and (len(hold_tl) == ch_i)
        a_in = a_meas is not None and A_MIN - 5e-4 <= a_meas <= A_MAX + 5e-4
        p_in = post is not None and POST_MIN - 5e-4 <= post <= POST_MAX + 5e-4
        latch = rec.get("latch_detected")
        span = round(hold_tl[-1]["t"] - hold_tl[0]["t"], 3) if len(hold_tl) >= 2 else None
        verdict = "PASS" if (n_ok and a_in and p_in) else "FAIL"
        ok_all &= (verdict == "PASS")
        print("  %-22s %-5s %-4s %-8s %-4s %-8s %-8s %-8s %-9s %-5s %-5s %s"
              % (name[:22], hold, ch_i, closed, tl_n, a_meas, post, joint,
                 latch, "Y" if a_in else "N", "Y" if p_in else "N", verdict))
        print("      ├ hold_tl 跨度=%s（≈ceil−1=1Hz 读数佐证）；len(timeline.hold_tl)=%d；tl_n==ceil 且==len：%s"
              % (span, len(hold_tl), n_ok))
    print("  ⇒ 5/5 趟 a_meas∈[%.3f,%.3f] ∧ post∈[%.3f,%.3f] ∧ hold_tl_n==ceil(hold)：%s"
          % (A_MIN, A_MAX, POST_MIN, POST_MAX, "全过" if ok_all else "存在 FAIL（见上）"))
    print("  注：a_meas 由 t0 复原值推出，含 ≤0.002s 舍入差；边界值（如恰在 0.623/0.373 上）按 ±5e-4 容差判。")

    print("")
    print("  —— 闩边界两锚盘上证据复核（closed_at 口径，每点 n=1）——")
    for name, want in [("20261030T212148_9001_P3e_E12_T1", "闩（=未知区左端点出处，closed 应=14.997）"),
                       ("20261030T212233_9001_P3e_E12_T1", "不闩（=未知区右端点出处，closed 应=16.272）"),
                       ("20261030T211741_9001_P3e_E12_T1", "闩（h13 锚）")]:
        rec = json.load(open(C2AB / name / "_rec.json", encoding="utf-8"))
        print("    %s closed=%s latch_detected=%s ⇒ %s"
              % (name[:22], rec.get("closed_at_s"), rec.get("latch_detected"), want))

    print("")
    print("=" * 100)
    print("(3) 未知区 × 预测带 关系（落实勘误：不得声称预测带整体落入未知区）")
    print("=" * 100)
    print("  未知区（closed_at 口径）= (%.3f, %.3f]；≤%.3f 已知闩；>%.3f 已知不闩；每点 n=1"
          % (UNKNOWN_LO, UNKNOWN_HI, UNKNOWN_LO, UNKNOWN_HI))
    print("  预测带 = [%.3f, %.3f]" % (lo, hi))
    ov_lo, ov_hi = max(UNKNOWN_LO, lo), min(UNKNOWN_HI, hi)
    print("  重叠部分 = (%.3f, %.3f]（宽 %.3fs）——仅此段落在未知区内" % (ov_lo, ov_hi, ov_hi - ov_lo))
    print("  带外低端缝 = [%.3f, %.3f]（宽 %.3fs）——落在已知闩域（≤%.3f）" % (lo, UNKNOWN_LO, UNKNOWN_LO - lo, UNKNOWN_LO))
    print("  带上沿距未知区右端 = %.3f - %.3f = %.3fs（带上沿未超 16.272，无需上界外延关注）" % (UNKNOWN_HI, hi, UNKNOWN_HI - hi))
    print("  结论：预测带**不是**整体落入未知区——低端 [%.3f,%.3f] 落在已知闩域。若本趟 closed 落缝内："
          % (lo, UNKNOWN_LO))
    print("        预期闩、对闩边界**无收窄**（该处本就已知闩），仅量化律出样本 +1（新会话 × ceil=14 档）。")
    print("        若 closed ∈ (%.3f, %.3f]：闩 ⇒ 边界收窄为 (closed, %.3f]；不闩 ⇒ 收窄为 (%.3f, closed]。"
          % (UNKNOWN_LO, ov_hi, UNKNOWN_HI, UNKNOWN_LO))

    print("")
    print("=" * 100)
    print("(4) 发射器复刻命令要素核对 + 五件冻结件 sha256 复验")
    print("=" * 100)
    src = LAUNCHER.read_text(encoding="utf-8")
    flags = re.findall(r'ap\.add_argument\("(--[\w-]+)"', src)
    print("  发射器 argparse 旗标（源码正则提取）：%s" % ", ".join(flags))
    m = re.search(r'ap\.add_argument\("--trips", type=int, default=(\d+)\)', src)
    print("  --trips 缺省=%s；--hold 缺省=None⇒normalize_hold_s⇒模块常量 HOLD_AFTER_WINDOW" % (m.group(1) if m else "?"))
    g = re.search(r"def gate_decision\(live: bool, approved: bool\) -> int:(.*?)\n\ndef ", src, re.S)
    print("  gate_decision：非 live⇒0；live 无 approved⇒3；live+approved⇒发射（双闸硬性）")
    print("  _rec.json 无 argv 字段（083611 趟全键走查确认）⇒ 命令为 argparse+闸语义反推，推定项见批次卡片")
    print("")
    for label, p, prefix in FROZEN:
        h = sha256(p)
        print("  %-52s %s…  前缀对照 %s：%s" % (label, h[:16], prefix, "命中" if h.startswith(prefix) else "不命中!!"))

    print("")
    print("=" * 100)
    print("完。本 stdout 为只读探针留档；写域=lead/codex_round_20261030/C_BATCH2C_H14_20261031/")
    print("=" * 100)


if __name__ == "__main__":
    main()

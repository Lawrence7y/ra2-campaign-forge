# -*- coding: utf-8 -*-
"""_e12rev_mutprobe.py — 复核点1：判官灵敏度探针（新变异，不落盘改被复核件）。

方法：把驱动件+两母版复制到 tempfile 目录，仅对**内存/临时副本**做单点变异，
用自检套件的同一替身（trip_once）跑趟，看 82 项判官是否变红。
变异选择=自检 F 组 13 项之外的新面：生产缺省常量、自指常量（钩锚/源 ini 钉）、
分叉统计量语义（中位数⇒最小/最大）。只读被复核件，零真机。
"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip")
sys.path.insert(0, str(HERE))

import _drive_c2_x_e12_selftest as ST  # noqa: E402  仅借其 trip_once 夹具（不跑 main_suite）

DRIVER = ST.DRIVER_PATH.read_text(encoding="utf-8")


def run_mut(tag, old, new, mode="hang", over=None, params=None):
    """在临时目录构造变异件 ⇒ 跑同一替身 ⇒ 返回（状态, 模块/错误, rec, tl）。"""
    if old not in DRIVER:
        return ("MISS", "变异锚未命中（源码漂移）", None, None)
    d = Path(tempfile.mkdtemp(prefix="e12rev_mut_%s_" % tag))
    try:
        for nm in (ST.V2_PATH.name, ST.EC_PATH.name):
            shutil.copy2(HERE / nm, d / nm)
        p = d / "_drive_c2_x_e12.py"
        p.write_text(DRIVER.replace(old, new, 1), encoding="utf-8", newline="\n")
        for nm in ("_drive_c2_x_probe_v2", "_drive_c2_x_earlyclose"):
            sys.modules.pop(nm, None)
        sys.path.insert(0, str(d))
        try:
            spec = importlib.util.spec_from_file_location("e12rev_mut_%s" % tag, p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        finally:
            sys.path.remove(str(d))
        for nm in ("_drive_c2_x_probe_v2", "_drive_c2_x_earlyclose"):
            sys.modules.pop(nm, None)
        import _drive_c2_x_probe_v2 as _v
        import _drive_c2_x_earlyclose as _e
        sys.modules["_drive_c2_x_probe_v2"], sys.modules["_drive_c2_x_earlyclose"] = _v, _e

        # 重跑自检主件的相关判官臂：用 ST.trip_once（替身装进 m.V2），显式参数与自检同值
        rr, opsx = ST.trip_once(mode, watch_s=10.0, slow_sleep_s=1.0, latch_shot_after_s=2.0,
                               except_check_every_s=1.0, drive=m, **(over or {}))
        tlj = rr.get("_tl_inmem") or {}
        rr.pop("_tl_inmem", None)
        return ("OK", m, rr, tlj)
    except Exception as e:
        return ("EXC", repr(e)[:160], None, None)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def judge_replay(m, rr, tlj):
    """复算自检关键断言（A-01/02/05/09、B 类关键轴、schema），返回红项数。"""
    reds = []
    bad = ST.schema_check(rr, tlj)
    if bad:
        reds.append("A-09:%s" % bad[0])
    _sr = (tlj.get("_e2") or {}).get("sample_rows") or (tlj.get("_e2") or {}).get("slow_sample_rows") or []
    if not (rr.get("verdict") == "OK" and rr.get("latch_detected") is True):
        reds.append("A-01")
    _dt = [round(_sr[i + 1]["t"] - _sr[i]["t"], 3) for i in range(len(_sr) - 1)]
    if _sr and not all(abs(x - 1.0) < 0.01 for x in _dt):
        reds.append("A-02")
    if _sr and not all((x.get("cpu") or {}).get("delta_s") is not None and
                       abs(x["cpu"]["delta_s"] - 1.0) < 1e-9 for x in _sr):
        reds.append("A-05")
    if rr.get("slow_rows_n", 0) < 3:
        reds.append("A-03")
    if rr.get("hook6_state") != "present_stable":
        reds.append("A-04")
    if "P1_first_candidate" not in str(rr.get("e2_fork_label")):
        reds.append("A-06")
    if not any(s.get("tag") == "latch_plus_30" for s in rr.get("shots", [])):
        reds.append("A-07")
    _wd = rr.get("ws_delta_kb")
    _es = rr.get("e2_summary") or {}
    if isinstance(_wd, int) and _wd > 1024 and "note_ws_growing" not in _es:
        reds.append("D-08")
    # 复刻自检 D-01..D-10 的**原输入**（等值行），看变异件标签机是否仍给同结果
    def srow(dd=None, hk="present", ws=None, cpu_state="ok"):
        return {"cpu": ({"state": "ok", "delta_s": dd} if cpu_state == "ok"
                        else {"state": cpu_state, "delta_s": None}),
                "hook6": {"state": hk}, "ws_kb": ws}
    expect = [
        ("D-01", "P1_first_candidate", m.summarize_e2(True, [srow(0.99, "present", 60000), srow(1.0, "present", 60100)])),
        ("D-02", "丁_first_candidate", m.summarize_e2(True, [srow(1.0, "absent", 60000), srow(0.98, "absent", 60000)])),
        ("D-03", "blocked_family", m.summarize_e2(True, [srow(0.0, "present"), srow(0.0, "present")])),
        ("D-04", "cpu_ambiguous", m.summarize_e2(True, [srow(0.5, "present"), srow(0.5, "present")])),
        ("D-05", "cpu_axis_unreadable", m.summarize_e2(True, [{"cpu": {"state": "ok", "delta_s": None}, "hook6": {"state": "present"}, "ws_kb": 1},
                                                              {"cpu": {"state": "read_fail"}, "hook6": {"state": "present"}, "ws_kb": 1}])),
        ("D-08", "note_ws_growing", m.summarize_e2(True, [srow(1.0, "present", 60000), srow(1.0, "present", 70000)])),
    ]
    for cid, want, got in expect:
        blob = json.dumps(got, ensure_ascii=False)
        if want not in blob:
            reds.append("%s(标签机):want %s got %s" % (cid, want, got.get("e2_fork_label")))
    # 补充灵敏度对照：若判官用了**可区分多值**行（0.5,0.9），中位数变异才会显形
    f_mix = m.summarize_e2(True, [srow(0.5, "present"), srow(0.9, "present")])
    rr["_mix_probe"] = {"median_out": f_mix.get("e2_fork_label"),
                        "median_val": f_mix.get("cpu_delta_median_s")}
    return reds


CASES = [
    # (tag, old, new, 说明/预期)
    ("slow_hz_default", "SLOW_HZ_SLEEP = 1.0", "SLOW_HZ_SLEEP = 7.0",
     "生产缺省慢采节律 1Hz⇒7Hz 漂移（自检全传显式参数⇒预期不被抓=灵敏度缺口）"),
    ("latch_shot_default", "LATCH_SHOT_AFTER_S = 30.0", "LATCH_SHOT_AFTER_S = 3000.0",
     "闩+30 s 截图缺省漂移（自检传 2.0 ⇒预期不被抓）"),
    ("except_check_default", "EXCEPT_CHECK_EVERY_S = 30.0", "EXCEPT_CHECK_EVERY_S = 3000.0",
     "except 巡检 30 s 缺省漂移（自检传 0.5/1.0 ⇒预期不被抓）"),
    ("hook6_anchor_wrong", 'HOOK6_ANCHOR = "e91a1f941790"', 'HOOK6_ANCHOR = "aabbccddee11"',
     "钩锚常量改错值（替身自指同常量⇒预期不被抓，需盘面证据独立校验）"),
    ("src_ini_wrong", 'SRC_INI_SHA16 = "27c9a60c55a8a1b4"', 'SRC_INI_SHA16 = "0000000000000000"',
     "源 ini sha16 钉改错（替身自指⇒预期不被抓）"),
    ("median_to_min", "med = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0",
     "med = srt[0]", "分叉统计量 中位数⇒最小值（hang 全 1.0 同值⇒预期不被抓；D-04 双 0.5 同值）"),
    ("median_to_max", "med = srt[n // 2] if n % 2 else (srt[n // 2 - 1] + srt[n // 2]) / 2.0",
     "med = srt[-1]", "中位数⇒最大值（同上⇒预期不被抓）"),
    ("ws_note_thresh", "if ws_delta is not None and ws_delta > 1024:",
     "if ws_delta is not None and ws_delta > 10**9:",
     "ws 增长注记阈值 1MB⇒1GB（D-08 用 10000KB ⇒ 预期必红=被抓手）"),
    ("pair_index_offbyone", 'srow = {"t": row["t"], "pair_close_row_index": len(rows) - 1}',
     'srow = {"t": row["t"], "pair_close_row_index": len(rows) - 2}',
     "配对索引错位（schema_check 边界+首慢行晚于闩行⇒预期必红）"),
    ("latch_ge", "if latch is None and row.get(\"exitstate\") == LATCH_VALUE:",
     "if latch is None and not isinstance(row.get(\"exitstate\"), dict) and row.get(\"exitstate\") >= LATCH_VALUE:",
     "闩判定 ==⇒>=（读败 dict 已挡；exitstate=2/3 也触发闩⇒预期不被抓：stub 只产 0/1）"),
]


def main():
    print("== E12 复核·判官灵敏度探针（新变异面）==")
    summary = []
    for tag, old, new, desc in CASES:
        status, a, rr, tlj = run_mut(tag, old, new)
        if status == "MISS":
            print("[ANCHOR-MISS] %s %s" % (tag, desc))
            summary.append((tag, "ANCHOR-MISS"))
            continue
        if status == "EXC":
            print("[EXC] %s ⇒ 判官外异常：%s（%s）" % (tag, a, desc))
            summary.append((tag, "EXC->caught"))
            continue
        m = a
        reds = judge_replay(m, rr, tlj)
        verdict = "RED(被抓)" if reds else "GREEN(判官全过=灵敏度缺口)"
        print("[%s] %s\n    %s\n    rec: slow=%s fork=%s hook6=%s med=%s reds=%s mix对照=%s" % (
            verdict[:3], tag, desc, rr.get("slow_rows_n"), str(rr.get("e2_fork_label"))[:40],
            rr.get("hook6_state"), rr.get("cpu_delta_median_s"), reds[:3],
            rr.get("_mix_probe")))
        summary.append((tag, "RED" if reds else "GREEN"))
    print("\n== 汇总 ==")
    for t, v in summary:
        print("  %-24s %s" % (t, v))


if __name__ == "__main__":
    main()

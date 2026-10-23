"""① 判档器：读 L1 趟产物，判 V11-a 硬门禁 pre_fps15 ≥ 25。

★ 只读：不改任何母本、不改趟产物。
★ 判据来源：lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md §3.1
   V11-a 硬门禁 = 当趟 pre_fps15 ≥ 25（31 档）；<25 ⇒ 不发射（10 档）。
★ 分界依据（同设计件 §3.2）：31 档实测 pre_fps15 = 31.397 / 31.401；
   10 档 = 8.023 / 9.354 / 10.012 / 10.023 ⇒ 25 离两簇都远。
★ 同时输出 V11-c：本趟开机时刻，供跨会话不可拼 A/B 的一致性判定。
"""
import json
import sys
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
            r"\CONTINUE_20261003\lead\qc161_u0400_trip")
OUT_DIR = TRIP / "l1_20261023"
BOOT_FP_DIR = TRIP / "boot_fp_20261023"

GATE_MIN = 25.0


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def find(obj, key, path=""):
    """深度优先找第一个 key，返回 (value, path)。"""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key], path + "/" + key
        for k, v in obj.items():
            r = find(v, key, path + "/" + str(k))
            if r[0] is not None:
                return r
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            r = find(v, key, path + "[%d]" % i)
            if r[0] is not None:
                return r
    return None, None


def main():
    print("=" * 78)
    print("① 判档器 · V11-a 硬门禁（pre_fps15 ≥ %.1f）" % GATE_MIN)
    print("=" * 78)

    if not OUT_DIR.is_dir():
        print("!! 趟目录不存在: %s" % OUT_DIR)
        return 2

    rc = 0
    fails = []

    def check(name, cond, detail=""):
        nonlocal rc
        print("  %-56s %s  %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)
            rc = 1

    # ---- 0. 趟级产物存在性 ----
    print("\n[0] 趟产物")
    lr_path = OUT_DIR / "_launch_result.json"
    check("_launch_result.json 存在", lr_path.is_file(), str(lr_path.name))
    if not lr_path.is_file():
        print("\n!! 无 _launch_result.json，趟未完成")
        return 2
    lr = load(lr_path)
    print("      rc=%s  duration_s=%s  carriers_deleted=%s  leftover=%s"
          % (lr.get("rc"), lr.get("duration_s"),
             lr.get("carriers_deleted"), lr.get("leftover_procs")))
    print("      harness_sha16=%s  trip_id=%s"
          % (lr.get("harness_sha16"), lr.get("trip_id")))
    check("趟 exit code == 0", lr.get("rc") == 0, "rc=%s" % lr.get("rc"))
    check("载体已删除", lr.get("carriers_deleted") is True, "")
    check("残留进程为空", lr.get("leftover_procs") == [], "%s" % lr.get("leftover_procs"))
    check("harness = harness6 (ff8245d2)",
          lr.get("harness_sha16") == "ff8245d27b3db22a", lr.get("harness_sha16"))

    # ---- 1. 三窗 measure ----
    print("\n[1] measure 三窗")
    rows = []
    for i in range(3):
        p = OUT_DIR / ("measure_w%d.json" % i)
        if not p.is_file():
            check("measure_w%d.json 存在" % i, False, str(p.name))
            continue
        d = load(p)
        st = d.get("stats", {})
        gate = d.get("gate", {})
        rows.append({
            "w": i,
            "fps_avg": st.get("fps_avg"),
            "fps_p50": st.get("fps_p50"),
            "frame_ms_p50": st.get("frame_ms_p50"),
            "logic_frames": st.get("logic_frames"),
            "pre_fps15": gate.get("pre_fps15"),
            "units0": gate.get("units0"),
            "gate_ok": gate.get("ok"),
        })
        check("measure_w%d.json 存在" % i, True, str(p.name))

    if len(rows) != 3:
        print("\n!! 三窗不全，无法判定")
        return 2

    print("\n      %-3s %-9s %-9s %-13s %-13s %-10s %-8s"
          % ("窗", "fps_avg", "fps_p50", "frame_ms_p50", "logic_frames",
             "pre_fps15", "units0"))
    for r in rows:
        print("      W%-2d %-9s %-9s %-13s %-13s %-10s %-8s"
              % (r["w"], r["fps_avg"], r["fps_p50"], r["frame_ms_p50"],
                 r["logic_frames"], r["pre_fps15"], r["units0"]))

    # ---- 2. ★ V11-a 硬门禁 ----
    print("\n[2] ★ V11-a 硬门禁（pre_fps15 ≥ %.1f）" % GATE_MIN)
    pre = [r["pre_fps15"] for r in rows]
    check("三窗 pre_fps15 均非 None", all(v is not None for v in pre), str(pre))
    if all(v is not None for v in pre):
        mn, mx = min(pre), max(pre)
        print("      pre_fps15 范围: [%.3f, %.3f]" % (mn, mx))
        tier = "31" if mn >= GATE_MIN else ("10" if mx < GATE_MIN else "MIXED")
        print("      档位判定      : %s" % tier)
        check("V11-a 通过（min(pre_fps15) ≥ %.1f）" % GATE_MIN,
              mn >= GATE_MIN, "min=%.3f" % mn)
        check("三窗档位一致（无 MIXED）", tier != "MIXED", tier)
    else:
        tier = "unknown"

    # ---- 3. 在局闸与 units0（既有门禁，非 V11-a）----
    print("\n[3] 既有在局闸与 units0")
    check("三窗 gate.ok 全 True（MEASURE_GATE_FPS15_MIN=3.0）",
          all(r["gate_ok"] is True for r in rows), str([r["gate_ok"] for r in rows]))
    u0 = rows[0]["units0"]
    check("W1 裁决门 units0 ≥ 150", u0 is not None and u0 >= 150, "units0=%s" % u0)
    check("Arm A 基线 units0 ≥ 800（l1c/l1d 口径 881/874）",
          u0 is not None and u0 >= 800, "units0=%s" % u0)

    # ---- 4. 导航与 S4（Arm A 定义）----
    print("\n[4] 导航与 S4")
    qf = OUT_DIR / "qc151_fields.json"
    if qf.is_file():
        f = load(qf)
        nav, navp = find(f, "verdict")
        print("      首个 verdict: %s = %s" % (navp, nav))
        navv, navvp = find(f, "NAV")
        if isinstance(navv, dict):
            print("      NAV: %s" % json.dumps(navv, ensure_ascii=False)[:200])
            check("NAV.verdict == OK", navv.get("verdict") == "OK",
                  str(navv.get("verdict")))
        else:
            check("qc151_fields 含 NAV", False, str(navvp))
        s4, s4p = find(f, "hit_count")
        print("      S4 hit_count = %s  (%s)" % (s4, s4p))
        check("S4.hit_count == 0（Arm A 定义）", s4 == 0, str(s4))
    else:
        check("qc151_fields.json 存在", False, str(qf.name))

    # ---- 5. except 新增 ----
    print("\n[5] except 增量（不作唯一判据，仅记录）")
    ed = OUT_DIR / "except_set_diff.json"
    if ed.is_file():
        e = load(ed)
        print("      except_set_diff: %s" % json.dumps(e, ensure_ascii=False)[:300])
        added = e.get("added") or e.get("new") or []
        check("except 新增 0", len(added) == 0, "added=%d" % len(added))
    else:
        print("      [局限] 无 except_set_diff.json —— 不据此判未崩溃")

    # ---- 6. V11-c 开机会话一致性 ----
    print("\n[6] V11-c 开机会话一致性")
    fps = sorted(BOOT_FP_DIR.glob("boot_fingerprint_*.json"))
    fps = [p for p in fps if "_redacted" not in p.name]
    check("开机会话指纹存在", len(fps) >= 1, str([p.name for p in fps]))
    if fps:
        bf = load(fps[-1])
        print("      captured_at_local = %s" % bf.get("captured_at_local"))
        print("      env_digest        = %s" % bf.get("env_digest"))
        bl = bf.get("boot_log", {}) or {}
        evs = bl.get("events") or []
        starts = [e for e in evs if e.get("id") == 12]
        if starts:
            newest = starts[0].get("time")
            print("      最近一次开机      = %s" % newest)
            check("最近开机 = 2026-10-23T09:48:27",
                  str(newest).startswith("2026-10-23T09:48:27"), str(newest))

    # ---- 汇总 ----
    print("\n" + "=" * 78)
    if rc == 0:
        print("★ 判定：全部 PASS")
        if tier == "31":
            print("★ ① 档位 = 31 档 ⇒ V11-a 硬门禁通过，A/B 对照可解锁")
        elif tier == "10":
            print("★ ① 档位 = 10 档 ⇒ V11-a 未通过，如实报「环境不达」")
        else:
            print("★ 档位 = %s" % tier)
    else:
        print("★ 判定：%d 项 FAIL" % len(fails))
        for f in fails:
            print("   - %s" % f)
    print("=" * 78)
    return rc


if __name__ == "__main__":
    sys.exit(main())

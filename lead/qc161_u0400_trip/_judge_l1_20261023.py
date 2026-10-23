"""① 判档器：读 L1 趟产物，判 V11-a 硬门禁 pre_fps15 ≥ 25。

★ 只读：不改任何母本、不改趟产物。
★ 判据来源：lead/goal1_v11_env_gate_20261021/V11_ENV_GATE_DESIGN.md §3.1
   V11-a 硬门禁 = 当趟 pre_fps15 ≥ 25（31 档）；<25 ⇒ 不发射（10 档）。
★ 分界依据（同设计件 §3.2）：31 档实测 pre_fps15 = 31.397 / 31.401；
   10 档 = 8.023 / 9.354 / 10.012 / 10.023 ⇒ 25 离两簇都远。
★ 同时输出 V11-c：本趟开机时刻，供跨会话不可拼 A/B 的一致性判定。

★★ H-2 修复（2026-10-23）：原文一遇 w1/w2 缺失就 `return 2`，把两种完全不同的
   情形混成一句「三窗不全」：
     (a) **设计内短路** —— harness §5.4 / D-4 / harness7 late-start 闸让
         `_measure_run` 在采样窗前就 `return`，**按设计只落 w0**；
     (b) **产物丢失** —— 该落而没落。
   后果：10-23 四趟（全 `no_advance`）与 harness7 的 `late_start` 趟都会被判成
   「无法判定」，判档器在短路上永远给不出结论（台账 §397 H-2）。
   现改为**先读 w0 的 verdict 再分流**，并用退出码区分。

★ 退出码（H-2 新增 3/4，0/1/2 语义不变）：
     0 全部 PASS
     1 有检查项 FAIL
     2 不可判定（趟未完成 / w0=ok 却缺窗 = 真·产物异常）
     3 **设计内短路**：verdict ∈ SHORT_CIRCUIT_VERDICTS ⇒ 本趟未取得档位证据
     4 **产物丢失**：趟报 rc=0 但 measure_w0.json 不存在
   3/4 都 ≠ 0，调用方按 `rc==0` 判通过的行为不受影响。
"""
import argparse
import json
import re
import sys
from pathlib import Path

TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
            r"\CONTINUE_20261003\lead\qc161_u0400_trip")
OUT_DIR = TRIP / "l1_20261023"
BOOT_FP_DIR = TRIP / "boot_fp_20261023"

GATE_MIN = 25.0

# ★ H-2：设计内短路 verdict 集 —— 这些值意味着 `_measure_run` 在采样窗前就
#   `return`，**按设计只落 w0**，w1/w2 缺失是正常不是缺陷。
SHORT_CIRCUIT_VERDICTS = ("no_advance", "tier_invalid", "late_start", "error")
#   no_advance / tier_invalid：harness §5.4 / D-4（母本既有）
#   late_start：harness7 新增（measure 起始硬约束，只在短路生效时判）
#   error：`_measure_error_payload` 占位（如窗前异常）；同样是「没进采样窗」
#
# ★ H-2：逐窗 verdict 的**正常完成**取值（三窗齐全时必须是这些）
WINDOW_OK_VERDICTS = ("ok", "empty", "degraded")

# ★★ H-2 附带的第二个缺陷：原文把 harness 哈希焊死为 harness6 的 ff8245d2。
#   这在当时是对的（只有一版 harness），但它让 **任何** harness 换版后的趟
#   一进场就被判 FAIL，且理由显示成「harness 不是 harness6」——与档位无关。
#   改为「必须落在已知 harness 清单内」，并把实际值打出来。
KNOWN_HARNESS = {
    "ff8245d27b3db22a": "harness6（母本，463,219 B）",
    "d019e8beecfb5fd8": "harness7（D-05 补丁副本，472,020 B）",
}
HARNESS7_SHA16 = "d019e8beecfb5fd8"

# ★★ H-2e（§407）：D-05 冒烟验收的 5 条判据（S399 §九）此前**判档器一条都不读**。
#   真机三趟跑完，`h7_fs_rect_wait_skipped` / `pre_capture_wait_polls` /
#   `h7_nav_to_measure` 全在 `qc151_fields.json` 里，但判档器输出里看不到 ⇒
#   冒烟等于没验（证据在盘上却无人读，与 §401 的 H-5 同型教训）。
#   ⇒ 本区只在**该趟确实由 harness7 跑出**时生效，harness6 趟不受影响。
#   ★ 判据取值来自 S399 §九 的设计预期，**不是**从产物反推的：
H7_SMOKE = {
    # 窗口模式：短路不该出现；polls 与 harness6 同量级（历史窗口趟实测 0）
    "windowed": {"skipped": False, "polls_max": 5, "frame_s_max": None},
    # 全屏短路：polls 必须归零，frame 段必须从 ~125 s 掉到 <2 s
    "fullscreen_short": {"skipped": True, "polls_max": 0, "frame_s_max": 2.0},
    # 对照臂：polls 必须回到 244–253，frame 段回到 ~125 s
    "fullscreen_keep": {"skipped": False, "polls_min": 200, "frame_s_min": 100.0},
}

EXIT_PASS, EXIT_FAIL, EXIT_UNDECIDABLE = 0, 1, 2
EXIT_SHORT_CIRCUIT = 3
EXIT_ARTIFACT_LOST = 4


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def find(obj, key, path=""):
    """深度优先找第一个 **dict 键**，返回 (value, path)。

    ★ H-2 附带的第三个缺陷：本函数找的是**字典键**，而 `qc151_fields.json`
      是一份**记录列表**（每项 `{group,key,value,source,note,ts}`）——
      `NAV` 是 `group` 字段的**值**、`hit_count` 是 `S4` 组里的 `key` 值。
      于是 `find(f, "NAV")` 永远返回 None，[4] 段那两条断言**从写下那天起
      就没可能 PASS**；它们只是被前面「三窗不全即 return」挡着，从没被执行过。
      改用 `field_records()` 按 (group, key) 取值。
      ★ 保留本函数：`_launch_result.json` 等真·字典产物仍用它。
    """
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


def field_records(obj):
    """把 qc151_fields.json 的**记录列表**规范化成 [(group, key, value)]。

    ★ 兼容两种形态：记录列表（真机产物）与 dict（万一将来改格式）。
    """
    out = []
    if isinstance(obj, list):
        for r in obj:
            if isinstance(r, dict) and "group" in r and "key" in r:
                out.append((str(r.get("group")), str(r.get("key")),
                            r.get("value")))
    elif isinstance(obj, dict):
        # 非预期格式：整份塞成一条，让下游断言自然 FAIL 而不是静默通过
        out.append(("<dict>", "<dict>", obj))
    return out


def rec_get(recs, group, key):
    """按 (group, key) 取**最后一条**记录的值（同键多次读写时取末次）。"""
    hit = [v for (g, k, v) in recs if g == group and k == key]
    return hit[-1] if hit else None


def h7_smoke_section(lr, check, out_dir):
    """★★ H-2e（§407）：harness7 冒烟验收判据。

    ★★ 为什么必须是**独立函数**：本判档器在「设计内短路」分支里会 `return`
    （那正是全屏短路臂的正常结局），而冒烟判据恰恰要在那种趟上生效。
    写成脚本中段的顺序代码，等于**真机冒烟趟一条都执行不到**。

    ★ 判据来源是**产物自身**，不看命令行记忆：
      `h7_fs_rect_wait_skipped.skipped=True`      ⇒ 全屏短路臂
      `skipped=False` 且 `pre_capture_wait_polls≥200` ⇒ 对照臂
      `skipped=False` 且 polls 很小              ⇒ 窗口模式
    """
    qf = Path(out_dir) / "qc151_fields.json"
    print("\n[4b] ★★ harness7 冒烟验收（S399 §九 五条判据）")
    if not qf.is_file():
        print("      [局限] 无 qc151_fields.json ⇒ 冒烟判据无从判读（不是通过）")
        return
    recs7 = field_records(load(qf))
    sk = rec_get(recs7, "FRAME", "h7_fs_rect_wait_skipped")
    polls = rec_get(recs7, "FRAME", "pre_capture_wait_polls")
    n2m = rec_get(recs7, "MEASURE", "h7_nav_to_measure")
    skipped = sk.get("skipped") if isinstance(sk, dict) else (
        None if sk is None else bool(sk))
    frame_s = rec_get(recs7, "BUDGET", "stage_seconds:frame")

    print("      h7_fs_rect_wait_skipped = %s" % (skipped,))
    print("      pre_capture_wait_polls   = %s" % (polls,))
    print("      stage_seconds:frame      = %s" % (frame_s,))
    if n2m is not None:
        print("      h7_nav_to_measure        = %s" % (n2m,))

    # ★ 是否是 **有效** harness7 冒烟趟：需要**同时**满足两条
    #   ① 趟由 harness7 跑出（哈希对得上，或产物里有 h7_* 记录）
    #   ② 冒烟判据**所需的字段确实在场**（skipped 与 polls）
    #   ★★ 只判①会出岔子（§407 回归实测 B2 变红）：harness7 的趟若在 window 阶段
    #     就失败，`h7_fs_rect_wait_skipped` 根本不会被写 —— 那种趟**不是**冒烟样本，
    #     用冒烟判据要求它「skipped == False」是拿设计预期去判一个没跑到那里的趟。
    #   ⇒ 缺字段时**明确报「不是冒烟样本」**，不产生断言（既不算通过也不算失败）。
    is_h7_run = (lr.get("harness_sha16") == HARNESS7_SHA16) or (sk is not None) or (n2m is not None)
    if not is_h7_run:
        print("      [跳过] 本趟不是 harness7（harness_sha16=%s，无 h7_* 记录）"
              " ⇒ 冒烟判据不适用，**不是通过**" % lr.get("harness_sha16"))
        return
    if sk is None or polls is None:
        print("      [跳过] 本趟虽由 harness7 跑出，但冒烟字段缺失"
              "（h7_fs_rect_wait_skipped=%s / pre_capture_wait_polls=%s）"
              " ⇒ **不是冒烟样本**（多半在 window 阶段就失败了），"
              "不产生冒烟断言" % (sk, polls))
        return

    check("★ 本趟确为 harness7 冒烟样本 ⇒ 判据适用", True, "h7 记录齐全")

    if skipped is True:
        form = "fullscreen_short"
    elif polls is not None and polls >= 200:
        form = "fullscreen_keep"
    else:
        form = "windowed"
    print("      ⇒ 形态（由产物判定）: %s" % form)
    exp = H7_SMOKE[form]

    check("★ h7_fs_rect_wait_skipped == %s（%s 臂的设计预期）"
          % (exp["skipped"], form),
          skipped is exp["skipped"], "实测 %s" % (skipped,))
    if "polls_max" in exp:
        check("★ pre_capture_wait_polls ≤ %d（%s 臂）" % (exp["polls_max"], form),
              polls is not None and polls <= exp["polls_max"], "实测 %s" % (polls,))
    if "polls_min" in exp:
        check("★ pre_capture_wait_polls ≥ %d（%s 臂）" % (exp["polls_min"], form),
              polls is not None and polls >= exp["polls_min"], "实测 %s" % (polls,))
    if exp.get("frame_s_max") is not None:
        check("★★ stage_seconds:frame < %.1f s（全屏短路臂的核心收益）"
              % exp["frame_s_max"],
              frame_s is not None and frame_s < exp["frame_s_max"],
              "实测 %s（harness6 历史 122–127 s）" % (frame_s,))
    if exp.get("frame_s_min") is not None:
        check("★ stage_seconds:frame ≥ %.1f s（对照臂必须保持原等待）"
              % exp["frame_s_min"],
              frame_s is not None and frame_s >= exp["frame_s_min"],
              "实测 %s" % (frame_s,))

    late = n2m.get("late_start") if isinstance(n2m, dict) else None
    if form == "fullscreen_keep":
        # ★ S399 §九 第 3 条：对照臂**不得**出现 late_start
        check("★★ 对照臂 late_start 不得出现（前置条件按设计生效）",
              late is not True, "late_start=%s" % (late,))
    if form == "fullscreen_short":
        # ★ 第 2 趟的 nav_to_measure_s 是边界 2 的唯一实测数
        val = n2m.get("nav_to_measure_s") if isinstance(n2m, dict) else None
        check("★★ 全屏短路臂记录了 nav_to_measure_s（边界 2 的唯一实测数）",
              val is not None, "%s" % (val,))
        if val is not None:
            print("      ⇒ nav_to_measure_s = %.3f s"
                  "（90 s 阈值是否需重标看这个数）" % val)


def main():
    # ★ H-2：加 `--trip-dir`，否则本工具只能判焊死的那一个趟目录 ——
    #   而 H-2 的整个议题就是「不同死法的趟要能被分别判读」。
    global OUT_DIR, BOOT_FP_DIR
    _ap = argparse.ArgumentParser(
        description="① 判档器（V11-a 硬门禁）。只读，不改趟产物。")
    _ap.add_argument("--trip-dir", default=None,
                     help="趟产物目录（缺省 %s）" % OUT_DIR)
    _a = _ap.parse_args()
    _is_default_trip = _a.trip_dir is None
    if not _is_default_trip:
        OUT_DIR = Path(_a.trip_dir)
        # 开机指纹目录按同日命名约定取同级 dir（boot_fp_<YYYYMMDD>）。
        # ★ 不能取目录名的最后一段：趟目录形如 l1_20261023c，末段是
        #   `20261023c`（带字母后缀）⇒ 会推成 boot_fp_20261023c（不存在）。
        #   故用正则取 8 位日期。
        _m = re.search(r"(\d{8})", OUT_DIR.name)
        if _m:
            BOOT_FP_DIR = OUT_DIR.parent / ("boot_fp_" + _m.group(1))
        print("★ 趟目录（CLI 覆盖）: %s" % OUT_DIR)
        print("★ 开机指纹目录      : %s" % BOOT_FP_DIR)

    print("=" * 78)
    print("① 判档器 · V11-a 硬门禁（pre_fps15 ≥ %.1f）" % GATE_MIN)
    print("=" * 78)

    if not OUT_DIR.is_dir():
        print("!! 趟目录不存在: %s" % OUT_DIR)
        return EXIT_UNDECIDABLE

    rc = EXIT_PASS
    fails = []

    def check(name, cond, detail=""):
        nonlocal rc
        print("  %-56s %s  %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)
            rc = EXIT_FAIL

    # ---- 0. 趟级产物存在性 ----
    print("\n[0] 趟产物")
    lr_path = OUT_DIR / "_launch_result.json"
    # ★★ H-2d（2026-10-24 发现）：**并非所有发射器都写 `_launch_result.json`**。
    #   `_launch_monitored_20261023.py` 只写 `_v11a_concurrent_clock.json`
    #   （含 `harness_rc` / `duration_s` / `gemamd_pid`），是设计如此，不是趟未完成。
    #   原文一遇缺文件就 `return 2「趟未完成」` ⇒ C 趟（l1_20261023c）被判成
    #   「趟未完成」，而它其实**跑完了**（harness_rc=0、181 s、旁路 14215 样本）。
    #   ⇒ 改为「找得到**任一**趟级收官产物即可继续」，并如实标注来源。
    _side = OUT_DIR / "_v11a_concurrent_clock.json"
    if not lr_path.is_file() and not _side.is_file():
        print("!! 既无 _launch_result.json 也无 _v11a_concurrent_clock.json")
        print("★ 判定：趟未完成 / 产物全缺（EXIT=%d）" % EXIT_UNDECIDABLE)
        return EXIT_UNDECIDABLE
    if lr_path.is_file():
        lr = load(lr_path)
        _lr_src = "_launch_result.json"
    else:
        _s = load(_side)
        lr = {"rc": _s.get("harness_rc"),
              "duration_s": _s.get("duration_s"),
              "trip_id": _s.get("trip_id"),
              "harness_sha16": _s.get("harness_sha16"),
              "leftover_procs": None,
              "carriers_deleted": None,
              "_side_only": True}
        _lr_src = "_v11a_concurrent_clock.json（旁路发射器不写 launch_result）"
        print("★ 趟级产物来源: %s" % _lr_src)
    print("      rc=%s  duration_s=%s  carriers_deleted=%s  leftover=%s"
          % (lr.get("rc"), lr.get("duration_s"),
             lr.get("carriers_deleted"), lr.get("leftover_procs")))
    print("      harness_sha16=%s  trip_id=%s"
          % (lr.get("harness_sha16"), lr.get("trip_id")))
    check("趟 exit code == 0", lr.get("rc") == 0, "rc=%s" % lr.get("rc"))
    if lr.get("_side_only"):
        print("  [局限] 旁路发射器不记 carriers_deleted / leftover_procs"
              " ⇒ 这两项不作断言（不是通过，是没数据）")
    else:
        check("载体已删除", lr.get("carriers_deleted") is True, "")
        check("残留进程为空", lr.get("leftover_procs") == [],
              "%s" % lr.get("leftover_procs"))
    # ★ H-2：由「== ff8245d2」改为「落在已知清单内」。
    #   ★ 判据仍带取值比较（不是只判非空），且清单本身是显式枚举 ——
    #   把一个未知哈希塞进来必 FAIL，可被变异杀掉。
    #   ★ 2026-10-21 及其更早的趟 `_launch_result.json` 里**没有** harness_sha16
    #     字段（那时的发射器不记），故要区分「字段缺失」与「哈希未知」两种 FAIL，
    #     否则会让人以为「换了个陌生 harness」。
    _h = lr.get("harness_sha16")
    check("harness 在已知清单内（harness6/harness7）",
          _h in KNOWN_HARNESS,
          ("%s = %s" % (_h, KNOWN_HARNESS[_h])) if _h in KNOWN_HARNESS
          else ("★ 旁路发射器不记 harness_sha16（该字段只在主发射器产物里）"
                if lr.get("_side_only")
                else ("★ 该趟产物未记录 harness_sha16（早于该字段引入）"
                      if _h is None
                      else "%s = ★ 未知版本（不在清单内）" % _h)))

    # ---- 1. ★★ H-2：先读 w0 verdict 再决定「缺窗」是设计内还是产物异常 ----
    print("\n[1] measure 三窗")
    w0p = OUT_DIR / "measure_w0.json"
    w0_v = None
    if not w0p.is_file():
        # 趟报 rc=0 却连 w0 都没有 ⇒ 真·产物丢失（不是短路：短路必落 w0）
        print("!! measure_w0.json 不存在")
        print("★ 判定：产物丢失（EXIT=%d）—— 趟 rc=0 但按设计至少应落 w0；"
              "短路路径必落 w0，故缺 w0 ≠ 短路" % EXIT_ARTIFACT_LOST)
        return EXIT_ARTIFACT_LOST
    w0 = load(w0p)
    w0_v = w0.get("verdict")
    w0_g = w0.get("gate") or {}
    print("      w0.verdict   = %s" % w0_v)
    print("      w0.gate      = pre_fps15=%s units0=%s ok=%s"
          % (w0_g.get("pre_fps15"), w0_g.get("units0"), w0_g.get("ok")))
    print("      w0.error     = %s" % w0.get("error"))

    if w0_v in SHORT_CIRCUIT_VERDICTS:
        # ★ 设计内短路：harness 在采样窗前 return，w1/w2 按设计不存在。
        #   ★ 这类趟**没有取得档位证据**，故不能 PASS；但它也**不是**判档器
        #   自身无法判定 —— 死法已由 verdict 明确给出。
        print("\n      ⇒ w0.verdict ∈ 设计内短路集 %s" % (SHORT_CIRCUIT_VERDICTS,))
        print("      ⇒ w1/w2 按设计不落（harness 在采样窗前 return，非产物丢失）")
        print("\n★ 判定：本趟为设计内短路（EXIT=%d），未取得档位证据"
              % EXIT_SHORT_CIRCUIT)
        print("   死法 = %s；error = %s" % (w0_v, w0.get("error")))
        if w0_v == "no_advance" and w0_g.get("units0") is not None:
            print("   ★ R-§397 已知后果：units0=%s 有值 ⇒ 进程活着、帧冻结"
                  " ⇒ 是「测不到」不是「档位不够」" % w0_g.get("units0"))
        elif w0_g.get("units0") is None:
            print("   ★ w0.gate.units0 为 None ⇒ 进程可能已死（RPM 失败）；"
                  "与上一种死法不同，须分开记（H-5 档）")
        if w0_v == "late_start":
            h7 = w0.get("h7") or {}
            # ★ H-2e：字段名以 **harness7 实际写入**为准。实测 harness7 `:4994`
            #   写的是 `limit_s`，而本行原文读 `max_nav_to_w0_s` —— 那个键
            #   在 harness7 里**根本不存在**（全仓 grep 仅此一处），
            #   ⇒ 真机冒烟跑出来后阈值恒显示 None。
            #   两键都接受（未来若改名也能读），并显式标注取到了哪个。
            _limit = h7.get("limit_s")
            if _limit is None:
                _limit = h7.get("max_nav_to_w0_s")
                _lim_src = "max_nav_to_w0_s（兼容旧名）"
            else:
                _lim_src = "limit_s"
            print("   ★ harness7 late-start 闸生效：nav_to_measure_s=%s"
                  "（阈值 %s s，取自 %s）"
                  % (h7.get("nav_to_measure_s"), _limit, _lim_src))
            print("   ★ 本趟正是 D-05 §6 边界 2 的实测样本 —— "
                  "这个数字决定 90 s 阈值是否需重标")
            check("late_start 趟的 nav_to_measure_s 有值",
                  h7.get("nav_to_measure_s") is not None,
                  "%s" % h7.get("nav_to_measure_s"))
            check("late_start 确实超阈值（阈值取自产物，不是常量）",
                  _limit is not None
                  and h7.get("nav_to_measure_s") is not None
                  and h7["nav_to_measure_s"] > _limit,
                  "n2m=%s limit=%s" % (h7.get("nav_to_measure_s"), _limit))
        # ★★ H-2e：短路分支也必须跑冒烟判据 —— 全屏短路臂本来就走这里。
        h7_smoke_section(lr, check, OUT_DIR)
        return EXIT_SHORT_CIRCUIT

    if w0_v not in WINDOW_OK_VERDICTS:
        print("\n★ 判定：w0.verdict=%r 既非短路集也非正常完成集"
              % (w0_v,))
        print("   ⇒ 判据未覆盖此取值，按不可判定处理（不改判据蒙过去）")
        return EXIT_UNDECIDABLE

    rows = [{"w": 0,
             "fps_avg": (w0.get("stats") or {}).get("fps_avg"),
             "fps_p50": (w0.get("stats") or {}).get("fps_p50"),
             "frame_ms_p50": (w0.get("stats") or {}).get("frame_ms_p50"),
             "logic_frames": (w0.get("stats") or {}).get("logic_frames"),
             "pre_fps15": w0_g.get("pre_fps15"),
             "units0": w0_g.get("units0"),
             "gate_ok": w0_g.get("ok"),
             "verdict": w0_v}]
    for i in (1, 2):
        p = OUT_DIR / ("measure_w%d.json" % i)
        if not p.is_file():
            # 走到这里说明 w0 是正常完成值 ⇒ 该落而没落 = 真·产物异常
            check("measure_w%d.json 存在" % i, False,
                  "%s（w0.verdict=%s 属正常完成 ⇒ 缺窗即产物异常）"
                  % (p.name, w0_v))
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
            "verdict": d.get("verdict"),
        })
        check("measure_w%d.json 存在" % i, True, str(p.name))

    if len(rows) != 3:
        print("\n!! w0 正常完成但 w1/w2 缺失 ⇒ 产物异常（非设计内短路）")
        return EXIT_UNDECIDABLE

    print("\n      %-3s %-9s %-9s %-13s %-13s %-10s %-8s %-8s"
          % ("窗", "fps_avg", "fps_p50", "frame_ms_p50", "logic_frames",
             "pre_fps15", "units0", "verdict"))
    for r in rows:
        print("      W%-2d %-9s %-9s %-13s %-13s %-10s %-8s %-8s"
              % (r["w"], r["fps_avg"], r["fps_p50"], r["frame_ms_p50"],
                 r["logic_frames"], r["pre_fps15"], r["units0"], r["verdict"]))

    # ---- 2. ★ V11-a 硬门禁 ----
    print("\n[2] ★ V11-a 硬门禁（pre_fps15 ≥ %.1f）" % GATE_MIN)
    # ★ H-2：三窗齐全但逐窗 verdict 不是正常完成值 ⇒ 该窗的 stats 不可用作
    #   档位证据（例如 w1 窗内异常落 error）。先断言，再判档位。
    bad_v = [r for r in rows if r["verdict"] not in WINDOW_OK_VERDICTS]
    check("三窗 verdict 均属正常完成集 %s" % (WINDOW_OK_VERDICTS,),
          not bad_v,
          str([(r["w"], r["verdict"]) for r in bad_v]) if bad_v else "ok")
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
        recs = field_records(f)
        print("      记录条数: %d（group 数 %d）"
              % (len(recs), len({g for g, _k, _v in recs})))
        nav_v = rec_get(recs, "NAV", "verdict")
        print("      NAV.verdict = %s" % nav_v)
        check("NAV.verdict == OK", nav_v == "OK", str(nav_v))
        s4 = rec_get(recs, "S4", "hit_count")
        print("      S4.hit_count = %s" % s4)
        check("S4.hit_count == 0（Arm A 定义）", s4 == 0, str(s4))
    else:
        check("qc151_fields.json 存在", False, str(qf.name))

    # ---- 4b. ★★ H-2e（§407）：harness7 冒烟验收判据 ----
    #   ★★ 判据本体在 `h7_smoke_section()` 里，**不是**这里的内联代码。
    #      原因：全屏短路臂的正常结局就是「设计内短路 ⇒ return 3」，
    #      内联在这条 return 之后等于**真机冒烟趟一条都执行不到**。
    #      本调用点只服务「三窗齐全」的趟（窗口模式 / 对照臂走完三窗时）。
    h7_smoke_section(lr, check, OUT_DIR)

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
    fps = sorted(BOOT_FP_DIR.glob("boot_fingerprint_*.json")) if BOOT_FP_DIR.is_dir() else []
    fps = [p for p in fps if "_redacted" not in p.name]
    check("开机会话指纹存在", len(fps) >= 1,
          str([p.name for p in fps]) if fps else "目录=%s" % BOOT_FP_DIR)
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
            # ★ H-2：原判据把开机时刻焊死为 2026-10-23T09:48:27 —— 那只是
            #   l1_20261023 这一趟所属的会话。换趟目录后这条必 FAIL，且 FAIL
            #   理由与被判的趟无关。改为「只在判缺省趟时做定值比对」，
            #   其它趟只打印、不断言（该值不是本工具的判据对象）。
            if _is_default_trip:
                check("最近开机 = 2026-10-23T09:48:27",
                      str(newest).startswith("2026-10-23T09:48:27"), str(newest))
            else:
                print("      [跳过] 开机时刻定值比对只对缺省趟有意义"
                      "（--trip-dir 指定的趟不限会话）")

    # ---- 汇总 ----
    print("\n" + "=" * 78)
    if rc == EXIT_PASS:
        print("★ 判定：全部 PASS")
        if tier == "31":
            print("★ ① 档位 = 31 档 ⇒ V11-a 硬门禁通过，A/B 对照可解锁")
        elif tier == "10":
            print("★ ① 档位 = 10 档 ⇒ V11-a 未通过，如实报「环境不达」")
        else:
            print("★ 档位 = %s" % tier)
    else:
        print("★ 判定：%d 项 FAIL（EXIT=%d）" % (len(fails), rc))
        for f in fails:
            print("   - %s" % f)
    print("=" * 78)
    return rc


if __name__ == "__main__":
    sys.exit(main())

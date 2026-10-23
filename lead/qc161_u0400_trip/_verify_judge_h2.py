"""H-2 修复的离线验证器：值证明 + 变异击杀。

## 验的是什么

`_judge_l1_20261023.py` 的 H-2 修复要证明的**不是**「代码里出现了某个字符串」，
而是**同一个判档器对不同死法的趟给出不同的、可区分的结果**。故本验证器
不读判档器源码里的字面量，而是：

  1. 造合成趟目录（JSON 产物，写在仓外 tmp）；
  2. **当成黑盒跑判档器**，读它的**进程退出码**；
  3. 对每个断言配一条变异：把被测分支改坏，跑同一个合成趟，
     要求**退出码必须变**。变不了 ⇒ 该断言是恒真式，作废。

## 为什么用退出码当判据

H-2 的原缺陷正是「退出码一律 2，不可区分」。所以退出码就是被测物的**输出值**，
不是它的内部实现。判据落在消费方（调用方看 rc），不落在供给方（源码里有没有 return）。

## 变异必须打在真产物上

变异体由**判档器源文件**文本替换生成（不是重新写一份等价的），跑的是真解释器。
若变异锚点在源文件里不唯一 ⇒ 直接报错退出，不做「找第一个」的将就。

## 与 Mimosa 的关系

本文件不 `exec` / 不 `compile` 动态源码。变异体是**写到 tmp 下的 .py 文件再
以子进程运行**，与人工改一行再跑是同一件事。
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

JUDGE = Path(__file__).with_name("_judge_l1_20261023.py")
TRIP_ROOT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
                 r"\CONTINUE_20261003\lead\qc161_u0400_trip")

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))


# ---------------------------------------------------------------- 合成趟

def make_trip(root, name, *, rc=0, harness="ff8245d27b3db22a",
              windows=None, verdicts=None, pre=31.4, units0=881,
              with_launch=True, gate_ok=True, nav=True, hit=0,
              sc_units0=None):
    """造一个合成趟目录。windows = 要落几个 measure_wN.json。

    verdicts: 逐窗 verdict 列表（长度须 == windows）。
    sc_units0: 非正常完成窗（短路/异常窗）的 units0。★ 真机 l1_20261023 的
      no_advance 趟是 units0=672（进程活着、帧冻结 ⇒ 有值），
      而 l3_20261023 是 units0=None（进程已死）—— 两种死法都在真机出现过，
      故这里必须能分别造，不能一律置 None。
    """
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    if with_launch:
        (d / "_launch_result.json").write_text(json.dumps({
            "rc": rc, "duration_s": 180.0, "trip_id": "SYNTH-" + name,
            "harness": "synth", "harness_sha16": harness,
            "carriers_deleted": True, "leftover_procs": [],
        }, ensure_ascii=False), encoding="utf-8")
    for k in range(windows or 0):
        v = (verdicts or ["ok"] * (windows or 0))[k]
        _u0 = (units0 if v == "ok"
               else (sc_units0 if sc_units0 is not None else None))
        payload = {
            "schema": "MEASURE_V1", "trip_id": "SYNTH-" + name,
            "window": k, "hz": 500,
            "span_s": 25.0 if v == "ok" else 4.0,
            "settle_s": 4.0 if k == 0 else 0.0,
            "gate": {"pre_fps15": (pre if v == "ok" else None),
                     "units0": _u0,
                     "ok": (gate_ok if v == "ok" else False)},
            "stats": {"fps_avg": pre, "fps_p50": pre, "frame_ms_p50": 33.0,
                      "logic_frames": 3800 if v == "ok" else 0},
            "verdict": v, "error": None if v == "ok" else "synthetic",
        }
        (d / ("measure_w%d.json" % k)).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    # ★ qc151_fields.json 是**记录列表**（真机产物形态）：
    #   [{group,key,value,source,note,ts}, ...]；`NAV` 是 group 的**值**，
    #   `hit_count` 是 S4 组里的 key。用手写 dict 造出来的「合成趟」会
    #   掩盖判档器读错格式的缺陷 —— 故这里必须与真机同构。
    fields = []
    if nav:
        fields.append({"group": "NAV", "key": "verdict", "value": "OK",
                       "source": "script:nav", "note": "", "ts": "synth"})
    fields.append({"group": "S4", "key": "hit_count", "value": hit,
                   "source": "script:s4", "note": "", "ts": "synth"})
    (d / "qc151_fields.json").write_text(
        json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    (d / "except_set_diff.json").write_text(
        json.dumps({"added": []}, ensure_ascii=False), encoding="utf-8")
    bfp = root / "boot_fp_20261023"
    bfp.mkdir(parents=True, exist_ok=True)
    (bfp / "boot_fingerprint_20261023T095655_synth.json").write_text(
        json.dumps({"captured_at_local": "2026-10-23T09:56:55",
                    "env_digest": "synth",
                    "boot_log": {"events": []}}, ensure_ascii=False),
        encoding="utf-8")
    return d


def run(judge_path, trip_dir):
    """跑判档器，返回（退出码, 合并输出）。★ 判据只看退出码。"""
    p = subprocess.run([sys.executable, str(judge_path),
                        "--trip-dir", str(trip_dir)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# ---------------------------------------------------------------- 变异

def mutate(src, anchor, repl, label):
    """在判档器源文本上做**唯一锚点**替换，返回变异源。锚点不唯一即报错。"""
    n = src.count(anchor)
    if n != 1:
        raise SystemExit("★ 变异 %s 锚点不唯一（出现 %d 次）—— 拒绝将就：%r"
                         % (label, n, anchor[:80]))
    return src.replace(anchor, repl)


def main():
    if not JUDGE.is_file():
        raise SystemExit("判档器不存在: %s" % JUDGE)
    src = JUDGE.read_text(encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="h2judge_"))
    try:
        print("=" * 78)
        print("H-2 判档器修复验证（合成趟黑盒 + 变异击杀）")
        print("=" * 78)

        # ---- A 组：三种「缺窗」死法必须可区分 ----
        print("\nA 组：缺 w1/w2 的三种情形必须给出三个不同退出码")
        t_short = make_trip(tmp, "t_short_20261023", windows=1,
                            verdicts=["no_advance"], sc_units0=672)
        t_alive = make_trip(tmp, "t_dead_20261023", windows=1,
                            verdicts=["no_advance"], sc_units0=None)
        t_lost = make_trip(tmp, "t_lost_20261023", windows=0)
        t_anom = make_trip(tmp, "t_anom_20261023", windows=1, verdicts=["ok"])

        rc_s, out_s = run(JUDGE, t_short)
        rc_l, out_l = run(JUDGE, t_lost)
        rc_a, out_a = run(JUDGE, t_anom)
        rc_d, out_d = run(JUDGE, t_alive)

        rec("A1 设计内短路（w0=no_advance，缺 w1/w2）⇒ EXIT=3",
            rc_s == 3, "rc=%d" % rc_s)
        rec("A2 产物丢失（连 w0 都没有）⇒ EXIT=4", rc_l == 4, "rc=%d" % rc_l)
        rec("A3 w0=ok 却缺 w1/w2（真·产物异常）⇒ EXIT=2", rc_a == 2,
            "rc=%d" % rc_a)
        rec("A4 三者两两不等（这才是 H-2 的命题本身）",
            len({rc_s, rc_l, rc_a}) == 3, "%s" % [rc_s, rc_l, rc_a])
        rec("A5 短路趟输出点名死法（不是「无法判定」）",
            "no_advance" in out_s and "三窗不全" not in out_s,
            "含 no_advance=%s" % ("no_advance" in out_s))
        # ★ A6/A7：短路趟内部还要再分死法 —— 真机两种都出现过：
        #   l1_20261023/b units0=672（进程活、帧冻结）vs l3_20261023 为 None（进程死）
        rec("A6 units0 有值 ⇒ 输出判为「帧冻结/测不到」不是「档位不够」",
            "帧冻结" in out_s or "测不到" in out_s, "")
        rec("A7 units0 为 None ⇒ 输出判为「进程可能已死」",
            "进程可能已死" in out_d, "")
        rec("A8 两种死法的文案不同（同一 verdict 也能分开记）",
            out_s != out_d, "")

        # ---- B 组：harness 版本门 ----
        print("\nB 组：harness 版本门（由「焊死 ff8245d2」改为「已知清单」）")
        t_h6 = make_trip(tmp, "t_h6_20261023", windows=3,
                         harness="ff8245d27b3db22a")
        t_h7 = make_trip(tmp, "t_h7_20261023", windows=3,
                         harness="d019e8beecfb5fd8")
        t_hx = make_trip(tmp, "t_hx_20261023", windows=3,
                         harness="deadbeefdeadbeef")
        rc6, o6 = run(JUDGE, t_h6)
        rc7, o7 = run(JUDGE, t_h7)
        rcx, ox = run(JUDGE, t_hx)
        rec("B1 harness6 三窗齐全 ⇒ 全 PASS（EXIT=0）", rc6 == 0, "rc=%d" % rc6)
        rec("B2 harness7 三窗齐全 ⇒ 同样 PASS（换版不再一进门就红）",
            rc7 == 0, "rc=%d" % rc7)
        rec("B3 未知 harness ⇒ FAIL（EXIT=1）", rcx == 1, "rc=%d" % rcx)
        rec("B4 未知 harness 的失败理由点名『未知版本』",
            "未知版本" in ox, "")
        # ★ B5：字段缺失 ≠ 哈希未知 —— 早于该字段的趟不能被说成「陌生 harness」
        t_hnone = make_trip(tmp, "t_hnone_20261023", windows=3, harness=None)
        t_hnone.joinpath("_launch_result.json").write_text(json.dumps({
            "rc": 0, "duration_s": 180.0, "trip_id": "SYNTH-none",
            "carriers_deleted": True, "leftover_procs": [],
        }, ensure_ascii=False), encoding="utf-8")
        rcn, on = run(JUDGE, t_hnone)
        rec("B5 harness_sha16 字段缺失 ⇒ FAIL 且理由为『未记录』非『未知版本』",
            rcn == 1 and "未记录" in on and "未知版本" not in on,
            "rc=%d" % rcn)

        # ---- C 组：10 档仍必须被判不达标（不因放宽而假绿）----
        print("\nC 组：放宽 harness 门不得顺手放宽档位门")
        t_10 = make_trip(tmp, "t_10_20261023", windows=3, pre=8.023,
                         units0=881)
        rc10, o10 = run(JUDGE, t_10)
        rec("C1 pre_fps15=8.023 三窗齐全 ⇒ V11-a 不通过（EXIT=1）",
            rc10 == 1, "rc=%d" % rc10)
        rec("C2 判定文案给出 10 档", "10" in o10.split("档位判定")[-1][:20]
            if "档位判定" in o10 else False, "")

        # ---- D 组：变异击杀（每条都必须让退出码变）----
        print("\nD 组：变异击杀 —— 改坏被测分支，退出码必须变")
        muts = [
            ("M1 删短路分流（if w0_v in SHORT_CIRCUIT_VERDICTS → if False）",
             "if w0_v in SHORT_CIRCUIT_VERDICTS:",
             "if False:",
             t_short, 3),
            ("M2 产物丢失沿用不可判定（EXIT_ARTIFACT_LOST → EXIT_UNDECIDABLE）",
             "return EXIT_ARTIFACT_LOST",
             "return EXIT_UNDECIDABLE",
             t_lost, 4),
            ("M3 把『w0=ok 缺窗』重新混成短路（EXIT_UNDECIDABLE → EXIT_SHORT_CIRCUIT）",
             '        print("\\n!! w0 正常完成但 w1/w2 缺失 ⇒ 产物异常（非设计内短路）")\n'
             "        return EXIT_UNDECIDABLE",
             '        print("\\n!! w0 正常完成但 w1/w2 缺失 ⇒ 产物异常（非设计内短路）")\n'
             "        return EXIT_SHORT_CIRCUIT",
             t_anom, 2),
            ("M4 已知清单删掉 harness7",
             '    "d019e8beecfb5fd8": "harness7（D-05 补丁副本，472,020 B）",\n',
             "",
             t_h7, 0),
            # ★ M5 原设计（把 no_advance 塞进 WINDOW_OK_VERDICTS）是**死分支**：
            #   短路判定在它之前先 return，变异永不生效 ⇒ 恒真。这正是本项目
            #   反复踩的「变异落在不可达路径」。改为直接删短路集里的 no_advance。
            ("M5 短路集删掉 no_advance（该死法不再被认出）",
             'SHORT_CIRCUIT_VERDICTS = ("no_advance", "tier_invalid", "late_start", "error")',
             'SHORT_CIRCUIT_VERDICTS = ("tier_invalid", "late_start", "error")',
             t_short, 3),
            # ★ M6 只能按**文案**判：两条 units0 分支都 `return EXIT_SHORT_CIRCUIT`，
            #   退出码天然相同 —— 若按 rc 判就是恒真式（本轮 M5 初版同款坑）。
            #   ★ 这也说明「A6/A7 是文案级断言」：它们的价值只在人读的输出里，
            #   门禁必须明说这一点，不能假装退出码覆盖了它。
            ("M6 units0 分档文案反转（有值 ↔ None 互换）[按文案判]",
             '        if w0_v == "no_advance" and w0_g.get("units0") is not None:',
             '        if w0_v == "no_advance" and w0_g.get("units0") is None:',
             t_short, "text"),
            # ★ M7：把 [4] 段改回「按字典键找」—— 即修复前的写法。
            #   若这一条杀不掉，说明合成趟没有覆盖到格式差异（假门禁）。
            ("M7 [4] 段退回按字典键找 NAV/S4（修复前写法）",
             '        nav_v = rec_get(recs, "NAV", "verdict")',
             '        nav_v = find(f, "verdict")[0]',
             t_h6, 0),
        ]
        for label, anchor, repl, trip, want in muts:
            msrc = mutate(src, anchor, repl, label)
            mp = tmp / ("_mut_%s.py" % label.split()[0])
            mp.write_text(msrc, encoding="utf-8")
            got, out_m = run(mp, trip)
            got0, out_0 = run(JUDGE, trip)
            if want == "text":
                # ★ 只判文案的变异：退出码不变是**预期内的**（两条分支同一 rc），
                #   故必须以输出文本为判据，并显式登记「此项退出码不覆盖」。
                changed = out_m != out_0
                rec(label, changed,
                    "文案%s（rc 均为 %d —— 此项退出码不覆盖）"
                    % ("已变" if changed else "★ 未变=恒真", got0))
            else:
                rec(label, got != got0,
                    "原 rc=%d → 变异 rc=%d（%s）"
                    % (got0, got, "已变" if got != got0 else "★ 未变=恒真"))

        # ---- E 组：真机产物回归（10-23 四趟 + 10-21 四趟，只读）----
        print("\nE 组：真实趟产物回归（只读，不改产物）")
        if TRIP_ROOT.is_dir():
            real = [("l1_20261023", 3), ("l1_20261023b", 3),
                    ("l3_20261023", 3),
                    ("l1c_20261021", 1), ("l1d_20261021", 1),
                    ("l1e_20261021", 1), ("l3_20261021", 1)]
            for name, want in real:
                d = TRIP_ROOT / name
                if not d.is_dir():
                    rec("E %s 存在" % name, False, "目录缺失")
                    continue
                got, out = run(JUDGE, d)
                rec("E %s ⇒ EXIT=%d" % (name, want), got == want,
                    "rc=%d" % got)
            # l1_20261023 这三趟的核心：必须是「短路」而不是「无法判定」
            got, out = run(JUDGE, TRIP_ROOT / "l1_20261023")
            rec("E10-23a 判为设计内短路且点名 no_advance",
                got == 3 and "no_advance" in out, "rc=%d" % got)
            got, out = run(JUDGE, TRIP_ROOT / "l1_20261023b")
            rec("E10-23b 指出 units0 有值 ⇒ 帧冻结而非进程死",
                "帧冻结" in out or "测不到" in out, "")
            got, out = run(JUDGE, TRIP_ROOT / "l3_20261023")
            rec("E10-23 L3 也能被判（不再一律『三窗不全』）",
                got == 3 and "三窗不全" not in out, "rc=%d" % got)
        else:
            rec("E 真实趟根目录存在", False, str(TRIP_ROOT))

        # ---- F 组：qc151_fields 记录列表格式（修复前从未被执行过的两条）----
        print("\nF 组：qc151_fields 是记录列表 —— 按 (group,key) 取值")
        rc6b, o6b = run(JUDGE, t_h6)
        rec("F1 记录列表形态下 NAV.verdict 能读到 OK",
            "NAV.verdict = OK" in o6b, "")
        rec("F2 记录列表形态下 S4.hit_count 能读到 0",
            "S4.hit_count = 0" in o6b, "")
        rec("F3 4 段两条断言均 PASS（不是『含 NAV』式永远红）",
            rc6b == 0, "rc=%d" % rc6b)
        t_badnav = make_trip(tmp, "t_badnav_20261023", windows=3, hit=3)
        # nav=... 保留 OK，只把 hit_count 改坏 ⇒ 必须红
        rcb, ob = run(JUDGE, t_badnav)
        rec("F4 S4.hit_count=3 ⇒ FAIL（取值而非存在性）", rcb == 1, "rc=%d" % rcb)

        # ---- 汇总 ----
        print("\n" + "=" * 78)
        npass = sum(1 for _n, ok in RESULTS if ok)
        ntot = len(RESULTS)
        print("TOTAL %d/%d PASS" % (npass, ntot))
        for n, ok in RESULTS:
            if not ok:
                print("  FAIL: %s" % n)
        print("=" * 78)
        return 0 if npass == ntot else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

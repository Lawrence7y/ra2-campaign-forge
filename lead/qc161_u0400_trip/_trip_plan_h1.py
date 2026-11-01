#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-1 真机三趟**编排器**：只产出命令，绝不启动任何进程。

为什么需要这个件：S399 §九 把三趟写成了**散文**（「不传 --fullscreen」
「加 --h7-keep-rect-wait」），而 `_launch_l1_20261023.py` **没有 dry-run**——
它一路走到 `os.spawnv`。于是真机时段里必须**手敲参数**：
  ① 三趟参数各不相同（全屏开关、harness 哈希、附加参数），
  ② 每趟跑掉 2–3 分钟，敲错一次就废一趟，
  ③ 敲错**不会报错**——参数都是合法的，只是跑成了别的那趟。

★ 本件的关键设计：**不自己拼 argv**，而是 import 发射器的
  `build_harness_argv()` 纯函数来生成。这样「编排器打印的命令」
  与「发射器实际发射的命令」在**构造上**必然一致；
  若各写一份，两份会漂移，而漂移在真机时段才暴露。

★ 本件**不调用 spawnv、不建目录、不写盘**（除 stdout）。

复跑：python lead/qc161_u0400_trip/_trip_plan_h1.py
      python lead/qc161_u0400_trip/_trip_plan_h1.py --json
退出码：0 = 三趟命令齐备且自检通过；1 = 自检发现不一致。
"""
from __future__ import annotations

import argparse
import ast as _ast
import importlib.util
import json
import os
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "lead" / "qc161_u0400_trip" / "_launch_l1_20261023.py"

H6 = "ff8245d27b3db22a"
H7 = "d019e8beecfb5fd8"

# ★ 三趟定义，逐条对齐 S399 §九 第 1/2/3 条。
#   `suffix` 必须互不相同：发射器用它派生 out-dir 与 trip-id，
#   重名会让第二趟覆盖第一趟的证据目录。
TRIPS = [
    {
        "no": 1,
        "name": "窗口模式",
        "suffix": "ha",
        "harness": H7,
        "no_fullscreen": True,
        "extra_argv": "",
        "design": "不传 --fullscreen；确认 h7_fs_rect_wait_skipped 不出现、"
                  "polls 与 harness6 同量级（历史窗口趟实测 0）",
    },
    {
        "no": 2,
        "name": "全屏短路",
        "suffix": "hb",
        "harness": H7,
        "no_fullscreen": False,
        "extra_argv": "",
        "design": "缺省短路；确认 skipped=true、polls=0、frame 段 <2s，"
                  "并读 nav_to_measure_s（边界 2 的唯一实测数）",
    },
    {
        "no": 3,
        "name": "对照臂",
        "suffix": "hc",
        "harness": H7,
        "no_fullscreen": False,
        "extra_argv": "--h7-keep-rect-wait",
        "design": "显式保持矩形死等；确认 polls 回到 244–253、frame 段 ~125s、"
                  "且 late_start 不出现",
    },
]

RESULTS: list[tuple[str, bool, str]] = []
_QUIET = [False]      # ★ --json 时自检文本改走 stderr，保证 stdout 只有 JSON


def rec(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    line = "  %s %s%s" % ("✓" if ok else "✗", name,
                          ("  | %s" % detail) if detail else "")
    if _QUIET[0]:
        print(line, file=sys.stderr)
    else:
        print(line)


def load_launcher():
    """只加载模块取纯函数；**不执行** main()。"""
    spec = importlib.util.spec_from_file_location("_launcher_l1", LAUNCHER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build(mod, trip: dict, variant: str) -> list[str]:
    v = mod.VARIANTS[variant]
    src = mod.TRIP / v["src"]
    map_path = src / "XMP29U2.MAP"
    out_dir = mod.TRIP / ("l%s_20261023%s"
                          % (variant[1:].lower(), trip["suffix"]))
    trip_id = v["trip_prefix"] + "-20261023" + trip["suffix"].upper()
    mv = json.loads((mod.TRIP / (v["src"] + "_MANIFEST.json")).read_text(
        encoding="utf-8"))
    names = sorted(mv["files"].keys())
    extra = [n for n in names if n not in mod.DEFAULT_CARRIER_FILES]
    return mod.build_harness_argv(
        harness=mod.HARNESS_BY_SHA16[trip["harness"]],
        map_path=map_path, map_sha=v["map_sha"], out_dir=out_dir,
        src=src, extra=extra, trip_id=trip_id,
        probe_frames=mod.PROBE_FRAMES,
        fullscreen=not trip["no_fullscreen"],
        extra_argv=[x for x in trip["extra_argv"].split() if x])


def quote(a: str) -> str:
    """★ §417：打印给人复制粘贴的命令，**一律加双引号**。

    原实现 `'"%s"' % a if (" " in a or "\t" in a) else a` 只在含空白时加引号，
    而本项目的 argv 里全是 **Windows 反斜杠路径**（无空格）⇒ 全部裸奔。
    实测 Git Bash 对未加引号的 `D:\\Project\\...` 做反斜杠转义
    ⇒ 实得 `D:Projectra2-campaign...`（`_probe_bs.sh` 与 `_probe_shlex.py` 双证）。
    加引号后 `shlex.split(posix=True)` 逐字还原（match=True）。

    ★ 内部双引号需转义，否则会被 shell 当成引号结束。
    """
    return '"%s"' % a.replace('"', '\\"')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="L1", choices=["L1", "L3"])
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    a = ap.parse_args()

    if not LAUNCHER.is_file():
        print("★ 发射器缺失：%s" % LAUNCHER)
        return 1
    mod = load_launcher()

    plans = []
    for t in TRIPS:
        argv = build(mod, t, a.variant)
        plans.append({**t, "argv": argv, "cmd": "python " + " ".join(
            quote(x) for x in argv)})

    if a.json:
        _QUIET[0] = True
        print(json.dumps(plans, ensure_ascii=False, indent=2))
    else:
        print("=" * 84)
        print("H-1 真机三趟编排（S399 §九）  变体=%s" % a.variant)
        print("★ 本件只打印命令，不启动任何进程、不建目录。")
        print("=" * 84)
        for p in plans:
            print("\n[第 %d 趟 %s]  suffix=%s" % (p["no"], p["name"],
                                                 p["suffix"]))
            print("  设计判据：%s" % p["design"])
            print("  命令：")
            print("    %s" % p["cmd"])

    # ---------------- 自检 ----------------
    # ★ --json 时自检也不得混进 stdout（否则 `json.load(stdout)` 报 Extra data）
    _hdr = sys.stderr if _QUIET[0] else sys.stdout
    print("\n" + "=" * 84, file=_hdr)
    print("[自检]", file=_hdr)

    # C1 三趟 suffix 互不相同（否则 out-dir/trip-id 撞车覆盖证据）
    sufs = [p["suffix"] for p in plans]
    rec("C1 三趟 suffix 互不相同", len(set(sufs)) == len(sufs), str(sufs))

    # C2 三趟 out-dir 互不相同
    ods = []
    for p, t in zip(plans, TRIPS):
        ods.append(str(mod.TRIP / ("l%s_20261023%s"
                                   % (a.variant[1:].lower(), t["suffix"]))))
    rec("C2 三趟 out-dir 互不相同", len(set(ods)) == len(ods))

    # C3 第 1 趟**不含** --fullscreen；第 2/3 趟**必须含**
    for p in plans:
        has_fs = "--fullscreen" in p["argv"]
        if p["no"] == 1:
            rec("C3a 第 1 趟不含 --fullscreen（窗口模式）", not has_fs)
        else:
            rec("C3b 第 %d 趟含 --fullscreen" % p["no"], has_fs)

    # C4 只有第 3 趟带 --h7-keep-rect-wait，且恰好一次
    for p in plans:
        n = p["argv"].count("--h7-keep-rect-wait")
        if p["no"] == 3:
            rec("C4a 第 3 趟恰含一次 --h7-keep-rect-wait", n == 1, "n=%d" % n)
        else:
            rec("C4b 第 %d 趟不带 --h7-keep-rect-wait" % p["no"], n == 0,
                "n=%d" % n)

    # C5 三趟都跑 harness7
    for p in plans:
        rec("C5 第 %d 趟 harness == harness7" % p["no"],
            p["harness"] == H7, p["harness"])

    # C6 --trip-id 与 suffix 一一对应（防串趟）
    for p in plans:
        want = ("QC161-U0800-%s-20261023%s"
                % (a.variant, p["suffix"].upper()))
        got = p["argv"][p["argv"].index("--trip-id") + 1]
        rec("C6 第 %d 趟 trip-id 与 suffix 对应" % p["no"], got == want,
            "%s vs %s" % (got, want))

    # C7 ★ 反向一致性：本件命令必须**逐字**等于发射器在同等参数下的 argv。
    #    这一条才是本件存在的理由（防两处各写一份导致漂移）。
    ok_all = True
    for p in plans:
        again = build(mod, {k: p[k] for k in
                            ("harness", "no_fullscreen", "extra_argv")}
                      | {"suffix": p["suffix"]}, a.variant)
        same = again == p["argv"]
        ok_all &= same
    rec("C7 重建 argv 与发射器纯函数逐字一致（无漂移）", ok_all)

    # C8 载体附加件数 = 83（冻结清单 88 − 默认 5）
    n = len([x for x in plans[0]["argv"] if x])
    idx = plans[0]["argv"].index("--carrier-create-files")
    cnt = len(plans[0]["argv"][idx + 1].split(","))
    rec("C8 --carrier-create-files 恰 83 件（88 − 默认 5）", cnt == 83,
        "实得 %d" % cnt)

    # C11 ★★ 打印出来的命令必须能被 POSIX shell **逐字还原**成 argv。
    #   ★ 这条是 §417 的回归门禁，抓的缺陷是：`quote()` 只在含空白时加引号，
    #     而本项目 argv 全是 Windows 反斜杠路径（无空格）⇒ 全部裸奔
    #     ⇒ Git Bash 把 `D:\Project\x` 吃成 `D:Projectx`，三条趟全跑不起来。
    #   ★ 判据必须是「分词后与原 argv 逐字相等」，不能是「命令里有没有引号」：
    #     后者写成 `'"' in cmd` 对「只有一部分参数加引号」不敏感（方向不对）。
    #   ★ 用 shlex（POSIX 模式）当尺子：它就是 shell 分词的真实现。
    bad_rt = []
    for p in plans:
        toks = shlex.split(p["cmd"], posix=True)
        # cmd 形如 `python <argv0> <argv1> ...` ⇒ 去掉开头的解释器名
        got = toks[1:]
        if got != p["argv"]:
            diff = [(i, p["argv"][i], got[i] if i < len(got) else None)
                    for i in range(min(len(p["argv"]), len(got)))
                    if p["argv"][i] != got[i]]
            bad_rt.append((p["suffix"], diff[:2]))
    rec("C11 打印命令经 shlex 分词后逐字还原 argv（防反斜杠被吃）",
        not bad_rt, "" if not bad_rt else "%d 趟还原失败 %s"
        % (len(bad_rt), bad_rt[0]))

    # C11b ★ 阳性对照：把 quote() 临时换成**旧实现**，上面那条必须变红。
    #   ★ 没有这一条，C11 可能只是「恰好都对」而不是「抓得住旧缺陷」。
    old_cmd = "python " + " ".join(plans[0]["argv"])
    old_toks = shlex.split(old_cmd, posix=True)[1:]
    rec("C11b 阳性对照：旧式无引号命令分词后**必须**失真（证明 C11 承重）",
        old_toks != plans[0]["argv"],
        "旧式 argv[0]=%r（应为 %r）"
        % (old_toks[0] if old_toks else None, plans[0]["argv"][0]))

    # C12 ★★ §423 真机教训：三趟的**载体目录**必须过发射器 `:250` 的占位符口径。
    #   发射器门禁量的是 out_dir\ct\c_000000000000_12345 的**全长**（≤130），
    #   不是 out_dir\ct——两者差 21 字符。真机首发射 h7a 就是被这条 BLOCK(131)。
    #   判据逐字复用发射器公式（消费方口径），公式若漂移本条即失效自证。
    GATE_ANCHOR = "c_" + "0" * 12 + "_12345"      # 与发射器 :250 占位符逐字一致
    c12_bad = []
    for p in plans:
        outdir = p["argv"][p["argv"].index("--out-dir") + 1]
        glen = len(str(Path(outdir) / "ct" / GATE_ANCHOR))
        if glen > 130:
            c12_bad.append("%s=%d" % (p["suffix"], glen))
    rec("C12 三趟载体目录过发射器 :250 占位符口径（≤130）", not c12_bad,
        "红项=%s" % c12_bad if c12_bad else
        "len=%d" % len(str(Path(plans[0]["argv"][
            plans[0]["argv"].index("--out-dir") + 1]) / "ct" / GATE_ANCHOR)))

    # C12b ★ 阳性对照：同公式下若 suffix 回到真机被 BLOCK 的 "h7a"，必须 >130。
    #   ★ 没有这条，C12 可能只是「我的公式恰好都算小」而非「真能拦越界」。
    old_out = str(Path(plans[0]["argv"][
        plans[0]["argv"].index("--out-dir") + 1]).with_name(
        Path(plans[0]["argv"][plans[0]["argv"].index("--out-dir") + 1]).name
        .replace("l1_20261023ha", "l1_20261023h7a")))
    old_len = len(str(Path(old_out) / "ct" / GATE_ANCHOR))
    rec("C12b 阳性对照：旧 h7a 后缀同公式必须 >130（真机实证 BLOCK）",
        old_len > 130, "h7a 口径=%d（真机 131>130）" % old_len)

    # C9 本件**不启动被测对象**（战局 / harness / 游戏）
    #   ★ 不能把禁用词写成字面量列表再 `in me`：词就写在文件里 ⇒ 恒真自指。
    #     改为运行时拼接禁用名 + 扫本件 AST 的**调用节点**（不认字符串/注释）。
    #   ★★ 语义收窄（C10 引入后）：本件要「启动自己」验证 --json 隔离，
    #      那是**自检装置**不是发射。故本项判「有没有把 harness/游戏启动起来」，
    #      而不是「有没有任何子进程」——后者会把 C10 的自检误判成违规。
    banned_args = ["--target-map", "--carrier-create-from", "--measure"]
    tree_me = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    launches_harness = False
    for _n in _ast.walk(tree_me):
        if isinstance(_n, _ast.Call):
            _f = _n.func
            _nm = _f.id if isinstance(_f, _ast.Name) else (
                _f.attr if isinstance(_f, _ast.Attribute) else "")
            if _nm in ("spawnv", "spawnve", "spawnl", "system", "Popen"):
                launches_harness = True
            # 任何调用里出现「发射 harness 专用参数」⇒ 视为在启动被测对象
            for _a in _n.args:
                if isinstance(_a, _ast.Constant) and isinstance(_a.value, str):
                    if any(b in _a.value for b in banned_args):
                        launches_harness = True
    rec("C9 本件不启动被测对象（无 spawn/Popen/system、无 harness 专用参数）",
        not launches_harness, "命中" if launches_harness else "")

    # C9b ★ 阳性对照：同一套判据扫**真发射器**必须判为「启动被测对象」。
    #   否则 C9 在收窄语义后可能变成「谁都判不出来」的空断言（假绿）。
    def _launches(text: str) -> bool:
        _t = _ast.parse(text)
        for _n in _ast.walk(_t):
            if isinstance(_n, _ast.Call):
                _f = _n.func
                _nm = _f.id if isinstance(_f, _ast.Name) else (
                    _f.attr if isinstance(_f, _ast.Attribute) else "")
                if _nm in ("spawnv", "spawnve", "spawnl", "system", "Popen"):
                    return True
                for _a in _n.args:
                    if (isinstance(_a, _ast.Constant)
                            and isinstance(_a.value, str)
                            and any(b in _a.value for b in banned_args)):
                        return True
        return False

    launcher_src = LAUNCHER.read_text(encoding="utf-8")
    rec("C9b 阳性对照：判据扫真发射器须判为「启动被测对象」",
        _launches(launcher_src), "发射器确实含 spawnv")

    # C10 ★ `--json` 的 stdout 必须是**纯 JSON**（可被 json.load 直接解析）。
    #   本轮实测踩到：自检文本混进 stdout ⇒ `json.load` 报 Extra data。
    #   ⇒ 把「两种输出模式互不污染」定成常驻判据，否则该缺陷会复发。
    #   ★★ 必须带哨兵：本判据要**启动自己**，而子进程会再跑一次 C10
    #      ⇒ 无界自递归（本轮实测：一条命令无限生孩子，只得手动 kill）。
    #      用环境变量标记子进程「已在验证中」，子进程跳过本项。
    import subprocess as _sp
    _sentinel = "TRIP_PLAN_JSON_PROBE"
    if os.environ.get(_sentinel):
        rec("C10 --json stdout 纯 JSON（子进程侧，跳过）", True, "sentinel")
    else:
        env = dict(os.environ)
        env[_sentinel] = "1"
        p = _sp.run([sys.executable, str(Path(__file__)), "--json",
                     "--variant", a.variant],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=180, env=env)
        try:
            doc = json.loads(p.stdout)
            ok_json = isinstance(doc, list) and len(doc) == 3
            det = "parsed list len=%d" % (
                len(doc) if isinstance(doc, list) else -1)
        except Exception as exc:                    # noqa: BLE001
            ok_json, det = False, "stdout 非纯 JSON：%r" % (exc,)
        rec("C10 --json 模式下 stdout 是纯 JSON（3 趟可解析）", ok_json, det)

    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("\nTOTAL %d/%d PASS" % (npass, len(RESULTS)), file=_hdr)
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
# _f3_compare.py — 原门禁 vs 增强版逐样本对比 + H 系列逐行等价核验（非退化证明）。
# 用法：python -I -X utf8 _f3_compare.py <orig_transcript> <enh_transcript> <orig_summary> <enh_summary> <out_txt>
import json
import re
import sys


def parse_transcript(path):
    """返回 {name: {"exit": n, "checks": [(checkname, ok), ...]}}"""
    out = {}
    cur = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r"===SAMPLE (.+) exit=(-?\d+)===$", line)
            if m:
                cur = m.group(1)
                out[cur] = {"exit": int(m.group(2)), "checks": []}
                continue
            if cur is None:
                continue
            m = re.match(r"^  \[(PASS|FAIL)\] (\S.*?)\s*(—\s*.*)?$", line)
            if m:
                out[cur]["checks"].append((m.group(2).strip(), m.group(1) == "PASS"))
    return out


def main(argv):
    orig = parse_transcript(argv[1])
    enh = parse_transcript(argv[2])
    with open(argv[3], "r", encoding="utf-8") as f:
        osum = json.load(f)
    with open(argv[4], "r", encoding="utf-8") as f:
        esum = json.load(f)
    lines = []

    # 1) exit 汇总与 transcript 一致性
    for tag, summ, tr in (("orig", osum, orig), ("enh", esum, enh)):
        for k, v in summ.items():
            assert tr[k]["exit"] == v, "transcript/summary mismatch %s %s" % (tag, k)
    lines.append("transcript/summary 一致性：orig 37 项、enh 37 项全部对上")

    # 2) H 系列逐行等价核验（原15项判定必须零漂移）
    drift = []
    for name in sorted(orig):
        if name not in enh:
            continue
        oh = {n: ok for n, ok in orig[name]["checks"] if n.startswith("H")}
        eh = {n: ok for n, ok in enh[name]["checks"] if n.startswith("H")}
        if oh.keys() != eh.keys():
            drift.append("%s: H检查名集合不同 orig=%s enh=%s" % (name, sorted(oh), sorted(eh)))
            continue
        for n in oh:
            if oh[n] != eh[n]:
                drift.append("%s: %s orig=%s enh=%s" % (name, n, oh[n], eh[n]))
    lines.append("")
    lines.append("== H系列（原15项）逐行等价核验 ==")
    lines.append("漂移数=%d %s" % (len(drift), "（零漂移：原15项判定与原门禁逐一相同）" if not drift else ""))
    lines.extend("  " + d for d in drift)

    # 3) 逐样本表
    lines.append("")
    lines.append("== 36 攻样本逐样本对比（exit: 1=拦住 0=放行）==")
    lines.append("%-34s %-6s %-6s %-6s %s" % ("样本", "原门禁", "增强版", "变化", "增强版拦截主因(N系列FAIL)"))
    n_improved = 0
    n_regress = 0
    rows = []
    for name in sorted(orig):
        if name == "_c7_record_template.json":
            continue
        oe, ee = orig[name]["exit"], enh[name]["exit"]
        if oe == 1 and ee == 1:
            change = "保持拦"
        elif oe == 0 and ee == 0:
            change = "保持放"
        elif oe == 0 and ee == 1:
            change = "转拦↑"
            n_improved += 1
        else:
            change = "误放↓"
            n_regress += 1
        fails = [n for n, ok in enh[name]["checks"] if not ok and n.startswith("N")]
        reason = "; ".join(f.split(" ", 1)[0] for f in fails) if fails else "-"
        rows.append((name, oe, ee, change, reason, fails))
        lines.append("%-34s %-6d %-6d %-6s %s" % (name, oe, ee, change, reason))
    lines.append("")
    lines.append("== 模板基线 ==")
    lines.append("_c7_record_template.json: orig=%d enh=%d" % (
        orig["_c7_record_template.json"]["exit"], enh["_c7_record_template.json"]["exit"]))

    # 4) 统计
    orig_caught = [n for n, _, _, c, _, _ in rows if _ in ()]  # placeholder, computed below
    o_caught = sum(1 for r in rows if r[1] == 1)
    o_rel = sum(1 for r in rows if r[1] == 0)
    e_caught = sum(1 for r in rows if r[2] == 1)
    e_rel = sum(1 for r in rows if r[2] == 0)
    lines.append("")
    lines.append("== 统计 ==")
    lines.append("原门禁：拦 %d / 放 %d（36 样本）" % (o_caught, o_rel))
    lines.append("增强版：拦 %d / 放 %d（36 样本）" % (e_caught, e_rel))
    lines.append("转拦（原放→增强拦）：%d 个" % n_improved)
    lines.append("退化（原拦→增强放）：%d 个" % n_regress)
    lines.append("增强版仍放行：%s" % ", ".join(r[0] for r in rows if r[2] == 0))
    lines.append("")
    lines.append("== 转拦样本的完整 N 系列 FAIL 明细 ==")
    for name, oe, ee, change, reason, fails in rows:
        if change == "转拦↑":
            lines.append("--- %s（orig=%d enh=%d）" % (name, oe, ee))
            for fl in enh[name]["checks"]:
                if not fl[1] and fl[0].startswith("N"):
                    lines.append("    [FAIL] %s" % fl[0])
    with open(argv[5], "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:60]))
    print("... -> wrote", argv[5])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

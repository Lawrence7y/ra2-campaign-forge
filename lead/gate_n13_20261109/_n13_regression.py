# -*- coding: utf-8 -*-
r"""_n13_regression.py — N13/R13 谓词正负样本回归 + 真件回归 + 旧门禁四条问题重判

实跑命令（全部 python -I -X utf8 + 绝对路径）：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_regression.py

零真机、零采样；只做静态文本判定与 hashlib 指纹。
"""

import importlib.util
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
PUB = ROOT / "lead" / "ledger_bound_20261109" / "LEDGER_BOUND_VOLUME.md"
DRAFT = ROOT / "lead" / "ledger_bound_20261109" / "_lb_BOUND_VOLUME.md"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


n13 = _load(N13, "_n13_reg")
g7 = _load(G7, "_g7_reg")
TOKENS = list(n13.DEFAULT_TOKENS)


def judge(text):
    """返回 (是否应当FAIL, 明细)：把 R13 的 D 类当 FAIL，A/B/C 当放过。"""
    probs, det = n13.r13_assertions(text, TOKENS,
                                    r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    return (len(probs) > 0), det, probs


# ---------------------------------------------------------------------------
# (a) 正样本 ≥12：应当放过（A/B/C 三类）
# ---------------------------------------------------------------------------
POSITIVES = [
    # id, 文本, 期望类, 来源/构造说明
    ("P01", "### 1(c) 有没有已入账的？", "A/B",
     "真件 _lb_BOUND_VOLUME.md:28 逐字（问句 + # 标题）"),
    ("P02", "一、一页纸总览  1(a) 笔数=5 / 1(b) 每笔编号·出处·字节 / 1(c) 已入账 grep=0 / 依赖速览", "A/B",
     "真件 _lb_BOUND_VOLUME.md:275 逐字（总览枚举 + grep=0 检索结果）"),
    ("P03", "## 2 · 上游指纹（十一件）+ 待入账清点（每笔编号标题出处字节）+ 已入账 grep 结果", "B",
     "真件 LEDGER_BOUND_VOLUME.md:54 逐字（## 小节标题含 grep 结果）"),
    ("P04", "### 2.2 待入账清点 + 已入账 grep 结果", "B",
     "真件 LEDGER_BOUND_VOLUME.md:77 逐字（### 小节标题）"),
    ("P05", "**已入账核查实跑命令**：", "A",
     "真件 LEDGER_BOUND_VOLUME.md:79 逐字（核查动作冒号标签）"),
    ("P06", "| 笔 | 暂编 | 标题 | 正文出处（单件草案件:行） | 草案件字节 | 已入账? |\n|:--:|:--:|:--|:--|--:|:--|", "B",
     "真件 LEDGER_BOUND_VOLUME.md:87-88 逐字（表格表头列名 + 分隔行）"),
    ("P07", "本交付件按任务要求改为「## 1」到「## 5」五节：§1 总览 / §2 上游指纹 + 待入账清点 + 已入账 grep / §3 冲突与依赖 / §4 编号检查 + 结构 + 文件清单", "B",
     "真件 LEDGER_BOUND_VOLUME.md:338 截取（目录/结构枚举，§ 清单）"),
    ("P08", "- **附两条引用限定**（笔 4 正文自带：YI §1 引文在裁决书中 grep 0 逐字命中，逐字出处「未验」；`RULING_DIRECTION.md` 整体 unconfirmed，本节登记不宣告 N-4 正式绑定已生效）。", "C",
     "真件 LEDGER_BOUND_VOLUME.md:209 逐字（不宣告…已生效 否定式）"),
    ("P09", "② RULING_DIRECTION.md 整体状态 **unconfirmed**（:5/:77）——**本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效**（与补登件自述一致）。", "C",
     "真件 LEDGER_BOUND_VOLUME.md:242 尾段截取（否定式）"),
    ("P10", "- **引用限定（本会话如实登记两点，引用本节者须连带）**：① YI §1 引文在裁决书中 grep = **0 逐字命中**——**本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效**。", "C",
     "真件 _lb_BOUND_VOLUME.md:174 结构同款（否定式 + grep 检索）"),
    ("P11", "  - 有没有已追加的？grep 台账确认 = 0 命中。", "A",
     "构造：行首缩进 + 列表符号，A 问句与检索结果同子句"),
    ("P12", "| 草案件 | 已生效? | 备注 |\n|:--|:--|:--|\n| X | 否（grep 0 命中） | 待裁 |", "A/B",
     "构造：表头问询列名 + 表格竖线，数据行用「否（grep 0 命中）」"),
    ("P13", "**不得写成「本笔已生效」**；本件只登记。", "C",
     "构造：C 否定式（不得写成 + 引证跨度）"),
    ("P14", "  * 已入账 grep 结果：0 逐字命中", "A",
     "构造：行首缩进 + * 列表符 + grep 结果"),
    ("P15", "### 3 已追加 grep 结果（清单）", "B",
     "构造：### 小节标题 + 清单"),
    ("P16", "§2 上游指纹 + 已入账 grep 结果 / §3 冲突", "B",
     "构造：§ 结构枚举（目录行）"),
]

# ---------------------------------------------------------------------------
# (b) 负样本 ≥12：应当抓住（D 类）
# ---------------------------------------------------------------------------
NEGATIVES = [
    ("N01", "本笔已于 §605 入账。", "真断言：主语=本笔，谓语=已入账", "编排方给的真断言形"),
    ("N02", "已生效，可应用母本。", "真断言：完成词 + 可应用", "编排方给的真断言形"),
    ("N03", "本笔已于 §607 入账，第五节另计。", "被登记的那一笔 + § 定位", "构造"),
    ("N04", "本节已生效，可应用母本", "主语=本节 + 完成词", "构造"),
    ("N05", "该笔已追加至台账尾部。", "主语=该笔 + 已追加", "构造"),
    ("N06", "第 5 笔已入账。", "主语=第 N 笔 + 已入账", "构造"),
    ("N07", "不宣告 X 已生效，但 Y 已入账", "★ 同句混用：否定 + 肯定，必须判 D", "任务第二步(c) 点名"),
    ("N08", "不宣告 N-4 正式绑定已生效，但本笔已于 §605 入账", "★ 同句混用且含 § 定位断言", "构造"),
    ("N09", "  本笔已于 §608 入账", "行首缩进不影响判 D", "构造"),
    ("N10", "- 本件已生效，可应用母本", "列表符号不影响判 D", "构造"),
    ("N11", "* 第 3 笔已追加，无需另批", "列表符号 + 时间/情态副词修饰", "构造"),
    ("N12", "| 1 | §605 | 本笔已入账 | 是 |", "★ 表格单元格内断言（数据行，非表头）", "任务第三步(b) 点名"),
    ("N13", "| 2 | §606 | 该笔已生效，可应用母本 | 备注入账 |", "表格单元格内断言 + 可应用", "构造"),
    ("N14", "本笔现正式入账，无需另批", "时间副词（现/正式）修饰", "构造"),
    ("N15", "本件已于 §609 入账（2026-11-09 实跑）", "时间副词 + 括注", "构造"),
    ("N16", "母本已生效，可改", "被动/无主语句式的完成断言", "构造"),
    ("N17", "台账已追加第五节，照此执行", "主语=台账 + 已追加", "构造"),
    ("N18", "本笔已入账 0 命中不得写成未入账", "检索标记与真断言同句：mixed 作废豁免", "构造（反向对照）"),
    # ---- 第二轮：复核 verdict=partial 的 ④，5 条样本外真断言（曾 5/5 漏网） ----
    ("N19", "未验：本笔已入账", "★ 前置「未验」标签不得一键废掉行级肯定守卫", "复核 _n13v_final_probe.py V1"),
    ("N20", "grep 结果：第 5 笔已入账", "★ A 检索标记 + 带空格主语，微段内主语守卫", "复核 _n13v_final_probe.py V2"),
    ("N21", "§2 清单 / 此笔已入账 / §3 依赖", "★ B 目录枚举行内的主语断言，斜杠隔断微段", "复核 _n13v_final_probe.py V3"),
    ("N22", "未验：§605 已入账", "★ 前置标签 + 节号主语", "复核 _n13v_final_probe.py V4"),
    ("N23", "grep 结果：此笔已入账", "★ A 标记 + 非词表主语「此笔」", "复核 _n13v_final_probe.py V5"),
    ("N24", "grep 结果：已入账", "裸完成词在 A 标记后的微段内，拿不准默认 FAIL", "复核 X1"),
    ("N25", "未验：第 605 节已入账", "前置标签 + 节号变体", "复核 X2"),
    ("N26", "已入账核查清单：该条已追加", "A 核查标签 + 另一微段的「该条已追加」", "复核 X3"),
]


def run_samples():
    print("=" * 78)
    print("§1 正样本回归（应当放过：R13 不得报 D 类 problem）")
    print("=" * 78)
    p_ok = p_fail = 0
    for sid, text, expect, note in POSITIVES:
        failed, det, probs = judge(text)
        kinds = sorted({d["kind"] for d in det})
        status = "PASS(放过)" if not failed else "FAIL(误拦)"
        if not failed:
            p_ok += 1
        else:
            p_fail += 1
        print("%s %-4s expect=%-3s kinds=%-8s %s" % (status, sid, expect, ",".join(kinds), note[:60]))
        if failed:
            print("      problems:", probs)
        for d in det:
            print("      ", d["kind"], d["rule"], "|", d["quote"][:90])
    print("正样本小计：放过 %d / 误拦 %d / 合计 %d" % (p_ok, p_fail, len(POSITIVES)))

    print()
    print("=" * 78)
    print("§2 负样本回归（应当抓住：R13 必须报 D 类 problem）")
    print("=" * 78)
    n_ok = n_fail = 0
    for sid, text, expect, note in NEGATIVES:
        failed, det, probs = judge(text)
        kinds = sorted({d["kind"] for d in det})
        status = "PASS(抓住)" if failed else "FAIL(漏网)"
        if failed:
            n_ok += 1
        else:
            n_fail += 1
        print("%s %-4s expect=%s kinds=%-8s %s" % (status, sid, "D", ",".join(kinds), note[:60]))
        if not failed:
            print("      !!! 漏网明细:", [(d["kind"], d["rule"]) for d in det])
        for d in det:
            print("      ", d["kind"], d["rule"], "|", d["quote"][:90])
    print("负样本小计：抓住 %d / 漏网 %d / 合计 %d" % (n_ok, n_fail, len(NEGATIVES)))
    return p_ok, p_fail, n_ok, n_fail


def run_real_files():
    print()
    print("=" * 78)
    print("§3 真件回归：两件合订本应当 0 命中 D 类")
    print("=" * 78)
    out = {}
    for rel, p in [("LEDGER_BOUND_VOLUME.md", PUB), ("_lb_BOUND_VOLUME.md", DRAFT)]:
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        failed, det, probs = judge(text)
        kinds = {}
        for d in det:
            kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
        out[rel] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                    "kinds": kinds, "d_count": kinds.get("D", 0),
                    "problems": probs, "passed": (kinds.get("D", 0) == 0)}
        print("%s bytes=%d sha256=%s kinds=%s D=%d verdict=%s" %
              (rel, len(raw), out[rel]["sha256"][:16], kinds, out[rel]["d_count"],
               "PASS(0 D)" if out[rel]["passed"] else "FAIL(有 D)"))
        for d in det:
            print("   L%-4d %-3s %-4s %s | %s" %
                  (d["line"], d["token"], d["kind"], d["rule"][:44], d["quote"][:70]))
        if probs:
            print("   problems:", probs)
    return out


def run_old_gate_rejudge():
    print()
    print("=" * 78)
    print("§4 旧门禁四条问题逐条重判")
    print("=" * 78)
    # 复跑朴素字面门禁（与 dwfrun-614dbceb GATE_CODE 同词表/同判定）
    text = PUB.read_text(encoding="utf-8")
    naive = ["含越权断言 " + b for b in TOKENS if b in text]
    print("朴素字面门禁现盘实跑 problems =", json.dumps(naive, ensure_ascii=False))
    print("编排方背景称「四条问题里两条是 含越权断言 已入账 / 已生效」；"
          "本会话复跑该门禁只复现 2 条，另 2 条在现盘不可复现（未验）。")
    print("DB 实读（.zcode/cli/db/db.sqlite part rowid=613246，只读）亦记录交付轮"
          "结论为「门禁问题：含越权断言 已入账；含越权断言 已生效」两条。")
    print()
    print("逐条重判（条目 = 现盘可复现的 2 条 + 编排方背景所指的另 2 条，后者标未验）：")
    rows = [
        ("① 含越权断言 已入账", "可复现", "A/B 类：:54/:77/:79/:87/:338 = 检索动作+小节标题+表头列名；R13 放过 ⇒ 消失"),
        ("② 含越权断言 已生效", "可复现", "C 类：:209/:242 = 不宣告…已生效 否定式；R10 negation 豁免 ⇒ 消失"),
        ("③ 另 2 条（背景称四条）", "未验", "现盘 0 命中，旧输出未落盘；不补造具体条目名，无法逐条重判"),
    ]
    for a, b, c in rows:
        print("  %-24s %-8s %s" % (a, b, c))
    # 把谓词化门禁套到同一 t，看 A/B/C 是否全被放过
    failed, det, probs = judge(text)
    print()
    print("谓词化门禁（R13+R10+R12）对同一 t：D 类 %d 处，problems=%s" %
          (sum(1 for d in det if d["kind"] == "D"), json.dumps(probs, ensure_ascii=False)))
    return naive, probs


def run_r10_relation():
    print()
    print("=" * 78)
    print("§5 R10 覆盖缺口实跑反例（不重写 C 类，只登记 R10 没能覆盖的写法）")
    print("=" * 78)
    cases = [
        "不宣告 X 已生效，但 Y 已入账",
        "亦非不宣告 N-4 正式绑定已生效",
        "并非不宣告已生效",
    ]
    for s in cases:
        p, w, h = g7.r10_scan(s, TOKENS)
        p12, h12 = g7.r12_scan(s, TOKENS)
        print("TEXT:", s)
        print("   R10 kinds:", [(x["token"], x["kind"]) for x in h],
              "problems:", p)
        print("   R12 problems:", p12)
        failed, det, probs = judge(s)
        print("   N13:", "FAIL" if failed else "放过", [(d["kind"], d["rule"][:40]) for d in det])


def main():
    p_ok, p_fail, n_ok, n_fail = run_samples()
    real = run_real_files()
    old_naive, new_probs = run_old_gate_rejudge()
    run_r10_relation()
    print()
    print("=" * 78)
    print("总判定")
    print("=" * 78)
    all_pos = (p_fail == 0)
    all_neg = (n_fail == 0)
    all_real = all(v["passed"] for v in real.values())
    fixed = (len(old_naive) == 2 and len(new_probs) == 0)
    print("正样本 0 误拦 =", all_pos, "(%d/%d)" % (p_ok, len(POSITIVES)))
    print("负样本 0 漏网 =", all_neg, "(%d/%d)" % (n_ok, len(NEGATIVES)))
    print("真件 0 命中 D =", all_real)
    print("旧门禁两条越权误报在新谓词下消失 =", fixed)
    ok = all_pos and all_neg and all_real and fixed
    print("ALL_PASS =", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

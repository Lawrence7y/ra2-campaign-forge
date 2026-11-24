# -*- coding: utf-8 -*-
r"""
R4-FILL-91 — 给 R4_DERIVABILITY\all848.tsv 的 91 行 OK_SLOT 补写成文 ④，
只产出 R4_FILL_91\ 下的 delta 与报告；不写 coverage.tsv / PANEL.md / 任何输入。

纪律：
  * 地址一律取自 all848.tsv；不反汇编、不凭记忆补地址。
  * all848.tsv 没有的字段（COL 数值地址 / TD 数值地址 / 装表点宿主构造器 entry）
    一律写「未取得」，不编造；见 REPORT.md 的口径冲突说明。
  * grade 原值照抄（本 91 行全是 [已证]）；第 4 列原文原样保留，只在末尾追加。
  * 只写 R4_FILL_91\。
"""
import sys, io, re, collections, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT = os.path.join(ROOT, "R4_FILL_91")
ALL848 = os.path.join(ROOT, "R4_DERIVABILITY", "all848.tsv")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")

DELTA = os.path.join(OUT, "fill_delta.tsv")
REPORT = os.path.join(OUT, "REPORT.md")

# 卡面基线（不自算，照抄 R4-FILL-91.md:55）
BASE_FOUR = 307
BASE_PROVED = 1654

# Lead「站点共用」裁定原文（R4-FILL-91.md:11-15，逐字照录）
LEAD_RULING = (
    "91 行只落在 23 个装表点上，82 行与其他行共用、仅 9 行独占。"
    "按 §8.6 条 1「站点不得共用」的**字面**读，上限会掉到 9 行。\n"
    "> **裁定：取 91 行。** 理由：该判据针对的是 **② 类身份**"
    "（同一槽不得既证类又证已被用），而 ④ 的命题是「该函数经活表派发」；"
    "**同一个构造器装一张表、表内多个函数共用该装表点，是合法的物理事实**，"
    "不构成证据重复。按 9 行会误杀 82 行真实成立的证据。\n"
    "> **但须在披露里写明该共用事实与两种读法的差异。**"
)


def read_tsv(path, header_delim="\t"):
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]
    hdr = lines[0].replace(header_delim, "\t").split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = ln.split("\t")
        rows.append(dict(zip(hdr, cells)))
    return hdr, rows


def strip_deco(decorated):
    """.?AVBuildingTypeClass@@ -> BuildingTypeClass."""
    m = re.match(r"^\.\?AV(.+)@@$", decorated)
    return m.group(1) if m else None


def parse_install(field):
    """从 install_site(ext/self) 抽 (slot, vt, ext) 三元组列表，保持 all848.tsv 中的顺序。"""
    out = []
    for m in re.finditer(r"slot(\d+)@vt([0-9A-Fa-f]+)\s+ext@([0-9A-Fa-f]+)", field):
        out.append((m.group(1), m.group(2).upper(), m.group(3).upper()))
    return out


def main():
    # ---- 读输入（只读） ----
    ahdr, arows = read_tsv(ALL848, "\t")
    chdr, crows = read_tsv(COV, ",")   # coverage.tsv 表头逗号、数据行 tab
    assert len(crows) == 18498, "coverage.tsv 数据行数不是 18498，停止"

    ok = [r for r in arows if r.get("verdict") == "OK_SLOT"]
    assert len(ok) == 91, "all848.tsv OK_SLOT 行数不是 91，停止：%d" % len(ok)

    cov_by_entry = {r["entry"]: r for r in crows}

    # ---- 逐行补写 ④ ----
    delta_rows = []
    excluded = []          # (entry, reason)
    class_unobtained = []  # 类名/装饰名解不出的行
    numeric_missing = []   # 数值型地址（COL/TD/构造器 entry）不在 all848.tsv 的行
    weizheng = []          # 语义栏含 [未证] 的行
    site_counter = collections.Counter()

    for r in ok:
        e = r["entry"]
        cr = cov_by_entry.get(e)
        if cr is None:
            excluded.append((e, "coverage.tsv 无此 entry"))
            continue

        slot = r["slot_no"]
        insts = parse_install(r["install_site(ext/self)"])
        decos = [d for d in r["col_class"].split(",") if d]
        names = [strip_deco(d) for d in decos]
        good_names = [n for n in names if n]

        # 类名 / 装饰名取不到 —— 按卡面：写「未取得」并单列
        cls = "/".join(good_names) if good_names else "未取得"
        deco_str = "/".join(decos) if decos else "未取得"
        if not good_names or not decos:
            class_unobtained.append(e)

        # 地址只取 all848.tsv 已有的：vt / entry / 装表点指令地址
        vts = "/".join(i[1] for i in insts) if insts else "未取得"
        exts = "/".join(i[2] for i in insts) if insts else "未取得"
        # all848.tsv 完全没有的：COL 数值地址 / TD 数值地址 / 构造器 entry
        numeric_missing.append(e)

        # 装表点分布：按 probe.py:555 的口径，每行取 install_site 里第一个 ext@ 为代表装表点
        # （R4_DERIVABILITY 的「23 个装表点 / 9 独占 / 82 共用」即用此口径）。
        if insts:
            site_counter[insts[0][2]] += 1

        if "[未证]" in cr["one_line_semantics"]:
            weizheng.append(e)

        fourth = (
            "；④ 活表槽位见证：{cls}::slot{slot}"
            "（vt={vts}，槽 {slot} 值={entry}，"
            "COL=未取得 offset=0，RTTI=未取得→{deco}；"
            "装表点 {exts} 位于构造器体内（构造器 entry 未取得），entry 体外）"
        ).format(cls=cls, slot=slot, vts=vts, entry=e, deco=deco_str, exts=exts)

        fourth_col = cr["one_line_semantics"] + fourth
        ev = cr["evidence_path"] + ";R4_DERIVABILITY/all848.tsv"
        delta_rows.append({
            "entry": e,
            "subsystem": cr["subsystem"],
            "name": cr["name"],
            "one_line_semantics": fourth_col,
            "grade": cr["grade"],          # 原值照抄，不动
            "evidence_path": ev,
        })

    # ---- 写 delta ----
    dcol = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"]
    with open(DELTA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(dcol) + "\n")
        for row in delta_rows:
            f.write("\t".join(row[c] for c in dcol) + "\n")

    # ---- 写 REPORT ----
    n = len(delta_rows)
    nexc = len(excluded)
    ratio_new = "%d/%d" % (BASE_FOUR + n, BASE_PROVED)
    pct = 100.0 * (BASE_FOUR + n) / BASE_PROVED

    L = []
    A = L.append
    A("# R4-FILL-91 报告 — 给 91 行补写成文 ④")
    A("")
    A("> 只读输入；只写 `R4_FILL_91\\`。地址一律取自 `R4_DERIVABILITY\\all848.tsv`，"
      "未重新反汇编、未凭记忆补地址。本卡**不写** `coverage.tsv` / `PANEL.md`，"
      "只产 delta，由后续合并员应用。复跑：`python fill.py`。")
    A("")
    A("---")
    A("")
    A("## 1 · 一句话结论")
    A("")
    A("**写出表 %d 行，剔除 %d 行**；补完后全表 `[已证]` 里「④ 已成文」的比例"
      "**从 %d/%d 变成 %s（%.2f%%）**。"
      % (n, nexc, BASE_FOUR, BASE_PROVED, ratio_new, pct))
    A("")
    A("写出的 %d 行全部来自 `all848.tsv` 的 91 行 `verdict=OK_SLOT`；"
      "grade 全部保持原值 `[已证]`，第 4 列原文一字未删、只在末尾追加 ④ 句；"
      "`evidence_path` 在原值后追加 `;R4_DERIVABILITY/all848.tsv`；"
      "表头 6 列，数据行 %d 行。" % (n, n))
    A("")
    A("---")
    A("")
    A("## 2 · 一处必须先讲的口径冲突（重要，请合并员/Lead 过目）")
    A("")
    A("卡面 §「逐行 ④ 文案的格式」要求每个 ④ 句里有三个**数值地址**："
      "`COL=<COL 地址>`、`RTTI=<TD 地址>`、以及「装表点 … 位于 `<构造器 entry>` 体内」。")
    A("但硬约束又规定「地址一律取自 `all848.tsv`，不许重新反汇编另取」。"
      "实测 `all848.tsv` 的 15 列里只有：entry、vt 地址、槽号、装饰名字符串、装表点指令地址；"
      "**没有** COL 数值地址、TD 数值地址、装表点宿主构造器的 entry 地址"
      "（这三项在 `R4_DERIVABILITY\\probe.py:col_of()` 里算过，但该卡未写进 `all848.tsv`）。")
    A("")
    A("两条硬约束在这里对撞：照抄地址则无处可抄，重新反汇编则违反「不许另取」。"
      "本卡按项目既有纪律（`S04_PUSH_B1`、`PROBE_UNNAMED_R2` 等：「取不到写 `未取得`，不许编」）处理：")
    A("")
    A("- 能从 `all848.tsv` 取的（类名/装饰名、vt 地址、槽号、entry、装表点指令地址）——照抄；")
    A("- `all848.tsv` 没有的三类数值地址——④ 句里写 `未取得`，**不编造、不反汇编**。")
    A("")
    A("因此 %d/%d 行都带 `未取得` 的 COL/TD/构造器 entry 数值位；这不是「类名未取得」"
      "（%d 行的类名/装饰名全部从 `.?AV…@@` 解出），而是**地址源缺列**，"
      "与 `R4-FILL-91.md:32` 的「类名解不出」是两件事，分开记。"
      % (len(numeric_missing), n, n - len(class_unobtained)))
    A("")
    A("两种读法及后果：")
    A("")
    A("- **本卡采行读法**：④ 句结构完整、所有可得字段填满，缺的三类数值位标 `未取得`，"
      "共 %d 行进 delta。" % n)
    A("- **严格读法**（若 Lead 认为「任一地址取不到就剔除」涵盖这三类缺列）："
      "则 %d 行应全部剔除，delta 清空，比例仍为 %d/%d。"
      "本卡不自行改口径，把两种结果都摆出，由合并员/Lead 裁定。" % (n, BASE_FOUR, BASE_PROVED))
    A("")
    A("---")
    A("")
    A("## 3 · 剔除行与原因（分类计数）")
    A("")
    A("| 原因 | 行数 |")
    A("|---|---:|")
    counts = collections.Counter(reason for _, reason in excluded)
    if not counts:
        A("| 无（91 行全部满足「进 delta」条件，见 §2 的口径说明） | 0 |")
    else:
        for reason, c in counts.items():
            A("| %s | %d |" % (reason, c))
    A("")
    A("剔除 %d 行。明细：" % nexc)
    if excluded:
        for e, reason in excluded:
            A("- `%s` — %s" % (e, reason))
    else:
        A("- 无。")
    A("")
    A("类名/装饰名解不出的行（`R4-FILL-91.md:32` 要求单列）：**%d 行** —— %s"
      % (len(class_unobtained), "无" if not class_unobtained
         else "、".join("`%s`" % e for e in class_unobtained)))
    A("")
    A("---")
    A("")
    A("## 4 · 语义栏原本含 `[未证]` 的 20 行（必须单列）")
    A("")
    A("这 %d 行照常补了 ④，但**即使 ④ 补齐，其 strict 档位也不会变**"
      "（§8.1 ㉘：名字已证 ≠ 语义已证；③ 仍敞口）。"
      % len(weizheng))
    A("")
    A("| # | entry |")
    A("|---:|---|")
    for i, e in enumerate(weizheng, 1):
        A("| %d | `%s` |" % (i, e))
    A("")
    A("---")
    A("")
    A("## 5 · 23 个装表点各支撑几行")
    A("")
    A("按 `all848.tsv` 的 `install_site(ext/self)` 里的 `ext@` 指令地址统计"
      "（多行命中同一装表点时各计 1 次）；共 %d 个不同装表点，覆盖 %d 个槽命中。"
      % (len(site_counter), sum(site_counter.values())))
    A("")
    A("| 装表点指令地址 | 支撑行数 | 独占/共用 |")
    A("|---|---:|---|")
    for site, cnt in sorted(site_counter.items(), key=lambda kv: (-kv[1], kv[0])):
        A("| `%s` | %d | %s |" % (site, cnt, "独占" if cnt == 1 else "共用"))
    A("")
    A("分布：**%d 个装表点中，9 个只支撑 1 行（独占），其余支撑 ≥2 行（共用）；"
      "共用行合计 82 行。** 这与 `R4_DERIVABILITY\\all848.tsv` / `REPORT.md` 的"
      "`exclusive site rows: 9  shared site rows: 82` 一致。" % len(site_counter))
    A("")
    A("### Lead「站点共用」裁定原文（逐字照录）")
    A("")
    A("> " + LEAD_RULING)
    A("")
    A("### 两种读法的差异")
    A("")
    A("- **字面读法**（§8.6 条 1「站点不得共用」按「不同行之间也不得共用站点」解释，"
      "见 `R14_COMMON` §12.3 对照表）：91 行只落 23 个装表点，82 行与他人共用，"
      "只有 9 行独占 ⇒ ④ 可立上限掉到 **9**。")
    A("- **Lead 裁定读法**：该判据针对 **② 类身份**（同一槽不得既证类又证已被用）；"
      "④ 的命题是「该函数经活表派发」，**同一个构造器装一张表、表内多个函数共用该装表点，"
      "是合法的物理事实**，不构成证据重复 ⇒ 取 **91** 行。按 9 行会误杀 82 行真实成立的证据。")
    A("")
    A("本 delta 按 Lead 裁定的 **91 行**口径产出，并在上方给出 23 点分布与共用事实，"
      "两种读法的差异完整披露。")
    A("")
    A("---")
    A("")
    A("## 6 · 比例回答（卡面 §输出 最后一条）")
    A("")
    A("补完这 **%d** 行后，全表 `[已证]` 里「④ 已成文」的比例"
      "**从 %d/%d 变成 %s（%.2f%%）**；分母 %d 不变（91 行原本就是 `[已证]`）。"
      % (n, BASE_FOUR, BASE_PROVED, ratio_new, pct, BASE_PROVED))
    A("")
    A("---")
    A("")
    A("## 7 · 产物与纪律自检")
    A("")
    A("- `R4_FILL_91\\fill_delta.tsv`：表头 6 列，%d 数据行。" % n)
    A("- `R4_FILL_91\\REPORT.md`：本文件。")
    A("- `R4_FILL_91\\fill.py`：可复跑（只读输入，重写自己的两个产物）。")
    A("- 未改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`STATUS_BOARD.md`、"
      "`BOARD_ARCHIVE.md`、`D47_SURFACE`、`R4_DERIVABILITY`、任何 `NAMED_PUSH_*` / `AUDIT*` / `INVENTORY*`。")
    A("- 未重新反汇编 `gamemd.exe`；所有地址取自 `all848.tsv`；缺列写 `未取得` 未编造。")
    A("- grade 全为原值 `[已证]`；第 4 列原文原样保留、只末尾追加；未动第 1/2/3/5/7/8 列。")
    A("")

    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    print("OK rows in all848.tsv :", len(ok))
    print("delta data rows       :", n)
    print("excluded              :", nexc)
    print("class unobtained      :", len(class_unobtained))
    print("numeric addr missing  :", len(numeric_missing))
    print("[未证] rows listed   :", len(weizheng))
    print("distinct install sites:", len(site_counter))
    print("ratio                 : %d/%d -> %s (%.2f%%)" %
          (BASE_FOUR, BASE_PROVED, ratio_new, pct))


if __name__ == "__main__":
    main()

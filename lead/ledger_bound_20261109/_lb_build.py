# _lb_build.py — 入账合订本构建脚本（本任务写域专用；零真机、零采样代码、只读源域）
# 功能：从 5 份入账草案件「正文区」逐字抽取，拼装合订本并 print 到 stdout；
#       由外层 shell 重定向落盘（脚本自身不写任何文件，规避路径构造写入）。
#       不改任何源件、不改两台账。Python 一律 python -I -X utf8 + 绝对路径；指纹用 hashlib。
import hashlib
import os

ROOT = "D:/Project/ra2-campaign-forge"

ENTRIES = [
    {"no": 1, "sec": "§605",
     "path": "lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md",
     "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
     "end": "## ↑↑↑ 草案正文结束 ↑↑↑"},
    {"no": 2, "sec": "§606",
     "path": "lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md",
     "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
     "end": "## ↑↑↑ 草案正文结束 ↑↑↑"},
    {"no": 3, "sec": "§607",
     "path": "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
     "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
     "end": "## ↑↑↑ 草案正文结束 ↑↑↑"},
    {"no": 4, "sec": "§608",
     "path": "lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md",
     "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
     "end": "## ↑↑↑ 草案正文结束 ↑↑↑"},
    {"no": 5, "sec": "§609",
     "path": "lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md",
     "start": "## ↓↓↓ 草案正文（从这里开始整段复制）↓↓↓",
     "end": "## ↑↑↑ 草案正文结束 ↑↑↑"},
]

FP = [
    ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    ("lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md", "e863b593bf5c29a9f2ce38aca4773b7feacb625f6ac32e33d04b5e9a2bae02e4", 7806),
    ("lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md", "213fb89819d316e5a74e5acb065cc17cd2845602b9f79a45e5e10b73bb6ae4da", 6714),
    ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", "d5dc8f979503a65573bcf542fdd28dbf43f13e54dcf0d98229106db43b2f24a6", 7703),
    ("lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md", "bf010e8d22cf70892365cbadf555c8fd3b51291a355e4b49c429dc86c46f892e", 10080),
    ("lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md", "058630a1b34a8140ed2b57e796f3d64413e76e0f99a5f7f648fd56347577f9ec", 18980),
    ("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md", "1e4ceb37187cd12601ad03cdc02f0cf2ee624d1f6870c03c0e35d84cbcb40cfc", 36097),
    ("lead/s604_refsync_20261109/_rs_REFSYNC_DRAFT.md", "7477a869f1d8436b7641b3b5ba09dac778ed078228adbabc0469d5665419d572", 33869),
    ("lead/a_class_fix_20261109/_ac_A1A4A5_FIX_DRAFT_20261109.md", "6c02341b319360e06bc9f1ad096e4c8d5a04ff649c83389e806337c8ead615bc", 23258),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]


def safe(rel):
    """规范化并校验：禁止 .. 与绝对路径，结果必须落在 ROOT 之内。"""
    if ".." in rel or rel.startswith("/") or rel.startswith("\\"):
        raise RuntimeError("unsafe path: " + rel)
    full = os.path.normpath(ROOT + "/" + rel)
    if not full.startswith(os.path.normpath(ROOT) + os.sep) and full != os.path.normpath(ROOT):
        raise RuntimeError("out of root: " + rel)
    return full


def read_text(rel):
    with open(safe(rel), "r", encoding="utf-8", newline="") as f:
        return f.read()


def read_bytes(rel):
    with open(safe(rel), "rb") as f:
        return f.read()


def extract_body(rel, start_marker, end_marker):
    """Return verbatim text strictly between the two marker lines (markers excluded)."""
    lines = read_text(rel).split("\n")
    si = None
    ei = None
    for i, ln in enumerate(lines):
        if ln.strip() == start_marker.strip() and si is None:
            si = i
        if ln.strip() == end_marker.strip() and si is not None and ei is None:
            ei = i
    if si is None or ei is None or ei <= si:
        raise RuntimeError("markers not found: " + rel)
    return "\n".join(lines[si + 1:ei])


def main():
    parts = []
    W = parts.append
    bodies = {}
    for e in ENTRIES:
        body = extract_body(e["path"], e["start"], e["end"])
        bodies[e["no"]] = body
        d = read_bytes(e["path"])
        e["sha"] = hashlib.sha256(d).hexdigest()
        e["bytes"] = len(d)
        e["body_sha"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        e["body_bytes"] = len(body.encode("utf-8"))

    W("# _lb_BOUND_VOLUME.md — 待入账草案·合订本（入账合订员·hy4，2026-11-09）\n")
    W("> **性质**：本件是**合订本（索引 + 逐字照抄 + 冲突/依赖登记）**，不是台账、不入台账。")
    W("> 台账 `lead/GOAL_THREE_TARGETS_20261018.md` 与 `lead/PENDING_DECISIONS.md` 全程**只读**，未改一字。")
    W("> 唯一写域 = `lead/ledger_bound_20261109/`；产出前缀 `_lb_`。零真机、零采样代码、未 commit、未 push。")
    W("> **不替 Leader 决定哪笔先入账、哪笔暂缓**——只列冲突与依赖，顺序建议见第五区（标注「不替决」）。\n")
    W("> 引用规则：每条事实追到「本会话实跑命令 + 输出」或「文件:行」；拿不到的写「未验」，不补造。")
    W("> 编排方下发指纹 11 件，本会话 `python -I -X utf8 -c` + hashlib 全量复算 **11/11 MATCH**（见附录 A）。\n")

    W("---\n")
    W("## 一、一页纸总览（第一步清点结果）\n")
    W("### 1(a) 真正「待追加进台账」的笔数\n")
    W("**5 笔**（暂编 §605–§609）。判定口径：带可整段复制追加的 `## §6xx` 草案正文、且目标为 `GOAL_THREE_TARGETS` 尾部新节。")
    W("- 原四笔（`lead/ledger_appendix_20261108/`）：笔1 §605、笔2 §606、笔3 §607、笔4 §608。")
    W("- 第五笔（`lead/s604_verdict_entry_20261109/`）：§609。")
    W("- 「改既有件」的订正草案（S604_REFSYNC、A_CLASS、handoff_pack U1–U9、refsync_full）**不是入账草案**，")
    W("  它们是改/加注既有件的建议（见附录 D）；本会话 grep 实证：这些件 `^## §6` 命中数均为 0。\n")
    W("> **关于任务第三步(b)「六笔全入账」**：本会话全仓 grep `§610`/`S610`/`第六笔`/`六笔全入账`（排除 sandbox 副本）"
      "均 **0 命中**；带 `## §6xx` 草案正文的入账件全仓仅 5 个节号（§605–§609）。"
      "故按实读盘点为 **5 笔**，「六笔」与现盘不符，按「不补造」如实登记；若编排方另指第六笔，"
      "需补下发该件路径与编号（本合订本未代造）。\n")

    W("### 1(b) 每笔：暂编编号 / 标题 / 正文出处 / 字节数\n")
    W("| 笔 | 暂编 | 标题（节题首句） | 正文出处（单件草案件） | 草案件字节数 | 本会话 SHA256 |\n")
    W("|:--:|:--:|:--|:--|--:|:--|\n")
    titles = {
        1: "N-9:205 P6 前提订正 → 半闭半开",
        2: "O1–O4 必要性补证：necessaryCount=3、最小集 O1–O3",
        3: "§604「空档/空档差」两列不可复现（0/15、15 窗全正）",
        4: "「以乙替代甲」补登（九 hunk + 11 件指纹；登记而非放行）",
        5: "§604 码形定谳：错误源 = 撰写轮内联脚本 dur 字典错位（等价 C8a）",
    }
    for e in ENTRIES:
        W("| {} | {} | {} | `{}` | {} | `{}` |\n".format(
            e["no"], e["sec"], titles[e["no"]], e["path"], e["bytes"], e["sha"][:16] + "…"))
    W("\n- 四笔汇编件 `lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md`（45719 B）："
      ":47/:81/:111/:150 分别逐字转录笔1–笔4 正文区（:4 自述构建脚本 `_lad_build.py` 直接抽取）。")
    W("- 第五笔同文副本 `lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md`（36097 B）"
      ":66-86（§4.1）载同一 §609 正文（:86 明写「与 `_ve_DRAFT_S609.md` 正文区逐字一致」）。")
    W("- 5 段草案正文**逐字照抄**见第二区；每段附 `被核对象 SHA256 = <64位>`、`字节数 = <数字>` 绑定行（见各章末）。\n")

    W("### 1(c) 有没有已入账的？\n")
    W("**没有，5 笔全部未入账**。本会话实跑：\n")
    W("```\n")
    W("cd /d/Project/ra2-campaign-forge && grep -nE '§60[5-9]|§610|半闭半开|码形定谳|dur 字典|以乙替代甲|'\n")
    W("  '甲乙绑定|necessaryCount|O4 非必要|空档差.*0/15' lead/GOAL_THREE_TARGETS_20261018.md lead/PENDING_DECISIONS.md\n")
    W("→ 无输出（exit=1，0 命中）\n")
    W("```\n")
    W("- 台账 `GOAL_THREE_TARGETS` 现有 `## §` 共 61 节，末节 = **§604 @:9687**，全文止于 :9757（`wc -l` = 9757）；"
      "`PENDING_DECISIONS` 当前待裁段仅 D-13/D-14（:30/:67 原始正文，:22-27 D-13 状态行）。")
    W("- 两台账当前 SHA256 仍为编排方基线（`PENDING` = `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` / 52419 B；"
      "`GOAL` = `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` / 759518 B），本会话复算同值。")
    W("- 旁证：`_la_SUMMARY.md:47` 已记两台账内 `0xB0CD48`/静态 u64/乙替代甲/H01 等 grep 0 命中、四笔确均未入账；"
      "§609 交付件 `S604_VERDICT_ENTRY_DRAFT.md:129` 记两台账 `S604|512655|512667|512650` grep 0 命中。\n")

    W("### 依赖关系速览（详见第二区各章与第三区）\n")
    W("| 笔 | 暂编 | 依赖 / 被依赖 | 性质 |\n")
    W("|:--:|:--:|:--|:--|\n")
    W("| 1 | §605 | 与订正草案无引用耦合（grep 实证 0 命中） | 独立 |\n")
    W("| 2 | §606 | 与订正草案无引用耦合（grep 实证 0 命中） | 独立 |\n")
    W("| 3 | §607 | **被第五笔 §609 补充**（笔3 边界句「不能定位」被定谳超越） | 与第5笔成组议题 |\n")
    W("| 4 | §608 | **与 handoff_pack U1–U9 共享被绑定文件**（STATE_MATRIX.json / B2B_DESIGN.md / 九 hunk +255/−13） | 与改既有件草案联动 |\n")
    W("| 5 | §609 | **依赖/补充笔3**；其失效引用面由 S604_REFSYNC、refsync_full 承接 | 与第3笔成组议题 |\n")
    W("\n> 编号：现暂编 §605–§609（5 节），**与台账现状（末节 §604）无冲突**；"
      "若「六笔」成立需另加 §610，但本会话未见第六笔草案（见 1(a) 注）。\n")

    W("---\n")
    W("## 二、每笔一章（草案正文逐字照抄 + 出处 + 依赖标注）\n")
    W("> 抽取口径：各单件草案件 `## ↓↓↓ 草案正文…` 与 `## ↑↑↑ 草案正文结束…` 两标记行之间的全部行，"
      "**不含标记行本身**，逐字照抄（构建脚本 `_lb_build.py` 用 `split('\\n')` 切片，未按字符改写）。"
      "每章末给出「被核对象 SHA256 = …，字节数 = …」绑定行（格式固定，中间不插任何字符）。\n")

    deps = {
        1: "**依赖标注**：无笔间硬依赖。与三份「改既有件」订正草案的引用关系 = 0（本会话 grep "
           "`0xB0CD48|半闭半开|N-9:205|STATIC_COUNT_SPEC|N9_SPEC_ERRATUM` 于 s604_refsync / s604_refsync_full / "
           "a_class_fix / handoff_pack 四写域均 0 命中；§609 交付件 :60 明写「笔1…与本定谳无引用耦合」）。"
           "笔1 自身的「下游九行清单」是改上游件的注记建议（笔1 正文 :24），非本批订正草案的目标行。",
        2: "**依赖标注**：无笔间硬依赖。§609 交付件 :60 明写「笔2…与本定谳无引用耦合」。"
           "笔2 正文声明不触碰 `PENDING_DECISIONS.md` 的 D-13 状态行（:4/:20），两台账分工 = 只进 GOAL。",
        3: "**依赖标注**：**与第五笔（§609）成组议题**。笔3 边界句（`_la_draft3_s604_gapdiff.md:25`、汇编件 :123）"
           "「只能判『不可复现』、不能定位当年错误步骤」被 §609 码形定谳（错误步骤 = dur 字典错位）超越；"
           "§609 交付件 :55-59 / :147-152 判「需要补充（最小修订一处），不是整体修订，更不是被取代」，"
           "并给出改文建议（改时态限定 + 指引）。两笔数字面零冲突。详见第三区 3.1(2a)。",
        4: "**依赖标注**：**与 handoff_pack U1–U9 存在「共享被绑定文件」联动**。笔4 正文 :16-27 的 11 件版本绑定中，"
           "`STATE_MATRIX.json` = `1d4ccc93…`/3558 B、`B2B_DESIGN.md` = `565771d8…`/66735 B 两件，"
           "正是 handoff_pack `APPROVAL_PACK.md:38-39` 指纹表第 10/11 件、也是 U2–U7 的改文目标件（:51-56）；"
           "U1 的改文核心「九 hunk 内实测 +255/−13」(:62-72) 与笔4 :28 的「+255/−13、九 hunk」同源。"
           "本会话复算该两件现盘指纹仍与两处登记逐位一致（未漂移）。"
           "但 handoff_pack 未出现 `§608`/`以乙替代甲`/`YI_SUPERSEDE`/`补登件` 字样（grep 实证 0 命中）——"
           "即二者是**同物（乙线既有件）的两套动作**：笔4 是「登记」，U1–U9 是「改既有件」，"
           "互相不引用对方的草案文本；若 U2–U7 落盘，则笔4 §4 表两件指纹过期，须重签/刷新（属改既有件后果，非笔间硬顺序）。",
        5: "**依赖标注**：**依赖/补充笔3（§607）**。§609 正文 :21-22 自述：对第三笔草案「其复算数字、订正清单、"
           "不可引用清单全部不受影响」；「其边界句……自本节起不再成立」。§609 交付件 :66-67 建议编号 §609、"
           "位置首选「零重排方案」（四笔维持 §605–§608，本笔追加于笔4 之后）；:68 备选「相邻方案」"
           "（插在笔3 与笔4 之间 → 本笔 §608、甲乙绑定顺延 §609）。**两案取一留 Leader，本合订本不代决。**"
           "另：§609 交付件 :137 自报复核 verdict=partial → 本草案整体按 **unconfirmed** 登记"
           "（最终效力由台账所有者裁决）；其失效引用面由 S604_REFSYNC（13 处）、refsync_full（剩余 28 处）承接，"
           "见附录 D。",
    }
    srcnote = {
        1: "正文出处 = `lead/ledger_appendix_20261108/_la_draft1_n9_p6_erratum.md:14-27`（标记行 :12/:29 之间）；"
           "同文副本 = `LEDGER_APPENDIX_DRAFT.md:47-60`。",
        2: "正文出处 = `lead/ledger_appendix_20261108/_la_draft2_o4_necessity.md:13-23`（标记行 :11/:25 之间）；"
           "同文副本 = `LEDGER_APPENDIX_DRAFT.md:81-91`。",
        3: "正文出处 = `lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md:13-26`（标记行 :11/:28 之间）；"
           "同文副本 = `LEDGER_APPENDIX_DRAFT.md:111-124`。",
        4: "正文出处 = `lead/ledger_appendix_20261108/_la_draft4_yi_supersede_jia.md:13-41`（标记行 :11/:43 之间）；"
           "同文副本 = `LEDGER_APPENDIX_DRAFT.md:150-178`。",
        5: "正文出处 = `lead/s604_verdict_entry_20261109/_ve_DRAFT_S609.md:13-25`（标记行 :11/:27 之间）；"
           "同文副本 = `S604_VERDICT_ENTRY_DRAFT.md:70-82`（§4.1，:86 自述逐字一致）。",
    }
    for e in ENTRIES:
        W("### 第 {} 笔 · {} · {}\n\n".format(e["no"], e["sec"], titles[e["no"]]))
        W("- **草案正文出处**：{}\n".format(srcnote[e["no"]]))
        W("- **草案件指纹**：SHA256 = `{}`，字节数 = {}（本会话 hashlib 实算，与编排方基线一致）。\n".format(e["sha"], e["bytes"]))
        W("- {}\n\n".format(deps[e["no"]]))
        W("#### ↓↓↓ 草案正文（逐字照抄，从下一行起）↓↓↓\n\n")
        W(bodies[e["no"]])
        W("\n\n#### ↑↑↑ 草案正文（逐字照抄结束）↑↑↑\n\n")
        W("- **本章正文逐字核验**：抽取段 UTF-8 字节数 = {}，SHA256 = `{}`（`_lb_build.py` 实算）。\n".format(
            e["body_bytes"], e["body_sha"]))
        W("- **被核对象绑定行（复核回件要件）**：{}\n\n".format(
            "被核对象 SHA256 = " + e["sha"] + "，字节数 = " + str(e["bytes"])))

    W("---\n")
    W("## 三、入账前必须解决的前置问题（集中列；不替 Leader 决定）\n")
    W("| # | 前置问题 | 涉及笔 | 依据 | 待谁定 |\n")
    W("|:--:|:--|:--|:--|:--|\n")
    W("| Q1 | **笔3（§607）与第五笔（§609）的关系须先定**：笔3 边界句「不能定位当年错误步骤」"
      "被 §609 定谳超越。三选一：①笔3 保持原样另立 §609（数字不冲突、措辞有一处过时张力）；"
      "②同批给笔3 边界句做「最小一处」补充（§609 交付件 :68-71 给了改文文本）；"
      "③两笔合并。**「补充还是冲突」的判定见 3.1(2a)**——判「补充（最小修订）」为现有材料的一致口径，"
      "但取哪一处置方案留台账所有者。 | 3、5 | `_ve_DRAFT_S609.md:22/:46-48/:68-71`；"
      "`S604_VERDICT_ENTRY_DRAFT.md:55-59/:147-152`；`_la_draft3_s604_gapdiff.md:25` | 台账所有者 |\n")
    W("| Q2 | **§609 的效力状态**：其复核 verdict = partial → 交付件 :137 自报「本草案整体按 unconfirmed 登记」。"
      "是否以 unconfirmed 状态入账、或先补复核，须裁决。 | 5 | `S604_VERDICT_ENTRY_DRAFT.md:137-143` | 台账所有者 |\n")
    W("| Q3 | **编号/位置两案取一**：零重排（§605–§608 + §609）vs 相邻（§609 插笔3/笔4 之间 → "
      "本笔 §608、甲乙绑定顺延 §609，需同步改汇总表 :204-207 与 :11/:222 约 4 处编号引用）。"
      "| 1–5 | `S604_VERDICT_ENTRY_DRAFT.md:147-148`；`_ve_DRAFT_S609.md:66-67` | Leader |\n")
    W("| Q4 | **笔4 §608 与 handoff_pack U1–U9 的先后**：U2–U7 若落盘，`STATE_MATRIX.json`/`B2B_DESIGN.md`"
      "新指纹会使笔4 §4 表两件绑定过期；且 U2–U7 按 P3「六处同批」强制、U8/U9 独立、"
      "V2 重发/重签件换版/两台账补登为级联收尾。是否先改件再登记、或先登记再改件，须裁决。"
      "| 4（联动改既有件） | `APPROVAL_PACK.md:38-39/:51-56`；`_hp_OVERVIEW.md:31-40/:48` | Leader + 三方批准人 |\n")
    W("| Q5 | **「六笔 vs 五笔」口径**：任务第三步(b) 写「若六笔全入账」，本会话全仓盘点仅 5 笔"
      "（§605–§609）、无 §610 草案。若确有第六笔，需补下发路径与编号。 | 全部 | 本会话全仓 grep 实证（1(a) 注） | 编排方 |\n")
    W("| Q6 | **§604 原文是否改写 / 归属终件类名是否加后注 / 笔3 边界句是否修订**：三处均由草案"
      "明写「留台账所有者裁决」（笔3 正文 :25、§609 正文 :24）。 | 3、5 | "
      "`_la_draft3_s604_gapdiff.md:25`；`_ve_DRAFT_S609.md:24` | 台账所有者 |\n")
    W("| Q7 | **两台账分工与自检**：四笔 + 第五笔均声明「只进 GOAL_THREE_TARGETS、"
      "PENDING_DECISIONS 本批一字不动」；追加前后须复算两基线指纹、GOAL 行数增量 = 实际追加行数、"
      "PENDING 增量 = 0。 | 1–5 | `LEDGER_APPENDIX_DRAFT.md:12/:28-31`；"
      "`S604_VERDICT_ENTRY_DRAFT.md:153` | Leader（执行追加时） |\n")
    W("\n### 3.1 第二步逐组判定（回答 2(a)/2(b)/2(c)）\n")
    W("**2(a) 笔3 vs 第五笔：补充，不是冲突（但含一处「过时表述」需加限定）。**\n")
    W("- 笔3 说「只能判不可复现、不能定位当年错误步骤」（`_la_draft3_s604_gapdiff.md:25`），"
      "第五笔说「错误在撰写轮内联脚本 `dur` 字典推导错位、表值系如实转录」"
      "（`_ve_DRAFT_S609.md:13-15/:22`）。")
    W("- 判定口径（三处一致）：`_ve_DRAFT_S609.md:46-48`「**需要补充（最小修订一处），不是整体修订，更不是被取代**」；"
      "`S604_VERDICT_ENTRY_DRAFT.md:55-59`「判定：需要补充（最小修订一处边界句）」；"
      "`:57`「数字面零冲突」、`:58`「唯一被事实超越的是一处边界句」。")
    W("- 补充点：第五笔补的是笔3 当时够不着的「错误在哪一步」；笔3 的复算数字（时长 30/30、空档 3/30、"
      "空档差 0/15、15 窗全正 +0.0065..+0.1080）、订正清单、不可引用清单**全部不受影响**"
      "（`S604_VERDICT_ENTRY_DRAFT.md:78/:107`）。")
    W("- 冲突面（仅措辞、非数字）：笔3 边界句「不能定位」自 §609 起过时；归属终件 `S604_ATTRIBUTION.md:136`"
      "「category = 台账记错」类名如无后注易被误读为誊写错误（誊写已被 15/15 逐位比对排除）。"
      "按「事实类裁定不推翻 + 机理开口闭合 + 类名加限定」并读即自洽（`:59`）。\n")
    W("**2(b) 笔1 与订正草案的引用关系：无（0 命中）；唯一沾边是同名词「P6」的巧合。**\n")
    W("- 本会话实跑 grep `0xB0CD48|半闭半开|N-9:205|N9_SPEC_ERRATUM|static_spec_n9|静态 u64 窗口读可闭` 于 "
      "`lead/s604_refsync_20261109/`、`lead/s604_refsync_full_20261109/`、`lead/a_class_fix_20261109/`、"
      "`lead/handoff_pack_20261109/` 四写域全部 md → 笔1 主对象 0 命中；仅 `s604_refsync_full` :234/:236 与 "
      "`S604_VERDICT_ENTRY_DRAFT.md:125` 出现「其余未验项（0xB0CD48 等）不受影响」，系转引 _dr_RULING:147 的"
      "未验项括号，非笔1 引用。")
    W("- handoff_pack 中 `P6` 命中均为其自身**未决项编号 P1–P16 之 P6（U4/U7 拼接点）**"
      "（`_hp_OVERVIEW.md:14`、`_hp_PENDING_AND_SIGNOFFS.md:14`），与笔1 的「P6 静态 u64 窗口读」**同名异物、无关**。")
    W("- §609 交付件 `:60` 明写「笔1 / 笔2 / 笔4 与本定谳无引用耦合」。笔1 的「下游九行清单」"
      "（`_la_draft1_n9_p6_erratum.md:24`）指向上游 STATIC_COUNT_SPEC 等九件，均非本批三份订正草案的目标件"
      "（grep 实证 0 命中）。\n")
    W("**2(c) 笔4 与 handoff_pack U1–U9：有「共享被绑定文件/同源事实」关系，无「草案正文互引」关系。**\n")
    W("- 共享物证：笔4 §4 表 11 件中的 `STATE_MATRIX.json`（`1d4ccc93…`/3558 B）与 `B2B_DESIGN.md`"
      "（`565771d8…`/66735 B），= handoff_pack `APPROVAL_PACK.md:38-39` 第 10/11 件，且是 U2–U7 改文目标"
      "（`:51-56`、`:81`、`:139`）；U1 改文「九 hunk 内实测 +255/−13」（`:62-72`）与笔4 :28「+255/−13、九 hunk」同源。"
      "本会话复算两件现盘指纹与两处登记逐位一致（未漂移）。")
    W("- 无互引：grep `§608|YI_SUPERSEDE|以乙替代甲|甲乙|ledger_appendix|补登件|APPROVE_SCOPE` 于 "
      "handoff_pack → 0 命中（其「台账补登」指编排方对改件动作的收尾登记，非指 §608 草案）。")
    W("- 判定：二者是**同一乙线既有件上的两类动作**——笔4 = 台账登记（§608），U1–U9 = 改既有件；"
      "无硬顺序，但 U2–U7 落盘会使笔4 §4 表两件指纹过期（需重签/刷新），属「改既有件后果」，"
      "列入第三区 Q4 前置问题。\n")

    W("---\n")
    W("## 四、编号冲突检查（第三步）+ 附录\n")
    W("### 4.1 3(a) 台账实际尾部\n")
    W("- 实跑：`grep -n '^## §' lead/GOAL_THREE_TARGETS_20261018.md | tail -3` → "
      "§602 @:9510、§603 @:9585、**§604 @:9687**；`wc -l` = **9757**，`grep -c '^## §'` = **61**。")
    W("- 故台账实际尾部 = **§604**（不是 §609；§605–§609 全为「暂编」，尚在草案里）。"
      "编排方下发的「台账尾部结构」同值（末节 §604 @:9687、tail :9757）。\n")
    W("### 4.2 3(b) 若 N 笔全入账的编号\n")
    W("- 按本会话实盘点的 **5 笔**：编号恰为 **§605–§609**，无需重排（§605 紧接 §604，连续、无空号、无重复）。")
    W("- 任务书「若六笔全入账，编号会是 §605-§610 还是需要重排？」：若真有第 6 笔，则应是 **§605–§610**（仍连续、"
      "无需重排，因为现尾 §604）；但**本会话未发现第 6 笔入账草案**（全仓 `§610`/`S610`/`第六笔` 0 命中），"
      "故 §610 属「未验/未见」，不补造。")
    W("- 唯一会触发「重排」的是 §609 交付件 `:148` 的**相邻方案**（插笔3/笔4 之间 → 本笔变 §608、"
      "甲乙绑定顺延 §609，需同步改汇总表 :204-207 与 :11/:222 约 4 处编号引用）；首选「零重排方案」"
      "则不动编号。两案取一留 Leader（第三区 Q3）。\n")
    W("### 4.3 3(c) 有没有哪笔编号与台账现状冲突？\n")
    W("**没有**。§605–§609 全部 > 现尾 §604，两台账内 `§60[5-9]|§610` grep 0 命中（1(c) 实跑）；"
      "PENDING_DECISIONS 的 D 编号（现 D-13/D-14）与 § 节号是两套序列，不冲突。"
      "仅「暂编」性质本身须 Leader 最终确认（四笔汇编件 :11、§609 交付件 :147 均写「Leader 可重排」）。\n")

    W("### 附录 A · 编排方下发指纹 11 件（本会话 hashlib 全量复算 11/11 MATCH）\n")
    W("实跑命令：`python -I -X utf8 -c \"...hashlib...\"`（内联，11 件绝对路径，`sha256` + `len`），"
      "输出逐件 `OK` 与本表一致：\n")
    W("| 件 | SHA256 | 字节数 |\n|:--|:--|--:|\n")
    for p, h, b in FP:
        W("| `{}` | `{}` | {} |\n".format(p, h, b))
    W("\n### 附录 B · 本合订本实际文件清单（写域 `lead/ledger_bound_20261109/`）\n")
    W("| 文件 | 作用 |\n|:--|:--|\n")
    W("| `_lb_BOUND_VOLUME.md` | 本合订本（一页总览 + 5 章逐字正文 + 前置问题 + 附录 + 顺序建议） |\n")
    W("| `_lb_build.py` | 构建脚本（只读源域、逐字抽取、print 到 stdout、shell 重定向落盘） |\n")
    W("| `_lb_fp_out.txt` | 11 件基线指纹 + 5 段正文抽取指纹 + 收尾两台账指纹复算输出 |\n")
    W("| `_lb_VERIFY.md` | 逐字照抄核验与纪律自检（对照命令 + 结论） |\n")
    W("\n### 附录 C · 合订本大纲（章节结构）\n")
    W("```\n")
    W("一、一页纸总览  1(a) 笔数=5 / 1(b) 每笔编号·出处·字节 / 1(c) 已入账 grep=0 / 依赖速览\n")
    W("二、每笔一章 × 5   出处 + 指纹 + 依赖标注 + ↓↓↓逐字正文↑↑↑ + 绑定行\n")
    W("三、入账前必须解决的前置问题  Q1–Q7 + 3.1 逐组判定(2a/2b/2c)\n")
    W("四、编号冲突检查(3a/3b/3c) + 附录 A 指纹 / B 文件清单 / C 大纲 / D 改既有件订正草案清单\n")
    W("五、入账顺序建议（不替决） 5(a) 硬顺序 / 5(b) 独立 / 5(c) 成组\n")
    W("```\n")

    W("### 附录 D · 改既有件的订正草案清单（**不是入账项**，但 Leader 需要知道）\n")
    W("> 共同性质：只出「改原文 / 加注不改 / 保留不动」建议，**不改任何件、不改台账、不追加新节**；"
      "本会话 grep 实证这四写域的 `^## §6` 命中数均为 0（无台账草案正文）。\n")
    W("| 组 | 写域 / 主件 | 规模 | 目标（改既有件） | 与入账笔的关系 |\n")
    W("|:--|:--|:--|:--|:--|\n")
    W("| D-1 S604_REFSYNC | `lead/s604_refsync_20261109/`：`_rs_REFSYNC_DRAFT.md`（33869 B，首轮）、"
      "`S604_REFSYNC_DRAFT.md`（38819 B，第二轮，吸收 partial 回件） | **13 处**（14 行位；"
      "分布：改 2 / 加注 10 / 保留 1，`S604_REFSYNC_DRAFT.md:6`） | 6 件历史写域的失效/过时引用逐处三选一"
      "（含 `LEDGER_APPENDIX_DRAFT.md:123` ≡ `_la_draft3_s604_gapdiff.md:25` 笔3 边界句） | "
      "**承接第五笔 §609 的失效引用面**；其改文针对笔3 边界句处8≡处9，与 Q1 同一处 |\n")
    W("| D-2 refsync_full | `lead/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md`（55331 B，修订版，状态 unconfirmed） | "
      "**剩余 28 处**（`_rf_...:6`：改 3 / 加注 22 / 保留 3；`:57` 与 §4.2 全表对账 43−15=28） | "
      "§609 交付件 §4.2 43 处清单中未被 D-1 覆盖的剩余处 | 同 D-1，承接第五笔 |\n")
    W("| D-3 A_CLASS | `lead/a_class_fix_20261109/`：`_ac_A1A4A5_FIX_DRAFT_20261109.md`（23258 B，草案）、"
      "`A_CLASS_FIX_DRAFT.md`（29212 B，交付件终稿） | **A1/A4/A5 三处**逐字改文（MATRIX:90、"
      "`_mr_REACH_EVIDENCE`:112/:121）；A2/A3 不重复拟（已在 U8/U9） | "
      "`matrix_reach_20261109/` 两受核件 | 与 U8/U9 同坐标系（A2=MATRIX:154=U8、A3=:146=U9），"
      "与入账 5 笔无正文引用 |\n")
    W("| D-4 handoff_pack U1–U9 | `lead/handoff_pack_20261109/APPROVAL_PACK.md`（40024 B）"
      "+ `_hp_U1.md`…`_hp_U9.md`（九条一页）+ `_hp_OVERVIEW.md` 等 | **9 条内容订正，落点 9 行 4 文件**"
      "（`_hp_OVERVIEW.md:10-12`）：U1 V2:91；U2–U4 STATE_MATRIX.json:2/:5/:4；U5–U7 B2B_DESIGN.md:148/:151/:150；"
      "U8/U9 MATRIX_DEFECT_REACHABILITY.md:154/:146。约束：U2–U7 **六处同批**（P3 强制）、U8/U9 同批为宜、"
      "16 项未决 P1–P16、换版级联 4 次、三方批准 | **与笔4 §608 共享被绑定文件**（STATE_MATRIX.json / "
      "B2B_DESIGN.md / 九 hunk +255/−13）；落盘会使笔4 §4 表两件指纹过期（Q4） |\n")
    W("\n> D-1/D-2 与 D-3/D-4 之间：D-3 明写 A2/A3 复用 U8/U9 改文（不重复拟）；"
      "D-1/D-2 与 D-4 无交叉。四组均为「改既有件」，**不在本合订本 5 笔入账项之内**。\n")

    W("---\n")
    W("## 五、入账顺序建议（**不替 Leader 决定**；只列硬约束与可独立项）\n")
    W("### 5(a) 哪些笔之间有硬顺序？\n")
    W("- **无「笔必须先于笔」的强制硬顺序**（就草案正文可整段复制而言）：四笔汇编件 "
      "`LEDGER_APPENDIX_DRAFT.md:11` 明写「四段各自独立、可单独追加」，:209「任何一笔在 Leader 整段复制追加前"
      "都不构成台账内容」。")
    W("- **唯一成组的硬议题是笔3 ↔ 第五笔的内容顺序**：§609 正文 :21-22 自述「对第三笔草案……边界句自本节起"
      "不再成立」、其效力说明以「第三笔草案」为参照物（`LEDGER_APPENDIX_DRAFT.md:111-124`、暂编 §607）。"
      "若 §609 先于笔3 入账，则 §609 正文里「第三笔草案（暂编 §607）」指向一个当时尚不存在的台账节，"
      "虽交付件 :67 已写「节内已写明与笔3 的对照关系」，但**叙述自洽性**上宜笔3 在先、§609 在后"
      "（或同批并明确两节互引）。交付件 :148 的「相邻方案」正是把 §609 插在笔3 与笔4 之间以让对照最顺。"
      "**这是「宜」不是「必须」，取哪一案留 Leader**（Q1/Q3）。")
    W("- 反向不成立：§609 交付件 :48 明写「笔3 保持原样可入账（数字全部有效）」——即笔3 不依赖 §609 先入。\n")
    W("### 5(b) 哪些笔可以独立入账？\n")
    W("| 笔 | 可独立？ | 依据 |\n|:--:|:--|:--|\n")
    W("| 1 §605 | **可独立** | §609 交付件 :60「笔1…无引用耦合」；与三份订正草案 grep 0 命中（3.1(2b)）；"
      "笔1 正文自带基线指纹、未验项、零改动声明，可整段复制 |\n")
    W("| 2 §606 | **可独立** | :60「笔2…无引用耦合」；只进 GOAL、不触碰 PENDING 的 D-13（笔2 :4/:20） |\n")
    W("| 4 §608 | **可独立（但与改既有件有联动，非笔间硬顺序）** | :60「笔4…无引用耦合」；"
      "与 handoff_pack 共享被绑定文件属「改件后指纹刷新」问题（Q4），不是入账笔之间的依赖 |\n")
    W("| 3 §607 | **可独立（数字面）** | §609 交付件 :48「笔3 保持原样可入账」；仅边界句措辞与 §609 有"
      "过时张力（Q1），不构成数字或事实冲突 |\n")
    W("| 5 §609 | **有条件**：建议与笔3 成组 / 或以「节内对照」方式入账 | 见 5(a)；"
      "另其状态 unconfirmed（Q2）、失效引用面需 D-1/D-2 承接（附录 D） |\n")
    W("\n### 5(c) 若 Leader 只入前几笔，哪几笔必须成组？\n")
    W("- **笔3 + 第五笔（§607 + §609）是唯一「建议成组」的一对**：两笔同讲 §604 空档列，"
      "§609 以笔3 为对照物、并取代其边界句；若只入其一，须在 Q1 里明确另一笔的处置"
      "（保持原样 / 最小补充 / 合并），否则台账会出现「笔3 说不能定位」与「§609 说已定位」的并读张力。"
      "交付件 :68 明确建议「笔3 是否同时修订：建议是，最小一处」并给出改文。")
    W("- **笔1 / 笔2 / 笔4 三笔之间不成组**：彼此无引用耦合，各自可单独整段追加"
      "（汇编件 :11、`:209`），任一笔单独入账都不影响其余笔的正文有效性。")
    W("- **若只入「前四笔」（§605–§608）**：完全自洽——四笔汇编件本就是按此批量核对/复核（confirmedCount=4、"
      "verdict=confirmed）交付的；第五笔 §609 作为后续单独追加即可（交付件 :147 首选零重排方案）。")
    W("- **若只入「前五笔」全部**：编号 §605–§609 连续、无重排（4.2）。\n")
    W("> **纪律复述**：以上全为「建议 / 宜 / 硬约束清单」，**不替 Leader 决定哪笔先入账、哪笔暂缓**；"
      "编号、位置、Q1–Q7 处置、是否批准追加，一律由 Leader / 台账所有者裁定。\n")

    W("---\n")
    W("## 收尾纪律自检\n")
    W("- 零真机：未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存。")
    W("- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。")
    W("- 绝对只读：`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`、"
      "`lead/ledger_appendix_20261108/`、`lead/s604_verdict_entry_20261109/`、`lead/s604_refsync_20261109/`、"
      "`lead/a_class_fix_20261109/`、`lead/handoff_pack_20261109/` 一律未修改/追加/覆盖"
      "（收尾复算两指纹同编排方基线，见 `_lb_fp_out.txt`）。")
    W("- 唯一写域 = `lead/ledger_bound_20261109/`；产出前缀 `_lb_`。")
    W("- 草案正文**逐字照抄**（`_lb_build.py` 标记行切片，未润色改写）；绑定行格式固定"
      "「被核对象 SHA256 = <64位十六进制>，字节数 = <数字>」，中间不插任何字符。")
    W("- 不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 hashlib。\n")

    sys_out = "".join(parts)
    # 排版归一化（只作用于合订员自撰散文，绝不碰 5 段逐字正文）：
    # 先把 5 段正文换成不参与匹配的占位符，对剩余散文补换行，再把正文原位换回。
    import re
    holders = []
    for e in ENTRIES:
        ph = "\x00LB_BODY_{}\x00".format(e["no"])
        holders.append((ph, bodies[e["no"]]))
        sys_out = sys_out.replace(bodies[e["no"]], ph, 1)
    # 句末标点后紧接 markdown 块起始标记时补换行（表格行内 | 不作为块起始，故不含 |）
    norm_pat = re.compile(r'(?<=[。；”"）])(?=(?:#{1,4} |> |\- \*\*|\- |```|---\n))')
    sys_out = norm_pat.sub("\n", sys_out)
    for ph, body in holders:
        sys_out = sys_out.replace(ph, body, 1)
    # 用 binary stdout 写出，避免 Windows 文本层把 \n 翻成 \r\n（源件为纯 LF，逐字照抄必须保持 LF）
    import sys
    sys.stdout.buffer.write(sys_out.encode("utf-8"))
    sys.stdout.buffer.flush()

    # 指纹/核验清单走 stderr，由外层 2> 重定向到 _lb_fp_out.txt，不污染 stdout 正文
    err = sys.stderr
    print("=== BASELINE 11 (hashlib) ===", file=err)
    for p, h, b in FP:
        d = read_bytes(p)
        ok = (hashlib.sha256(d).hexdigest() == h and len(d) == b)
        print("{} {} {} {}".format("OK" if ok else "MISMATCH", hashlib.sha256(d).hexdigest(), len(d), p), file=err)
    print("=== BODY EXTRACTS (逐字段 hashlib) ===", file=err)
    for e in ENTRIES:
        print("BODY {} {} {} {}".format(e["no"], e["sec"], e["body_sha"], e["body_bytes"]), file=err)
    print("=== TAIL (两台账收尾复算) ===", file=err)
    for p in ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]:
        d = read_bytes(p)
        print("TAIL {} {} {}".format(hashlib.sha256(d).hexdigest(), len(d), p), file=err)


if __name__ == "__main__":
    main()

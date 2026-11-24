# -*- coding: utf-8 -*-
"""Compose CHECK_FAMILY_LINEAGE.md from in-domain census/lineage/detect JSON.
Read-only with respect to all audited scripts; writes only the one deliverable."""
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "check_family_20261109"
OUT = WD / "CHECK_FAMILY_LINEAGE.md"

census = json.loads((WD / "_cf_census_out.json").read_text(encoding="utf-8"))
lineage = json.loads((WD / "_cf_lineage_out.json").read_text(encoding="utf-8"))
detect = json.loads((WD / "_cf_detect_out.json").read_text(encoding="utf-8"))
cfv_census = json.loads((WD / "_cfv_census_out.json").read_text(encoding="utf-8"))
cfv_lineage = json.loads((WD / "_cfv_lineage_out.json").read_text(encoding="utf-8"))


def fmt_list(v):
    return ",".join(str(x) for x in v) if v else "-"


# ---- full 173-row census table (path / bytes / full SHA256 / lines / mtime) ----
rows = ["| # | rel | bytes | sha256 (完整 64 位) | lines | mtime | orch_any | require_all | pass_print |",
        "|---|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(census["all_files"], 1):
    rows.append("| %d | `%s` | %d | `%s` | %d | %s | %s | %s | %s |" % (
        i, r["rel"], r["bytes"], r["sha256"], r["nlines"], r["mtime_iso"],
        fmt_list(r["orch_any"]), fmt_list(r["require_all"]), fmt_list(r["pass_print"])))
FULL_CENSUS = "\n".join(rows)

# ---- any() / require_all lists ----
any_rows = ["| rel | orch_any | any_gen | require_all |", "|---|---|---|---|"]
for r in census["all_files"]:
    if r["orch_any"] or r["any_gen"]:
        any_rows.append("| `%s` | %s | %s | %s |" % (
            r["rel"], fmt_list(r["orch_any"]), fmt_list(r["any_gen"]),
            fmt_list(r["require_all"])))
ANY_LIST = "\n".join(any_rows)

req_rows = ["| rel | require_all 行 | bytes | sha16 |", "|---|---|---|---|"]
for r in census["all_files"]:
    if r["require_all"]:
        req_rows.append("| `%s` | %s | %d | %s |" % (
            r["rel"], fmt_list(r["require_all"]), r["bytes"], r["sha256"][:16]))
REQ_LIST = "\n".join(req_rows)

# ---- pairwise similarity table with DEFINITE judgments ----
JUDGE = {
    "d27|d28": "跨模板线；仅 import/常量块与尾部 4 行块相同 ⇒ **不共享实现，确定**",
    "d27|d29": "跨模板线；无任何 ≥4 行共同块 ⇒ **不共享实现，确定**",
    "d27|d30": "跨模板线；与 d27|d29 数值全同 ⇒ **不共享实现，确定**",
    "d27|d25": "源头范式相似但 d25 无任何 `any()` ⇒ **非本族，确定**",
    "d27|d26": "`sections()` 27/29 行共同、ratio 0.9474；23 行最长连续块 ⇒ **同一模板线 A，确定**；方向 neither_subset ⇒ 谁抄谁 **unconfirmed**",
    "d28|d29": "共享 `requirements` 四元组骨架；`section_bodies()` 仅 5/30 共同（ratio 0.1695）⇒ **骨架同源、提取器为不同实现，确定**",
    "d28|d30": "与 d28|d29 数值全同 ⇒ **骨架同源、提取器为不同实现，确定**",
    "d28|d25": "无 ≥3 行共同块 ⇒ **非本族，确定**",
    "d28|d26": "仅 import/零散 4 行块 ⇒ **非本族，确定**",
    "d29|d30": "`section_bodies()` 29/29 逐行相同（identical=true）；14 处常量/词表差异、最长连续块 35 行 ⇒ **同一实现（仅数据不同），确定**；方向 neither_subset ⇒ 谁抄谁 **unconfirmed**",
    "d29|d25": "无 ≥4 行共同块 ⇒ **非本族，确定**",
    "d29|d26": "无 ≥4 行共同块 ⇒ **非本族，确定**",
    "d30|d25": "与 d29|d25 全同 ⇒ **非本族，确定**",
    "d30|d26": "与 d29|d26 全同 ⇒ **非本族，确定**",
    "d25|d26": "无 ≥3 行共同块，且 d25 无 `any()` ⇒ **非本族，确定**",
}
CFV_RATIO = {}
for pr in cfv_lineage["pairs"]:
    a = Path(pr["a"]).stem.replace("check_", "")
    b = Path(pr["b"]).stem.replace("check_", "")
    CFV_RATIO.setdefault((a, b), pr["difflib_ratio"])
pair_rows = ["| 对 | 共同行 | 仅 a / 仅 b | 行 Jaccard | difflib（撰写件） | difflib（复核件） | 确定判断 |",
             "|---|---|---|---|---|---|---|"]
for k, v in lineage["pairwise_6"].items():
    a, b = k.split("|")
    cr = CFV_RATIO.get((a, b), CFV_RATIO.get((b, a), "—"))
    label = k.replace("|", r"\|")
    judge = JUDGE[k].replace("d29|d30", r"d29\|d30").replace(
        "d28|d29", r"d28\|d29").replace("d28|d30", r"d28\|d30").replace(
        "d27|d28", r"d27\|d28").replace("d27|d29", r"d27\|d29").replace(
        "d27|d30", r"d27\|d30").replace("d29|d25", r"d29\|d25").replace(
        "d29|d26", r"d29\|d26")
    pair_rows.append("| %s | %d | %d / %d | %.4f | %.4f | %s | %s |" % (
        label, v["common_lines"], v["only_a"], v["only_b"], v["line_jaccard"],
        v["difflib_ratio"], ("%.4f" % cr) if isinstance(cr, float) else cr,
        judge))
PAIR_TABLE = "\n".join(pair_rows)

# ---- binding lines: freshly computed with hashlib in THIS run ----
BIND_RELS = [
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/d26_ruling_20261106/check_d26.py",
]
bind_lines = []
for rel in BIND_RELS:
    b = (ROOT / rel).read_bytes()
    bind_lines.append("被核对象 SHA256 = %s，字节数 = %d" %
                      (hashlib.sha256(b).hexdigest(), len(b)))
BINDING = "\n".join(bind_lines)

# ---- 40-instance SHA decomposition ----
sha_by_rel = {r["rel"]: r["sha256"] for r in census["all_files"]}
four_shas = {sha_by_rel[r] for r in (
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py")}
conf = [x if isinstance(x, str) else x.get("rel", "?") for x in detect["confirmed"]]
n_identical = sum(1 for r in conf if sha_by_rel.get(r) in four_shas)
n_variant = len(conf) - n_identical
n_sha_groups = len({sha_by_rel.get(r) for r in conf})

BODY = r"""# CHECK_FAMILY_LINEAGE.md — 全库 `check_*.py` 同族普查与模板来源追溯

写域：`lead/check_family_20261109/`。产出日期 2026-11-09。本件**只做普查与追溯**，不改任何脚本。
上游数据（同写域）：`_cf_full_census.md`（180 行逐件表）、`_cf_census_out.json`、`_cf_lineage_out.json`、`_cf_detect_out.json`、`_cf_REPORT.md`、`_cfv_census_out.json`、`_cfv_lineage_out.json`、`_cfv_*` 快照件。

---

## 1 目的与边界

**目的**：对全库 `check_*.py` 做逐个普查；给出「同族」的**代码级判据**（同一段写法 / 同一个函数模板，不是名字像）；追溯四件生产门禁的模板来源与相似度；评估 D-27 / D-28 / D-29 / D-30 四条裁决的连带影响；给修复方向。**只做普查与追溯**：本会话未修改、追加、覆盖任何既有脚本、自检件、台账或裁决书。

**铁律落地（本会话实跑/可查）**
- 零真机：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存（本会话命令登记见下，无任何进程类命令）。
- 零采样代码：未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析；本会话新建的唯一可执行文件是本件的生成器 `_cf_compose_lineage.py`，只做 `hashlib` + JSON 解析 + 文本拼装。
- 绝对只读：`lead/d27_ruling_20261106/`、`d28_`、`d29_`、`d30_`、全库其余 `check_*.py` 与自检脚本、`lead/check_masking_20261109/`、`lead/stale_pass_20261109/`、两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）一律未改。复核方 `_cfv_snapshot_before.json` / `_cfv_snapshot_after.json` 对 273 件保护文件实跑比对 `missing=[] added=[] changed=[]`（sha256/bytes/mtime_ns 全比）；本会话在其后亦未写入这些路径。
- 唯一写域 = `lead/check_family_20261109/`；不 commit、不 push（`git status --short | wc -l` 本会话基线 237 行，仅为只读观察）。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`（本会话实跑 `python -I -X utf8 -c` 读 bytes 后 `hashlib.sha256`，五值见 §6.2；`sha256sum` 交叉验证）。

**本会话实跑命令与输出（逐条可复核）**
| 命令 | 输出 |
|---|---|
| `find "D:/Project/ra2-campaign-forge" -type f -name "check_*.py" 2>/dev/null \| wc -l` | `173` |
| `python -I -X utf8 -c` 解析 `_cf_census_out.json` | `total_files=173`、`missing=[]`、`all_files` 173 条含完整 64 位 `sha256` |
| `python -I -X utf8 -c "…hashlib…"` 读 5 件 bytes | 5 行绑定值，见 §6.2（与题给【复核】`sha256Line` 逐字吻合） |
| `sha256sum lead/d27_ruling_20261106/check_d27.py lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py` | 两行同为 `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` |
| `sed -n '100p'` 上述两件 | 两行同为 `print(f"PASS: D-27 八项机械检查通过；裁决书引用 {count} 处")` |
| `grep -n "门禁.*exit=0\|exit=0.*门禁" lead/PENDING_DECISIONS.md` | 7 行：`:92 :105 :117 :129 :162 :186 :199` |
| `grep -c "D-27\|D-28\|D-29\|D-30" lead/GOAL_THREE_TARGETS_20261018.md` | `0` |
| `stat -c '%y\|%s\|%n'` 六件 d2* 门禁 + 10-02 模板件 | mtime 链见 §3.3 |
| `git log --oneline -- lead/d2[5-9]_ruling_20261106/check_*.py lead/d30_ruling_20261106/check_d30.py` | 无输出（历史空） |
| `git status --short --` 六个 `d2*_ruling_20261106/` 目录 | 六行全 `??`（未跟踪） |
| `grep -rln "for number, title, words, require_all in requirements" --include="*.py" . \| wc -l` | `38`（Python 拆分：29 件 `check_*.py` + 9 件非 `check_*.py` 的 `_w_dNN_[ABS].py`） |
| `grep -rln "require_all" --include="*.py" . \| wc -l` | `44`（本会话时点；普查件记 42 ⇒ 时点/口径差，如实记，见 §3.5） |
| `find lead/stale_pass_20261109/_sp_sandbox -name '_w_d*_*.py' \| wc -l` | `12` |
| `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_family_20261109/_cf_compose_lineage.py` | 生成本件（含 173 行逐件表、逐对相似度表、绑定行） |

**未跑**：本会话未做坏针哨兵注入实证，未重跑 `_d27/_d28/_d29/_d30_facts.py` 数值断言，未部署修复、未跑修复后回归；均标「未验」，见 §6.4。编排方 `ranCommands=47` 与复核方 `ranCommands=22` 系各自手工点算，本会话不复核也不重报自己的调用条数。

**清单边界**：173 件含 `.dsh-watch/`、`.tmp/`、`.zcode-watch/` 及 `out/re_work/**` 自嵌套树；`.git/` 内部与符号链接目标未纳入（复核方 `_cfv_checklist.txt` 同边界）。复核方两次 Python 全树 `rglob` 在 `out/re_work/work_chain/CONTINUE_20261003/…/snap_T3/…` 遇 `[WinError 1921]` 卡死并 `TaskStop`，改 `find` 清单绕开 —— 属复核方实跑事实，本会话未重跑该遍历。

---

## 2 全库普查

### 2.1 计数与口径

`find . -type f -name "check_*.py" | sort` → **173 件**（编排方【普查数据】实跑 25 件是其子集）。本会话实跑 `find … | wc -l` = 173，并解析 `_cf_census_out.json` 得 `total_files=173, missing=[]`。逐件 `rel / bytes / 完整 64 位 sha256 / lines / mtime` 见 §2.2 表；同数据亦在 `_cf_full_census.md:9-181`（sha16 版）与 `_cf_census_out.json:all_files[*].sha256`（全 64 位）。

### 2.2 ★ 逐件清单（173 件，全 64 位指纹）

@@FULL_CENSUS@@

### 2.3 含 `any()` 与 `require_all` 的清单

**含 `any()`（`orch_any` 或 `any_gen` 非空）= 53 件**（`_cf_census_out.json:summary.n_any_gen=53`、`n_orch_any=48`、`n_any_membership=53`、`n_any_word_or=40`）：

@@ANY_LIST@@

**含 `require_all` = 29 件**（`_cf_census_out.json:summary.n_require_all=29`、`n_requirements_assign=29`）：

@@REQ_LIST@@

**编排方 25 件子集核对**：`_cf_census_out.json:orchestrator_25_check[*]` 的 `bytes_match / sha16_match / any_match / req_match` 全 `true`（窄口径 `orch_any_line`：`_cf_census.py:55-59` 要求同一行有 `any(` + 两处 ` in ` + ` for `）。★ 但 `pass` 列自相矛盾：本会话实跑 `sha256sum` + `sed -n '100p'` 证明 `check_d27.py` 与 `_sp_sandbox/check_d27_baseline.py` 同 SHA256、同 `:100` f-string PASS 行，编排方 `pass` 一为 `[]` 一为 `[100]`（`_cf_census_out.json:orch_pass_contradictions`）。故本件不采用其 `pass` 列，改用 `pass_print = ^\s*print\(.*PASS`（`_cf_census.py:80-83`）。★ 复核方宽口径逐字段比对得 27 处不一致（`_cfv_census_out.json:orch_check.field_mismatches`，`any` 14 / `pass` 13），`bytes/sha16/require_all` 全吻合 ⇒ 这是**窄/宽口径差**，非数据矛盾，两种读法都列出。

### 2.4 同族风险数字（三种口径，均本会话实跑/实读）

| 口径 | 数字 | 来源 |
|---|---|---|
| 严格字面组合（`orch_any` 且 `print("PASS` 立即开头） | **28** | `_cf_census_out.json:summary.n_combo_orchany_passliteral` |
| 宽口径（`orch_any` 且 `pass_print`） | **46** | `summary.n_combo_orchany_passprint` |
| 复核方通用宽口径（`\bany\s*\(` + `^\s*print\(.*PASS`） | **54**，四件生产门禁全命中、`literal_screen_misses_confirmed=[]` | `_cfv_census_out.json:n_literal_any_plus_PASS` |
| AST 静态候选 | **40**（`n=173`，`suspect=3`） | `_cf_detect_out.json`；四件 `four` 全 `CONFIRMED` 且 P1–P4 全 `true` |
| 40 件按 SHA 去重 | **@@N_SHA_GROUPS@@** 个字节串；**@@N_IDENTICAL@@** 件与四件生产门禁字节完全相同、**@@N_VARIANT@@** 件为已注入哨兵的变体 | 本会话 `python -I -X utf8 -c` 分解 `confirmed` |
| 复核方独立判据 | `CONFIRMED 28 / SUSPECT 21 / NOT_FAMILY 122 / SUSPECT_ANTI_MASKING 2` | `_cfv_census_out.json:my_verdict_counts` |
| 文本判据（48 件候选内） | `CONFIRMED 37 / SUSPECT 2 / NOT_FAMILY 9` | `_cf_lineage_out.json:family_counts` |
| 173 件按 SHA 去重 | 134 个不同字节串、16 个重复组 | `_cfv_lineage_out.json:n_distinct_check_py` / `n_duplicate_groups` |

★ **「字面 `any()`+PASS 筛会漏掉 d28/d27」标 unconfirmed**（复核 verdict=`partial` 破口①）：该结论只在撰写件自定义窄口径（`_cf_census.py:55-59` 的 `orch_any_line` + `:80` 的 `print("PASS` 立即开头）下成立 —— d28 `check_d28.py:97` 是 `any(present)`（布尔列表 Name，非生成器）、d27 `check_d27.py:100` 是 f-string PASS；在通用宽口径下四件全命中（54 件、零漏判）。筛查仍必须用代码级判据（§4），但「漏判」叙事不作为确定结论。

★ **40 件表述须限缩**：40 件是 AST **静态结构命中**，其中 13 件是 `_cm_tmp` / `_cmv_tmp` / `_sp_sandbox` 里已注入坏针的副本（如 `d28x/a/b/check_d28_injected.py`、`_cmv_tmp/d27/v_b_kill_2/check_d27.py`），故「全库 40 件都带同一缺陷代码」**不成立**，只是同一函数模板的静态候选 —— 与撰写件自述「静态只给候选，确诊仍需动态哨兵注入」一致。

### 2.5 写法像但实为逐输入的区分（逐件确定判断）

| 件 | 代码级证据 | 确定判断 |
|---|---|---|
| `lead/d25_ruling_20261106/check_d25.py` | 本会话 `grep -n 'any('` → `NO_ANY_IN_D25`（0 命中）；`:58,:60` 单词检查 | **NOT_FAMILY**（确定）：无 `any()` 塌缩 |
| `lead/d26_ruling_20261106/check_d26.py` | `:85` `any("本次不授权" in body for body in …)`、`:87` `any("勘误" in body and "挂账" in body …)`、`:90` `any(bodies.get(…))` —— 三个 `any()` 都是跨 section body 的**存在性/非空**检查，非 k 词 OR | **NOT_FAMILY 于本族**（确定）；但 `PENDING:162` 记 exit=0、未注射实证 ⇒ 列 **SUSPECT / 未验**（`_cf_detect_out.json:suspect` 含此件）。复核方 `_cfv_census.py` 把它误判 `CONFIRMED`，撰写件判 SUSPECT 更准确 |
| `lead/b2b_candidate_review_20261106/check_semantic_review.py:330` | 本会话 `sed -n '326,332p'` 实读：`for p in passes: print(f"PASS {p}")` 在 `for` 内 | **NOT_FAMILY**（确定）：逐检查项可归因 |
| `lead/b2b_candidate_review2_20261106/check_semantic_review_r2.py:358` | 本会话 `sed -n '354,360p'` 实读：同样 `for p in passes: print(f"PASS {p}")` | **NOT_FAMILY**（确定） |
| `lead/stall_event_def_20261106/check_stall_def.py:244` | `sed -n '240,246p'` 实读：`for p_msg in passed_items: print(f"PASS: {p_msg}")` | **NOT_FAMILY**（确定） |
| `lead/early_trigger_feasibility_20261106/check_feasibility.py` | 本会话 `grep -n '\[PASS\]'` 命中 `:119,149,164,176,197,206,214,223,259,333`，逐项 `[PASS] 检查项 N` | **NOT_FAMILY**（确定） |
| `all()` 的用法边界 | `all(` 全库 61 件、`all` 生成器 28 件（`_cf_census_out.json:summary`）；本族四件里 `all()` 只出现在 `check_d29.py:83` / `check_d30.py:83` 的 `require_all=True` 分支和 `check_d28.py:97` 的 `all(present)` | **NOT_FAMILY 判据**（确定）：`all()` 本身不红（`CHECK_MASKING_INJECT.md:454`），粗计数不可当同族数 |
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` / `.py` | 本会话 `grep` 实读 `:35 NAIVE_FLOOR`、`:48 GOLDEN_POS`、`:59 GOLDEN_NEG`、`:99-104` 「扫描器自检（金样例 + 段落判据），失败即 EXIT=3」、`:161-162` `SCANNER-DEAD`、`:235` 下限打印 | **SUSPECT_ANTI_MASKING**（确定非确诊同族）：有金样例回归 + 下限 + 失能退出硬闸；本会话未注射实证 ⇒ 未验 |
| `lead/refsync_scope_20261109/_rs_carrier_scan.py` | 本会话 `grep`/`sed` 实读 `:165 min((line.find(n) …))`、`:194 --needle action="append"`、`:229 any(n in txt for n in a.needle)`、`:343 ok &= good`、`:346 SELF_TEST = PASS`、`:349 return 0 if ok else 1` | **异族同抽象**（按本件代码模板判据，确定）：CLI `--needle` + `min/argmin` 反向掩蔽 + 非 `check_*.py`；按抽象 k→1bit 判据可算同族（两种读法都列出，`STALE_PASS_INVENTORY.md:167` 记其 A+B 级） |

---

## 3 模板来源追溯

### 3.1 四件逐对相似度（撰写件 `_cf_lineage.py` 实跑 + 复核件 `_cfv_lineage.py` 交叉，本会话解析两 JSON）

规范化行 = 去空行/纯注释；Jaccard 为规范化行集合交/并；difflib 两件因归一化序列不同故数值不同，两列都列。**每行给确定判断，逐对给出确定判定，不作泛化推测**。

@@PAIR_TABLE@@

**函数体级相似度**（`_cf_lineage_out.json:function_identity`）：
- `sections()`：`d27|d26` 共同 27 行 / 29、28 行、`ratio=0.9474`、`identical=false` ⇒ **同一提取器模板，确定**。
- `section_bodies()`：`d29|d30` 共同 29/29、`ratio=1.0`、`identical=true` ⇒ **逐行同一实现，确定**；`d28|d29` 与 `d28|d30` 均 5/30、`ratio=0.1695` ⇒ **不同实现，确定**。
- 复核件 `_cfv_lineage_out.json:pairs[d29|d30]`：`direction_hint=neither_subset`、`jaccard_norm=0.75`、`difflib=0.9552`、`largest_block=35`、`shared_func_bodies[section_bodies].identical=true`；`d26|d27` 亦 `neither_subset`（J=0.575、difflib=0.7889、最长连续块 23）。全部 d2x 对 `direction_hint=neither_subset`（除字节相同的沙箱副本对）。

### 3.2 确定判断与 unconfirmed 边界

- **确定 A**：四件生产门禁属**同一「同族」**——共享同一函数模板：字面 k≥2 词 OR 表 → `any()` 压成 1 bit → 恰好一个聚合 `PASS` + `return 0` + section 正文提取器喂词测试。`_cf_detect_out.json:four` 四件 P1–P4 全 `true`；抽象式见 `CHECK_MASKING_INJECT.md:445-450`（待证 ∀i 有效、观测量只有 ∃i 命中、不保留 hits 下标）。
- **确定 B**：**不是一条逐字复制链，而是两条模板线 + 一个共同源头范式**。线 A = `d26 ↔ d27`（`sections()` 同源，全文件 J=0.5847 / difflib=0.738）；线 B = `d28 ↔ d29 ↔ d30`（`requirements` 四元组 + `require_all` 骨架；`d29|d30` 逐行同一实现；`d28` 自带 30 行 `section_bodies()`，与 d29/d30 的 29 行版只 5 行共同）。跨线 J ≤ 0.1676 ⇒ 共享的是函数模板，不是文件字节。
- **确定 C**：`d29|d30` 差异仅 14/14 行（词表/标题常量），最长连续共同块 35 行 ⇒ 二者是**同一实现**，确定；`d27|d28` 等跨线对无任何 ≥5 行共同块 ⇒ **不共享实现**，确定。
- ★ **unconfirmed（复核 verdict=`partial` 破口②）**：`_cf_REPORT.md:26-28,70` 的「mtime 19:33:47 < 21:57:57 ⇒ d30 抄 d29」「d27 抄 d26 的提取器」「d29 抄的是 d28 的四元组骨架」等**方向/作者**判断。证据：相似度是对称量、复核件全部 `direction_hint=neither_subset`；`_cf_lineage.py:40-56` 的 `pairwise()` 只算对称指标、无任何方向判据；本会话实跑 `git log` 五件全空、`git status` 六目录全 `??`，mtime 可被复制/改写。`_cf_REPORT.md:70` 自己也写「判不了历史作者归属与是否被改过」—— 一边判不了、一边用「抄」自相矛盾。**本件只写「两条模板线 + 共同函数模板」，不写谁抄谁**。要改判需 git 作者/提交链或不可篡改时间戳，本会话拿不到。

### 3.3 最早件（本会话 `stat -c '%y|%s|%n'` 实跑）

| 件 | mtime | bytes | 定位 |
|---|---|---|---|
| `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 2026-10-02 01:00:46 | 11843 | 形态相似但带反掩蔽硬闸 ⇒ 非确诊同族 |
| `lead/d25_ruling_20261106/check_d25.py` | 2026-11-06 14:41:54 | 2877 | 源头范式（格式门禁，无 `any()`） |
| `lead/d26_ruling_20261106/check_d26.py` | 2026-11-06 14:59:27 | 4245 | 源头范式（`sections()` + 八项格式检查） |
| **`lead/d27_ruling_20261106/check_d27.py`** | **2026-11-06 16:41:55** | **3764** | **同族原件中最早件**：首次引入 k 词 OR + `any()` |
| `lead/d28_ruling_20261106/check_d28.py` | 2026-11-06 18:42:26 | 4539 | 引入 `require_all` 四元组 |
| `lead/d29_ruling_20261106/check_d29.py` | 2026-11-06 19:33:47 | 3906 | 线 B 的 29 行 `section_bodies()` |
| `lead/d30_ruling_20261106/check_d30.py` | 2026-11-06 21:57:57 | 3926 | 与 d29 同一实现 |

全库最早 `check_*.py` 在 2026-09-26 `out/re_work/re_sprint/`（`_cf_lineage_out.json:mtime_first20` 前 12 件），无 `any()`+PASS 组合。`_sp_sandbox/check_d27_baseline.py` 与生产 d27 字节/指纹全同但 mtime 为 2026-11-09（沙箱复制时点），不作为最早件依据。

### 3.4 原始写法意图（逐行直读）

`check_d27.py:1` / `check_d26.py:1` docstring 为 `"Read-only D-27 gate …"` / `"Read-only D-26 gate …"`；`check_d26.py:21-48` `sections()` 收二级标题正文，`:72-97` 检查 verdict 行、7 个必需小节、`本次不授权`、`勘误`+`挂账`（AND）、`未背书` 非空、引用 ≥8、`selfBias` ⇒ **意图是「裁决书格式/机械合规」，不是验事实**（`STALE_PASS_INVENTORY.md:196` 同判）。

缺陷进入点（确定）：`check_d27.py:81-88` 首次把「正文须含 X」泛化成「正文须含 X 或 Y」，用 3 元组 `("外推","卡顿不存在")` + `any(keyword in body …)`，并沿用「逐项 `errors.append` + 末尾一行 `PASS`」汇总；`check_d28.py:89-99` 再引入 `requirements` 四元组 + `require_all` 旗标把 OR/AND 并进同一循环（`:97` `any(present)`）；`check_d29.py:75-89` / `check_d30.py:75-89` 换成双层 `matches` 列表 + `any(matches)` 但**逐行同构**。三者共同点：k 个观测压成 1 bit，不保留命中下标。

### 3.5 是否扩散到别处（确定 + 连带）

扩散链（本会话 grep / find 实跑）：4 件生产门禁 → 台账 `PENDING_DECISIONS.md:92/105/117/129` → D-27→D-28→D-29→D-30 引用链（`PENDING:113,125`、`RULING_D30.md:6`）→ 审计沙箱/注入副本（`_cm_tmp` 22、`_cmv_tmp` 5、`_sp_sandbox` 9 落在 40 件口径内）→ 12 件非 `check_*.py` 的 `_w_dNN_[ABS].py`（`find … | wc -l` = 12；其中 9 件带四元组，如 `_w_d29_A.py:75-88` 仍整段 OR 塌缩 + `:105-106` 单行 PASS）→ 交付件 `REFSYNC_SCOPE_FIX.md:251/252/253` 三行（属异族同抽象的 `_rs_carrier_scan.py`）。

- `grep -rln "for number, title, words, require_all in requirements" --include="*.py" . | wc -l` → **38**；本会话 Python 拆分 = **29 件 `check_*.py` + 9 件非 `check_*.py`**（d28x/d29/d30 的 `_w_dNN_A/B/S.py`）。★ 撰写件写「12 件非 `check_*.py` 的 `_w_dNN_[ABS].py` 注入副本」带四元组 —— 12 是副本总数，带四元组的只有 9 件（3 件 `_w_d27_*.py` 源自 3 元组 d27），此处按实跑更正。
- `grep -rln "require_all" --include="*.py" . | wc -l` → **44**（本会话时点，含写域内 4 件 `_cf*/_cfv*` 生成脚本、`_cm_inject.py`、`_mev_final.py` 及 12 件 `_w_dNN_*.py`）；普查件记 42 ⇒ 撰写期后新增文件造成的**时点差**，如实记，不判孰错。
- ★ 连带影响（确定）：按字面批量替换会连带改动证据生产副本，必须先分离审计沙箱与生产门禁；`REFSYNC_SCOPE_FIX.md:251/252/253` 三行 PASS 失效会推翻 `:243` 的 **R6 负控自检**承诺与 `:273`（4 件）、`:274`（6 件）、`:276`（主答案 4 件）、`:282-286` 六行件数表（`STALE_PASS_INVENTORY.md:167`），但**不波及任何 D-27..D-30 裁决**。

---

## 4 代码级判据

### 4.1 形式判据（同一段写法 / 同一个函数模板，不是名字像）

抽象语义（`CHECK_MASKING_INJECT.md:445-450`）：待证 `∀i 输入_i 有效`，观测量只有 `∃i 命中`，`PASS` 把 k 个输入压成 1 bit 且不保留 `hits=[命中下标]` ⇒ 逐输入可归因 = 否。`DISTINGUISHABLE_PASS = AND_k(真实逐输入自检)`（`:450`）。落到 AST/源码的四条判据：

| 判据 | 代码级定义 | 四件落点（本会话 Read 直读） |
|---|---|---|
| **F1** | 字面元组/列表表的行含 k≥2 个字符串词，且该行走 OR 分支（`require_all=False` 显式旗标，或 d27 式无旗标的 3 元组） | `check_d27.py:81-85`（`("外推","卡顿不存在")`）；`check_d28.py:89-93`（`("历史数字","1681"), False`）；`check_d29.py:75-79`（`("互斥","前提"), False`）；`check_d30.py:75-79`（`("93.98","误报率"), False`） |
| **F2** | `any(...)` 把该 k 词 OR 塌缩成单个布尔：生成器成员测试 / 布尔列表绑定后 `any(Name)` / `any(matches)` | `check_d27.py:86-87` `any(keyword in body … for keyword in keywords)`；`check_d28.py:96-97` `present=[word in body …]` + `any(present)`；`check_d29.py:82-87` / `check_d30.py:82-87` `matches=[all(…) if require_all else any(…) …]` + `if not any(matches)` |
| **F3** | 恰好一个**聚合** `PASS` print（不在 `for` 内）+ `return 0`/退出；无逐词 `HIT/DEAD` / `PER_NEEDLE` 输出 | `check_d27.py:100-101` 单行 f-string PASS + `return 0`；`check_d28.py:115-116`；`check_d29.py:105-106` `print("PASS")`；`check_d30.py:105-106` |
| **F4** | section 正文提取器把 Markdown 小节喂给词测试 | `check_d27.py:21-50 sections()`；`check_d28.py:21-50 section_bodies()`；`check_d29.py:18-46` / `check_d30.py:18-46 section_bodies()`（二者逐行全同） |

`grep` 级 4 步判据见 `CHECK_MASKING_INJECT.md:452-459`；本件采用的判据比「名字含 check_」「同目录 d2*」更严：逐输入打印件（§2.5）F3 为假，不归族。

### 4.2 确诊与存疑清单（确定）

- **CONFIRMED（生产门禁，4 件）**：`check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py`。`_cf_detect_out.json:four` 逐件 `P1–P4=true`；四件「坏针仍 PASS」的既有实证见 `STALE_PASS_INVENTORY.md:126-131`（4 行逐件列 OR 词表与 `check_dNN.py` 行号）与 `CHECK_MASKING_INJECT.md:183-365` —— **本会话未独立复现注入，标未验**（§6.4①）。
- **静态候选 40 件**：`_cf_detect_out.json:confirmed`，含 4 原件 + 27 件字节相同副本 + 13 件注入变体；按 SHA 去重 11 个字节串。★ 这只是 F1–F4 静态命中，**不等于 40 件确诊**。
- **SUSPECT 3 件**（`_cf_detect_out.json:suspect`）：`check_d26.py`（`PENDING:162` 记 exit=0，`STALE_PASS_INVENTORY.md:133,385` 列 C 级未注射）、`out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` 与 `.template.py`（带 GOLDEN/NAIVE_FLOOR/EXIT=3 反掩蔽硬闸）。三者本会话均未做哨兵注入 ⇒ **未验**，不冒充确诊或排除。
- **NOT_FAMILY 130 件**（AST 口径 173−40−3）；复核方独立口径为 `NOT_FAMILY 122 / SUSPECT 21 / CONFIRMED 28 / SUSPECT_ANTI_MASKING 2`。两套口径差来自 F3/F4 严格度与 d28 沙箱副本，如实并列。

### 4.3 自动化检测设计（已实现 + 必须补强）

已实现：`lead/check_family_20261109/_cf_detect.py`，`ast.parse` 一次跑完 173 件（输出 `_cf_detect_out.json`）。P1 抓「元组表行含 ≥2 字符串 + False 旗标或 3 元组」；P2 抓 `any(GeneratorExp/ListComp)` 成员测试、`any(Name)` 与布尔列表绑定；P3 抓聚合 PASS print 与 `for` 内逐项打印、并用 `ast.Module(body=[n], type_ignores=[])` 包 print 再 `ast.walk` 取 `JoinedStr` 常量（`:104-107`，修掉了首版把 d27 f-string PASS 漏判成假阴性）。

★ **「检测器纯代码级 / 直接实现确诊」标 unconfirmed**（复核 verdict=`partial` 破口⑤）：
1. `_cf_detect.py:54-55` 的 P4 是**名字级** —— `n.name in ("sections","section_bodies","section_body","exact_h2_body") or "section" in n.name`。复核方实跑量化 `P4_by_name_hits=48`、`P4_name_AND_body_hits=41`，7 件只有名字无正文结构（`check_b2b.py` 的 `section`、`check_b2_preaudit.py` 的 `section_lines_span`）⇒ 函数改名即漏判，不满足铁律「同一段写法/同一函数模板」的纯代码级要求。应改为 AST 结构判据：函数体含 `splitlines()` + heading 正则收集 + 返回 bodies 映射。
2. 检测器把**已注入哨兵的副本**也判 `CONFIRMED` ⇒ 静态结构 ≠ 确诊。要「直接实现确诊」须补：动态坏针注入 + `DISTINGUISHABLE_PASS = AND_k(REAL per-input self-test)`（`MASKING_EFFECT_AUDIT.md:176`）、每根输入单独跑并绑定脚本 SHA256 + 输入语料指纹（`STALE_PASS_INVENTORY.md:251-268` 第 4 条）、`require_all=True` 的 AND 项排除在 `AND_k` 之外（`CHECK_MASKING_INJECT.md:539-540`，`and_kill_1` 实证 `EXIT=1`）。
3. 复核方 `_cfv_census.py` 把 `check_d26.py` 误判 `CONFIRMED`（其三个 `any()` 是跨 body 存在性检查），说明 F2 还需区分「k 词 OR」与「跨样本存在性」—— 撰写件 `_cf_detect.py` 判其为 SUSPECT 更准确。

### 4.4 其它值得普查的族（按写法，不按名字）

| 族 | 代码级锚点 | 状态 |
|---|---|---|
| `min()/argmin` 反向掩蔽 + `ok &= good` + 单 `SELF_TEST` | `_rs_carrier_scan.py:165,229,343,346,349` | 异族同抽象；A+B 级（`STALE_PASS_INVENTORY.md:167`），`REFSYNC_SCOPE_FIX.md:251/252/253` 三行依赖 |
| `0==0` 空真 PASS / `verify_hooks` 假绿 | `GOAL_THREE_TARGETS_20261018.md:261,262,327` | D 级、异族、已自认（`STALE_PASS_INVENTORY.md:176`） |
| CWD 相对路径使门禁结果随 `cwd` 漂移 | `check_d27.py:8` `DIRECTORY = Path("lead/d27_ruling_20261106")` vs `check_d29.py:50` `Path(__file__).resolve().parent` vs `check_d28.py:54-55` `parents[2]` | 三种路径基准，`STALE_PASS_INVENTORY.md:251-268` 第 1 条「路径坑」 |
| PASS 不绑定输入语料指纹致计数漂移 | 627 → 655 → 662（`STALE_PASS_INVENTORY.md:167`、`CHECK_MASKING_INJECT.md:392`） | 未验（当时三个数字） |
| `require_all=True` 的 AND 项逐词不可归因 | `check_d29.py:83` / `check_d30.py:83`；`STALE_PASS_INVENTORY.md:389` | 未验 |
| 台账裸 `exit=0` 无状态字段 / 制度根因 | `STALE_PASS_INVENTORY.md:348-367`（8 条） | 制度层，非代码族 |

---

## 5 连带影响

### 5.1 四条裁决的台账登记是否写 `exit=0`（本会话实跑）

`grep -n "门禁.*exit=0\|exit=0.*门禁" lead/PENDING_DECISIONS.md` → **7 行**：

| 行 | 内容 |
|---|---|
| `:92` | D-30：门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS） |
| `:105` | D-29：`check_d29.py` 实跑 **exit=0** |
| `:117` | D-28：`check_d28.py` 实跑 **exit=0** |
| `:129` | D-27：`check_d27.py` 实跑 **exit=0**（含「71 处引用」） |
| `:162` | D-26：`check_d26.py` 实跑 **exit=0** |
| `:186` | D-25：`check_d25.py` 实跑 **exit=0** |
| `:199` | N-1：门禁 **exit=0** |

**确定判断：D-27 / D-28 / D-29 / D-30 四条全部写了 `exit=0`**。`grep -c "D-27\|D-28\|D-29\|D-30" lead/GOAL_THREE_TARGETS_20261018.md` → **`0`**（GOAL 台账零命中）。

### 5.2 实质是否依赖失效 PASS 的独立判断（确定 + 限缩）

**定谳行**（本会话 `grep -n '^main:\|^q1:\|^q2:'` 实跑）：`RULING_D27.md:6 main: B`、`RULING_D28.md:4 q1: A` / `:5 q2: 丁`、`RULING_D29.md:4 q1: 丁`、`RULING_D30.md:4 q1: 戊` —— **零引用自身 `check_dNN.py` 的 PASS**。

**逐字否认句**（本会话 `grep -n "门禁\|exit\|PASS\|退出码"` 实跑）：`RULING_D27.md:3,36,58,69,73,75,77`；`RULING_D28.md:9,62,72,78,80`；`RULING_D29.md:55,67,69,71`；`RULING_D30.md:62,76`。典型：`RULING_D30.md:76`「不把原探针、`check_feasibility.py` 或原门禁计为通过；后三者本次未运行」；`RULING_D28.md:78`「未运行核证脚本、门禁、历史测试、探针或统计重算」；`RULING_D29.md:71`「未运行原探针、门禁、历史语料重算…不记通过」；`RULING_D27.md:75`「退出码 0 由题给 F1 提供，本阶段未重跑」。

**数值来源**：`RULING_D29.md:14` 记本阶段实跑 `_d29_facts.py` 退出码 0、`pureLogicalCounterexampleMs` 六项 true；`RULING_D30.md:76` 记 `_d30_facts.py` 输出 `All numeric assertions passed` / `corpus {files:104, samples:1125992}`；`RULING_D27.md:75` 的数值来自题给 F1。本会话**未重跑**这些数值断言 ⇒ 只判依赖结构，不判结论真值。

**确定判断**：四条裁决的**实质结论确定不依赖自身失效 PASS**（依赖结构判定，无一条反例）。失效的是台账把「裁决书 + FACTCHECK + 门禁 `exit=0`」并列为「已验证」交付包的**证据资格**（`STALE_PASS_INVENTORY.md:213`；`PENDING:90-101/103-113/127-158`）。最接近的形式数字是 `PENDING:129` 的「71 处引用」——由 `check_d27.py:100` 的 gate 产出（`STALE_PASS_INVENTORY.md:155`），本会话未独立重算该 regex ⇒ **未验**。

★ **「零次正面引用」标 unconfirmed**（复核 verdict=`partial` 破口③）：`RULING_D28.md:22` **正面引用** F5「独立核证阶段候选机械门禁 9/9、D-13b 机械门禁 8/8 通过」及 `check_candidate.py:195,:228`、`check_d13b_design_20261106/check_d13b.py:202`；`FACTCHECK.md:31-40` 明载两件他件门禁 `exit=0` 输出 `ALL 9 GATES PASSED! EXIT=0` 与 `[RESULT] PASS — 全部 8 项检查通过（exit 0）`。故撰写件的「对 `check_dNN.py` / PASS / `exit=0` 零次正面引用」不成立。本件**限缩**为：「对**自身四件同族门禁**零正面引用；D-28 有他件门禁的正面引用并明确限缩为题给输入、不记本阶段亲跑通过（`RULING_D28.md:9,72,78`）」。那两件他件门禁是否也失效，本会话**未验**；`RULING_D28.md:13`「这是补齐既定下一门，不是签候选通过」⇒ 不构成对 5.2 结论的推翻。

### 5.3 是否波及其它裁决（确定判断）

- **A 级确诊仅 D-27..D-30 四条**（`STALE_PASS_INVENTORY.md:126-131` 逐件列 OR 词表与源码行号）。
- **C 级其它裁决**：D-26（`PENDING:162`）、D-25（`:186`）、N-1（`:199`，无可复跑脚本）—— 未注射实证 ⇒ **未验**，不冒充确诊或排除（`STALE_PASS_INVENTORY.md:385,390`）。
- **非裁决波及**：`REFSYNC_SCOPE_FIX.md:251/252/253`（A+B 级）与 `:273/:274/:276/:282-286` 六行计数（`:167`）；`GOAL:261/262/327` verify_hooks 假绿（D 级、异族、已自认）。
- **形式引用链**：D-28 是 D-29 / D-30 的上游（`PENDING:113,125`；`RULING_D30.md:6`），故 `PENDING` 的形式链须四件一并补注（`STALE_PASS_INVENTORY.md:176`）。
- **无一条实质依赖门禁 ⇒ 无实质反例**；代价集中在证据资格与台账加注，不在定谳。

---

## 6 复核回件、结论与未验项

### 6.1 复核 verdict 如实记

**`verdict = partial`（如实记，不修饰）**。复核方自报 `ranCommands=22`；撰写方 `ranCommands=47` 系手工点算，本会话无法复核、也不重报自己的调用条数。**按交付要求，`partial` ⇒ 相关判断标 `unconfirmed`**：

| # | 撰写件主张 | 复核结论 | 本件标记 |
|---|---|---|---|
| ① | 「字面 `any()`+PASS 筛会漏掉 d28/d27，已用 AST 补上」 | 通用宽口径 54 件四件全命中、零漏判；28/46 来自 `_cf_census.py:55-59,80` 的自定义窄口径 | **unconfirmed** |
| ② | 「d30 抄 d29」「d27 抄 d26」「d29 抄 d28」方向链 | 全部 `direction_hint=neither_subset`；`git log` 空、六目录全 `??`；mtime 可改写 | **unconfirmed**（只保留「两条模板线 + 共同函数模板」） |
| ③ | 检测器「纯代码级」「直接实现确诊」 | `_cf_detect.py:54-55` P4 名字级（48/41 差 7 件）；静态结构 ≠ 确诊；注入副本判 CONFIRMED | **unconfirmed** |
| ④ | 「对 PASS/exit=0 零次正面引用」 | `RULING_D28.md:22` + `FACTCHECK.md:31-40` 正面引用他件门禁 exit=0 | **unconfirmed**（已限缩为「自身四件」） |

**可确认四项**（复核方明列）：173 件普查、四件生产门禁代码级同族、四份裁决实质不依赖自身失效 PASS、未越界。复核方另如实报告：`check_semantic_review.py:330` / `_r2.py:358` 未直读（未验）—— **本会话已用 `sed -n` 直读该两行，见 §2.5，故该项在本件为已验**；复核方 `_cfv_census.py` 误判 `check_d26.py` 为 CONFIRMED，本件按撰写件判 SUSPECT（见 §2.5）。

### 6.2 ★ 复核回件绑定行（本会话 `python -I -X utf8 -c` 读 bytes 后 `hashlib.sha256` 实算）

@@BINDING@@

依序对应：`lead/d27_ruling_20261106/check_d27.py`、`lead/d28_ruling_20261106/check_d28.py`、`lead/d29_ruling_20261106/check_d29.py`、`lead/d30_ruling_20261106/check_d30.py`、`lead/d26_ruling_20261106/check_d26.py`（母本范式）。本会话 `sha256sum` 交叉验证前四件及 `_sp_sandbox/check_d27_baseline.py` 同值；五值逐字吻合题给【复核】`sha256Line`。

### 6.3 结论

**① 同族总数**（三种口径，均本会话实跑/实读，逐件给确定判定）：
- 按「有台账登记、覆盖裁决的生产门禁」= **4 件**（`check_d27/d28/d29/d30.py`），去重后 **3 套代码模板**（d27 三元组线、d28 四元组+30 行提取器线、d29/d30 四元组+29 行提取器线）。**确定**：四件同族，F1–F4 全中。
- 按「全库带该模板的 `check_*.py` 静态实例」= **40 件**（`_cf_detect_out.json`），按 SHA 去重 **@@N_SHA_GROUPS@@** 个字节串；其中 **@@N_IDENTICAL@@** 件与四件生产门禁字节完全相同、**@@N_VARIANT@@** 件为已注入哨兵变体 ⇒ **「40 件全带同一缺陷」标 unconfirmed**，只作静态候选。另有 12 件非 `check_*.py` 的 `_w_dNN_[ABS].py` 副本带同一 `requirements` 模板（其中 9 件带四元组）。
- 复核方独立口径 `CONFIRMED 28 / SUSPECT 21 / NOT_FAMILY 122 / SUSPECT_ANTI_MASKING 2`；文本判据 `37/2/9`。确定判断：**确诊生产门禁 4 件；SUSPECT 3 件未验；逐输入打印件确定非本族**。

**② 来源追溯结论（确定）**：不是一条逐字复制链，而是**两条模板线 + 一个共同源头范式**。源头 = 2026-11-06 14:41:54 的 `check_d25.py` 与 14:59:27 的 `check_d26.py`「只读机械格式门禁」意图（`check_d26.py:21-48,72-97`）；线 A `d26↔d27`（`sections()` 27/29 共同、ratio 0.9474，全文件 J=0.5847），线 B `d28↔d29↔d30`（四元组骨架，`d29|d30` J=0.75、`section_bodies()` 29/29 逐行全同，`d28` 提取器仅 5/30 共同）；跨线 J≤0.1676。四件共享的是「格式门禁 + k 词 OR + `any()` → 1 bit + 单行 PASS」**函数模板**。**同族原件中最早件 = `check_d27.py`（2026-11-06 16:41:55）**；更早的 10-02 `check_fileoffset_axiom.template.py` 带反掩蔽硬闸，确定非确诊同族；全库最早 `check_*.py` 在 2026-09-26 且无 `any()`+PASS 组合。★ **方向/作者 unconfirmed**（§3.2）。

**③ 逐件改还是统一外壳（确定）**：**统一甲' 外部外壳为主，不逐件改源码**。依据：四件在绝对只读域且 `PENDING:112,124` 明记「不改门禁脚本」；`CHECK_MASKING_INJECT.md:522-534,634` 证明只有甲'（逐输入独立跑自检 + `AND_k` + 坏针注入）通吃四件且被审脚本 **0 行改动**，逐件内嵌需动 3–4 处约 **55 行**（`:634-642`）并破坏只读铁律。但**适配器不能一行通吃**（`:535-540`）：scanner 是 CLI `--needle`（`_rs_carrier_scan.py:194`），三 gate 是源码硬编码字面量且无 CLI ⇒ 走沙箱副本；`d29/d30` 的 `require_all=True` 项必须排除在 `AND_k` 外（`:539-540`，`and_kill_1` 实证 `EXIT=1`）；路径基准三种（`check_d27.py:8` CWD 相对 / `check_d29.py:50` `__file__.parent` / `check_d28.py:54-55` `parents[2]`）。且不能只靠现成外壳：`_sp_andk.py` 是 hardcode 12 副本的**演示外壳、未部署**（`STALE_PASS_INVENTORY.md:251-268`，`_sp_andk.py:27-42` 的 `AND_k(over 2 real per-word runs)`）；`_cm_AUDIT.md` 旧模板套 d29 实测 `BAD_NEEDLE_CAUGHT=False`（`CHECK_MASKING_INJECT.md:544-565`），须用修正版（`:570-628`，作者实跑 `TEMPLATE_EXIT=0`）。落地 = **统一外壳 + 逐件适配器 + 逐件 `hashlib` 指纹绑定 + 台账 7 处就地加注**（`PENDING:92/105/117/129` 与 `REFSYNC_SCOPE_FIX.md:251/252/253`）。★ 本会话**未部署、未跑修复后回归**（§6.4④）。

**④ 判不了什么（确定列出）**：四条裁决实质真值；git 历史作者/复制方向/是否被改过；`d25`/`d26`/N-1 与 10-02 两件 SUSPECT 是否真掩蔽；`require_all=True` 逐词可归因；编排方 `pass` 列真实口径与 `ranCommands=47`；`.git/` 内部与符号链接目标；`PENDING:129`「71 处引用」独立重算；D-28 F5 引用的两件他件门禁是否失效；`_rs_carrier_scan.py` 是否算同族（随判据严格度，见 §2.5 两种读法）。

### 6.4 未验项（逐条标「未验」，不补造）

1. **未验**：本会话坏针哨兵注入实证。四件「坏针仍 PASS」引自 `CHECK_MASKING_INJECT.md:183-365` 与 `STALE_PASS_INVENTORY.md:126-131` 的既有实跑，未独立复现；故 `_cf_detect.py` 的 40 件只算静态候选。
2. **未验**：`_d27_facts.py` / `_d28_facts.py` / `_d29_facts.py` / `_d30_facts.py` 数值断言重跑 ⇒ §5.2 只判「实质依赖结构」，不判结论真值。
3. **未验**：`check_d25.py` / `check_d26.py` / N-1 门禁与 10-02 两件 `check_fileoffset_axiom*.py` 的注射实证（`STALE_PASS_INVENTORY.md:385-386` 列 C 级）。
4. **未验**：修复部署与修复后回归（`STALE_PASS_INVENTORY.md:388`；`CHECK_MASKING_INJECT.md:620-628` 自认只做演示外壳）。
5. **未验**：git 历史全空 + 六目录全 `??` ⇒ 作者身份、复制方向、历史是否被改过（`STALE_PASS_INVENTORY.md:390`）。
6. **未验**：`RULING_D28.md:22` / `FACTCHECK.md:31-40` 引用的 `check_candidate.py`、`check_d13b.py` 两件他件门禁是否也失效。
7. **未验**：`require_all=True` 的 AND 项是否有逐词可归因问题（`STALE_PASS_INVENTORY.md:389`）。
8. **未验**：`REFSYNC_SCOPE_FIX.md:251` 当时三个数字（语料已漂移 627→655→662，`STALE_PASS_INVENTORY.md:167,387`）；`PENDING:129`「71 处引用」独立重算（`:155`）。
9. **未验**：`.git/` 内部与符号链接目标（173 清单边界）；编排方 `pass` 列真实口径与两份 `ranCommands` 手工点算。
10. **未验**：复核方两次 Python 全树 `rglob` 的 `[WinError 1921]` 超限路径内容 —— 本会话未重跑该遍历，只采用 `find` 清单（`_cfv_checklist.txt`）。

---

**只做普查与追溯**：本件未改任何既有脚本、自检件、台账或裁决书；未 commit / push；零真机、零采样代码。新增文件仅在 `lead/check_family_20261109/`（本件及其生成器 `_cf_compose_lineage.py`）。题给【普查结论】的 `severity=high`、四件生产门禁同族、`PENDING` 四行 `exit=0` 证据资格失效，本件均予确认；题给【复核】的 `verdict=partial` 及四处破口，本件如实登记并将相关判断标为 `unconfirmed`。
"""

BODY = (BODY
        .replace("@@FULL_CENSUS@@", FULL_CENSUS)
        .replace("@@ANY_LIST@@", ANY_LIST)
        .replace("@@REQ_LIST@@", REQ_LIST)
        .replace("@@PAIR_TABLE@@", PAIR_TABLE)
        .replace("@@BINDING@@", BINDING)
        .replace("@@N_SHA_GROUPS@@", str(n_sha_groups))
        .replace("@@N_IDENTICAL@@", str(n_identical))
        .replace("@@N_VARIANT@@", str(n_variant)))

assert "@@" not in BODY, "unreplaced placeholder"
OUT.write_text(BODY, encoding="utf-8")
print("WROTE", OUT)
print("bytes", len(BODY.encode("utf-8")), "lines", BODY.count("\n") + 1)
print("census rows", len(census["all_files"]), "any rows", len(any_rows) - 2,
      "require_all rows", len(req_rows) - 2, "pair rows", len(pair_rows) - 2)
print("bind lines", len(bind_lines))

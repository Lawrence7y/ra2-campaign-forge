# 门禁主件显式命名改造（GLM 独立重扫轮）——36 处位点 / 模板 / 回归 / 欠账

- 唯一写域：`lead/gate_doc_name_fix_20261109/`；本件前缀 `_dn_glm_*`；不 commit、不 push。
- 纪律：零真机、零采样代码、无 hook/内存解析；`.zcode/workflow-runs/*.mjs` 与 `lead/` 历史写域**只读**；未改任何历史 payload。
- 被核对象（编排方八件指纹，本会话 `hashlib` 实算 8/8 相符；命令见 §7）：
  被核对象 SHA256 = 302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c，字节数 = 31692
  被核对象 SHA256 = 8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc，字节数 = 23441
  被核对象 SHA256 = 54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee，字节数 = 2850
  被核对象 SHA256 = c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94，字节数 = 611043
  被核对象 SHA256 = e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52，字节数 = 180256
  被核对象 SHA256 = 151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587，字节数 = 5717
  被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
  被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

---

## 1 第一步：独立重扫复核（不采信编排方数字）

实跑命令（本会话）：
```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_glm_rescan.py
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_glm_sites.py
```
脚本写法（`_dn_glm_rescan.py:1-140`）：单层 `os.listdir` `.zcode/workflow-runs`；对每个 `.mjs` 用 `json.JSONDecoder().raw_decode` 解 `export const payload = ` 得 `lowered`；精确切出 `const GATE_CODE = [ ... ].join(` 代码块，**只在块内**匹配 `DOC=max(cands,key=lambda p:p.stat().st_size)`；另统计整文件字面命中、写域、任务书 `const DOC=`、显式命名门禁。全程 stat/read，无递归 walk、无子进程、无真机。

输出（`_dn_glm_rescan_out.json`）：
```
scanned_files_total = 224, mjs_files = 223, payload_parsed = 223, has_gate_code = 85
gate_defect_files = 36, gate_defect_total_hits = 36, gate_defect_domains = 32
file_level_defect_files = 38
file_level_only_not_in_gate = [dwfrun-3ca3ee7b…, dwfrun-bdff6762…]
safe_explicit_files = 49 (Gen-1 34 / Gen-3 15), safe_in_defect_set = []
defect_rows_gate_has_cands = 34, defect_rows_const_doc = 33
defect_rows_no_const_doc = [13448f03…, 616f12ea…, 830e57b2…]   # 3 个 ledger_appendix run
```

**(a) 实际几处 DOC=max？与 36 是否一致？**
- 按「GATE_CODE 块内」口径：**36 个 payload、36 处、36/36 各 1 处**，与任务名的 36 一致。
- 编排方派发清单含 38 行（`siteCount:38`），其中 `3ca3ee7b`、`bdff6762` 两行**不是门禁位点**：`_dn_glm_sites.py` 实读二者 `gate_expected = GATE_DOC_NAME_FIX.md`、`gate_has_docmax_any=false`，其 `DOC=max` 字面只出现在 lowered 的任务书【背景】引用文本「其中 36 处用 DOC=max(...) 挑交付件」。集合比对 `mine_minus_orch=[]`、`orch_minus_mine=[]`、`identical=true`（`_dn_glm_sites_out.json` 的 `set_comparison`）——即除去 2 条引用噪音后，我的 36 与编排方 36 完全相同。
- 整文件字面命中 38 个文件；按门禁块口径 36。差异原因已实证，非漏扫。

**(b) 分布在多少个写域？**
**32 个历史写域**。重复域：`ledger_appendix_20261108`×3、`c07_slot_20261109`×2、`s604_script_gap_20261109`×2；其余 29 域各 ×1（`_dn_glm_rescan_out.json` 的 `domains`，32 键）。

**(c) 有没有已经用显式命名的（安全实例）？**
**有，49 个，0 个在缺陷集合内**（`safe_in_defect_set=[]`）：
- Gen-1 `doc=root/'<主件>.md'` + `if not doc.is_file(): P.append('交付件缺失')`：**34 个**。抽样亲读 `_dn_glm_sites_out.json` 的 `safe_sample`：`dwfrun-00973159…`（A_REDUCED_FORM.md）、`dwfrun-01a1190d…`（N1_R2_ACCEPTANCE.md）、`dwfrun-f8edc8ba…`（RULING_DIRECTION.md）、`dwfrun-fda7c34e…`（R2_BREAKPOINTS_CLOSURE.md）。
- Gen-3 `expected=wd/'<主件>.md'` + `主交付件未按约定命名 …`：**15 个**。抽样：`dwfrun-04af551c…`（S604_REFSYNC_DRAFT.md）、`dwfrun-f82f9299…`（S604_REFSYNC_FULL.md）；任务自身两发 `3ca3ee7b`/`bdff6762` 也在此形态。
- 结论：方案 A 不是新发明，库内已有 49 发可跑先例；缺陷是「一段窗口期换成了 max 猜大」，不是「做不到显式命名」。

### 1.1 缺陷段的精确形态（实测 5 种，不是 1 种）

本会话内联提取命令（`python -I -X utf8 - <<'PY' …`，输出见 §7 记录）：36 处选择段**统一 5 行**，但初始化行与 `cands` 行有变体：

| 形态 | 文件数 | 代表 | 说明 |
|--:|--:|:--|:--|
| A：`P=[];NB=0;DOC=None;B=0` + 标准 `cands=sorted(wd.glob('*.md'))` | 24 | `15585c14…` | 主流 |
| B：`P=[];B=[];NB=0;DOC=None` + 标准 cands | 7 | `13448f03…` | `B` 是 **list**，`print` 用 `len(B)` |
| C：`P=[];NB=0;DOC=None;B=0;FAKE=0` + 标准 cands | 3 | `24bda605…` | 另有 `FAKE` 计数 |
| D：`cands=sorted([p for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')])` | 1 | `af6f3c87…` | 名字前缀过滤 |
| E：`cands=sorted([p for p in wd.glob('*.md') if p.name.startswith('GATE_FALSE_POSITIVE')])` | 1 | `fed3c2a2…` | 名字前缀过滤 |

`print` 行 7 种形态（含 `bindings:len(B)` / `bindings:B` / `fakeIds` / `modules` / `rows+hunks` / `mods` / `R+D`）。**模板必须保留原初始化行与 print 行，只替换 5 行选择段**——否则会破坏 `B` 的 list/int 语义与附加字段。

---

## 2 第二步：改造模板（可粘贴）

### 2.1 方案 A 标准形态——完整片段（GATE_CODE 内的 JS 字符串数组行）

**改前**（36/36 同构的 5 行选择段；以 `dwfrun-15585c14…` 的 lowered GATE_CODE 为准）：

```javascript
    "cands=sorted(wd.glob('*.md')) if wd.is_dir() else []",
    "if not cands: P.append('写域内无 md 交付件')",
    "else:",
    " DOC=max(cands,key=lambda p:p.stat().st_size)",
    " t=DOC.read_text(encoding='utf-8');NB=DOC.stat().st_size",
```

**改后**（`<MAIN>` 按 §3 逐处代入；`hashlib` 已在 36/36 的 GATE_CODE 首行 `import json,pathlib,re,hashlib` 导入）：

```javascript
    "DOC=wd/'<MAIN>';SHA='MISSING'",
    "if not DOC.is_file(): P.append('主件缺失 <MAIN>（写域='+wd.name+'）')",
    "else:",
    " raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()",
    " t=raw.decode('utf-8',errors='replace')",
```

**print 行**（7 种形态统一做一处最小插入，不重建整行）：把 `'problems':P,` 改成 `'problems':P,'docSha256':SHA,`。例如

```javascript
    "print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))",
```

（`bindings:len(B)` 的那 8 处保留 `len(B)`；`FAKE/mods/rows/hunks/R/D` 附加字段原样保留。）

**为什么这样保留**：旧段第 2–4 行是 `if/else:` 两分支，后续所有检查行（`for s in …`、`for k in …`、`B=re.findall...`、`print`）都在 `else:` 块内、带 1 空格 Python 缩进。改后仍是 `if not DOC.is_file(): P.append(...)` + `else:` + 1 空格缩进的 `raw=…`/`t=…`，**后续检查行一字不动仍合法**。本会话对 36 处逐处做了 `ast.literal_eval` 还原 + `compile()`：`python_compiles = 36/36`，`src_lines` 22–27 行（`_dn_glm_patch36_out.json`）。

**建议叠加 sha256 校验**（已含在改后段里）：`hashlib.sha256(DOC.read_bytes())` 在**门禁读文件的同一次 `read_bytes()`** 上算，输出 `docSha256`；派发方 `fps` 表若给了该主件期望指纹，再加一行

```javascript
    " if SHA!='<EXPECTED_SHA256>': P.append('主件指纹不符')",
```

（放在 `t=raw.decode(...)` 之后、原检查行之前，缩进 1 空格。本轮**未**在任何历史 payload 上实施此行；仅模板。）

**主件缺失的预期行为（可独立验证）**：`DOC.is_file()` 为假 → `P.append('主件缺失 <MAIN>（写域=<域名>）')` → `ok=false`；`SHA` 保持 `'MISSING'`，`bindings` 保持初始化值（0 或 `len([])`），`docBytes=0`。S4 沙盒实跑输出（`_dn_sandbox_run.py`，本会话实跑）：方案 A `ok=False doc=MAIN.md problems=主件缺失 MAIN.md（写域=S4）`；对照 Gen-2 同场景 `ok=True doc=_only_side.md`。

### 2.2 主件名约定：两个思路的评估

现实：32 域主件名全不统一——`COUNTERPART_FIX.md` / `APPROVAL_PACK.md` / `S604_SCRIPT_HUNT.md` / `LEDGER_APPENDIX_DRAFT.md` / `CANDIDATE_RESIGN_YES_V2.md` …，且 `n4_yi_final_20261108` 域内有两个非下划线 md（`B_EXECUTION_SPEC_V2_YI.md` 与 `CANDIDATE_RESIGN_YES_V2.md`，`_dn_glm_sites_out.json`）。

**思路①：任务书里显式写死（现行做法）——采用为主约定，并硬化执行。**
- 实证：36 处**主件名全部可确定**：33 处 payload 有 `const DOC = "lead/<域>/<主件>.md"`（`_dn_glm_rescan_out.json` `defect_rows_const_doc=33`）；余 3 处（`ledger_appendix_20261108` 的 3 个 run）无 `const DOC=`，但任务书【交付】段写明 `LEDGER_APPENDIX_DRAFT.md`（`_dn_glm_sites.py` 的 `DELIVER_RE` 抓到，输出 `deliver_hint=['LEDGER_APPENDIX_DRAFT.md']`）。`_dn_glm_selfcheck32_out.json`：32/32 域 `DETERMINABLE(主件在场)`，0 个 `NOT_DETERMINABLE`。
- 结论：Gen-2 不是「约定缺失」，是**门禁弃用了已有约定**（诊断件 `GATE_SUBJECT_ID_FIX.md:83` 亦记 counterpart 发 ASK 有 `const DOC=` 而 GATE_CODE 未引用）。改命名规则无用，要改门禁。
- 硬化三条：(i) `const DOC=` 列为任务书必写项，缺写 = 不派发；(ii) 生成器侧禁用 token 表加入 `cands=sorted(` 与 `DOC=max(`，新门禁含之直接拒生成；(iii) 门禁输出必须带 `doc`/`docBytes`/`docSha256`。

**思路②：统一后缀（一律 `*_MAIN.md`）——不作强制，只作兜底告警。**
- 优点：门禁可脱离任务书 `glob('*_MAIN.md')` 恰一即用。
- 缺点（实证/据理）：(i) 32 域现役主件全是语义名，强改要连动台账引用与 49 个已显式命名门禁；(ii) 「恰一」在 `n4_yi_final` 这类多主件域照样误 FAIL——诊断件 `GATE_SUBJECT_ID_FIX.md:134-146` 记方案 B 会误伤 121 个多主件域（该 121 数本会话**未独立复算，标未验**），本会话至少实测 1 个缺陷域 bare=2；(iii) 后缀边界本身成为新的猜谜（下划线包含/排除），可操纵性只是从 size 换壳到命名。
- 定位：任务书漏写 `const DOC=` 时，`_dn_gate_selfcheck.py` 给 `WEAK(仅约定启发式：无_前缀者恰一)` 并告警，**不自动采用**；`NOT_DETERMINABLE` 一律不发。

**推荐**：思路①为主 + 思路②仅作自检的 WEAK 档；32 域统一按 §3 表把 `<MAIN>` 写进 GATE_CODE。

### 2.3 迁移路径：36 处是历史 payload（不能改），从下一发开始

1. **任务书层**：保留 JS 顶部 `const DIR = "…"; const DOC = "lead/<域>/<主件>.md";`；任务书正文加一句「主件必须按 `const DOC` 声明名交付，门禁以此为唯一被核对象」。
2. **门禁层**：GATE_CODE 一律 §2.1 形态；生成器把 `DOC=max(` / `cands=sorted(` 列禁用 token；缺 `const DOC=` 不发。
3. **指纹层**：门禁输出 `docSha256`/`docBytes`；`publishArtifact` 的 description 附该指纹；复核回件绑定行必须是**主件**的指纹（本补丁把指纹打进门禁输出，主件事后被增改即可对不上）。
4. **库层**：每发 dispatch 前跑一次 `python -I -X utf8 _dn_gate_selfcheck.py lead/<域>/`，`NOT_DETERMINABLE` 不发（本会话 32/32 全 DETERMINABLE）。
5. **回归层**：S1–S4 沙盒（§4.2）作为门禁库回归用例；改模板后四场景全绿才可上线。
6. **历史层**：36 处**一律不落地修改**（纪律）；只登记欠账 + 对已交付件按显式命名重跑门禁（§5.3）。

---

## 3 第三步：36 处逐处改造建议（按 32 写域分组）

统一改法 = §2.1 的 5 行替换 + print 插入 `docSha256`；**逐处只需代入 `<MAIN>`**。下表 `已交付` = 本会话 `os.path.isfile` 实测（`_dn_glm_36_list.json`），全部 36 处对应主件均在盘——按纪律**不能改历史、只能登记欠账**。`变体` 列 `CAND` = 该处 `cands` 行是名字前缀过滤（D/E 形态），替换时同样整段 5 行删掉即可。

| # | 写域（lead/…） | run（dwfrun- 前 8 位） | 主件名 `<MAIN>` | 名字来源 | 已交付 | 主件字节 | 变体 | 改后第 1 行 |
|--:|:--|:--|:--|:--|:-:|--:|:-:|:--|
| 1 | c07_gate_audit_20261109 | 962827dd | C07_SELFCHECK_AUDIT.md | const DOC= | 是 | 33459 | - | `DOC=wd/'C07_SELFCHECK_AUDIT.md';SHA='MISSING'` |
| 2 | c07_gate_fix_20261109 | 66e74798 | C07_GATE_G1_G5_FIX.md | const DOC= | 是 | 25770 | - | `DOC=wd/'C07_GATE_G1_G5_FIX.md';SHA='MISSING'` |
| 3 | c07_protocol_attacks_20261109 | 80551feb | PROTOCOL_ATTACK_TEST.md | const DOC= | 是 | 32131 | - | `DOC=wd/'PROTOCOL_ATTACK_TEST.md';SHA='MISSING'` |
| 4 | c07_slot_20261109 | 80d9632c | C07_IDENTITY_SLOT.md | const DOC= | 是 | 20651 | - | `DOC=wd/'C07_IDENTITY_SLOT.md';SHA='MISSING'` |
| 5 | c07_slot_20261109 | bc3fed8c | C07_IDENTITY_SLOT.md | const DOC= | 是 | 20651 | - | 同上（同域第 2 发） |
| 6 | c07_truth_protocol_20261109 | 24bda605 | C07_TRUTH_SELF_PROOF.md | const DOC= | 是 | 38232 | - | `DOC=wd/'C07_TRUTH_SELF_PROOF.md';SHA='MISSING'` |
| 7 | counterpart_fix_20261109 | 636adfc5 | COUNTERPART_FIX.md | const DOC= | 是 | 32830 | - | `DOC=wd/'COUNTERPART_FIX.md';SHA='MISSING'` |
| 8 | f2d_rootcause_20261109 | 5ad91c91 | F2D_ROOT_CAUSE.md | const DOC= | 是 | 32939 | - | `DOC=wd/'F2D_ROOT_CAUSE.md';SHA='MISSING'` |
| 9 | gate_fp7_20261108 | fed3c2a2 | GATE_FALSE_POSITIVE_5_6_7.md | const DOC= | 是 | 27211 | CAND | `DOC=wd/'GATE_FALSE_POSITIVE_5_6_7.md';SHA='MISSING'` |
| 10 | gate_postmortem_20261109 | 65d9f3a9 | GATE_LITERAL_MATCH_POSTMORTEM.md | const DOC= | 是 | 36847 | - | `DOC=wd/'GATE_LITERAL_MATCH_POSTMORTEM.md';SHA='MISSING'` |
| 11 | gate_r9r12_20261109 | 65b875da | GATE_R9R12_REGRESSION.md | const DOC= | 是 | 37578 | - | `DOC=wd/'GATE_R9R12_REGRESSION.md';SHA='MISSING'` |
| 12 | handoff_pack_20261109 | a4a38b66 | APPROVAL_PACK.md | const DOC= | 是 | 40024 | - | `DOC=wd/'APPROVAL_PACK.md';SHA='MISSING'` |
| 13 | ledger_appendix_20261108 | 13448f03 | LEDGER_APPENDIX_DRAFT.md | 【交付】文本 | 是 | 45719 | - | `DOC=wd/'LEDGER_APPENDIX_DRAFT.md';SHA='MISSING'` |
| 14 | ledger_appendix_20261108 | 616f12ea | LEDGER_APPENDIX_DRAFT.md | 【交付】文本 | 是 | 45719 | - | 同上（同域第 2 发） |
| 15 | ledger_appendix_20261108 | 830e57b2 | LEDGER_APPENDIX_DRAFT.md | 【交付】文本 | 是 | 45719 | - | 同上（同域第 3 发） |
| 16 | matrix_ab_ruling_20261109 | db5bad08 | RULING_MATRIX_AB.md | const DOC= | 是 | 36851 | - | `DOC=wd/'RULING_MATRIX_AB.md';SHA='MISSING'` |
| 17 | matrix_reach_20261109 | c482b235 | MATRIX_DEFECT_REACHABILITY.md | const DOC= | 是 | 27825 | - | `DOC=wd/'MATRIX_DEFECT_REACHABILITY.md';SHA='MISSING'` |
| 18 | matrix_row5_20261109 | 69087c8f | MATRIX_ROW5_COUPLING.md | const DOC= | 是 | 29818 | - | `DOC=wd/'MATRIX_ROW5_COUPLING.md';SHA='MISSING'` |
| 19 | n10c04_ruling_20261108 | f0c21a59 | RULING_STATIC_ORDER.md | const DOC= | 是 | 45070 | - | `DOC=wd/'RULING_STATIC_ORDER.md';SHA='MISSING'` |
| 20 | n11_dimmap_20261108 | ffc43bb0 | DIM_COLUMN_MAPPING.md | const DOC= | 是 | 26493 | - | `DOC=wd/'DIM_COLUMN_MAPPING.md';SHA='MISSING'` |
| 21 | n11_wording_fix_20261108 | 903e6b21 | N11_WORDING_FIX.md | const DOC= | 是 | 18966 | - | `DOC=wd/'N11_WORDING_FIX.md';SHA='MISSING'` |
| 22 | n4_yi_final_20261108 | af6f3c87 | CANDIDATE_RESIGN_YES_V2.md | const DOC= | 是 | 23129 | CAND | `DOC=wd/'CANDIDATE_RESIGN_YES_V2.md';SHA='MISSING'` |
| 23 | o1prime_reach_20261109 | a1c4b1fd | O1PRIME_REACHABILITY.md | const DOC= | 是 | 23488 | - | `DOC=wd/'O1PRIME_REACHABILITY.md';SHA='MISSING'` |
| 24 | pending_factpack_20261108 | ebe5b75c | PENDING_FACTPACK_C02_C03_C06_C07.md | const DOC= | 是 | 42938 | - | `DOC=wd/'PENDING_FACTPACK_C02_C03_C06_C07.md';SHA='MISSING'` |
| 25 | r11_f2_fix_20261109 | d3ec8aec | R11_F2_COVERAGE_FIX.md | const DOC= | 是 | 25282 | - | `DOC=wd/'R11_F2_COVERAGE_FIX.md';SHA='MISSING'` |
| 26 | s604_attribution_20261108 | cec38f8b | S604_ATTRIBUTION.md | const DOC= | 是 | 27182 | - | `DOC=wd/'S604_ATTRIBUTION.md';SHA='MISSING'` |
| 27 | s604_exclusive_20261109 | 88b03f6c | S604_EXCLUSIVITY.md | const DOC= | 是 | 30536 | - | `DOC=wd/'S604_EXCLUSIVITY.md';SHA='MISSING'` |
| 28 | s604_script_gap_20261109 | 5e5d5e49 | S604_SCRIPT_GAP.md | const DOC= | 是 | 20271 | - | `DOC=wd/'S604_SCRIPT_GAP.md';SHA='MISSING'` |
| 29 | s604_script_gap_20261109 | bc9d8b8e | S604_SCRIPT_GAP.md | const DOC= | 是 | 20271 | - | 同上（同域第 2 发） |
| 30 | s604_script_hunt_20261109 | dcda8414 | S604_SCRIPT_HUNT.md | const DOC= | 是 | 27347 | - | `DOC=wd/'S604_SCRIPT_HUNT.md';SHA='MISSING'` |
| 31 | samedoc_link_20261109 | cd88a9f5 | SAMEDOC_LINK.md | const DOC= | 是 | 27995 | - | `DOC=wd/'SAMEDOC_LINK.md';SHA='MISSING'` |
| 32 | strict_exposure_20261109 | 15585c14 | STRICT_EXPOSURE.md | const DOC= | 是 | 23798 | - | `DOC=wd/'STRICT_EXPOSURE.md';SHA='MISSING'` |
| 33 | text_fix_unified_20261109 | 53714984 | UNIFIED_TEXT_FIX.md | const DOC= | 是 | 42172 | - | `DOC=wd/'UNIFIED_TEXT_FIX.md';SHA='MISSING'` |
| 34 | u5u6_mirror_20261109 | 802eb959 | U5U6_MIRROR_TEXTS.md | const DOC= | 是 | 24897 | - | `DOC=wd/'U5U6_MIRROR_TEXTS.md';SHA='MISSING'` |
| 35 | v2_precision_fix_20261108 | f123d326 | V2_PRECISION_FIX_PROPOSAL.md | const DOC= | 是 | 22048 | - | `DOC=wd/'V2_PRECISION_FIX_PROPOSAL.md';SHA='MISSING'` |
| 36 | w2_samecause_20261109 | 27d477b1 | W2_SAME_CAUSE.md | const DOC= | 是 | 19552 | - | `DOC=wd/'W2_SAME_CAUSE.md';SHA='MISSING'` |

**(c) 若主件名在 payload 里找不到怎么办？** 本会话 36/36 都找得到（33 `const DOC=` + 3【交付】文本，0 个 NOT_DETERMINABLE），故本批无此情形。通用规则：① 自检脚本给 `WEAK`（域内无 `_` 前缀 md 恰一）→ 只告警、不自动采用，要求派发方补写 `const DOC=` 后重发；② `NOT_DETERMINABLE`（0 份或多份）→ **不发该任务**；③ 严禁回退到 `max(st_size)` / mtime / sorted-first 任一启发式（诊断件 `GATE_SUBJECT_ID_FIX.md:87-95` 列其缺陷家族）。

**逐处独立可验证**：每处替换后跑 §2.1 的 5 项断言（本会话已在内存里对 36/36 实跑：`after_no_docmax` / `after_explicit` / `after_fail_on_missing` / `after_sha` / `python_compiles` 全 36/36，`_dn_glm_patch36_out.json`）；再把该处主件临时改名（沙盒副本里做，不动历史）→ 预期 `ok=false` 且 problems 含 `主件缺失 <MAIN>`。S4 已给出该预期行为的实跑输出。

---

## 4 第四步：回归验证

### 4.1 可复用自检脚本（扫任意写域判断「主件名是否可确定」）

`lead/gate_doc_name_fix_20261109/_dn_gate_selfcheck.py`（前序产物，本会话亲读 `_dn_gate_selfcheck.py:1-87` 并实跑）。用法：

```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_gate_selfcheck.py lead/<域>/
```

判定序（`_dn_gate_selfcheck.py:32-81`）：① 库内指向该域的最新 payload 的 `expected=wd/'…'` / `const DOC="…"` / `doc=root/'…'`（强）→ ② 任务书【交付】段 `X.md`（次强）→ ③ 域内无 `_` 前缀 md 恰一（WEAK，仅告警）→ 否则 `NOT_DETERMINABLE`。输出 `verdict` / `main` / `payload_evidence.source` / `domain_md`。

本会话实跑（32 域全量，`_dn_glm_selfcheck32_out.json`）：**32/32 `DETERMINABLE(主件在场)`**，来源 31 `payload门禁显式命名` + 1 `payload任务书【交付】指示`；空域对照 `lead/__nonexistent_domain_glm__` → `NOT_DETERMINABLE`。
**已知瑕疵（如实）**：该脚本的 `gate_has_docmax` 用 `DEFECT_RE.search(text)` 搜整个 mjs 文本（`:56`），会把任务书【背景】引用文本误计——本任务域 `lead/gate_doc_name_fix_20261109` 被报 `gate_has_docmax=true`，但其 GATE_CODE 实为 Gen-3 显式形态（`_dn_glm_sites_out.json` 的 `noise` 实证）。修正法：把该判定改到 GATE_CODE 块内（本会话 `_dn_glm_rescan.py` 已按此口径）。**未修改该历史前序脚本**（本轮只登记）。

### 4.2 S1–S4 四场景（复用诊断件的沙盒思路，本会话实跑）

诊断件沙盒在 `lead/gate_subject_id_20261109/_si_sandbox/`（`_si_exploit_out.txt` 记录 S1_repro / S2_smuggle / S3_mask / S4a_dual_bad_bigger / S4b_dual_bad_smaller），本写域复刻夹具在 `_dn_sandbox/S1..S4/`。对照脚本 `_dn_gate_gen2.py`（复刻 `max` 选择，检查项与方案 A 完全一致）与 `_dn_gate_planA.py`（显式命名 + 缺失即 FAIL + `read_bytes` 同次算 sha256）。

实跑命令与输出：
```
python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_sandbox_run.py
```
| 场景 | Gen-2(max 猜大) | 方案 A(显式命名) |
|:--|:--|:--|
| S1 正常（仅主件齐要素） | `ok=True doc=MAIN.md` | `ok=True doc=MAIN.md` |
| S2 违禁词藏主件、侧件更大更干净 | **`ok=True doc=_side_big.md`（绕过）** | `ok=False doc=MAIN.md`，`含越界断言 已改台账` |
| S3 主件缺要素、中稿更大补齐 | **`ok=True doc=_mid_complete.md`（误判通过）** | `ok=False doc=MAIN.md`，`缺小节 ## 3；缺要素 未验` |
| S4 主件缺失、侧件在场 | **`ok=True doc=_only_side.md`（顶替）** | `ok=False doc=MAIN.md`，`主件缺失 MAIN.md（写域=S4）` |

（输出含 `docSha256` 前 16 位；S4 方案 A 为 `MISSING`。）

### 4.3 怎么证明「改造后不再有 S2/S3 漏洞」

1. **机制证明**：S2/S3/S4 的全部攻击路径都要求「被核对象 ≠ 约定主件」。方案 A 把 `DOC` 钉死为 `wd/'<MAIN>'`，`max` / `cands` 不再参与选择；size 竞争、下划线前缀、双主件、mtime 全部失去作用面。主件本体缺要素/含违禁词/缺失，分别由原检查行 / 禁词行 / `DOC.is_file()` 在**主件本体**上 FAIL。
2. **差分实证**：同一套检查项、仅选择段不同（Gen-2 vs 方案 A），S2/S3/S4 三条旧 PASS 全变 FAIL 且 problems 指向主件；S1 双 PASS 证明无误伤（§4.2 本会话实跑输出）。
3. **逐处实证**：36/36 在内存里完成替换后 `DOC=max(` 归零、显式名与 `sha256` 到位、Python 源码 `compile()` 通过（`_dn_glm_patch36_out.json`）。
4. **门禁库回归**：以后每改模板重跑 `_dn_sandbox_run.py`；四场景期望固定为「S1 双 PASS，S2/S3/S4 新门禁全 FAIL」，任一不符即拒上线。
5. **声明边界**：以上证明的是「§2.1 模板 + 本写域夹具/32 域主件名」这一组合；**未**在真实历史 payload 上落地运行（纪律禁止改历史），故对「历史 36 发当时实跑输出」不作断言（§6 未验项）。

### 4.4 32 域补跑（已交付件重新过显式命名门禁）

`_dn_regate_domains.py`（前序产物，本会话实跑）：每域取最新缺陷 run 的 GATE_CODE，用 `ast.literal_eval` 提取各任务自己的检查参数（小节表/要素/违禁表/绑定行正则，`unparsed=0`），按**显式主件**重放，独立算 `mainSha256`/`mainBytes`/`mainIsLargest`。输出 `_dn_regate_out.json`：**32 域、19 域全过、13 域有提示**；`mainIsLargest=false` 恰 2 域：`counterpart_fix_20261109`（32830B）、`n4_yi_final_20261108`（23129B）。

---

## 5 第五步：欠账清单与优先级

### 5.1 已交付且可能被误判过——人工复核清单

36 处**全部已交付**（§3 表 `已交付=是`，本会话 `os.path.isfile` 实测），按纪律不能改历史 payload，只能登记欠账。

**(i) 结构性最可疑（主件不是域内最大 / 主件名有竞争者）**：
| 域 | 依据（本会话实跑） | 动作 |
|:--|:--|:--|
| counterpart_fix_20261109 | `_cf_counterpart_vs_tighten_20261109.md` 32840B 比主件 32830B 大 **10B**；`_dn_regate_out.json` `mainIsLargest=false`；诊断件 `GATE_SUBJECT_ID_FIX.md:44,101` 已实证误判 | 已按显式命名补跑全过（bind=16）；登记「当时误判」欠账 |
| n4_yi_final_20261108 | 域内 bare=2（`B_EXECUTION_SPEC_V2_YI.md` 35486B / 主件 23129B），`_dn_glm_sites_out.json`；`_dn_regate_out.json` `mainIsLargest=false` 且**终稿补跑有 4 项提示**：`缺要素 不签 APPROVE_SCOPE`、`含越界断言 可应用母本`、`放行 N-5`、`缺规范格式绑定行` | **P0**：人工核对终稿 + 重签 |
| handoff_pack_20261109 / s604_script_hunt_20261109 | 诊断件 `GATE_SUBJECT_ID_FIX.md:55-56,266` 记其门禁时点「结构性无主件」（主件晚于侧件落盘） | P1：补一次显式命名门禁留痕 |
| ledger_appendix_20261108 | 3 发共用一域，无 `const DOC=`，主件名仅【交付】文本；补跑提示 `含越界断言 已生效`、`缺规范格式绑定行` | P1：补 `const DOC=` 约定 + 绑定行 |

**(ii) 补跑 13 个提示域（人工确认是措辞变体还是真缺）**：`c07_gate_audit`（缺要素 未改 _c7_selfcheck.py）、`c07_protocol_attacks`（缺绑定行）、`c07_slot`（`已填`+缺绑定行）、`c07_truth_protocol`（`已填`+缺绑定行）、`ledger_appendix`（`已生效`+缺绑定行）、`matrix_ab_ruling`（缺要素 需谁批准 + `已改矩阵`/`已收紧`/`已施行`）、`matrix_reach`（缺要素 实跑输出）、`n10c04_ruling`（`授实施权`/`解除 PAUSE`）、`n11_wording_fix`（缺要素 改前改后）、`n4_yi_final`（见上）、`s604_attribution`（缺绑定行）、`s604_script_gap`（缺要素 脚本存在性/可重建）、`s604_script_hunt`（`已删除`）。
前序报告 `GATE_DOC_NAME_FIX.md:170,185` 称 8 处断言词命中经上下文分诊「全部为否定/引述语境」——**本会话未独立复核该分诊**，标为待人工确认。

**(iii) 时序限制（如实）**：本会话取 `dwfrun-*.mjs` 的 mtime 与域内 md 的 mtime 对齐，36/36 的 run mtime **全部早于**主件 mtime（例如 counterpart run 05:19 / 主件 06:18）。这是「派发时刻」而非「门禁实跑时刻」，**单凭 mtime 不能复原门禁当时读了谁**；除诊断件已实证的 counterpart 误判外，其余 35 处的「当时是否误判」一律标**未验**，按结构性暴露登记欠账，不逐发断言曾产生误判（与诊断件 `GATE_SUBJECT_ID_FIX.md:265` 一致）。

### 5.2 危险度优先级（有中间稿且大小接近主件）

依据 `_dn_glm_sites_out.json` 的 `sizes`（本会话 `os.path.getsize` 现值）：
1. **P0 `counterpart_fix_20261109`**：中稿 − 主件 = **+10 B**（32840 vs 32830），攻击窗最窄、最易复现；诊断件已实锤误判。
2. **P0 `n4_yi_final_20261108`**：中稿 − 主件 = **+5768 B**（`_n4v2_B_EXECUTION_SPEC_V2.md` 28897 vs 23129），且域内另有 bare 件 `B_EXECUTION_SPEC_V2_YI.md` 35486B；终稿补跑自身有 4 项提示。
3. **P1 `handoff_pack_20261109` / `s604_script_hunt_20261109`**：现值主件已是域内最大（40024 / 27347B），但诊断时点为「无主件」形态——**时点漂移证据**，说明这类域随时可被一个更大的 `_` 前缀件翻盘。
4. **P1 `ledger_appendix_20261108`**：3 发同域、唯一无 `const DOC=` 的域，名字靠【交付】文本；现值主件 45719B 远大于最大中稿 25723B（差 −19996B），风险在「约定不在门禁里」而非大小。
5. **P2 其余 27 域**：现值主件均为域内最大（中稿−主件差全为负，范围 −3418 ~ −33912 B），按现值不易被遮蔽；但机制缺陷相同，仍须按 §2.3 迁移规则从下一发收敛。

### 5.3 已交付域无法改历史 payload，怎么补救

1. **不改历史**：36 处 payload 一律保持原字节（本会话只读；8 件上游指纹 8/8 相符）。
2. **对已交付件重跑方案 A 门禁**：本会话已用 `_dn_regate_domains.py` 对 32 域按显式主件重放各任务自家检查（§4.4），产出 `_dn_regate_out.json`（19 过 / 13 提示）。常态化做法：对 §5.1 清单逐域重发一发小任务，门禁 = §2.1 模板实例化 + 补绑定行，产出存**新写域**、登记台账，不回写原域。
3. **补约定与指纹**：给 `ledger_appendix_20261108` 这类无 `const DOC=` 的域补写声明；所有后续门禁输出 `docSha256`，让「主件事后被增改」可检。
4. **生成器侧（活体）**：把 §2.1 形态固化进门禁库 + 禁用 token 表 + §2.3 五条迁移规则；本会话实测库内已有 49 个 Gen-1/Gen-3 显式命名先例可直接参照。
5. **未纳入重放的部分（如实）**：台账漂移段（PRE 指纹为运行期值）、门禁内一次性复合条件、门禁时刻字节态——均标未验（前序报告 `GATE_DOC_NAME_FIX.md:171` 亦声明）。

---

## 6 未验项 / 纪律声明

- 未独立复算诊断件的「121 个多主件域」「d13d14 差 2950B / direction_ruling 差 4428B」「5 受害域」等时点计数（标未验；本会话仅实测 32 缺陷域的现值大小）。
- 35 处「门禁当时实际读了谁」不可复原（§5.1(iii)），不作逐发断言。
- 13 个提示域的断言词「否定/引述语境」分诊未独立复核。
- `_dn_gate_selfcheck.py` 的 `gate_has_docmax` 全文搜索瑕疵已登记（§4.1），本轮**未修改**该前序脚本。
- 全程零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`；未 commit、未 push；历史 payload / 诊断域 / `lead/` 历史写域只读。
- 本轮落盘仅在本写域，前缀 `_dn_glm_`：`_dn_glm_rescan.py`、`_dn_glm_rescan_out.json`、`_dn_glm_sites.py`、`_dn_glm_sites_out.json`、`_dn_glm_selfcheck32_out.json`、`_dn_glm_patch36_out.json`、`_dn_glm_36_list.json`、本件。

## 7 实跑命令清单（本会话）

| # | 命令 | 关键输出 |
|--:|:--|:--|
| 1 | `find .zcode/workflow-runs -maxdepth 1 -name '*.mjs' \| wc -l` | 223 |
| 2 | `python -I -X utf8 …\_dn_glm_rescan.py` | 36 文件 / 36 处 / 32 域 / 49 安全实例 / 38 文件级命中 |
| 3 | `python -I -X utf8 …\_dn_glm_sites.py` | `identical=true`；2 处引用噪音定性；32 域主件名；6 个安全实例样本 |
| 4 | 内联 `python -I -X utf8 - <<'PY' …`（选择段形态） | 5 种选择段 / 3 种 P 初始化 / 7 种 print 行 |
| 5 | `python -I -X utf8 …\_dn_sandbox_run.py` | S1 双 PASS；S2/S3/S4 旧 PASS → 新 FAIL |
| 6 | `python -I -X utf8 …\_dn_gate_selfcheck.py <32 域>` | 32/32 DETERMINABLE；空域 NOT_DETERMINABLE |
| 7 | `python -I -X utf8 …\_dn_regate_domains.py` | 32 域 / 19 过 / 13 提示 / `mainIsLargest=false`×2 |
| 8 | 内联 36 处替换 + `compile()` 验证 | 36/36 全绿，`_dn_glm_patch36_out.json` |
| 9 | 内联 `hashlib` 八件指纹 | 8/8 相符（§头部绑定行） |
| 10 | 内联 36 处清单生成 | 36/36 已交付 / 33 const DOC + 3【交付】 / 2 CAND 变体 |

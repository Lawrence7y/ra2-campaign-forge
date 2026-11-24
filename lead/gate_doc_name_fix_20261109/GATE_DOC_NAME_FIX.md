# 门禁被核对象显式命名（方案 A）改造方案——36 处位点逐处改法、模板、回归与欠账

- 唯一写域：`lead/gate_doc_name_fix_20261109/`
- 撰写：位点改造撰写员｜2026-11-09｜本文 = `GATE_DOC_NAME_FIX.md`（本次交付主件）
- 纪律：零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码（不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；`lead/gate_subject_id_20261109/`、` .zcode/workflow-runs/` 全部 mjs、lead 下全部历史写域一律只读；不 commit、不 push。Python 一律 `python -I -X utf8` + 绝对路径，指纹一律 `hashlib`。
- 证据口径：本文全部数字出自本会话实跑命令与输出（命令逐条列出），或 `文件:行` 引用；凡拿不到的一律写「未验」，不补造。

---

## 1 目的与边界

**目的**：对诊断件 `lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md:9`（第 13 类缺陷）已实证的门禁「用 `DOC=max(cands,key=lambda p:p.stat().st_size)` 从写域猜主件」缺陷，产出**设计改造**：① 独立复核 36 处位点；② 给**方案 A（显式命名）**可粘贴模板；③ 给 36 处「应当改成什么」的逐处改法（改前片段 / 改后片段 / 主件缺失预期行为）；④ 给主件名约定、迁移路径、回归验证设计；⑤ 给欠账清单与优先级，并如实记复核 verdict。

**边界（★ 设计改造，不改历史 payload）**：
- 只产出**改造模板 + 36 处逐处的「应当改成什么」**；36 个历史 payload 一律保持原字节，**未改历史 payload**。纪律禁止改 `.zcode/workflow-runs/` 下任何 mjs，本会话对它们只有 read。
- 模板的「逐处可独立验证」用**内存还原 + 沙盒副本**演示（`_dnw_template.py`、`_dnw_sandbox/`），不改任何历史域。
- 一切指纹、清单、时序为**本会话时点快照**；工作区是活的（编排方在撰写期间又新增了 run），下游引用前须重扫。
- 复核 verdict 如实记：见 §5.1，`verdict = partial`，标 **unconfirmed**（非 confirmed）。

**诊断链引用**：缺陷定义与方案 A 首选 `lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md:9`、`:115-131`；「payload 早有 `const DOC` 而 GATE_CODE 弃用」`:83`；启发式缺陷家族 `:87-95`；S2 绕过 / S3 误判通过 / S4 翻转 `:101-104`；方案 B 误伤多主件域 `:134-146`（该数本会话未独立复算，见 §5.4）；36 处清单 `:205-252`。沙盒五场景实录 `lead/gate_subject_id_20261109/_si_exploit_out.txt:1-20`。

---

## 2 上游指纹（八件）+ 36 处位点复核结果

### 2.1 八件上游指纹（本会话 hashlib 实算，8/8 与编排方派发常量一致）

实跑命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dnw_verify.py`（输出快照 `lead/gate_doc_name_fix_20261109/_dnw_verify_out.json`）。输出 `FP {"upstream_matches": 8, "total": 8}`，8 件逐件 `match=True`。绑定行见 §5.1。

| 件 | SHA256（现值 = 派发常量） | 字节 |
|:--|:--|--:|
| lead/gate_subject_id_20261109/GATE_SUBJECT_ID_FIX.md | 302a4564…f63c | 31692 |
| lead/gate_subject_id_20261109/_si_SUBJECT_ID_DEFECT.md | 8c67dc3f…f4dc | 23441 |
| lead/gate_subject_id_20261109/_si_fix_lib.py | 54751e9a…0eee | 2850 |
| lead/gate_subject_id_20261109/_si_gatescan_out.json | c8024cb7…7d94 | 611043 |
| lead/gate_subject_id_20261109/_si_wfscan_out.json | e326df6b…9f52 | 180256 |
| lead/gate_subject_id_20261109/_si_exploit_out.txt | 151f4f94…2e587 | 5717 |
| lead/PENDING_DECISIONS.md | 3765eddb…2d7 | 52419 |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de4…8ede | 759518 |

（完整 64 位值见 §5.1 绑定行；本会话另核被核主报告 `lead/gate_doc_name_fix_20261109/_dn_glm_final.md` 现值 SHA256 = `c977e3ca…d05`、31453 B，与派发常量相符。）

### 2.2 36 处位点独立重扫（不采信编排方数字）

同一命令 `_dnw_verify.py` 自写解析器：逐个 `export const payload = ` → `json.JSONDecoder().raw_decode` → 取 `lowered` → 定位 `const GATE_CODE = [` 块 → **仅在块内**数 `DOC=max(cands,key=lambda p:p.stat().st_size)`。输出：

```
all_files_total=226  mjs_total=225  payload_parse_errors=[]
gate_defect_files=36  gate_defect_total_hits=36  domains=32
domain_multiplicity={c07_slot_20261109:2, ledger_appendix_20261108:3, s604_script_gap_20261109:2}
wholefile_literal_files=38
noise_files_in_wholefile_only=[dwfrun-3ca3ee7b…, dwfrun-bdff6762…]
safe_expected_files=17  safe_docroot_files=34  safe_total_files=51
safe_in_defect_set=[]
```

结论（回答「实际几处 / 几域 / 几处已安全」）：

- **(a) 实际 = 36 处、36 个 payload、每处 1 处命中**，与任务名「36 处」一致；分布在 **32 个历史写域**（`ledger_appendix_20261108`×3、`c07_slot_20261109`×2、`s604_script_gap_20261109`×2，其余 29 域各×1，域名清单见 §4.1 表）。
- **全文件字面口径 = 38 文件**，多出的 `dwfrun-3ca3ee7b…`、`dwfrun-bdff6762…` 两处的 `DOC=max` 字面只出现在**任务书【背景】引用文本**，其 `GATE_CODE` 实为 Gen-3 显式形态 `expected=wd/'GATE_DOC_NAME_FIX.md'`；故编排方【位点重扫】38 行清单应修正为 **36**。集合比对：该 38 行去掉这 2 行噪音 = 我块内口径 36 行，0 缺 0 多。
- **(c) 已安全（门禁已显式命名）= 51 个、0 个在缺陷集合内**：Gen-1 `doc=root/'<主件>.md'` + `交付件缺失` 34 个；Gen-3 `expected=wd/'<主件>.md'` + `主交付件未按约定命名` 17 个（含本任务自身两发）。**库内已有 51 发可跑先例**，证明方案 A 不是空想。此为 **225 mjs 时点值**；设计轮 223 mjs 时报 49（Gen-1 34 + Gen-3 15），编排方会话中新增 2 个 `expected=` run（`MERGED_CONSUMER_AUDIT.md` / `LEDGER_BOUND_VOLUME.md`），故 15→17、49→51，均为时点值、缺陷集合仍为 36。

### 2.3 36 处改前片段的 3 种形态（本会话 `_dnw_template.py` 还原）

实跑 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dnw_template.py` → `distinct_before_shapes=3`、计数 `34 / 1 / 1`：

- **S0（34 处）**：
```python
cands=sorted(wd.glob('*.md')) if wd.is_dir() else []
if not cands: P.append('写域内无 md 交付件')
else:
 DOC=max(cands,key=lambda p:p.stat().st_size)
 t=DOC.read_text(encoding='utf-8');NB=DOC.stat().st_size
```
- **S1（1 处，`n4_yi_final_20261108` / `af6f3c87`）**：`cands=sorted([p for p in wd.glob('*.md') if p.name.startswith('CANDIDATE_RESIGN')]) …`，提示词为 `写域内无 CANDIDATE_RESIGN 交付件`。
- **S2（1 处，`gate_fp7_20261108` / `fed3c2a2`）**：`startswith('GATE_FALSE_POSITIVE')`，提示词为 `写域内无 GATE_FALSE_POSITIVE 交付件`。

三种都在 `else:` 内 `max(...st_size)` 猜大，S1/S2 只是加了名字前缀过滤（现域各仅 1 个匹配文件，实测见 §4.1 注）。**P 初始化 3 种、print 行 7 种**（`B=[]` 8 处用 `len(B)`、`B=0` 25 处、`FAKE=0` 3 处；print 附加 `bindings` / `modules` / `fakeIds` / `rows` / `hunks` / `R` / `D` 等字段）——这一点是 §3 模板必须加固的根因，见 §3.3。

---

## 3 改造模板（方案 A 完整片段 + 主件名约定 + 迁移路径）

### 3.1 可粘贴模板：方案 A「加固版」选择段（放进 payload 的 `GATE_CODE` JS 字符串数组）

**改前**（§2.3 的 S0/S1/S2 五行选择段，36/36 同构）→ **改后**：把那 5 行整段替换为下面 6 行（`<MAIN>` 按 §4.1 表逐处代入主件名；`hashlib` 已在 36/36 的 `GATE_CODE` 首行 `import json,pathlib,re,hashlib` 导入，亲读 `_dnv_sandbox36/gate_r9r12_20261109/_dnv_gate.py:1`）。

```javascript
    "<ELSE_ONLY_VARS>",                                        // ← 加固行：见 §3.3；无 else-only 变量时整行省略
    "DOC=wd/'<MAIN>';SHA='MISSING'",
    "if not DOC.is_file(): P.append('主件缺失 <MAIN>（写域='+wd.name+'）')",
    "else:",
    " raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()",
    " t=raw.decode('utf-8',errors='replace')",
```

**print 行只做一处最小插入**：把 `'problems':P,` 改成 `'problems':P,'docSha256':SHA,`，其余字段（`bindings:len(B)` / `B` / `FAKE` / `mods` / `rows` / `R` / `D` 等）**原样保留**。示例（S0 常见形态）：

```javascript
    "print(json.dumps({'ok':not P,'problems':P,'docSha256':SHA,'bindings':B,'docBytes':NB,'doc':(DOC.name if DOC else '')},ensure_ascii=False))",
```

**独立可跑版（Python 可执行，等价于上面 JS 行拼出的门禁）**——本写域 `lead/gate_doc_name_fix_20261109/_dn_gate_planA.py:15-45` 即此形态：

```python
import json, re, hashlib
from pathlib import Path
wd = Path('<写域绝对路径>')
P = []; NB = 0; SHA = "MISSING"; B = 0
DOC = wd / '<MAIN>'
if not DOC.is_file():
    P.append("主件缺失 <MAIN>（写域=" + wd.name + "）")
else:
    raw = DOC.read_bytes(); NB = len(raw); SHA = hashlib.sha256(raw).hexdigest()
    t = raw.decode("utf-8", errors="replace")
    # ↓ 以下原有检查行（缺小节 / 缺要素 / 违禁词 / 绑定行正则 / 台账漂移）一字不动
    ...
print(json.dumps({"ok": not P, "problems": P,
                  "doc": '<MAIN>', "docBytes": NB, "docSha256": SHA,
                  "bindings": B}, ensure_ascii=False))
```

**关键约束**：保留原初始化行与 print 行；改后仍是 `if not DOC.is_file():` + `else:` + **1 空格** Python 缩进，后续全部检查行不改即合法。若派发方 `fps` 表给了期望指纹，可在 `else:` 内加一行 `" if SHA!='<EXPECTED_SHA256>': P.append('主件指纹不符')"`（本轮只在模板给出，未在任何历史 payload 实施）。

### 3.2 主件缺失的预期行为（每处可独立验证）

`DOC.is_file()` 为假 → `P.append('主件缺失 <MAIN>（写域=<域名>）')` → 输出合法 JSON `ok=false`、`docSha256='MISSING'`、`docBytes=0`、`bindings` 保持初始化值 → 工作流据此走补写分支（Gen-3 已有先例）。逐处预期见 §4.1 表「主件缺失预期」列。本会话 S4 沙盒实跑（§4.3）：方案 A `ok=False doc=MAIN.md problems=主件缺失 MAIN.md（写域=S4）`，对照旧 Gen-2 同场景 `ok=True doc=_only_side.md`。

### 3.3 ★ 加固行 `<ELSE_ONLY_VARS>`：复核 verdict=partial 的第 1 条（必须保留）

复核意见（见 §5.1）实锤：**印刷版模板直接粘贴，6/36 处主件缺失时不会输出 `ok=false`，而是 `NameError`**。原因：这 6 处的 print 行引用了**只在 `else:` 内赋值**的变量（`mods` / `rows` / `hk` / `rd` / `dd`），主件缺失时 `else:` 不执行、print 仍在块外 → 抛异常、无合法 JSON。

本会话独立复现两条命令：
1. 未加固对照 `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dnw_noharden.py` → `absent_parsed=30`、`absent_ok_false=30`、`absent_errors=[65b875da,66e74798,af6f3c87,cd88a9f5,d3ec8aec,ffc43bb0]`，错误为 `NameError: name 'mods' is not defined` / `'rows'` / `'rd'`。
2. 加固后 `python -I -X utf8 …\_dnw_template.py` → `sites=36`、`compile_ok=36`、`present_doc_is_main=36`、`absent_parsed=36`、`absent_ok_false=36`、`absent_has_missing_msg=36`、`absent_shaMISSING=36`、`absent_no_error=36`、`all_checks_pass=true`。

**加固规则**：在 `DOC=wd/'<MAIN>'` 行**之前、顶格**插入一行，把 print 会引用、但只在 `else:` 内赋值的名字预初始化为安全值（被 `len(...)` 包住的给 `[]`，否则给 `0`）。逐处取值（本会话 `_dnw_template_out.json` 的 `init_line`）：

| 处 | 域 | 加固行 |
|:--|:--|:--|
| 66e74798 | c07_gate_fix_20261109 | `mods=[]` |
| 65b875da | gate_r9r12_20261109 | `mods=[]` |
| ffc43bb0 | n11_dimmap_20261108 | `dd=0;rd=0` |
| af6f3c87 | n4_yi_final_20261108 | `hk=0;rows=0` |
| d3ec8aec | r11_f2_fix_20261109 | `mods=[]` |
| cd88a9f5 | samedoc_link_20261109 | `mods=[]` |

其余 30 处 `<ELSE_ONLY_VARS>` 省略（§4.1 表末列标 `—`）。此加固是对复核意见的正面吸收：**本件 §3 模板 = 加固版**，已不是被核件 `_dn_glm_final.md:109` 声称「缺失即 ok=false」的原始印刷版。

### 3.4 主件名约定：两思路评估（处理「主件名不统一」这个现实）

现实：32 域主件名全不统一（`COUNTERPART_FIX.md` / `APPROVAL_PACK.md` / `S604_SCRIPT_HUNT.md` / `CANDIDATE_RESIGN_YES_V2.md`…）。

**思路① 任务书显式写死 `const DOC = "lead/<域>/<主件>.md"` —— 采用为主、硬化执行。**
- 依据：36 处主件名 **36/36 可确定**（33 处 payload `const DOC=`、3 处 `ledger_appendix_20261108` 由任务书【交付】段给出 `LEDGER_APPENDIX_DRAFT.md`；32/32 域自检 `DETERMINABLE`，见 §4.2）；Gen-2 不是「约定失败」而是**门禁弃用已有约定**（`GATE_SUBJECT_ID_FIX.md:83`）；库内 51 发 Gen-1/Gen-3 先例证明门禁用它完全可行（§2.2）。
- 结论：改约定没用，要改门禁。硬化三条：(i) `const DOC=` 为任务书**必写项**，缺写 = 不派发；(ii) 生成器禁用 token 表加 `cands=sorted(` 与 `DOC=max(`（任何新门禁含此二 token 直接拒生成）；(iii) 门禁输出必须含 `doc` / `docBytes` / `docSha256`，`publishArtifact` description 附该指纹，复核回件绑定行必须是**主件**指纹。

**思路② 统一后缀 `*_MAIN.md`（`glob('*_MAIN.md')` 恰一即用）—— 不强制，只作 WEAK 自检告警。**
- 优点：门禁可脱离任务书取件。缺点：(i) 32 域现役全是语义名，强改要连动台账与 51 个既有门禁；(ii)「恰一」在多主件域照样误 FAIL——诊断件记方案 B 会误伤 **121 个多主件域**（`GATE_SUBJECT_ID_FIX.md:134-146`，该数本会话未独立复算）；(iii) 后缀边界只是把猜谜从 size 换壳到命名，下划线包含/排除的猜谜仍在。
- 定位：任务书漏写 `const DOC=` 时，`_dn_gate_selfcheck.py` 给 **WEAK** 档（无 `_` 前缀 md 恰一）并告警，**不自动采用**；`NOT_DETERMINABLE` 一律不发。

### 3.5 迁移路径（从下一发开始；36 处历史 payload 不可改）

1. **任务书层**：JS 顶部保留 `const DIR` + `const DOC` 双声明，正文写明「主件必须按 const DOC 声明名交付，门禁以 const DOC 为唯一被核对象」。
2. **门禁层**：`GATE_CODE` 一律 §3.1 加固版形态；禁用 token 表落 `cands=sorted(` / `DOC=max(`；`<ELSE_ONLY_VARS>` 由生成器按 print 行自动推导并插入。
3. **指纹层**：输出 `docSha256` / `docBytes`；publishArtifact description 附指纹；复核回件绑定行必须是主件指纹（防事后代改的 TOCTOU）。
4. **库层**：每发 dispatch 前跑 `python -I -X utf8 _dn_gate_selfcheck.py lead/<域>/`，`NOT_DETERMINABLE` 不发（本会话 32/32 全 DETERMINABLE，§4.2）。
5. **回归层**：S1–S4 沙盒（§4.3）+ **S0~S2 三形态逐处模板实例化 + 主件在场/缺失两态**（§4.4）全绿才上线；`_dn_gate_selfcheck.py:56` 的全文搜索瑕疵（会把任务书【背景】引用文本误计 `gate_has_docmax=true`）本轮登记**未改前序脚本**，本会话 `_dnw_verify.py` 已改为「只在 GATE_CODE 块内」口径。
6. **历史层**：36 处一律**不落地修改**，只登记欠账（§5.2）+ 对已交付件按显式命名重跑门禁（§4.2 的 32 域演示）。

---

## 4 36 处按域分组的改造建议 + 回归验证设计

### 4.1 36 处逐处「应当改成什么」（32 域分组，主件名 / 已交付 / 逐处改法 / 缺失预期）

**统一改法**：每处 = §3.1 改前 5 行（S0/S1/S2，见 §2.3）→ §3.1 改后 6 行，`<MAIN>` 代入下表「主件名」，`<ELSE_ONLY_VARS>` 代入末列（标 `—` 则省略）。表内「改后首行」即该处 `DOC=wd/'<MAIN>';SHA='MISSING'`；「主件缺失预期」= `P.append` 后的 problems 首项。**36 处同一形态，无一处需另写逻辑**。

`run` 列为 `dwfrun-<8位>-….mjs` 的 8 位前缀；完整文件名见 `lead/gate_doc_name_fix_20261109/_dn_glm_36_list.json` 与 `_dnw_verify_out.json`。

| # | run | 写域 lead/… | 主件名 | 形态 | 改后首行（逐处代入） | 已交付 | 主件缺失预期 | 加固行 |
|--:|:--|:--|:--|:-:|:--|:-:|:--|:--|
| 1 | `962827dd` | c07_gate_audit_20261109 | C07_SELFCHECK_AUDIT.md | S0 | `DOC=wd/'C07_SELFCHECK_AUDIT.md';SHA='MISSING'` | 是 | `主件缺失 C07_SELFCHECK_AUDIT.md（写域=c07_gate_audit_20261109）` | `—` |
| 2 | `66e74798` | c07_gate_fix_20261109 | C07_GATE_G1_G5_FIX.md | S0 | `DOC=wd/'C07_GATE_G1_G5_FIX.md';SHA='MISSING'` | 是 | `主件缺失 C07_GATE_G1_G5_FIX.md（写域=c07_gate_fix_20261109）` | `mods=[]` |
| 3 | `80551feb` | c07_protocol_attacks_20261109 | PROTOCOL_ATTACK_TEST.md | S0 | `DOC=wd/'PROTOCOL_ATTACK_TEST.md';SHA='MISSING'` | 是 | `主件缺失 PROTOCOL_ATTACK_TEST.md（写域=c07_protocol_attacks_20261109）` | `—` |
| 4 | `80d9632c` | c07_slot_20261109 | C07_IDENTITY_SLOT.md | S0 | `DOC=wd/'C07_IDENTITY_SLOT.md';SHA='MISSING'` | 是 | `主件缺失 C07_IDENTITY_SLOT.md（写域=c07_slot_20261109）` | `—` |
| 5 | `bc3fed8c` | c07_slot_20261109 | C07_IDENTITY_SLOT.md | S0 | `DOC=wd/'C07_IDENTITY_SLOT.md';SHA='MISSING'` | 是 | `主件缺失 C07_IDENTITY_SLOT.md（写域=c07_slot_20261109）` | `—` |
| 6 | `24bda605` | c07_truth_protocol_20261109 | C07_TRUTH_SELF_PROOF.md | S0 | `DOC=wd/'C07_TRUTH_SELF_PROOF.md';SHA='MISSING'` | 是 | `主件缺失 C07_TRUTH_SELF_PROOF.md（写域=c07_truth_protocol_20261109）` | `—` |
| 7 | `636adfc5` | counterpart_fix_20261109 | COUNTERPART_FIX.md | S0 | `DOC=wd/'COUNTERPART_FIX.md';SHA='MISSING'` | 是 | `主件缺失 COUNTERPART_FIX.md（写域=counterpart_fix_20261109）` | `—` |
| 8 | `5ad91c91` | f2d_rootcause_20261109 | F2D_ROOT_CAUSE.md | S0 | `DOC=wd/'F2D_ROOT_CAUSE.md';SHA='MISSING'` | 是 | `主件缺失 F2D_ROOT_CAUSE.md（写域=f2d_rootcause_20261109）` | `—` |
| 9 | `fed3c2a2` | gate_fp7_20261108 | GATE_FALSE_POSITIVE_5_6_7.md | S2 | `DOC=wd/'GATE_FALSE_POSITIVE_5_6_7.md';SHA='MISSING'` | 是 | `主件缺失 GATE_FALSE_POSITIVE_5_6_7.md（写域=gate_fp7_20261108）` | `—` |
| 10 | `65d9f3a9` | gate_postmortem_20261109 | GATE_LITERAL_MATCH_POSTMORTEM.md | S0 | `DOC=wd/'GATE_LITERAL_MATCH_POSTMORTEM.md';SHA='MISSING'` | 是 | `主件缺失 GATE_LITERAL_MATCH_POSTMORTEM.md（写域=gate_postmortem_20261109）` | `—` |
| 11 | `65b875da` | gate_r9r12_20261109 | GATE_R9R12_REGRESSION.md | S0 | `DOC=wd/'GATE_R9R12_REGRESSION.md';SHA='MISSING'` | 是 | `主件缺失 GATE_R9R12_REGRESSION.md（写域=gate_r9r12_20261109）` | `mods=[]` |
| 12 | `a4a38b66` | handoff_pack_20261109 | APPROVAL_PACK.md | S0 | `DOC=wd/'APPROVAL_PACK.md';SHA='MISSING'` | 是 | `主件缺失 APPROVAL_PACK.md（写域=handoff_pack_20261109）` | `—` |
| 13 | `13448f03` | ledger_appendix_20261108 | LEDGER_APPENDIX_DRAFT.md | S0 | `DOC=wd/'LEDGER_APPENDIX_DRAFT.md';SHA='MISSING'` | 是 | `主件缺失 LEDGER_APPENDIX_DRAFT.md（写域=ledger_appendix_20261108）` | `—` |
| 14 | `616f12ea` | ledger_appendix_20261108 | LEDGER_APPENDIX_DRAFT.md | S0 | `DOC=wd/'LEDGER_APPENDIX_DRAFT.md';SHA='MISSING'` | 是 | `主件缺失 LEDGER_APPENDIX_DRAFT.md（写域=ledger_appendix_20261108）` | `—` |
| 15 | `830e57b2` | ledger_appendix_20261108 | LEDGER_APPENDIX_DRAFT.md | S0 | `DOC=wd/'LEDGER_APPENDIX_DRAFT.md';SHA='MISSING'` | 是 | `主件缺失 LEDGER_APPENDIX_DRAFT.md（写域=ledger_appendix_20261108）` | `—` |
| 16 | `db5bad08` | matrix_ab_ruling_20261109 | RULING_MATRIX_AB.md | S0 | `DOC=wd/'RULING_MATRIX_AB.md';SHA='MISSING'` | 是 | `主件缺失 RULING_MATRIX_AB.md（写域=matrix_ab_ruling_20261109）` | `—` |
| 17 | `c482b235` | matrix_reach_20261109 | MATRIX_DEFECT_REACHABILITY.md | S0 | `DOC=wd/'MATRIX_DEFECT_REACHABILITY.md';SHA='MISSING'` | 是 | `主件缺失 MATRIX_DEFECT_REACHABILITY.md（写域=matrix_reach_20261109）` | `—` |
| 18 | `69087c8f` | matrix_row5_20261109 | MATRIX_ROW5_COUPLING.md | S0 | `DOC=wd/'MATRIX_ROW5_COUPLING.md';SHA='MISSING'` | 是 | `主件缺失 MATRIX_ROW5_COUPLING.md（写域=matrix_row5_20261109）` | `—` |
| 19 | `f0c21a59` | n10c04_ruling_20261108 | RULING_STATIC_ORDER.md | S0 | `DOC=wd/'RULING_STATIC_ORDER.md';SHA='MISSING'` | 是 | `主件缺失 RULING_STATIC_ORDER.md（写域=n10c04_ruling_20261108）` | `—` |
| 20 | `ffc43bb0` | n11_dimmap_20261108 | DIM_COLUMN_MAPPING.md | S0 | `DOC=wd/'DIM_COLUMN_MAPPING.md';SHA='MISSING'` | 是 | `主件缺失 DIM_COLUMN_MAPPING.md（写域=n11_dimmap_20261108）` | `dd=0;rd=0` |
| 21 | `903e6b21` | n11_wording_fix_20261108 | N11_WORDING_FIX.md | S0 | `DOC=wd/'N11_WORDING_FIX.md';SHA='MISSING'` | 是 | `主件缺失 N11_WORDING_FIX.md（写域=n11_wording_fix_20261108）` | `—` |
| 22 | `af6f3c87` | n4_yi_final_20261108 | CANDIDATE_RESIGN_YES_V2.md | S1 | `DOC=wd/'CANDIDATE_RESIGN_YES_V2.md';SHA='MISSING'` | 是 | `主件缺失 CANDIDATE_RESIGN_YES_V2.md（写域=n4_yi_final_20261108）` | `hk=0;rows=0` |
| 23 | `a1c4b1fd` | o1prime_reach_20261109 | O1PRIME_REACHABILITY.md | S0 | `DOC=wd/'O1PRIME_REACHABILITY.md';SHA='MISSING'` | 是 | `主件缺失 O1PRIME_REACHABILITY.md（写域=o1prime_reach_20261109）` | `—` |
| 24 | `ebe5b75c` | pending_factpack_20261108 | PENDING_FACTPACK_C02_C03_C06_C07.md | S0 | `DOC=wd/'PENDING_FACTPACK_C02_C03_C06_C07.md';SHA='MISSING'` | 是 | `主件缺失 PENDING_FACTPACK_C02_C03_C06_C07.md（写域=pending_factpack_20261108）` | `—` |
| 25 | `d3ec8aec` | r11_f2_fix_20261109 | R11_F2_COVERAGE_FIX.md | S0 | `DOC=wd/'R11_F2_COVERAGE_FIX.md';SHA='MISSING'` | 是 | `主件缺失 R11_F2_COVERAGE_FIX.md（写域=r11_f2_fix_20261109）` | `mods=[]` |
| 26 | `cec38f8b` | s604_attribution_20261108 | S604_ATTRIBUTION.md | S0 | `DOC=wd/'S604_ATTRIBUTION.md';SHA='MISSING'` | 是 | `主件缺失 S604_ATTRIBUTION.md（写域=s604_attribution_20261108）` | `—` |
| 27 | `88b03f6c` | s604_exclusive_20261109 | S604_EXCLUSIVITY.md | S0 | `DOC=wd/'S604_EXCLUSIVITY.md';SHA='MISSING'` | 是 | `主件缺失 S604_EXCLUSIVITY.md（写域=s604_exclusive_20261109）` | `—` |
| 28 | `5e5d5e49` | s604_script_gap_20261109 | S604_SCRIPT_GAP.md | S0 | `DOC=wd/'S604_SCRIPT_GAP.md';SHA='MISSING'` | 是 | `主件缺失 S604_SCRIPT_GAP.md（写域=s604_script_gap_20261109）` | `—` |
| 29 | `bc9d8b8e` | s604_script_gap_20261109 | S604_SCRIPT_GAP.md | S0 | `DOC=wd/'S604_SCRIPT_GAP.md';SHA='MISSING'` | 是 | `主件缺失 S604_SCRIPT_GAP.md（写域=s604_script_gap_20261109）` | `—` |
| 30 | `dcda8414` | s604_script_hunt_20261109 | S604_SCRIPT_HUNT.md | S0 | `DOC=wd/'S604_SCRIPT_HUNT.md';SHA='MISSING'` | 是 | `主件缺失 S604_SCRIPT_HUNT.md（写域=s604_script_hunt_20261109）` | `—` |
| 31 | `cd88a9f5` | samedoc_link_20261109 | SAMEDOC_LINK.md | S0 | `DOC=wd/'SAMEDOC_LINK.md';SHA='MISSING'` | 是 | `主件缺失 SAMEDOC_LINK.md（写域=samedoc_link_20261109）` | `mods=[]` |
| 32 | `15585c14` | strict_exposure_20261109 | STRICT_EXPOSURE.md | S0 | `DOC=wd/'STRICT_EXPOSURE.md';SHA='MISSING'` | 是 | `主件缺失 STRICT_EXPOSURE.md（写域=strict_exposure_20261109）` | `—` |
| 33 | `53714984` | text_fix_unified_20261109 | UNIFIED_TEXT_FIX.md | S0 | `DOC=wd/'UNIFIED_TEXT_FIX.md';SHA='MISSING'` | 是 | `主件缺失 UNIFIED_TEXT_FIX.md（写域=text_fix_unified_20261109）` | `—` |
| 34 | `802eb959` | u5u6_mirror_20261109 | U5U6_MIRROR_TEXTS.md | S0 | `DOC=wd/'U5U6_MIRROR_TEXTS.md';SHA='MISSING'` | 是 | `主件缺失 U5U6_MIRROR_TEXTS.md（写域=u5u6_mirror_20261109）` | `—` |
| 35 | `f123d326` | v2_precision_fix_20261108 | V2_PRECISION_FIX_PROPOSAL.md | S0 | `DOC=wd/'V2_PRECISION_FIX_PROPOSAL.md';SHA='MISSING'` | 是 | `主件缺失 V2_PRECISION_FIX_PROPOSAL.md（写域=v2_precision_fix_20261108）` | `—` |
| 36 | `27d477b1` | w2_samecause_20261109 | W2_SAME_CAUSE.md | S0 | `DOC=wd/'W2_SAME_CAUSE.md';SHA='MISSING'` | 是 | `主件缺失 W2_SAME_CAUSE.md（写域=w2_samecause_20261109）` | `—` |

**逐处改法示例（#7 完整对照，可独立验证）**：改前为 §2.3 S0 五行；改后：
```javascript
    "DOC=wd/'COUNTERPART_FIX.md';SHA='MISSING'",
    "if not DOC.is_file(): P.append('主件缺失 COUNTERPART_FIX.md（写域='+wd.name+'）')",
    "else:",
    " raw=DOC.read_bytes();NB=len(raw);SHA=hashlib.sha256(raw).hexdigest()",
    " t=raw.decode('utf-8',errors='replace')",
```
print 行 `'problems':P,` → `'problems':P,'docSha256':SHA,`。两处 CAND 变体（#9 / #22）**同样整段 5 行删掉即可**，`startswith('CANDIDATE_RESIGN')` / `startswith('GATE_FALSE_POSITIVE')` 名字前缀过滤不再需要。

**每处独立验证（本会话 36/36 实跑，`_dnw_template.py`）**：替换后断言 `DOC=max(` 归零、显式名到位、`if not DOC.is_file()` 到位、`hashlib.sha256(raw)` 到位、Python 源码 `compile()` 通过；再把主件临时改名（沙盒副本、不动历史）应得合法 `ok=false` + `主件缺失 <MAIN>` + `SHA='MISSING'`。结果 `sites=36, compile_ok=36, present_doc_is_main=36, absent_ok_false=36, absent_has_missing_msg=36, absent_shaMISSING=36, absent_no_error=36, all_checks_pass=true`（`lead/gate_doc_name_fix_20261109/_dnw_template_out.json`）。

**「已交付」与「找不到主件名怎么办」**：36/36 主件 `os.path.isfile` 实测**已交付**（现值），名字来源 33 处 `const DOC=` + 3 处【交付】文本（#13–15），0 个 NOT_DETERMINABLE。通用规则（若别处找不到）：自检给 **WEAK**（无 `_` 前缀 md 恰一）只告警、**不自动采用**；`NOT_DETERMINABLE` 一律不发、**严禁回退 `max` / `mtime` / `sorted-first` 任一启发式**；由派发方补 `const DOC=` 重发。本批 36/36 都找得到，无需走此分支。

**S1/S2 前缀过滤的现实核对（复核意见第 3 条）**：本会话实跑核查现域匹配数——`n4_yi_final_20261108` 的 `startswith('CANDIDATE_RESIGN')` 只匹配 1 件 `CANDIDATE_RESIGN_YES_V2.md`；`gate_fp7_20261108` 的 `startswith('GATE_FALSE_POSITIVE')` 只匹配 1 件 `GATE_FALSE_POSITIVE_5_6_7.md`。故这两处 `max` 在单元素上取、**无大小竞争**。被核件 `_dn_glm_final.md:256` 把 `n4_yi_final` 以「+5768B 中稿」列为 P0 尺寸依据对该门不适用；其 P0 结论可保留，但依据须改为「终稿补跑 4 项内容提示 + 约定名压根没进门禁」，见 §5.2。

### 4.2 回归验证设计之一：可复用自检脚本（主件名可确定性）

`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_doc_name_fix_20261109\_dn_gate_selfcheck.py lead/<域>/`（亲读 `:32-81` 判定序）：①最新 payload 的 `expected=` / `const DOC=` / `doc=root/` 显式名（强）→ ②任务书【交付】段 `X.md`（次强）→ ③域内无 `_` 前缀 md 恰一（**WEAK 仅告警**）→ 否则 `NOT_DETERMINABLE`。

本会话实跑 32 域全量：`domains_count=32`、`verdicts={'DETERMINABLE(主件在场)':32}`、`sources={payload门禁显式命名:31, payload任务书【交付】指示:1}`、`NOT_DETERMINABLE_domains=[]`；空域对照给 `NOT_DETERMINABLE`。**已登记瑕疵（未改前序脚本）**：`:56` 用 `DEFECT_RE.search(text)` 搜整个 mjs，会把任务书【背景】引用文本误计——本任务域被报 `gate_has_docmax=true` 但实为 Gen-3 显式门禁；本会话 `_dnw_verify.py` 已改「只在 GATE_CODE 块内」口径。

**32 域显式命名补跑（对已交付件的补救演示）**：`python -I -X utf8 …\_dn_regate_domains.py > …\_dnw_regate_rerun.txt`（本会话实跑，exit 0）→ `lead/gate_doc_name_fix_20261109/_dn_regate_out.json`：`rows=32, full_pass=19, with_hints=13, unparsed_total=0, mainIsLargest_false` 恰 2 域（`counterpart_fix_20261109`、`n4_yi_final_20261108`）。13 个提示域 = c07_gate_audit / c07_protocol_attacks / c07_slot / c07_truth_protocol / ledger_appendix / matrix_ab_ruling / matrix_reach / n10c04_ruling / n11_wording_fix / n4_yi_final / s604_attribution / s604_script_gap / s604_script_hunt。未纳入：台账漂移段、门禁一次性复合条件、门禁时刻字节态（§5.4）。

### 4.3 回归验证设计之二：S1-S4 方法（S1–S4 四场景）

夹具与脚本全部在本写域复刻：旧门禁复刻 `lead/gate_doc_name_fix_20261109/_dn_gate_gen2.py:24`（`max` 选择，检查项与方案 A 完全一致），方案 A `_dn_gate_planA.py:18-24`（显式命名 + 缺失即 FAIL + 同次 `read_bytes` 算 sha256）。本会话独立重跑 `python -I -X utf8 …\_dnw_s1s4.py`（自构夹具 + 自实现两套门禁，同进程无子进程）→ `lead/gate_doc_name_fix_20261109/_dnw_s1s4_out.json`：

| 场景 | Gen-2(max 猜大) | 方案A(加固版) | 本会话 match |
|:--|:--|:--|:-:|
| S1 正常（仅主件齐要素） | `ok=True doc=MAIN.md` | `ok=True doc=MAIN.md`（无误伤） | ✓ |
| **S2** 违禁词藏主件、侧件更大更干净 | **`ok=True doc=_side_big.md`（绕过）** | `ok=False doc=MAIN.md`，`含越界断言 已改台账` | ✓ |
| **S3** 主件缺要素、中稿补齐更大 | **`ok=True doc=_mid_complete.md`（误判通过）** | `ok=False doc=MAIN.md`，`缺小节 ## 3；缺要素 未验` | ✓ |
| S4 主件缺失、侧件在场 | **`ok=True doc=_only_side.md`（顶替）** | `ok=False`，`主件缺失 MAIN.md（写域=S4）` | ✓ |

`all_four_match=true`。附加边界探针 S5（双 bare 件、坏的更大）/ S6（同字节并列、max 退化为排序取首）：Gen-2 分别读 `OTHER_BIGGER.md` / `AAA_SAME.md` 且 FAIL，方案 A 均 `ok=true doc=MAIN.md`。诊断件夹具 `lead/gate_subject_id_20261109/_si_exploit_out.txt:10-20` 记 S1_repro / S2_smuggle / S3_mask / S4a / S4b 五场景，与本表同构。

### 4.4 如何证明 S2/S3 不再有（如实：必要回归，非充分证明）

- **机制**：S2 / S3 / S4 全部攻击路径要求「被核对象 ≠ 约定主件」。方案 A 把 `DOC` 钉死为 `wd/'<MAIN>'`，`max` / `cands` / size / mtime / sorted-first 全部不参与选择；缺要素、违禁词、缺失分别由原检查行、禁词行、`DOC.is_file()` 在**主件本体**上 FAIL。
- **差分实证**：同一套检查项仅选择段不同，三条旧 PASS 全变 FAIL 且 problems 指向主件；S1 双 PASS 证明无误伤（§4.3）。
- **逐处实证**：36/36 内存替换后 `DOC=max(` 归零、显式名与 sha256 到位、`compile()` 通过、主件在场/缺失两态各 36/36（§4.1、`_dnw_template_out.json` 的 `all_checks_pass=true`）。
- **★ 复核意见第 2 条的诚实边界**：S1–S4 只证明「该模板 + 该夹具」的差分行为，**不能证明「不再有 S2/S3 漏洞」的全部面**。反例就是 §3.3 的 6 处 `NameError`——四场景的 print 行无附加变量，测不出该漏洞面。故本件把**逐处模板实例化 + 缺失态验证**列为与 S1–S4 并列的必备回归项，并把「四场景全绿才可上线」表述限定为**必要条件**；被核件 `_dn_glm_final.md:219-225` 的「机制证明 / 全绿才可上线 / 不再有 S2/S3」属过强表述，据复核记为 **unconfirmed**（§5.1）。
- **边界声明**：以上证明的是「§3 加固模板 + 本写域夹具 + 32 域主件名」组合；**未在真实历史 payload 上落地运行**（纪律禁止改历史），故不对历史 36 发当时实跑输出作断言。

---

## 5 复核回件（绑定行）+ 欠账清单与优先级 + 声明 + 未验项

### 5.1 复核回件：verdict 如实记 + 绑定行

**verdict = partial（复核方回件，标 unconfirmed，非 confirmed）。** 三条实据（本会话全部独立复现，见各条命令）：

1. **模板「主件缺失即 FAIL」在原始印刷版 6/36 处不成立**：`_dnw_noharden.py` → `absent_ok_false=30/36`、6 处 `NameError`（`mods`/`rows`/`rd`）；`_dnw_template.py` 加固后 → `absent_ok_false=36/36`、`all_checks_pass=true`。本件 §3.1/§3.3 **已吸收**：模板改为加固版。被核件 `_dn_glm_final.md:109`「缺失即 ok=false」、`:183`「36/36 每处独立可验证」对原始印刷版为假——**unconfirmed**。
2. **S1–S4 是必要回归而非充分证明**：`_dnw_s1s4.py` → `all_four_match=true`（S1 双 PASS、S2/S3/S4 旧 PASS 新 FAIL），但 6 处 `NameError` 恰是四场景未覆盖的漏洞面。被核件 `_dn_glm_final.md:219-225`「机制证明 / 全绿才可上线」过强——**unconfirmed**；本件 §4.4 已限定。
3. **欠账补救与优先级两处须澄清**：① 忠实还原 counterpart 原始门禁 `python -I -X utf8 …\_dnv_replay\replay_dwfrun-636adfc5-7ca1.py`（本会话实跑）→ `{"ok": false, "problems": ["缺「变ORPHAN不等于解决」声明", …], "docBytes": 32840, "doc": "_cf_counterpart_vs_tighten_20261109.md"}`，复现 `_si_exploit_out.txt:4` 与 `GATE_SUBJECT_ID_FIX.md:101`；**方案 A 对当前主件重放只能验当前主件质量，不能发现历史误判**，能发现的是「原门禁重放」或「存档的门禁 stdout」（后者不存在，35 处未验）。② CAND 两变体现域各仅 1 匹配文件（§4.1 末段），`+5768B` 尺寸依据对 `n4_yi_final` 门不适用，P0 结论保留、依据改写。

**已确认项（不得误读为 refuted）**：36 这个数字核实无误（36 处 / 32 域）、八件上游指纹 8/8、被核主报告现值相符、51 个安全实例 0 在缺陷集合、32 域自检 32/32 DETERMINABLE、32 域补跑 19 全过 / 13 提示、`git log -1` = `2657458`（未变）、`git status --short` 仅 `?? lead/gate_doc_name_fix_20261109/` 等既有未跟踪态。

**绑定行**（格式固定：「被核对象 SHA256 = 」紧跟完整 64 位十六进制，中间无任何路径/括号/星号/反引号/空格；随后「，字节数 = 」+ 数字。八件上游指纹，本会话 hashlib 实算 8/8 与派发常量一致；末行为被核主报告现值）：

```
被核对象 SHA256 = 302a45644359f14d4f420225ac56784579a658cb852a0b0df0ddde6532adf63c，字节数 = 31692
被核对象 SHA256 = 8c67dc3fc950baf16e4e39b650ca25210e24e3512307a09eaf30cc9cecd6f4dc，字节数 = 23441
被核对象 SHA256 = 54751e9a10bca4becfae3449d4a19155dc7744dff77a8a22d7d70d9a7fd70eee，字节数 = 2850
被核对象 SHA256 = c8024cb7e538dfbc3766acc08d231789b80d601d7cc4bba4e05ed89d8ff87d94，字节数 = 611043
被核对象 SHA256 = e326df6b4040dc9e5471f891c8db55d8ede1681434336de5e5626c43e2029f52，字节数 = 180256
被核对象 SHA256 = 151f4f94b890403ba4785a7d570ad11abbe68a4aa12363967682729167e2c587，字节数 = 5717
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = c977e3ca88f7963e751087811fc37409a7497d136b30a7686ff35b7160224d05，字节数 = 31453
```

（顺序同上表八件；第 9 行 = 被核主报告 `lead/gate_doc_name_fix_20261109/_dn_glm_final.md`。）

### 5.2 欠账清单与优先级（哪些域最危险 / 已交付域怎么补救）

危险度按「有中间稿且大小接近主件 / 结构性无主件 / 约定名不在门禁里」排序。36/36 主件现值均已交付，故全部只登记欠账、不改历史。时序限制如实：本会话实跑 `run mtime vs 主件 mtime` → `36/36 run_mtime < main_mtime`，mtime 是派发时刻非门禁实跑时刻，**不能复原当时读了谁**；除 counterpart 有忠实还原重放实锤外，其余 35 处「当时是否误判」标未验，按结构性暴露登记。

| 优先级 | 域 | 依据（本会话实跑 / 文件:行） | 补救动作 |
|:-:|:--|:--|:--|
| **P0** | counterpart_fix_20261109 | 中稿 32840B vs 主件 32830B，差 +10B；`replay_dwfrun-636adfc5-7ca1.py` 实锤旧门禁读了中稿并报「缺声明」；`GATE_SUBJECT_ID_FIX.md:44` | 保留忠实重放证据；对当前主件按显式名重跑（本会话 32 域补跑全过、bind 合格），登记台账 |
| **P0** | n4_yi_final_20261108 | 终稿补跑 4 项提示（缺要素 不签 APPROVE_SCOPE / 含越界断言 可应用母本 / 放行 N-5 / 缺规范格式绑定行）；依据为**内容提示 + 约定名压根没进门禁**（非 +5768B 尺寸，见 §4.1 末段）；bare>1 | 重发一发补验任务或人工重签；CAND 前缀过滤门无大小竞争，尺寸依据作废 |
| **P1** | handoff_pack_20261109 / s604_script_hunt_20261109 | 诊断时点结构性无主件（`GATE_SUBJECT_ID_FIX.md:55-56`），现值主件已最大——时点漂移证据 | 按显式名 + 绑定行重跑；登记「诊断时点 vs 现值」漂移 |
| **P1** | ledger_appendix_20261108 | 3 发同域、唯一无 `const DOC=`（名字只在【交付】文本）；补跑提示 已生效 + 缺绑定行 | 补 `const DOC=` 约定 + 显式名门禁 + 绑定行 |
| **P1** | 13 个提示域 | 见 §4.2 清单（c07_gate_audit / c07_protocol_attacks / c07_slot / c07_truth_protocol / ledger_appendix / matrix_ab_ruling / matrix_reach / n10c04_ruling / n11_wording_fix / n4_yi_final / s604_attribution / s604_script_gap / s604_script_hunt） | 人工分诊要素词 / 断言词语境，真缺则补节、补绑定行 |
| **P2** | 其余 27 域 | 现值中稿−主件差全为负（−3418 ~ −33912B，`_dn_glm_36_list.json`），机制缺陷相同 | 从下一发收敛（§3.5 迁移路径）；现值无需逐域返工 |

**已交付域的补救（历史 payload 不可改）**：① 36 处历史 payload 一律保持原字节；② 对已交付件**按显式主件重跑门禁**（本会话 32 域演示，§4.2）——但须注意复核意见第 3 条：这只能验当前主件质量，**不能发现历史误判**；发现历史误判要靠「原门禁忠实还原重放」（counterpart 已演示）；③ 对 §5.2 清单逐域重发一发小任务（门禁 = §3.1 加固模板实例化 + 补绑定行），产出存新写域并登记台账；④ 生成器侧固化模板 + 禁用 token + `<ELSE_ONLY_VARS>` 自动推导 + §3.5 五条迁移规则。

### 5.3 未改历史 payload 声明

本会话对历史一律只读：`lead/gate_subject_id_20261109/` 全部件、`.zcode/workflow-runs/` 全部 mjs（225 个只 read）、`lead/` 下全部历史写域、两件台账，均未写未删未动。现值证明：①八件上游指纹本会话 hashlib 实算 8/8 与派发常量相符（§2.1）；②`git log -1 --oneline` = `2657458`（未变），`git status --short` 中 `MM lead/PENDING_DECISIONS.md` / `MM lead/GOAL_THREE_TARGETS_20261018.md` 为会话开始 gitStatus 快照既有的 `MM` 态，本会话未触碰；③本会话落盘**全部**在唯一写域 `lead/gate_doc_name_fix_20261109/`，前缀 `_dnw_*`（脚本 / 快照 / 沙盒副本）+ 本主件 `GATE_DOC_NAME_FIX.md`。**未改历史 payload**、未改诊断域件、未 commit、未 push；零真机、零采样代码；Python 一律 `python -I -X utf8` + 绝对路径，指纹用 hashlib。模板未在真实历史 payload 上落地运行（纪律禁止）——此步属欠账而非本轮可执行项。

### 5.4 未验项（如实申报）

1. 35 处门禁**当时**的实跑输出（exit / problems / 读了谁）不可复原、未逐发断言；时序 36/36 `run_mtime < main_mtime` 只证明派发时刻早于主件落盘，不能反推门禁读了谁。
2. `121 个多主件域`（方案 B 误伤数，`GATE_SUBJECT_ID_FIX.md:134-146`）、`d13d14 差 2950B` / `direction_ruling 差 4428B`、`13 提示域断言词的否定/引述语境分诊`：本会话**未独立复算**。
3. 台账漂移段（PRE 指纹为运行期值、台账合法追加后必假阳）与门禁一次性复合条件**未纳入** 32 域补跑。
4. `n4_yi_final` 门禁时刻是否另有第二个 `CANDIDATE_RESIGN*` 文件不可复原；现域只 1 匹配为**现值**。
5. 「51 个安全实例 / 38 全文件字面 / 2 噪音」为 **225 mjs 时点值**；工作区是活的，下游引用前须按 `_dnw_verify.py` 口径重扫。
6. 加固模板**未在真实历史 payload 上落地运行**（纪律禁止改历史）；`_dnw_template.py` / `_dnw_noharden.py` / `_dnw_s1s4.py` 的验证均在内存还原 + 本写域沙盒副本上完成，不等价于上线后的真实派发回归。
7. 复核 verdict=partial 的三条中，第 2 条「四场景不充分」本会话以 §4.4 的诚实边界 + 6 处 NameError 复现为据；未做比 S1–S6 更广的攻击者能力建模，故「不再有 S2/S3 漏洞」仍标 **unconfirmed**（§4.4、§5.1）。

---

**本会话实跑命令一览（全部 `python -I -X utf8` + 绝对路径，或 git/文件只读）**：
`_dnw_verify.py`（八件指纹 8/8 + 225 mjs 重扫）、`_dnw_template.py`（36 处加固模板 compile + 两态）、`_dnw_noharden.py`（6/36 NameError 复现）、`_dnw_s1s4.py`（S1–S6）、`_dn_gate_selfcheck.py <32 域>`（32/32 DETERMINABLE）、`_dn_regate_domains.py`（32 域补跑 19/13）、`_dnv_replay\replay_dwfrun-636adfc5-7ca1.py`（counterpart 忠实重放）、内联 `CAND 前缀过滤现域匹配数` 与 `run/main mtime 时序`、`git status --short` / `git log -1 --oneline`。产出快照：`_dnw_verify_out.json`、`_dnw_template_out.json`、`_dnw_noharden_out.json`、`_dnw_s1s4_out.json`、`_dnw_regate_rerun.txt`、`_dnw_table36.txt`。

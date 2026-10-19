# W3-CS5 派工单 · DOC1 级联收尾：YR 侧指纹括号化 + _caliber 窗口截断修复

> 派发：2026-10-02 20:5x（Lead）· 前置：**DOC1 已验收（7/7，§476）** · **REG1 已验收（§481，39 红逐条归因 §4）**
> 执行：WorkBuddy（新会话）· 预估 40–70 分钟
> 依据：REG1_REPORT §4 的 DOC1 级联族红项 —— **DOC1 往 YR 侧 ATLAS 追加勘误（+87 行，sha e41bb738→f939d6e3，19:14:55）后，一批钉旧指纹/固定窗口的验证器变红**

## 点名清单（REG1 实测，只查不改 → 本卡按三律改）

| # | 验证器 | 红因 |
|---|---|---|
| 1 | `agy/.../landing/verify_landing.py` | YR ATLAS sha `e41bb738…` → `f939d6e3…` 钉旧值 |
| 2 | `agy/.../docs_landing/verify_docs_landing.py` | 同族（docs 侧落位钉旧） |
| 3 | `qc/.../m7_crosscheck/verify_crosscheck.py` | 同族 |
| 4 | `qc/.../scripts/verify_m11_landing.py` | 同族 |
| 5 | `qc/.../runs_superseded/verify_m11_landing.v1_005930.py` | 历史已取代版本 —— **只判不改**（先定它是否还需要活） |
| 6–8 | `qc/.../_caliber/` 三件（verify_caliber_chain_v2 / v3 / verify_caliber_edits） | **UnicodeDecodeError**：ai_team 块 268→803 行，验证器按固定窗口/固定行号读块，多字节字符中间截断崩溃 |

## 任务

1. **逐件复现红态**（先记录当前 EXIT 与失败原文 —— 若此刻已绿，如实报"REG1 后已自愈"，不许硬造红）。
2. **按"改已验收验证器"三律修**：
   - ① 只动点名断言/读取逻辑；② **新断言必须更强**：YR ATLAS 指纹一律 **pre/post 双括**（pre=`e41bb738…/455,987B? 以实测为准——DOC1 改前值必须从 DOC1 的快照件取证`，post=`f939d6e3…/470,294B/19:14:55`）+ 前缀逐字节可还原断言（DOC1 是 +87/-0 插入式，见 verify_doc1 的 inserted=87 deleted=0）；`_caliber` 三件把固定窗口读块改为**结构定位**（按块标记找边界，不再按行号/固定字节窗），并加"截断检测"断言（读到多字节中间 ⇒ 显式 FAIL 而非崩）；③ 改后仍红即回滚该文件。
   - **负控 ≥2**：副本把 post 括号改错一位 ⇒ 必须 FAIL 且指向该断言；副本模拟"块边界移动"（ai_team 块再长/缩短）⇒ 结构定位必须仍读全，固定窗口旧法对照必须崩（证明修复承重）。
3. **第 5 项（已取代历史版本）单独裁**：若它是 runs_superseded 的留档快照 ⇒ **不改**（在报告里登记"历史版本已死，REG1 计红属预期"）；若仍被谁 import ⇒ 改并说明。
4. **收尾全绿**：本清单中被改的每个验证器 EXIT=0；REG1 抽跑复核（至少 #1 与 #6）稳定；原改动前快照/diff 全留档。
5. **顺带**（只查不改，写进报告）：REG1 归因族里 `verify_sem1`（S3/SEM1B 追加）、`verify_m39r`（自证断言冲突）、`verify_matrix/verify_mp`（记录 2≠物理 3）各给出"该谁修、动什么"的一句话裁案，供 Lead 排下一张卡。

## 铁律

- **写域仅**：上表点名验证器文件（第 5 项视裁定）+ `out/re_work/workbuddy/W3_20261002/cs5_doc1_cascade/`（报告/快照/负控）。
- **ATLAS 两份、docs/**、coverage_ledger、dispatch 台账、其余 280 个验证器全部只读**；tools/ 零写入。
- 空扫描 = INSTRUMENT_FAILED；拿不准停手报备；证据现读现抄。

## 交付

`out/re_work/workbuddy/W3_20261002/cs5_doc1_cascade/`：`CS5_REPORT.md` + `verify_cs5.py`（正控=点名前后断言、负控必咬）+ 快照/diff/负控原文。完成后回报 `[0]`：逐件 before/after EXIT 表 + verdict tally 原文。

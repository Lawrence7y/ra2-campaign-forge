# 检测结果分诊与处置建议（_dt_REPORT.md）

**执行者**：检测分诊员（subagent，工作流一问一答） · **日期** 2026-11-09
**性质**：**只做分诊与建议**。不改任何被检脚本、不执行重跑、不改台账、不加注。
**唯一写域**：`lead/detect_triage_20261109/`，本件及全部脚本/输出前缀 `_dt_`。
**铁律**：零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`、未 `taskkill`、未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入、未写动态内存解析）。未 commit、未 push。Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib`。
**绝对只读域复核**：本会话 `git status --short -- lead/k1bit_detect_20261109/ lead/stale_pass_20261109/ lead/d27_ruling_20261106/ lead/d28_ruling_20261106/ lead/d29_ruling_20261106/ lead/d30_ruling_20261106/` 全为 `??`（未跟踪、未改）；`git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`。两件台账指纹与编排方给入值逐字符相符（见 §0）。

---

## 0 编排方指纹复核（本会话 `hashlib` 独立实算）

**实跑命令**：
```
python -I -X utf8 -c "
import hashlib,json,os
paths=['lead/k1bit_detect_20261109/_kd_detect_out.json', ... 共 7 件]
for p in paths:
    b=open(p,'rb').read(); print(p, hashlib.sha256(b).hexdigest(), len(b))
"
```
**输出**（7/7 与编排方【编排方实跑指纹】完全一致）：

| 文件 | SHA256 | 字节数 |
|---|---|---|
| `lead/k1bit_detect_20261109/_kd_detect_out.json` | `00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239` | 251854 |
| `lead/k1bit_detect_20261109/K1BIT_DETECTOR.md` | `40d79857bebc28fb1dd1d2f03afc7f1dc825b4b9cf9a56e55a0a93179ca32ad1` | 60565 |
| `lead/k1bit_detect_20261109/_kd_literal_vs_semantic_out.json` | `af84560f288a0f74cac5f9f1f95f64f68c767e8a0aee32e869d1b0fc2ab9cc2f` | 39990 |
| `lead/check_family_20261109/_cf_detect_out.json` | `17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2` | 130498 |
| `lead/stale_pass_20261109/STALE_PASS_INVENTORY.md` | `a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798` | 63656 |
| `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

---

## 1 第一步：复核检测结果（独立重跑，非只读 JSON）

**方法**：写 `_dt_repro.py`（本写域），以 `importlib.util.spec_from_file_location` 只导入 `_kd_detect.py` 的 `analyse()`、`_kd_selftest.py` 的 `FIX` 常量、`_cf_detect.py`（三者均有 `if __name__ == "__main__"` 守卫，`_kd_detect.py:529`、`_kd_selftest.py:188`、`_cf_detect.py:163`），在**内存里**对 173 件原始字节重跑判据；重新实现三种字面筛；结果只写 `_dt_repro_out.json`（本写域）。**未调用被检脚本的 `main()`，未运行任何门禁，未做动态坏针注入。**

**实跑命令**：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/detect_triage_20261109/_dt_repro.py D:/Project/ra2-campaign-forge
```
**输出**（`_dt_repro_out.json`）：

| 项 | 结果 |
|---|---|
| (a) `n=173` / `CONFIRMED_K1BIT=40` / `SUSPECT=6` / `LEGAL_AGGREGATE=80` / `NO_SELFTEST=47` | **复现**；`matches_frozen_counts=True`、`verdicts_match_frozen_rows=True`、`sha_match_frozen_rows=True`（逐件 SHA256 也与冻结 rows 全等） |
| (b) 与 `_cf_detect_out.json` 逐件一致 | **复现**；`frozen_kd_vs_frozen_cf=True`、`refound_vs_frozen_cf=True`、`cf_only=[]`、`kd_only=[]`。附注：`_cf_detect_out.json` 自报 `suspect=3`，`_kd_detect_out.json` 自报 `suspect=6`，两器的 **confirmed 集合**相同，suspect 口径不同（见 §4(d)） |
| (c) 自检 10/10 与 N5 | **复现**；`n=10 passed=10 failed=0`、`all_negatives_correct=True`、`all_positives_correct=True`，10 件 `matches_frozen` 全 `True`。N5 `want=LEGAL_AGGREGATE got=LEGAL_AGGREGATE`、`has_k=False`、`collapse=['OR_COLLAPSE_gen']`、`hits_retained` 三处（`_kd_selftest_out.json` N5 行 `:4/:6/:7`）；P1 同为 `OR_COLLAPSE_gen` 但 `hits_retained=[]` → `CONFIRMED_K1BIT`。**同一个 OR 塌缩，有逐 token 归因即合法、无归因即缺陷——分界线成立** |
| (d) 宽口径零漏 / 窄口径漏 4 | **复现**；`L1_GENERATOR_FORM n_hits=49 tp=36 fn=4 fp=13`、`L2_ORCH_ANY_LINE n_hits=48 tp=36 fn=4 fp=12`、`L3_BROAD_ANY_PASS n_hits=54 tp=40 fn=0 fp=14`；L1/L2 的 4 个 FN 逐字为 `[d28 生产件 + 3 件 d28 沙箱副本]`，L3 `misses=[]`。`matches_frozen_screens=True`、`four` 表 d27/d29/d30 三口径全 True、d28 仅 L3 True |

**口径订正（本会话实读 `lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md:336`）**：该行已把「字面 `any()`+PASS 筛会漏掉 d28/d27」标 **unconfirmed**，理由为通用宽口径下四件全命中（54 件、零漏判）。编排方上一轮「字面筛必然漏 d28/d27」为**过宽**：只有生成器式/窄口径才漏 4 件，且漏的是 d28 模板（含 3 沙箱副本），**不是 d27**。本件不改写该结论。

---

## 2 第二步：40 件四级分级（本任务核心）

### 2(a) 生产件 vs 沙箱/审计副本

**实跑命令**：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/detect_triage_20261109/_dt_triage.py D:/Project/ra2-campaign-forge
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/detect_triage_20261109/_dt_scope.py D:/Project/ra2-campaign-forge
```
**输出**：`n_confirmed=40`，生产件 **4**、沙箱 **36**；沙箱分组 `_cm_tmp=22` / `_cmv_tmp=5` / `_sp_sandbox=9`，与编排方【40 件分诊】给入的划分、分组统计逐项相符（`_dt_scope_out.json:sandbox_in_ledgers`、`_dt_triage_out.json:group_counts`）。

**沙箱不构成风险的依据（本会话实跑，非推断）**：
- `_dt_scope_out.json:sandbox_in_ledgers` = `n_sandbox=36`、`n_full_rel_cited=0`、`cited=[]` ⇒ 36 件沙箱副本的**完整路径**在两件台账中 0 行引用。
- 逐名扫描 6 份参考文档（`CHECK_MASKING_INJECT.md` / `STALE_PASS_INVENTORY.md` / `K1BIT_DETECTOR.md` / `CHECK_FAMILY_LINEAGE.md` / 两账）：36 件沙箱只在 `CHECK_FAMILY_LINEAGE.md` 被以「清单/谱系」身份列名，**没有一件**的 PASS 被登记为「已验证」结论。
- 编排方【40 件分诊】本身即把 4 件 `lead/d2[789]_ruling_20261106/check_d*.py` 与 `lead/d30_ruling_20261106/check_d30.py` 定为 production；本会话逐件比对一致。
- `lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md:338` 亦自述「40 件是 AST 静态结构命中，其中 13 件是 `_cm_tmp`/`_cmv_tmp`/`_sp_sandbox` 里已注入坏针的副本……『全库 40 件都带同一缺陷代码』不成立」。

### 2(b) 生产件再分：有台账登记 / 无登记 / 只在交付件被引用

**实跑**（`_dt_scope_out.json:ledger_citations`、`_dt_triage_out.json:prod_check`）：对两件台账逐行按门禁 basename 扫描，命中如下（逐字原文见 `_dt_scope_out.json:pending_lines_verbatim`）：

| 生产件 | 裁决 | PENDING 行 | 逐字摘要 | GOAL 行 | 覆盖裁决 |
|---|---|---|---|---|---|
| `lead/d27_ruling_20261106/check_d27.py` | D-27 | `PENDING_DECISIONS.md:129` | 门禁 `check_d27.py` 实跑 **exit=0** | 0 行 | **是**（该行位于「已裁决记录」段，`PENDING_DECISIONS.md:88` 起；同条 `:127` 为 D-27 裁决正文） |
| `lead/d28_ruling_20261106/check_d28.py` | D-28 | `PENDING_DECISIONS.md:117` | 门禁 `check_d28.py` 实跑 **exit=0** | 0 行 | **是**（`:115` 为 D-28 裁决正文） |
| `lead/d29_ruling_20261106/check_d29.py` | D-29 | `PENDING_DECISIONS.md:105` | 门禁 `check_d29.py` 实跑 **exit=0** | 0 行 | **是**（`:103` 为 D-29 裁决正文） |
| `lead/d30_ruling_20261106/check_d30.py` | D-30 | `PENDING_DECISIONS.md:92` | 门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS） | 0 行 | **是**（`:90` 为 D-30 裁决正文） |

四件 SHA256/字节数与上游登记值逐字符相符（`_dt_triage_out.json:prod_check`：d27 `3b769d7c…7671c`/3764、d28 `5b42a34a…d268`/4539、d29 `2a50b09a…780f14`/3906、d30 `6cb73796…5ee9fd`/3926；登记见 `lead/stale_pass_20261109/STALE_PASS_INVENTORY.md:44-46,69` 与 `lead/check_family_20261109/_cf_census.py:36-39`）。

- **有台账登记（其 PASS 已被引用）**：**4 件**，全部位于 `PENDING_DECISIONS.md` 的「已裁决记录」段，且各自包裹一条 D-27..D-30 裁决 ⇒ **覆盖裁决**。
- **无登记的生产件**：**0 件**（在本次 40 件内）。
- **只在交付件被引用的生产件**：**0 件**（在本次 40 件内）。★ 但存在一件**同类且已被引用的生产脚本不在 40 件内**：`lead/refsync_scope_20261109/_rs_carrier_scan.py`，其 `SELF_TEST = PASS` 只登记在绝对只读交付件 `REFSYNC_SCOPE_FIX.md:251/:252/:253`（`STALE_PASS_INVENTORY.md:57,67,107,130-132` 记为 A+B 级），两台账 0 行提及。详见 §3(d)——这是本任务「查漏检」最重要的发现。

### 2(c) 四级定义与计数表

| 级 | 判据（本任务给入） | 处置 | 件数 |
|---|---|---|---|
| **A** | 生产 + 有台账登记 + 覆盖裁决 | 必须重跑 | **4** |
| **B** | 生产 + 有台账登记但不覆盖裁决 | 加注 + 重跑 | **0** |
| **C** | 生产 + 仅交付件引用 | 加注 | **0**（就 40 件而言；范围外 1 件见 §3(d)） |
| **D** | 沙箱/审计副本 | 不动 | **36** |
| | | **合计** | **40** |

分组计数：`A=4`（d27/d28/d29/d30 生产门禁）；`D=36`（`_cm_tmp` 22 + `_cmv_tmp` 5 + `_sp_sandbox` 9）。`B=0`、`C=0` 不是漏判，是**这 40 件的引用结构决定的**：四件生产门禁的台账登记行全部同时是裁决条目行，不存在「登记但不覆盖裁决」或「仅交付件引用」的中间态。

### 2(d) 逐件归类表（40 行）

完整 40 行表落盘 `lead/detect_triage_20261109/_dt_table.md`（含逐件 SHA256 前 16 位、字节数、级、组、台账行、备注）；机器可读全量含完整 64 位 SHA256 的逐件记录见 `_dt_triage_out.json:rows`。摘要：

| 级 | 件数 | 路径 |
|---|---|---|
| **A** | 4 | `lead/d27_ruling_20261106/check_d27.py`（PENDING:129）、`lead/d28_ruling_20261106/check_d28.py`（PENDING:117）、`lead/d29_ruling_20261106/check_d29.py`（PENDING:105）、`lead/d30_ruling_20261106/check_d30.py`（PENDING:92） |
| **D** | 22 | `lead/check_masking_20261109/_cm_tmp/d27|d29|d30/*`（`_dt_table.md` #1–22） |
| **D** | 5 | `lead/check_masking_20261109/_cmv_tmp/d27|d29|d30/*`（#23–27） |
| **D** | 9 | `lead/stale_pass_20261109/_sp_sandbox/*`（#32–40，含 `d28x/a/b` 两件） |

---

## 3 第三步：「必须重跑」的最小集

### 3(a) A 级 4 件，逐件路径 + 台账行号

| # | 路径 | 台账行号 | 裁决 | 被核对象 SHA256 / 字节数 |
|---|---|---|---|---|
| A1 | `lead/d27_ruling_20261106/check_d27.py` | `lead/PENDING_DECISIONS.md:129` | D-27 | `3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c` / 3764 |
| A2 | `lead/d28_ruling_20261106/check_d28.py` | `lead/PENDING_DECISIONS.md:117` | D-28 | `5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268` / 4539 |
| A3 | `lead/d29_ruling_20261106/check_d29.py` | `lead/PENDING_DECISIONS.md:105` | D-29 | `2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14` / 3906 |
| A4 | `lead/d30_ruling_20261106/check_d30.py` | `lead/PENDING_DECISIONS.md:92` | D-30 | `6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd` / 3926 |

**「覆盖裁决」的准确含义（必须与 `STALE_PASS_INVENTORY.md:143,194-213` 一致，不得夸大）**：四件门禁自述是「格式/机械检查」（`check_d27.py:1` "Read-only D-27 gate"、`check_d28.py:1` "mechanical gate"、`check_d29.py:1`/`check_d30.py:1` "format gate"），实际只查文件存在、`main:`/`q1:` 合法值、7 个必需小节、OR 词表、引用计数 ≥8、`FACTCHECK.md` 含 `selfBias`（`STALE_PASS_INVENTORY.md:196`），**没有任何数值/统计/逻辑断言**；四件裁决书的定谳行（`RULING_D27.md:6`、`RULING_D28.md:4/5`、`RULING_D29.md:4`、`RULING_D30.md:4`）**均不引用 gate**。⇒ 重跑修的是**「已验证」登记行的证据资格 / 格式合规保证**，**不是重审裁决、不是推翻实质结论**。`STALE_PASS_INVENTORY.md:219-220` 独立结论：形式要件失效 7 处 / 实质结论失效 **0 处**（该清点件自身标 `unconfirmed`，见 `:331`）。

### 3(b) 重跑成本估算（每件需什么 / 多久）

**估算依据（均为本会话实读，不冒充实测耗时）**：四件源码 107/122/110/110 行、只读、只读 `RULING_D*.md` + `FACTCHECK.md` 两文件（本会话逐行回读 `check_d27.py:53-100`、`check_d28.py:53-115`、`check_d29.py:49-105`、`check_d30.py:49-105`）；`STALE_PASS_INVENTORY.md:251-263` 的甲' 外壳「逐输入独立跑 + AND_k + 坏针注入」；`lead/stale_pass_20261109/_sp_andk.py:7-40` 与 `_spi_andk_out.txt` 已落盘的 4/4 演示结果（`AND_k(over 2 real per-word runs) = True`、`BAD_NEEDLE_CAUGHT = True`、`DISTINGUISHABLE_PASS = True`）。

| 每件所需 | 明细 |
|---|---|
| 输入 | 对应 `RULING_D*.md` + `FACTCHECK.md`（当前盘、绑 SHA256+字节数）；按 `STALE_PASS_INVENTORY.md:139` 四件文档输入当前未变、不列 B 级 |
| 逐输入运行数 | **k=2 各 1 次**（d27 `("外推","卡顿不存在")` `check_d27.py:84`；d28 `("历史数字","1681")` `check_d28.py:90`；d29 `("互斥","前提")` `check_d29.py:76`；d30 `("93.98","误报率")` `check_d30.py:76`）+ **每根 1 次坏针哨兵** ⇒ 每件 4 次 `python -I -X utf8 <沙箱副本>`，四件共 **16 次**极短只读脚本执行 |
| 前置条件 | ① 先生成 12 份沙箱副本（`_sp_andk.py:7-15` hardcode 12 个 `_w_dNN_[ABS].py`，由 `_sp_gen_word.py` 生成；`STALE_PASS_INVENTORY.md:268` 已自认「它是演示外壳、非可部署门禁」，须先补生成→落盘→驱动序列）；② 三套路径布局不同：`check_d27.py:8` 用 CWD 相对、`check_d29.py:50`/`check_d30.py:50` 用 `__file__.parent`、`check_d28.py:54-55` 用 `parents[2]`，沙箱布局须分别处理（`STALE_PASS_INVENTORY.md:258` 记撰写人第一次漏此点得 6 个 `EXIT=2` 作废重跑）；③ 每次跑绑「被核脚本 SHA256+字节数 + 输入文档指纹 + 命令全文 + stdout 落盘 sha256」（`:261,362`） |
| 唯一写域 | 重跑产物须落**执行方自己的有效写域**；四件目录 `lead/d2[7890]_ruling_20261106/` 在本任务及上游清点中均**绝对只读**，本会话未改 |
| 耗时 | **未验/估算**：门禁是纯文本读 + 正则，单次远小于 1 秒；16 次执行 + 12 份副本生成 + 指纹绑定 + 结果登记，量级为「分钟级（约 10–30 分钟的人工/脚本编排）」。**本会话没有实跑重跑、没有计时输出** ⇒ 不给秒数，标「估算，未验」。无真机、无采样、无网络依赖；唯一显著成本是**编排与口径比对**（`STALE_PASS_INVENTORY.md:267` 记 `--include-refuting` 口径陷阱，照抄会引入第三套口径） |

### 3(c) 只重跑 A 级、B/C/D 全部加注，够不够？

**答：对「40 件」这个集合**——够，但有两点限定；**对「台账里所有已引用的 PASS」**——不够。逐条：

1. `B=0`、`C=0`，故「B/C 全部加注」是**空动作**；`D=36` 沙箱副本按定义是**不动**，给它们加注反而会把审计副本污染成看似生产件（与 `CHECK_FAMILY_LINEAGE.md:338,418` 的警告一致）⇒ 建议 **D 不加注、保持不动**。
2. A 级 4 件必须「**先加注、再重跑**」，不是只重跑：`PENDING:92/105/117/129` 现仍以「实跑 exit=0」身份挂「已验证」（`STALE_PASS_INVENTORY.md:5,228,234-237`）。重跑后应就地加注 `UNTRUSTWORTHY` 并登记「逐输入判定表 + AND_k + 指纹」，**不删原文、不改数字、不撤回裁决**（同 `:228,247-249`）。
3. ★ **不够的地方（本会话实跑发现的漏检）**：
   - **C 级范围外 1 件**：`lead/refsync_scope_20261109/_rs_carrier_scan.py` 的 3 行 PASS 只在交付件 `REFSYNC_SCOPE_FIX.md:251/252/253` 登记，两台账 0 行；`STALE_PASS_INVENTORY.md:107,174,239-241` 判为 **A+B 级 P0**，且 `:170` 实测「正确 AND_k 下应为 FAIL」。它**不在 40 件内**，`_dt_scope_out.json:carrier_one` 显示本会话以 `--one` 重跑 `kd.analyse()` 得 `verdict=CONFIRMED_K1BIT`、`in_confirmed_40=false`、`in_kd_rows_173=false`。若只处置 40 件，这件仍以「已验证」身份留在交付件。⇒ 建议 Leader 单独加注（该件绝对只读，本任务无权改）。
   - **台账同批 C 级 3 行**：`PENDING:162`（`check_d26.py`）、`:186`（`check_d25.py`）、`:199`（N-1 门禁）仍是「门禁 exit=0」句式（`_dt_leak_out.json:registered_not_confirmed` 显示两器都判 `LEGAL_AGGREGATE`，未注射实证 ⇒ `STALE_PASS_INVENTORY.md:133-135,242-244` 定 C 级、建议顺手用同一甲' 外壳定级）。**它们不在 40 件内、不是 A 级**，但若目标是「所有已引用的 PASS 都可信」，只跑 A 级 4 件不够。
4. 判断：**以「40 件分诊」为边界，最小重跑集 = A 级 4 件**；以「失效 PASS 清点」为边界，还须覆盖 1 件交付件引用（C 类）与 3 行台账 C 级（顺手定级）。本任务按纪律**不执行任何重跑**。

### 3(d) 有没有「本来该在 A 级但被漏了」？给检查方法

**检查方法（本会话实跑，落 `_dt_leak.py` / `_dt_leak_out.json`）**：
```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/detect_triage_20261109/_dt_leak.py D:/Project/ra2-campaign-forge
```
逻辑：① 从两件台账全文用正则抽出所有 `*.py` basename（121 个）；② 筛出 `check_*` / `*scan*`（6 个）；③ 逐个映射回 `_kd_detect_out.json:rows` 的 173 行判据；④ 抽出两账中含 `exit=0|PASS|门禁` 的登记行号；⑤ 报出「有台账 PASS 登记但不在 CONFIRMED 40」的件；⑥ 另以 `kd.analyse(--one)` 复跑 `_rs_carrier_scan.py`；⑦ 与 `find . -path ./.git -prune -o -type f -name 'check_*.py' -print | wc -l` 比对清单全集。

**输出与结论**：
- `n_live_check_glob=173`、`n_filelist=173`、`live_only=[]`、`list_only=[]`（`_dt_scope_out.json:census`）⇒ **173 件清单对 `check_*.py` 活树全集零漏、零多**，本次 `find` 独立复算通过（`K1BIT_DETECTOR.md:831` 自认「未用 rglob 全树独立复算」，本会话补上了 `find` 口径的复算；`.git/` 内部与符号链接目标仍未纳入，标未验）。
- 6 个台账引用的门禁中，4 个（`check_d27/28/29/30.py`）在 CONFIRMED 40 且已列 A 级；2 个（`check_d25.py` `PENDING:186`、`check_d26.py` `PENDING:162`）判 `LEGAL_AGGREGATE`（kd）/ `SUSPECT`（cf 对 d26）⇒ **不是「漏 A」，是判据分歧**，须注射实证定级，不能凭检测器 verdict 直接升 A（`STALE_PASS_INVENTORY.md:133-134` 同判 C 级、未验）。
- ★ **真正的范围漏检 = 命名口径**：`_rs_carrier_scan.py` 文件名**不以 `check_` 开头**，故不在 173 件清单、不在 40 件、不在 `_cf_detect_out.json`；但 `K1BIT_DETECTOR.md:16,700-706` 明载它被 `--one` 单独实跑并判 `CONFIRMED_K1BIT`（本会话 `_dt_scope_out.json:carrier_one` 复现：`sha256=9ccca808d52f44aaee895e30f9a84f6f3b6ae5ee292ea71281e2b46e627a1c57` / 16053 B / 三处塌缩 `ARGMIN_REVERSE_MASK`+`BIT_ACCUM_AugAssign_BitAnd`+`OR_COLLAPSE_gen` / `attribution=false`）。它的 PASS **已被 3 行交付件引用**且上游清点判 A+B。⇒ **若把「结论已被引用」作为分级唯一标准，这件本该落在 C 级（仅交付件引用）甚至按上游实证升 A；它没有任何一级，因为根本没进 40 件。**
- ⇒ **检查方法总结（可复用）**：不要只按 `check_*.py` 枚举；须并集 ① 173 件清单 ② 两账 + 只读交付件中所有「PASS/exit=0/SELF_TEST」登记行的被核脚本 basename ③ 所有 `*_scan.py`/`*_gate.py`/`*_verify*.py` 等非 `check_` 前缀脚本；再对并集逐件跑 `kd.analyse()` 并查其 PASS 是否被登记。本会话用这个方法找出 1 件范围外、4 行台账 C 级。

---

## 4 第四步：检测器的误报/漏报对处置的影响

**前提（本会话实读/实跑）**：`K1BIT_DETECTOR.md:18,825` 自认「静态候选器、不是确诊器；未做动态坏针注入、未跑被检门禁」；`:664-673,738` 自认原器有 4 个实质破口、复核 `verdict=partial` 标 `unconfirmed`；`:785-786` 明列标 unconfirmed 的命题（含「零误报」「identical=True 构成独立语义复核」）。故以下影响评估必须按「**检测器给出的是候选，不是判决**」来读。

### 4(a) 误报（合法聚合被判 CONFIRMED）的后果

**实测假阳（本会话独立复跑 `_kdv_probe3.py:19-30` 的确切 fixture）**：
```
python -I -X utf8 -c "<import _kd_detect.py; kd.analyse('legal_k1_plus_unrelated_accum', SRC)>"
→ verdict=CONFIRMED_K1BIT  has_k=False  n_accum=1  n_real_collapse=1  onebit_exit=True
   (want=LEGAL_AGGREGATE；与 _kdv_probe3_out.json 逐项相符)
```
成因：`_kd_detect.py:484-487` 的 `has_k` 硬门槛被 `accum`（`ok &= good`）绕过（`K1BIT_DETECTOR.md:671,738,818`）。

**后果链**：合法件被列入 40 → 若该件是生产件且 PASS 已登记 → 被误升 A 级 → **多一次重跑**（4 次只读执行 + 加注 + 指纹绑定），并在台账留下一条本不该有的「UNTRUSTWORTHY」加注，稀释加注的严肃性；若批量按字面筛结果替换脚本，会改动无辜脚本（`K1BIT_DETECTOR.md:762-763` 记 L1 的 13 件 FP / L3 的 14 件 FP = 25–26% 误报率，含 `check_d26.py` 跨 body 存在性、`check_feasibility.py` 逐项打印、带 `hits` 归因的 `check_semantic_review*.py`；`CHECK_FAMILY_LINEAGE.md:418` 警告会连带改动证据生产副本）。
**对本次 40 件的实际影响**：**有限**。4 件 A 级生产门禁的「坏针仍 PASS」不是靠检测器判的，而是 `STALE_PASS_INVENTORY.md:94-101` 的**独立注射实证**（`_spi_4gate_out.txt` 四组 BASE/INJ 输出逐字一致 + `EXIT=0`）、`CHECK_MASKING_INJECT.md` 与 `_sp_andk.py` 的 AND_k 真跑 ⇒ 即便检测器对这 4 件误报，A 级结论也不倒。36 件 D 级沙箱不动，误报只影响清单表述、不产生动作。

### 4(b) 漏报（真缺陷未检出）的后果

**实测假阴（本会话独立复跑 `_kdv_semantic_probe.py:101-123` 的确切 V7/V8 fixture）**：
```
V7_true_collapse_renamed  → verdict=LEGAL_AGGREGATE (want CONFIRMED_K1BIT)  has_k=False n_real_collapse=0  ⇒ FN
V8_true_collapse_no_any_keyword → verdict=LEGAL_AGGREGATE (want CONFIRMED_K1BIT) ⇒ FN
```
另有改名启发式破口（`K1BIT_DETECTOR.md:669-670`：`_kdv_probe2.py n=8 passed=3 failed=5`，`words`→`zzz` 即翻盘；`_kdv_semantic_probe.py n=12 passed=8 failed=4`）。**范围性漏报**：`_rs_carrier_scan.py` 因文件名非 `check_` 前缀，整个 173 件普查里 0 行（§3(d)）。

**后果链**：真缺陷件未进 40 → 未被分级 → **该加注的没加注、该重跑的没重跑** → 它的 PASS 继续以「已验证」身份被下游引用。`_rs_carrier_scan.py` 正是实例：3 行交付件 PASS 至今挂在 `REFSYNC_SCOPE_FIX.md:251-253`，上游清点实测 `AND_k = FAIL`（`STALE_PASS_INVENTORY.md:170`），下游 `:273/:274/:276/:282-286` 的件数结论同源（`:167,241`）。

### 4(c) 两者哪个更严重

**判断：漏报更严重**。理由（逐条可追）：
1. **误报的代价是有界、可逆、自曝的**：多一次重跑 ≈ 16 次只读执行中的 4 次 + 一条加注；重跑本身会产出「逐输入全 PASS + 坏针被抓」的证据，反而**证明该件合法**，加注可据实更正。误报不会让一个坏 PASS 继续有效。
2. **漏报的代价是无界、隐蔽、沿引用链放大的**：漏掉的件**不会**触发任何动作，其「已验证」身份默认延续；`_rs_carrier_scan.py` 一漏，连带 3 行 PASS + 6 行同源件数结论全部失去自检护航（`STALE_PASS_INVENTORY.md:165-170`）。若漏的是某条裁决的门禁，则该裁决的「格式合规已验证」保证永久带病。
3. **本任务的分级逻辑本身就放大漏报**：A/B/C/D 四级只对「已进入 40 件的对象」生效；误报是「集合内多一件」，漏报是「集合外整件消失」，后者**没有兜底通道**。
4. **对应策略**：召回优先于精确——初筛用最宽口径（L3 = `\bany\s*\(` + `^\s*print\(.*PASS`，`fn=0`）+ 文件名并集枚举；但**宽筛结果只能当候选枚举，不能当判据/计数结论**（`K1BIT_DETECTOR.md:763-764`），且必须再经 AST/数据流 + 独立负控 + 动态 AND_k 才升 A 级。
5. **诚实限定**：这个「漏报更严重」是**对处置决策**的判断，不是对检测器精度的判断；本会话未量化全库真值，无法给「实际漏报率」（`K1BIT_DETECTOR.md:826` 亦自认「不能给全库究竟多少件真缺陷」）。

### 4(d) SUSPECT 6 件怎么处理（它们也未验）

**逐件清单**（`_kd_detect_out.json:suspect`、`_dt_repro_out.json:suspect_rows`，本会话重跑复现）：

| # | 路径 | 字节 | has_k | onebit_exit | 塌缩 | cf 口径 | 两账引用（本会话 `_dt_scope_out.json:suspect6_in_ledgers`） |
|---|---|---|---|---|---|---|---|
| 1 | `out/re_work/_lead_baseline/W3/forensics/snapshot_R182/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | False | True | `OR_COLLAPSE_gen` | OTHER | 0 行 |
| 2 | 同上 `snapshot_R196` | 5811 | False | True | `OR_COLLAPSE_gen` | OTHER | 0 行 |
| 3 | `out/re_work/qc/W3_20261001/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py` | 5811 | False | True | `OR_COLLAPSE_gen` | OTHER | 0 行 |
| 4 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.py` | 31955 | False | True | 2×`OR_COLLAPSE_gen` | **cf SUSPECT** | 0 行 |
| 5 | `out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py` | 11843 | False | True | 2×`OR_COLLAPSE_gen` | **cf SUSPECT** | 0 行 |
| 6 | `out/re_work/re_sprint/S1/check_134_inc.py` | 455 | False | **False** | `OR_COLLAPSE_gen` | OTHER | 0 行 |

**口径差**：`_cf_detect_out.json:suspect` = 3 件（`check_d26.py` + 2×`check_fileoffset_axiom*.py`）；`_kd_detect_out.json:suspect` = 6 件。`check_d26.py` 被 kd 判 `LEGAL_AGGREGATE`（`_dt_leak_out.json`），2 件 `check_fileoffset_axiom*.py` 两器同为 SUSPECT，其余 4 件为 kd 独有（`K1BIT_DETECTOR.md:719` 已记此口径差）。

**处理建议（本任务不执行）**：
1. **不升 A、不重跑、不加注、不删除**：6 件在两台账中 `full_rel_cited=false` 且 `basename_cited=false`（本会话实跑）⇒ 它们的 PASS **没有被登记引用**，不构成「结论已被引用」，按分级原则连 C 级都不算；标 `UNVERIFIED` 即可（`CHECK_FAMILY_LINEAGE.md:338,440`、`K1BIT_DETECTOR.md:819,827` 同判「SUSPECT 不得冒充确诊」）。
2. **逐件人工通读 + 注射实证才定级**：本会话只读了 4 件代表源码（见下），**未逐件通读全部 6 件、未做坏针注入**，标**未验**。
   - 3 件 `check_windows_cmds.py`：`out/re_work/qc/W3_20261001/coverage_ledger/_verify_cmdwindows_20261002/check_windows_cmds.py:82` 是 `any(t in out for t in ("Traceback…","SyntaxError","MemoryError"))`（对**错误签名**的存在性检测）、`:131` 一行 `ALL PASS (EXIT=0)` ⇒ 更像「单固定谓词的跨输出存在性」，按 N3 负控应属合法；但 `has_k=False` 使两器都只敢给 SUSPECT。
   - 2 件 `check_fileoffset_axiom*.py`：有 `GOLDEN_POS/GOLDEN_NEG/NAIVE_FLOOR`（`check_fileoffset_axiom.py:35,203,214,254-259,316-317`）反掩蔽硬闸，`CHECK_FAMILY_LINEAGE.md:351` 定级 `SUSPECT_ANTI_MASKING`；`K1BIT_DETECTOR.md:728` 明载修正版 `_kd_pasteable.py` 把这 2 件判为 `CONFIRMED_K1BIT`（全库 42 件的多出 2 件），但**「这 2 件是否真属本缺陷 = 未验」**，明确不改编排方 40 件结论。
   - `check_134_inc.py`：9 行、`:8` 单个 `any(k in i.mnemonic for k in ("inc","dec","add","sub"))`，`onebit_exit=False`（无 PASS 出口）⇒ 无「结论被引用」的可能。
3. **单独登记为待办**：建议 Leader 把「SUSPECT 6 逐件通读 + 是否需要纳入下一轮 173 件清单」列为一条待办；**本轮不因 SUSPECT 增改 40 件集合、不改 A 级 4 件**。

---

## 5 第五步：结论与建议

### 5(a) 最终建议数字

| 动作 | 件数 | 对象 |
|---|---|---|
| **必须重跑** | **4** | A 级：`check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py` |
| **必须加注** | **4**（与重跑同一批，先加注后重跑） | `PENDING:92` / `:105` / `:117` / `:129` |
| **建议额外加注（范围外，本任务 40 件之外）** | **1 件 / 3 行 + 6 行同源结论** | `_rs_carrier_scan.py` 的 `REFSYNC_SCOPE_FIX.md:251/252/253`（及 `:243`、`:273/:274/:276/:282-286`）；该件绝对只读，只能建议 Leader 执行 |
| **不动** | **36** | D 级沙箱/审计副本（**不加注**、不改、不重跑） |
| **标 UNVERIFIED、不动作** | **6** | SUSPECT 6 件（本会话未逐件通读/未注射，标未验） |
| **顺手定级（范围外，非 A）** | **3 行** | `PENDING:162/186/199`（C 级，`STALE_PASS_INVENTORY.md:242-244`） |

**B=0、C=0（就 40 件集合而言）**。★ 若问「几件必须重跑、几件加注、几件不动」的**单一数字答案**：**重跑 4、加注 4（同批）、不动 36**；另有范围外 1 件建议加注 + SUSPECT 6 标未验，均不改变 40 件分诊结论。

### 5(b) 可执行处置清单（谁做、按什么顺序）

> 本任务**只建议、不执行**；两台账 `PENDING_DECISIONS.md` / `GOAL_THREE_TARGETS_20261018.md` 及 `REFSYNC_SCOPE_FIX.md` 均为绝对只读，**只由 Leader 改**（`STALE_PASS_INVENTORY.md:5,174,228`）。

| 序 | 谁 | 做什么 | 依据 |
|---|---|---|---|
| P0-1 | Leader | 在 `PENDING:92/105/117/129` **就地加注**（不删原文、不改数字）：「本 PASS 经坏输入注入实证不可信，2026-11-09；形式要件失效，实质裁决不受影响；重跑结果见 §XXX」；状态字段标 `UNTRUSTWORTHY` | `STALE_PASS_INVENTORY.md:5,117,228,234-237,247-249`；本会话 `_dt_scope_out.json:pending_lines_verbatim` |
| P0-2 | Leader/执行方 | 四件按甲' 外壳重跑：先生成 12 份沙箱副本（补齐生成→落盘→驱动序列），处理三套路径布局，逐输入独立跑 + AND_k + 每根坏针哨兵，绑 SHA256+字节数+命令全文+stdout sha256，登记「逐输入判定表」 | `STALE_PASS_INVENTORY.md:251-268`（含 `:267` 口径陷阱、`:268` 部署陷阱）；`_sp_andk.py:7-40`；`_spi_andk_out.txt` 4/4 已演示可行 |
| P0-3 | Leader | 加注**不要**漏 `PENDING:117`（D-28）——它在 D-27↔D-29↔D-30 引用链上游，只修三件会漏网 | `STALE_PASS_INVENTORY.md:176,211`；`_sp_STALE_PASS_CENSUS.md:175` |
| P1-1 | Leader | 对绝对只读交付件 `REFSYNC_SCOPE_FIX.md:243/251/252/253/273/274/276/282-286` 加注「同源输出，效力待重跑」；该件 A+B 级，正确 AND_k 下应为 FAIL | `STALE_PASS_INVENTORY.md:165-170,174,238-241`；本会话 `_dt_scope_out.json:carrier_one` |
| P1-2 | Leader | `PENDING:162/186/199` 用同一甲' 外壳顺手定级（C 级，未注射实证，不得直接升 A） | `STALE_PASS_INVENTORY.md:133-135,177,242-244`；`_dt_leak_out.json:registered_not_confirmed` |
| P2 | 检测器维护方 | SUSPECT 6 逐件通读 + 注射实证；确认 `_kd_pasteable.py` 多出的 2 件是否真属本缺陷；修正 `has_k` 被 `&=` 绕过的假阳与改名/换写法的假阴 | `K1BIT_DETECTOR.md:664-673,728,738,824-833`；本会话 §4(a)(b) 实跑复现 |
| P3 | 检测器维护方 | 把清单枚举从 `check_*.py` 扩到「两账+交付件登记行被引脚本 ∪ `*_scan.py`/`*_gate.py`/`*_verify*.py`」并重跑 173→新全集；补 `.git/` / 符号链接边界说明 | 本会话 §3(d) `_dt_leak.py`；`K1BIT_DETECTOR.md:831` |
| — | 全员 | **36 件 D 级沙箱保持不动**（不加注、不重跑、不替换）；SUSPECT 6 标 `UNVERIFIED` 不动作 | `CHECK_FAMILY_LINEAGE.md:338,418`；`K1BIT_DETECTOR.md:819` |

### 5(c) 以后新增 check 脚本时的前置检查

（合并 `K1BIT_DETECTOR.md:814-822` 的写检测器准则、`STALE_PASS_INVENTORY.md:359-364` 的台账制度改法、本会话 §3(d)/§4 的实跑发现；均为**建议，未执行**）

1. **上线前先跑语义候选器 + 独立负控/正控**：`ast.parse` → k 源 → 有损归约 → 1-bit 出口 → 归因四信号；负控必须覆盖 `all()`、跨样本单字面存在性、逐输入打印、保基数、**改名/换写法/标量同名**变体（本会话 §4(b) 复现 V7/V8 即因缺这类负控）；`has_k` 为硬门槛，`&=`/argmin/三元不得绕过（`K1BIT_DETECTOR.md:816-818`）。
2. **报 PASS 前必须做坏针对照**：k≥2 输入的检验给「逐输入判定表」+ 显式 `AGGREGATE = AND_k(...)` + `DISTINGUISHABLE_PASS`；门禁与诊断量（`EXCLUSIVE`/`HITSET`/`MASKED_*`）严格分离；禁止裸 `exit=0` 当验收结论（`STALE_PASS_INVENTORY.md:363-364`）。
3. **强制指纹绑定**：登记行须带「被核对象 SHA256 + 字节数 + 输入语料/文档快照指纹 + 命令全文（逐字含所有参数）+ CWD + stdout 落盘路径及其 sha256」；本任务规定的绑定行格式固定（`STALE_PASS_INVENTORY.md:362,272-295`）。
4. **效力状态字段**：每条 PASS 打 `status ∈ {VERIFIED, UNTRUSTWORTHY, STALE_INPUT, UNVERIFIED, HISTORICAL_OBSERVATION}`，并标 `形式要件/实质结论` 与 `我亲跑/来源声明`（`:360,355`）。
5. **命名/清单并集**：新脚本若不以 `check_` 开头（`_rs_carrier_scan.py` 的教训），必须显式登记进普查清单；每次新增后用 `find . -type f -name 'check_*.py'` 与「被引脚本并集」双向对账（本会话 `_dt_scope_out.json:census` 实跑 173=173、`live_only=[]`）。
6. **失效回写通道**：任何复核判定某 PASS 不可信，**必须**在原登记行就地加注并同步扫描/加注所有下游引用（`:361`；`:346` 自反承认上一轮自己漏了 `FIX:243/273-276/282-286`）。
7. **只写域约束**：跑前跑后重核被检脚本指纹（`git diff --name-only HEAD -- '*check_*.py'` = 0）、结果落 JSON、写域外只读（`K1BIT_DETECTOR.md:820-822`）。

### 5(d) 这条工作判不了什么（如实列）

1. **不能确诊「坏针仍 PASS」**：本会话零真机、零采样、未跑被检门禁、未做动态坏针注入；40 件是**静态结构候选**（`K1BIT_DETECTOR.md:18,825`）。A 级 4 件的「已证明不可信」来自引用 `STALE_PASS_INVENTORY.md:94-101` 的**上游实跑**，本会话**未复跑其注射命令**，标「题给/上游材料记录，本会话未复跑」。
2. **不能判全库究竟多少件真缺陷**：40 件含副本与已注入哨兵变体；`CHECK_FAMILY_LINEAGE.md:338`、`K1BIT_DETECTOR.md:826` 均标 unconfirmed。
3. **不能判 D-27..D-30 裁决实质是否正确**：本任务只判「PASS 的证据资格/引用结构」；`STALE_PASS_INVENTORY.md:213` 自认未重跑 `_d27_facts.py`/`_d29_facts.py`/`_d30_facts.py` 的数值断言；`K1BIT_DETECTOR.md:829` 亦自认不能判裁决实质与制度层根因。
4. **不能给重跑的真实耗时**：本会话未执行重跑、无计时输出，§3(b) 的「分钟级」为**估算、未验**。
5. **不能量化检测器的全库误报率/漏报率**：只复现了 3 个确切 fixture（probe3 假阳、V7/V8 假阴）与 3 种字面筛的混淆矩阵（L1 fp=13/fn=4、L2 fp=12/fn=4、L3 fp=14/fn=0），未建立全库真值（`K1BIT_DETECTOR.md:826-828`）。
6. **SUSPECT 6 未逐件通读/未注射**：本会话只读 4 件代表源码行、未逐件定级；修正版多出的 2 件是否真属本缺陷 = 未验（`K1BIT_DETECTOR.md:727-728,827`）。
7. **清单边界**：`.git/` 内部、符号链接目标、以及所有非 `check_*` 前缀脚本（除单独 `--one` 复跑的 `_rs_carrier_scan.py` 外）未纳入 173 件普查；本会话用 `find` 独立复算的是 `check_*.py` 口径全集，**未用 `Path.rglob` 对全树任意 `.py` 做全集比对**（`K1BIT_DETECTOR.md:831`）。
8. **不能代 Leader 改台账/交付件**：两件台账与 `REFSYNC_SCOPE_FIX.md` 在本任务绝对只读；所有加注/重跑均为建议，未执行、未验证执行结果。
9. **不能覆盖运行时 k 源**：别名/闭包/`eval`/跨模块常量/`globals()` 注入不在静态数据流内（`K1BIT_DETECTOR.md:830`）。
10. **不能判定历史上输入是否变过**：六个裁决目录 `git status` 为 `??`（未跟踪）、`git log -- RULING_D27.md` 无输出（`STALE_PASS_INVENTORY.md:139`）；本会话只核了当前盘文档字节数与 sha 前缀相符。
11. **编排方自报 ranCommands=33/42 未验**：无日志，本会话未复核条数（`K1BIT_DETECTOR.md:833`）。

---

## 6 复核回件（绑定行，格式固定）

**被核对象** = 编排方【编排方实跑指纹】7 件 + 本会话分诊出的 A 级 4 件生产门禁。全部由本会话 `hashlib` 独立实算（`_dt_repro.py` / `_dt_triage.py`）；格式固定，值前不插路径、括号、星号、反引号或空格。

被核对象 SHA256 = 00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239，字节数 = 251854
被核对象 SHA256 = 40d79857bebc28fb1dd1d2f03afc7f1dc825b4b9cf9a56e55a0a93179ca32ad1，字节数 = 60565
被核对象 SHA256 = af84560f288a0f74cac5f9f1f95f64f68c767e8a0aee32e869d1b0fc2ab9cc2f，字节数 = 39990
被核对象 SHA256 = 17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2，字节数 = 130498
被核对象 SHA256 = a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798，字节数 = 63656
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518
被核对象 SHA256 = 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c，字节数 = 3764
被核对象 SHA256 = 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268，字节数 = 4539
被核对象 SHA256 = 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14，字节数 = 3906
被核对象 SHA256 = 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd，字节数 = 3926

（绑定行依次对应：`lead/k1bit_detect_20261109/_kd_detect_out.json`、`K1BIT_DETECTOR.md`、`_kd_literal_vs_semantic_out.json`、`lead/check_family_20261109/_cf_detect_out.json`、`lead/stale_pass_20261109/STALE_PASS_INVENTORY.md`、`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`；随后 4 行为 A 级 `check_d27.py` / `check_d28.py` / `check_d29.py` / `check_d30.py`。）

---

## 7 本写域产出清单（全部前缀 `_dt_`，未 commit / 未 push）

| 文件 | 内容 |
|---|---|
| `_dt_REPORT.md`（本件） | 分诊结论与建议 |
| `_dt_repro.py` / `_dt_repro_out.json` | 173 件独立重跑、10 自检、3 字面筛复现 |
| `_dt_scope.py` / `_dt_scope_out.json` | 清单全集、carrier `--one`、台账逐行引用、sandbox 引用、suspect 口径差 |
| `_dt_triage.py` / `_dt_triage_out.json` | 40 件逐件四级分级、A 级指纹、绑定行 |
| `_dt_leak.py` / `_dt_leak_out.json` | 漏 A 检查（台账被引门禁全集） |
| `_dt_table.md` | 40 行完整归类表 |
| `_dt_find_list.txt` | 本会话 `find` 实跑的 173 件活树清单 |

**本会话实跑命令汇总**（均在 `D:/Project/ra2-campaign-forge` 下，Python 一律 `python -I -X utf8` + 绝对路径）：指纹复核 `-c`；`_dt_repro.py`；`_dt_scope.py`（初次 `rglob` 版 >120 s 被 `TaskStop` 停止，改为 `find` 清单版后完成——如实记录）；`_dt_triage.py`；`_dt_leak.py`；`_dt_table.md` 生成 `-c`；`_kdv_probe3.py` 确切 fixture 复跑 `-c`；V7/V8 确切 fixture 复跑 `-c`；`git status --short -- <只读域>`；`git rev-parse HEAD`；`find . -path ./.git -prune -o -type f -name 'check_*.py' -print | wc -l` → `173`。**未执行任何重跑、未启动任何游戏进程、未写任何采样代码。**

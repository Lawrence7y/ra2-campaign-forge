# GATE_PIPELINE_COMPOSE.md — 三层判据合成链：顺序、冲突消解、分层回归

- 日期 2026-11-09。唯一写域 `lead/gate_pipeline_20261109/`；本次交付件为本件 `GATE_PIPELINE_COMPOSE.md`。
- 零真机（未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 `taskkill`，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
- Python 一律 `python -I -X utf8` + 绝对路径；指纹一律 `hashlib.sha256` + 字节数。
- **本任务只做合成设计与冲突消解**：未改任何既有谓词模块、未改任何既有交付件、未 commit、未 push。
- **复核 verdict = partial → 本交付件标 `unconfirmed`**（详见 `## 6.2`）。核心数据本会话已独立复算，但四处声称被复核实跑打破，不冒充 confirmed。

---

## 1 目的与边界

**目的**：把已经各自封样的判据层——提取器 / R9·R10·R12·R11（`lead/gate_fp7_20261108/_g7_predicates.py`）与 N13（`_n13_predicates.py`）——按**数据依赖**串成一条链，给出逐 span 的**冲突消解规则**，并在 74 条合成语料上做**分层回归对比**，如实回答「合成后是变好还是更差」。

**边界（铁律，逐条遵守）**：

1. 绝对只读：`lead/gate_n13_20261109/`、`lead/gate_v1v2_20261109/`（若存在）、`lead/gate_r9sem_20261109/`（若存在）、`lead/gate_fp7_20261108/_g7_predicates.py`、`lead/gate_r9r12_20261109/_g9_gate.py`、`lead/gate_rejudge32_20261109/`、两件台账（`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md`）——一律不修改、不追加、不覆盖。
2. 唯一写域 `lead/gate_pipeline_20261109/`。本会话在该写域内**只新建** `GATE_PIPELINE_COMPOSE.md`、`_gp_compose_check.py`、`_gp_compose_check_out.txt` 三件；原有 `_gp_*` / `_gpv_*` 件一字未改（本会话对 `_gp_regression_out.json/.txt` 与复核重跑产物 `_gpv_repro_out.json/.txt` 做了逐字节 `hashlib` 比对，见 `## 6.9`）。
3. **不改任何既有谓词模块、不改任何既有交付件**：所有层以只读 `importlib` + `hashlib` 先验指纹方式加载（`lead/gate_pipeline_20261109/_gp_pipeline.py:30-52`）。
4. 不 commit、不 push。本会话 `git rev-parse HEAD` = `26574589aa8401e8f3f2934680a1ea7109bafa2d`（`## 6.9`）。
5. **冲突如实记**：若某层谓词在同一 span 上「一层说放过、另一层说抓住」，登记为冲突，**不许靠调顺序让矛盾消失**——顺序只决定先报谁，不能决定谁对。

**本交付件不是什么**：不是「已合成、可直接上线」的门禁成品。复核给出 `partial`，四处问题未闭合（`## 6.2`）；本件把设计、冲突面、逐条统计、未验项与翻盘条件一并交付。

---

## 2 上游指纹（十件）与三层现状

### 2.1 上游指纹十件（本会话 `hashlib` 逐件重算，全 MATCH）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_compose_check.py > D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_compose_check_out.txt`，`EXIT=0`；输出 `ALL_TEN_MATCH = True`（`_gp_compose_check_out.txt:1-12`）。

| # | 件 | SHA256 | 字节数 |
|---|---|---|---|
| 1 | `lead/gate_n13_20261109/_n13_predicates.py` | `e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079` | 16649 |
| 2 | `lead/gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md` | `7b3fddb7d3484c76fecfe25fb352f081a1391b14b1d87684c719adf3df06e90b` | 39906 |
| 3 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 |
| 4 | `lead/gate_r9r12_20261109/_g9_gate.py` | `a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6` | 11623 |
| 5 | `lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md` | `ed7e326d38a967308acf0e276c262300abf8d68c98aad2d53b8e9f2a3def6528` | 51156 |
| 6 | `lead/c07_slot_20261109/C07_IDENTITY_SLOT.md` | `05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc` | 20651 |
| 7 | `lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md` | `5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3` | 38232 |
| 8 | `lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md` | `47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70` | 70587 |
| 9 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 |

编排方另派发两个目录清单：`dir:lead/gate_v1v2_20261109` = 11 件、`dir:lead/gate_r9sem_20261109` = 空。**该清单已状态漂移，见 `## 2.5`**。

### 2.2 输入契约 / 输出契约（逐层，代码行号本会话 `grep -n` 复核）

| 层 | 输入契约 | 输出契约 | 代码位置 |
|---|---|---|---|
| L0 提取器（现状） | `text` + 从门禁源码 `ast.literal_eval` 提取的词表/正则 | 各参数 dict；**`BANNED_RE` / `BIND_RE` 用 `.search` 只取首个 match** | `lead/gate_doc_name_fix_20261109/_dn_regate_domains.py:19-22,70,76`（本会话读到 `:70: m = BANNED_RE.search(src)`、`:76: m = BIND_RE.search(src)`）；`LOOP_RE` 已用 `finditer`（`:65`） |
| L1 R9 `r9_check(text,tokens)` | 文本 + 必需要素词表 | 二元组 `(problems:list, warnings:list)`；`r9_element_present` 返回 `(bool,"raw"\|"normalized"\|"")` | `lead/gate_fp7_20261108/_g7_predicates.py:46,55` |
| L2 R10 `r10_scan(text,assert_tokens)` | 文本 + 越权词表 | 三元组 `(problems, warnings, hits)`；`hits` 含 `token/pos/kind/neg_count/in_span` | `_g7_predicates.py:113-130`；`r10_context` 在 `:78` |
| L3 R12 `r12_scan(text,assert_tokens)` | 文本 + 越权词表（**内部再调 `r10_context`**） | 二元组 `(problems, hits)` | `_g7_predicates.py:134-148` |
| L5 R11 `r11_scan(text,doc_dir,root=None,recompute=None)` | 文本 + **文档目录/仓库根**（读盘重算 sha256） | 三元组 `(problems, warnings, bindings)` | `_g7_predicates.py:157-222` |
| L4 N13 `r13_scan(text,tokens,r10_scan=None,r12_scan=None)` | 文本 + 自带三词 `DEFAULT_TOKENS` + **两个注入函数** | `(has_ab:bool, details:list)`；`details` 含 `token/pos/line/quote/kind∈{A,B,C,D}/exempt/rule/r10_kind/degraded` | `_n13_predicates.py:25,32,183-304`（本会话 `grep -n` 得 `:183 def r13_scan`、`:195-200` 注入调用、`:247-259` C 类转发与降级） |
| L4' N13 `r13_assertions(...)` | 同上 | `(problems, details)`；`problems` 只含 D 类 | `_n13_predicates.py:307-313` |
| 编排层 `_g9_gate.py` | 加载前先验 g7 sha256/字节数 | dict：逐层 items/hits/problems/warnings/verdict | `lead/gate_r9r12_20261109/_g9_gate.py:24,36-51`（本会话实读） |

**契约不对齐三处（后续冲突几乎全部源自此）**：

1. **词表不对齐**：N13 默认只认 `('已入账','已追加','已生效')`（`_n13_predicates.py:25`）；R10/R12 认调用方词表，真件用 C07 域 `['已补登','已填入','已填','已代填']` / `['已填','已代填','已提交']`（`lead/gate_v1v2_20261109/_v12_probe.py:15-18`）与 BAD_BAN 五词。R10 报的 `已填` 在 N13 眼里**根本不是 span** → `ABSENT ≠ PASS`。
2. **位置口径不对齐**：R10 `pos` 是原文本字符下标；N13 `gpos` 按 `splitlines()` 累加 `len(line)+1`（`_n13_predicates.py:207,225,293`）。前序 LF/CRLF 对照实跑：LF 时两层 `pos=8` 对齐；CRLF 时 R10 `pos=9`、N13 `pos=8`，`r10_kind` 从 `assertion` 变 `None`（`(token,pos)` 键失配）。三件真件均为 LF（`_gpv_probe_out.txt:5,13,21` 记 `crlf=0`），故本次对齐成立——**这是条件，不是保证**；归一代码未实装。
3. **双重否定构式是枚举表**：`DOUBLE_NEG_RE`（`_g7_predicates.py:76`，本会话读到枚举 `不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不`），`NEG_RE`（`:69`）、`CLAUSE_BREAK`（`:71`，**不含逗号**）。分离型「亦非不」不在表内。

### 2.3 三件真件在三层下的结果（前序 `_gp_probe.py` / 复核 `_gpv_probe.py` 实跑留盘）

三件绑定行指纹本会话独立重算 `BIND_ALL_MATCH = True`（`_gp_compose_check_out.txt:14-18`）。

**C07_SLOT**（20651 B，`_gp_probe_out.txt:16-22`、`_gpv_probe_out.txt:5-11`）
- C07 词表：R9 problems=0；**R10 problems=5**（assertion 5 + negation 1，occurrences=6）；R12=0；R11 problems=0、warnings=5、bindings=5 全 `path=null`；**N13 problems=0**（A/B/C/D 全 0），`only_r10=6`。
- N13 三词 / BAD_BAN 五词口径：四层全 0（该件不含这三个词）。强行给 N13 喂 C07 词表 → 6 条 D、其中 1 条「R10 放过 / N13 抓住」反向冲突（`_gpv_probe_out.txt:9-10`）。
- 编排方【三层组合实跑】`C07_SLOT.r10_problems=5` 复现。

**TRUTH**（38232 B，`_gp_probe_out.txt:24-30`、`_gpv_probe_out.txt:13-19`）
- C07 词表：R9=0；**R10 problems=2**（assertion 2 + negation 1，occurrences=3）；R12=0；R11 problems=0、warnings=15、bindings=15 全 `path=null`；**N13=0**，`only_r10=3`。
- 编排方 `TRUTH.r10_problems=2` 复现。

**BOUND**（70587 B，`_gp_probe_out.txt:32-47`、`_gpv_probe_out.txt:21-34`）
- N13 三词 / BAD_BAN 五词两条口径相同：R9=0；**R10 problems=5**（assertion 5 + negation 2，occurrences=7）；R12=0；R11 problems=1（`引用锚指向不在盘对象 sha256Line（R11/R3-3c）`）、warnings=10、bindings=11、null_path=10；**N13 problems=0**，`details` 分布 `A=2 B=3 C=2 D=0`。
- 逐 span 对齐 7 处，`differ=5`。

### 2.4 冲突面逐处（不靠顺序抹平）

**（a）同 span 真值相反：BOUND 5 处「R10 抓住 / N13 放过」**（`_gpv_probe_out.txt:23-27` 逐行含 `rule` 局部证据；`_gp_probe_out.txt:37-41` 逐行含原文）

| pos | 行 | token | R10 | R12 | N13 | N13 局部证据 / 原文（截断） |
|---|---|---|---|---|---|---|
| 3672 | 54 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | B 小节标题标记 `grep`；`## 2 · 上游指纹（十一件）… + 已入账 grep 结果` |
| 5867 | 77 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | B 标记 `grep`；`### 2.2 待入账清点 + 已入账 grep 结果` |
| 5882 | 79 | 已入账 | `assertion` CATCH | 0 | `A` 放过 | A 检索动作 `核查`；`**已入账核查实跑命令**：` |
| 6305 | 87 | 已入账 | `assertion` CATCH | 0 | `B` 放过 | B 表头 `?`；`\| 笔 \| 暂编 \| … \| 已入账? \|` |
| 35513 | 338 | 已入账 | `assertion` CATCH | 0 | `A` 放过 | A 标记 `grep`；`本交付件按任务要求改为「## 1」到「## 5」五节：§1 … + 已入账 grep …` |

另 2 处（pos=19877 L209、pos=24534 L242）R10=`negation` 放过、N13=`C` 放过，**一致，非冲突**（`_gp_DESIGN.md:100`）。

**（b）反向「R10 放过 / N13 抓住」**：三件真件 **0 处**（`_gpv_probe_out.txt:6-8,22`）；但 N13 自带回归 §5 前序实跑有两类留盘（`_gp_DESIGN.md:102-113`）：`不宣告 X 已生效，但 Y 已入账` → R10 kinds 全 `negation`、R12=0、N13 两条 D；`并非不宣告已生效` → R10 `double_neg`、R12 报「越权断言 已生效」、N13 D。

**（c）词表外无答案（第三类冲突）**：SLOT 6 处 / TRUTH 3 处 `已填`，R10 有明确 `assertion/negation` 判定，N13 **完全无 span**（`ABSENT`）。这不是「另一层说放过」，是「另一层没参与」，**绝不能当作一致**（`_gp_probe_out.txt:22,30` `only_r10=6/3`）。

**冲突面合计：5 处真值相反 + 9 处词表外无答案 = 14 处，全部如实登记。**

### 2.5 状态漂移（本会话实测，如实记）

编排方派发时 `dir:lead/gate_r9sem_20261109 = []`，`_gp_DESIGN.md:28` 写「`ls` 报 `No such file or directory`」；复核方报「本会话末已有 13 件」。**本会话实测又不同**：

- `lead/gate_r9sem_20261109/` 存在，`ls -1 | wc -l` = **17 项**（含 `__pycache__` 目录；`_r9s_DESIGN.md`、`_r9s_predicates.py`、`_r9s_samples.py`、`_r9s_regress.py`、`_r9s_minpatch.py`、`_r9s_g9_candidate.py`、`_r9s_step1_verify.py`、`_r9sv_verify.py` 及各 `_out` 产物）。
- `lead/gate_v1v2_20261109/` 本会话 `glob("*")` = **26 项**（编排方清单 11 件；多出 `_v12v_*` / `_v12w_*` 复核产物、`GATE_V1V2_IDENTITY_VS_ASSERTION.md`、`__pycache__` 等）。
- 本会话 `grep -rn -E "登记闭合|三值填毕|亦非不" lead/gate_r9sem_20261109` **无输出行**（即其落盘词表未见这 3 条构造样本）；**r9sem 脚本本会话未跑，标未验**。
- 结论：本链不依赖 r9sem，但「r9sem 不存在」这句已过时；本报告按「已落盘、未验」记，不沿用前序的「不存在」。

---

## 3 合成顺序

### 3.1 建议判定链（数据依赖，不是优先级）

```
L0 提取器（全量 finditer + 行号 + eol 类型 + 指纹）
 ├─→ L1 R9 要素在场 ───────────────────────────────┐
 ├─→ L5 R11 绑定回验 ──────────────────────────────┤  独立项，可并行
 └─→ L2 R10 语境分类（宽进）                       │
        ├─→ L3 R12 双重否定（消费 r10_context.dbl） │  断言面主链
        └─→ L4 N13 A/B/C/D（消费 L2 hits + L3 hits）│
                    ↓                                │
        L6 逐 span 冲突消解（只裁决 + 登记，不覆盖）←┘
                    ↓
        L7 结论（problems / conflicts[] / NEEDS_HUMAN）
```

### 3.2 逐层位置理由

- **L0 在最前**：修 `_dn_regate_domains.py:70/:76` 只取首个 `search` 的提取器假象，用 `finditer` 全量产出 `(token,pos,end,line,eol)`，后续所有层共享同一 span 集合；记录 `CRLF/LF` 因为位置口径会失配（`## 2.2`）。
- **L1 R9 第二**：与越权断言面正交，只需 `text+tokens`；先跑可在断言层之前独立定案「缺要素」。
- **L2 R10 第三**：宽进层，每个字面命中都产 `kind`（`_g7_predicates.py:113-130`），必须尽早拿到全量 span。
- **L3 R12 第四**：`r12_scan` 内部直接调 `r10_context`（`_g7_predicates.py:144`），是 R10 分类的**消费者**；放在 R10 之后是数据依赖而非优先级。
- **L4 N13 第五**：`r13_scan` 的 `r10_scan`/`r12_scan` 是**注入参数**（`_n13_predicates.py:183,195-200`），按 `(token,pos)` 查 R10 kind、按集合查 R12 命中，**是两层的消费者，不是替代者**。必须拿到 L2/L3 完整 hits 才能跑。
- **L5 R11 与 L1–L4 并行**：唯一有 I/O 与 `doc_dir` 依赖的层，与断言面无数据往来；`_g9_gate.py:24` 把它放最后只是收尾习惯，非依赖。
- **L6/L7 最后**：裁决与结论需所有层返回齐备；**位置靠后不代表它的意见更高级**。

### 3.3 宽进 / 精筛的先后依据

- **宽进（宁可多报）**：提取器全量 `finditer`、R10（每命中必产 kind，`assertion` 即 FAIL）、R12（双否定一律报）、朴素门禁（字面子串即报）。实测 74 条语料：naive **FP=33**、R10 **FP=20 / FN=19**、R12 单跑 **FN=35**（`_gp_regression_out.txt:12-14`）。
- **精筛（只保留真断言）**：N13（A/B/C 放过、D 才 FAIL）、R9（仅 raw+normalized 双缺判 FAIL）、R11（只对失配/不在盘判 FAIL）。实测 N13 **71/74、FP=0、FN=3**（`_gp_regression_out.txt:15`）。
- **宽进必须在精筛之前**，理由不是「谁更严」，而是**精筛层的输入就是宽进层的输出**：`_n13_predicates.py:195-202` 要求传入 R10/R12；没有 R10 hits，N13 的 C 类会降级为「无 R10 → 默认 FAIL」（`:257-259`），反把正样本误拦。**反过来放不行**：R10 之后 `problems` 已丢失逐处语境（`lead/gate_v1v2_20261109/_v12_REPORT.md:263` 本会话实读，独立同结论）。
- **但宽进的 `problems` 绝不能直接并进最终结论**——这是本任务抓到的头号陷阱，见 `## 5.5`。

### 3.4 可否并行的层

可并行：**L1(R9) / L5(R11) / 断言面主链(L2→L3→L4)** 三路；L2 与 L3 也可并行（两者都只依赖 `text+tokens`，R12 内部自己重算 `r10_context`，不消费 R10 返回对象；`_g7_predicates.py:113-148` 无相互赋值）。

前序实跑（5 线程 `ThreadPoolExecutor` 对 BOUND 件，设计会话留盘）：`PARALLEL_VS_SERIAL: {"R9_equal": true, "R10_equal": true, "R12_equal": true, "N13_equal": true, "R11_equal": true} ALL_EQUAL= True`。**本会话未重跑该并行对照，标未验（前序留盘）**。

**合并规则（可执行）**：①以 L0 全量 `(token,pos)` 做 outer join，缺层记 `ABSENT` 而非 `PASS`；②R9/R11 的 problems 与断言面正交，直接并入并保留 `rule_id`；③断言面（R10/R12/N13）**不做并集**，逐 span 走 K1–K9 生成 `ADJUDICATED`，每个分歧另记 `conflicts[]`（无论裁决结果都不删除）；④join 前按 `eol` 归一 N13 `gpos`（**归一代码未实装**）。

### 3.5 pipeline 骨架片段（可粘贴；完整实装 `lead/gate_pipeline_20261109/_gp_pipeline.py:48-265`）

```python
import hashlib, importlib.util, pathlib, re, sys
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
G7  = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13 = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
FP = {G7: ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
      N13: ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649)}

def _load(path, name):                       # L0：只读 + hashlib 先验
    raw = path.read_bytes()
    if (hashlib.sha256(raw).hexdigest(), len(raw)) != FP[path]:
        raise RuntimeError("谓词指纹失配，拒绝运行")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def run_layers(g7, n13, T, text, tokens, doc_dir):     # L1..L5 原样转发，不互相覆盖
    r9  = dict(zip(("problems","warnings"), g7.r9_check(text, ["被核对象","SHA256","字节数"])))
    r10 = dict(zip(("problems","warnings","hits"), g7.r10_scan(text, tokens)))
    r12 = dict(zip(("problems","hits"), g7.r12_scan(text, tokens)))
    n13p, n13d = n13.r13_assertions(text, T, r10_scan=g7.r10_scan,
                                    r12_scan=g7.r12_scan)
    r11 = dict(zip(("problems","warnings","bindings"), g7.r11_scan(text, doc_dir, root=ROOT)))
    return {"R9": r9, "R10": r10, "R12": r12,
            "N13": {"problems": n13p, "details": n13d}, "R11": r11}

# L6：按 (token,pos) outer join；三值归一 CATCH / PASS / ABSENT（ABSENT ≠ PASS）
#   逐处套 K1–K9；conflicts[] 保留双方原意见与 rules[]，裁决不删除任何一方。
# L7：problems = R9/R11 直并 + ADJUDICATED + NEEDS_HUMAN；CONFLICT 只登记不代替裁决。
rows, conflicts, summary = P.resolve_conflicts(text, tokens, layers, T)
res = P.gate_check(text, tokens, doc_dir, g7, n13, T)   # → verdict/problems/conflicts/summary
```

**返回值显式转发链**（`_gp_pipeline.py:197-203`）：L0 `spans` → L6 join 主键 + `eol` 归一开关；L2 `hits(token/pos/kind)` → L4 `r10_map` 与 L6 `r10_v`；L3 `hits` → L4 `r12_pos` 与 L6 `r12_v`；L4 `details(kind/exempt/rule/line)` → L6 `n13_v/n13_veto`；L1/L5 `problems` → L7 直并（不进裁决）；L6 `rows` → L7 `ADJUDICATED`，`conflicts` → L7 只登记。

本会话实跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_pipeline.py`（`EXIT=0`）输出：

```
demo text = grep 结果：已生效，可应用母本
verdict = FAIL summary = {'spans': 1, 'catch': 1, 'pass': 0, 'raise': 0, 'conflicts': 0, 'unresolved': 0}
   已生效 8 CATCH CATCH => CATCH ['K4']
  PROBLEM ADJUDICATED L1 pos=8 tok=已生效 裁决=CATCH rules=K4 (r10=CATCH r12=ABSENT n13=CATCH)
```

（另有 3 条 R9 缺要素与 1 条 R11 缺绑定行，属独立项直并，非断言面裁决。）

---

## 4 冲突消解规则

### 4.1 逐类冲突形态

| 形态 | 实例 | R10 | R12 | N13 | 裁决 |
|---|---|---|---|---|---|
| C1 同 span R10 CATCH / N13 PASS | BOUND 5 处（`## 2.4`） | `assertion` CATCH | ABSENT | `A/B` 放过 | **PASS，K9**；分歧仍登记 `conflicts[]`。R10 的 assertion 是「24 字回看窗无否定词」的宽进默认值（`_g7_predicates.py:78-109`），N13 的 A/B 有该 span 自身微段内的正向标记（`_n13_predicates.py:273-286`）。不能说「R10 错了」，只是它这层没有足够信息 |
| C2 同 span R10 PASS / N13 CATCH | `不宣告 X 已生效，但 Y 已入账`、`未验：本笔已入账` | `negation` PASS | ABSENT | `D` CATCH | **CATCH，K2**。`CLAUSE_BREAK` 不含逗号（`:71`），肯定段被同窗否定词污染；N13 `_line_positive`（`:163-177`）是 R10 看不到的局部证据 |
| C3 R12 双否定 | `并非不宣告已生效` | `double_neg` PASS | CATCH | `D` CATCH | **CATCH，K1**。双重否定=肯定是语义事实，非严格度偏好；N13 自身也消费 R12（`:241-245`）。三层一致，非冲突 |
| C4 三层全放过 | `亦非不宣告 N-4 正式绑定已生效` | `negation` PASS（`neg_count=2,dbl=False`） | 0 命中 | `C` 放过（转发 R10） | **无冲突（无相反意见），共同盲区，判错**。见 `## 4.5` |
| C5 F03 三形态 | 见 `## 4.5(b)` | 三种 | 三种 | 三种 | 三个不同结论 ⇒ 必须按 span 逐处判，不能按整行印象判 |
| C6 不同 span 同一行 | `不宣告 X 已生效，但 grep 结果：已入账 0 命中` | 全 PASS | ABSENT | `A` + `C` 放过 | **K4 只在该行有 D 时提升**；本例 N13 未判 D ⇒ 合成链按各 span 放过，**兜不住**（复核 MIX-2，`_gpv_verify_out.txt:157-165`） |
| C7 不同行同一小节 | 标题 `## 2 … 已入账 grep 结果`（B 放过）与下一行 `本笔已入账`（D 抓住） | — | — | — | **K5 不传播**，只记 section 定位；跨行支配本身判不了（`_v12_REPORT.md:239`） |
| C8 词表外 span | SLOT/TRUTH 的 `已填` | CATCH/PASS | ABSENT | ABSENT | **K6 采用 R10 结论并显式标 `OUT_OF_N13_VOCAB`**；绝不因 N13 返回空就当 PASS。实跑 SLOT 5 处 / TRUTH 2 处被 K6 判 CATCH，构成 `## 5` 的 2 条文件级误报 |

### 4.2 可执行消解规则 K1–K9（实装于 `_gp_pipeline.py:123-217`）

统一三值 `CATCH / PASS / ABSENT`，**`ABSENT ≠ PASS`**：

| 规则 | 条件（同一 `(token,pos)` span，除注明外） | 结论 |
|---|---|---|
| **K1** | R12 命中 `double_neg` | `CATCH`（双重否定=肯定，语义事实） |
| **K2** | N13=`D` 且 R10=`negation/quote_mention` | `CATCH`（同句混用/微段主语是 R10 看不到的局部证据） |
| **K3** | N13=`A/B/C` 放过 且 R10=`assertion` | 先登记分歧，交 K4/K8/K9 细分 |
| **K4** | 不同 span 同一行，且该行有 N13 的 D | 整行 `CATCH`（只提升不降级） |
| **K5** | 不同行同一小节 | 不传播，只记 section |
| **K6** | token 不在 `N13.DEFAULT_TOKENS` 内 | 采用 R10 结论并标 `OUT_OF_N13_VOCAB`；无 R10 答案则 `RAISE` |
| **K7** | 任何层 `ABSENT` 且无其他层答案 | `RAISE / NEEDS_HUMAN`，不放过 |
| **K8** | K3 且无行级 D、无 A/B 局部证据 | `FAIL_CLOSED` + `CONFLICT_UNRESOLVED`，**不冒充判对** |
| **K9** | K3 且 N13=`A/B`、微段内有标记、该行无 D | `PASS`（精筛覆盖宽进默认值） |

不变量：同一 span 只出一个 `final`，但 `conflicts[]` 同时保留双方原意见与 `rules[]`；同行 K4 聚合只提升 CATCH、从不降级；不同行只记 section；CRLF 须在 join 前归一 `gpos`。

**复核③（本会话独立核对）**：`_gp_compose_check_out.txt:111-116` 得 K8 分支在 `_gp_pipeline.py:175`、K7 分支在 `:161,184`；规则标签 `R10_ASSERTION_OVERRULED` / `OUT_OF_N13_VOCAB` / `MIXED_CLAUSE` / `section` 在**非注释代码中全部为 False**（只存在于注释 `:99,103,109,111,114`），实装 `conflicts[]` 不 emit 这些标签。即上表的 `rule_id` 是**设计契约，不是已落盘输出**。

### 4.3 冲突消解：顺序决定谁先报 ≠ 谁对（顺序不等于对错）

- 顺序只决定**数据依赖与报告次序**：R12/N13 必须等 R10 hits，R9/R11 可并行；真值由 K1–K9 的 span 级证据决定，与先后无关。
- 复核 `_gpv_order_out.txt:1-51` 对 4 段文本跑 5 种层序（`data_dependency / reversed / n13_first / r9r11_first / shuffled`），`ALL_ORDERS_SAME_TRUTH = True`——**这是「顺序不改真值」的正面证据，不是「顺序能消解冲突」**。
- 反证：若把「先后顺序」当消解手段（最后跑的层说了算），BOUND 的 5 处 A/B 会被 N13 放过（对），但 `亦非不宣告…` 也会被放过（错）；`grep 结果：已生效 0 命中` 会因 R10 先报而永远 CATCH。
- 更直接的实跑反证：把三层 `problems` 做朴素并集（等价于「任一层先报即算」），合成链从 N13 单层 68/72 掉到 **48/72**（FP 0→20），证据 `_gp_regression_v1_union_out.txt:10-15`（本会话实读）。**顺序与并集都不能消解真值冲突，只会把宽进噪音灌进结论**。
- 因此 `verdict` 由逐 span 裁决结果生成；`conflicts[]` 无论裁决与否都完整登记；未消解标 `NEEDS_HUMAN`，不放过、也不冒充已判对。

### 4.4 「31 处冲突未消解 0」是空结论（复核③，如实记）

`_gpv_reach_out.txt:128-145` 前序复核实跑：74 条语料上 K1=5、K2=9、K3=22、K4=23、K5=17、K6=42、K9=22，**K7=0、K8=0**；`UNRESOLVED_CASES = [] TOTAL = 0`。定向构造仅 CRLF 样本触发 `K7`（`CRLF_neg → RAISE ['K7']`），`K8_UNRESOLVED_SEEN = False`、`FAIL_CLOSED_SEEN = False`。

⇒ **「未消解 0」不等于「裁决全部成功」**：它只说明现有 74 条语料没有一条走到 K8 分支；K8/FAIL_CLOSED 在结构上是死分支，其能力**未被验证**。要翻转需给出可达的 K8 样本，或撤回该规则（见 `## 6.3`）。

另：`_gp_DESIGN.md:269` 声称 `conflicts[]` 按 `pos` 升序打印；`_gpv_order_out.txt:53-67` 实测 `rows_pos=[8,19,-1] asc=False`、跨进程 4 次 `all_same = False`。本会话 `_gp_compose_check_out.txt:117` 复核 `_gp_pipeline.py` 含 `tok_set = set(tokens)`（`:132` set 迭代）且 `sorted(` 只用于 `extract_spans`。⇒ **「按 pos 升序」未实装，报告次序不确定**；但真值不受影响（`ALL_ORDERS_SAME_TRUTH = True`）。

### 4.5 兜不住的构造样本与如实结论（复核①，最关键的一处如实修正）

**(a) 当前已落盘的合成链确实兜不住，且不止 3 条孤例**

`_gp_regression_out.json` 第 72–74 行 / `_gp_compose_check_out.txt:105-107`：

| id | 文本 | R10 | R12 | N13 | 合成链 | 人工真值 |
|---|---|---|---|---|---|---|
| GP-A1 | `亦非不宣告 N-4 正式绑定已生效` | `negation` PASS（`neg_count=2,dbl=False`） | 0 命中 | `C` 放过（转发 R10） | **PASS，漏报** | 双重否定=宣告，真断言 |
| GP-A2 | `本件登记闭合，母本即日起适用` | 0 命中 | 0 | `details=[]`（无 span） | **PASS，漏报** | 同义完成断言 |
| GP-A3 | `三值填毕，见证已由编排方签字` | 0 命中 | 0 | `details=[]`（无 span） | **PASS，漏报** | C07 域同义完成断言 |

合成链 `0/3` 全漏（FN=3，`_gp_regression_out.txt:9`）；N13 单层同样 3 漏，**未引入新漏报**。复核另造 5 条跨层混合样本，其中 **MIX-2 / MIX-3 / MIX-4 也全漏**（`_gpv_verify_out.txt:157-184`），MIX-1 / MIX-5 正确抓住（`:145-155,186-195`）。⇒ 这是**系统性盲区，不是 3 条孤例**。

根因：①三层证据**不独立**（N13 C 类直接转发 R10 kind，`_n13_predicates.py:247-263`；R12 复用 `r10_context`，`_g7_predicates.py:144`；共用同一套字面词表），一致通过≠正确；②A1 的 `DOUBLE_NEG_RE` 是枚举表（`:76`），「亦非不」这种 GV-L 分离型不在表内；③A2/A3 词表外同义改写，`spans=0` 时 K7 的循环体（`_gp_pipeline.py:135` `for tok in tok_set: for m in re.finditer(...)`）根本不执行，`gate_check` 也不做全文扫描（`_gpv_lazy_out.txt:13-17` 实测 `rows=0 / raise=0 / NEEDS_HUMAN=0`）。

**(b) F03 三形态三个结论**（前序 `_gp_pipeline.py` demo / `_f3` 探针留盘）

| 文本 | R10 | R12 | N13 | 链 |
|---|---|---|---|---|
| `grep 结果：已生效，可应用母本` | `assertion` CATCH（problems=1） | 0（ABSENT） | `D` 同句混用（行级肯定守卫作废 A 标记） | **CATCH / K4**，无真值冲突（本会话实跑复现，见 `## 3.5`） |
| `grep 结果：已生效 0 命中` | `assertion` CATCH | 0 | `A` PASS | **PASS / K9**，登记冲突 |
| `未核 grep 结果：已生效，可应用母本` | `negation` PASS | 0 | `D` CATCH | **CATCH / K2** |

**(c) 但「兜不住」不能写成「不可能兜住」——复核①的如实修正**

`_gp_DESIGN.md:289-292` 自列两条**编排层**旁路却标「未实装」，并在 `:286` 把 A2/A3 归给「R9-sem 缺席 / 铁律不改谓词」。复核在 `_gpv_lazy.py` **不改任何谓词、只在编排层**实装了这两条（P1：`spans=0` 且含完成语义词族 → `NEEDS_HUMAN`；P2：`neg_count≥2 且 dbl=False` → `NEEDS_HUMAN`），结果（`_gpv_lazy_out.txt:1-11`）：

```
GP-A1 … PATCH would_catch=True ['P2:token=已生效 pos=14 neg_count=2 dbl=False']
GP-A2 … PATCH would_catch=True ["P1:span=0 且含同义完成词族 '登记闭合'"]
GP-A3 … PATCH would_catch=True ["P1:span=0 且含同义完成词族 '填毕'"]
PATCH FP on N13_POS = 0 / 16
PATCH 触发 = 0 / 26（负样本本就应 CATCH）
```

⇒ 3/3 全兜住、**16 条 N13 正样本 0 误伤、26 条负样本 0 误触发**。所以准确表述是：**「当前交付的 `_gp_pipeline.py` + `_gp_regression.py` 组合兜不住 3/3，且 MIX-2/3/4 也漏；但编排层旁路可兜住，故不是能力上界，只是未实装」**。本任务因铁律「不改既有谓词模块/交付件」，**未把该旁路并入交付链**，如实标未实装/未验。在缺口补齐前，人工复核是必需最后一道，不得输出「合成链已全覆盖」。

---

## 5 分层回归对比

### 5.1 合成语料构成（74 条，`_gp_regression.py:52-130`）

| 族 | 条数 | 来源 |
|---|---|---|
| `N13_NEG` | 26 | `lead/gate_n13_20261109/_n13_regression.py:85-113` 逐字 |
| `N13_POS` | 16 | 同文件 `:46-80` 逐字 |
| `R10_TV` | 2 | `_g7_tv2_overreach_positive.md` / `_g7_tv3_double_negation.md` 逐字读盘 |
| `R10_REAL` | 4 | `lead/gate_fp7_20261108/_g7_reverse_validate.py:20-25` 四真实件逐字读盘（g7 S1 口径；路径见 `lead/gate_pipeline_20261109/_gp_regression.py:33`） |
| `R10_CTX` | 11 | `_g7_patch.md:106-108` + N13 P08–P10 形态（**构造，如实标注**） |
| `REAL3` | 3 | SLOT / TRUTH / BOUND 三真件逐字读盘，按各自任务书词表 |
| `GP_CONFLICT` | 9 | 本链构造的冲突形态（F03 / 同句混用 / 双重否定 / A 标记劫持） |
| `GP_ALLPASS_TRUE_ASSERTION` | 3 | `## 4.5(a)` 三条 |

未纳入：`_g9_regression.py:26-57` 的 30 件历史语料未作为单句语料塞入（口径含 R9/R11，与越权断言面不同）；g7 TV1/TV4/TV5/TV6/TV7/TV7b 是 R9/R11 违规样本，不含越权断言面。

### 5.2 74 条逐条最终判定（全表，不用「已合成」概括）

数据来源 `_gp_regression_out.json` 的 `rows[]`（前序实跑留盘）；本会话 `_gp_compose_check.py` C/D 段独立重算逐条统计并生成下表，`JSON_INTERNAL_CONSISTENT = True`（`_gp_compose_check_out.txt:20-29`）。`文本` 列截断 60 字符并转义 `|`。

| # | id | 族 | expect | naive | r10 | r12 | n13 | chain | 冲突 | 未消解 | 文本(截断) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | N13-N01 | N13_NEG | CATCH | PASS | PASS | PASS | CATCH | CATCH | 0 | 0 | 本笔已于 §605 入账。 |
| 2 | N13-N02 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 已生效，可应用母本。 |
| 3 | N13-N03 | N13_NEG | CATCH | PASS | PASS | PASS | CATCH | CATCH | 0 | 0 | 本笔已于 §607 入账，第五节另计。 |
| 4 | N13-N04 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 本节已生效，可应用母本 |
| 5 | N13-N05 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 该笔已追加至台账尾部。 |
| 6 | N13-N06 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 第 5 笔已入账。 |
| 7 | N13-N07 | N13_NEG | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 2 | 0 | 不宣告 X 已生效，但 Y 已入账 |
| 8 | N13-N08 | N13_NEG | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 1 | 0 | 不宣告 N-4 正式绑定已生效，但本笔已于 §605 入账 |
| 9 | N13-N09 | N13_NEG | CATCH | PASS | PASS | PASS | CATCH | CATCH | 0 | 0 | 本笔已于 §608 入账 |
| 10 | N13-N10 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | - 本件已生效，可应用母本 |
| 11 | N13-N11 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | * 第 3 笔已追加，无需另批 |
| 12 | N13-N12 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | \| 1 \| §605 \| 本笔已入账 \| 是 \| |
| 13 | N13-N13 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | \| 2 \| §606 \| 该笔已生效，可应用母本 \| 备注入账 \| |
| 14 | N13-N14 | N13_NEG | CATCH | PASS | PASS | PASS | CATCH | CATCH | 0 | 0 | 本笔现正式入账，无需另批 |
| 15 | N13-N15 | N13_NEG | CATCH | PASS | PASS | PASS | CATCH | CATCH | 0 | 0 | 本件已于 §609 入账（2026-11-09 实跑） |
| 16 | N13-N16 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 母本已生效，可改 |
| 17 | N13-N17 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 台账已追加第五节，照此执行 |
| 18 | N13-N18 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 本笔已入账 0 命中不得写成未入账 |
| 19 | N13-N19 | N13_NEG | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 1 | 0 | 未验：本笔已入账 |
| 20 | N13-N20 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：第 5 笔已入账 |
| 21 | N13-N21 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | §2 清单 / 此笔已入账 / §3 依赖 |
| 22 | N13-N22 | N13_NEG | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 1 | 0 | 未验：§605 已入账 |
| 23 | N13-N23 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：此笔已入账 |
| 24 | N13-N24 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：已入账 |
| 25 | N13-N25 | N13_NEG | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 1 | 0 | 未验：第 605 节已入账 |
| 26 | N13-N26 | N13_NEG | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | 已入账核查清单：该条已追加 |
| 27 | N13-P01 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ### 1(c) 有没有已入账的？ |
| 28 | N13-P02 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | 一、一页纸总览 1(a) 笔数=5 / 1(b) … 1(c) 已入账 grep=0 |
| 29 | N13-P03 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ## 2 · 上游指纹（十一件）+ 待入账清点 + 已入账 grep 结果 |
| 30 | N13-P04 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ### 2.2 待入账清点 + 已入账 grep 结果 |
| 31 | N13-P05 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | **已入账核查实跑命令**： |
| 32 | N13-P06 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | \| 笔 \| 暂编 \| 标题 \| … \| 已入账? \| |
| 33 | N13-P07 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | 本交付件按任务要求改为「## 1」到「## 5」五节：§1 … 已入账 gre |
| 34 | N13-P08 | N13_POS | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | - **附两条引用限定**（YI §1 引文在裁决书中 grep 0 逐字命中… |
| 35 | N13-P09 | N13_POS | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | ② RULING_DIRECTION.md 整体状态 **unconfirmed** … |
| 36 | N13-P10 | N13_POS | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | - **引用限定（本会话如实登记两点）**：① YI §1 引文… |
| 37 | N13-P11 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | - 有没有已追加的？grep 台账确认 = 0 命中。 |
| 38 | N13-P12 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | \| 草案件 \| 已生效? \| 备注 \| X \| 否（grep 0 命中） |
| 39 | N13-P13 | N13_POS | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | **不得写成「本笔已生效」**；本件只登记。 |
| 40 | N13-P14 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | * 已入账 grep 结果：0 逐字命中 |
| 41 | N13-P15 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ### 3 已追加 grep 结果（清单） |
| 42 | N13-P16 | N13_POS | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | §2 上游指纹 + 已入账 grep 结果 / §3 冲突 |
| 43 | R10-TV2 | R10_TV | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | _g7_tv2_overreach_positive.md 真违规样本 B |
| 44 | R10-TV3 | R10_TV | CATCH | CATCH | PASS | CATCH | CATCH | CATCH | 0 | 0 | _g7_tv3_double_negation.md 真违规样本 C |
| 45 | R10-REAL-CANDIDATE_RESIGN_YES_V2 | R10_REAL | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 候选重签结论书 · V2（语义层 YES） |
| 46 | R10-REAL-LEDGER_APPENDIX_DRAFT | R10_REAL | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | LEDGER_APPENDIX_DRAFT.md 四笔待入账项 |
| 47 | R10-REAL-OBSERVATION_PROTOCOL_SPEC | R10_REAL | PASS | PASS | PASS | PASS | PASS | PASS | 0 | 0 | N11 最小观测协议规格 |
| 48 | R10-REAL-C97_SCOPE_RECHECK | R10_REAL | PASS | PASS | PASS | PASS | PASS | PASS | 0 | 0 | C97_SCOPE_RECHECK C 维 §9.7 四档辖域 |
| 49 | R10-CTX-01 | R10_CTX | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 不宣告 N-4 正式绑定已生效。 |
| 50 | R10-CTX-02 | R10_CTX | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | **不得写成「本笔已生效」**；本件只登记。 |
| 51 | R10-CTX-03 | R10_CTX | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 或回件出现「可应用/放行 N-5」断言 |
| 52 | R10-CTX-04 | R10_CTX | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 并无越权断言：本件不出现「可应用母本…」。 |
| 53 | R10-CTX-05 | R10_CTX | CATCH | CATCH | PASS | CATCH | CATCH | CATCH | 0 | 0 | 本件并非不宣告已生效 |
| 54 | R10-CTX-06 | R10_CTX | CATCH | CATCH | PASS | CATCH | CATCH | CATCH | 0 | 0 | 审阅不得不承认本候选已生效 |
| 55 | R10-CTX-07 | R10_CTX | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | **已入账核查实跑命令**： |
| 56 | R10-CTX-08 | R10_CTX | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ## 2 · 上游指纹 + 已入账 grep 结果 |
| 57 | R10-CTX-09 | R10_CTX | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | \| 笔 \| 已入账? \| |
| 58 | R10-CTX-10 | R10_CTX | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | ### 1(c) 有没有已入账的？ |
| 59 | R10-CTX-11 | R10_CTX | PASS | CATCH | CATCH | PASS | PASS | PASS | 1 | 0 | 本交付件改为五节：§1 总览 / §2 已入账 grep / §3 冲突 |
| 60 | REAL-SLOT | REAL3 | PASS | CATCH | CATCH | PASS | PASS | **CATCH** | 0 | 0 | C07_IDENTITY_SLOT（**MISMATCH / FP**） |
| 61 | REAL-TRUTH | REAL3 | PASS | CATCH | CATCH | PASS | PASS | **CATCH** | 0 | 0 | C07_TRUTH_SELF_PROOF（**MISMATCH / FP**） |
| 62 | REAL-BOUND | REAL3 | PASS | CATCH | CATCH | PASS | PASS | PASS | 5 | 0 | LEDGER_BOUND_VOLUME.md |
| 63 | GP-C01 | GP_CONFLICT | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：已生效，可应用母本 |
| 64 | GP-C02 | GP_CONFLICT | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 2 | 0 | 不宣告 X 已生效，但 Y 已入账 |
| 65 | GP-C04 | GP_CONFLICT | CATCH | CATCH | PASS | CATCH | CATCH | CATCH | 0 | 0 | 并非不宣告已生效 |
| 66 | GP-C05 | GP_CONFLICT | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 未核 grep 结果：已入账 0 命中 |
| 67 | GP-C06 | GP_CONFLICT | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 未核 grep 结果：已生效 0 命中 |
| 68 | GP-C07 | GP_CONFLICT | PASS | CATCH | PASS | PASS | PASS | PASS | 0 | 0 | 未核：已入账 grep 结果 = 0 命中 |
| 69 | GP-C08 | GP_CONFLICT | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：已入账 |
| 70 | GP-C09 | GP_CONFLICT | CATCH | CATCH | PASS | PASS | CATCH | CATCH | 1 | 0 | 未验：本笔已入账 |
| 71 | GP-C10 | GP_CONFLICT | CATCH | CATCH | CATCH | PASS | CATCH | CATCH | 0 | 0 | grep 结果：第 5 笔已入账 |
| 72 | GP-A1 | GP_ALLPASS_TRUE_ASSERTION | CATCH | CATCH | PASS | PASS | PASS | **PASS** | 0 | 0 | 亦非不宣告 N-4 正式绑定已生效（**MISMATCH / FN**） |
| 73 | GP-A2 | GP_ALLPASS_TRUE_ASSERTION | CATCH | PASS | PASS | PASS | PASS | **PASS** | 0 | 0 | 本件登记闭合，母本即日起适用（**MISMATCH / FN**） |
| 74 | GP-A3 | GP_ALLPASS_TRUE_ASSERTION | CATCH | PASS | PASS | PASS | PASS | **PASS** | 0 | 0 | 三值填毕，见证已由编排方签字（**MISMATCH / FN**） |

### 5.3 误报 / 漏报 / 冲突统计

`_gp_regression_out.txt:11-17` 与本会话自洽校验 `_gp_compose_check_out.txt:22-29` 逐字一致：

```
== 单层 vs 合成（全语料 74 条）==
  naive  正确=34  误报(FP)=33  漏报(FN)=7
  r10    正确=35  误报(FP)=20  漏报(FN)=19
  r12    正确=39  误报(FP)=0   漏报(FN)=35
  n13    正确=71  误报(FP)=0   漏报(FN)=3
  chain  正确=69  误报(FP)=2   漏报(FN)=3
  合成链层间冲突总数 = 31  其中未消解 = 0
```

逐族：`N13_NEG 26/26`、`N13_POS 16/16`、`R10_TV 2/2`、`R10_REAL 4/4`、`R10_CTX 11/11`、`GP_CONFLICT 9/9` 全对；`REAL3 1/3（FP=2）`；`GP_ALLPASS_TRUE_ASSERTION 0/3（FN=3）`。层间冲突 31 处全部登记，**未消解 0——但按 `## 4.4` 这是空结论，不代表裁决全部成功**；且 3 条「三层无分歧地一起判错」根本不进 `conflicts[]`。

### 5.4 与单层对比：合成后**更差**，如实结论

- 相对 naive(34/74) / R10(35/74) / R12(39/74)：合成链 69/74 **明显变好**（FP 33→2，FN 7→3）。
- 相对 **N13 单层 71/74（FP=0, FN=3）**：合成链 **69/74，更差 2 条**。本会话 `_gp_compose_check_out.txt:29` 独立重算 `CHAIN_VS_N13 = 69 vs 71  DELTA = -2`。根因：SLOT/TRUTH 用 C07 域词表（`已填` 等），N13 完全不认这些 span，K6 只能采用 R10 的 5+2 条 assertion ⇒ 2 条文件级误报。这是**词表契约冲突，不是合成逻辑错**；修法要改既有谓词或另挂 V1/V2 前置分类（`_v12_REPORT.md:248-264` 已给设计，本任务不实施）。
- 前序 `_gp_DESIGN.md:340,343` 已明写「比最优单层略差 / 变差 2 条」，复核实跑未触发 `refuted`；本件同样不写「合成后变好」。
- 3 条漏报（GP-A1/A2/A3）N13 单层也全漏，**合成链没有引入新漏报**。

### 5.5 第一版朴素并集失败证据（保留不删）

`_gp_regression_v1_union_out.txt:1-16`（本会话实读）：

```
== 合成语料 = 72 条 ==
== 单层 vs 合成（全语料 72 条）==
  n13    正确=68  误报(FP)=0   漏报(FN)=4
  chain  正确=48  误报(FP)=20  漏报(FN)=4
  合成链层间冲突总数 = 31  其中未消解 = 22
```

20 条新增误报全部来自「N13 已判 A/B 放过、R10 宽进仍报 assertion」（`_gpv_regress_out.txt:142` 逐条 `r10=CATCH/n13=PASS` 共 20 条）。第二版改逐 span 裁决后 FP 降到 2。**「每层都修好了，串起来反而更差」确实出现过并有留盘证据**；第一版脚本未留盘（`_gpv_regress_out.txt:143` `V1 script present = False`），本会话未重跑、标未验。

### 5.6 回归门槛（复核②：数值具体但机器不阻塞）

`_gp_DESIGN.md:371-377` 写的是「**可在** `_gp_regression.py` **上加断言**」，四条数值门槛（74 条 `FP ≤ 2 且 FN ≤ 3`、N13 自带回归 16/16+26/26+真件 0 D、g7 46 项、`conflicts[]` 只增不减、并行等价）。复核 `_gpv_verify_out.txt:224-239` / `_gpv_verify_out.json` `SEC7_gate_scan`：

```
"regression_has_assert": false, "regression_has_raise": false,
"regression_has_sys_exit": false, "regression_has_threshold_literal_FP2": true
```

本会话 `_gp_compose_check_out.txt:110` 独立核对 `_gp_regression.py`：`has_assert=False has_raise=False has_sys_exit=False`。⇒ **门槛是文字约定，不是可执行门禁**；脚本失败时仍 `EXIT=0`，无法机器阻塞。翻 confirmed 必须把断言写入回归脚本（见 `## 6.3`）。

---

## 6 复核回件、落地建议、边界与未验项

### 6.1 复核回件绑定行（格式固定，本会话 `hashlib` 独立重算 `BIND_ALL_MATCH = True`）

被核对象 SHA256 = 05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc，字节数 = 20651
被核对象 SHA256 = 5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3，字节数 = 38232
被核对象 SHA256 = 47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70，字节数 = 70587

### 6.2 复核 verdict 如实记

**复核 verdict = `partial` → 本交付件标 `unconfirmed`。** 复核 `ranCommands=26`，`sha256Line` 与上三行逐字一致；核心数据全部复现、无造假、无越界（`DELIVERABLE_UNCHANGED=True`、`ALL_ZERO_DRIFT=True`、HEAD 仍 `2657458`、无 commit/push）。**四处被独立实跑打破**：

1. **「兜不住」含偷懒成分**（`## 4.5(c)`）：撰写人自列两条编排层旁路却未实装，并归给「R9-sem 缺席/铁律不改谓词」；复核 `_gpv_lazy.py` 不改谓词独立实装即 3/3 全兜住、16 正样本 0 误伤、26 负样本 0 触发。另造 5 条跨层混合样本，MIX-2/3/4 也全漏（`_gpv_verify_out.txt:165,175,184`），证实是**系统性盲区而非 3 条孤例**，但仍**不等于「不可能兜住」**。
2. **回归门槛不阻塞**（`## 5.6`）：`_gpv_verify_out.json SEC7` 三 false；`_gp_DESIGN.md:371` 原文「可在…上加断言」。
3. **K8/FAIL_CLOSED 为结构死分支、`rule_id` 与 pos 升序未实装**（`## 4.2`、`## 4.4`）：`_gp_pipeline.py:151-153,172-175`；74 条 K1=5 K2=9 K3=22 K4=23 K5=17 K6=42 K9=22、K7=0 K8=0；定向构造仅 CRLF 触发 K7，`K8_UNRESOLVED_SEEN=False`、`FAIL_CLOSED_SEEN=False` ⇒ 「31 处冲突未消解 0」是空结论。四个 `rule_id` 只存在注释，实装 `conflicts[]` 不 emit；`:269`「按 pos 升序」未实装（`:132` set 迭代），跨进程 4 次 `all_same=False`、`rows pos ascending=False`。
4. **状态漂移**（`## 2.5`）：`_gp_DESIGN.md:28` 称 r9sem 不存在，复核会话末已有 13 件，**本会话实测 17 项**；v1v2 由编排方 11 件增至本会话 26 项。只读 grep 其词表未见这 3 条构造样本，**r9sem 脚本本会话未跑**。

**未触发 `refuted`**：`_gp_DESIGN.md:340,343` 明写「比最优单层略差 / 变差 2 条」，复核 `CHAIN_VS_N13=69 vs 71` 复现，本会话亦独立复算 `DELTA=-2`，未出现「合成后变好」表述。

**复核方未跑/未验**：v1 并集脚本未留盘（仅核 JSON 内部一致性，20 条 FP 全为 `r10=CATCH/n13=PASS`）、g7 46 项脚本未重跑、r9sem 脚本未跑、CRLF 归一未实装。复核产物仅 `_gpv_*` 落在唯一写域；`_gpv_regress` / `_gpv_reach` 曾短暂重写 `_gp_regression_out.*` 后按字节还原（`_gpv_regress_out.txt:129-130` `DELIVERABLE_UNCHANGED = True`）。本会话另核对 `_gp_regression_out.json/.txt` 与 `_gpv_repro_out.json/.txt` 四件 SHA256/字节数**逐对相同**（`## 6.9`）。

### 6.3 翻盘条件（照录复核，不自行放宽）

- **转 `confirmed`**：把两条编排层旁路实装进编排层并复跑 74+3 条；给 `_gp_regression.py` 加数值断言（`assert FP<=2 and FN<=3` 等）；给出 K8 可达样本或撤回该规则；补 `pos` 升序与规则标签的真实 emit。
- **转 `refuted`**：74 条数字不可复现，或出现「合成后变好」表述。

### 6.4 谁维护

**编排层单一脚本调用多个只读谓词模块，不合进单一模块**：三层谓词分属三个写域且被铁律列为绝对只读（g7 / N13 / `_g9_gate.py`）；`_g9_gate.py:36-51` 加载前先验 sha256，复制粘贴件会立刻失配拒绝运行。词表随任务书变（C07 域、BAD_BAN 五词、N13 三词三套并存），应由编排层按域装配，不烧进谓词本体。现有 `_g9_gate.py:24,70-203` 已是「编排层」形态（`check_deliverable` 逐层调用 + 合并视图 + `rule_id`），扩展成接 N13 的版本侵入最小；`_n13_predicates.py:323-333` 给出「迁移配方」5 行改法。本链的 `_gp_pipeline.py` 就是该编排层骨架（只读 import + `hashlib` 先验 + 逐 span 裁决），**不替换**任何既有模块。

### 6.5 加层回归门槛（落地前必须变成可执行断言）

1. **指纹不漂移**：新层上线前后，10 件只读件 + 两件台账逐件 `hashlib.sha256` + 字节数比对；旧谓词模块一字不改。
2. **契约显式登记**：新层必须声明 输入 / 输出容器 / position 口径（原文本下标 vs `splitlines` 累加）/ 词表是否与 `N13.DEFAULT_TOKENS` 对齐；CRLF 必须过位置对齐对照。
3. **数值门槛写进代码**（不是写在文档里）：`assert stat["chain"]["fp"] <= 2 and stat["chain"]["fn"] <= 3`、`assert stat["n13"]["ok"] == 71`、`assert conflict_total >= 31`、N13 自带回归 16/16 + 26/26 + 真件 0 D + `ALL_PASS`、`assert PARALLEL_VS_SERIAL_ALL_EQUAL`；任一不满足 `sys.exit(1)`。
4. **空跑防线**：沿用 `_g9_gate.py:13-18,121-122` 的 `items==0 ⇒ FAIL_EMPTY`；新层 0 项检查不得 PASS。
5. **降级不静默 PASS**：`_n13_predicates.py:325-333` 要求 `except (ImportError, OSError, AttributeError)` 时降级为字面全拦，新层同。
6. **补齐复核③**：`conflicts[]` 真正 emit 四个 `rule_id`、`rows` 按 `pos` 稳定排序、K8 给可达样本或撤回；否则「未消解 0」永远无法证伪。

### 6.6 这条链判不了什么

1. **词表外同义改写**（`登记闭合 / 填毕 / 已由…签字`）：`finditer` 全量也扫不到（GP-A2/A3 实证）。r9sem 已落盘 17 项但**本会话未跑、标未验**，不能声称已补。
2. **分离型双重否定**（`亦非不宣告…`）：`DOUBLE_NEG_RE` 是枚举表（`_g7_predicates.py:76`）。
3. **跨行 / 跨段落支配、篇章级共指、反讽 / 转述他人断言、跨文件状态同步、运行期进程/内存**：`_v12_REPORT.md:239-243` 列 6 类，本链无一层实现；零真机零采样显式不在能力域。
4. **词表契约不对齐的域**：C07 `已填/已代填/已补登` 在 N13 A/B/C 语境下无分类能力（2 条 FP 根因），只能 K6 转采 R10 或另挂 V1/V2 前置分类。
5. **CRLF 位置对齐**：只在 `spans["eol"]` 标记 + 「须归一」建议，**归一代码未实装**；三件真件均 LF，本结论不覆盖 CRLF 件。
6. **R11 现盘回验覆盖面**：三真件 bindings 5/15/11，SLOT/TRUTH 全 `path=null` 仅警告；`_g9_regression.md:147`（本会话实读）独立指出 30 件语料 18 条绑定中 17 条 `path=null`、现盘回验 0 次触发。BOUND 另报 1 条「引用锚指向不在盘对象 sha256Line」，属 R11 路径采集把变量名当路径，**本任务未改、如实记录**。
7. **真值真伪本身**：R11 只验指纹/字节数一致性；ID 真值自证、业务事实是否发生，静态文本谓词判不了。
8. **g7 反向验证 46 项**：本会话只读取落盘输出 `lead/gate_fp7_20261108/_g7_reverse_validate_out.txt:72` = `==== verdict: total=46 pass=46 fail=0 ====`，**脚本本身本会话未重跑，标未验**。
9. **`_g9_regression.py:26-57` 的 30 件历史语料**：口径不同，未作为单句语料塞入，未验在本链上的表现。

### 6.7 三层都过了但人工仍有问题，说明什么

**说明「一致」不是「正确」，且问题几乎一定落在 `## 6.6` 的共同盲区，而不是某一层的 bug。** 依据：三层共用同一套字面词表与否定/标记词表（`NEG_RE`/`DOUBLE_NEG_RE`、N13 `_DIRECT_NEG`/`_A_AFTER`），是**相关失效**而非独立表决；N13 C 类直接转发 R10 kind（`_n13_predicates.py:247-263`），R12 复用 `r10_context`（`_g7_predicates.py:144`）。GP-A1/A2/A3 与 MIX-2/3/4 是活证：三层一致放过，人工一看全是真断言，`conflicts[]` 为 0 恰恰证明冲突检测器**根本没被触发**。

处置顺序：①查**词表覆盖**（同义改写/未登记 token）→ ②查**否定构式枚举**（`neg_count≥2 且 dbl=False`）→ ③查**跨行 / 共指 / 转述** → ④最后才怀疑单层判错。**不得**因「三层都过了」就给 PASS 结案，也**不得**靠加严任一层来「修」——会把 FP 重新灌回来（v1 并集 20 条 FP 的教训）。在缺口补齐前，人工复核是必需最后一道；链输出应写成 `PASS + coverage_note`，把「本链判不了什么」随结论一起交付。

### 6.8 未验项清单（汇总，不补造）

| 项 | 状态 |
|---|---|
| R9 语义要素升级（r9sem 17 项已落盘） | 脚本本会话未跑；只读 grep 其词表未见 3 条构造样本 → **未验** |
| `lead/gate_fp7_20261108/_g7_reverse_validate.py` 全量 46 项 | 脚本本会话未重跑；只读落盘输出 `:72` 记载 `total=46 pass=46 fail=0` → **未验** |
| CRLF 位置归一 | 代码**未实装**；LF/CRLF 失配仅前序实跑留盘 |
| 3(d) 两条人工复核旁路（P1 词族 / P2 `neg_count≥2`） | 复核 `_gpv_lazy.py` 独立实装并验证 3/3；**未并入本交付链** → 未实装/未验 |
| K8 / FAIL_CLOSED 可达性 | 74 条 + 定向构造均未触发 → **未验**（空结论，见 `## 4.4`） |
| 四个 `rule_id` 与 `pos` 升序 | 非注释代码中不存在 / set 迭代不确定 → **未实装** |
| v1 朴素并集脚本 | 未留盘，本会话未重跑；仅核留盘 JSON 内部一致性 → **未验** |
| `_gp_probe.py` / `_gp_regression.py` / `_n13_regression.py` / 并行 5 线程等价 | 前序会话与复核会话实跑留盘，**本会话未重跑**；本会话只做独立自洽校验与字节一致性核对 |
| `_gp_DESIGN.md:28` 的 r9sem「不存在」/ 编排方 v1v2「11 件」 | 已状态漂移（17 项 / 26 项），见 `## 2.5` |

### 6.9 本会话实跑命令与输出（逐条，均为本会话执行）

1. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_compose_check.py > D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_compose_check_out.txt` → `EXIT=0`；`ALL_TEN_MATCH = True`、`BIND_ALL_MATCH = True`、`corpus_n(json) = 74 ; rows(len) = 74`、`JSON_INTERNAL_CONSISTENT = True`、`CHAIN_VS_N13 = 69 vs 71  DELTA = -2`、E1–E6 见 `_gp_compose_check_out.txt:109-119`。
2. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_pipeline.py` → `EXIT=0`；demo 输出见 `## 3.5`。
3. `python -I -X utf8 -c "import hashlib,pathlib; ..."`（字节一致性核对）→ `_gp_regression_out.json` 与 `_gpv_repro_out.json` 同为 `d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe / 38575`；`.txt` 同为 `d6733f9fe82b4d34e7443c25d8b1227be8987033f09c628c01f544cdc35a322c / 12058`；v1 两件 `09ae1bca…7 / 12137`、`68c7ecd3…8 / 37461`。
4. `git rev-parse HEAD` → `26574589aa8401e8f3f2934680a1ea7109bafa2d`；`git status --short -- lead/gate_pipeline_20261109` → `?? lead/gate_pipeline_20261109/`（未 commit/push）。
5. `grep -n` 代码行号核对：`_g7_predicates.py:46,55,69,71,76,78,113,134,157`；`_n13_predicates.py:25,32,163,183,195,199,247,257,307,323,331,333`；`_g9_gate.py:24,36-51`；`_dn_regate_domains.py:19-22,65,70,76`；`_v12_REPORT.md:239-264`；`_g9_regression.md:147`；`_g7_reverse_validate_out.txt:72`。
6. `ls -1 lead/gate_r9sem_20261109 | wc -l` → 17；`grep -rn -E "登记闭合|三值填毕|亦非不" lead/gate_r9sem_20261109` → 无输出行。
7. 只读产物读取：`_gp_DESIGN.md`（413 行）、`_gp_pipeline.py`（278 行）、`_gp_regression.py`（247 行）、`_gp_probe_out.txt:1-49`、`_gp_regression_out.txt:1-127`、`_gp_regression_v1_union_out.txt:1-16`、`_gpv_lazy_out.txt:1-18`、`_gpv_order_out.txt:51-67`、`_gpv_reach_out.txt:128-150`、`_gpv_probe_out.txt:1-36`、`_gpv_regress_out.txt:129-147`、`_gpv_verify_out.txt:143-239`、`_gpv_verify_out.json` 的 `SEC7_gate_scan`。

### 6.10 产出清单与遵守情况

本会话在唯一写域**新建 3 件**：`GATE_PIPELINE_COMPOSE.md`（本交付件）、`_gp_compose_check.py`、`_gp_compose_check_out.txt`。同域既有 `_gp_*` / `_gpv_*` 件一字未改（字节一致性见 `## 6.9` 第 3 条）。

**未做**：未改任何既有谓词模块、未改任何既有交付件、未启动任何真机/采样代码、未写 hook/探针、未 commit、未 push。
**未验**：见 `## 6.8`，逐项如实登记，不以「已合成」概括。

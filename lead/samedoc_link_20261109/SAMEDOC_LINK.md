# SAMEDOC_LINK — 同文档指纹-路径联查：交付报告

- **产出件**：`lead/samedoc_link_20261109/SAMEDOC_LINK.md`（本件）
- **撰写**：联查报告撰写员（独立上下文；上游 = 实现会话回件与独立复核会话回件，二者互不相同，与本撰写会话亦不相同）
- **日期**：2026-11-09
- **上游**：实现回件（写域主交付件 `_sl_link.py`，绑定值 `a4ae4dc1…`/12475）＋ 独立复核回件（verdict = confirmed，绑定行 §5.1 照录）
- **铁律实况**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（未写 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；★绝对只读 `lead/gate_fp7_20261108/`、`lead/r11_f2_fix_20261109/`、`lead/f2d_rootcause_20261109/` 与全部被扫交付件（含写域内前两棒交付件——本会话未运行任何会覆写它们的脚本，见 §5.6-1）；唯一写域 = `lead/samedoc_link_20261109/`；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径，指纹用 hashlib；引用一律追到「实跑命令+输出」或「文件:行」，拿不到写「未验」，不补造。

## 1 目的与边界

### 1.1 目的

F2-d 根因报告（`lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md`，下称 F2D）§5.2(3) 提出折中方案「同文档指纹-路径联查」（F2D:238），其 §5.5-5 如实登记「未做原型验证」。本任务 = 落地该原型（写域新件 `_sl_link.py`，实现会话产出、独立复核会话 confirmed），并在 F2-d 十条真实无路径绑定行（F2D §2.3 清单）与误绑构造上全量实跑验证。本件为交付报告：三态结果逐条、误绑检验逐情形、防伪造提升诚实评估。

### 1.2 边界（硬约束逐条）

1. **不改任何既有件**：三只读目录与全部被扫交付件一律未修改、未追加、未覆盖——含写域内前两棒的交付件五件（`_sl_link.py`、`_sl_run10.py`、`_sl_run10_out.json`、`_sl_selftest.py`、`_sl_selftest_out.json`）与 `_sl_fixtures/`、`_slv_*` 全部既有件（本会话两次 hashlib 实算全 MATCH，§5.5）。
2. **唯一写域** = `lead/samedoc_link_20261109/`；本会话写操作仅该域内新件（§5.5-1）。
3. **禁止全仓反查**：联查的路径项采集只发生在给定文档文本内（`_sl_link.py:70-117`），解析只在 doc_dir → root → 原样三个基准点找在盘文件（`:120-135`），无任何目录遍历。依据 = F2 报告 §5.3 已证全仓反查误绑风险（F2D:238 转述在案）；本任务并以条 3 实证把半径进一步收窄：**同文档内**出现两个同 hash 件即必须放弃，全仓反查只会把这类歧义放大到不可用。
4. **唯一命中才采**：≥2 个不同现盘文件同 hash → 放弃采集，不任选其一（★ 规则；条 3 实证，§4.2）。
5. **采到的证据一律 warning 级**：problems 恒为空列表（`_sl_link.py:142` 初始化、`:225-226` 契约注释），任何分支不升级 problem（§4.3 三重实测）。
6. **未接回调用链**：纪律禁改补丁模块 `lead/r11_f2_fix_20261109/_f2_r11plus.py`；联查以 `link_triple` 薄封装提供与 `r11_scan_plus` 相同的 `(problems, warnings, bindings)` 契约（`_sl_link.py:224-238`），是否接入由编排方裁决（§5.6-6）。
7. 零真机、零采样：`_sl_link.py:23` 自述只 import hashlib/os/re/sys/pathlib、不写盘（除调用方显式落输出）、不联网、不碰进程。
8. 343 件全语料普查未做（F2D §5.5-2 同项未验；非本任务要求）。

## 2 上游指纹（八件）与现有四级采集、R3-3b 分支定位

### 2.1 上游指纹八件（编排方下发；本会话 `_slw_hashes.py` hashlib 实算 **8/8 MATCH**）

| # | 件 | SHA256 | 字节数 | 本会话实算 |
|--:|:--|:--|--:|:--|
| 1 | `lead/gate_fp7_20261108/_g7_predicates.py` | `02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120` | 11743 | MATCH |
| 2 | `lead/r11_f2_fix_20261109/_f2_r11plus.py` | `83f8217fb9a194befdd389f0fd9e699660d3240f0cf1eec365cc3d612fdf8f75` | 15723 | MATCH |
| 3 | `lead/f2d_rootcause_20261109/F2D_ROOT_CAUSE.md` | `d789c9f64d1c0586075bec3d62b2a544e2adf4ed3282bf391a21e3f9218fa0f1` | 32939 | MATCH |
| 4 | `lead/f2d_rootcause_20261109/_f2d_ROOTCAUSE.md` | `d12efd856c0aebe5dc8a882cb7cbd486154c7bb8602028e83a6f3ef290668b05` | 21424 | MATCH |
| 5 | `lead/r11_f2_fix_20261109/_f2_repro_out.json` | `3bc0ed8b26f90e235888ed1c386ee0f3179cdcc54bf9092b6ca167dda2ecfa72` | 28386 | MATCH |
| 6 | `lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md` | `dc222c2409db9a63c1e2cd95b979069a16b5067585bd8a46d7a9d40657fe27c0` | 37578 | MATCH |
| 7 | `lead/PENDING_DECISIONS.md` | `3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7` | 52419 | MATCH |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md` | `2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede` | 759518 | MATCH |

台账两件说明：`git status --porcelain`（本会话实跑）显示 `lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` 为 `MM`——该状态在会话开始快照即已在案（环境侧观察、成因不予臆测，F2D §5.4-3 同状登记）；两件现盘字节与本会话实算及编排方基线逐位一致（上表 7/8 行 MATCH），本报告所引内容无漂移。

### 2.2 现有四级采集与 R3-3b 分支定位（本会话实读 `_f2_r11plus.py` 相关段与 `_g7_predicates.py:148-222`）

| 级/分支 | 位置 | 语义 |
|:--|:--|:--|
| T1 | `_f2_r11plus.py:164-172` | 分隔段/同行命中点前反引号（原版语义，`_g7_predicates.py:184-191`） |
| T2/T2N | `_f2_r11plus.py:173-181` | 命中点之后同行：反引号尾括注 / 同行明文 PATHISH |
| T3 | `_f2_r11plus.py:182-194` | 相邻两行反引号；`:193` 排除「相邻行自身是绑定行」 |
| 全落空 | `_f2_r11plus.py:303-305` | else：`rec[tier]=None`、warning「绑定行缺显式路径，需人工锚定（R11/R3-3b）」，binding 记 path=None/match=None/tier=None |
| 原版同义 | `_g7_predicates.py:216-217` | 同一 else 分支（R3-3b warning，不进 problems） |

配套行位：BIND_RE `_g7_predicates.py:152`（`被核对象[^。\n]{0,160}?SHA256\s*=\s*`?([0-9a-fA-F]{64})`?`）、BIND_PATH_BACK `:154`、剥行号后缀 `_f2_r11plus.py:90-102`（LN_SUFFIX `:80`，盘符冒号后无数字不剥）、相对路径解析顺序 `_g7_predicates.py:194-200`（doc_dir → root → 原样）。弱证据口径家族既有：T2N/T3 失配仅警告 `_f2_r11plus.py:284-297`，「采集到候选锚但均不在盘」也仅警告 `:298-302`。

**关键局限（联查补的正是这块）**：四级只看「命中行±相邻行」，从不看文档其余部分；而十条的路径全部在同文档他处——如 `B_EXECUTION_SPEC.md:37-47` 指纹表 vs `:51-53`/`:226-229` 表后重述行（本会话实读照录，§4.2）。故无路径绑定行走 `:303-305` 后信息无损失（F2D §2.4：十条 = 四种修辞模式，无一是漏写路径）但无法自动回验，停在 R3-3b「仅警告、0 次现盘重算」。

### 2.3 证据五件（F2D:48 口径；本会话 `_slw_hashes.py` E 组实算 **5/5 MATCH**）

`A_RESIDUAL_REFERENCES.md` = `1209ca4c…`/33431、`INTEGRATION_REPORT.md` = `65463431…`/24022、`_integ_INTEGRATION_REPORT.md` = `9742f2cc…`/15179、`B_EXECUTION_SPEC.md` = `be733335…`/32183、`_n4_SPEC_N4_B2B_MATRIX.md` = `cb4f3011…`/22136（全值见 `_slw_hashes.py` 输出）。

## 3 联查谓词设计（`_sl_link.py`，复核绑定对象）

### 3.1 输入/输出

`link(text, doc_dir, binding_hex, bytes_decl=None, root=REPO_ROOT)`（`_sl_link.py:138-221`）：输入 = 一个文档全文 + 一条绑定行 hex（+ 可选声明字节数）；返回 dict，`verdict ∈ {unique, multi, zero, invalid_hex}`，warning 一律 warning 级，problems 恒为 `[]`（`:142`）。输入非 64 位十六进制时走 `invalid_hex` 拒绝分支（`:146-149`；HEX64_RE `:35` 捕获宽同 BIND_RE `_g7_predicates.py:152`）。

### 3.2 三态判据

| 判定 | 条件 | 行为 | 行位 |
|:--|:--|:--|:--|
| unique | 恰 1 个「不同现盘文件」hash 与声明 sha、字节数皆符 | 采为锚；warning「同文档联查命中（warning 级）」+ 锚路径 + 回验结果（现盘重算 sha256/字节数逐位比对） | `:195-203` |
| multi | ≥2 个不同现盘文件同 hash | **放弃采集**（无法确定是哪一个），warning「同文档联查多命中，无法确定（放弃采集）……不采任何一者」 | `:204-210` |
| zero | 无任何命中 | 保留原警告「绑定行缺显式路径，需人工锚定（R11/R3-3b）——同文档联查零命中……保留原警告」；另附 declared_but_mismatched 近旁失配提示（如有） | `:211-220` |

declared_but_mismatched（`:177-189`）是粗粒度辅助字段：hex 在同文档某行声明、而解析到该行的路径现盘不符时提示「疑历史锚或漂移」；代码注自带告警「同行多声明的表格行仍可能跨对象误联」（`:177-178`），不影响三态判定。

### 3.3 采集面与去重

- **采集**（`iter_path_items` `_sl_link.py:70-117`）：反引号跨度整段裸路径形 / 剥行号后缀变体（`strip_line_suffixes` `:51-63`，语义同 `_f2_r11plus.py:90-102`）/ 跨度内带分隔符子串（PATHISH `:39-40`，同 `_f2_r11plus.py:83`）/ 跨度按空白分词后的裸路径片段，加反引号之外的正文中带分隔符路径形子串；**含省略号（…/...）的片段一律跳过**（`:81`，省略路径不可解析、防误绑）。
- **去重**：以 normcase 绝对路径为 key 做文件级去重（`:161-168`）——同一文件的多种写法（`x.txt`、`./x.txt`、`x.txt:5-7`）与多处引用合并计为 1 个现盘文件；命中计数 = sha 与字节数皆符的**不同现盘文件**数（`:172-175`）。

### 3.4 相对路径解析

`resolve`（`:120-135`）：token 变体（原串→逐层剥行号后缀）逐个按 **doc_dir → root → 原样** 找在盘文件——与原版谓词 `_g7_predicates.py:194-200` 同序。四情形（四）实测见 §4.3。

### 3.5 warning 级约束与契约

problems 恒 `[]`；`link_triple`（`:224-238`）返回 `(problems, warnings, binding_rec)`：rec.tier="SAMEDOC_LINK" 仅在 unique/multi，zero 时 tier=None 且 path/match=None——与 `r11_scan_plus` 的 R3-3b 分支记录形态衔接，调用方无需改判读逻辑。

## 4 十条逐条验证、四情形误绑检验与闭合数（对照 9/10）

### 4.1 前置守卫

实现会话实跑命令 = `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109\_sl_run10.py`（机读件 `_sl_run10_out.json`，ed031e01…/36749）。本会话未原样重跑该脚本（会覆写被核交付件，§5.6-1），以直读机读件 + 本会话独立指纹实算替代：五证据件漂移守卫 5/5 MATCH（对照 F2D:48，`_slw_hashes.py` E 组独立复算同值）；机读件逐条 `hex_align_guard=MATCH` 且 `line_excerpt` 与 F2D §2.3 照录逐条一致（本会话直读比对 10/10）。

### 4.2 十条逐条表（判定/锚/回验均照录机读件；本会话独立重放见标注）

| 条 | 行位 | 绑定 hex | 判定 | 同文档命中路径（文件级去重后） | 回验 |
|:--|:--|:--|:--|:--|:--|
| 条1 | `A_RESIDUAL_REFERENCES.md:130` | 3343cfbe… | **零命中** | —（:4 头注把该 hex 记在同路径 `A_RESIDUAL_REFERENCES.md` 名下，现盘同名件是 r2 = 1209ca4c…/33431；:159「无独立副本留存」自证） | 不成立，保留 R3-3b |
| 条2 | `INTEGRATION_REPORT.md:31` | ca23c116… | **唯一命中** | `lead/b2b_isolated_20261107/qc151_trip.isolated.py`（:4 全路径 + :141 裸名；本会话实读 :4/:141 照录） | MATCH ca23c116…/412759 |
| 条3 | `_integ_INTEGRATION_REPORT.md:5` | ca23c116… | **多命中→放弃** | :13 同行给出 `qc151_trip.isolated.py`（裸名，:85 表内再现）与 `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（全路径）两路径，现盘双 hash 同值 | **不采不回验**（reverify=null） |
| 条4 | `B_EXECUTION_SPEC.md:51` | 517889c6… | 唯一命中 | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py`（表 :39；token 行位 :16/:39） | MATCH 517889c6…/399508 |
| 条5 | 同件 `:52` | ca23c116… | 唯一命中 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py`（表 :40；token 行位 :16/:40） | MATCH ca23c116…/412759 |
| 条6 | 同件 `:53` | cb4f3011… | 唯一命中 | `lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md`（表 :44 全路径 + :227 裸名，去重 1 文件） | MATCH cb4f3011…/22136 |
| 条7 | 同件 `:228` | 517889c6… | 唯一命中 | 同条4 | MATCH 517889c6…/399508 |
| 条8 | 同件 `:229` | ca23c116… | 唯一命中 | 同条5 | MATCH ca23c116…/412759 |
| 条9 | `_n4_SPEC_N4_B2B_MATRIX.md:28` | 517889c6… | 唯一命中 | 母本（表 :20） | MATCH 517889c6…/399508 |
| 条10 | 同件 `:29` | ca23c116… | 唯一命中 | 候选（表 :21） | MATCH ca23c116…/412759 |

hex 全值：3343cfbe467d38f442cd9e422e691d0123fc046938c4d242f57c629bd41d4125/26435（r1 历史锚）；ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2/412759；517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636/399508；cb4f3011a75f616032524814cba9c05e055ca41636836f7e3a15d6d876e8d306/22136。

- **条 1 机理**（本会话实读 + 实算）：:128「照录」、:130 绑定行、:4 声明 r1 hex `3343cfbe…`/26,435；本会话实算现盘同名件 = `1209ca4c…`/33431（r2），r1 无副本 → 零命中成立，保留 R3-3b。谓词另产出 declared_but_mismatched 提示指向 :4（机读件 warning 原文：「同文档 [4] 行近旁有对 …A_RESIDUAL_REFERENCES.md 的同值 hash 声明但现盘不符（1209ca4c8149…/33431 B，疑历史锚或漂移）」）。
- **条 3 机理（多命中直证，本会话独立实算）**：`_integ_INTEGRATION_REPORT.md:13` 自述「隔离副本与候选逐字节同一」并给出两路径；本会话 `_slw_hashes.py` 条 3 组实算两文件均 = `ca23c116…`/412759 且逐字节比较 **True**——多命中为真歧义非谓词误判，按 ★ 规则**放弃采集、不采不回验**。
- **干扰排查**（本会话观察）：`B_EXECUTION_SPEC.md:45` 旧候选 `lead/b2b_candidate_20261106/qc151_trip.candidate.py` 在盘但 hash 不同（9656e432…/420292，表内自标「禁绑」），不构成对条 5/8 的多命中干扰。
- **附加对照 2 行位**（编排方提取件多出、不在十条清单）：附加A = `INTEGRATION_REPORT.md:147` → 唯一命中 MATCH（F2D §2.2-4 因 :148 紧邻行有路径而排除出十条；本会话实读 :147-148 照录）；附加B = `_integ_INTEGRATION_REPORT.md:6` → 零命中（该行「母本 SHA256 =」无「被核对象」前缀，BIND_RE `_g7_predicates.py:152` 不命中，本就不是绑定行）。

### 4.3 四情形误绑检验（三重实跑）

| 情形 | 实现会话 `_sl_selftest.py`（9/9 PASS，`_sl_selftest_out.json`） | 复核会话 `_slv_multitest.py`（11/11 PASS，`_slv_fix/slv_multitest_out.json`） | 本会话重放 `_slw_fix4.py`（6/6 PASS） |
|:--|:--|:--|:--|
| 多命中 | (a) 同字节双件 → verdict=multi、anchors=2、放弃采集 ✓ | A1/A2/A3：multi 列 2 锚、link_triple rec.path=None/match=None、problems 恒空 ✓ | (一) 同字节双件（d6236d718cc6…/18 B）→ verdict=multi、anchors=2、reverify=None、warning 含「放弃采集」「不采任何一者」✓ |
| 重复路径 | (b)+(e) 同文件三次写法（含 `:5-7` 行号后缀）→ 去重后 unique、回验 MATCH、后缀剥除生效 ✓ | B1 三写法去重 unique；B2 hash 符但声明字节数不符 → zero 不误采；E1 三件同 hash 仅引用其一 → 锚被引用者 ✓ | (二) `t_one.txt`/`./t_one.txt`/`t_one.txt:5-7` 三写法 → 文件级去重 unique、1 现盘文件、回验 MATCH、后缀剥除生效 ✓ |
| 零命中 | (c) marker hex → zero、保留「绑定行缺显式路径…」原警告 ✓ | C1 凭空 hex → zero 保留 R3-3b；C2 zero 分支 problems 恒空 ✓ | (三) 凭空 hex → zero、anchors=0、problems=[]、保留 R3-3b ✓ |
| 相对路径 | (d1) doc_dir ✓；(d2) root 回退 ✓；(d3a) doc_dir 优先 ✓；(d3b) 以 root 件 hex 绑定被遮蔽 → 如实 zero ✓；(d4) 仓库根回退解析真实候选件 ✓ | D1 doc_dir 优先；D2 同名遮蔽如实 zero（不偷换对象）✓ | (四) (d1)doc_dir 命中 → (d2)root 回退命中 → (d3a)同名件 doc_dir 优先 → (d3b)以 root 件 hex 绑定 → zero（不偷换对象）✓ |

本会话重放命令 = `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\samedoc_link_20261109\_slw_fix4.py`：自建 `_slw_fix4/` 夹具（全新目录，不碰 `_sl_fixtures/`），前置断言被驱动谓词 sha256 = a4ae4dc1…/12475；7/7 分支 problems 恒空断言通过。如实登记：重放中撰写员两次夹具构造错误（token 多写了目录前缀致解析不到；「doc_dir 同名件」错放到根侧）均由自纠发现，两次错误布局下谓词行为均如实（不迁就错误夹具），修正后 6/6 PASS——运行记录在 stdout，夹具留存 `_slw_fix4/`。

### 4.4 闭合数统计与 9/10 对照

**统计**（本会话按 `_sl_run10_out.json` 逐条重算）：唯一命中且回验 MATCH = **8/10**（条 2/4/5/6/7/8/9/10）；多命中放弃 = 1（条 3）；零命中保留 R3-3b = 1（条 1）；唯一命中但回验失配 = 0。实现回件脚本输出原文照录：「自动闭合(唯一命中且回验 MATCH) = 8/10；多命中放弃 = 1 条 ['条3']；零命中保留 R3-3b = 1 条 ['条1']；唯一命中但回验失配 = 0 条」。复核会话独立计数（自写正则/采集/解析/hashlib，**不 import 被核件**）unique=8、multi=1、zero=1，行位 hex 与 F2D §2.3 自抄清单 10/10 对齐——三棒一致。

**9/10 对照**：F2D §2.5「9/10 对象在盘且哈希逐一 MATCH、信息无损失」（F2D:160）**为真**——条 3 的隔离副本确在盘且 MATCH（本会话实算）。但 F2D §5.2(3) 由此推「同文档联查本轮 10 条中 9 条可自动闭合」（F2D:238）在「唯一命中才采」判据下**不成立**：`_integ_INTEGRATION_REPORT.md:13` 同文档内既有隔离副本路径又有逐字节同源的候选路径，两现盘文件同 hash，按本任务 ★ 规则必须放弃。两个口径的差异是**判据差异**：调查件按「对象可回验」计数，联查按「锚唯一性」计数。若编排方接受「字节同一副本算同一对象」的等价类合并，条 3 可恢复闭合（需显式改判据并登记），否则 **8/10 为该判据下的真值**。

## 5 复核回件、防伪造评估、残余风险、口径意见与声明

### 5.1 独立复核回件（绑定行格式，照录）

被核对象 SHA256 = a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5，字节数 = 12475

（被核对象 = 写域主交付件 `lead/samedoc_link_20261109/_sl_link.py`。本撰写会话 `_slw_hashes.py` D1 组 hashlib 实算 = 同值同字节，MATCH。同域其余四件本会话逐一实算吻合：`_sl_run10.py` = 666ef44f…/**7277**、`_sl_run10_out.json` = ed031e01…/36749、`_sl_selftest.py` = adf95027…/8294、`_sl_selftest_out.json` = 4ee4996c…/1905。实现回件把 `_sl_run10.py` 字节数写作 7278，盘上实测与复核实测均 7277，hash 两棒一致——以实算为准，不影响绑定。）

- **verdict = confirmed**（复核回件自报 ranCommands=11；回件无 refuted/partial 项，**无需 unconfirmed 标注**——如实记录）。
- 复核覆盖面（按复核回件如实转述）：①指纹守卫（会话首+尾两次实算；g7 谓词件/补丁模块与编排方基线逐位一致，F2D 九件与五证据件全 MATCH，受保护目录无 M）；②四级行位实读（本报告 §2.2 独立实读同证）；③★独立计数 8/1/1（§4.4）；④★多命中构造 11/11 PASS（§4.3）；⑤相对路径真实件解析（条 4 锚 out/ 回退解析复算 MATCH，本会话 `_slw_hashes.py` A条4 组同值实算）；⑥诚实度核查——防伪造未被夸大，发现一处措辞不精确（§5.3-4(b)），不影响任何判定与计数；⑦越界检查干净（无改 g7/补丁模块/任何被扫交付件；无全仓反查——`link()` 仅采集给定文档文本，run10 只开五证据件，selftest 只动写域夹具 + 一个显式传入的真实件；复核脚本全部 `_slv_` 前缀落写域）。
- 复核未做（回件自报，如实登记）：未原样重跑 `_sl_run10.py` 与 `_sl_selftest.py`（会覆写被核交付件，按 ★ 绝对只读不碰），以「逐字节副本仅改输出路径重跑（`_slv_run10copy.py`，输出 `_slv_run10copy_out.json` 与被核记档逐字节一致、同 ed031e01…/36749）+ 独立实现双重替代」；ranCommands=12 计数未复算；343 件全语料普查未做。

### 5.2 防伪造能力提升评估（诚实口径）

**提升面（实测）**：
1. 凭空捏造的 hex 现盘零命中 → 仍保留 R3-3b 警告——**不比原 R3-3b 更松**（实现自测 C1、复核 C2、本会话情形三，三重实证）。
2. 抄来/挪用的 hex 被锚到真实对象，且 warning 显式打印锚路径 + 现盘重算值——同文档可锚定项从「0 次现盘重算、纯人工」升级为「1 次现盘重算 + 路径暴露」：十条中 8 条实现自动闭合，锚路径全部显式在案（§4.2 表），人工一眼可比对锚对象与括注角色（如「母本」「正式候选」「规格草案」）是否相符。
3. 失配可见性：hex 在同文档有近旁同值声明但现盘不符时（条 1 的 r1 历史锚形态），declared_but_mismatched 把「疑历史锚或漂移」显式化（机读件条 1 warning 原文在案）。

**不提升面（如实）**：
- 指纹相等是唯一判据，**机器无法辨意图**——「张冠李戴」型伪造（绑定行挪用同文档另一真实对象的 hash）仍会「唯一命中」并报 MATCH；缓解仅在锚路径显式打印供人工比对。此型不闭合，防伪造净效果仍为正：凭空捏造不放松（零命中照旧），抄来的 hex 则被锚到真实对象并暴露不一致。
- 无路径且同文档无可锚定项的伪造仍只走 R3-3b 警告——与 F2D §5.2 兜底评估（F2D:240）登记的缺口同构，防伪造主责仍在人工锚定与他件交叉引用。

**净效果**：正、但有限——把「路径在同文档他处、信息无损失」（F2D §2.4）这一形态里可机验的部分收进自动回验（8/10），不放大任何既有 FAIL/PASS 面。

### 5.3 残余风险（六项单列）

1. **张冠李戴型伪造不可机辨**（§5.2）——唯一命中的 MATCH 对恶意挪用 hash 无免疫力，仅靠锚路径显式化供人工审。
2. **字节同一副本强制放弃**（真实发生：条 3）——安全方向但损失闭合率（按对象口径 9 → 按锚口径 8）。
3. **doc_dir 同名遮蔽**（自测 d3b、复核 D2）——合法锚被判 zero，安全方向但漏闭合。
4. **路径采集为启发式**：(a) 省略号路径一律跳过；(b) 两段拼合形态（写域声明 + 文件清单分离，F2D §2.3 条 3 归因）中若无任何显式路径/裸名 token 则联查不可达——条 3 实际因 :13/:85 给出裸名与全路径而可达；复核 ⑥ 纠正实现回件 risks(4) 原措辞「条 3 若无 :13 显式路径则联查不可达」以偏概全：`_integ_INTEGRATION_REPORT.md:85` 反引号裸名本可 doc_dir 解析，若无 :13 该条将变 **unique** 而非不可达；「纯写域声明、无文件名 token」形态确不可采，本报告采信纠正后口径；(c) 无分隔符纯文件名仅反引号内可采；(d) PATHISH 扩展名段 `[A-Za-z0-9]{1,8}` 在明文路由会把 `…candidate_lf.py` 截为 `…candidat`（机读件 unresolved_samples 在案，如条 4 的 :16/:40 截断 token）——无碍判定（完整 token 由反引号路由采到并锚定），登记为采集面已知伪影。
5. **declared_but_mismatched 粗粒度**：同行窗口在多声明表格行会跨对象误联（实测噪声：条 3 → `_integ_make_isolated_out.txt`、附加B → `_integ_fingerprint_pre/post.txt`）——字段已标注、不影响三态。
6. **TOCTOU**：回验是联查时刻快照，锚对象其后漂移则 MATCH 失效（与全家族回验同限；本纪律下不可实测，§5.6-5）。

### 5.4 problem-vs-warning 口径意见：维持 warning 级

1. 联查是**同文档推断而非行内直证**——锚由「全文档唯一 hash 命中」这一全局性质建立，原则上可错锚（风险 1），证据强度天然低于行内路径直验。
2. 家族惯例本就把弱证据定 warning：T2N/T3 失配仅警告（`_f2_r11plus.py:284-297`）、「采集到候选锚但均不在盘」也仅警告（`:298-302`）。
3. 若升 problem：条 1 这类**规范自举例的合法历史锚**（模板 R3-3-b 条款以 A_RESIDUAL:130 为无路径实例——`GATE_TEMPLATE_FIXED.py.txt:159-160`，转引自 F2D §3.2-1/F2D:173 与 §3.3；本会话未实读该模板件，转述登记）会被打成违规，重演项目刚消灭的第 8 类误报，并推翻 30 件回归语料对四件的 PASS 判档（F2D §3.2-4 转述在案）。
4. warning 级两个分支都不放松也不拦：zero 保留原警告、unique 纯增益、multi 显式放弃——人工锚定责任仍在；升 problem 只会制造新误报而不增拦截力。

**severity = low**（沿 F2D §4 口径：无新 FAIL/PASS 面，残余风险如上单列）。

### 5.5 未改任何文件声明

1. 本会话写操作仅限唯一写域 `lead/samedoc_link_20261109/` 内新件：`SAMEDOC_LINK.md`（本件）、`_slw_hashes.py`、`_slw_fix4.py` 与 `_slw_fix4/` 夹具目录。未修改、未追加、未覆盖**任何**既有件——含写域内前两棒交付件五件与 `_sl_fixtures/`、`_slv_*` 全部既有件。未 commit、未 push。
2. 只读核验（本会话实跑 `git status --porcelain`）：`lead/gate_fp7_20261108/`、`lead/r11_f2_fix_20261109/`、`lead/f2d_rootcause_20261109/`、`lead/gate_r9r12_20261109/` 与三份证据件目录（`a_residual_n1`/`b2b_isolated`/`bexec_n4`）全部仅 `??` 未跟踪态，无任何 `M`；`lead/PENDING_DECISIONS.md`、`lead/GOAL_THREE_TARGETS_20261018.md` 的 `MM` 为会话开始快照即有的在案状态（环境侧观察、成因不予臆测，F2D §5.4-3 同状登记），两件现盘字节经本会话实算与编排方基线逐位一致（§2.1 表 7/8 行）。
3. 字节级无漂移：八件上游 + 五件交付件 + 五证据件 hashlib 实算全 MATCH（§2.1/§2.3/§5.1）。
4. 前两棒越界结论如实转述：实现回件（写操作仅写域五件 + 夹具；未接回 r11_scan_plus 调用链）与复核回件（⑦ 越界干净）。

### 5.6 未验项（单列，不补造）

1. **未原样重跑 `_sl_run10.py` 与 `_sl_selftest.py`**——二者会覆写被核交付件（`_sl_run10_out.json`、`_sl_fixtures/`、`_sl_selftest_out.json`），按 ★ 绝对只读不碰；以「直读机读记档 + 复核员逐字节副本重跑（输出与记档逐字节一致）+ 本会话四情形独立重放 6/6」三重替代。
2. 实现回件 ranCommands=12 计数未复算。
3. 343 件全语料无路径绑定行总量未普查（调查件、实现、复核同状；非本任务要求）。
4. `GATE_TEMPLATE_FIXED.py.txt:159-160` 等模板条款本会话未实读，沿 F2D §3.2/§3.3 转述（F2D 会话实读在案）。
5. TOCTOU 漂移窗口（§5.3-6）在零真机 + 只读纪律下不可实测，仅登记。
6. 联查接入 `r11_scan_plus` 调用链后的端到端回归未做（本任务无权改补丁模块；接入与否待编排方裁决）。

---

（本件一次写成、无自嵌哈希——朴素自绑定密码学不可行；全件 SHA256/字节数由消费方 hashlib 实算。）

# 判别实验成件：DG 判定器 7 条 fp 误报根因判别（E2 消融 / E1 2×2 / E5 扩样）

- 成件日期：2026-11-10。撰写者：判别实验成件撰写员（独立于执行员会话与复核员会话）。
- 性质声明：**这是判别实验成件，不是修复交付**。全文不写「已修复」；修复清单标注「未实施」。单次语料（41 条自造对抗样本）上的结果不写成定论。
- 复核状态：复核员独立重跑三实验后判 **confirmed**（§6.1），执行员数据全部可信、判别结论成立且方向正确；复核另给 4 处表述精度修正（§6.1.c），本成件已按修正后的口径行文，凡执行员散文与其实跑 JSON 有出入处，以 JSON 实测为准并如实标注。

---

## 1 目的与边界

### 1.1 目的

判定 `lead/dneg_generative_20261109/_dg_core.py` 判定器在 41 条自造对抗样本上 strict 口径下的 7 条假阳性（fp=P06–P12）的真实根因，在三个候选解释间做判别：

- **解释 A（机制）**：fp 源于「护栏未穷尽 ⇒ 过宽」＋二次 veto 作用域缺陷，可用补数据/改代码消除（上游 FP_PATTERN_ANALYSIS.md:75–82 给出源码依据与受控替换证据；本实验逐条验证）。
- **解释 B（构造偏差）**：fp 恰好都落在表内构式上是造样本方式决定的，外推力存疑（上游 FP_PATTERN_ANALYSIS.md:82）。
- **「表内构式带毒性」**：若成立，删构式表即可去 fp。

三实验分工：**E2 消融**（甲=补数据、甲c=补数据+改代码、乙/乙2/乙3=删构式表、灾难臂=极限删表）判「补数据 vs 改代码 vs 删表」哪条路成立、代价几何；**E1 2×2 析因**判 CATCH 的必要条件是不是「表内构式成员资格 × 未登记边界词」；**E5 扩样**判「构式记忆」是否独立成因。

### 1.2 只读域（本任务全程零改动，逐条列）

1. lead/PENDING_DECISIONS.md
2. lead/GOAL_THREE_TARGETS_20261018.md
3. lead/fp_pattern_20261109/
4. lead/advset_indep_20261109/
5. lead/dg_adversarial_20261109/
6. lead/dneg_generative_20261109/
7. lead/h5_governance_20261109/
8. lead/gate_fp7_20261108/
9. lead/gate_pipeline_20261109/
10. lead/gate_n13_20261109/

### 1.3 写域（唯一）

lead/fp_discriminate_20261109/。执行员会话产出 `_fd_*` 件、复核员会话产出 `_fdv_*` 件（清单与绑定行见 §6.1）；本撰写会话新增 `_fdw_fingerprint.py`、`_fdw_fingerprint_out.json` 与本件，均在写域内。

### 1.4 铁律执行

零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹 hashlib。受保护十件实验前后零漂移（执行员 `_fd_material_out.json` 字段 `originals_unchanged_after_all.drift=[]`；复核员 `_fdv_fp_before.txt`/`_fdv_fp_after.txt` diff 零输出；本撰写会话再算一次仍全同，见 §6.1）。

---

## 2 素材复核

### 2.1 素材逐条核对（26/26 identical）

命令（执行员报告记载）：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_run.py`（§(1)，CASES 由 `_dga_adversarial.py:66` 起 AST 字面抽取，只读不执行）。输出：`_fd_material_out.json` 字段 `material_check`：`n_cases_total=41`、`all_26_identical=true`，编排方给的 7 fp / 11 fn / 8 neg_ok 与 CASES 原文逐条 `identical=true`。全集 41 条 = P01–P17（17 PASS）+ C01–C19（19 CATCH）+ C20,A01–A04（5 AMBIG，strict 口径排除，见 `_fd_baseline_out.json` 字段 `DG_pure_strict.amb_excluded`）；编排方素材未含的 15 条（P16,P17,C06,C13–C19,C20,A01–A04）已在全集补齐实跑。

7 条 fp 原文（expect=PASS，tokens=[已生效]）：

| id | 原文 |
|---|---|
| P06 | 前稿不敢不承认其实本件不宣告已生效 |
| P07 | 前稿不敢不承认说到底本件不宣告已生效 |
| P08 | 旧稿并不否认尽管本件不宣告已生效 |
| P09 | 旧稿并不否认与监理方不宣告已生效 |
| P10 | 本件不承认或并不否认已生效 |
| P11 | "并非不宣告已生效"只是引文，本件不采信该说法 |
| P12 | 《并不否认已生效》只是引文，本件不采信该说法 |

11 条 fn 原文（expect=CATCH）：

| id | 原文 | id | 原文 |
|---|---|---|---|
| C01 | 不容不宣告本件已生效 | C07 | 非登记五份原始件不可才算本件已生效 |
| C02 | 未许不宣告本件已生效 | C08 | 非登记一或二不可才算本件已生效 |
| C03 | 别想不登记本件已入账 | C09 | 非登记本件不可才算本件已生效 |
| C04 | 甭想不承认本件已生效 | C10 | 并非本件不宣告已生效 |
| C05 | 没准不承认本件已生效 | C11 | 非不承认本件已生效 |
| — | — | C12 | 非不认可本件已生效 |

8 条 neg_ok 原文（expect=PASS）：P01「旧稿不承认，本件不宣告已生效」、P02「旧稿未登记、本件亦未宣告已生效」、P03「无越权断言，也不出现放行 N-5 类措辞，本件不采信已生效」、P04「前段不采信母本后段不宣告本件已生效」、P05「不核不录，本件不采信已生效」、P13「既不宣告旧稿已入账，也不宣告本件已生效」、P14「不予登记亦不宣告本件已生效」、P15「旧稿不承认，但本件也不宣告已生效」。（逐条原文与 expect 见 `_fd_material_out.json` 字段 `material_check.groups.neg_ok`，8 条逐条 identical=true。）

### 2.2 基线独立复现

执行员自写 detect（协议同 `_dga_adversarial.py:210` 起的 `detect()`：toks=TOKS 在文者或 [已生效]，DG_pure=DG.dg_scan，DG_dropin=沙箱 g7 的 DOUBLE_NEG_RE 换 DG.DG_DROPIN_RE 后 r12_scan），结果（`_fd_baseline_out.json`）：

- **DG_pure strict**（n=36，排除 A01–A04,C20）：fp=7=[P06,P07,P08,P09,P10,P11,P12]，fn=11=[C01,C02,C03,C04,C05,C07,C08,C09,C10,C11,C12]；与编排方 `_dga_adversarial_out.json` scoring_strict.DG_pure 逐 id 全同（`baseline_vs_orchestrator.identical=true`）。
- **DG_dropin strict**：fp=8=[上 7 条+P17]，fn=10=[基线 11 条去 C08]（C08 判对），同样与编排方全同。

复核员独立重跑（`_fdv_run1_out.json` 字段 `baseline`/`baseline_dropin`/`baseline_match_orchestrator=true`）逐 id 复现一致。本撰写会话核对两件输出 JSON 的逐 id 列表，全同。

### 2.3 护栏常量逐项（行号本会话以 sed/grep 实读核证）

| 常量 | 值/规模 | 位置 |
|---|---|---|
| NEG1 | 59 项（含 不/没/无/非/未/莫/勿/别/甭/岂…及并非/并不是/不是/不敢/并不/不否认/不由得 等） | _dg_core.py:37 |
| MID | 23 项，**含 ε 与实词「敢」** | _dg_core.py:55 |
| NEG2 | 21 项，含 5 个完整否定谓语 **否认/不承认/不认为/不宣告/不出现** | _dg_core.py:63（5 谓语由复核员 `_fdv_run1_out.json` 字段 guard_constants.NEG2_完整否定谓语5 实证） |
| GAP / SCOPE_VERB / SPLIT_TAIL | 9 / 29 / 5 项 | _dg_core.py:69 / :71 / :77 |
| PSEUDO_DN | 12 项词汇化伪构式（无非/莫非/莫不是/不非/没没/无无/非非/没不/不没/非不/没没不/不不不） | _dg_core.py:81-82 |
| _BREAK / _BQ | 。！？；;，,、：:\n（_BQ 另含「」『』“”`，**不含转折词**） | _dg_core.py:85 / :86 |
| _SECOND | 14 字面词（本笔/本件/本节/本回件/本候选/该笔/该件/此笔/台账/母本/本域/本轮/审阅回件/复核回件）+ 第\s*\d+\s*笔；**监理方∉_SECOND** | _dg_core.py:88（监理方不在由 `_fdv_run1_out.json` guard_constants.监理方_in_SECOND=false 实证） |
| DG_BREAK_RE | [句界]|但|但是|然而|不过|却|只是|反之|相反|另外|另 = **10 词**；**「但」排在「但是」前**（词序瑕疵，见 §6.5-⑧） | _dg_core.py:89 |
| DG_SECOND_SUBJ_RE / DG_COORD_RE / DG_QUOTE_RE | 二次主语 / **[/／]|、|或|以及|同时|并且|一是|二是|其一|其二** / **恰 4 类引号「」『』“”`** | _dg_core.py:90 / :91 / :92 |
| veto / comp / govern | PSEUDO_DN 词首负向前瞻 / 补语{0,4}? / 同微句锚 ≤24 | _dg_core.py:116 / :118 / :125 |
| T12/T3 笛卡尔积 | pattern=(?:t12|t3)+govern，wildcards=1 | _dg_core.py:126-128（上游 FP_PATTERN_ANALYSIS.md:77 同） |
| R12_TEN 对账锚 | 不得不/并非不/并不是不/不是不/无不/没有不/不无/不能不/不可不/未曾不 | _dg_core.py:144-145（逐字取自 _g7_predicates.py:76） |
| _mask_quotes | 引证内置空格 + **4 组截断对（「」『』“”``）**，ASCII " 与 《》 无截断对 | _dg_core.py:148-158（截断对 :154） |
| _scope | 取最后一个 DG_BREAK_RE 切点之后的管辖前缀 | _dg_core.py:161-164 |
| dg_double_neg | :173 在 scope 上 search；**:179-181 第二主语 veto 只查 hit_text；:182-184 并列 veto 只查 hit_text** | _dg_core.py:167-186 |
| NEG_WINDOW / CLAUSE_BREAK | 24 / 。！？；\n | _g7_predicates.py:70 / :71 |
| DOUBLE_NEG_RE | 10 支字面构式 | _g7_predicates.py:76 |
| r10_context 窗口 | s=max(0,start-24)，句界 boundary 回看 | _g7_predicates.py:86-87；dbl=DOUBLE_NEG_RE.search(pre) 在 :92 |
| r12_scan | R12 谓词 | _g7_predicates.py:134 |

以上规模逐项与 `_fd_material_out.json` 字段 guard_constants、复核员 `_fdv_run1_out.json` 字段 guard_constants 双源一致。

### 2.4 fp 7 条根因逐条（双源：执行员 `_fd_baseline_out.json` 字段 fp7_root_cause_detail + 复核员 `_fdv_run_out.json` 字段 fp_root_cause_detail，本会话两件均实读）

| id | hit_text | scope | 根因（证据字段值） |
|---|---|---|---|
| P06 | 不敢不承认 | 前稿不敢不承认其实本件不宣告 | 未登记边界词「其实」在 scope 不在 hit（复核 boundary14_in_scope=[其实]、boundary14_in_hit=[]，hit_span=[2,7]）；二次主语「本件」亦只进 scope 不进 hit（second_subj_in_scope=true / second_subj_in_hit=false） |
| P07 | 不敢不承认 | 前稿不敢不承认说到底本件不宣告 | 同上，「说到底」（boundary14_in_scope=[说到底]） |
| P08 | 并不否认 | 旧稿并不否认尽管本件不宣告 | 未登记让步词「尽管」（boundary14_in_scope=[尽管]）；T12 零通配拼出（NEG2 含「否认」:63） |
| P09 | 并不否认 | 旧稿并不否认与监理方不宣告 | **监理方∉_SECOND:88**（两源 JSON second_subj_in_scope=false）＋二次 veto 只查 hit_text :179-184，scope 内「不宣告」的「不」从未被检（复核 neg1_members_in_rest=[不]）。注意：执行员散文称 P09 second_subj_in_scope=true，与其 JSON false 相悖，以 JSON 为准——本条核心机制（veto 只查 hit_text）两源一致 |
| P10 | 并不否认 | 本件不承认或并不否认 | 「或」∈DG_COORD_RE:91 但在 hit_text 之外（coord_in_scope=true / coord_in_hit=false，hit_span=[6,10]）；并列 veto :182-184 只查 hit_text ⇒ 不触发 |
| P11 | 并非不宣告 | "并非不宣告 | ASCII 双引号不在 DG_QUOTE_RE:92 的 4 类内 ⇒ _mask_quotes:148-158 不生效（复核 unmasked_quote_chars_in_pre=["\"" ]） |
| P12 | 并不否认 | 《并不否认 | 书名号《》未登记（unmasked_quote_chars_in_pre=["《"]），引证跨度未被屏蔽 |

与上游 FP_PATTERN_ANALYSIS.md:130-136 根因表逐格一致；上游 :138 把 P06/P07/P08/P11/P12 归失败模式 A（5/7）、P09/P10 归失败模式 B（2/7）（引 ADVSET_INDEPENDENCE.md:399-410）。

### 2.5 二次 veto 的语料级作用（复核员最小实现实证）

复核员按 `_dg_core.py:148-158/:161-164` 规格自写 mask/scope/scan（不用执行员任何改版件，`_fdv_run1_out.json` 字段 minimal_impl_agreement）：41 条上 mask 一致 41/41、scope 一致 41/41、hit 判定一致 40/41。唯一分歧 = C08：`DG_COORD_RE` 并列 veto（:182-184）在 41 条语料上**仅触发这一次，且触发对象是真阳**（C08 hit=非登记一或二不可被判「命中链内含并列标记：两个独立否定项」，见 `_fdv_e1e5_out.json` 字段 raw_vs_veto_disagreement）⇒ 该 veto 的语料级唯一效果是制造假阴性（C08），而其作用域盲区（只查 hit_text）制造 P09/P10 假阳性。

### 2.6 「4 类引号」歧义的判断与依据

任务指派中「4 类引号」可读作「登记现有 4 类」或「新增 4 类」。判：**指新增，且实际只需 2 类**。依据四条（复核员逐条独立复核通过）：

1. DG_QUOTE_RE 现有恰 4 类「」『』“”`（_dg_core.py:92 本会话实读），登记现有 4 类 = 空操作；
2. 上游修复清单原文「② 引号补 ASCII 双引号 / 书名号进 ：92」= 2 类新增（FP_PATTERN_ANALYSIS.md:165，本会话 grep 实读）；
3. fp 证据只需 P11 的 ASCII " 与 P12 的《》；
4. 本会话实读两份引号普查（执行员 `_fd_probe3_out.json` 字段 quote_chars_in_41、复核员 `_fdv_e1e5_out.json` 字段 quote_chars_in_41）：41 条中引号类字符仅 ASCII "(P11)、《》(P12)、「」(P17) 三处，其余候选字符零出现；且复核员「甲4引号」臂（新增 ASCII"/ASCII'/《》/（）4 类）逐 id 结果与甲全同（fp=2=[P09,P10]，`_fdv_run1_out.json` e2_arms.甲4引号）——2 类或 4 类在本语料上无差别，歧义不影响结论。

实验按操作化定义执行：14 边界词 + ASCII"/《》 2 类。

---

## 3 ★ E2 消融（五臂 + 乙3 + 灾难臂）

### 3.0 臂定义与命令

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_run.py`（§(3)）与 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_probe3.py`（乙3/灾难臂/逐臂 hit 串/探针）。沙箱底版经 `_fd_build.py`（shutil.copyfile，:26-27）复制并逐字节 SHA256 校验（`_fd_sandbox/_dg_core_base.py` = 7a8074ef…/12322、`_fd_sandbox/_g7_predicates_base.py` = 02c17e49…/11743，本撰写会话实算同，见 §6.1）。

| 臂 | 改动（全部落在写域改版件） |
|---|---|
| base | 沙箱底版（逐字节同原件） |
| 甲（补数据） | DG_BREAK_RE +14 边界词（其实/说到底/尽管/换言之/与此同时/反倒/结果/终究/总而言之/归根结底/话说回来/退一步说/哪怕/说白了，清单源 `_ai_verify.py:486-487` 本会话实读）；DG_QUOTE_RE +ASCII"/《》；_mask_quotes 截断对 +2（改版件 _fd_dg_core_jia.py） |
| 甲c（补数据+改代码） | 甲 + 二次 veto 改查 hit 链外整窗（改版件 _fd_dg_core_jiac.py） |
| 乙（删 NEG1 侧） | NEG1 删 不敢/并不/并非（_fd_dg_core_yi.py） |
| 乙2（删 NEG2 侧） | NEG2 删 否认/不承认（_fd_dg_core_yi2.py） |
| 乙3（最大非灾难删表） | 乙+乙2+MID 删「敢」（_fd_dg_core_yi3.py = 45540dafbb986b4c1b1f7f700b036fe560b8dc2bce8748ac7299c5e5ace88b0e，字节数 = 12249） |
| 灾难臂 | 乙3+NEG2 删单字「不」，仅内存（_fd_probe3_out.json 字段 yi4_catastrophic） |
| 纯改代码（复核增量臂） | 仅二次 veto 整窗化（+PSEUDO 豁免，按上游 FP_PATTERN_ANALYSIS.md:165 修复项④），无任何数据改动 |
| 甲+并列词进断裂（复核增量臂） | 甲 + 与|或|及|和|同|跟 追加进 DG_BREAK_RE，纯数据 |
| 甲_监理方进SECOND（复核增量臂） | 甲 + 监理方 塞进 _SECOND，纯数据 |

以下三表均 DG_pure strict（n=36）。执行员五臂数据：`_fd_e2_out.json` 字段 e2_arms/hidden_cost_probes；乙3：`_fd_probe3_out.json` 字段 yi3_strict；灾难臂：同件 yi4_catastrophic；复核员十一臂数据：`_fdv_run1_out.json` 字段 e2_arms/probes。本撰写会话逐字段实读核对。

### 3.1 表一：fp 侧逐 id 进出（7 fp × 各臂判定，括号内为命中串）

| id | base | 甲 | 甲c | 乙 | 乙2 | 乙3 | 灾难 | 纯改代码(复核) | 甲+并列(复核) | 甲_监理方进SECOND(复核) |
|---|---|---|---|---|---|---|---|---|---|---|
| P06 | CATCH(不敢不承认) | **PASS**↓ | **PASS**↓ | CATCH(不敢不承认) | CATCH(不敢不) | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ |
| P07 | CATCH(不敢不承认) | **PASS**↓ | **PASS**↓ | CATCH(不敢不承认) | CATCH(不敢不) | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ |
| P08 | CATCH(并不否认) | **PASS**↓ | **PASS**↓ | CATCH(不否认) | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ |
| P09 | CATCH(并不否认) | CATCH | **PASS**↓ | CATCH(不否认) | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | CATCH |
| P10 | CATCH(并不否认) | CATCH | **PASS**↓ | CATCH(不否认) | **PASS**↓ | **PASS**↓ | **PASS**↓ | **PASS**↓ | CATCH | CATCH |
| P11 | CATCH(并非不宣告) | **PASS**↓ | **PASS**↓ | **PASS**↓ | CATCH(并非不宣告) | **PASS**↓ | **PASS**↓ | CATCH | **PASS**↓ | **PASS**↓ |
| P12 | CATCH(并不否认) | **PASS**↓ | **PASS**↓ | CATCH(不否认) | **PASS**↓ | **PASS**↓ | **PASS**↓ | CATCH | **PASS**↓ | **PASS**↓ |

fp 计数：base=7；甲=2[P09,P10]；甲c=0；乙=6[P06,P07,P08,P09,P10,P12]；乙2=3[P06,P07,P11]；乙3=0；灾难=0；纯改代码=2[P11,P12]；甲+并列=1[P10]；甲_监理方进SECOND=2[P09,P10]。

**删表再生的直接证据**（_fd_probe3_out.json 字段 regen_path_proof，独立正则探针 matched=true）：乙臂 P06 的命中串仍=「不敢不承认」，由 不(NEG1)+敢(MID「敢」)+不承认(NEG2) 笛卡尔积再生；乙臂 P08/P09/P10/P12 命中串=「不否认」，由 不+ε(MID)+否认 再生；乙2 臂 P06/P07 命中串=「不敢不」，由 不敢(NEG1)+ε+不(NEG2) 再生。⇒ 闭合表删少量构式，表面串经其他路径再生，**删不净**。

### 3.2 表二：fn 侧逐 id 进出 + AMBIG 联动

基线 fn 11 条（C01,C02,C03,C04,C05,C07,C08,C09,C10,C11,C12）在**所有臂中无一被修好**（各臂 fn_ids 均含全部 11 条；fp 修复与 fn 覆盖正交）。各臂新增 fn 与 AMBIG 翻转：

| 臂 | strict fn | 新增 fn（vs base） | AMBIG 翻转（CATCH→PASS） | R12_TEN 锚（_fd_core.py:144-145 十式对账） |
|---|---|---|---|---|
| base | 11 | — | 无 | 全生成 true |
| 甲 | 11 | 无 | 无 | true |
| 甲c | 11 | 无 | A02,C20（执行员无豁免实现，_fd_e2_out.json jiac.changed_ids）；复核按上游修复项④加 PSEUDO 豁免后仅 C20（_fdv_run1_out.json 甲c.ambig_flip=[C20]；其 甲c无豁免 臂=[C20,A02]） | true |
| 乙 | 13 | **C17,C19** | 无 | **false（缺「并非不」）** |
| 乙2 | 11 | 无 | **A01,A02**（执行员散文未提，_fd_e2_out.json yi2.changed_ids 实有） | true |
| 乙3 | 13 | **C17,C19** | A01,A02 | **false（缺「并非不」）** |
| 灾难 | **15** | **C15,C16,C17,C19** | C20,A01,A02 | **false（9/10 断，仅「不无」幸存）** |
| 纯改代码(复核) | 11 | 无 | C20 | true |
| 甲+并列(复核) | 11 | 无 | 无 | true |
| 甲_监理方进SECOND(复核) | 11 | 无 | 无 | true |

（依据：执行员各臂 `_fd_e2_out.json` e2_arms.*.DG_pure_strict.fn_ids 与 changed_ids_vs_base、R12_TEN_anchor_all_generated；乙3 `_fd_probe3_out.json` yi3_strict.fn_ids；灾难 `_fdv_run1_out.json` 灾难_乙3删不.fn_ids/R12TEN_unmatched。撰写员更正一处执行员散文笔误：「乙3（+C11,C17,C19）」中 C11 已是基线 fn（base fn_ids 含 C11），实际新增仅 C17/C19，fn=13 计数本身正确；「灾难臂 P06 才消」亦不成立——P06 在乙3 已 PASS（乙3 fp=0），灾难臂新增损失是 C15/C16。）

乙3 臂仍能抓住的非表内构式真阳（`_fd_probe3_out.json` yi3_strict.verdicts 逐条）：C06(非登记五份原件不可)、C13(何尝不认为)、C14(不见得不认为)、C15(岂敢不)、C16(不由得不)、C18(亦非不)——删表删掉的只是「表内能拼出的真阳」，表外构式真阳仍 CATCH。

### 3.3 表三：隐藏代价探针（真阳丢失逐条）

`_fd_e2_out.json` 字段 hidden_cost_probes + `_fdv_run1_out.json` 字段 probes（复核员 12 臂 × 5 探针，本会话两件实读）：

| 探针文本 | 性质 | base | 甲 | 甲c | 纯改代码 | 乙 | 乙2 | 乙3 | 灾难 | 甲+并列 | 甲_监理方进SECOND |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 非登记结果不可才算本件已生效 | 真阳 | CATCH | **PASS(丢)** | PASS(丢) | **CATCH(保住)** | CATCH | CATCH | CATCH | CATCH | PASS(丢) | PASS(丢) |
| 未尝不承认审核结果本件已生效 | 真阳 | CATCH | **PASS(丢)** | PASS(丢) | CATCH(保住) | CATCH | CATCH | CATCH | CATCH | PASS(丢) | PASS(丢) |
| 复审组并非不承认本件已生效 | 真阳 | CATCH | CATCH | CATCH | CATCH | **PASS(丢)** | CATCH | **PASS(丢)** | PASS(丢) | CATCH | CATCH |
| 监理方并不否认本件已生效 | 真阳 | CATCH | CATCH | CATCH | CATCH | CATCH | **PASS(丢)** | **PASS(丢)** | PASS(丢) | CATCH | CATCH |
| 监管方不敢不承认本件已生效 | 真阳 | CATCH | CATCH | CATCH | CATCH | CATCH | CATCH(不敢不) | CATCH | CATCH | CATCH | CATCH |

⇒ 甲 的新断裂词「结果」撞名词（两探针真阳丢失，「结果」宜收窄或接受）；乙/乙2/乙3 删表各丢至少一条真阳（复审组/监理方句）；**纯改代码臂在全部五条探针上保住真阳**。

### 3.4 (甲) 消了什么、没消什么；P09/P10 是补数据还是改代码

- **(甲) 消了**：P06↓（「其实」）、P07↓（「说到底」）、P08↓（「尽管」）、P11↓（ASCII " 进引号表+截断对）、P12↓（《》同）。**没消**：P09、P10（fp=2 残留）。
- **执行员判**（其 14 词菜单下）：P09/P10 补词表消不掉，必须改代码。机理：监理方∉_SECOND:88、veto 只查 hit_text:179-184、「或」进 DG_BREAK_RE 只会把 scope 切成「并不否认」仍命中。
- **复核员增量实证（本成件采信，逐条在 `_fdv_run1_out.json` e2_arms/probes）**：
  - **P09 存在纯数据消法**：甲+并列词进断裂（与|或|及|和|同|跟）⇒ fp=1[仅 P10]，fn 零变化——P09 被消掉（断裂后 scope=「监理方不宣告」无命中）。故「P09/P10 补词表消不掉」仅对执行员 14 词菜单成立，**P10 才是唯一结构性免疫词表法的 fp**（或→断裂只把 scope 切成「并不否认」仍命中，第二主语「本件」先于 hit 同微句，任何断裂/并列词表追加都无法触及）。
  - **把实体名词塞 _SECOND 无用**：甲_监理方进SECOND ⇒ fp 仍=2——veto 只搜 hit_text，反证作用域缺陷诊断。
  - **纯改代码可独力消 5/7**：仅整窗 veto（rest=scope 去掉 hit 后查 NEG1 成员+DG_COORD_RE，PSEUDO_DN 豁免）⇒ fp=2[仅 P11,P12]，fn 零变化，且不付甲的「结果」真阳代价（表三：甲→PASS、纯改代码→CATCH）。

**判**：fp 根因 = 护栏未穷尽 + 二次 veto 作用域代码缺陷；「表内构式带毒性」被否证（乙系删不净、乙3 全消但 +2 真 fn 且 R12_TEN 锚断）。按执行员菜单是「5 补数据（P06/P07/P08/P11/P12）+ 2 改代码（P09/P10）」；按最小必要修改是「**1 处改代码（:179-184 veto 整窗化）消 5/7（P06/P07/P08/P09/P10）+ 2 类引号补数据消 2/7（P11/P12）**」——两菜单皆零 strict-fn 达 fp=0（甲c 实证）。「哪类 fp 必须改代码」的划界是**菜单相对的**，唯一菜单无关的结论是 P10 无数据路线。

### 3.5 甲/甲c 对交付形态 DG_dropin 完全无效

甲/甲c 臂下 DG_dropin strict 恒 fp=8[P06,P07,P08,P09,P10,P11,P12,P17] fn=10，与 base 逐 id 全同（`_fd_e2_out.json` jia/jiac 的 DG_dropin_strict）——印证 `_g7_predicates.py:92` 一行替换不携带 guard（`DNEG_GENERATIVE.md:173` 本会话 grep 实读：「只换 `:76` 一行后，7 条不变式里 4 条 guard 一个都不执行」）：mask/_scope/二次 veto 都不在 r10_context 内，补数据只改 _dg_core 侧、dropin 侧的正则虽经 :142 同步重编译但缺全部运行时护栏。**要修 dropin 必须把 _mask_quotes/_scope/veto 并入 r10_context（上游修复项③），本次未实施。**

---

## 4 ★ E1 2×2 析因

### 4.1 设计与独立前提实证

模板固定 {构式}{边界词}本件不宣告已生效，共 100 条（5 表内构式 × 5 表外构式 × 5 已登记边界词 × 5 未登记边界词）。命令：`python -I -X utf8 …/_fd_run.py`（§(4)），全矩阵 `_fd_e1_out.json`；复核员独立重跑 `_fdv_e1e5v.py` → `_fdv_e1e5_out.json`。

前提实证（两源 JSON 字段 construct_in_table_standalone / standalone / in_break）：

- 表内构式 不敢不承认/并不否认/并非不承认/不得不否认/未尝不承认：standalone 命中 DG_DROPIN_RE **5/5 true**；
- 表外构式 不容不承认/未许不宣告/别想不登记/甭想不承认/没准不承认：standalone **5/5 false**；
- 边界词 另外/但是/然而/不过/只是 ∈ DG_BREAK_RE（已登记）5/5 true；其实/说到底/尽管/哪怕/反倒 5/5 false（未登记）。

### 4.2 四格结果（每格 25 条）

| 格 | 构式 × 边界词 | n | CATCH | 率 |
|---|---|---|---|---|
| G1 | 表内 × 已登记 | 25 | 0 | 0% |
| G2 | **表内 × 未登记** | 25 | **25** | **100%** |
| G3 | 表外 × 已登记 | 25 | 0 | 0% |
| G4 | 表外 × 未登记 | 25 | 0 | 0% |

G1/G3/G4 全 50 条逐条 PASS、G2 全 25 条逐条 CATCH（行级数据：`_fd_e1_out.json` e1.cells.*.rows 共 100 行、`_fdv_e1e5_out.json` e1.rows 共 100 行，本会话两件实读）。G2 格 5×5 明细（每格命中串）——「不得不否认」行的命中串为「不得不」（T12：不+得+不），其余四构式命中整串：

| | 其实 | 说到底 | 尽管 | 哪怕 | 反倒 |
|---|---|---|---|---|---|
| 不敢不承认 | CATCH(不敢不承认) | CATCH(不敢不承认) | CATCH(不敢不承认) | CATCH(不敢不承认) | CATCH(不敢不承认) |
| 并不否认 | CATCH(并不否认) | CATCH(并不否认) | CATCH(并不否认) | CATCH(并不否认) | CATCH(并不否认) |
| 并非不承认 | CATCH(并非不承认) | CATCH(并非不承认) | CATCH(并非不承认) | CATCH(并非不承认) | CATCH(并非不承认) |
| 不得不否认 | CATCH(不得不) | CATCH(不得不) | CATCH(不得不) | CATCH(不得不) | CATCH(不得不) |
| 未尝不承认 | CATCH(未尝不承认) | CATCH(未尝不承认) | CATCH(未尝不承认) | CATCH(未尝不承认) | CATCH(未尝不承认) |

逐构式 5/5 CATCH、逐边界词 5/5 CATCH（复核员明细补齐）。

### 4.3 判别结论

CATCH **仅出现于「表内 × 未登记」格** ⇒ ①选择器约束成立：必须表内构式才能 CATCH——fp 现象里的「训练构式」实为「表内构式」，与训练无关（DG 判定器无训练过程，只有闭合部件表 NEG1/MID/NEG2 的笛卡尔积，_dg_core.py:126-128）；②与未登记边界词构成精确交互（唯一 CATCH 格）；③格3/格4 恒 PASS 排除「表外也误报」。E2 侧印证：删表臂（乙系）证明表内成员是 CATCH 的必要条件；E5 侧印证：表内+正确切断不误报。

---

## 5 ★ E5 负对照扩样（表内构式 + 正确切断）

### 5.1 执行员 7 条（_fd_e5_out.json e5.rows，命令 _fd_run.py §(5)）

| id | 文本 | 切断手段 | 判定 |
|---|---|---|---|
| N1 | 旧稿不敢不承认，但是本件不宣告已生效 | 已登记断裂：，+但是 | PASS |
| N2 | 旧稿并不否认，然而本件不宣告已生效 | 已登记断裂：，+然而 | PASS |
| N3 | "并非不宣告已生效"只是引文，本件不采信该说法 | 已登记引号："" | PASS |
| N4 | 「并不否认已生效」只是引文，本件不采信该说法 | 已登记引号：「」 | PASS |
| N5 | `不敢不承认已生效`只是引文，本件不采信该说法 | 已登记引号：反引号 | PASS |
| N6 | 前稿不敢不承认，本件不宣告已生效 | 已登记断裂：， | PASS |
| N7 | 旧稿并不否认，本件不宣告已生效 | 已登记断裂：，+第二主语后置 | PASS |

7/7 PASS。如实记录：N3 的引号内串是「并非不宣告」，不在 5 构式清单内（JSON 字段 construct=""、construct_in_table=null），但它是 P11 fp 的同款表面串，属闭合表可生成面（并非∈NEG1:37、ε∈MID:55、不宣告∈NEG2:63）；其余 6 条的构式 construct_in_table=true。

### 5.2 复核员独立自建 7 条（_fdv_e1e5_out.json e5，非照抄执行员样本）

| id | 文本 | 切断 | 判定 |
|---|---|---|---|
| N1 | 前稿不敢不承认，本件不宣告已生效 | ， | PASS |
| N2 | 前稿不敢不承认但是本件不宣告已生效 | 但是 | PASS |
| N3 | 旧稿并不否认然而本件不宣告已生效 | 然而 | PASS |
| N4 | 「不敢不承认已生效」只是转述，本件不采信该说法 | 「」 | PASS |
| N5 | “并不否认已生效”只是引文，本件不采信该说法 | “” | PASS |
| N6 | `并非不宣告已生效`只是引文，本件不采信该说法 | 反引号 | PASS |
| N7 | 旧稿并不否认不过本件不宣告已生效 | 不过 | PASS |

7/7 PASS——「构式记忆」作为独立成因不成立的结论在复核员独立样本上复现。

### 5.3 判

「构式记忆」解释（表内构式必然误报）**不成立**：表内构式 + 正确切断 = 不误报（14/14 两套独立样本全 PASS）；fp 需要护栏缺口（未登记边界词/未登记引号/作用域盲区）才发生，与 E2（甲臂消 5/7）、E1（唯一 CATCH 格=表内×未登记）三角互证。**Caveat（如实记）**：这 14 条的「正确切断」定义取自护栏词表本身（，/但是/然而/「」/“”/反引号均在 _dg_core.py:85/:89/:92 已登记），内生性与解释 B 的 d1 批评同构——本实验只证伪「构式记忆必然误报」，不能证明护栏已完备。

---

## 6 复核回件 + 结论

### 6.1 复核回件（verdict 如实记 = confirmed）

复核员会话独立于执行员会话，重跑三实验全部复现（ranCommands=13；脚本与输出：_fdv_build.py/_fdv_run1.py/_fdv_e1e5v.py/_fdv_fingerprint.py 及 4 个输出 JSON + 2 个指纹快照，均在写域，本撰写会话实读其输出件）。复核判 **confirmed**——执行员三实验数据全部可信、判别结论成立且方向正确；另给 4 处表述精度修正（不推翻主结论，反而强化「改代码路线被低估」）：

- (a) R12_TEN 对账锚自「乙」臂起已断（缺「并非不」），非仅灾难臂（执行员对乙3 只写「风险」）；灾难臂 9/10 断。
- (b) 灾难臂真阳代价是 C15+C16 两条，执行员只报 C15（灾难 fn=15）。
- (c) 一处代码修改（:179-184 整窗 veto）可独力消 5/7 fp——「5 补数据+2 改代码」是甲菜单的属性而非必要性二分。
- (d) P09 存在执行员未试出的纯数据消法（并列词进断裂表，fp=1 仅剩 P10）；「P09/P10 补词表消不掉」仅对其 14 词菜单成立，P10 才真正必须改代码。
- 另记两处口径出入：执行员「甲c A02/C20 回归」对应无豁免实现，按其自引上游修复项④加 PSEUDO 豁免后仅 C20（strict 指标不受影响，A02/C20 均被排除）；其「乙3（+C11,C17,C19）」中 +C11 为笔误（C11 本就是基线 fn）。
- 复核员声明：执行员沙箱内历史中间产物未读（保持独立）；lead/eqdecl_gate_20261109/__pycache__ 的 00:13:42 .pyc 属并行会话产物，不在保护清单、不在任何导入路径，与本复核无关。

**绑定行（本撰写会话 hashlib 实算，命令 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fdw_fingerprint.py`，输出 _fdw_fingerprint_out.json：十件对编排方基线 match_baseline 全=true，即实验前后零漂移、且与执行员/复核员自报绑定行逐件全同）：**

[lead/dneg_generative_20261109/_dg_core.py]（复核回件核心被核对象）
被核对象 SHA256 = 7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1，字节数 = 12322

[lead/gate_fp7_20261108/_g7_predicates.py]
被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743

[lead/PENDING_DECISIONS.md]
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

[lead/GOAL_THREE_TARGETS_20261018.md]
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

[lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md]
被核对象 SHA256 = d80b8b0e389da9c88121d648ac90331751586ff9c1710fce07880ee0f87d2d6b，字节数 = 45189

[lead/fp_pattern_20261109/_fp_recompute_out.json]
被核对象 SHA256 = 476be04d9b72c6f343a81906e71f70072992bf2ca949c5c0aa8cf6fc0d6c9fff，字节数 = 17850

[lead/dg_adversarial_20261109/_dga_adversarial_out.json]
被核对象 SHA256 = 395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c，字节数 = 55528

[lead/dg_adversarial_20261109/DG_ADVERSARIAL.md]
被核对象 SHA256 = e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb，字节数 = 42689

[lead/dneg_generative_20261109/DNEG_GENERATIVE.md]
被核对象 SHA256 = 94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4，字节数 = 46334

[lead/h5_governance_20261109/_h5_pasteable.py]
被核对象 SHA256 = b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c，字节数 = 8540

写域内改版件抽核（同命令输出）：_fd_dg_core_yi3.py 被核对象 SHA256 = 45540dafbb986b4c1b1f7f700b036fe560b8dc2bce8748ac7299c5e5ace88b0e，字节数 = 12249（与 _fd_probe3_out.json yi3_core_sha256 及复核员抽查全同）；沙箱副本 _fd_sandbox/_dg_core_base.py、_fd_sandbox/_g7_predicates_base.py 与原件逐字节全同。

### 6.2 结论：能否判定解释 A vs 解释 B

**能判的判了，判别结果如下**（均为本语料 41 条上的判别，非定论）：

1. **解释 A 的机制主张被证实且比上游更精确**：fp 根因 = 护栏未穷尽（P06/P07/P08 可补 3 边界词、P11/P12 可补 2 类引号）＋二次 veto 只查 hit_text 的代码作用域缺陷（:179-184）；最小必要修改 = 1 处改代码（整窗 veto）消 5/7 + 2 类引号补数据消 2/7，零 strict-fn 全消 7/7（甲c 实证 fp=0 fn=11；复核纯改代码臂 fp=2[P11,P12] fn=11 零变化）。上游把 P06/P07/P08/P11/P12 归失败模式 A（5/7）、P09/P10 归失败模式 B（2/7）（FP_PATTERN_ANALYSIS.md:138）按缺失护栏归因**无误**，但「哪类 fp 必须改代码」的划界是菜单相对的（P09 有并列词数据路线）。
2. **「表内构式带毒性」被否证**：乙/乙2 删表删不净（表面串经笛卡尔积再生，§3.1 regen_path_proof）；乙3 才消净但 +2 真 fn（C17/C19）且 R12_TEN 对账锚自乙臂即断；灾难臂再丢 C15/C16、锚 9/10 断；E1 表内×已登记 0/25、E5 表内+切断 14/14 PASS。
3. **解释 B 的构造偏差批评未被推翻**：本实验样本同样按固定模板自造（E1/E5 与被检语料同模板），E5 的切断手段定义取自护栏词表（循环性），d3（命中串必为表内笛卡尔积）在本实验设定下恒真、无第三方真值裁定——B 的证据效力批评在射程内成立。
4. **两者不互斥**：A 是机制层结论（误报怎么发生、怎么消），B 是外推效力层结论（这批样本能否代表盲化新语料）。本三实验判定 A 成立、B 未被推翻；**A vs B 的最终裁决需 E3（盲化新语料）**，未跑。

### 6.3 与上游预判比对：无推翻性「不符」

上游预判（FP_PATTERN_ANALYSIS.md:77-82 受控替换/根因定位、:130-136 根因表、:165 修复清单①-④）方向与实验结果**全部一致**：14 未登记词开关 fp（复现于 E1 G2 格 25/25）、修复清单「补护栏/收紧不动构式表」被证明是正路、其修复项②（引号 2 类）与④（二次 veto 整窗）分别对应 P11/P12 与 P09/P10 的消解路径。两处**精确化**（非不符）：①上游修复清单④就是「改代码」，实验证明它独力覆盖 5/7，上游未明说的「5 补数据 vs 2 改代码」二分应改述为菜单相对；②P09 在上游分类（失败模式 B）下暗示须改代码，实证在本语料上并入列表可纯数据消。无任何实验结果与上游预判相矛盾，故无「不符」项需回改预判。

### 6.4 最小修复清单（**未实施**——判别实验不交付修复）

1. `_dg_core.py:89` DG_BREAK_RE 追加 14 边界词 → 消 P06/P07/P08。实证代价：名词「结果」撞新断裂词，两条真阳转 PASS（§3.表三）；「结果」宜收窄或接受。
2. `_dg_core.py:92` DG_QUOTE_RE 追加 "[^"\n]*" 与 《[^》\n]*》 2 类，`_dg_core.py:154` _mask_quotes 截断对补 ("\"","\"")/("《","》") → 消 P11/P12；strict 零代价（甲臂 fn=11 零进出）。
3. `_dg_core.py:179-184` 二次 veto 改查 hit 链外整窗（rest = scope 去掉 hit 后查 NEG1 成员 + DG_COORD_RE；PSEUDO_DN 类副词按上游修复项④先豁免）→ 消 P09/P10；strict 零代价；AMBIG 联动：有豁免仅 C20 翻转，无豁免 A02+C20（A02/C20 strict 均排除，不影响 strict 指标）。**仅此项（纯改代码）+第 2 项（2 类引号）即可 fp=0 且零 strict-fn、且不付第 1 项的「结果」真阳代价。**
4. 交付形态缺口（DNEG_GENERATIVE.md:173）：`_g7_predicates.py:92` 一行替换不携带 guard——实证甲/甲c 对 DG_dropin 完全无效（fp=8 fn=10 不变）；要修必须把 _mask_quotes/_scope/veto 并入 r10_context（上游修复项③），本次未实施，dropin 形态修复效果**未验**。
5. 不建议删表（乙系）：乙/乙2 消不掉 fp，乙3 才消净但 +2 真 fn（C17/C19，另有 R12_TEN 锚断与真阳探针丢失），删表路线被否证。

### 6.5 实验设计自批评（7+1 条，如实）

① 固定模板 {构式}{边界词}本件不宣告已生效 只覆盖「构式紧邻 token」形状，govern≤24 窗内更远构式、多构式叠加、N2 后接宾语等形状未覆盖；② G3/G4 的 0/50 只是 5 条特定表外串拼不出的抽查，「一切表外拼不出」靠闭合笛卡尔积的结构论证（_dg_core.py:126-130）而非统计；③ 每格 25 条优于 ≥5 要求，但词表目录仍小、无置信区间；④ 甲 的 14 词清单取自上游探针 MY_BREAK（_ai_verify.py:486-487 本会话实读），与 fp 证据仅 3 词交集（其实/说到底/尽管）——把上游词表当规范有目录内生性；⑤ AMBIG 排除口径决定「甲c 零代价」结论：若 AMBIG 算真阳，甲c 代价 = 2（无豁免 A02/C20）或 1（有豁免 C20）；⑥ E5 的切断手段定义取自护栏词表（循环性，见 §5.3）；⑦ 全部样本同模板自造、无第三方真值裁定；⑧ 附带发现：DG_BREAK_RE 词序瑕疵——「但」排在「但是」前（_dg_core.py:89，「但是」被切成 但+是；_fdv_run1_out.json guard_constants.但先于但是=但），本实验语料无「但是」相邻句故无害，属隐患。

### 6.6 判不了的 + 未验项

**判不了（射程外）**：外推到盲化新语料（需 E3，未跑）；d3 恒真/d1 同源等分析口径问题；真实大文本上整窗 veto 的误伤率；DG_dropin 交付形态的修复效果（未实施）；41 条外真阳/真阴比例；「训练」语义下构式与表内成员的区分（DG 无训练过程）。

**未验项（如实列，不补造）**：
- E3 盲化新语料实验：双方均判射程外，未跑。
- 整窗 veto 在真实大文本上的误伤率：未验。
- 修复清单①-⑤：全部未实施，实施后效果未验。
- 乙2 臂 AMBIG 联动（A01/A02 翻转）：执行员散文未提、JSON 实有（_fd_e2_out.json yi2.changed_ids），复核员实测记录在案；forced 口径（_dga_adversarial.py:168）对 AMBIG 联动的影响未逐条展开。
- 执行员会话写域内更早残留件（_fd_setup.py/_fd_e2.py/_fd_e1e5.py/_fd_probe.py/_fd_probe2.py/_fd_dg_core_D1-D6 等，Nov 9 22:45–23:14）：执行员声明未读未用未改；本撰写会话同样未读未用（其结论已由 _fd_run.py 系与复核员独立重跑覆盖）。
- 复核员未跑：执行员沙箱历史中间产物（独立性取舍）。

### 6.7 撰写会话自检（本会话实跑清单）

本撰写会话实跑：`python -I -X utf8 …/_fdw_fingerprint.py`（十件原件+写域抽核件指纹，输出 _fdw_fingerprint_out.json，all_baseline_match=true）；对 `_dg_core.py`/`_g7_predicates.py`/`FP_PATTERN_ANALYSIS.md`/`DNEG_GENERATIVE.md`/`_ai_verify.py`/`_dga_adversarial.py` 的全部引用行号以 sed/grep 实读核证（含 DNEG_GENERATIVE.md:173 grep 定位）；实读执行员/复核员全部 8 个输出 JSON 的逐 id 字段。零原件改动（只读）；写域内仅新增 _fdw_fingerprint.py、_fdw_fingerprint_out.json 与本件；未 commit/push；零真机、零采样代码。执行员与复核员实验命令（_fd_run.py/_fd_probe3.py/_fdv_run1.py/_fdv_e1e5v.py 等）系前两会话所跑，本会话以其输出件（本会话逐字段实读）+复核员独立重跑一致 + 指纹链三重核验为准入依据，本会话未重跑三实验本体。

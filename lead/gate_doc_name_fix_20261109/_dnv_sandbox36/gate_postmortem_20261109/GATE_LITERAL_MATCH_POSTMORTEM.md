# GATE_LITERAL_MATCH_POSTMORTEM —— 门禁「字面包含」11 类误报复盘与结构谓词替代方案（交付版）

撰写：复盘撰写员（dynamic workflow 子代理）。日期：2026-11-09。
上游：复盘件 `lead/gate_postmortem_20261109/_pm_postmortem_20261109.md`（复核 verdict = **confirmed**，见 §6.1）＋编排方指纹与否定语境实测两套基线。本件为其六节整理交付版；**全部关键数字在本会话重跑复核**，并按复核回件更正四处外围计数瑕疵（§6.2）。

纪律：零真机、零采样代码；被核对象十二件只读未改；唯一写域 = `lead/gate_postmortem_20261109/`；未 commit、未 push；指纹 hashlib 实算；Python 一律 `python -I -X utf8` + 绝对路径（heredoc 直执行）。
本会话实跑输出（全部落本写域）：`_pml_hash_out.txt`（指纹）、`_pml_neg_out.txt`（否定双口径探针）、`_pml_pred_out.txt`（谓词演示一）、`_pml_pred_out2.txt`（谓词演示二）、`_pml_tv3_count_out.txt`（tv3 同形计数）。
引用约定：`文件:行` 为本会话实读；`实跑` 指本会话命令+落盘输出；凡拿不到的一律标「未验」，不补造。

---

## 1 目的与边界

1. **本任务只复盘与给方案**：登记 11 类门禁误报（§3）、分析共同根因（§4）、给逐类可运行的结构谓词替代方案（§5）、记录复核结论与优先级（§6）。
2. **不改任何既有模板、不改任何交付件**：`lead/gate_template_20261108/`、`lead/gate_validate_20261108/`、`lead/gate_fp7_20261108/` 三个受护目录与 §2 十二件被核对象全程只读（未改之证 = §2 指纹 12/12 全符，字节级一致）。
3. **唯一写域** = `lead/gate_postmortem_20261109/`；本会话在此写域新增仅五个 `_pml_*` 输出文件与本件（§6.4）。
4. **不 commit、不 push**；零真机（未启动/终止任何进程、未读活进程内存）；零采样代码（无 hook/MiniDump/SuspendThread/StackWalk/注入/动态内存解析的可运行实现，文中 API 名仅为引证既有门禁原文）。
5. **方法论红线**：本方案不含任何「多写几条正则穷举字面词」成分——归一化、结构判定、作用域限定、现盘重算均为有限、双侧、可约定的变换；且每个「放宽」都捆绑反向验证（无捆绑的放宽已被回归报告实证改判不可投入实战，`GATE_TEMPLATE_REGRESSION.md:128-135`，本会话实读）。凡本质仍是词表膨胀的路，如实标注「走不通」而不是包装（§5.9 B/C 档）。

## 2 上游指纹（十二件，本会话 hashlib 实算，输出 = `_pml_hash_out.txt:1-15`，SUMMARY matched=12/12）

文件 1：lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md
被核对象 SHA256 = 1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b，字节数 = 23129

文件 2：lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md
被核对象 SHA256 = 724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e，字节数 = 45719

文件 3：lead/n11_dimmap_20261108/DIM_COLUMN_MAPPING.md
被核对象 SHA256 = 083b499e1efa32fe4eba282598bb11712ace659ab5dc67d0ea9ecd915463a5fd，字节数 = 26493

文件 4：lead/n10c04_ruling_20261108/RULING_STATIC_ORDER.md
被核对象 SHA256 = 4c2b3b38ced6a8e110800e03c0144babd24c5c60e8030838f37e0a523cf4b412，字节数 = 45070

文件 5：lead/s604_attribution_20261108/S604_ATTRIBUTION.md
被核对象 SHA256 = 8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237，字节数 = 27182

文件 6：lead/n11_wording_fix_20261108/N11_WORDING_FIX.md
被核对象 SHA256 = 4ef31846050ef4e1506221c42354b61636701c37657e455c075a2e85f207f1b4，字节数 = 18966

文件 7：lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md
被核对象 SHA256 = 6d88fc9241e31e0d6ed7af4988ab712c8e0f4e4caa9d3d92e4f736bf23f46395，字节数 = 21690

文件 8：lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md
被核对象 SHA256 = b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b，字节数 = 22048

文件 9：lead/pending_factpack_20261108/PENDING_FACTPACK_C02_C03_C06_C07.md
被核对象 SHA256 = 4dd5efb83727a0ca4ddbfe34b43809825f212c1be7eefd70a4f819c0efb3c175，字节数 = 42938

文件 10：lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt
被核对象 SHA256 = 543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe，字节数 = 28128

文件 11：lead/PENDING_DECISIONS.md
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419

文件 12：lead/GOAL_THREE_TARGETS_20261018.md
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

复核对象（复盘件 `_pm_postmortem_20261109.md`）亦在本会话实算（`_pml_hash_out.txt:13-14`）：SHA256 = f85a7ccce99023ad38e3684e0267145ea973ff8eb296f94a7cecdf1497810eeb，字节数 = 32997，与复核回件绑定行一致（MATCH）。

## 3 十一类误报逐类登记

「复发次数」均为可追溯口径：门禁级 problems 计数取自回归报告（本会话实读），语料计数取自本会话实跑（`_pml_neg_out.txt`、`_pml_pred_out.txt`、`_pml_pred_out2.txt`、`_pml_tv3_count_out.txt`）。

| 类 | 机制（门禁实际在判什么） | 实例（一手 file:line / 本会话实跑） | 复发次数 |
|---|---|---|---|
| **1 禁词子串** | 全文子串扫禁词，把反禁词自检机制、mock 拦截串、文档串当违规本体，不看「是否真有调用行为」 | `GATE_FALSE_POSITIVES.md:55-57`：`_verify_A_recompute.py:679` BANNED_PAT 一条正则字符串贡献全部 7 条命中；mock.patch 串命中；qc151 派生副本与母本逐字节相同仍计数 | 门禁级 **31 条 problems**（1c93b364×21 + cd57bf1c×10，`GATE_TEMPLATE_REGRESSION.md:81`）；子串命中面更大（三自检脚本各 10、qc151 87、_integ 7，:82）而 **AST 调用边全 0**。本会话 mini-demo：naive=6 命中 vs AST 边=0（`_pml_pred_out2.txt:13`） |
| **2 措辞不匹配** | 要素词按字面等值查（`if k not in t: 缺要素`），词表错取自中间稿转述 | `GATE_FALSE_POSITIVES.md:65` 门禁码逐字（词表含「最小字段」）；权威原文 `NEXT_STEPS_20261106.md:103` 本会话一手实读=含「最少字段」、不含「最小字段」；转述源 SLOW_WINDOW_LIMITS.md:139（:72） | **1 起**（2b4e006c problems 恰一条「缺要素 最小字段」，:50/:67，交付件六要素齐全）；同族漏报侧：R2 纯子串「提及即通过」真违规 9/10 漏检（`GATE_TEMPLATE_REGRESSION.md:105-117`） |
| **3 空跑通过** | 门禁声明了检查意图但无运行时自检：不计数、不重算，把「没查」当「查了没事」 | `GATE_FALSE_POSITIVES.md:85`：20 个既有门禁 GATE_CODE 内 `hexdigest` 出现 0 次、无一做现盘重算比对；`GATE_TEMPLATE_REGRESSION.md:74`：25 个解码门禁码 grep=0（本轮一手） | **20/20**（另 25 门禁码层面亦 0）；本会话守卫演示 `gate_run([])`→FAIL（`_pml_pred_out2.txt:10`） |
| **4 报告层禁词字面引证自锁** | ask 层「不得含…字面量」禁令＋门禁字面扫描：交付件逐字引证禁令原文即中，掩码书写成为常态 | `GATE_FALSE_POSITIVES.md:124`：对交付 DOC 做三字面扫描的门禁实存 10 个；掩码事实 4/3/3；复发条件已模板登记（`GATE_TEMPLATE_FIXED.py.txt:266-269` R5-4，本会话实读） | 门禁家族 **10 个**文档扫描门禁在位（:124）；「证据引证被结构性惩罚」风险真实存在（同段） |
| **5 反引号/换行拆断标识符** | 搜「无引号裸字面量」，被反引号包裹或换行拆断的必现要素漏认存在→误报缺要素 | 真件 `_g7_tv7_split_token.md`（`` `APPROVE_\nSCOPE` ``）：本会话 raw=False→归一化 True；`_g7_tv7b_wrapper_only.md` 包裹形态同理（`_pml_pred_out.txt:2-4`）；语料实例 CANDIDATE:15/150/155/160 | 语料 **14 处**（CANDIDATE 5 + LEDGER 6 + RULING 3，本会话附录 `_pml_pred_out2.txt:15-18`；更正：复盘件原记「9 处」不可复现，见 §6.2a） |
| **6 否定式自查被当越权断言** | 禁词字面命中即罪，不看断言极性：逐条排除声明（「不放行 N-5」「无越权断言」）恰是命中最多的动作 | CANDIDATE L17/L150/L155「不放行 N-5」「无越权断言」、RULING L44/L425「不授实施权」（本会话 S1 逐条定位，`_pml_neg_out.txt:2-7、32-36`） | 本语料 14 命中中 **6 处 negated + 7 处引号 mention + 1 处围栏 mention = 14/14 非断言**（:9-14、19、41-42）；朴素全文扫描 FP 率 14/14（:66） |
| **7 否定句含完成时词** | 「不宣告…已生效」搜到「已生效」即罪，不看否定辖域 | CANDIDATE L150、LEDGER L146/L177/L194 全为排除声明（本会话 S1）；fp7 真件 tv3 L10 为对照豁免行 | 12 基线件 **4 处**（`_pml_pred_out2.txt:19-21`）；tv3 同形 2 处（L8 双重否定形+L10 单否定形，`_pml_tv3_count_out.txt:1-4`）＝含对照共 6（更正：复盘件原记「8 处」不可复现，见 §6.2b） |
| **8 绑定行路径隔断** | 要求「被核对象」与「SHA256 =」紧邻，不容括注路径/加粗/反引号→误报缺绑定 | 真件 `CANDIDATE_RESIGN_YES_V2.md:122`（路径括注+反引号 hex+加粗）：本会话紧邻正则解析 **False（FP 现场复现）**、宽容解析 True、路径抽出后现盘重算 ee27b4caf4fa…/11948 **MATCH=True**（`_pml_pred_out.txt:6-9`） | 真件 **1 处**；口径分歧属合同-门禁不一致（现行铁律禁 infix），修法=合同参数显式化，非门禁私改 |
| **9 带分隔符编号** | `\bD(\d+)\b` 类正则匹配不到 D-01 等带分隔符形态→误报「无编号」 | 真件 DIM L101：本会话 naive 命中 **0（FP 复现）** 而归一化 D01 在场（`_pml_pred_out.txt:22`）；DIM 全文以 D-01..D-13 书写 | DIM 表内编号 **≥13 处** 全部对 naive 不可见；警示：无作用域的全文件归一化引入 16 个噪声 token（:23-24，见 §5.5） |
| **10 加粗包裹/千分位变体** | 要求反引号包裹 hex→加粗变体漏认；数值正则对千分位只截前段 | 真件 `DIM_COLUMN_MAPPING.md:193/194`（加粗绑定行、无反引号）：backtick-required naive=**False（FP 复现）**、宽容解析 True、现盘重算 3d463483ad0d…/44300 与 c0dfb0d17eda…/54351 **双 MATCH=True**（`_pml_pred_out.txt:11-14`）；千分位「26,435」naive 只取 '26'（:15；`GATE_FALSE_POSITIVES.md:124` ①、`GATE_TEMPLATE_FIXED.py.txt:166-168`） | 真件 **2 处**＋潜伏变体 2（千分位/`## 1` 无界字面，`GATE_FALSE_POSITIVES.md:124` ②，无已发实例） |
| **11 同义措辞（改前改后）** | 查「改前改后」四字连写这类固定词形，而非「成对改前块/改后块」的结构存在性 | 真件 `N11_WORDING_FIX.md`：四字连写全文 **0 次（FP 复现）**，但【改前】/【改后】块对在 :81/:82（方案 A）与 :88/:89（方案 B）；本会话结构判定器（零硬编码同义词）提取标注体系 {改前,改后,行,要点,适用}，(改前,改后)×2 等相邻对→**YES**（`_pml_pred_out2.txt:2-5`） | N11 全文连写 **0 处** vs 块对 **2 组**（4 行）；对照 A/B/C 证明判定与具体标注词无关（:6-8） |

## 4 共同根因分析（否定语境实测数据支撑）

### 4.1 一句话根因

**11 类误报是同一个结构性错误在两个失效方向上的投影：门禁把「字面词形是否出现在全文里」（surface containment）当作「合同义务是否成立」（obligation holding）的判据；而义务谓词实为三元组——(作用域 scope：义务只约束承载断言语语行为的区段) × (结构形态 shape：绑定对/成对块/编号所指/标识符，经归一化) × (断言极性 polarity：肯定断言 vs 否定/引用/元语言提及)。字面包含对三层全不敏感：对词形变体（类 5/8/9/10/2）「漏认存在」→误报缺要素；对元语言使用（类 1/4/6/7/11）「误认断言」→误报越权；类 3 是门禁自身无运行时自检，把「没查」当「查了没事」。**

r2 修正模板总则已点破同一根因（本会话一手实读 `GATE_TEMPLATE_FIXED.py.txt:47-52` R0）：「旧门禁把『字面出现』当『违规』——全文子串扫禁词……字面等值查要素词……把历史指纹当现盘指纹要求」。本复盘的贡献不在重述 R0，而在：把 11 类全部归一到 R0、补齐模板尚未覆盖的类 3/9/11 与类 6/7 的极性层、并给每类可运行谓词（§5）。

### 4.2 三层失敏 × 11 类映射（逐层归一）

- **shape 层失敏（漏认存在）→ 类 5/8/9/10/2**：归一化可根治——词形变体是有限可约定变换（反引号/加粗/空白/分隔符），不是无限词表。
- **polarity 层失敏（误认断言）→ 类 6/7/1/4/11**：use-mention 分层＋否定构式判定可把本语料降到 0 误报；自由散文的极性终审机器不可判定（§5.3、§5.9 B/C 档如实说）。
- **scope 层失敏 → 类 1/4**（兼 6/7 根治路径、类 9 的前置件）：义务只约束「本写域新增行为」（py=AST 真实调用边+派生做差）或合同定义的断言区段（doc）。
- **自检缺失 → 类 3**：以上一切谓词的可信度都依赖门禁自身在跑——计数器+正反控制件是全局前置件（§5.8）。

### 4.3 否定语境实测数据支撑（本会话 `_pml_neg_out.txt` 实跑）

1. **编排方 6 个可比数据格全部复现**（:9、:11、:19、:41、:42，S2 对账 6/6= :58）：CANDIDATE 已生效 1/1、可应用母本 1/1、放行 N-5 4/3；LEDGER 已生效 3/3；RULING 授实施权 4/4、解除 PAUSE 1/1。基线数据与被核对象字节（§2）互洽。
2. **朴素全文扫描 FP 率 = 14/14 = 100%**（:60-66）：六件×六禁用词共 14 命中，A 口径（否定回看）13 处在否定语境、B 口径（分层）14/14 非断言（6 negated＋7 引号 mention＋1 围栏 mention）——**0 个肯定断言**。
3. **否定回看（前 N 字符）不是充分修复**：CANDIDATE L130 翻案条款引文「回件出现『可应用/放行 N-5』断言，本 confirmed 即翻」——A 口径判 plain（仍会误报），B 口径第 0 层判 mention_quote（:5）。**use-mention 层是独立必需的一层**。
4. **单向否定回看同时制造漏报**：fp7 真件 tv3（双重否定=真违规样本）——A 口径 3/3 判否定语境，**漏检 2 处真违规**（:68-70；B 口径 2 assertion_dblneg+1 negated 全对）。禁令侧滥杀与要求侧滥放同源：回归报告一手实证 R2「提及即通过」在否定句里提及要素词即放行，真违规 9/10（`GATE_TEMPLATE_REGRESSION.md:105-117`）——**同一个字面谓词，在禁令侧 14/14 误报、在要求侧 9/10 漏检，这是 4.1 根因的最强佐证。**
5. **双重否定必须先于单否定判定（层序是正确性的一部分）**：本会话 S5 电池（:72-78）——「不得不承认已生效」「本件并非不宣告已生效」「不能不承认已生效」正确层序全判 assertion_dblneg（FAIL 捕获）；若第 2 层先跑，三例全被「不」误判 negated 放行。
6. **否定词奇偶计数被两反例否决**（:80-81）：「无越权断言：审阅回件不出现「…」类断言」两个否定词→奇偶判 assertion（对合规句误报）；「复核方并未漏看，本件并非不宣告已生效」三个否定词→奇偶判 negated（对真违规漏检）。奇偶是语法玩具（fp7 R12 注释原文同结论，`_g7_predicates.py:74-75、137-139` 本会话实读）。

### 4.4 推论验证：「越守规矩的件，误报率越高」——成立，且需精确化

本会话 S3 聚合（`_pml_neg_out.txt:60-66`）：

| 件 | 字节数 | hits | hits/KB | A_neg | B 非断言 |
|---|---|---|---|---|---|
| CANDIDATE_RESIGN_YES_V2（YES 回件，越权排除声明段） | 23,129 | 6 | 0.27 | 5 | 6/6 |
| LEDGER_APPENDIX_DRAFT（台账登记件） | 45,719 | 3 | 0.07 | 3 | 3/3 |
| RULING_STATIC_ORDER（裁决定稿，越权排除声明节） | 45,070 | 5 | 0.11 | 5 | 5/5 |
| DIM / S604 / N11（纯技术件） | — | 0 | 0.00 | 0 | 0/0 |
| 合计 | — | **14** | — | 13 | **14/14** |

三个可验证结论：

1. **命中精确落在「做元合规言语行为的件」上**：三件有命中的全是裁定/回件/台账登记类——其合规动作（逐条「不授实施权」「不宣告…已生效」「不出现『放行 N-5』类断言」）必然以被禁词形本身书写否定声明；三件纯技术件零命中。越守规矩（越需要逐条声明自己不做什么），mention 越多，误报越多——**推论成立**。
2. **精确化（诚实限定）**：命中密度与自查否定密度并非严格单调（RULING 自查否定 26 处 vs CANDIDATE 7 处，但 hits/KB 0.11 vs 0.27——自查否定计数为上轮口径 `_pm_negation_probe_out.txt:73-79`，本轮未重算，见 §6.5-6）。准确表述：**误报数 ∝ 交付件用被禁词形本身做否定/引用的次数**（本语料：CANDIDATE 6 命中=2 来自 L150＋2 来自 L155＋1 来自 L130 引文＋1 来自 L17；更正见 §6.2c）。
3. **反向激励**：把自查改写成同义词的件（如 N11 全文 0 命中）会「完美通过」词表门禁——字面门禁训练产出方隐晦化，对真违规的灵敏度同步退化。同类「消除机制自带绕过面」三例已被回归报告实证（R4-2 自指/R3-2 泛词/R6，`GATE_TEMPLATE_REGRESSION.md:128-135`，severity 因此改 high，:190）。

## 5 结构谓词方案（逐类可运行片段，全部真件验证）

总框架：每条门禁检查回答四问——(a) 作用域：我在看承载义务言语行为的区段吗？(b) 形态：归一化后结构成立吗？(c) 极性：这是肯定断言还是 mention？(d) 自检：本次实际检查了几项？输出三态 **PASS / FAIL / REVIEW**（不确定 → REVIEW，永不「不确定 → 放行」）。

### 5.1 P-A 归一化匹配（类 5/10，兼类 8 解析层）——已在真件实跑（`_pml_pred_out.txt:1-4`）

```python
import re

def join_backtick(s):                      # N2：反引号跨度内换行拆断修复
    out, pos = [], 0
    for m in re.finditer(r"`([^`]*)`", s, re.S):
        out.append(s[pos:m.start()]); out.append(m.group(1).replace("\n", "")); pos = m.end()
    out.append(s[pos:]); return "".join(out)

def norm(s):                               # N1：剥 ` * ~ 修饰符、压空白
    s = re.sub(r"[`*~]+", "", s.replace("\u00a0", " "))
    return re.sub(r"[ \t\u3000]+", " ", s).strip()

# 匹配 = "APPROVE_SCOPE" in norm(join_backtick(text))，needle 与 haystack 双侧同函数
```

实跑：tv7 拆断形态 raw=False→**True**（救回）；tv7b 包裹形态 True→True；tv1 真缺要素 False→**False（真缺不误放）**。归一化是有限、双侧、可约定的变换——这正是它与「多写几条正则」的区别：不新增任何词形，只消除书写噪声。

### 5.2 P-B 绑定行两问分治（类 8/10）——已在真件实跑（`_pml_pred_out.txt:5-15`）

```python
tol = re.search(
    r"被核对象(?:（[^（）]*）)?\s*SHA256\s*=\s*`?([0-9a-f]{64})`?\s*[,，]\s*字节数\s*=\s*([\d,]+)",
    norm(line))
# 第 1 问 可提取性（宽容）：tol 为 None -> REVIEW（人工锚定，模板 R3-3b），不 fail
# 第 2 问 真实性（从严）：能提取 -> 现盘 hashlib 重算比对；失配=FAIL（R3-3a），对象不在盘=FAIL（R3-3c）
path = re.search(r"lead/[\w\-./]+\.md", line).group(0)
data = open(path, "rb").read()
ok = (hashlib.sha256(data).hexdigest() == tol.group(1)
      and len(data) == int(tol.group(2).replace(",", "")))   # 千分位先剥（R3-4）
```

实跑：CANDIDATE:122 紧邻正则 False（朴素 FP 复现）→宽容 True→重算 MATCH=True；类 10 真件 DIM:193/194 backtick-required naive=False→宽容解析+重算 **双 MATCH=True**；千分位「26,435」naive 取 '26'→剥逗号 26435。**排版宽容度只影响「能否提取」，永远不影响「是否真实」——最终判据是密码学比对，不是措辞。**「被核对象」与 hex 间允许的 infix 是合同参数，应写进任务书（现行铁律禁 infix，则类 8 形态在现行合同下属违规；11 类清单把它列为误报说明当时合同与门禁口径不一致——修法是统一口径）。

### 5.3 P-C 断言极性分层判定（类 6/7，含双重否定处理）——已在真件实跑（`_pml_neg_out.txt`）

```python
NEG_RE   = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")   # 编排方同词表（_g7_predicates.py:69）
DBLNEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")  # R12 闭类构式表
CLAUSE_BREAK = "。！？；\n"; NEG_WINDOW = 24
SPAN_PATS = [r"「([^」\n]{0,80})」", r"『([^』\n]{0,80})』", r"“([^”\n]{0,80})”", r"`([^`\n]*)`"]

def clause_prefix(text, start):            # 回看窗裁到子句界（_g7_predicates.py:86-90 同构）
    s = max(0, start - NEG_WINDOW)
    b = max(text.rfind(ch, 0, start) for ch in CLAUSE_BREAK)
    return text[b:start] if b > s else text[s:start]

def classify(text, start, end, spans):     # 层序是正确性的一部分：L0 > L1 > L2 > L3 > L4
    for a, b, kind in spans:               # L0 use-mention：围栏/行内码/短引号 = mention（结构性可靠）
        if a <= start and end <= b: return "mention_" + kind
    pre = clause_prefix(text, start)
    if DBLNEG_RE.search(pre): return "assertion_dblneg"    # L1 双重否定=肯定，FAIL —— 必须先于 L2
    if NEG_RE.search(pre):    return "negated"             # L2 子句辖域单否定，豁免 + warning
    if re.search(r"(若|如果|一旦|假设|触发|出现)", pre): return "conditional"  # L3 假设语境，REVIEW
    return "assertion"                                     # L4 兜底，FAIL
```

- **双重否定处理**：闭类构式表命中即判肯定断言（tv3 真违规 2/2 捕获，`_pml_neg_out.txt:68-70`）；层序陷阱已实证——第 2 层先跑会把「不得不/并非不/不能不」三例全部放行（:73-78）。奇偶计数两反例否决（:80-81），不得采用。
- **mention 层**：RULING L5 命中处 3-26 行围栏码块内判 mention_code（:32）——第 0 层是结构判定，可依赖。
- **残限（如实）**：「未尝不承认已生效」「难道不应该已生效吗」在词表外，两种层序下都判 negated（漏检，:77-78）；长辖域否定（列表引导句+分号项）未构造向量（§6.5-3）。**因此极性判定器只做 REVIEW 分诊，不做终审**；终审靠作用域限定（P-D）或合同断言区段制。

### 5.4 P-D 作用域限定（类 1/4，兼类 6/7 根治路径与类 9 前置件）——py 侧已 mini-demo 实跑（`_pml_pred_out2.txt:12-13`）

```python
import ast

def ast_edges(src):        # 只走 Import/Call/Attribute 节点，根本不遍历字符串常量
    edges = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import): edges += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module: edges.append(node.module)
        elif isinstance(node, ast.Call):
            f = node.func
            edges.append(f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "?"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            edges.append(node.value.id + "." + node.attr)
    return edges

# 判罪依据 = set(ast_edges(derived)) - set(ast_edges(source))；逐字节相同 => 新增边恒零（模板 R4）
# doc 件：合同显式定义「断言区段」，禁词扫描只在断言区段 pass/fail，区段外命中 mention 记账，永不 fail（R5-1）
```

实跑（静态测试数据，从不执行）：反禁词自检清单形态 naive=6 命中 vs **AST 禁用调用/导入边=0**（`_pml_pred_out2.txt:13`）——与回归报告一手审计同构（三自检脚本子串各 10 而 AST 边=0，`GATE_TEMPLATE_REGRESSION.md:82`）。**必须捆绑防洗白通道**：排除区（围栏/引号/自查节）每轮出审计清单供抽查——R4-2 派生豁免自指绕过已实证同一真违规在 FAIL/PASS 间翻转（`GATE_TEMPLATE_REGRESSION.md:128、132`）：作用域限定若不带排除区审计，等于把「误杀合法」换成「放过真违规」。

### 5.5 P-E 编号归一化（类 9）——已在真件实跑（`_pml_pred_out.txt:16-24`）

```python
def idtok(s):                              # D-01 / D01 / D_01 / D.01 / "D 01" -> D01
    s = re.sub(r"(?<=[A-Za-z])[-_.\s]+(?=\d)", "", norm(s))
    return re.sub(r"\s+", "", s).upper()

# 判定 = 双侧用同一 idtok 提取 token 集合，比对集合等价与计数，而不是数某种拼写
# 必须配作用域限定（表首列/标题行模式）——P-D 是全局前置件而非独立补丁
```

实跑：五种分隔形态全部归一为 D01；DIM L101 上 `\bD(\d+)\b` 命中 0（FP 复现）而归一化 D01 在场。**设计警示（同段实跑暴露）**：全文件无差别 idtok 收 29 个不同 token——13 个合法（D01..D13）+ **16 个噪声**（D14..D99，来自 `d13d14_cards_20261108` 之类路径/日期碎片，:23-24；更正见 §6.2d：29 是全集，污染是 16）。编号提取不配作用域限定就会把噪声当要素。

### 5.6 P-F 成对改前/改后块结构存在性（类 11）——已在真件实跑（`_pml_pred_out2.txt:1-8`）

```python
LBL = re.compile(r"^\s*[-*]\s*【([^】]{1,8})】\s*(.*)$")   # 标注词从文中提取，零硬编码同义词
seq = []
for i, ln in enumerate(text.split("\n"), 1):
    m = LBL.match(ln)
    if m: seq.append((m.group(1), norm(m.group(2)), i))

pairs = {}
for a, b in zip(seq, seq[1:]):
    if a[0] != b[0] and a[1] != b[1]:      # 相邻、异标签、主体内容互异 -> 候选对
        pairs[(a[0], b[0])] = pairs.get((a[0], b[0]), 0) + 1

verdict = "YES" if any(c >= 2 for c in pairs.values()) else "NO"   # 同形对重复>=2 = 稳定标记体系
```

实跑（真件 N11）：四字连写 0 次（朴素 FP 复现）但提取出标注体系 {改前,改后,行,要点,适用}，相邻异标签对 (行,改前)×2、(改前,改后)×2、(改后,要点)×2 → **YES**；对照 A（无关标签 输入/输出 ×2）判 YES 证明**词独立性**、对照 B（同标签无差分）NO、对照 C（仅一对）NO。标注词语义与义务的对应从上游原文提取（与类 2 同机制），门禁不自带词表——这不是换皮关键词：判定器代码里没有任何「改前/改后」字面。

### 5.7 P-G 上游术语提取（类 2）——锚点已一手实读；全机制为规格级（§6.5-5）

```python
anchor = open(BASE + "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md", "rb"
              ).read().decode("utf-8").split("\n")[102]
seeds = [w for w in ("最少字段", "采集时机", "代价上限", "能排除的假设") if w in anchor]
if not seeds:
    FAIL("上游术语提取失败")               # 提取失败必须 FAIL，不许静默回退硬编码词表
# 要素命中判定还要过 P-C 第 0 层：引证语境内的「提及」不算在场
# （反制 R2「提及即通过」9/10 漏检，GATE_TEMPLATE_REGRESSION.md:105-117）
```

锚点真实性（本会话实读）：`NEXT_STEPS_20261106.md:103` 含「最少字段」、不含「最小字段」（补跑输出同 `GATE_FALSE_POSITIVES.md:70-72` 一致）——词表错取自 N-8 转述（SLOW_WINDOW_LIMITS.md:139）即类 2 全案。补强两点：提取失败转 FAIL；要素命中过引证语境排除。

### 5.8 P-H 自检计数器 + 正反控制件（类 3）——已在真件实跑（`_pml_pred_out2.txt:9-11`）

```python
def gate_run(checks):
    if not checks:
        return {"ok": False, "problems": [{"rule_id": "R0", "what": "0 checks executed (empty run)"}]}
    return {"ok": not any(not f for _, _, f in checks),
            "artifacts": [{"rule": r, "target": t, "found": f} for r, t, f in checks]}

# 另配正反控制件，每轮随跑：阳性控制（tv1 缺要素/tv3 双重否定形态）判不出 FAIL => 门禁自身 FAIL；
# 阴性控制（合规样本）误判 FAIL => 门禁自身 FAIL。控制件 = 门禁的运行时单元测试。
```

实跑：`gate_run([])`→FAIL（空跑不放行）。模板 R7 输出契约已有逐项工件外壳（`GATE_TEMPLATE_FIXED.py.txt:306-322`，本会话实读）但缺 `n_checks>=1` 硬校验——这是模板的登记缺口。不修类 3，其余一切谓词的可信度都未知（20/20 门禁 hexdigest=0，`GATE_FALSE_POSITIVES.md:85`）。

### 5.9 覆盖率评级（三档，逐类）

| 档 | 类 | 判定依据与残余 |
|---|---|---|
| **A 档 · 能根治**（7 类） | 1、3、5、8、9、10、2（条件：上游可读） | 类 1：AST 边+做差（回归实证 31 条 problems→0，`GATE_TEMPLATE_REGRESSION.md:80-83`；残余=漏报侧盲区属另一问题）；类 3：计数器+控制件，成本最低、无残余；类 5：双侧归一化真件双向验证；类 8/10：两问分治+现盘重算（真件 MATCH=True ×3）；类 9：归一化+作用域限定组合，**缺一不可**（16 噪声 token 实证）；类 2：上游术语提取（上游不可读时该谓词整体不可用→转人工，不许硬编码兜底） |
| **B 档 · 只能缓解**（自动侧缓解、终审人审）（4 类） | 4、6、7、11 | mention 层+否定构式层已把本语料降到 0 误报且 tv3 真违规 2/2 捕获（§5.3）；但自由散文的极性终审（长辖域/隐含否定/元话语）本质不可由词法判定——自动判定只做 REVIEW 分诊，根治需 ask 层合同改断言区段制（R5-4 已登记复发条件在 ask 层，`GATE_TEMPLATE_FIXED.py.txt:266-269`）。类 11 自动侧：块/表格形态可判（真件 YES）；**纯散文形态自动不可确证**，需合同把「改动必须块化」写清，否则转人工 |
| **C 档 · 明确不该自动判** | 类 6/7 的散文极性终审；类 11 的散文形态；类 4 终审 | 机器只能分诊进 REVIEW 队列；这两处若强行自动 pass/fail，判错方向不可控（tv3 实证：极性判错即漏真违规）。如实说：这条路（词法判语义极性）走不通 |

## 6 复核回件、优先级与未验项

### 6.1 复核回件（如实记录）

- **verdict = confirmed**（非 refuted / partial，不标 unconfirmed）。复核方对本复盘件做了八项独立核查（指纹、否定探针独立复跑、根因逐类验证、结构谓词独立实现、双重否定定向攻击、类 11 词独立性对照、覆盖率诚实度、越界检查），全部为复核方自写脚本实跑，与本件数字逐项吻合。
- 被核对象 = `lead/gate_postmortem_20261109/_pm_postmortem_20261109.md`，绑定行（本会话 hashlib 实算复核一致，`_pml_hash_out.txt:13-14`）：

被核对象 SHA256 = f85a7ccce99023ad38e3684e0267145ea973ff8eb296f94a7cecdf1497810eeb，字节数 = 32997

- 复核方对两难点的定向攻击未破：双重否定四例全被第 1 层捕获（且实证层序反转即陷阱）；类 11 判定器经对照件证明与具体标注词无关、语义绑定走上游提取而非门禁词表。

### 6.2 复核发现的四处数字瑕疵与本件更正（均已并入 §3/§4 正文）

1. (a) 类 5「真件 9 处 APPROVE_SCOPE」不可复现——本会话实算：CANDIDATE=5、LEDGER=6、RULING=3，12 基线件合计 **14**（`_pml_pred_out2.txt:15-18`）。
2. (b) 类 7「本语料 8 处全是排除声明」不可复现——12 基线件实算 **4 处**（`_pml_pred_out2.txt:19-20`）＋tv3 同形 2 处＝6（`_pml_tv3_count_out.txt:1-4`）。注：`_pml_pred_out2.txt:21` 行尾「+tv3=5」系该段附录脚本硬编码 +1 的遗留（只计了 L10 单否定对照行）；tv3 内「不宣告…已生效」同形实为 2 处（L8 双重否定形＋L10 单否定对照形），以补跑 `_pml_tv3_count_out.txt` 为准。
3. (c) 「CANDIDATE 6 命中里 5 个来自 :150/:155」实为 **4 个**来自 :150/:155（各 2），另 1 个来自 :130 引文、1 个来自 L17（本会话 S1 逐行定位，`_pml_neg_out.txt:2-7`）。
4. (d) 类 9「引入 29 token 污染」措辞不准——29 是含 13 个合法 token 的**全集**，污染实为 **16**（D14..D99，`_pml_pred_out.txt:23-24`）。

### 6.3 优先级排序

排序原则：先修「危险」类（真违规被放过/门禁自身失效），再修「吵闹」类（合法被误杀）；任何「放宽」必须往 REVIEW 方向兜底，永不往 PASS 方向兜底。

| 优先级 | 谓词 | 覆盖类 | 理由 |
|---|---|---|---|
| **P0-1** | 自检计数器+正反控制件（§5.8） | 3 | 唯一「门禁自身失效→真违规静默全放」的类（hexdigest=0/20 实证）；成本≈0；不修它，其余一切谓词可信度未知 |
| **P0-2** | 归一化族（§5.1+§5.2+§5.5） | 5/8/9/10 | 一套 norm/idtok+绑定行解析修 4 类；纯机械、零语义判断、不引入漏报（只放宽修饰符/空白/分隔符，永不放宽 hex 与编号字符集本身）；绑定行重算把措辞门禁升级为密码学门禁；全部已在真件验证 |
| **P1-1** | mention/作用域机制（§5.4+§5.3 第 0 层） | 1/4/6/7 | 误报量最大来源（14/14 命中皆非断言）；必须捆绑排除区审计+反向验证向量交付（三个无捆绑放宽已被改判不可投入实战，`GATE_TEMPLATE_REGRESSION.md:128-135、186-193`） |
| **P1-2** | 上游术语提取（§5.7） | 2、类 11 标注词 | 消除「门禁自造词压过任务书原文」整族；前置条件=上游可读 |
| **P2-1** | 极性分诊器（§5.3 第 1-3 层） | 6/7 残余 | 只产出 REVIEW 队列不做 pass/fail；语料外泛化未测（§6.5-3） |
| **P2-2** | 成对块判定器（§5.6） | 11 残余 | 需合同先把「改动必须块化」写清，否则散文形态自动覆盖不了 |

**枢纽改动**：门禁输出从二元改三态 PASS/FAIL/REVIEW——让机器不确定的命中不再被迫二值裁决，也让「越守规矩误报越多」的反向激励失去作用点（mention 记账不再产生成本）。

### 6.4 未改任何文件声明

1. **被核对象十二件只读未改**：字节级之证 = §2 指纹本会话重算 12/12 全符（`_pml_hash_out.txt:1-12`）。
2. **受护目录未动**：`gate_template_20261108/`、`gate_validate_20261108/`、`gate_fp7_20261108/` 全程只读（本会话对其仅有 Read/cat 与被读文件的 hashlib）。
3. **本会话写域新增仅六件**：`_pml_hash_out.txt`、`_pml_neg_out.txt`、`_pml_pred_out.txt`、`_pml_pred_out2.txt`、`_pml_tv3_count_out.txt`、本件；无其他目录写入。
4. 未 commit、未 push；零真机、零采样代码。

### 6.5 未验项（如实登记）

1. **类 9/10/11 的原始涉事门禁正则未提取验证**：复核方对盘上 6 个 dwfrun-*.mjs 检索类 9/10/11 关键词（D(\d+、放行、改前改后、被核对象）= 0 命中——原始码不在盘，无法提取；类 9 的 `\bD(\d+)\b` 与类 10 的「要求反引号包裹」以任务书描述＋本会话 FP 现场复现为准。
2. **编排方否定探针原始实现未读**：A 口径系按 `_g7_predicates.py:69-71` 记录口径复刻；本会话 6/6 数据格对账吻合为间接证据，不构成直接证明。
3. **极性判定器泛化未测**：14 真命中＋tv3 之外的误报/漏报率未知；残限已实证——「未尝不承认已生效」「难道不应该已生效吗」词表外漏检（`_pml_neg_out.txt:77-78`）；长辖域否定未构造向量。
4. **tv2 其余两个禁用词未实扫**（上轮已声明，本会话仅重跑 tv3）。
5. **P-G 全机制与 P-D doc 侧断言区段制为规格级**：未整段实跑（P-D py 侧 AST 谓词已 mini-demo 实跑；P-G 锚点行已一手实读）。
6. **自查否定密度列（7/14/4/26/4/12）为上轮口径**（`_pm_negation_probe_out.txt:73-79`），本轮未重算；§4.4 的推论表述只依赖本轮重算的 hits 与 hits/KB。
7. **全部演示代码为演示级**，未生产化、未实战回归（与模板未验项同口径，转引复盘件 §7.5）。

—— 完。一句话总结：11 类 = 字面包含一个谓词在 scope/shape/polarity 三层上的投影 + 门禁无自检；替代方案 = 结构谓词族（归一化 / 两问绑定行 / use-mention 分层与双重否定构式 / 编号归一化 / 成对块结构存在性 / 作用域限定与上游提取 / 计数器），7 类可根治、4 类机器只能缓解须人审或合同结构化兜底；落地次序 = 计数器 → 归一化族 → mention/作用域（捆绑反向验证）→ 上游提取 → 极性分诊 → 成对块。

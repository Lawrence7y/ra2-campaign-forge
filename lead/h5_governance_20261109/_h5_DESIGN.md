# _h5_DESIGN.md — H5 管辖关系修复【补丁设计】（只出设计，不改任何既有件）

**任务**：H5 管辖修复设计员 / 2026-11-09
**唯一写域**：`lead/h5_governance_20261109/`（本件与全部 `_h5_*` 产物）
**绝对只读**：`lead/gate_v1v2_20261109/`、`lead/v12_impact_20261109/`、`lead/gate_n13_20261109/`、`lead/gate_fp7_20261108/_g7_predicates.py`（R12）、`lead/gate_pipeline_20261109/`、两件台账——全部未改、未追加、未覆盖（§6 指纹对账）。
**纪律**：零真机（未启动 gamemd.exe / ra2loader / YURI.exe，未 taskkill，未读活进程内存）；零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）；不 commit、不 push；Python 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib`。

## 0 复核回件绑定行（被核对象 = 分类器本体 `lead/gate_v1v2_20261109/_v12_rule.py`）

被核对象 SHA256 = 15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0，字节数 = 9148

来源：本会话实跑 `python -I -X utf8 -c "<hashlib 逐件复算>"`（§6），与编排方【实跑指纹】第 1 项、与 `V12_FULL_IMPACT.md:304` 的绑定行逐字一致。

---

## 1 第一步：九条管辖样本复核

### 1.1 独立实跑

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_repro9.py`
实现：`_h5_repro9.py` 用 `importlib.util.spec_from_file_location` 直接 `import _v12_rule.classify_v12`，逐条把 `text.find(token)` 作 `start`、`start+len(token)` 作 `end` 传入。输出落 `_h5_repro9_out.json`。

**逐条与编排方九条【实跑】完全一致**（verdict / hard / override / weak 四项逐一相同，`_h5_repro9_out.json` 对账）：

| id | 输入文本 | token | 期望 | V12 实际 | hard | override | weak |
|:--|:--|:--|:--|:--|:--|:--|:--|
| REGRESS1 | `本笔已入账 0 命中不得写成未入账` | 已入账 | CATCH | **V1（放过）** | `H5_否定禁止管辖` | `` | `[]` |
| REGRESS2 | `审阅不得不承认本候选已生效。` | 已生效 | CATCH | **V1（放过）** | `H5_否定禁止管辖` | `` | `[]` |
| CTRL_OK | `本件已生效，可应用母本` | 已生效 | CATCH | V2（抓） | `[]` | `` | `[]` |
| TRUE_NEG | `本节登记不宣告 N-4 正式绑定已生效` | 已生效 | PASS | **V2（抓）** | `[]` | `` | `[]` |
| TRAIL_NEG | `已入账不得重复登记` | 已入账 | CATCH | **V1（放过）** | `H5_否定禁止管辖` | `` | `[]` |
| LEAD_NEG | `不得写成已入账` | 已入账 | PASS | V1（放过） | `H5_否定禁止管辖` | `` | `[]` |
| DOUBLE_1 | `并非不宣告已生效` | 已生效 | CATCH | **V1（放过）** | `H5_否定禁止管辖` | `` | `[]` |
| DOUBLE_2 | `不能不说本笔已入账` | 已入账 | CATCH | V2（抓） | `[]` | `V2_OVERRIDE:已入账` | `[]` |
| DOUBLE_3 | `无不认为本件已生效` | 已生效 | CATCH | V2（抓） | `[]` | `` | `[]` |

附加实跑事实（本会话 `_h5_repro9_out.json`）：`CTRL_OK / TRUE_NEG / DOUBLE_3` 三条 `review_flag=True`，即走 `_v12_rule.py:167-170` 的 S3 fail-closed 默认 V2，不是有理由的判定；`TRUE_NEG` 判 V2 属**误拦**，`DOUBLE_3` 判 V2 属「碰巧抓对」。

### 1.2 逐条判对错与错在哪条规则

| id | 判 V12 | 错在哪 |
|:--|:--|:--|
| REGRESS1 | **错（漏）** | `_v12_rule.py:116` `prohibit_U = any(k in U_bare for k in PROHIBIT)`：句尾「不得」在 token **之后**，却按「U 内有禁止词」把句首真断言 `已入账` 豁免了。`:135-136` 据此 append `H5`，`:143-146` 提前 return V1。同 `V12_FULL_IMPACT.md:223`。 |
| REGRESS2 | **错（漏）** | 同 `:116`：「不得不」里的「不得」被当普通禁止词；`:41-43` 的 `PROHIBIT` 含「不得」，`ADJ_NEG_RE` 只查 `pre[-1]` 紧邻字符/2 字尾巴，管不了多字构式；无双重否定识别。同 `V12_FULL_IMPACT.md:224`。 |
| CTRL_OK | 对（但理由是 S3「判不了」，非结构判定） | 无 |
| TRUE_NEG | **错（误拦）** | `:115` 的 `adj_neg` 只认 `pre[-1]` 或 `ADJ_NEG_RE`（`[^。；|]{0,2}$`）：`本节登记不宣告 N-4 正式绑定` 的「不」距 token 十余字，既非紧邻也不在 2 字尾 → 不认前向管辖；`:135` 无 H5 → 落到 `:167-170` S3 默认 V2。这是「真否定管辖反而被拦」。 |
| TRAIL_NEG | **错（漏）** | 同 `:116`，禁止词在后仍豁免。 |
| LEAD_NEG | 对 | `:116` 恰巧命中（禁止词在前且短），但理由不严谨：它靠「U 内有禁止词」而非「禁止词支配 token」。 |
| DOUBLE_1 | **错（漏）** | 同 REGRESS2：`并非不` 是双重否定=肯定，`:116` 只看「不得/不」的一律豁免。 |
| DOUBLE_2 | 对（碰巧） | `:152` 的 `V2_OVERRIDE` 命中 `已入账`（`_v12_rule.py:36` 把 `已入账` 自身列为宣称词）→ V2。与 R12/双重否定无关；换个 token（如 `已生效`）即漏，见 DOUBLE_1/3。 |
| DOUBLE_3 | 对（碰巧） | 无 `V2_OVERRIDE` 词、无 H5 → S3 默认 V2。理由仍是「判不了」。 |

合计：**V12 九条只对 4 条、错 5 条**（4 漏 1 误拦）；本会话 `_h5_regress_out.json:A_score` 实跑 `old correct=4 fp=1 fn=4 / total=9`。

### 1.3 (c) 三条以「不」字头/含「不」的双重否定——V12 判对了吗？

**没有一条是「靠双重否定识别」判对的**：

| 构式 | 文本 | 期望 | V12 | 实际理由 |
|:--|:--|:--|:--|:--|
| 并非不 | `并非不宣告已生效` | CATCH | **V1 错** | `:116` 把「不得/不」当豁免 |
| 不能不说 | `不能不说本笔已入账` | CATCH | V2 对 | `:36/:152` `V2_OVERRIDE:已入账`，纯属 token 词表巧合 |
| 无不认为 | `无不认为本件已生效` | CATCH | V2 对 | S3 fail-closed（`review_flag=True`），「判不了」而非判准 |

佐证：`_g7_predicates.py:76` 的 `DOUBLE_NEG_RE` 十式里三式全在表内（本会话 `_h5_r12_gap.py` 实跑：`DOUBLE_NEG_RE.search('不得不'/'并非不'/'不能不'/'无不') = True`，`r12_scan` 四条均 `problems=1`），但 `_v12_rule.py` **全文没有 import 或调用 R12**（实读 `:29` 只有 `import re`），所以 V12 的 H5 完全没有双重否定概念。结论：编排方给的三条 `DOUBLE_*` 期望「应 CATCH」，V12 两条碰巧抓对、一条漏，**能力上全错**。

### 1.4 (d) `已入账不得重复登记`（禁止词在后）

**判错**：实跑 V1 / `hard=['H5_否定禁止管辖']`，期望 CATCH。根因同上 `:116`——禁止词在 token **之后**（`post='不得重复登记'`），`U_bare` 里照样有「不得」，于是把已经发生的完成断言 `已入账` 豁免了。这正是任务点名的「后向不管辖」反例；`V12_FULL_IMPACT.md:223` 的 REGRESS1 与它是同一根因的两种写法。

### 1.5 附带确凿缺陷（本任务范围内登记，不修）

`_v12_rule.py:143-146` 提前 `return` 时把 `override`/`weak` 恒置空，与 `:23-27` 的「hard/override 双标记一并回报」承诺不符。`V12_FULL_IMPACT.md:260` 实跑 `hard_AND_override=2`、`hard_AND_weak=9`；`V12_FULL_IMPACT.md:287`、`:330` 把它列为插门禁前置条件之一。本补丁**不改这段**（见 §5(b) 未修清单）。

---

## 2 第二步：管辖关系的判定方法（核心）

### 2.1 (a) 「管辖」的定义

设分析单元 `U`（`_v12_rule.py:78-98` 已按表格行 / 子句切好）、token 在 `U` 中的前缀 `pre`、后缀 `post`。称一个否定/禁止算子 `n` **管辖**该 token，当且仅当同时满足 **G1–G5**：

- **G1 前向性**：`n` 必须落在 `pre`（token 之前）。`post` 里的「不得/禁止/严禁」一律不构成对该 token 的管辖——它要么约束另一个动作（「不得重复登记」约束「登记」），要么约束后续句子。这是修掉 REGRESS1 / TRAIL_NEG 的硬条件。
- **G2 同微句**：`n` 与 token 必须在同一个**管辖微句**内。微句边界 = `U` 已有的 `。！？；\n`（`:66`）**再加** `，,` 与转折连词 `但/然而/不过/却/只是/反之/相反/另`。`n` 在边界另一侧 ⇒ 不管辖。取 `pre` 最后一个边界之后的片段 `scope` 作为实际判定前缀。这是修掉「跨子句否定」的硬条件。
- **G3 有辖域路径**（不是只看距离）：`n` 与 token 之间必须存在下列三条**句法路径**之一：
  - **形状 a 紧邻**：`pre[-1] ∈ 不未无非勿没禁别` 或 `ADJ_NEG_RE`（`_v12_rule.py:41-43` 原口径，≤2 字尾）；
  - **形状 b 辖域动词桥接**：`(否定/禁止算子) + [把/将/被/让/令/以/按/照]? + (辖域动词) + 补语[≤24字]`，且 token 落在该补语末端。辖域动词 = 宣告/宣布/宣称/声称/断言/认定/认为/承认/写成/记作/记为/标为/视作/视为/当作/判为/登记/注明/录入/表明/代填/覆盖/应用/填/写/记/说/做/见/算/盘/交/录/签。补语内**不得出现第二个独立主语**（本笔/本件/该笔/此笔/台账/母本/第 N 笔…）或转折词，否则视为另起断言；
  - **形状 c 全句否定辖域框**：`U` 句首有否定标签（不可能/未覆盖/未见/未做/未验/未发现/未含/无越权/非断言）且 `post[:40]` 内有谓语否定（未做/未覆盖/未见/没有/无须/无需/不用/未/无/非/不可能）。形状 c 只为保住现盘 `s604_script_hunt:143`「**不可能/未覆盖**：已删除文件的磁盘残块 carving 未做」这一处真否定申报（§4(e) 对账）；它是**句级**框架，不是「U 里随便有个否定词」。
- **G4 引证屏蔽**：`pre` 内完整 `「…」/『…』/\`…\`/“…”` 跨度内部置空格（保留开闭界符与位置），未闭合开界符之后截断。防止引文里的「不得」被当作本句管辖；也保留 `禁止填「已生效」字样` 里 `填「` 的桥接动词。沿用 `_v12_rule.py:101-105` `_strip_quotes` 的精神，但改为**只作用于 pre 且保留边界**。
- **G5 非双重否定**：若 `scope` 内含双重否定构式（§3），则否定两两抵消 = 肯定，**取消 H5 豁免并强制 CATCH**。不做「否定词奇偶计数」（`_g7_predicates.py:74-75` 已实证奇偶法会把两个独立否定短语误判成肯定）。

**管辖的输出语义**：`H5 管辖成立` ⇒ `hard += H5_否定禁止管辖` ⇒ V1（PASS，门禁放过）。判定失败 ⇒ 不 append H5，按 `:148-170` 原有 S1/S2/S3 走（V2 = CATCH）。

### 2.2 (b) 三种情形的规则

| 情形 | 例子 | G1 | G2 | G3 路径 | 结果 |
|:--|:--|:--|:--|:--|:--|
| **前向管辖** | `本节登记不宣告 N-4 正式绑定已生效` | ✅「不」在 pre | ✅ 同句 | 形状 b：`不`+`宣告`+`N-4 正式绑定`(≤24 字、无第二主语) | **V1 / PASS（应豁免）** |
| **前向管辖（紧邻）** | `不放行 N-5`、`不授实施权` | ✅ | ✅ | 形状 a：`pre[-1]='不'` | **V1 / PASS**（现盘 4 处，§4(e)） |
| **后向不管辖** | `已入账不得重复登记`、`本笔已入账 0 命中不得写成未入账` | ❌「不得」在 post | — | — | **不豁免 → V2 / CATCH** |
| **跨子句不管辖** | `不宣告 N-4 已生效，但本笔已入账`（token=已入账） | ✅ | ❌ 跨 `，但` | 重取 `scope='但本笔'`，无算子 | **V2 / CATCH** |
| **跨子句不管辖（已切 U）** | `不宣告 N-4 已生效；本笔已入账` | ✅（全文）但 U 已按 `；` 切 | ❌ 跨 U | U 内 `pre='本笔'`，无否定 | **V2 / CATCH** |
| **双重否定抵消** | `并非不宣告已生效` | ✅ | ✅ | 形状 b 本可成立，但 **G5 命中** | **强制 V2 / CATCH** |

实现片段：`lead/h5_governance_20261109/_h5_pasteable.py`（`h5_govern(pre, post)` 返回 `adj_neg / prohibit_governs / double_neg / dn_hit / shapes / scope`），以及 `_h5_patch.py` 的四处机械替换。`_h5_v12_patched.py` 是施加补丁后的**写域副本**（17,352 B，sha256 `d21b555a…`），用于回归；**不是**对 `_v12_rule.py` 的落地。

### 2.3 (c) 可粘贴片段（替换 `:116` 那一行及其上下文）

**全文**：`_h5_pasteable.py`（`import re` + 常量 + `_h5_mask_quotes` / `_h5_last_micro` / `_h5_no_second_subject` / `h5_govern`）。把该文件除模块 docstring 外的内容**插到 `def classify_v12` 之前**（即 `_v12_rule.py:107` 之后）。四处精确替换（逐字，`_h5_patch.py` 已用 `assert count==1` 验证锚点唯一）：

```python
# ① 替换 _v12_rule.py:115-116（含 :114 注释行）
    # ---- H5 补丁：管辖 = 前向 + 同微句 + 有辖域路径 + 非双重否定 ----
    gov = h5_govern(pre, post)
    adj_neg = gov["adj_neg"]
    prohibit_U = gov["prohibit_governs"]      # ← 取代 any(k in U_bare ...)
    double_neg = gov["double_neg"]

# ② 替换 _v12_rule.py:135（append 行 :136 不动）
    if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:
        hard.append("H5_否定禁止管辖")

# ③ 在 _v12_rule.py:143 `if hard:` 【之前】插入（放 return 之后即成死代码）
    if double_neg:
        return {"verdict": "V2", "hard": [], "weak": [],
                "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],
                "unit": U, "line": line, "review_flag": False,
                "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}

# ④ 替换 _v12_rule.py:152
    if hit_override and not adj_neg and not prohibit_U and not double_neg:
```

说明：②让 H5 不因双重否定而误豁免；③让双重否定**主动**判 V2（否则 `DOUBLE_2/3` 会掉回 S3 或 S1，仍是「碰巧」）；④堵住 `V2_OVERRIDE` 在双重否定句里抢先返回 V2 之外的路径一致性。`U_bare = _strip_quotes(U)`（`:112`）保留但不再用于 `prohibit_U`（避免误删后仍有引用问题；若所有者希望彻底删掉也可，`_h5_v12_patched.py` 里保留未用）。

### 2.4 (d) 为什么「只检查 distance」不够（实跑反例）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_distance.py` → `_h5_distance_out.txt`。四组对照，全部实跑旧/新两轨 + `r10_context` 的 24 字窗口：

| 组 | 文本 | `n`→token 距离 | R10 | 期望 | 旧 | 修后 |
|:--|:--|--:|:--|:--|:--|:--|
| A | `不得写成未入账的本笔已入账` | 10 字 | negation (neg_count=2) | **CATCH** | PASS ❌ | CATCH ✅ |
| A | `不得宣告 N-4 正式绑定已生效` | 13 字 | negation (1) | **PASS** | PASS ✅ | PASS ✅ |
| B | `不宣告 N-4 正式绑定已生效` | 12 字 | negation (1) | **PASS** | CATCH ❌ | PASS ✅ |
| B | `本笔已入账 0 命中不得写成未入账` | **−8 字（在后）** | assertion (0) | **CATCH** | PASS ❌ | CATCH ✅ |
| C | `不宣告 N-4 已生效，但本笔已入账` | 15 字（窗内） | negation (1) | **CATCH** | CATCH ✅ | CATCH ✅ |
| C | `不宣告 N-4 已生效；本笔已入账` | 14 字 | assertion (0) | **CATCH** | CATCH ✅ | CATCH ✅ |
| D | `并非不宣告已生效` | 3 字 | double_neg (2) | **CATCH** | PASS ❌ | CATCH ✅ |
| D | `不宣告已生效` | 3 字 | negation (1) | **PASS** | PASS ✅ | PASS ✅ |

三条硬反例：

1. **同距不同真值**：A 组两句「不得」都在 10–13 字窗口内、都 <24 字，一句该 CATCH 一句该 PASS。纯距离阈值（≤24 字即豁免）无法区分「不得写成**未入账**的本笔**已入账**」（「不得」只支配前半定语，token 是后半真断言）与「不得宣告…已生效」（真管辖）。必须看 **G3 辖域动词路径 + 补语内无第二主语**。本补丁的形状 b 正是靠这一点分开的。
2. **后向距离是负的**：B 组第二句 `dist=-8`，任何「取绝对距离/看 U 内词」的做法都会把后置「不得」算进来；只有 **G1 前向性**（算子只在 `pre`）能挡住。
3. **奇偶计数失效**：D 组两句距离同为 3 字、否定词计数分别 2 和 1；`并非不宣告已生效`（2 个否定词）与 `不宣告已生效`（1 个）真值相反，但「两个独立否定短语」如 `无越权断言…不出现` 也是 2 个否定词却**不是**双重否定（`_g7_predicates.py:74-75` 明载）。故必须按**构式**识别（§3），不能数个数。C 组还显示 `r10_context` 的 `neg_count=1` 在「，但」跨子句后仍会污染（其 `CLAUSE_BREAK` 不含逗号，`_g7_predicates.py:71`），所以 **G2 的微句边界**也不可省。

---

## 3 第三步：双重否定识别

### 3.1 (a) 实读 R12 的实现与覆盖构式

读件：`lead/gate_fp7_20261108/_g7_predicates.py`（只读，sha256 `02c17e49…`/11,743 B，已对账）。

- `_g7_predicates.py:76`：`DOUBLE_NEG_RE = re.compile(r"(不得不|并非不|并不是不|不是不|无不|没有不|不无|不能不|不可不|未曾不)")` —— **十式，纯枚举、相邻连写**（本会话 `_h5_r12_gap.py` 实跑 `.pattern` 逐字打印并逐式 `search` 全 True）。
- `:69-71`：`NEG_RE`（不|无|未|非|禁|勿|否决|排除|不宣告|不得）、`NEG_WINDOW = 24`、`CLAUSE_BREAK = "。！？；\n"`（**不含逗号**）。
- `:78-111` `r10_context`：回看窗 `max(start-24, 最后一个句界)`，`neg_count` 只作信息；`dbl = bool(DOUBLE_NEG_RE.search(pre))`；`dbl → kind='double_neg'`，`neg_count≥1 → 'negation'`（豁免），`assertion` 才入 problems。
- `:134-148` `r12_scan`：对 `kind=='double_neg'` 的命中重新判违规（`problems` +1）；其 docstring `:136-139` 明确「不用否定词奇偶计数」。
- 明确**不覆盖**的是分离型/换写型；`GATE_FALSE_POSITIVE_5_6_7.md:162,267,279` 登记 **GV-L**：`亦非不宣告已生效` R10/R12 全 0 漏检；`GATE_N13_QUOTED_ASSERTION.md:442` 把它列为「分离型双重否定，本方案不修 R10/R12，只登记」；`GATE_PIPELINE_COMPOSE.md:65,266,272,488` 记为 GP-A1 合成链漏报（`R10=negation PASS / R12=0 / N13=C 放过 / 人工真值=真断言`）。

### 3.2 (b) 我自己找到的其它漏式（实跑实证）

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_r12_gap.py` → `_h5_r12_gap_out.json`。对 20 条候选构式逐条跑 `DOUBLE_NEG_RE.search` + `r10_context` + `r12_scan(text, ['已生效'])`：

| 漏式 | `DOUBLE_NEG_RE` | R10 kind | `dbl` | `r12_scan` problems | 语义 |
|:--|:--|:--|:--|--:|:--|
| `亦非不`（N13/FP7 已登记） | False | negation | False | **0** | 亦非不宣告 = 宣告 |
| `未尝不` / `未始不` / `未有不` | False | negation | False | 0 | 文言/书面双重否定 |
| `莫不` | False | negation | False | 0 | 莫不认为 = 都认为 |
| `不敢不` / `不会不` / `不可能不` | False | negation | False | 0 | 情态动词 + 不 |
| `未必不` / `未免不` | False | negation | False | 0 | 委婉肯定 |
| `岂能不` / `焉能不` / `哪能不` | False | negation | False | 0 | 反问式双重否定 |
| `不可谓不` / `不为不` | False | negation | False | 0 | 书面构式 |
| `并非没有` / `并非毫无` / `不是没有` | False | negation | False | 0 | 「并非 + 否定存在」= 有 |
| `并不否认` | False | negation | False | 0 | 「不 + 否认」= 承认 |

共 **19 条实跑 `r12_problems=0` 的漏式**（第 20 条 `没有不承认` 被 `没有不` 覆盖，`dbl=True / problems=1`，作对照）。8 条已在表内的构式对照组全部 `dbl=True / problems=1`。这是「枚举表非穷尽」的实测证据，与 `GATE_FALSE_POSITIVE_5_6_7.md:279`、`GATE_PIPELINE_COMPOSE.md:488` 的方向一致，但**逐式实跑是本会话新做的**。

### 3.3 (c) V12 的 H5 应当复用 R12 的识别，还是自己实现？

**判断：不直接 `import` / 调用 R12 的函数；在本补丁内做「语义复用 + 本地超集 + 改作用域」。** 三条理由（均有实读依据）：

1. **R12 的服务对象与 H5 不同**：`r12_scan(text, assert_tokens)`（`_g7_predicates.py:134-148`）是「全局扫描词表命中 → 报 problems」的门禁谓词，内部对**每一处命中再调 `r10_context`**；H5 需要的是「给定一处 `(pre, post)` 答 True/False」的纯函数。直接复用会把 24 字回看窗、`CLAUSE_BREAK` 不含逗号、`SPAN_RE` 引证跨度等 R10 口径一并带进来（§2.4 C 组已实证逗号污染）。
2. **R12 表本身有 19 条实测漏式**（§3.2）与 GV-L 残余；照抄等于把已知漏判移植进 V12。且 `_g7_predicates.py` 是**绝对只读**件，本任务无权改它来补表。
3. **架构上 V12 是独立前置分类器**：`_v12_rule.py:29` 只有 `import re`，`:4` 自述「只用 re / 静态文本」；`_v12_rule.py:108-170` 的契约是 `classify_v12(text,start,end,token) → dict`。引入对 `lead/gate_fp7_20261108/` 的运行时依赖会破坏它的单文件可用性与本任务「只出补丁设计、不改既有件」的边界。

**做法**：把 R12 十式**逐字保留**为 `H5_R12_TEN`（保证与既有门禁口径对账），另加 `H5_DN_EXTRA` 补 19 条漏式 + 一条分离型通配 `非[^，,。；;]{0,4}不(?:宣告|认定|认为|承认|说|写|登|记|填)`（覆盖 `亦非不宣告` / `非…不认定` 这类 GV-L）；识别只在 **G2 的 `scope`（管辖微句）**内做，不做奇偶计数（`_g7_predicates.py:74-75` 的教训）。若将来所有者允许改 `_g7_predicates.py`，正确做法是「把超集回填 `DOUBLE_NEG_RE`，V12 再改成 `import`」——但那是另一个写域的事，本补丁不代做。

### 3.4 (d) 可粘贴片段与第二步的衔接

见 `_h5_pasteable.py`：`H5_R12_TEN` / `H5_DN_EXTRA` / `H5_DOUBLE_NEG_RE`（`_h5_pasteable.py` 常量段，长式在前防 `并不是不` 被 `不是不` 先吃掉）。衔接点在 `h5_govern()` 内**第一步**：

```python
p = _h5_mask_quotes(pre)          # G4
scope = _h5_last_micro(p)         # G2（逗号/分号/转折后重取前缀）
dm = H5_DOUBLE_NEG_RE.search(scope)   # G5：只在管辖微句内识别
double_neg, dn_hit = bool(dm), dm.group(0) if dm else ""
adj_neg = ...                     # 形状 a（原 :115 语义）
bm = H5_BRIDGE_RE.search(scope)   # 形状 b（G1+G3，算子只在 pre/scope）
frame = ...                       # 形状 c（post 只用于谓语否定，不引入算子）
return {"adj_neg": ..., "prohibit_governs": bridge or frame,
        "double_neg": ..., "dn_hit": ..., "shapes": ..., "scope": ...}
```

`classify_v12` 侧的四处替换见 §2.3：② 让 `double_neg` 取消 H5 豁免，③ 让 `double_neg` **先于** `if hard:` 主动返回 `V2` 并带 `H5_DOUBLE_NEG:<构式>` 审计标记，④ 让 `V2_OVERRIDE` 不与 G5 冲突。三者共用同一个 `gov` 对象，不重复扫描、不引入第二套词表。

---

## 4 第四步：样本集与回归

### 4.1 (a)(b) 样本集

文件：`_h5_samples.py`（`POS 18` + `NEG 26` = **44 条**，均 ≥15）。

- **正样本 18 条（应 PASS）**：前向桥接 `不宣告/不认定/不承认/不认为/不写成`、禁止 `不得写成/不得宣告/不得把…写成/禁止填「…」/不得代填`、紧邻 `不授实施权/不放行 N-5`、长补语 `不宣告第 3 笔已入账`、含后置转折 `…，但后句另有安排`（转折不管辖 token）、全句否定辖域框 `**不可能/未覆盖**：已删除文件…未做`（现盘形态）。
- **负样本 26 条（应 CATCH）**，覆盖任务点名四类：
  - **后向禁止** 4 条：`N01–N04`（含 REGRESS1 / TRAIL_NEG 原句）；
  - **跨子句否定** 4 条：`N05–N08`（`但`/`；`/`。`/后置否定四种）；
  - **各类双重否定** 13 条：`N09–N21`，其中 R12 十式 7 条（`不得不/并非不/不能不/无不/并不是不/不可不/未曾不`）+ R12 漏式 6 条（`亦非不` GV-L / `未尝不` / `不敢不` / `并非没有` / `并不否认` / `莫不`）；
  - **token 在否定词与禁止词之间** 3 条：`N22–N24`（同句混用 / 分号 / 双算子夹击）；
  - 另 2 条纯断言对照 `N25–N26`。

### 4.2 (c) 在修好的实现上跑：correct / fp / fn

命令：`python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_patch.py`（生成写域修后副本）→ `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\h5_governance_20261109\_h5_regress.py`。输出 `_h5_regress_out.json` / `_h5_regress_out.txt`。

| 尺度 | 轨 | correct | fp（应 PASS 却 CATCH） | fn（应 CATCH 却 PASS） | 总数 |
|:--|:--|--:|--:|--:|--:|
| A 编排方九条 | 修复前 | 4 | 1 | 4 | 9 |
| A 编排方九条 | **修复后** | **9** | **0** | **0** | 9 |
| B 自建样本集 | 修复前 | 28 | 7 | 9 | 44 |
| B 自建样本集 | **修复后** | **44** | **0** | **0** | 44 |

`fp`/`fn` 定义：`expect=PASS` 而判 V2 ⇒ fp（误拦）；`expect=CATCH` 而判 V1 ⇒ fn（漏放/回退）。

### 4.3 (d) 与修复前对比：2 处回退修好？有无新回退？

**2 处确凿回退全修好**（`_h5_regress_out.json:A_nine` / `V12_FULL_IMPACT.md:223-224`）：

| 反例 | 修复前 | 修复后 | 修复后理由 |
|:--|:--|:--|:--|
| `本笔已入账 0 命中不得写成未入账` | V1 / `H5_否定禁止管辖` | **V2** | G1：禁止词在 post ⇒ 不管辖；`V2_OVERRIDE:已入账` 生效（`_v12_rule.py:36/:152`） |
| `审阅不得不承认本候选已生效。` | V1 / `H5_否定禁止管辖` | **V2** | G5：`H5_DOUBLE_NEG:不得不` 强制返回 V2 |

**同时保住真否定管辖**：`TRUE_NEG`（本节登记不宣告…已生效）修复前 V2 误拦 → 修复后 **V1 / PASS**（形状 b 桥接 `不`+`宣告`）；`LEAD_NEG`（不得写成已入账）修复前后均 V1 / PASS。**三条以「不」起的双重否定全部 CATCH**（`DOUBLE_1 V1→V2` 修好；`DOUBLE_2/3` 保持 V2 且理由从「碰巧」变成 `H5_DOUBLE_NEG:不能不` / `:无不`）。**后向禁止 `TRAIL_NEG` V1→V2 修好**。

**新回退 = 0**：B 集 44 条修复后 `fn=0`；A 集 9 条 `fn=0`；且修复前判对的 28/44 条中**没有一条被改错**（`_h5_regress_out.json:B_samples` 逐行比对，修复后错判行集合为空）。修复前 16 条错判逐条：`P01/P02/P03/P04/P05/P13/P14` 由 CATCH→PASS（7 条 fp 消除）、`N01/N02/N03/N04/N09/N10/N14/N22/N24` 由 PASS→CATCH（9 条 fn 消除）。

### 4.4 (e) 32 域现盘 26 处再跑

口径（`_h5_regress.py:C`）：读 `lead/gate_rejudge32_20261109/_rj_delivery_baseline.json` 的 32 域 `(domain, main, params.banned)` + `lead/v12_impact_20261109/_vi_shadow_out.json` 留盘的 26 处 `(pos, token)`，**真件现盘重算**（不 import 撰写人脚本），逐处用**原 pos** 调 `classify_v12(text, pos, pos+len(tok), tok)`，避免同 token 多次出现取错位置。

实跑输出（`_h5_regress_out.txt:C`）：

```
C counts = {"old_V1": 26, "new_V1": 26, "changed": 0, "baseline_fp_mismatch": 0}
```

- 修复后**仍 26 处判 V1**（`V12_FULL_IMPACT.md:94` 基线 `V12 verdict={"V1": 26}`、`_vi_shadow_out.json:summary.v12_verdict_counts` 一致）。
- **本来对的没有变错**：`changed=0`，26 处逐处 `old==new`；`baseline_fp_mismatch=0`（32 件 main 的 sha256/字节数与 baseline 全匹配）。
- 逐处保住的机制（`_h5_ctx26_out.json`，8 处旧 `H5_否定禁止管辖`）：
  - `n10c04_ruling L5/L44/L425`、`n4_yi_final L17/L150`：`pre[-1]='不'` → 形状 a；
  - `n10c04_ruling L348` 两处：`H2_引述占位` 与 H5 双标记，修复后仍 V1；
  - `n4_yi_final L17`（不放行 N-5）形状 a + `H2` 保留；
  - `s604_script_hunt L143`「**不可能/未覆盖**：已删除文件…carving 未做」：`adj_neg=False / 旧 prohibit_U=True`，修复后靠**形状 c 全句否定辖域框**继续 V1（这是形状 c 存在的唯一现盘理由；若无它，此处会翻成 V2，构成新回退）。

---

## 5 第五步：修复后的取舍建议

### 5.1 (a) 修好 H5 之后，V12 能不能插进生产门禁？

**判断：仍然不能全局插入；可在严格白名单 + 影子模式下有限启用。** 依据：

- H5 是 `V12_FULL_IMPACT.md:226` 认定的「唯一实质缺陷」，但 `:287` 明列**四条前置条件**：「只对白名单 3 域启用 / 先修 H5 管辖误判与 `V2_OVERRIDE` 自指词 / S3 不再无条件 fail-closed / 补齐逐处回归门槛并先影子 N≥3 轮」，并写「缺一即净损失」。本补丁只满足第 2 条的一半（H5 已修，`V2_OVERRIDE` 自指词**未修**）。
- `:333` 的 11 条反例门槛：本补丁实跑已让 2 条回退（§6.3(b) 第 2 项）达标，但 §6.3(b) 第 3 项「3 处 S3 误拦必须 PASS」、第 4 项「6 处检索/标题形态必须 PASS」、第 6 项「同触双标记回报」**均不在本补丁范围**，现状仍不达标（§5(b)）。
- `V12_FULL_IMPACT.md:344` 总闸门原话：「在门槛补齐并修掉 H5 管辖误判 / `V2_OVERRIDE` 自指词之前，**不建议把分类器真正插入任何生产门禁**」。
- 本会话未重新实跑 `_v12_verify.py` 的 `V1 22/22、V2 14/14、MIXED 4/4` 套件（`V12_FULL_IMPACT.md:348` 亦标「未验」），也未跑影子 N≥3 轮；故**「可插」这一结论本会话不成立**，标未验。

### 5.2 (b) 还有哪些未修的缺陷（逐条）

| # | 缺陷 | 证据 | 本补丁是否处理 |
|--:|:--|:--|:--|
| 1 | **`V2_OVERRIDE` 把禁用词自身当宣称词**：`_v12_rule.py:36` 把 `已入账` 列入 `V2_OVERRIDE`，使「已入账 grep 结果/核查命令」等检索形态被判 V2。实跑 6 处新增误报 | `V12_FULL_IMPACT.md:242-247`（P02/P03/P04/P05/P07/P16）、`:324-328` 门槛第 4 项 | **未修**（本任务只做 H5 管辖） |
| 2 | **S3 无条件 fail-closed**：`_v12_rule.py:167-170`「判不了 → V2 + review_flag」，把「机器判不了」直接转成误拦；3 处应 PASS 被误拦，且 P09/P10 同型句一 V2 一 V1 随格式抖动 | `V12_FULL_IMPACT.md:230-232,289-296`、`:325` 门槛第 3 项 | **未修** |
| 3 | **提前 return 抹掉 hard/override 双标记**：`:143-146` 返回时 `override/weak` 恒空，与 `:23-27` 承诺不符 | `V12_FULL_IMPACT.md:260`（`hard_AND_override=2`、`hard_AND_weak=9`）、`:330` | **未修** |
| 4 | **双重否定表在 R12 侧仍漏 19 式 + GV-L**：本补丁只在 V12 的 H5 本地超集补齐；`_g7_predicates.py:76`（绝对只读）未改，R10/R12/N13/合成链仍漏 | `_h5_r12_gap_out.json`、`GATE_N13_QUOTED_ASSERTION.md:442`、`GATE_PIPELINE_COMPOSE.md:266,488` | **部分**（仅 V12 侧） |
| 5 | **词表不对齐 / 相关失效**：R10/R12/N13 共用字面词表与否定词表，三层一致通过 ≠ 正确 | `GATE_PIPELINE_COMPOSE.md:63,272,499` | 未修（跨层架构） |
| 6 | **本补丁的形状表仍是枚举/启发式**：桥接动词、微句边界、`24` 字补语上限、`SELF_SUBJ` 词表都是有限枚举；分离型「非…不」只覆盖一条通配；跨行/跨小节/同义改写/被动式/英文未覆盖 | `_h5_pasteable.py`、`GATE_N13_QUOTED_ASSERTION.md:459-471` 边界表 | 部分（已在 §5(d) 给替代方案） |

### 5.3 (c) 「V12 达到可插条件」检查清单

沿用并补全 `V12_FULL_IMPACT.md:324-331` 的 7 条，逐条给可实跑的判据：

1. **指纹门槛**：加载前 `hashlib` 验 `_v12_rule.py` = `15e421…`/9148（落地后应更新为新指纹）、`_g7_predicates.py` = `02c17e…`/11743、baseline 32 件 main 全匹配；失配拒绝运行。本会话已实跑 8/8 MATCH（§6）。
2. **H5 管辖门槛**：2 处回退反例必须 CATCH + 真否定管辖（TRUE_NEG / LEAD_NEG）必须 PASS + 三条 `DOUBLE_*` 必须 CATCH —— 本会话 A 集 **9/9 达标**（`_h5_regress_out.json:A_score.new`）。
3. **样本集门槛**：≥15 PASS + ≥15 CATCH 且四类负样本齐备，`correct=total / fp=0 / fn=0` —— 本会话 B 集 **44/44、fp=0、fn=0** 达标。
4. **32 域逐处对账**：26 处 `(pos,token,R10 kind,V12 verdict)` 与 `_vi_shadow_out.json` 一致、`changed=0`、无新回退 —— 本会话 **26/26、changed=0** 达标。
5. **`V2_OVERRIDE` 自指词门槛**：P02/P03/P04/P05/P07/P16 六处检索/标题形态必须 PASS（`V12_FULL_IMPACT.md:328`）—— **当前不达标，须先修 `_v12_rule.py:36/:149-156`**。
6. **S3 门槛**：P09 / P15 / TV3:L10 三处应 PASS 必须 PASS；建议按 `V12_FULL_IMPACT.md:296` 把 S3 改为「verdict 回退上一轨 + `NEEDS_HUMAN`」，或限定「仅当 U 内无检索/标题/清单结构」才 fail-closed —— **当前不达标**。
7. **双标记回报门槛**：`hard∧override`(2) 与 `hard∧weak`(9) 须在输出同触可见 —— **当前不达标，须修 `:143-146` 提前 return**。
8. **原回归套件**：`_v12_verify.py` 的 `V1 22/22 / V2 14/14 / MIXED 4/4` 须 100%（`_v12_regression.json:224-229`）—— **本会话未重跑，标未验**，落地前必须实跑。
9. **影子 N≥3 轮**：每轮真实交付跑 `_vi_shadow.py` 口径，连续 N 轮 `新增误报=0 且 回退=0 且 S3 误拦=0` 才分级扩域（`V12_FULL_IMPACT.md:335`）—— **未实施**。
10. **双重否定统一**：把 §3.2 的 19 式 + GV-L 回填到 `_g7_predicates.py:76`（需所有者授权另一写域），否则 V12 与 R12/N13/合成链口径不一致 —— **未实施**。

**总闸门**：1–4 本会话已达标；5–10 未达标/未验。故「可插」= 否。

### 5.4 (d) 若 H5 修不好（语义太复杂），替代方案

按代价从小到大，全部**不把 V1/V2 分类器插进真门禁**：

1. **白名单 + 精确参数匹配（首选）**：`V12_FULL_IMPACT.md:314-322` 实跑过的方案 —— 按 `(domain, tuple(banned))` 精确匹配 3 域（`c07_slot` / `c07_truth_protocol` / `s604_script_hunt`），不在白名单**完全不调用 `classify_v12`**，保留原 R10/R12 结论。明确排除 `DEFAULT_TOKENS=("已入账","已追加","已生效")` 与 `ASSERT_TOKENS` 五词的门禁族。这 3 域的收益来自 S0 HARD_V1（`:268,293`），不依赖 H5 的长距语义。
2. **只做「后向/跨子句」的窄补丁，放弃长距前向管辖**：把 `:116` 改成 `prohibit_pre = any(k in pre for k in PROHIBIT)`（只把算子限制在 `pre`），可修掉 REGRESS1 / TRAIL_NEG；但 TRUE_NEG 仍会被 S3 误拦、双重否定仍漏。配合「H5 只作 warning 不判 verdict」，把拿不准的交给 `NEEDS_HUMAN`。代价最小、语义风险最小。
3. **回退到在位 N13/R13 轨**：`V12_FULL_IMPACT.md:286` 实跑 `N13 gate correct=43/45 (FP=0,FN=2)` 优于 `V12 correct=34/45 (FP=9,FN=2)`；`GATE_PIPELINE_COMPOSE.md:414` 合成链 69/74。不插 V12，用 N13 + R10/R12 的既有链，V12 仅留作影子差分。
4. **把 H5 降级为「只加审计标记」**：`H5_否定禁止管辖` 不改 verdict，只写 `review_flag` / `shapes[]`，由人工逐处裁决；真门禁继续走朴素字面 + R9/R11。与 `V12_FULL_IMPACT.md:296` 对 S3 的建议同构。
5. **词表/语料层面堵口（最保守）**：在交付模板里禁止「完成词与禁止词同单元」的写法，直接把 REGRESS1 这类句子改写为两条分句；`GATE_PIPELINE_COMPOSE.md:499` 提醒「一致不是正确」，故仍需人工抽检。

---

## 6 指纹/只读件对账与实跑命令清单

**本会话实跑的指纹复算**（`python -I -X utf8 -c "<hashlib 逐件 read_bytes>"`，两次：会话首、末）：

```
MATCH 9148   lead/gate_v1v2_20261109/_v12_rule.py                 15e4211f…
MATCH 32956  lead/v12_impact_20261109/_vi_REPORT.md                9375f37c…
MATCH 52341  lead/v12_impact_20261109/_vi_probe_out.json           7fd90337…
MATCH 11743  lead/gate_fp7_20261108/_g7_predicates.py              02c17e49…
MATCH 16649  lead/gate_n13_20261109/_n13_predicates.py                                   e1195b3b…
MATCH 15811  lead/gate_pipeline_20261109/_gp_pipeline.py           25c7753f…
MATCH 52419  lead/PENDING_DECISIONS.md                             3765eddb…
MATCH 759518 lead/GOAL_THREE_TARGETS_20261018.md                   2baa0de4…
```

8/8 与编排方【实跑指纹】逐字一致；会话末复跑仍 MATCH ⇒ 绝对只读件未被修改/追加/覆盖。`gate_v1v2_20261109/__pycache__/_v12_rule.cpython-312.pyc` 与 `gate_fp7_20261108/__pycache__/_g7_predicates.cpython-312.pyc` 时间戳仍为 12:18:26 / 00:45:10（会话前），本会话脚本一律 `sys.dont_write_bytecode=True`，未生成新字节码。

**实跑命令清单**（全部 `python -I -X utf8` + 绝对路径）：

| # | 命令 | 关键输出 |
|--:|:--|:--|
| 1 | `…\_h5_repro9.py` | 九条 `loaded=True`，逐条 verdict/hard/override/weak 与编排方一致 → `_h5_repro9_out.json` |
| 2 | `…\_h5_ctx26.py` | 26 处 U/pre/post，8 处旧 H5 逐处列 → `_h5_ctx26_out.json` |
| 3 | `…\_h5_r12_gap.py` | R12 十式全 True；19 条漏式 `r12_problems=0` → `_h5_r12_gap_out.json` |
| 4 | `…\_h5_patch.py` | 绑定行 `15e421…/9148`；修后副本 `d21b555a…/17352` → `_h5_v12_patched.py` |
| 5 | `…\_h5_regress.py` | `A 9/9`、`B 44/44 fp=0 fn=0`、`C old_V1=26 new_V1=26 changed=0` → `_h5_regress_out.{json,txt}` |
| 6 | `…\_h5_distance.py` | 8 条距离反例，4 组同距/后向/跨子句/双重否定 → `_h5_distance_out.{json,txt}` |
| 7 | 首末两次 `hashlib` 复算 | 8/8 MATCH |

**未跑 / 未验（如实登记，不补造）**：`_v12_verify.py` 的 `22/22 · 14/14 · 4/4` 原回归套件本会话未重跑；影子 N≥3 轮未实施；「S3 verdict 回退上一轨 + NEEDS_HUMAN」的完整后果未实测；编排方 `v12_api` 原始脚本未独立重放（其脚本不在本次可读件里）；本补丁未做真实生产门禁插入，全部为影子/写域副本对照。

**产出清单**（唯一写域 `lead/h5_governance_20261109/`）：`_h5_DESIGN.md`（本件）、`_h5_pasteable.py`（可粘贴片段）、`_h5_patch.py`（机械施加）、`_h5_v12_patched.py`（修后副本，**非**既有件）、`_h5_samples.py`、`_h5_regress.py` / `_h5_regress_out.{json,txt}`、`_h5_repro9.py` / `_h5_repro9_out.json`、`_h5_ctx26.py` / `_h5_ctx26_out.json`、`_h5_r12_gap.py` / `_h5_r12_gap_out.json`、`_h5_distance.py` / `_h5_distance_out.{json,txt}`。

**改前 / 改后一行对照**（供所有者决定是否落地）：

| | 改前（`_v12_rule.py:116` + `:135`） | 改后（`_h5_pasteable.py` + 四处替换） |
|:--|:--|:--|
| 判据 | `any(k in U_bare for k in PROHIBIT)`：U 内有禁止词即豁免 | `h5_govern(pre, post)`：G1 前向 + G2 同微句 + G3 辖域路径 + G4 引证屏蔽 + G5 非双重否定 |
| 九条 | 4 对 / 5 错（4 漏 1 误拦） | **9 对 / 0 错** |
| 自建 44 | 28 对 / fp=7 / fn=9 | **44 对 / fp=0 / fn=0** |
| 32 域 26 处 | 26 V1 | **26 V1，changed=0** |
| 2 处确凿回退 | 2/2 放过 | **2/2 抓住** |
| 真否定管辖 | TRUE_NEG 被误拦 | **TRUE_NEG 放过** |

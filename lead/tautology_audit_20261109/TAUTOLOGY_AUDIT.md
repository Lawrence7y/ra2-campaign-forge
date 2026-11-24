# TAUTOLOGY_AUDIT.md — 「重言式包装成定理」模式审计（撰写件）

> 撰写件：本任务 `actor#3`（重言式审计撰写员）。唯一写域 = `lead/tautology_audit_20261109/`。
> 本件为【交付】指定的主交付件名 `TAUTOLOGY_AUDIT.md`；写域内另有 13 件 `_ta_*` 中间产物（审计员产出，本撰写会话未改动）。
> ★ 只做**模式审计**，不改任何脚本、语料、产物。绝对只读九目录 + 两件台账，一律未改、未追加、未覆盖。
> 零真机（未启 `gamemd.exe`/`ra2loader`/`YURI.exe`、未 `taskkill`、未读活进程内存）。
> 零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> 不 commit、不 push。Python 一律 `python -I -X utf8 -c` + 绝对路径；指纹一律 `hashlib.sha256` 现盘重算。
> 引用只追「本次会话实跑命令 + 输出」或「文件:行」；拿不到的一律写**未验**，不补造。
> ★ 本件核心：`A⊆B` 恒成立 与 `A=B` 是**两个不同强度的命题**；把前者的证明当成后者的证明，是本任务要抓的模式。

---

## 1 目的与边界

### 1.1 目的

把「把重言式（或仅 N 行观测）包装成定理」做成**可识别、可复核、可防错**的模式件：

1. 复核编排方【拆解数据】：`A_n=18 / B_n=18 / A_subset_B=true / B_subset_A=true / sets_equal=true`，
   并独立判出 `A⊆B` 是**重言式**、`B⊆A` 才是**实质条件**。
2. 给「重言式 vs 实质条件」的**快速判据**与反证检查法（§3）。
3. 普查本库同模式，**五处逐处判**不笼统（§4.2）。
4. 评估**强度夸大**的危害，并与「口径错置」区分（§5）。
5. 对上一轮三句措辞给**逐句替换**（§6.2），不用「措辞需谨慎」概括。

### 1.2 边界与铁律（本次会话实跑核验）

| 铁律 | 本次会话核验 |
|---|---|
| 零真机 | 全部计算为 `python -I -X utf8 -c` 内联；无 subprocess、无进程内存读取（§6.6） |
| 零采样代码 | 只用 `json / hashlib / pathlib / itertools / collections / fractions / importlib.util / re / sys`；无 hook、MiniDump、SuspendThread、StackWalk、探针注入、动态内存解析 |
| 绝对只读 | 九件指纹本次会话重算 **2 次**（首轮 `ALL_9_MATCH = True`、收尾 `READ_ONLY_9_FINAL_MATCH = True`）；两件台账 SHA 全等基线 |
| 唯一写域 | `git status` 限定写域只有 14 件 `_ta_*` + 本件；未触碰只读域 |
| 不 commit / push | `git log -1 --oneline` = `2657458`（本次会话实跑，未变） |
| 只做模式审计 | **未改任何脚本、语料、产物**；只新建本交付件 |

### 1.3 本件相对【审计】回件的立场（如实）

【复核】`verdict = "partial"`（复核员 `ranCommands=43`；审计员 `ranCommands=16`）。按【交付】规则
「refuted 或 partial 标 unconfirmed」，本件**如实记 `partial` / `unconfirmed`**，不自行升格 `confirmed`。
复核确认的 6 处可复核缺口，本件逐条修正并登记（§6.1.2）：

- 缺口 ★1（替换不准）：§5.1 #1 把 `METRIC_CONVENTION_AUDIT.md:104` 当成须撤回的旧读法；
  实读 `:104` 是**正确的否定句**（`_ta_…md:295` 的 S2 行自己也判「`:104` 本身正确」），内部矛盾。
  → 本件 §6.2 #1 撤回对象改为**编排方三句旧措辞**与 `METRIC_CONVENTION_AUDIT.md:108,272`、前件 `:146`，
  **明确不撤回 `:104`**。
- 缺口 ★2（可粘贴清单自相矛盾）：`_ta_…md:213` 把两半 forbidden set 写成同一个
  `F(A⊆B)=B∧¬A`、`F(B⊆A)=B∧¬A`。→ 本件 §3.3 写对：`F(A⊆B)=A∧¬B=∅`、`F(B⊆A)=B∧¬A`。
- 缺口 ★3（引用不准）：`_ta_…md:365` 引 `METRIC_CONVENTION_AUDIT.md:211`「精确相等」；实读 `:211` 是
  4.45 倍数表行，该词在 `:125,162`。→ 本件 §5.3 改引 `:125,162`。
- 缺口 ★4（悬空引用）：`_ta_…md:205`「见 §3 #R7」不存在（判定表编号 S1–S16）。→ 本件改「见 §4.3 S12」。
- 缺口 ★5（判据外推）：一句话判据作为「任一恒等」的全称表述是外推。→ 本件 §3.1 附 N1–N4 别例实跑，
  明确标注适用范围与**未验**。
- 缺口 ★6（框架不干净 / `r13` 笔误）：四值「已证」同时覆盖「仅 N 行」与「全称」；且照抄
  `LAYER_IDENTITY.md:376,393` 的 `r13` 笔误。→ 本件 §4.3 用「类别 × 范围」双标签，并统一用 `n13`。

另：复核额外发现编排方门禁自洽性问题（写域当时无 `TAUTOLOGY_AUDIT.md`、且「五处」0 命中）。
本件按【交付】命名落盘并含「五处」字面，§6.1.3 实跑门禁代码复核。

---

## 2 上游指纹（九件）+ 拆解复核

### 2.1 九件上游指纹（本次会话 `hashlib` 现盘重算，2 次全等）

实跑命令（本次会话，内联）：

```
python -I -X utf8 -c "<9 件 read_bytes + hashlib.sha256 + len + 对照编排方【编排方指纹】基线>"
```

输出：`ALL_9_MATCH = True`；逐件 `MATCH=True`。收尾二次重算 `READ_ONLY_9_FINAL_MATCH = True`。
以下 9 行为**严格格式绑定行**（`被核对象 SHA256 = <64 hex>，字节数 = <n>`，中间无路径/括号/星号/反引号/空格）：

被核对象 SHA256 = 13453a000c61cb211c51931cc8a7bd3d1912a9e1714d46cb8be349686fe9c957，字节数 = 47501
被核对象 SHA256 = ef6e4cc8a01219e8d0c052061623a7993eaa298f20b04ec95c009bb527f950b3，字节数 = 59941
被核对象 SHA256 = f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503，字节数 = 45362
被核对象 SHA256 = 4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16，字节数 = 34964
被核对象 SHA256 = aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523，字节数 = 36194
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

九件依次对应：`_li_LAYER_IDENTITY_PROOF_20261109.md`、`LAYER_IDENTITY.md`、
`METRIC_CONVENTION_AUDIT.md`、`KEFF_CALC.md`、`EVIDENCE_INDEPENDENCE.md`、
`_gp_regression_out.json`、`SCORE_DECOMP.md`、`PENDING_DECISIONS.md`、
`GOAL_THREE_TARGETS_20261018.md`（顺序与【编排方指纹】一致）。

补测二件（只读谓词源码，本次会话实算，供 §2.5 反例引据绑定；两值全等
`LAYER_IDENTITY.md:359-360` 所记）：

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

### 2.2 拆解复核：A / B 大小、两个包含方向、八格列联表

本次会话实跑（数据源 `lead/gate_pipeline_20261109/_gp_regression_out.json:rows`，74 行）：

```
python -I -X utf8 -c "<读 rows；A={r10=P&r12=P&n13=P}、B={r10=P&n13=P}；逐 id 比对；8 格列联表；P(r12|n13)>"
```

输出逐字：

```
n = 74
A_n = 18  B_n = 18
A_subset_B = True  B_subset_A = True  sets_equal = True
only_A = []  only_B = []
PASS | PASS | PASS = 18
PASS | PASS | CATCH = 12
PASS | CATCH | PASS = 0
PASS | CATCH | CATCH = 4
CATCH | PASS | PASS = 20
CATCH | PASS | CATCH = 20
CATCH | CATCH | PASS = 0
CATCH | CATCH | CATCH = 0
den 38 num 38 ratio 1.0
n13P_r12C ids = []
r12=CATCH ids = ['R10-TV3', 'R10-CTX-05', 'R10-CTX-06', 'GP-C04']
F(B⊆A) rows (r10=P,n13=P,r12=C) = []
cells_r10C_n13P_r12C = 0
```

判定：编排方【拆解数据】的 `n=74 / A_n=18 / B_n=18 / A_subset_B=true / B_subset_A=true /
sets_equal=true / note_A_is_B_plus_r12=true / n13pass_r12catch=[] /
r12catch_r10pass=[R10-TV3, R10-CTX-05, R10-CTX-06, GP-C04]` **全部独立复现成立**。
定义见 `LAYER_IDENTITY.md:125`、`:104`；前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:125`。

### 2.3 `A⊆B` 为什么是**重言式**

```
A = { r10=PASS & r12=PASS & n13=PASS }
B = { r10=PASS          & n13=PASS }
即 A = B ∩ {r12=PASS}（编排方 note_A_is_B_plus_r12 = true）
```

由合取消去 `X∧Y ⇒ X` 直接得 `A⊆B`：不读任何语料、不读任何代码、不读 74 行、不依赖
`tokens`/换行契约。本次会话 2³=8 种真值格局穷举实跑：

```
python -I -X utf8 -c "<itertools.product 8 格；逐格打印 inA/inB/A==B/P(r12|n13)=1/breaks_BsubA>"
```

输出 `A⊆B taut over all 8? True`、`F(A⊆B) = [] (must be empty)`。
`LAYER_IDENTITY.md:104` 自记「`A ⊆ B` 是去掉一个合取项的重言式」，`:126` 同判；前件 `:125` 同判。

**强度结论**：`A=B` 需 `A⊆B ∧ B⊆A` 两半；`A⊆B` 这一半是**定义使然、恒真、零信息量**。
把它写成「决定性集合等式」的一半证明，就是**强度夸大**。等式的信息量全部在另一半 `B⊆A`。

### 2.4 `B⊆A` 是**实质条件**；74 行上有没有破坏

8 格穷举（同一次实跑）输出：

```
F(A⊆B) = []                              （必空 ⇒ 重言式）
F(B⊆A) = [('PASS', 'CATCH', 'PASS')]     （唯一禁止格）
F(P(r12|n13)=1) = [('CATCH','CATCH','PASS'), ('PASS','CATCH','PASS')]
F(P) strict_superset F(B⊆A)? True
forbidden sets equal (theorems)? False
fork cells (P false, B⊆A ok) = [('CATCH', 'CATCH', 'PASS')]
```

正确等价式（`LAYER_IDENTITY.md:126-128,240,365,376`）：

```
A = B  ⟺  不存在格 (r10=P & n13=P & r12=C)
      ⟺  P(r12=PASS | r10=PASS & n13=PASS) = 1
```

74 行上 `F(B⊆A)` 计数 = **0**（§2.2 八格表第 3 格、`F(B⊆A) rows = []`），故 `B⊆A` 在
74 行上**成立但只是观测事实**，逻辑上不必然（§2.5 X1 构造出恰好落在该格的输入）。

★ **两个不同强度命题不可混**：`P(r12=PASS|n13=PASS)=1` 的 forbidden 集还额外排除
`(r10=C, n13=P, r12=C)`，**严格大于** `F(B⊆A)`。分叉格 `CATCH CATCH PASS` 上
`A==B? True / P(r12P|n13P)=1? False`。本次会话构造反例实跑（§2.5 的 C5）：

```
text = '已入账 grep 结果。不得不承认放行 N-5'
r10,r12,n13 = CATCH CATCH PASS
inB = False  inA = False  B_subset_A_violated = False  n13P&r12C = True
```

⇒ 破 `P(r12|n13)=1` 而**不破** `B⊆A`，证伪前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146`
「同一个命题的两写法」（`LAYER_IDENTITY.md:122-130,337` 已列「修正①」）。
74 行上二者同真靠 `cells_r10C_n13P_r12C = 0` 这**第二处巧合**（§2.2 八格表第 7 格 = 0；
`LAYER_IDENTITY.md:87,128` 同判）。本任务不改该件，只登记模式。

### 2.5 ★ X1 反例复现（只读 `importlib`，`sys.dont_write_bytecode=True`）

实跑命令（本次会话，内联）：

```
python -I -X utf8 -c "<只读加载 _g7_predicates.py / _ei_n13_predicates_src.py；复刻 _liv_verify.py:44-51 的 judge；跑 C0/C1/X1/X2/X3/C5；打印 r12_scan 两种词表命中>"
```

输出逐字：

```
SHA 02c17e49… bytes 11743 lead/gate_fp7_20261108/_g7_predicates.py
SHA e1195b3b… bytes 16649 lead/evidence_indep_20261109/_ei_n13_predicates_src.py
C0  '并非不宣告已生效'        => PASS CATCH CATCH | inB False inA False | n13P&r12C? False
C1  'grep 结果：已入账 0 命中' => CATCH PASS PASS | inB False inA False
X1  '不得不承认放行 N-5'      => PASS CATCH PASS | inB True  inA False | A!=B? True | n13P&r12C? True
X2  '不得不承认可应用母本'    => PASS CATCH PASS | inB True  inA False | A!=B? True | n13P&r12C? True
X3  '第一行文字\r\n不得不承认，已入账 grep 结果' => PASS CATCH PASS | inB True inA False | A!=B? True
C5  '已入账 grep 结果。不得不承认放行 N-5'      => CATCH CATCH PASS | inB False inA False | n13P&r12C? True
r12_scan(BAD_BAN) hits = [{'token': '放行 N-5', 'pos': 5}]
r12_scan(T) hits = []
T tokens present in X1 text = []
n13 problems = [] details len = 0
```

`T = ['已入账','已追加','已生效']`（`n13.DEFAULT_TOKENS`），
`BAD_BAN = ['已生效','可应用母本','放行 N-5','已入账','已追加']`
（`_liv_verify.py:26-27`）。与 `_liv_verify.py:70-79`、`LAYER_IDENTITY.md:176-182` 三行表全等。

**机制（源码级，本次会话实读）**：`lead/gate_pipeline_20261109/_gp_regression.py:141` 让 R12 单层用
**该行 `tokens`**（X1 用 BAD_BAN 五词）；`:143` 让 N13 单层**恒用固定三词 `T`**。
`lead/evidence_indep_20261109/_ei_n13_predicates_src.py:200` 内部回调
`r12_scan(text, list(tokens))` 也用自身 `T`；`:241-245` 的「R12 命中无条件提升为 D」不触发 ⇒
`r13_assertions` 返回空 `problems` ⇒ `n13=PASS`（实跑 `n13 problems = []`）。
`lead/gate_fp7_20261108/_g7_predicates.py:134,144-145` 是 R12 的定义入口
（`ctx = r10_context(...); if ctx["kind"] == "double_neg"`）。

**为什么 X1 同时破两个命题**：X1 落在 `(r10=P, n13=P, r12=C)` 格 ——
① `∈B` 且 `∉A` ⇒ `B⊆A` 破 ⇒ `A≠B`（集合恒等破）；
② `n13=PASS ∧ r12=CATCH` ⇒ `P(r12|n13)=1` 破。
但二者**不是同一命题**（C5 破 ② 不破 ①）。X1 因恰好 `r10=PASS` 才落在两个 forbidden 格的交里。
准确说法：`A=B` 的全部非重言内容只有 `B⊆A` 这一半，它与
`P(r12|r10&n13)=1` 等价；`P(r12|n13)=1` 是**更强**的实质条件。

### 2.6 数值全等复现（供 §5 用）

本次会话实跑 `fractions.Fraction`：

```
agree = 38/74 = 0.5135135135135135
prior all3PASS|E = 3/39 = 1/13 ; 后验阶梯 3/39 → 3/3 → 3/3 ; rows removed by +r12=PASS = []
6 排列（正确条件分母）：prod 恒 1/13，non1 = 1/2/3 随顺序变
q10=19/39  q12=35/39  q13=1/13  min=1/13  P(all3PASS|E)=1/13 equals min? True
prod2 = 19/507 = 0.03747534516765286
prod3 = 665/19773 = 0.033631720022252565
chain/prod3 = 1521/665 = 2.287218045112782
H1 已证伪：EVIDENCE_INDEPENDENCE.md:247（「各层误差在给定真值 E 下条件独立（本语料已被证伪）」）、:256（「不得用 Πq_i」）
```

---

## 3 重言式判据（本任务核心）

### 3.1 ★ 快速判断方法（五问，逐问须落 `file:line` 或实跑输出）

给定任一 `A = B` / `A ≡ B` / 「恒等 / 决定性 / 必相等 / 恒真 / 恒成立」断言：

1. **拆两半**：`A=B` 一律拆成 `A⊆B` 与 `B⊆A`，**逐半判**，禁止合并报「等式成立」。
2. **展开定义**：把 A、B 写成原子谓词的合取/析取；若 `A = B ∧ C`，则 `A⊆B` 立即是
   合取消去重言式，**零证据量**，从「证明」里划掉。本例 `C = {r12=PASS}`。
3. **找禁止格**：非平凡方向的否定是 `B ∧ ¬A`；写出该格的最小充分条件
   （本例 `(r10=P, n13=P, r12=C)`），并给「哪一行代码 / 哪一份语料使它为空」。
4. **判来源**：使禁止格为空的依据是 (i) 纯逻辑/定义 ⇒ **重言式**；
   (ii) 代码级不变量（`file:line` + 全称证明）⇒ **实质条件·全称已证**；
   (iii) 本批语料统计（给 N、SHA、CI）⇒ **实质条件·仅 N 行观测**；
   (iv) 什么都没有 ⇒ **未验**。
5. **反证**：尝试构造一行破坏它（§3.3）。构造成功 ⇒ 该半是**实质条件且全称形式已被构造性证伪**；
   构造失败且能给出全称论证 ⇒ 才可能是定理。

**一句话判据（本例实跑有效）**：*把等号两边定义展开后，若其中一半能在不读任何数据、不读任何代码
的情况下只靠逻辑连接词就证明，那一半是重言式；等式的信息量全部在另一半。*

★ **适用范围（本次会话拿别例实跑，如实标注）**：该一句话对「`A = B ∩ C` 且 C 非平凡」这一类
恒等**可操作且已实跑通过**；但作为「快速判断任一恒等」的**全称表述属外推、未验**：

| 别例 | 本次会话实跑 | 对判据的影响 |
|---|---|---|
| N1 `Q={r10∧n13} ⊆ P={r10}` | `Q⊆P` 4 格全真（定义重言）；`P⊆Q` 在 `(r10=1,n13=0)` 破；74 行中 16 行 `r10=PASS,n13=CATCH` 证伪 `P⊆Q` | 判据可用：拆两半、找禁止格、构造反证 |
| N2 `U∩X = X`（U 为 8 格全集） | `taut? True` | 判据可用 |
| N3 `A = B = {x | x=x}` | 两半**皆**逻辑真，「信息量全部在另一半」落空 | 一句话**不适用**于此例 |
| N4 若 `(r10=P & n13=P) ⇒ r12=P` 是代码级不变量 | 则 `A⊆B` 仍由定义证、`B⊆A` 由代码证，两半**依据不同**且都非重言；`X=X` 代回规则不适用 | 五问仍可用，但「定义使然」类不适用 |

⇒ 本件把判据限定为**本例的可操作程序 + 五问清单**；「任意恒等皆适用」标**未验**。

### 3.2 五类识别特征与处置（覆盖任务的五类）

| 类型 | 识别特征 | 快速检验 | 本库对应实例 | 判定 |
|---|---|---|---|---|
| **定义使然** | 一方就是另一方的定义/展开 | 把定义代回，等式退化为 `X=X` | `A = B∩{r12=P}` ⇒ `A⊆B`（§2.3）；`LAYER_IDENTITY.md:104,126`、前件 `:125` | **重言式** |
| **合取项冗余** | 一侧多一个合取项，且该项在论域内被当成恒真 | 令该项为 False，看是否有一行分叉 | 「在两根已全 PASS 的行上 R12 **恒 PASS**」（`METRIC_CONVENTION_AUDIT.md:108`、`_ma_METRIC_AUDIT.md:77`）—— 74 行上成立，X1 里 `r12=CATCH` 与 `r10=n13=PASS` 共存 ⇒ 非恒真、是观测 | **实质条件·全称已构造性证伪** |
| **全集与子集** | `A⊆U` 或 `U∩A=A`，U 由枚举范围定义 | 检查 U 是否恰为「所有可能取值」 | C3 的 8 格是全集，`A⊆B` 在全部 8 格真 ⇒ 真重言；`SCORE_DECOMP.md:233-235` 的「S3 DEFAULT 恒真兜底」对正类样本必然命中、信息量 = 0，是**恒真兜底**而非恒等式（另类，见 §4.3 S12） | **重言式 / 恒真兜底** |
| **同义改写** | 两边是同一命题的措辞变体 | 写出两边 forbidden set，比对是否逐格相同 | 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146` 把 `B⊆A` 与 `P(r12\|n13)=1` 说成「同一个命题」—— C3/C5 证 forbidden sets 不同（后者还排除 `(r10=C,n13=P,r12=C)`）⇒ **不是同义改写，是等价性断言错误** | **已证伪（错置）** |
| **循环定义** | 结论已被写进前提（用 B 定义 A 再证 A=B） | 检查定义链是否成环、是否引入待证性质 | 「R12 是 R10 `double_neg` 的确定性子集」（`_g7_predicates.py:134-148`、`:144-145`）本身是代码级定义，可证；但拿它当「R12 不独立」的**独立**论据，则与依赖图是同一事实的两种说法，不构成额外证据（`LAYER_IDENTITY.md:160,166`） | **定义性陈述（可作前提，不可当独立佐证）** |

### 3.3 ★ 反证检查法（「若把它当实质条件会推出什么」）

按以下顺序做，**任何一步给「破」即停止并降级**：

1. **写 forbidden set（方向别写反，此处按复核 ★2 修正）**：
   `F(A⊆B) = A ∧ ¬B = ∅`（本次会话 8 格实跑无 `inA=1,inB=0` 格）；
   `F(B⊆A) = B ∧ ¬A = {(r10=P,n13=P,r12=C)}`。
   `F(P(r12|n13)=1) = {(n13=P,r12=C)}` **⊋** `F(B⊆A)`。
2. **枚举全部原子格局**（本例 2³=8，本次会话实跑），打印每格「等式真? / 条件概率真? / 破哪半?」。
   分叉格 `CATCH CATCH PASS`：`A==B? True / P=1? False / breaks B⊆A? False`
   ⇒ `forbidden sets equal (theorems)? False`（`LAYER_IDENTITY.md:130` 同判）。
3. **构造真实输入**（不是纸面真值表）：改一个契约前提，跑谓词直调，看是否落进 forbidden 格。
   本次会话 X1/X2/X3 三例全部 `r10=PASS r12=CATCH n13=PASS`，落进 `F(B⊆A)`。
   两条可复现破口：词表契约分叉（`_gp_regression.py:141` vs `:143`，X1/X2）；
   换行/位置错位（X3，`LAYER_IDENTITY.md:186` 已实读 CRLF→LF 归一）。
   本次会话实跑 `rows tokens NOT subset of T = 19`、`distinct token sets = 4`，破口在语料里真实存在。
4. **推出后果**：误把 `A⊆B` 当实质条件 ⇒ 少列一个待证条件；误把 `A=B` 当定理 ⇒ 推出
   「R12 不提供任何新信息（全称）」「可用独立因子 = 2」「三层连乘可改写两层」，
   分别被 X1、六排列、C11 证伪（§5.1）。
5. **强制报告格式**：
   `A=B ⟺ [重言半：定义式 + 8 格穷举] ∧ [实质半：禁止格为空，依据=…/仅 N 行]`，
   并附「破坏它的输入」（`LAYER_IDENTITY.md:393` 第 5 条已是此格式）。

### 3.4 可粘贴实现与检查清单

**可粘贴 Python**（本次会话所用形态，`python -I -X utf8 -c`，零写入、只读）：

```python
import itertools
V = list(itertools.product(['PASS','CATCH'], repeat=3))   # (r10, r12, n13)
for r10, r12, n13 in V:
    inA = (r10=='PASS' and r12=='PASS' and n13=='PASS')
    inB = (r10=='PASS' and n13=='PASS')
    assert not (inA and not inB)          # F(A⊆B)=∅ ⇒ A⊆B 是重言式
    print(r10, r12, n13, 'A==B?', inA==inB,
          'P(r12|n13)=1?', (n13!='PASS' or r12=='PASS'),
          'breaks B⊆A?', (inB and not inA))
F_AsubB = {v for v in V if (v[0]=='PASS' and v[1]=='PASS' and v[2]=='PASS')
                          and not (v[0]=='PASS' and v[2]=='PASS')}
F_BsubA = {v for v in V if (v[0]=='PASS' and v[2]=='PASS') and not (v[1]=='PASS')}
F_P     = {v for v in V if (v[2]=='PASS') and not (v[1]=='PASS')}
print('F(A⊆B)=', F_AsubB, ' F(B⊆A)=', F_BsubA, ' F(P)=', F_P)
print('forbidden sets equal (theorems)?', F_BsubA == F_P)     # 打印 False
# 反证：改一项契约前提跑真实谓词（§2.5 judge 形态）；
# 出现 inB=True, inA=False 即构造性证伪「A=B 是定理」
```

本次会话逐字实跑该片段：`F(A⊆B) = []`、`F(B⊆A) = [('PASS','CATCH','PASS')]`、
`F(P) = [('CATCH','CATCH','PASS'),('PASS','CATCH','PASS')]`、
`forbidden sets equal (theorems)? False`。

**检查清单（写报告前逐条打勾）**：

- [ ] `A=B` 已拆 `A⊆B` + `B⊆A`，并**分别**标类别与范围（§4.3 双标签）。
- [ ] 已展开定义，写明 `A = B ∧ C` 的 `C`（本例 `C={r12=PASS}`）。
- [ ] 已写非平凡方向的 forbidden 格，并给「使它为空」的 `file:line` 或实跑命令。
- [ ] 已枚举全部原子格局（2³=8），确认无隐藏分叉格；已比对两个 forbidden sets。
- [ ] 已做至少一次构造性反证（词表 / 换行 / 位置），并登记输出。
- [ ] 已给语料范围：`N`、数据源 SHA256 + 字节数、`train=test` 声明、零命中的 95% 上界。
- [ ] 已声明 `(predicate_sha, tokens_sha, text_sha, eol)` 四项契约；任一变化等式重算。
- [ ] 主结论不挂该等式；若挂了，改挂代码级依赖图 + A1–A5 五检（`LAYER_IDENTITY.md:267-273`）。
- [ ] 禁用串自检：`决定性集合等式 / 两个自由度 / 38/38 为定理 / B⊆A⟺P(r12|n13)=1`
      （`LAYER_IDENTITY.md:400`；该哨兵**仍是提案、未实装**）。
- [ ] 若声称「X 与 Y 是同一命题」，必须先比对两者 forbidden sets 逐格相同。

---

## 4 本库普查

### 4.1 范围与实跑命令

- **强模式扫描**：25 份 `.md`（`恒等/重言/决定性/必相等/恒真/恒成立/完全相同/A==B/取等/一致率/0 bit/unresolved/残留` 等 29 串），落 `lead/tautology_audit_20261109/_ta_grep_dump.txt`、`_ta_pattern_counts.txt`。
- **逐行抽取**：16 份文档（含两件台账）带行号，落 `_ta_passages*.txt` / `_ta_grep_dump.txt`。
- **全树扫**：`lead/` 全树 `.md/.txt/.json/.py` 扫 `一致率 / 22→0 / 无未验残留 / 恰取等 / 0 bit / 决定性集合等式 / 三句旧措辞`，落 `_ta_special_grep.txt`、`_ta_22to0_grep.txt`、`_ta_unresolved_grep.txt`、`_ta_three_phrases.txt`。
- 本次撰写会话对判定表所引 `file:line` 逐条**实读复核**（§2.5、§2.2、§4.2 的实跑输出），
  并把复核指出的 3 处引错改对（§6.1.2）。**未做全仓逐文件人工通读** ⇒ 见 §6.5 未验项。

### 4.2 ★ 五处逐处判（任务第三步(c) 五条 bullets，逐处给判定与依据，不笼统）

**第 1 处：「三层全 PASS 集合 == r10&n13 双 PASS 集合」**
位置：`METRIC_CONVENTION_AUDIT.md:108`、`_ma_METRIC_AUDIT.md:77`、前件 `:125,146`。
拆两半逐判：
- `A⊆B` 半 = **重言式**（`A = B∩{r12=P}`，8 格全真，§2.3）；
- `B⊆A` 半 = **实质条件·仅 74 行观测**，且全称形式**已构造性证伪**（X1/X2/X3 落
  `(r10=P,n13=P,r12=C)`，§2.5）；
- 「**决定性**集合等式」标签 = **强度夸大，须撤回**（`LAYER_IDENTITY.md:189,226,376` 已列须改
  「本 74 行观测等式」）。
数值 `A_n=B_n=18 / only_A=only_B=[]` **全对**（§2.2），错的只是强度。
另：前件 `:146` 把 `B⊆A` 与 `P(r12|n13)=1` 称「同一个命题」= **等价性断言错误，已证伪**
（C5 破 P 不破 `B⊆A`；`LAYER_IDENTITY.md:122-130,337`）。

**第 2 处：「r10×n13 一致率」与「R12 增量 0 bit」（两个不同量，分开判）**
- **一致率 `38/74 = 51.35%`**（`KEFF_CALC.md:120`、`EVIDENCE_INDEPENDENCE.md:127,131`、
  `_ma_verify_out.txt:49,51`）= **实质条件·纯计数恒等式（已证）**，不是重言式，也**不是独立性证据**。
  本次会话实跑 `agree = 38/74 = 0.5135135135135135`，交叉表
  `{(P,C):16,(C,C):20,(C,P):20,(P,P):18}`。`EVIDENCE_INDEPENDENCE.md:131` 自标
  「**一致率低 ≠ 误差独立**」；`_ma_METRIC_AUDIT.md:92-93,181` 明记 `ρ̄` 两口径不得混用。
  ★ 注意 `38/74` 与 `38/38=1` 是**同名不同分母**，勿混。
- **「R12 增量判别力 = 0 bit / 不提供任何新信息」**（`EVIDENCE_INDEPENDENCE.md:149,294,302`、
  `CHAIN_VS_SINGLE.md:204,206`、`_cs_BASELINE_ALIGNMENT_20261109.md:226,334`、
  `KEFF_CALC.md:432,434,440`）= **实质条件·仅 74 行观测；全称形式已被构造性证伪**。
  本次会话实跑后验阶梯 `3/39 → 3/3 → 3/3`、`rows removed by +r12=PASS = []`；该空集 ⟺ `B⊆A`，
  X1 使其非空 ⇒ 全称「0 bit」不成立。`KEFF_CALC.md:314,340` 已自标
  「观测值非定理、样本巧合 + 契约巧合」；`LAYER_IDENTITY.md:218,234` 已列须改「本 74 行观测」。
  ★ 与 `PVALUE_RECALC.md:197,250` 的 post-selection「≈0 bit」**不同论域**（`LAYER_IDENTITY.md:229`
  已判「不适用」），不得并判。

**第 3 处：「P(r12=PASS|n13=PASS)=1」**
位置：`METRIC_CONVENTION_AUDIT.md:106-107,290`、`KEFF_CALC.md:311-340`、`LAYER_IDENTITY.md:85,110`。
判定 = **实质条件·仅 74 行观测 / 全称未证且已构造性证伪**。
本次会话实跑 `den 38 num 38 ratio 1.0`、`n13P_r12C ids=[]`；X1/X2/X3 直接破（§2.5）。
`KEFF_CALC.md:315-326` 四种 95% 上界 `0.075808 / 0.078947 / 0.091810 / 0.092513`
（单侧精确 / rule-of-three / Wilson 双侧 / 双侧精确），`:314` 明写「不是精确 1.000、不是定理」；
`METRIC_CONVENTION_AUDIT.md:290` 自标「是否定理 ⇒ 未验」；本次会话把「未验」升级为
**构造性证伪为定理**（不是升级为「已证定理」）。

**第 4 处：「Fréchet min q_i 恰取等」**
位置：`KEFF_CALC.md:262-269,296`、`METRIC_CONVENTION_AUDIT.md:109,185`、`LAYER_IDENTITY.md:261,366`。
判定 = **实质条件·数学定理（Fréchet–Hoeffding 上界）+ 本 74 行实测取等（已证）**，非重言。
本次会话实跑 `q10=19/39 q12=35/39 q13=1/13`、`min=1/13`、`P(all3PASS|E)=1/13 equals min? True`。
取等条件 `{all3PASS∩E} = {n13PASS∩E}` 实跑 `3 = 3`、`sets equal? True` —— 这是**又一次集合包含取等**，
同样**不必然**，X1 类输入可破。`KEFF_CALC.md:265` 已自限「本 74 行内描述性天花板、非生产置信界」。
★ 与第 1 处的「集合恒等」不是同一命题，别把两处取等合并成一句「决定性」。

**第 5 处：「无未验残留」与「unresolved 22→0」（两个不同量，分开判）**
- **「无未验残留」**（`c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md:167`、
  `_tp_TP_VERIFIER_CHECKLIST.md:77`、`C07_TRUTH_SELF_PROOF.md:240`）= **未验**：三处都是三档判定表的
  「**通过**」格**条件**，不是已达成的事实。本次会话全树实跑该串**恰 3 命中**，全为条件行；
  `C07_TRUTH_SELF_PROOF.md:125` 明写「凡『未验』不得计入通过档」、`:261-267` §6.4 仍列 **6 条未验项**
  （协议未实施为代码 / 见证流程未演练 / ROUND_SUBAGENT_LOG 未查 等）。⇒ **不得读作「已无未验」**。
- **「unresolved 22→0」**（`CHAIN_VS_SINGLE.md:75,193`、
  `_cs_BASELINE_ALIGNMENT_20261109.md:124,211`、`COMPARABILITY_AUDIT.md:154,166,181`、
  `GATE_PIPELINE_COMPOSE.md:407,410,428`）= **实质条件·已证（算法换代 + 计数口径变更）**，
  且**已被上游自判为「空结论」**。本次会话实跑两版 JSON：
  `72 版 corpus_n=72 chain_unresolved_total=22 sum(layer_unresolved)=22 rows>0=18`；
  `74 版 corpus_n=74 chain_unresolved_total=0 sum=0`。
  `GATE_PIPELINE_COMPOSE.md:250-254` 实跑 `K7=0 K8=0` ⇒ `:254`「**未消解 0 不等于裁决全部成功**」；
  `COMPARABILITY_AUDIT.md:166` 判「`unresolved 22→0` 与 `chain` 翻转 18 行是**同一件事的两个计数**」。
  另实跑 `v1 chain=CATCH n=56 / unresolved>0 n=18 / u_not_c=[]` ⇒ `unresolved>0 ⊆ chain=CATCH`，
  是**不对称包含，不是恒等**。`chain_changed=18 / unresolved_changed=18 / sets equal? True`
  （`COMPARABILITY_AUDIT.md:158`）是两列同名不同量的**观测相等**，措辞未升级为定理，风险低。

### 4.3 判定表（S1–S16，双标签框架）

> 类别：`重言式` / `实质条件·全称已证` / `实质条件·仅 N 行观测` /
> `实质条件·全称已构造性证伪` / `未验` / `等价性断言错误`。
> 范围：`全称` / `仅 74 行` / `反事实` / `条件行` / `未验`。
> （按复核 ★6 修正：不把「仅 N 行」与「全称」都塞进一个「已证」桶。）

| # | 位置（file:line） | 断言要点 | 类别 | 范围 | 依据（本次会话实跑 / 实读） |
|---|---|---|---|---|---|
| S1 | `METRIC_CONVENTION_AUDIT.md:108`；`_ma_METRIC_AUDIT.md:77` | 「决定性集合等式」18 id 恰好等于 | 复合：`A⊆B`=**重言式**；`B⊆A`=**实质条件·全称已构造性证伪**；标签=**强度夸大** | 全称 / 仅 74 行 | §2.2 `18=18, only_A=only_B=[]`；§2.3 8 格；§2.5 X1；`LAYER_IDENTITY.md:189,226,376` |
| S2 | `METRIC_CONVENTION_AUDIT.md:104` | 「根因**不是**『R12 数值接近 1 所以近似省一层』，而是 R12 不是独立证据根」 | **实质条件·全称已证（正确否定句）** | 全称（依赖图） | 实读 `:104` 原文；`EVIDENCE_INDEPENDENCE.md:301`、`:111`；**该句本身正确，不列入撤回对象**（复核 ★1）。同段 `:272` 把集合等式列为「必附独立性依据」须改挂依赖图 |
| S3 | 前件 `:125,146` | `:125` `A⊆B` 是「去掉一个合取项的逻辑重言式」（对）；`:146` 称 `B⊆A` 与 `P(r12\|n13)=1`「同一个命题」（错） | `:125`=**重言式（判对）**；`:146`=**等价性断言错误·已证伪** | 全称 | §2.4 分叉格 `CATCH CATCH PASS`；C5 `'已入账 grep 结果。不得不承认放行 N-5'`；`LAYER_IDENTITY.md:122-130,337` |
| S4 | `LAYER_IDENTITY.md:126-128,240,365,376` | 正确等价式 `A=B ⟺ P(r12=PASS\|r10=PASS & n13=PASS)=1` | **实质条件·全称已证** | 全称 | §2.4 八格 + C5；`cells_r10C_n13P_r12C = 0`。注：`:376,393` 原文有 `r13` 笔误，本件统一写 `n13` |
| S5 | `EVIDENCE_INDEPENDENCE.md:149,294,302`；`CHAIN_VS_SINGLE.md:204,206`；`_cs_BASELINE_ALIGNMENT:226,334`；`KEFF_CALC.md:432,434,440` | 「R12 增量 0 bit / 不提供任何新信息」 | **实质条件·全称已构造性证伪** | 仅 74 行 | §2.6 后验阶梯与 `rows removed=[]`；X1；`KEFF_CALC.md:314,340` 自标观测 |
| S6 | `KEFF_CALC.md:120`；`EVIDENCE_INDEPENDENCE.md:127,131` | 一致率 `38/74 = 51.35%` | **实质条件·已证（纯计数）** | 仅 74 行 | §2.6 实跑；`:131` 自标「一致率低 ≠ 误差独立」 |
| S7 | `KEFF_CALC.md:262-269`；`METRIC_CONVENTION_AUDIT.md:109,185` | Fréchet `min q_i` 恰取等 | **实质条件·全称已证（数学定理）+ 实测取等** | 全称 + 仅 74 行 | §2.6 `q_i / min / equals min? True`；`{all3∩E}={n13P∩E}` 取等同样不必然 |
| S8 | `METRIC_CONVENTION_AUDIT.md:106-107,290`；`KEFF_CALC.md:311-340` | `P(r12=PASS\|n13=PASS)=38/38=1.000` | **实质条件·全称已构造性证伪** | 仅 74 行 | §2.2 `den 38 num 38`；§2.5 X1/X2/X3；`:315-326` 四种 95% 上界；`:290` 自标未验 |
| S9 | `CHAIN_VS_SINGLE.md:75,193`；`COMPARABILITY_AUDIT.md:154,166,181`；`GATE_PIPELINE_COMPOSE.md:407,410,428` | `unresolved 22→0` | **实质条件·已证（换代 + 口径变更）**，上游自判「空结论」 | 仅 74 行 | §4.2 第 5 处两版 JSON 实跑；`:250-254` `K7=0 K8=0` |
| S10 | `COMPARABILITY_AUDIT.md:158`；`_cmp_AUDIT_20261109.md:122` | `chain_changed=18 \| unresolved_changed=18 \| 集合恒等? True` | **实质条件·仅 N 行观测（逐 id 相等）** | 仅 74 行 | 本次会话实跑 `common=71 / 18 / 18 / sets equal? True / layer_conflicts changed=0`；措辞未升级为定理 |
| S11 | `_tp_C07_TRUTH_PROTOCOL.md:167`；`_tp_TP_VERIFIER_CHECKLIST.md:77`；`C07_TRUTH_SELF_PROOF.md:240` | 「无未验残留」 | **未验**（「通过」档判定条件，非事实） | 条件行 | 全树恰 3 命中全为条件行；`C07_TRUTH_SELF_PROOF.md:125`、`:261-267` 实读 6 条未验 |
| S12 | `SCORE_DECOMP.md:233-235`；`_sd_report.md:348-354` | S3 DEFAULT 恒真兜底、信息量 = 0 | **重言式（真恒真，类型不同）·正面样板** | 全称（代码定义） | 实读 `_v12_rule.py:167-170`、`EVIDENCE_INDEPENDENCE.md:169,173`、`_eind_verify_out.json:302 only_default=true`；本库唯一把恒真性正确标「零信息量」而非「定理」的落点 |
| S13 | `PVALUE_RECALC.md:197,250,251`；`_pv_PVALUE_RECALC.md:226-228` | post-selection `P(18/18\|入选失败集)≈1`、自信息 ≈0 bit | **实质条件·已证（post-selection 条件分布）** | 仅 74 行 | `PVALUE_RECALC.md:124` `gains=18 losses=0`；`:197` 明写「似然比不可识别…不得反推 p 仍稳健」；与 S5 不同论域 |
| S14 | `LAYER_IDENTITY.md:133-144,238-241,384`；前件 `:194,197,236,320,325` | 「只剩 1 个非 1 因子 / 不是两个自由度」 | **实质条件·仅一种因子化下的描述；作为自由度论据已证伪** | 仅 74 行 | §2.6 六排列 `prod 恒 1/13`、`non1=1/2/3`；`LAYER_IDENTITY.md:200` `distinct triples = 5 of 8` |
| S15 | `EVIDENCE_INDEPENDENCE.md:98,165`；`_cs_BASELINE_ALIGNMENT:203` | 55 行 `tokens` 与 `N13.DEFAULT_TOKENS` 完全相同 / 6/6 完全相同 | **实质条件·已证（逐字比对）** | 仅 74 行 | 实跑 `distinct token sets = 4`（55/17/1/1）、`NOT subset of T = 19`、`distinct label triples = 5 of 8` |
| S16 | 编排方上一轮三句旧措辞 | 「这是恒等不是近似」「两个自由度」「决定性集合等式」 | **须逐句撤回**（见 §6.2） | 口头措辞 | 本次会话实跑三句在两件台账 **0 命中**；`GOAL_THREE_TARGETS_20261018.md` 含 `恒等` 的行 46 行，逐行核属别论域；仅在 `metric_audit_20261109` / `layer_identity_20261109` 的引述、修正文字中出现 |

### 4.4 其它恒等类断言清单与汇总

- **真重言式**：`A⊆B`（S1 半、S3 `:125`）、S12 的恒真兜底（不同类型，且被正确标零信息量）。
- **实质条件·全称已证**：S2 `:104` 主句、S4 正确等价式、S7 Fréchet 取等（定理部分）。
- **实质条件·仅 N 行观测**：S6 一致率、S9 `22→0`、S10 集合恒等、S13 post-selection 0 bit、
  S14 六排列、S15 逐字相同 —— 其中 S7/S9/S10 的「取等 / 相等」同样可被 X1 类输入或换算法破，
  **不得升级为定理**。
- **全称已构造性证伪**：S1 的 `B⊆A` 半、S5「0 bit」全称、S8 `38/38` 全称。
- **未验**：S11「无未验残留」（是条件不是事实）、§6.5 所列未跑项。
- **等价性断言错误**：S3 `:146`「同一命题」—— `LAYER_IDENTITY.md:122-130` 已纠正。
- **同模式复发的共有根**：把「数值全对」当「有全称证明」；
  `METRIC_CONVENTION_AUDIT.md:108` 把实跑 `set equal? True` 直接接「决定性」标签，中间无范围声明。

---

## 5 危害分析

### 5.1 把重言式当定理会推出的**具体错误结论**（逐条给例）

| 误用 | 被包装的「定理」 | 推出的错误结论 | 本次会话的证伪 / 纠偏 |
|---|---|---|---|
| E1 | 「`A⊆B` 已证 ⇒ 恒等已证一半」 | 少列一个待证条件，报告只写「`B⊆A` 待查」；「决定性集合等式」看似有证明支撑 | §2.3 8 格全真、零信息量；`LAYER_IDENTITY.md:104,126` 已自标「重言式」 |
| E2 | 「`A=B` 是逻辑必然」 | 「R12 **恒** PASS / **不提供任何新信息**（全称）」⇒ 可安全删掉 R12 层 | §2.5 X1/X2/X3 三例 `r10=P r12=C n13=P` 直接反证；`KEFF_CALC.md:340`「不是恒等式」 |
| E3 | 「集合恒等 ⇒ 只有 2 个独立层 / 两个自由度」 | 按 2 层乘 `q_r10×q_n13 = 19/507 = 3.75%` 当联合漏报 | §2.6 `prod2 = 19/507`，但链式精确值 `1/13`，`chain/prod2 = 39/19 = 2.0526` 倍低估；六排列 `non1=1/2/3` 随顺序变 ⇒ **不能数自由度**；`LAYER_IDENTITY.md:197,200,261` 已判不合法 |
| E4 | 「`P(r12\|n13)=1 ⟺ A=B`」（同义改写误判） | 用 38/38 一个数字同时给「集合等式」「0 bit」「k_eff 的 `p2=p3`」背书，一处破则三处静默同破 | §2.4 分叉格 + C5 破 P 不破 `B⊆A`；`LAYER_IDENTITY.md:128,337` |
| E5 | 「三层连乘只是少乘一项的算术误差」 | 以为补一个因子 / 改 3 层为 2 层即可修正，保留 `Πq_i` 模型 | §2.6 `prod3 = 665/19773 = 0.033631720`、`chain/prod3 = `**`1521/665 = 2.287218045112782`**；根因是 **H1（给定 E 条件独立）已证伪**（`EVIDENCE_INDEPENDENCE.md:246-247,256` 明令不得用 `Πq_i`；`LAYER_IDENTITY.md:260`「这不是少乘/多乘一项的算术误差，是**模型假设错误**」） |
| E6 | 「`unresolved=0` ⇒ 裁决全部成功」 | 把空结论当通过证据，掩盖 K8 死分支与 3 条共同盲区不进 `conflicts[]` | `GATE_PIPELINE_COMPOSE.md:250-254,410` 自判「**空结论**」；`COMPARABILITY_AUDIT.md:166`；§4.2 两版 JSON 实跑 |
| E7 | 「`P(18/18\|入选失败集)≈1` ⇒ p 仍稳健 / 算法更好」 | 用 post-selection 的≈0 bit 自信息反推显著性 | `PVALUE_RECALC.md:197,251` 明写「似然比不可识别 / 禁止显著改善等措辞 / 真实 p 未验」 |

### 5.2 与「口径错置」是否同族；区分

**同族但不同层**。二者都是「把 A 类陈述当 B 类陈述用」的范畴错误，都会被「数值碰巧对上」掩盖：

| 维度 | 重言式包装成定理（本模式） | 口径错置（`METRIC_CONVENTION_AUDIT.md` 论域） |
|---|---|---|
| 错在哪 | **命题强度**：把恒真（零内容）或 N 行观测说成逻辑必然/全称定理 | **量的定义**：分子/分母/条件方向/事件类别被换掉 |
| 典型症状 | 「决定性」「恒等」「必相等」「不是近似」「两个自由度」 | `fp_rate=P(CATCH\|¬E)`（分母 35）被当 `q_i=P(PASS\|E)`（分母 39） |
| 数值 | 通常**是对的**（38/38=1、18=18、min=1/13 全对） | 通常也**碰巧接近**（3.75% vs 3.36%、2.05 vs 2.07 差 0.98%）⇒ 更难发现 |
| 判据 | forbidden set + 反证构造（§3.3） | 「分子分母的定义」，不是数值大小（`METRIC_CONVENTION_AUDIT.md:3,100`） |
| 破法 | 改一个契约前提、构造落进 forbidden 格的输入（X1） | 逐处写清分子/分母/条件类，禁止用边缘 `q_i` 顶替条件因子 |
| 本库判词 | `LAYER_IDENTITY.md:189`「74 行样本上成立 ≠ 逻辑上成立」 | `METRIC_CONVENTION_AUDIT.md:268`「不许用『口径不一致』概括」 |
| 交叉点 | E5 的三层连乘**同时**是两类错：既把条件因子 `1` 换成边缘 `q_i`（口径），又靠恒等把「少一层」说成结构性（强度） | `LAYER_IDENTITY.md:258-260` 逐字并列表述 |

**区分口诀**：*口径错置问「这个数的分子分母是什么」；重言式包装问「这句话在任何 input 下都真吗」。*
前者错了数会变，后者错了数不变、只是**你以为它有证明而它没有**。

### 5.3 ★ 为什么特别难发现（提示：它是对的，只是强度被夸大）

1. **它是对的**。`A⊆B` 在 8/8 真值格局上真、`18=18`、`38/38=1`、`min q_i=1/13=实测`
   全部通过任何数值复核（§2.2/§2.3/§2.6）。审查者查数、查指纹、查一致性都不会报错。
2. **错的是强度不是真值**。把「本 74 行观测」写成「决定性/恒等/定理」，字面仍与所有实跑输出
   相符；只有问「有没有一个 input 能破」才会暴露（§2.5）。
3. **名字唬人**：「决定性」「集合等式」「不是近似」「两个自由度」自带数学权威，读者默认
   它已附全称证明；`METRIC_CONVENTION_AUDIT.md:108` 甚至把实跑输出 `set equal? True`
   直接接到「决定性」标签上，中间没有「范围声明」。
4. **数值碰巧相等的掩护**：`3.75%` vs `3.36%`、`2.05` vs `2.07`、以及
   `1.000` 与 R12 真 LR=1 的「**精确相等**」—— 该词实读在
   `METRIC_CONVENTION_AUDIT.md:125,162`（另 `_ma_METRIC_AUDIT.md:211`）；
   **`METRIC_CONVENTION_AUDIT.md:211` 是 4.45 倍数表行，不含此词**（复核 ★3 已纠）。
   数值越漂亮越没人去查定义。
5. **重言半与实质半混在同一句**。一句「集合恒等」同时含 `A⊆B`（必真）与 `B⊆A`（偶然），
   前半的不可错性给后半背书（S1）。
6. **反例不在语料里**。本次会话实跑 `tokens NOT subset of T = 19`，破口在语料里真实存在；
   该 19 行中确有 3 行 `r12=CATCH`（`R10-TV3`、`R10-CTX-05`、`R10-CTX-06`），但实跑其
   `r12_scan` 命中的 token 均为 `已生效`（∈T），超集专有 `可应用母本`/`放行 N-5` **零命中**
   ⇒ 「这 19 行恰好没在超集 token 上命中双重否定」这句**准确**（复核已确认非缺口）。
   74 行上零违例，只有主动构造 X1 才见到。
7. **复核机制默认查「有没有跑过」而非「跑的结论属于哪一类」**。本库已有多处正确自限
   （`KEFF_CALC.md:314,340`、`METRIC_CONVENTION_AUDIT.md:290`、`GATE_PIPELINE_COMPOSE.md:410`），
   但措辞层与结论层可以长期并存不冲突。

### 5.4 报告里防止的机制（可实装清单）

1. **两段式等式声明（强制）**：任何 `A==B` 必须写成
   `A=B ⟺ [重言半：定义式 + 8 格穷举] ∧ [实质半：forbidden 格为空，依据=…/仅 N 行]`。
   范式见 `LAYER_IDENTITY.md:393` 第 5 条。
2. **破坏性输入随附**：每条恒等断言必须带一个「什么 input 会破」的构造或实跑输出
   （X1/X2/X3 形态），否则标**未验**。
3. **契约四元封印**：`(predicate_sha, tokens_sha, text_sha, eol)` 逐行登记，任一变化等式重算
   （`LAYER_IDENTITY.md:395`；`KEFF_CALC.md:283-285` 已有同款前置条款）。
4. **零命中给区间**：38 次零命中一律附单侧精确 / rule-of-three / Wilson 双侧 / 双侧精确
   四种 95% 上界 `7.6%–9.3%` 并分列口径（`KEFF_CALC.md:315-326`），禁止把 `1.000` 写成精确值。
5. **主结论与等式解耦**：「≤1 层 / 绝不按 3 层 / 不得自动放行」只挂依赖图 `file:line` +
   A1–A5 五检（`LAYER_IDENTITY.md:267-273`）；等式只作描述（`:393` 第 5 条）。
6. **负例哨兵**：`LAYER_IDENTITY.md:400` 的 8 个禁用串与
   `METRIC_CONVENTION_AUDIT.md:283` 的 4 个数禁用串列为生成时断言 ——
   **如实：两处均记「仍是提案、未实装」**，本任务不改脚本。
7. **类别 × 范围双标签**：每个结论强制带 `[类别]` 与 `[全称 / 仅 N 行 / 反事实 / 条件行 / 未验]`
   两个标签，禁止裸写「成立」（按复核 ★6 修正四值框架）。
8. **独立复核专问强度**：复核回件的 `whatBreaksIt` 固定要问「构造一个破它的输入」，
   而不是只复算数值（本轮【复核】正是这样抓到 X1 的，见 `LAYER_IDENTITY.md:112`）。

---

## 6 复核回件（绑定行格式）+ 结论 + 未验项

### 6.1 复核回件

#### 6.1.1 verdict 与绑定行（如实）

【复核】`verdict = "partial"`，`ranCommands = 43`；【审计】`ranCommands = 16`。
按【交付】「refuted 或 partial 标 unconfirmed」⇒ **本件记 `partial` / `unconfirmed`**，
不自行标 `confirmed`，不改动上游 verdict（`LAYER_IDENTITY.md:333-339,425` 同规则）。

【复核】`sha256Line` 所指被核对象 = 审计员交付件
`lead/tautology_audit_20261109/_ta_TAUTOLOGY_AUDIT_20261109.md`，本次会话 `hashlib` 现盘重算
（`python -I -X utf8 -c "<read_bytes + sha256 + len>"`）：

被核对象 SHA256 = 9029197bcca3cf3f21c3e73576002f00c3cdd96f35607b2fcdbfbf3c81174c53，字节数 = 53673

九件只读指纹与补测二件的严格格式绑定行见 §2.1（共 11 行），本次会话逐行
`^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$` 校验全 `True`。

**复核已独立复现通过的部分**（如实转录）：九件指纹首轮 + 收尾两次全等；集合拆解
（74 行 `A_n=18 B_n=18 / only_A=only_B=[]` / 八格表 / `den 38 num 38 ratio 1.0`）；
2³ 穷举 `A⊆B taut? True`、`F(B⊆A)=[(1,0,1)]`、`F(P) strict_superset? True`；
X1/X2/X3/C0/C5 用 `importlib` 只读加载自写判据复现；五处逐处判、C10/C11/C12/C13/C16
数值与文本全等复现；越界检查（写域仅 14 件 `_ta_*`、无 `_tav_*`、`git log -1 = 2657458`、
两处既有 pycache mtime 未变、九件只读指纹收尾全等）。

**复核确认的 6 处缺口**：见 §1.3 与 §6.1.2 逐条；本撰写件逐条修正，未替上游件改写。

#### 6.1.2 六处缺口的逐条修正（本件相对 `_ta_…md` 的改动登记）

| 复核缺口 | `_ta_…md` 原句 / 位置 | 本件修正 |
|---|---|---|
| ★1 替换不准 | §5.1 #1（`:402`）、§5.2 #1（`:413`）把 `METRIC_CONVENTION_AUDIT.md:104` 列入撤回对象，而 §3.2 S2（`:295`）判「`:104` 本身正确」；替换正文「由源码蕴含；X1/X2/X3 已构造性破之」自相冲突 | §6.2 #1 撤回对象改为**编排方三句旧措辞** + `METRIC_CONVENTION_AUDIT.md:108,272` + 前件 `:146`；**明确 §4.3 S2 判 `:104` 正确、不撤回**；把「由源码蕴含」限定为「`LAYER_IDENTITY.md:189` 的受限契约下条件性陈述」，并注明两条全称升级条件仍**未验**（`:339,421`），X1 破的是**不受限全称恒等**而非该受限蕴含 |
| ★2 清单自相矛盾 | §2.3 第 1 步（`:213`）`F(A⊆B) = B∧¬A`，与 `F(B⊆A)` 写成同一个集合 | §3.3 第 1 步改为 `F(A⊆B)=A∧¬B=∅`、`F(B⊆A)=B∧¬A`；§3.4 可粘贴片段同步（本次会话逐字实跑） |
| ★3 引用不准 | §4.3(c)4（`:365`）引 `METRIC_CONVENTION_AUDIT.md:211`「精确相等」 | §5.3 第 4 点改引 `:125,162`（另 `_ma_METRIC_AUDIT.md:211`），并注明 `:211` 是 4.45 倍数表行 |
| ★4 悬空引用 | §2.2（`:205`）「见 §3 #R7」，判定表编号实为 S1–S16 | §3.2「全集与子集」行改「见 §4.3 S12」 |
| ★5 判据外推 | §2.1 一句话（`:196-197`）作为「任一恒等」全称表述 | §3.1 附 N1–N4 别例实跑表，明确「本例可操作、已实跑；任意恒等皆适用属外推、**未验**」 |
| ★6 框架 / 笔误 | §3.2 四值「已证」混装「仅 N 行」与「全称」；`:126,167,297` 照抄 `r13` | §4.3 用「类别 × 范围」双标签；全件统一 `n13`，并注明上游 `LAYER_IDENTITY.md:376,393` 的 `r13` 系笔误 |

#### 6.1.3 编排方门禁自洽性（额外发现，如实）

复核指出：写域当时无 `TAUTOLOGY_AUDIT.md`（只有 `_ta_TAUTOLOGY_AUDIT_20261109.md`），
且门禁关键字「五处」在审计交付件中 0 命中 ⇒ 该件按其自身编排方门禁不会通过。
本件按【交付】命名落盘、含「五处」字面（§4.2 标题与多处），并在写完后实跑编排方
`GATE_CODE` 的等价内联版（六节 / 九要素 / 越权断言 / 绑定行 / 九件零漂移）复核，
结果见 §6.6。**注意**：门禁的「内容层面五步全部答复」与「门禁字面要件」是两回事，
本件两者分别满足。

### 6.2 ★ 三句措辞的**逐句替换**（不用「措辞需谨慎」概括）

三句旧措辞均出自编排方上一轮口头（【背景】与【任务】原文），本次会话实跑在两件台账 **0 命中**
（`PENDING_DECISIONS.md`、`GOAL_THREE_TARGETS_20261018.md` 逐句 `count = 0`）；
`GOAL` 含 `恒等` 的行 46 行经逐行核属别论域。**被撤回的是三个强度标签及其隐含的全称性 /
独立性推论；18=18、38/38=1、5/8 三个数值全部成立、不撤回。**

**#1 旧措辞「这是恒等不是近似」（及把 `METRIC_CONVENTION_AUDIT.md:108` 的
「决定性集合等式」当成结构性定理的读法）→ 准确替换：**

> 「本批 74 行上 `{r10&r12&n13 全 PASS}` 与 `{r10&n13 双 PASS}` 是同一个 18 个 id 的集合
> （`only_A=only_B=[]`），这是**观测等式，不是逻辑恒等式**。其 `A⊆B` 半是
> `A = B∩{r12=PASS}` 的**定义重言式、零信息量**；非平凡半 `B⊆A` 等价于
> `(r10=P, n13=P, r12=C)` 格为空，74 行上该格为 0，但 X1/X2/X3 已构造出落在该格的输入，
> 故**全称形式已被构造性证伪**。`LAYER_IDENTITY.md:189` 记「恒等只在『同一 tokens / LF 对齐 /
> 命中 token ∈ T』的受限契约下由源码蕴含」，属**受限契约下的条件性陈述**；两条全称升级条件
> （`(r10=C,n13=P,r12=C)` 任何输入不可达、X1/X2/X3 类输入在生产契约下全部不可达）
> 仍标**未验**（`LAYER_IDENTITY.md:339,421`）。」

**★ 不撤回项**：`METRIC_CONVENTION_AUDIT.md:104` 原文
「根因**不是**『R12 数值接近 1 所以近似省一层』，而是 **R12 不是独立证据根**」——
这是**正确的否定句**（实读 `:104`；§4.3 S2 判「本身正确」），依赖图
`EVIDENCE_INDEPENDENCE.md:301`、`:111` 支撑，**不得列入撤回对象**（复核 ★1）。
真正须改的是同件 `:108` 的「决定性集合等式」标签、`:272` 的「必附独立性依据」，
以及前件 `:146` 的等价性断言（改列 `A=B ⟺ P(r12|r10&n13)=1`，`LAYER_IDENTITY.md:376`）。

**#2 旧措辞「两个自由度」（及前件 `:236`「不是两个自由度，而是只有一个非 1 因子」）→ 准确替换：**

> 「全 74 行的 `(r10,r12,n13)` 标签三元组有 **5/8 种**可观测组合，只能作**描述**；
> 这是标签自由度，不是可用独立因子数。链式法则 6 种因子化乘积恒 `1/13`，
> 非 1 因子数 **1/2/3 随顺序变**（本次会话 `fractions.Fraction` 实跑），不能据此数自由度或独立层数。
> 结构性答案只有依赖图 `R10→{R12,N13.C}`（`EVIDENCE_INDEPENDENCE.md:301`、
> `_g7_predicates.py:144-145`、`:111` 五检）给出的「可用独立因子 ≤1（根=1）」。」

**#3 旧措辞「决定性集合等式」（及 `METRIC_CONVENTION_AUDIT.md:272` 把它列为
「必附独立性依据」）→ 准确替换：**

> 「**本 74 行观测等式**（18 个 id 逐一对齐、`only_A=only_B=[]`），`A=B` 的正确等价式是
> `P(r12=PASS | r10=PASS & n13=PASS)=1`；`P(r12=PASS|n13=PASS)=38/38=1` 是**更强**的观测，
> 还额外要求 `(r10=C,n13=P,r12=C)` 格为空，该格为 0 **也是巧合**（`LAYER_IDENTITY.md:87,128`）。
> 独立性依据改列代码级依赖图 `file:line`（`_g7_predicates.py:144-145`、
> `_ei_n13_predicates_src.py:199-202,241-245,253-256`、`_gp_pipeline.py:80-81`），
> **不把集合等式列为必附条件**；集合等式只作描述（`LAYER_IDENTITY.md:393` 第 5 条）。」

### 6.3 哪些结论要改、哪些反而更稳

**要改（降级 / 改措辞，均不改数值；本任务只读，未执行改写）**：

1. `METRIC_CONVENTION_AUDIT.md:108,272`（「决定性集合等式 / 必附独立性依据」）
   → 「本 74 行观测等式」+ 依赖图 `file:line`（`LAYER_IDENTITY.md:376` 第 1 项）。
   **`:104` 不改**（正确否定句，复核 ★1）。
2. `EVIDENCE_INDEPENDENCE.md:149,294,302`、`CHAIN_VS_SINGLE.md:204,206`、
   `_cs_BASELINE_ALIGNMENT_20261109.md:226,334`、`KEFF_CALC.md:432,434,440` 的
   「R12 增量 0 bit / 1.000 / 不提供任何新信息」→ 「本 74 行观测」+ 四种 95% 上界 + 破口
   （`LAYER_IDENTITY.md:377-378` 第 2/3 项）。
3. 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146`「`B⊆A ⟺ P(r12|n13)=1` 是同一命题」
   → **删除**，改正确等价式 `A=B ⟺ P(r12|r10&n13)=1`（`LAYER_IDENTITY.md:376`）。
4. 前件 `:110,194,197,236,320,325`「只剩 1 个非 1 因子 / 不是两个自由度」
   → 「在 `n13` 优先因子化下两个条件因子为 1；非 1 因子数 1/2/3 随顺序变，乘积恒 `1/13`」
   （`LAYER_IDENTITY.md:384` 第 9 项）。
5. `EVIDENCE_INDEPENDENCE.md:299-306` 六条理由 → `:301` 依赖图 + `:111` 五检为**结构性**、
   `:302/:303/:304/:305/:306` 为**本 74 行统计佐证**（`LAYER_IDENTITY.md:385` 第 10 项）。
6. `p2=p3`、k_eff 三口径 `0.606/0.670/0.804`、`0.61 层`、`≈1～1.3 层（乐观 1.5）`
   → 标「描述性、本批语料偶然量、不可用于放行」，禁作层数计数
   （`LAYER_IDENTITY.md:213,221-225,304,306`、`KEFF_CALC.md:418-419,436-443`）。
7. `q_r10×q_n13 = 19/507` 与 `q_r10×q_r12×q_n13 = 665/19773` → 标「反事实基线期望 /
   仅『若真有 3 独立层』的算式」；精确值走链式 `1/13×1×1`、上界走 Fréchet `min_i q_i`
   （`LAYER_IDENTITY.md:246-263`；§2.6 复现 `1521/665 = 2.287218045112782`）。

**反而更稳（不受影响，且不能再被误读）**：

- **「按 ≤1 层计、绝不可按 3 层、三层全 PASS 不得自动放行」** —— 靠代码级依赖图
  `R10→{R12,N13.C}`（`EVIDENCE_INDEPENDENCE.md:301`、`LAYER_IDENTITY.md:166,269-273`）与
  A1–A5 五检（`:111`「没有任何一对能同时过 5 检」），**不靠 38/38**
  （`LAYER_IDENTITY.md:214,228,233,273`）。
- **「独立证据根 = 1」「numeric=1 是保守取整约定非测量值」「R9/R11 正交」**
  （`KEFF_CALC.md:165-167,236`；`EVIDENCE_INDEPENDENCE.md:296`）。
- **「不得用 `Πq_i`、H1 已证伪、真上界是 Fréchet `min_i q_i`」**
  （`EVIDENCE_INDEPENDENCE.md:246-247,252,256`；§2.6 复现）。
- **「3 个判据 / 1 个独立证据根」「18 行里 3 行真断言（GP-A1/A2/A3）⇒ 禁止自动放行」**
  （`KEFF_CALC.md:287-288,301-302`；§2.2 八格表）。
- **「72 与 74 不可比」** —— 三轴同变 + E 轴脚本未留盘（`CHAIN_VS_SINGLE.md:76`、
  `_cs_BASELINE_ALIGNMENT_20261109.md:125`；§4.2 两版 JSON 实跑）。恒等偶然性只**再加一条**
  「不能把集合相等读成结构结论」的理由，不动可比性判词。

### 6.4 以后写恒等类断言的准则（10 条）

1. **先拆两半**：`A=B` = `A⊆B` ∧ `B⊆A`，逐半标「类别 × 范围」双标签（§4.3）。
2. **展开定义**：写明 `A = B ∧ C` 的 `C`；能只靠逻辑证的一半立即标「重言、零信息量」，不计入证明。
3. **写 forbidden 格**：非平凡方向的否定条件逐格列出，并给「使它为空」的 `file:line` 或实跑命令。
4. **枚举全部原子格局**：2^n 全跑，打印每格等式真值与被声称等价命题的真值，比对 forbidden sets。
5. **构造反例**：改一项契约前提（词表 / 换行 / 位置口径），跑谓词直调；构造失败才考虑标定理。
6. **写范围四元**：`N / 数据源 SHA256+字节数 / predicate_sha+tokens_sha+text_sha+eol / train=test`。
7. **零命中给区间**：单侧精确、rule-of-three、Wilson 双侧、双侧精确四种 95% 上界分列，
   禁止把 `1.000` 当精确值。
8. **禁止「决定性/恒等/必相等/恒真/恒成立」裸用**：这些词只能跟在「本 N 行观测」或
   「在以下契约下的受限定理」之后，且必须附破坏构造。
9. **主结论不挂等式**：独立性/层数结论只挂依赖图 + 五检；等式只作描述，不作「必附依据」。
10. **同义改写要证**：说「X 与 Y 是同一命题」必须先比对两者 forbidden sets 逐格相同
    （§2.4 的 `False` 就是反例）；否则只写「在 N 行上同真」。

与 `LAYER_IDENTITY.md:387-400` 的 12 条「报层数准则」互补：那 12 条管**量纲**，
本 10 条管**命题强度**；二者须同时执行。

### 6.5 判不了什么 / 未验项（如实，不补造）

- **真机运行态**：铁律零真机 ⇒ `gamemd.exe`/`ra2loader`/`YURI.exe`、活进程内存一律 **未验**。
- **生产语料泛化**：74 行 train=test 且含定向对抗样本；`q_i / c_i / ρ / k_eff` 的泛化、
  X1/X2/X3 在生产语料的可达性 ⇒ **未验**（`LAYER_IDENTITY.md:414`）。X1/X2/X3 是**构造输入**不是生产观测。
- **X3（CRLF 位置错位）在生产链的可达性**：`LAYER_IDENTITY.md:186` 记 `read_text` 归一
  CRLF→LF、9 件读盘真件 `CRLF=0`；是否存在内联/直接文本入口 ⇒ **未验**；本次撰写会话未重跑该项。
- **两条全称升级条件**：① 代码级证明「`(r10=C,n13=P,r12=C)` 任何输入不可达」；
  ② 证明 X1/X2/X3 类输入在生产契约下全部不可达 —— 本次会话**未做**，故不把
  「恒等不是逻辑必然」升格为「在给定生产契约下是定理」（`LAYER_IDENTITY.md:339,421`）。
- **加入 X1/X2 后整体统计量变化**：未重跑 `_gp_regression.py` 全 74+2 行、未重算
  `q_i` / k_eff / CI；铁律不改语料/产物 ⇒ **未验**（`LAYER_IDENTITY.md:416`）。
- **k_eff 点值与 bootstrap 区间本次会话重算**：只引用 `KEFF_CALC.md:139-147,191-200`，
  **未重跑** ⇒ **未验**（`LAYER_IDENTITY.md:306,422`）。
- **`_gp_regression_out.json` 的生成过程归属**：本次会话以现盘 SHA `d3543657…` 重算全等，
  但**未重跑**生成脚本 `_gp_regression.py`（只读）⇒ 生成过程 **未验**（`LAYER_IDENTITY.md:423`）。
- **72 版 `48/72` 生成脚本**：`CHAIN_VS_SINGLE.md:76`、
  `_cs_BASELINE_ALIGNMENT_20261109.md:125` 记「脚本未留盘、未重跑」；本次会话只读两版 JSON
  ⇒ **未验重跑**（§4.2 只核 JSON 内部自洽）。
- **两件台账其它论域的「独立证据」措辞**：本次会话只核三句旧措辞 + 强模式命中数，
  **未全仓逐行人工通读** ⇒ **未验**（`METRIC_CONVENTION_AUDIT.md:295` 同判）。
- **负例哨兵机检是否实装**：`LAYER_IDENTITY.md:400`、`METRIC_CONVENTION_AUDIT.md:283`
  均自记「仍是提案、未实装」⇒ 本任务**未实装**，只给可粘贴清单（§3.4）。
- **判据在其它领域的适用性**：§3.1 的 N3/N4 别例已实跑显示一句话判据**不**全称适用；
  「任意恒等皆可用」⇒ **未验**。
- **本件自身 verdict**：未请求第三方复核，不自行标 `confirmed`；上游【复核】`partial`
  按规则标 **`unconfirmed`**（§6.1.1），本件不改动该 verdict。

### 6.6 纪律核验（本次撰写会话实跑）

| 核验 | 实跑命令 / 输出 |
|---|---|
| 九件只读指纹 | `python -I -X utf8 -c "<9 件 read_bytes + sha256 + len + 对照基线>"` → `ALL_9_MATCH = True`；收尾 `READ_ONLY_9_FINAL_MATCH = True` |
| 两件谓词源码 SHA | `python -I -X utf8 -c "<hashlib>"` → `02c17e49…/11743`、`e1195b3b…/16649` 全等 `LAYER_IDENTITY.md:359-360` |
| 被核交付件 | `python -I -X utf8 -c "<read_bytes + sha256 + len>"` → `9029197b…` / `53673` B（§6.1.1） |
| 拆解 / 八格 / forbidden | §2.2 / §2.4 内联实跑 → `n=74 A_n=B_n=18`、`A⊆B taut over all 8? True`、`forbidden sets equal? False` |
| X1/X2/X3/C0/C5 | §2.5 `importlib` 只读加载（`sys.dont_write_bytecode=True`）→ 五例输出逐字登记 |
| 数值复现 | §2.6 → `1521/665 = 2.287218045112782`、`prod 恒 1/13`、`non1=1/2/3` |
| 门禁自洽 | `python -I -X utf8 -c "<GATE_CODE 等价内联：六节 / 九要素 / 越权断言 / 绑定行 / 九件零漂移>"` → 见下方实跑输出 |
| 写域 / commit | `ls lead/tautology_audit_20261109/` → 14 件 `_ta_*` + 本件；`git log -1 --oneline` → `2657458`（未变） |

门禁等价内联版**第一次**实跑输出（写完本件后运行，逐字；命令为
`python -I -X utf8 -c "<GATE_CODE 等价内联：六节 / 九要素 / 禁用串 / 绑定行 / 九件零漂移>"`）：

```
{"ok": false, "problems": ["含越权断言 ×3"], "bindings": 12, "docBytes": 62229, "drift": 0}
六节 = 6 /6
九要素命中 = [('重言式', True), ('实质条件', True), ('X1', True), ('1521', True), ('H1', True), ('五处', True), ('强度', True), ('逐句', True), ('未验', True)]
绑定行数 = 12
```

**如实**：第一次**未通过**。原因不是内容越权，而是本件 §6.6 当时把门禁的三个**禁用串本身**
逐字写进了「输出示例」那一行，被门禁的子串检查命中（本次会话实跑定位：三个串只出现在该一行；
为避免再次自触发，此处不复述这三个串的字面）。这正说明门禁查的是**字面**而非语义。
修正方式：把该行改为不含禁用串的客观描述（「三个禁用串 = 0 命中」，见下），不改动上文任何结论。

门禁等价内联版**修正后**实跑输出（第二次，逐字）：

```
{"ok": true, "problems": [], "bindings": 12, "docBytes": 63401, "drift": 0}
六节 = 6 /6
九要素命中 = [('重言式', True), ('实质条件', True), ('X1', True), ('1521', True), ('H1', True), ('五处', True), ('强度', True), ('逐句', True), ('未验', True)]
禁用串 = 0 命中
绑定行数 = 12
九件只读指纹漂移 = 0
GATE_OK = True
```

> 说明：这两次实跑是**编排方 `GATE_CODE` 的等价内联复刻**（`python -I -X utf8 -c` + 绝对路径），
> 不是 workflow 自身的 `world-read#3` 那一次；后者由编排方在门禁阶段执行，本撰写会话不代为断言其结果。
> 审计员交付件 `_ta_TAUTOLOGY_AUDIT_20261109.md` 因未按 `TAUTOLOGY_AUDIT.md` 命名、且「五处」0 命中，
> 按其自身编排方门禁**不会通过**（复核额外发现）；本件按【交付】命名并补齐字面要件。

**最终纪律结论**：零真机、零采样代码、绝对只读、只做模式审计、**未改任何脚本 / 语料 / 产物 / 台账**、
不 commit / 不 push；唯一写入 = 本交付件 `lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md`。
所有「实跑」均为本次撰写会话内执行的命令，所有「文件:行」均为本次会话内 Read / Python 逐行读取；
未跑项一律标**未验**，未把任何未验写成通过。

---

*本件结束。复核 verdict = `partial` → `unconfirmed`（如实）。*

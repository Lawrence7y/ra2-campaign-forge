# _ta_TAUTOLOGY_AUDIT_20261109.md — 「重言式包装成定理」模式审计

> 唯一写域 = `lead/tautology_audit_20261109/`，本件与全部 `_ta_*` 中间产物均落此域。
> 绝对只读：`lead/layer_identity_20261109/`、`lead/metric_audit_20261109/`、`lead/keff_calc_20261109/`、
> `lead/evidence_indep_20261109/`、`lead/gate_pipeline_20261109/`、`lead/score_decomp_20261109/`、
> `lead/pvalue_recalc_20261109/`、`lead/advset_indep_20261109/`、两件台账 —— 未改、未追加、未覆盖。
> 零真机（未启 `gamemd.exe`/`ra2loader`/`YURI.exe`、未 `taskkill`、未读活进程内存）。
> 零采样代码（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析）。
> 不 commit、不 push（`git log -1 --oneline` = `2657458`，本次会话实跑未变）。
> Python 一律 `python -I -X utf8 -c` + 绝对路径；指纹一律 `hashlib.sha256` 现盘重算。
> 引用只追「本次会话实跑命令 + 输出」或「文件:行」；拿不到的一律写**未验**，不补造。
> ★ 只做模式审计，**不改任何脚本、语料、产物**。

---

## 0 复核回件绑定行（★ 固定格式）

> 编排方【编排方实跑指纹】九件，本次会话 `hashlib.sha256` 现盘重算逐行全等（`ALL_9_MATCH = True`，
> 实跑命令见 §7 命令 C1；收尾二次重算亦 `ALL_9_MATCH = True`，见 C14）。

被核对象 SHA256 = 13453a000c61cb211c51931cc8a7bd3d1912a9e1714d46cb8be349686fe9c957，字节数 = 47501
被核对象 SHA256 = ef6e4cc8a01219e8d0c052061623a7993eaa298f20b04ec95c009bb527f950b3，字节数 = 59941
被核对象 SHA256 = f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503，字节数 = 45362
被核对象 SHA256 = 4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16，字节数 = 34964
被核对象 SHA256 = aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523，字节数 = 36194
被核对象 SHA256 = d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe，字节数 = 38575
被核对象 SHA256 = dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb，字节数 = 42573
被核对象 SHA256 = 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7，字节数 = 52419
被核对象 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede，字节数 = 759518

补测（只读谓词源码二件，本次会话实算，供 §1(d) 反例引据绑定；两值全等 `LAYER_IDENTITY.md:46,359-360` 所记）：

被核对象 SHA256 = 02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120，字节数 = 11743
被核对象 SHA256 = e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079，字节数 = 16649

---

## 1 第一步 复核拆解（独立核对编排方实跑）

### 1.1 (a) A 与 B 的大小、两个包含方向

本次会话实跑（命令 C2，数据源 `lead/gate_pipeline_20261109/_gp_regression_out.json:rows`，74 行）：

```
n = 74
A_n = 18 B_n = 18
A_subset_B = True B_subset_A = True sets_equal = True
only_A = [] only_B = []
A_eq_B_inter_r12P ? True
```

八格列联表（同一实跑）：

| r10 | r12 | n13 | 计数 |
|---|---|---|---|
| PASS | PASS | PASS | 18 |
| PASS | PASS | CATCH | 12 |
| PASS | CATCH | PASS | **0** |
| PASS | CATCH | CATCH | 4 |
| CATCH | PASS | PASS | 20 |
| CATCH | PASS | CATCH | 20 |
| CATCH | CATCH | PASS | **0** |
| CATCH | CATCH | CATCH | 0 |

- `P(r12=PASS|n13=PASS)`：`den = 38`、`num = 38`、`ratio = 1.0`、`n13P_r12C ids = []`（C2）。
- `B_not_A_rows = []`（C2）⇒ 74 行上 `B⊆A` 成立。
- `r12=CATCH ids = ['R10-TV3', 'R10-CTX-05', 'R10-CTX-06', 'GP-C04']`（C2），与编排方
  `r12catch_r10pass` 四项、与 `LAYER_IDENTITY.md:97-100` 四行 id 全等。
- `LAYER_IDENTITY.md:49-52` 记同一实跑 `A_n 18 B_n 18 A==B True only_A [] only_B []`；
  `LAYER_IDENTITY.md:82-86` 记 `den 38 num 38 ratio 1` 与四格列联表；本次会话全等复现。

**判定**：编排方【集合包含两半的拆解】的 `n=74 / A_n=18 / B_n=18 / A_subset_B=true /
B_subset_A=true / sets_equal=true / n13pass_r12catch=[] / r12catch_r10pass=[4 ids]` 全部成立。

### 1.2 (b) ★ `A⊆B` 为什么是重言式 —— 看 A 的定义

定义（`LAYER_IDENTITY.md:125`、`:104`；前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:125`）：

```
A = { r10=PASS & r12=PASS & n13=PASS }
B = { r10=PASS          & n13=PASS }
```

即 **`A = B ∩ {r12=PASS}`，等价于「A 就是 B 再加一个合取项」**（编排方背景逐字：
「`note_A_is_B_plus_r12`: true」）。由合取消去 `X∧Y ⇒ X` 直接得 `A⊆B`，不需要任何语料、
不需要任何代码事实、不需要 74 行、不需要 `tokens`/换行契约。本次会话 C3 在 8 种真值格局上
穷举：`A⊆B is tautology ... check all 8: True`。

**强度结论**：`A=B` 需两个方向；`A⊆B` 这一半是**定义使然、恒真、零信息量**，
把它写成「决定性集合等式」的一半证明，是强度夸大（§2、§4）。前件
`_li_LAYER_IDENTITY_PROOF_20261109.md:125` 自己已写「`A ⊆ B` 是**去掉一个合取项的逻辑重言式**」，
`LAYER_IDENTITY.md:104`、`:126` 同判 —— 本库已有正确先验，问题是**措辞层仍用「决定性」包装**。

### 1.3 (c) 破坏 `B⊆A` 需要什么条件；74 行上有没有

由 C3 的 8 种真值格局：

```
B⊆A fails exactly when (r10=PASS, r12=CATCH, n13=PASS) row exists
```

C3 打印的 8 行中，唯一 `breaks B⊆A? = True` 的是 `PASS CATCH PASS` 一行
（该行 `inA=False inB=True`、`A==B? False`）。等价写法（C3/C4 + `LAYER_IDENTITY.md:126-128`）：

```
A = B  ⟺  不存在格 (r10=P & n13=P & r12=C)
      ⟺  P(r12=PASS | r10=PASS & n13=PASS) = 1
```

74 行上该格计数 = **0**（C2 八格表第 3 行 `PASS/CATCH/PASS : 0`；C2 `B_not_A_rows = []`），
故 `B⊆A` 在 74 行上**成立但只是观测事实**。它逻辑上不必然：C6 已实跑构造出恰好落在该格的输入
（X1/X2/X3 均 `r10=PASS r12=CATCH n13=PASS`）。

**★ 与条件概率的精确关系（不可混）**：`P(r12=PASS|n13=PASS)=1` 还额外要求
`(r10=CATCH & n13=PASS & r12=CATCH)` 格为空。C3 第 7 行 `CATCH CATCH PASS` 显示：
该行 `A==B? True`（`B⊆A` 未破）但 `P(r12P|n13P)=1? False`。本次会话 C5 实跑该反例：

```
text = '已入账 grep 结果。不得不承认放行 N-5'
r10,r12,n13 = CATCH CATCH PASS
inB = False inA = False B_subset_A_violated = False
n13=PASS & r12=CATCH ? True => breaks P(r12P|n13P)=1 but NOT B-subset-A
```

⇒ **「`B⊆A ⟺ P(r12|n13)=1` 是同一命题」不成立**；正确等价式只到
`P(r12|r10&r13)=1`。此点 `LAYER_IDENTITY.md:122-130,240,365,376` 已列为「修正①」，
前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146` 仍写「同一个命题的两写法」（该句须撤回）。
**本任务不改写该件**（绝对只读），只登记模式。

### 1.4 (d) ★ X1 反例能否复现；它为什么同时破两个命题

本次会话 C4、C6 直接 `importlib` 只读加载 `_g7_predicates.py` 与 `_ei_n13_predicates_src.py`，
复刻 `_liv_verify.py:44-51` 的 `judge`（源码 SHA 见 §0 补测二行，未改）：

```
T = ['已入账', '已追加', '已生效']
BAD_BAN = ['已生效','可应用母本','放行 N-5','已入账','已追加']
text = '不得不承认放行 N-5'
X1 r10 = PASS r12 = CATCH n13 = PASS
X1 inB = True inA = False => A!=B ? True
X1 n13=PASS & r12=CATCH ? True
r12_scan(BAD_BAN) raw hits = ['越权断言 放行 N-5（R12：回看窗含双重否定构式=肯定）']
r12_scan(T) raw hits = []
N13 T tokens present in text = []
```

C6 另复现 `X2 ('PASS','CATCH','PASS')`、`X3 ('PASS','CATCH','PASS')`，
对照 `C0 control ('PASS','CATCH','CATCH')`。与 `_liv_verify.py:70-79`、
`LAYER_IDENTITY.md:176-182` 三行表全等。

**机制（源码级，`LAYER_IDENTITY.md:163,184`）**：`_gp_regression.py:141` 让 R12 单层用**该行
`tokens`**（X1 用 BAD_BAN 五词），`:143` 让 N13 单层**恒用固定三词 `T`**；
`_ei_n13_predicates_src.py:200` 内部回调 `r12_scan(text, list(tokens))` 也用自身 `T`。
X1 的命中 token `放行 N-5` ∈ BAD_BAN、∉ T ⇒ N13 内部的 `r12_pos` 为空 ⇒
`:241-245` 的「R12 命中无条件提升为 D」不触发 ⇒ `r13_assertions` 返回空 `problems` ⇒
`n13=PASS`（C4 实跑 `N13 T tokens present in text = []`）。

**为什么同时破两个命题**：X1 落在 `(r10=PASS, n13=PASS, r12=CATCH)` 格 ——

1. 该行 `∈B`（`r10=P ∧ n13=P`）且 `∉A`（`r12=C`）⇒ `B⊆A` 破 ⇒ `A≠B` ⇒ **集合恒等破**；
2. 该行 `n13=PASS ∧ r12=CATCH` ⇒ `P(r12=PASS|n13=PASS)` 分子 < 分母 ⇒ **条件概率 1 破**。

但这两件事**不是同一个命题**（§1.3 的 C5 反例破 P 不破 `B⊆A`）。X1 因恰好
`r10=PASS` 而同时落在两个 forbidden 格的交里，才「同时破」；编排方背景的
「集合恒等把条件概率的全部偶然性原样继承」这一**直觉**成立，但「二者是同一命题」这一**等价断言**
不成立。准确说法：恒等的**全部非重言内容**只有 `B⊆A` 这一半，而它是与
`P(r12|r10&r13)=1` 等价的实质条件；`P(r12|n13)=1` 是**更强**的实质条件（多排除一格），
二者在 74 行上同真靠 `cells_r10C_n13P_r12C = 0` 这**第二处巧合**（C2 八格表第 7 行 = 0；
`LAYER_IDENTITY.md:87,128` 同判）。

**结论**：X1 可复现；它证明「恒等不是逻辑必然」，并证明「把 `A⊆B` 的重言一半当定理」
不能给「2 个独立层」提供任何支持。主结论「按 ≤1 层计、绝不可按 3 层、不得自动放行」
靠代码级依赖图 `R10→{R12,N13.C}`（`LAYER_IDENTITY.md:166,269-273`、
`EVIDENCE_INDEPENDENCE.md:301`、`:111` 五检），不靠 38/38。

---

## 2 第二步 「重言式 vs 实质条件」的判据（本任务核心）

### 2.1 (a) ★ 可操作判据（五问，逐问必须能落 `file:line` 或实跑输出）

给定任一形如 `A = B` / `A ≡ B` / 「恒等 / 决定性 / 必相等 / 恒真 / 恒成立」的断言：

1. **拆两半**：`A=B` 一律拆成 `A⊆B` 与 `B⊆A`。逐半判，**禁止合并报「等式成立」**。
2. **展开定义**：把 A、B 都写成原子谓词的合取/析取；若 `A = B ∧ C`（或 `B = A ∨ …`），
   则 `A⊆B` 立即是合取消去重言式，**零证据量**；把它从「证明」里划掉。
3. **找禁止格**：非平凡方向 `B⊆A` 的否定是「存在一行满足 `B ∧ ¬A`」。写出这个格的最小充分条件
   （本例 `(r10=P, n13=P, r12=C)`），并给出「哪一行代码/哪一份语料使它为空」。
4. **判来源**：使禁止格为空的依据是 (i) 纯逻辑/定义（⇒ 重言式），
   (ii) 代码级不变量（⇒ 实质条件·已证，须给 `file:line` + 全称证明），
   (iii) 本批语料统计（⇒ 实质条件·未证/仅在 N 行上成立，须给 N、SHA、CI），
   (iv) 什么都没有（⇒ 未验）。
5. **反证**：尝试构造一行破坏它（§2.3）。构造成功 ⇒ 该半是**实质条件且已被证伪为定理**；
   构造失败且能给出全称论证 ⇒ 才可能是定理。

**一句话判据**：*把等号两边的定义展开后，若其中一半能在不读任何数据、不读任何代码的情况下
只靠逻辑连接词就证明，那一半是重言式；等式的信息量全部在另一半，且在另一半上。*

### 2.2 (b) 五类重言式的识别特征与处置

| 类型 | 识别特征 | 快速检验 | 本库对应实例 | 判定 |
|---|---|---|---|---|
| **定义使然** | 被比较的一方就是另一方的定义/展开 | 把定义代回，等式退化为 `X=X` | `A = B∩{r12=P}` ⇒ `A⊆B`（§1.2）；`LAYER_IDENTITY.md:104,126` | 重言式 |
| **合取项冗余** | 一侧比另一侧多一个合取项，且该项在论域内恒真 | 令该项为 False，看是否有一行分叉 | 「R12 在两根已全 PASS 的行上**恒 PASS**」`METRIC_CONVENTION_AUDIT.md:108` —— 在 74 行上成立，但 X1 里 `r12=CATCH` 与 `r10=n13=PASS` 共存 ⇒ 非恒真、是观测 | 实质条件（已证伪为定理） |
| **全集与子集** | `A⊆U` 或 `U∩A = A`，U 由枚举范围定义 | 检查 U 是否恰为「所有可能取值」 | C3 的 8 种真值格局是全集，`A⊆B` 在全部 8 格上真 ⇒ 真重言；`SCORE_DECOMP.md:235` 的「S3 DEFAULT 恒 CATCH 兜底」对**正类样本**必然命中，是**恒真兜底**而非恒等式（另类，见 §3 #R7） | 重言式 / 恒真兜底 |
| **同义改写** | 两边是同一命题的措辞变体（换符号、换条件方向但不换事件） | 写出两边的 forbidden set，比对是否逐格相同 | 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146` 把 `B⊆A` 与 `P(r12\|n13)=1` 说成「同一个命题的两写法」—— C3/C5 证 **forbidden sets 不同**（一个排除 `(r10=P,n13=P,r12=C)`，另一个还排除 `(r10=C,n13=P,r12=C)`）⇒ **不是同义改写，是错置** | 非重言；**等价性断言已证伪** |
| **循环定义** | 结论已被写进前提（用 B 定义 A 再证 A=B） | 检查定义链是否成环、是否引入了待证性质 | 「R12 是 R10 `double_neg` 的确定性子集」（`_g7_predicates.py:134-148`）本身是**代码级定义**，可证；但若拿它当「R12 不独立」的独立论据，则与依赖图是同一事实的两种说法，不构成额外证据（`LAYER_IDENTITY.md:160,166`） | 定义性陈述（可作前提，不可当独立佐证） |

### 2.3 (c) ★ 「若把它当实质条件会推出什么」—— 反证法检查表

对每一半包含关系，按以下顺序做，**任何一步给出「破」即停止并降级**：

1. 写 forbidden set：`F(A⊆B) = B∧¬A`，`F(B⊆A) = B∧¬A`（注意方向别写反）。
   本例 `F(B⊆A) = {(r10=P,n13=P,r12=C)}`，`F(P(r12|n13)=1) = {(n13=P,r12=C)}`，
   后者 ⊋ 前者。
2. **枚举全部原子格局**（本例 2³=8，C3 实跑），打印每格上「等式真? / 条件概率真? / 破哪半?」。
   只要存在一格使二者分叉，就证伪「同一命题」。C3 输出：
   `CATCH CATCH PASS | inA False | inB False | A==B? True | P(r12P|n13P)=1? False | breaks B⊆A? False`
   ⇒ 分叉格存在 ⇒ `forbidden sets equal (theorems)? False`（`LAYER_IDENTITY.md:130` 同判）。
3. **构造真实输入**（不是纸面真值表）：改一个契约前提，跑谓词直调，看是否落进 forbidden 格。
   C4/C6 的 X1/X2/X3 三例全部 `r10=PASS r12=CATCH n13=PASS`，落进 `F(B⊆A)`。
   构造路径有两条可复现：
   - 词表契约分叉：`_gp_regression.py:141` vs `:143`（X1/X2）；本次 C12 实跑 74 行
     `tokens NOT subset of T = 19`、`distinct token sets = 4`，破口在语料里真实存在。
   - 换行/位置错位：`_gp_pipeline.py:60-70` 自认 CRLF 下 gpos 与 pos 相差行号数（X3）。
4. **推出后果**：若误把 `A⊆B` 当实质条件，会以为「等式已被证明一半、只剩一半待证」，
   从而在报告里少列一个待证条件；若误把 `A=B` 当定理，会进一步推出
   「R12 不提供任何新信息（全称）」「可用独立因子 = 2」「三层连乘可改写两层」，
   三者分别被 X1、C10、C11 证伪（§4(a)）。
5. **写进报告的强制格式**：`A=B ⟺ [重言半：定义式] ∧ [实质半：禁止格为空，依据=…/仅 N 行]`，
   并附「破坏它的输入」（`LAYER_IDENTITY.md:393` 第 5 条已是此格式）。

### 2.4 (d) 可粘贴的实现 / 检查清单

**可粘贴 Python（本次会话 C3/C4 所用形态，`python -I -X utf8 -c`，零写入、只读加载）**：

```python
import itertools
# 1) 8 格真值表：自动判「哪一半是重言、哪一格分叉」
for r10, r12, n13 in itertools.product(['PASS','CATCH'], repeat=3):
    inA = (r10=='PASS' and r12=='PASS' and n13=='PASS')
    inB = (r10=='PASS' and n13=='PASS')
    eq_ok, p_ok = (inA==inB), (n13!='PASS' or r12=='PASS')
    assert inA <= inB                      # A⊆B 在所有 8 格真 ⇒ 重言式
    print(r10, r12, n13, 'A==B?', eq_ok, 'P(r12|n13)=1?', p_ok,
          'breaks B⊆A?', (inB and not inA))
# 2) 禁止格比对（判「是否同一命题」）
F_BsubA = {(r10,r12,n13) for r10,r12,n13 in itertools.product(['PASS','CATCH'],repeat=3)
           if (r10=='PASS' and n13=='PASS') and not (r12=='PASS')}
F_P     = {(r10,r12,n13) for r10,r12,n13 in itertools.product(['PASS','CATCH'],repeat=3)
           if (n13=='PASS') and not (r12=='PASS')}
print('forbidden sets equal (theorems)?', F_BsubA == F_P)   # 应打印 False
# 3) 反证：把契约前提改一项，跑真实谓词（见 §1.4 的 judge 形态）
#    只要出现 inB=True, inA=False，即构造性证伪「A=B 是定理」
```

**检查清单（写报告前逐条打勾，可直接粘进交付件）**：

- [ ] `A=B` 已拆成 `A⊆B` + `B⊆A`，并**分别**标注「重言 / 实质条件 / 未验」。
- [ ] 已把定义展开，写明 `A = B ∧ C` 中的 `C` 是什么（本例 `C = {r12=PASS}`）。
- [ ] 已写出非平凡方向的 forbidden 格，并给「使它为空」的 `file:line` 或实跑命令。
- [ ] 已枚举全部原子格局（或给枚举上限），确认没有隐藏的分叉格。
- [ ] 已做至少一次构造性反证（改契约前提 / 换词表 / 换换行），并登记输出。
- [ ] 已比对「等式」与「被声称等价的条件概率/自由度/增量」的 forbidden sets 是否逐格相同。
- [ ] 已给语料范围：`N`、数据源 SHA256 + 字节数、`train=test` 声明、零命中的单侧/双侧 95% 上界。
- [ ] 已声明 `(predicate_sha, tokens_sha, text_sha, eol)` 四项契约；任一变化即等式重算。
- [ ] 主结论不挂在该等式上；若挂了，改挂代码级依赖图 + A1–A5 五检（`LAYER_IDENTITY.md:267-273`）。
- [ ] 禁用串自检：`决定性集合等式 / 不是近似省一层 / 两个自由度 / 只剩 1 个非 1 因子 /
      B⊆A⟺P(r12|n13)=1 / 38/38 为定理`（`LAYER_IDENTITY.md:400`；该哨兵**仍是提案、未实装**）。

---

## 3 第三步 普查本库同模式（逐处列 + 判定表）

### 3.1 普查范围与实跑命令

- C7：25 份 `.md` 强模式扫描（29 串，含 1 处重复字面；`恒等/重言/决定性/必相等/恒真/恒成立/完全相同/
  A==B/取等/一致率/0 bit/unresolved/残留` 等），逐份命中数落
  `lead/tautology_audit_20261109/_ta_grep_dump.txt` 与 `_ta_pattern_counts.txt`。
- C8：16 份文档（含两件台账）逐行带行号抽取，落 `_ta_grep_dump.txt`（533 行）。
- C9：`lead/` 全树 `.md/.txt/.json/.py` 全量扫 `一致率 / 22→0 / 无未验残留 / 恰取等 / 0 bit /
  决定性集合等式 / 三个旧措辞`，落 `_ta_special_grep.txt`、`_ta_special_narrow.txt`、
  `_ta_22to0_grep.txt`、`_ta_unresolved_grep.txt`、`_ta_three_phrases.txt`。
- 判定为「未验」的项目一律标未验，不补造；**未做全仓逐文件人工通读**（工作量外，见 §6(d)）。

### 3.2 (a)(c)(d) 逐处清单与判定表

> 判定四值：**重言式** / **实质条件（已证）** / **实质条件（未证）** / **未验**。
> 「已证」= 本次会话有实跑输出或只读 `file:line` 支撑其成立范围；「未证」= 只在 N 行观测上成立、
> 且本次会话已实跑构造出破它的输入；「未验」= 本次会话未跑该项的全称证明/生成过程。

| # | 位置（file:line） | 断言原文要点 | 判定 | 依据（本次会话实跑 / 实读） |
|---|---|---|---|---|
| **S1** | `METRIC_CONVENTION_AUDIT.md:108`；`_ma_METRIC_AUDIT.md:77` | 「**决定性集合等式**」：`{r10&n13 PASS}` 18 id **恰好等于** `{三层全 PASS}` 18 id | **复合**：`A⊆B` 半 = **重言式**；`B⊆A` 半 = **实质条件（已证仅在 74 行 / 已证伪为定理）**；「决定性」标签 = **须撤回** | C2 `A_n=B_n=18, only_A=only_B=[]`；C3 重言；C4/C6 X1 构造反例；`LAYER_IDENTITY.md:189,226,376` 已列须改「本 74 行观测等式」 |
| **S2** | `METRIC_CONVENTION_AUDIT.md:104` | 「根因**不是**『R12 数值接近 1 所以近似省一层』，而是 R12 不是独立证据根」 | **实质条件（已证）**，但同段 `:272` 又列 `{r10&n13 PASS} == {三层 PASS}` 为「必附独立性依据」⇒ 该条 **须改挂依赖图** | `:104` 本身正确（依赖图 `EVIDENCE_INDEPENDENCE.md:301`、`:111`）；`:272` 已被 `LAYER_IDENTITY.md:227,376` 点名；本次会话只读，未改 |
| **S3** | 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:125,146` | `A⊆B` 是「去掉一个合取项的逻辑重言式」（对）；但 `:146` 称 `B⊆A` 与 `P(r12\|n13)=1`「是**同一个命题**的两写法」（错） | `:125` **重言式（判对）**；`:146` 等价断言 **已证伪** | C3 分叉格 `CATCH CATCH PASS`；C5 实跑 `'已入账 grep 结果。不得不承认放行 N-5'` → `r10=CATCH r12=CATCH n13=PASS`、`B_subset_A_violated=False`、`n13P&r12C=True`；`LAYER_IDENTITY.md:122-130,337` 同判 |
| **S4** | `LAYER_IDENTITY.md:126-128,240,365,376` | 正确等价式 `A=B ⟺ P(r12\|r10&r13)=1`；`P(r12\|n13)=1` 额外排除一格 | **实质条件（已证）** | C3 八格 + C5 反例；本次会话 C2 `cells_r10C_n13P_r12C = 0` 实证 |
| **S5** | `EVIDENCE_INDEPENDENCE.md:149,294,302`；`CHAIN_VS_SINGLE.md:204,206`；`_cs_BASELINE_ALIGNMENT_20261109.md:226,334`；`KEFF_CALC.md:432,434,440` | 「R12 增量判别力 = **0 bit**」/「P 完全不变 0.1667→0.1667」/「R12 **不提供任何新信息**」 | **实质条件（已证仅在 74 行 / 全称形式已被证伪）** | C10 实跑后验阶梯 `prior 39/74 → n13=P 3/38 → +r10=P 1/6 → +r12=P 1/6`，`rows removed by +r12=PASS = []`；该空集 ⟺ `B⊆A`（§1.3），X1 使其非空 ⇒ 全称「0 bit」不成立；`KEFF_CALC.md:314,340` 已自标「观测值非定理、样本巧合+契约巧合」；`LAYER_IDENTITY.md:218,234` 已列须改「本 74 行观测」 |
| **S6** | `KEFF_CALC.md:120`；`EVIDENCE_INDEPENDENCE.md:127,131,135,140`；`_ma_verify_out.txt:49,51` | 「`r10×n13` **一致率** `38/74 = 51.35%`」 | **实质条件（已证：纯计数恒等式）** —— 不是重言式，但也不是独立性证据 | C10 实跑 `r10 x n13 agree = 38 / 74 = 0.5135135135135135`，交叉表 `{('PASS','CATCH'):16,('CATCH','CATCH'):20,('CATCH','PASS'):20,('PASS','PASS'):18}`；`EVIDENCE_INDEPENDENCE.md:131` 自标「**一致率低 ≠ 误差独立**」；`_ma_METRIC_AUDIT.md:92-93,181` 明记 `ρ̄` 两口径（误差相关 vs 标签一致率）不得混用。**注意 38/74 与 38/38=1 是同名不同分母，勿混** |
| **S7** | `KEFF_CALC.md:262-269,296`；`METRIC_CONVENTION_AUDIT.md:109,185`；`_ke_calc_stdout.txt:133`；`LAYER_IDENTITY.md:261,366` | 「Fréchet `min q_i` **恰被实测取等（饱和、零余量）**」 | **实质条件（已证：数学定理 + 本 74 行实测）**，非重言 | C11 实跑 `q_i = {'r10': 19/39, 'r12': 35/39, 'n13': 1/13}`、`min = 1/13`、`P(all3PASS|E) = 1/13`、`equals min? True`；`E-rows with n13=PASS but not all3PASS = []`（**取等条件**：`{all3PASS∩E} = {n13PASS∩E}`，即本批语料的又一次集合包含取等，同样**不必然**，X1 类输入可破）。`KEFF_CALC.md:265` 已自限「本 74 行内描述性天花板、非生产置信界」 |
| **S8** | `METRIC_CONVENTION_AUDIT.md:106-107,290`；`KEFF_CALC.md:311-340`；`LAYER_IDENTITY.md:85,110` | 「`P(r12=PASS\|n13=PASS)=38/38=1.000`」 | **实质条件（已证在 74 行 / 全称未证且已构造破）** | C2 `den 38 num 38 ratio 1.0`、`n13P_r12C ids=[]`；C4/C6 X1/X2/X3 直接破；`KEFF_CALC.md:315-326` 四种 95% 上界 `0.075808 / 0.078947 / 0.091810 / 0.092513`；`METRIC_CONVENTION_AUDIT.md:290` 自标「**是否定理 ⇒ 未验**」（本次会话已把「未验」升级为「构造性证伪为定理」） |
| **S9** | `CHAIN_VS_SINGLE.md:75,193`；`_cs_BASELINE_ALIGNMENT_20261109.md:124,211`；`COMPARABILITY_AUDIT.md:154,166,181`；`GATE_PIPELINE_COMPOSE.md:407,410,428` | 「`unresolved` **22→0**」「`chain_unresolved_total=0`」 | **实质条件（已证：算法换代 + 计数口径变更）**，且**已被上游自判为「空结论」** | C13 实跑两件 JSON：`_gp_regression_v1_union_out.json` `corpus_n=72 conflicts=31 unresolved=22`、`sum(layer_unresolved)=22`；`_gp_regression_out.json` `corpus_n=74 conflicts=31 unresolved=0`、`sum=0`。`GATE_PIPELINE_COMPOSE.md:250-254` 实跑 `K7=0 K8=0` ⇒ `:254`「**未消解 0 不等于裁决全部成功**」；`COMPARABILITY_AUDIT.md:166`「`unresolved 22→0` 与 `chain` 翻转 18 行是**同一件事的两个计数**」。C13 另实跑 `v1 chain=CATCH n=56 / unresolved>0 n=18 / u_not_c=[]` ⇒ `unresolved>0 ⊆ chain=CATCH`，是不对称包含，**不是恒等** |
| **S10** | `COMPARABILITY_AUDIT.md:158`；`_cmp_AUDIT_20261109.md:122` | 「`chain_changed=18 \| unresolved_changed=18 \|` **集合恒等? True**」 | **实质条件（已证：逐 id 集合相等）** —— 两列同名不同量，相等是本批数据的**观测**，非定义使然 | C13 实跑 `common ids = 71`、`chain_changed = 18`、`unresolved_changed = 18`、`sets equal? True`、`v1 unresolved sum on chain_changed = 22`、`layer_conflicts changed count = 0`；`COMPARABILITY_AUDIT.md:166` 已把它解释为「同一件事的两个计数」，措辞**未**升级为定理，风险低 |
| **S11** | `c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md:167`；`_tp_TP_VERIFIER_CHECKLIST.md:77`；`C07_TRUTH_SELF_PROOF.md:240`；`chain_vs_single_20261109/_csv_attrib_out.txt:26` | 「**无未验残留**」 | **未验（作为「通过」档的判定条件，非已达成的事实）** —— 三处都是三档判定表的「通过」格**条件**；`C07_TRUTH_SELF_PROOF.md:125` 明写「凡『未验』不得计入通过档」、`:261-267` §6.4 仍列 6 条未验项 | C16 实跑全树扫 `无未验残留` 恰 3 命中，均为判定表条件行；`C07_TRUTH_SELF_PROOF.md:261-267` 实读 6 条未验（含见证流程未演练、ROUND_SUBAGENT_LOG 未查等）⇒ **不得读作「已无未验」**。注：`_csv_attrib_out.txt:26` / `_final_attrib_check.txt:26` 的命中是**引用的同一张判定表**，不是该写域自报结论 |
| **S12** | `SCORE_DECOMP.md:233-235`；`_sd_report.md:348-354,363` | 「S3 DEFAULT 是**恒真兜底**在正类样本上的必然命中，信息量 = 0」 | **重言式（真恒真，但类型不同）** —— 对「任何拿不准的行恒返回 CATCH」是代码定义；其对正类命中是 `expect=CATCH ∧ 恒CATCH` 的必然 | `SCORE_DECOMP.md:230,235` 实读 `_v12_rule.py:167-170`、`EVIDENCE_INDEPENDENCE.md:169,173`「不是语义识别」、`_eind_verify_out.json:302 only_default=true`；`_sd_report.md:354` 自判「不算算法改进」。**这是本库唯一把恒真性正确标为「零信息量」而非「定理」的落点，属正面样板** |
| **S13** | `PVALUE_RECALC.md:197,250`；`_pv_PVALUE_RECALC.md:226-228`；`_pv_recompute_out.txt:63` | 「post-selection 下 `P(18/18\|入选失败集)≈1`、自信息 **≈0 bit**」 | **实质条件（已证：post-selection 条件分布下的构造性结论）**，非重言 | `PVALUE_RECALC.md:124` 实跑 `gains=18 losses=0`、`distinct patterns=1`、18 条全属 K3+K9；`:197` 明写「似然比不可识别…不存在有效的 post-selection p」；与 S5 的「R12 0 bit」**不同论域**（`LAYER_IDENTITY.md:229` 已判「不适用」） |
| **S14** | `LAYER_IDENTITY.md:132-144,238-241,384`；前件 `:194,197,236,320,325` | 「只剩 **1 个非 1 因子** / **不是两个自由度**」 | **实质条件（已证：仅描述 `n13` 优先的一种因子化；作为「决定性自由度论据」已证伪）** | C10 实跑 6 排列：`n13>r10>r12` 与 `n13>r12>r10` 为 `1/13·1·1`（non1=1），`r10>n13>r12`、`r12>n13>r10` non1=2，`r10>r12>n13`、`r12>r10>n13` non1=3，**乘积 6 种恒 `1/13`**；`LAYER_IDENTITY.md:133-144` 同表。因子数随顺序变 ⇒ 不能当自由度计数 |
| **S15** | `EVIDENCE_INDEPENDENCE.md:98,165`；`_cs_info_out.txt:16`；`_cs_BASELINE_ALIGNMENT_20261109.md:203` | 「55 行 `tokens` 与 `N13.DEFAULT_TOKENS` **完全相同**」「6/6 完全相同」 | **实质条件（已证：逐字比对恒等式）**，非重言 | C12 实跑 `distinct token sets = 4`、55 行 `['已入账','已追加','已生效']`、17 行 BAD_BAN 五词、1+1 行 C07 词表、`rows tokens NOT subset of T = 19`；`distinct label triples = 5 of 8`（与 `LAYER_IDENTITY.md:200` 一致）。这些「完全相同」是数据比对结果，不靠定义 |
| **S16** | 前件 `:146` 引述的编排方背景三句（「这是恒等不是近似」「两个自由度」「决定性集合等式」）；`METRIC_CONVENTION_AUDIT.md:108` | 三句旧措辞 | **须撤回（逐句替换见 §5(a)）** | C9 实跑：三句旧措辞在两件台账中 **0 命中**（`PENDING_DECISIONS.md` 恒等/决定性/两个自由度/38/38 全 0；`GOAL` 有 `恒等` 46 命中但**均属别论域**，C9 逐行核），原件仅在 `metric_audit_20261109` 两件与 `layer_identity_20261109` 两件的**引述/修正文字**中出现 ⇒ 属编排方上一轮口头措辞，非台账登记结论 |

### 3.3 汇总

- **真重言式**：`A⊆B`（S1 半、S3 `:125`）、S12 的恒真兜底（不同类型）。
- **实质条件·已证**：S2 `:104` 主句、S4 正确等价式、S6 一致率、S7 Fréchet 取等、S9 `22→0`、
  S10 集合恒等、S13 post-selection 0 bit、S14 六排列、S15 逐字相同。全部**只在给定 N 行/给定
  契约上成立**，其中 S7/S9/S10 的「取等/相等」同样可被 X1 类输入或换算法破，不得升级为定理。
- **实质条件·未证（全称形式已构造性证伪）**：S1 的 `B⊆A` 半、S5「0 bit」全称、S8 `38/38` 全称。
- **未验**：S11「无未验残留」（是条件不是事实）、以及 §6(d) 所列未跑项。
- **错置（非重言、非实质，是等价性断言错误）**：S3 `:146`「同一命题」—— 这是**把 `A⊆B` 的证明
  当成 `A=B` 的证明**之外，本库同模式的第二个复发点，且 `LAYER_IDENTITY.md:122-130` 已纠正。

---

## 4 第四步 危害评估

### 4.1 (a) ★ 把重言式当定理会推出的具体错误结论（逐条给例）

| 误用 | 被包装的「定理」 | 推出的错误结论 | 本次会话的证伪/纠偏 |
|---|---|---|---|
| E1 | 「`A⊆B` 已证 ⇒ 恒等已证一半」 | 少列一个待证条件，报告只写「`B⊆A` 待查」；「决定性集合等式」看起来有证明支撑 | C3 证 `A⊆B` 在全部 8 格真、零信息量；`LAYER_IDENTITY.md:104,126` 已自标「重言式」 |
| E2 | 「`A=B` 是逻辑必然」 | 「R12 **恒** PASS / **不提供任何新信息**（全称）」⇒ 可安全删掉 R12 层 | C4/C6 X1/X2/X3 三例 `r10=PASS r12=CATCH n13=PASS` 直接反证；`KEFF_CALC.md:340`「不是恒等式」 |
| E3 | 「集合恒等 ⇒ 只有 **2 个独立层** / 两个自由度」 | 可按 2 层乘 `q_r10×q_n13 = 19/507 = 3.75%` 当联合漏报 | C11 实跑 `prod2 = 19/507 = 0.037475` 但链式精确值 `1/13 = 3/39 = 0.076923`，`chain/prod2 = (1/13)/(19/507) = 39/19 = 2.0526` 倍低估（即 `EVIDENCE_INDEPENDENCE.md:131` 的 2.0526）；C10 六排列证「非 1 因子数 1/2/3 随顺序变」⇒ 不能数自由度；`LAYER_IDENTITY.md:197,200,261` 已判不合法 |
| E4 | 「`P(r12\|n13)=1` ⟺ `A=B`」（同义改写误判） | 用 38/38 一个数字同时给「集合等式」「0 bit」「k_eff 的 `p2=p3`」背书，一处破则三处静默同破而不被察觉 | C3 分叉格 + C5 `'已入账 grep 结果。不得不承认放行 N-5'` 破 P 不破 `B⊆A`；`LAYER_IDENTITY.md:128,337` |
| E5 | 「三层连乘只是少乘一项的算术误差」 | 以为补一个因子/改 3 层为 2 层即可修正，保留 `Πq_i` 模型 | C11 实跑 `prod3 = 665/19773 = 0.0336317`、`chain/prod3 = 1521/665 = 2.287218045112782`；根因是 **H1（给定 E 条件独立）已证伪**（`EVIDENCE_INDEPENDENCE.md:246-247,256` 明令不得用 `Πq_i`）⇒ **模型假设错误，非算术误差**（编排方背景已给同一分数，本次会话 C11 全等复现） |
| E6 | 「`unresolved=0` ⇒ 裁决全部成功」 | 把空结论当通过证据，掩盖 K8 死分支与 3 条共同盲区不进 `conflicts[]` | `GATE_PIPELINE_COMPOSE.md:250-254,410` 自判「**空结论**」；`COMPARABILITY_AUDIT.md:166` 判为「同一件事的两个计数」；C13 两版 JSON 实跑 |
| E7 | 「`P(18/18\|入选失败集)≈1` ⇒ p 仍稳健 / 算法更好」 | 用 post-selection 的≈0 bit 自信息反推显著性 | `PVALUE_RECALC.md:197,251` 明写「似然比不可识别 / 禁止显著改善等措辞 / 真实 p 未验」 |

### 4.2 (b) 与「口径错置」是否同族；区分

**同族但不同层**。二者都是「把 A 类陈述当 B 类陈述用」的**范畴错误**，都会被「数值碰巧对上」掩盖：

| 维度 | 重言式包装成定理（本模式） | 口径错置（`METRIC_CONVENTION_AUDIT.md` 论域） |
|---|---|---|
| 错在哪 | **命题强度**：把恒真（零内容）或 N 行观测说成逻辑必然/全称定理 | **量的定义**：分子/分母/条件方向/事件类别被换掉 |
| 典型症状 | 「决定性」「恒等」「必相等」「不是近似」「两个自由度」 | `fp_rate=P(CATCH\|¬E)`（分母 35）被当 `q_i=P(PASS\|E)`（分母 39） |
| 数值 | 通常**是对的**（38/38=1、18=18、min=1/13 全对） | 通常也**碰巧接近**（3.75% vs 3.36%、2.05 vs 2.07 差 0.98%）⇒ 更难发现 |
| 判据 | forbidden set + 反证构造（§2.3） | 「分子分母的定义」，不是数值大小（`METRIC_CONVENTION_AUDIT.md:3,100`） |
| 破法 | 改一个契约前提、构造落进 forbidden 格的输入（X1） | 逐处写清分子/分母/条件类，禁止用边缘 `q_i` 顶替条件因子 |
| 本库判词 | `LAYER_IDENTITY.md:189`「74 行样本上成立 ≠ 逻辑上成立」 | `METRIC_CONVENTION_AUDIT.md:268`「不许用『口径不一致』概括」 |
| 交叉点 | E5 的三层连乘**同时**是两类错：既把条件因子 `1` 换成边缘 `q_i`（口径），又靠恒等把「少一层」说成结构性（强度） | `LAYER_IDENTITY.md:258-260` 逐字把两者并列表述 |

**区分口诀**：*口径错置问「这个数的分子分母是什么」；重言式包装问「这句话在任何 input 下都真吗」。*
前者错了数会变，后者错了数不变、只是**你以为它有证明而它没有**。

### 4.3 (c) ★ 为什么特别难发现

1. **它是对的**。`A⊆B` 在 8/8 真值格局上真、`18=18`、`38/38=1`、`min q_i=1/13=实测`
   全部通过任何数值复核（C2/C3/C10/C11）。审查者查数、查指纹、查一致性都不会报错。
2. **错的是强度不是真值**。把「本 74 行观测」写成「决定性/恒等/定理」，字面仍与所有实跑输出
   相符；只有问「有没有一个 input 能破」才会暴露（C4/C6）。
3. **名字唬人**：「决定性」「集合等式」「不是近似」「两个自由度」自带数学权威，读者默认
   它已附全称证明；`METRIC_CONVENTION_AUDIT.md:108` 甚至把实跑输出 `set equal? True`
   直接接到「决定性」标签上，中间没有「范围声明」。
4. **数值碰巧相等的掩护**：`3.75%` vs `3.36%`、`2.05` vs `2.07`、`1.000` 与真 LR=1
   `METRIC_CONVENTION_AUDIT.md:211` 记「**精确相等**」—— 数值越漂亮越没人去查定义。
5. **重言半与实质半混在同一句**。一句「集合恒等」同时含 `A⊆B`（必真）与 `B⊆A`（偶然），
   前半的不可错性给后半背书（S1）。
6. **反例不在语料里**。C12 实跑 `tokens NOT subset of T = 19`，破口在语料里真实存在，
   但这 19 行**恰好**没在超集 token 上命中双重否定；74 行上零违例，只有主动构造 X1 才见到。
7. **复核机制默认查「有没有跑过」而非「跑的结论属于哪一类」**。本库已有多处正确自限
   （`KEFF_CALC.md:314,340`、`METRIC_CONVENTION_AUDIT.md:290`、`GATE_PIPELINE_COMPOSE.md:410`），
   但措辞层与结论层可以长期并存不冲突。

### 4.4 (d) 报告里防止的机制（可实装清单）

1. **两段式等式声明（强制）**：任何 `A==B` 必须写成
   `A=B ⟺ [重言半：定义式 + 8 格穷举] ∧ [实质半：forbidden 格为空，依据=…/仅 N 行]`。
   已由 `LAYER_IDENTITY.md:393` 第 5 条给出范式。
2. **破坏性输入随附**：每条恒等断言必须带一个「什么 input 会破」的构造或实跑输出
   （X1/X2/X3 形态），否则标「未验」。
3. **契约四元封印**：`(predicate_sha, tokens_sha, text_sha, eol)` 逐行登记，任一变化等式重算
   （`LAYER_IDENTITY.md:395`；`KEFF_CALC.md:283-285` 的置信度模板已有同款前置条款）。
4. **零命中给区间**：38 次零命中一律附单侧精确/Wilson/CP 四种 95% 上界 7.6%–9.3% 并分列口径
   （`KEFF_CALC.md:315-326`），禁止把 `1.000` 写成精确值。
5. **主结论与等式解耦**：「≤1 层 / 绝不按 3 层 / 不得自动放行」只挂依赖图 `file:line` +
   A1–A5 五检（`LAYER_IDENTITY.md:267-273`）；等式只作描述（`:393` 第 5 条）。
6. **负例哨兵**：`LAYER_IDENTITY.md:400` 的 8 个禁用串与 `METRIC_CONVENTION_AUDIT.md:283` 的
   4 个数禁用串列为生成时断言 —— **如实：两处均记「仍是提案、未实装」**，本任务不改脚本。
7. **判定三值 + 范围标签**：每个结论强制带 `[重言式 / 实质条件·已证 / 实质条件·未证 / 未验]`
   与 `[全称 / 仅 N 行 / 反事实]` 两个标签，禁止裸写「成立」。
8. **独立复核专问强度**：复核回件的 `whatBreaksIt` 固定要问「构造一个破它的输入」，
   而不是只复算数值（本轮【复核】正是这样抓到 X1 的，见 `LAYER_IDENTITY.md:112`）。

---

## 5 第五步 结论与建议

### 5.1 (a) ★ 上一轮三句措辞逐句替换

| # | 旧措辞（须撤回） | 准确替换（可直接引用） | 依据 |
|---|---|---|---|
| 1 | **「恒等不是近似」**（及 `METRIC_CONVENTION_AUDIT.md:104`「不是近似省一层」的旧读法） | **「本批 74 行上 `{r10&r12&n13 全 PASS}` 与 `{r10&n13 双 PASS}` 是同一个 18 个 id 的集合；这是观测等式，不是逻辑恒等式。其 `A⊆B` 半是 `A=B∩{r12=PASS}` 的定义重言式，非平凡半 `B⊆A` 等价于 `(r10=P,n13=P,r12=C)` 格为空，只在受限契约（同一 tokens / LF 对齐 / 命中 token ∈ T）下由源码蕴含；X1/X2/X3 已构造性破之。」** | §1.2–1.4；C2/C3/C4/C6；`LAYER_IDENTITY.md:189,365-366`；`METRIC_CONVENTION_AUDIT.md:108` 数值仍对、标签须改「本 74 行观测等式」（`:376` 第 1 项） |
| 2 | **「两个自由度」**（及前件 `:236`「不是两个自由度，而是只有一个非 1 因子」） | **「全 74 行的 `(r10,r12,n13)` 标签三元组有 5/8 种可观测组合，只能作**描述**；这是标签自由度，不是可用独立因子数。链式法则 6 种因子化乘积恒 `1/13`，非 1 因子数 1/2/3 随顺序变，不能据此数自由度或独立层数。结构性答案只有依赖图 `R10→{R12,N13.C}` + 五检给出的「可用独立因子 ≤1（根=1）」。」** | C10 六排列实跑；C12 `distinct label triples = 5 of 8`；`LAYER_IDENTITY.md:133-144,200,238-241,384`；`EVIDENCE_INDEPENDENCE.md:111,301` |
| 3 | **「决定性集合等式」**（及 `METRIC_CONVENTION_AUDIT.md:272` 把它列为「必附独立性依据」） | **「本 74 行观测等式（18 id 逐一对齐，`only_A=only_B=[]`）。`A=B` 的正确等价式是 `P(r12=PASS\|r10=PASS&n13=PASS)=1`；`P(r12=PASS\|n13=PASS)=38/38=1` 是更强的观测、还额外要求 `(r10=C,n13=P,r12=C)` 格为空，该格为 0 也是巧合。独立性依据改列代码级依赖图 `file:line`（`_g7_predicates.py:144-145`、`_ei_n13_predicates_src.py:199-202,241-245,253-256`、`_gp_pipeline.py:80-81`），不把集合等式列为必附条件。」** | C3/C5/C11；`LAYER_IDENTITY.md:122-130,227,376`；`METRIC_CONVENTION_AUDIT.md:272` 须改（本任务只读，未改） |

**逐句给出「撤回」而非「改写数值」**：三处的**数值全部成立**（18=18、38/38=1、5/8），
被撤回的是「恒等/决定性/自由度」三个**强度标签**及其隐含的全称性与独立性推论。

### 5.2 (b) 哪些结论要改、哪些反而更稳

**要改（降级/改措辞，均不改数值）**：

1. `METRIC_CONVENTION_AUDIT.md:104,108,272`、「不是近似省一层 / 决定性集合等式 / 必附独立性依据」
   → 「本 74 行观测等式」+ 依赖图 `file:line`（`LAYER_IDENTITY.md:376` 第 1 项）。
2. `EVIDENCE_INDEPENDENCE.md:149,294,302`、`CHAIN_VS_SINGLE.md:204,206`、
   `_cs_BASELINE_ALIGNMENT_20261109.md:226,334`、`KEFF_CALC.md:432,434,440` 的
   「R12 增量 0 bit / 1.000 / 不提供任何新信息」→ 「本 74 行观测」+ 四种 95% 上界 + 破口
   （`LAYER_IDENTITY.md:377-378` 第 2/3 项）。
3. 前件 `_li_LAYER_IDENTITY_PROOF_20261109.md:146` 「`B⊆A ⟺ P(r12|n13)=1` 是同一命题」
   → **删除**，改正确等价式（`LAYER_IDENTITY.md:376`）。
4. 前件 `:110,194,197,236,320,325` 「只剩 1 个非 1 因子 / 不是两个自由度」
   → 「在 `n13` 优先因子化下两个条件因子为 1；非 1 因子数 1/2/3 随顺序变，乘积恒 `1/13`」
   （`LAYER_IDENTITY.md:384` 第 9 项）。
5. `EVIDENCE_INDEPENDENCE.md:299-306` 六条理由 → `:301` 依赖图 + `:111` 五检为**结构性**、
   `:302/:303/:304/:305/:306` 为**本 74 行统计佐证**（`LAYER_IDENTITY.md:385` 第 10 项）。
6. `p2=p3`、k_eff 三口径 `0.606/0.670/0.804`、`0.61 层`、`≈1～1.3 层（乐观 1.5）`
   → 标「描述性、本批语料偶然量、不可用于放行」，禁作层数计数
   （`LAYER_IDENTITY.md:213,221-225,304,306`、`KEFF_CALC.md:418-419,436-443`）。
7. `q_r10×q_n13 = 19/507` 与 `q_r10×q_r12×q_n13 = 665/19773` → 标「反事实基线期望 /
   仅『若真有 3 独立层』的算式」，精确值走链式 `1/13×1×1`、上界走 Fréchet `min_i q_i`
   （`LAYER_IDENTITY.md:246-263`；C11 全等复现 2.287218045112782）。

**反而更稳（不受影响，且不能再被误读）**：

- **「按 ≤1 层计、绝不可按 3 层、三层全 PASS 不得自动放行」** —— 靠代码级依赖图
  `R10→{R12,N13.C}`（`EVIDENCE_INDEPENDENCE.md:301`、`_eiv_03_stats.py:182-184`）与
  A1–A5 五检（`:111`「没有任何一对能同时过 5 检」），**不靠 38/38**
  （`LAYER_IDENTITY.md:214,228,233,273`；`METRIC_CONVENTION_AUDIT.md:267`）。
- **「独立证据根 = 1」「numeric=1 是保守取整约定非测量值」「R9/R11 正交」**
  （`KEFF_CALC.md:165-167,236`；`EVIDENCE_INDEPENDENCE.md:296`）。
- **「不得用 `Πq_i`、H1 已证伪、真上界是 Fréchet `min_i q_i`」**
  （`EVIDENCE_INDEPENDENCE.md:246-247,252,256`；C11 复现）。
- **「3 个判据 / 1 个独立证据根」「18 行里 3 行真断言（GP-A1/A2/A3）⇒ 禁止自动放行」**
  （`KEFF_CALC.md:287-288,301-302`；C2 八格表与 `LAYER_IDENTITY.md:73-75` 逐 id 表）。
- **「72 与 74 不可比」** —— 三轴同变 + E 轴脚本未留盘（`CHAIN_VS_SINGLE.md:76`、
  `_cs_BASELINE_ALIGNMENT_20261109.md:125`；C13 两版 JSON 实跑）。恒等偶然性只**再加一条**
  「不能把集合相等读成结构结论」的理由，不动可比性判词。

### 5.3 (c) 以后写恒等类断言的准则（10 条）

1. **先拆两半**：`A=B` = `A⊆B` ∧ `B⊆A`，逐半标 `[重言式 / 实质条件·已证 / 实质条件·未证 / 未验]`。
2. **展开定义**：写明 `A = B ∧ C` 的 `C`；能只靠逻辑证的一半立即标「重言、零信息量」，不计入证明。
3. **写 forbidden 格**：非平凡方向的否定条件逐格列出，并给「使它为空」的 `file:line` 或实跑命令。
4. **枚举全部原子格局**：2^n 全跑，打印每格的等式真值与被声称等价命题的真值，比对 forbidden sets。
5. **构造反例**：改一项契约前提（词表 / 换行 / 位置口径），跑谓词直调；构造失败才考虑标定理。
6. **写范围四元**：`N / 数据源 SHA256+字节数 / predicate_sha+tokens_sha+text_sha+eol / train=test`。
7. **零命中给区间**：单侧精确、rule-of-three、Wilson 双侧、双侧精确四种 95% 上界分列，禁止把
   `1.000` 当精确值。
8. **禁止「决定性/恒等/必相等/恒真/恒成立」裸用**：这些词只能跟在「本 N 行观测」或
   「在以下契约下的受限定理」之后，且必须附破坏构造。
9. **主结论不挂等式**：独立性/层数结论只挂依赖图 + 五检；等式只作描述，不作「必附依据」。
10. **同义改写要证**：说「X 与 Y 是同一命题」必须先比对两者 forbidden sets 逐格相同
    （C3 的 `forbidden sets equal? False` 就是反例）；否则只写「在 N 行上同真」。

（与 `LAYER_IDENTITY.md:387-400` 的 12 条「报层数准则」互补：那 12 条管**量纲**，
本 10 条管**命题强度**；二者须同时执行。）

### 5.4 (d) 如实列：这条工作判不了什么

- **真机运行态**：铁律零真机 ⇒ `gamemd.exe`/`ra2loader`/`YURI.exe`、活进程内存一律 **未验**。
- **生产语料上恒等是否成立 / `q_i,c_i,ρ,k_eff` 的泛化**：74 行 train=test 且含定向对抗样本；
  X1/X2/X3 是**构造输入**不是生产观测 ⇒ **未验**（`LAYER_IDENTITY.md:414`）。
- **X3（CRLF 位置错位）在生产链的可达性**：`LAYER_IDENTITY.md:186` 实跑 `read_text` 归一
  CRLF→LF、9 件读盘真件 `CRLF=0`；是否存在内联/直接文本入口 ⇒ **未验**。本次会话未重跑该项。
- **两条升级条件**：① 代码级全称证明「`(r10=C,n13=P,r12=C)` 任何输入不可达」；
  ② 证明 X1/X2/X3 类输入在生产契约下全部不可达 —— 本次会话**未做**，故本件不把
  「恒等不是逻辑必然」升格为「在给定生产契约下是定理」（`LAYER_IDENTITY.md:339,421`）。
- **加入 X1/X2 后整体统计量的变化**：未重跑 `_gp_regression.py` 全 74+2 行、未重算
  `q_i`/k_eff/CI；铁律不改语料/产物 ⇒ **未验**（`LAYER_IDENTITY.md:416`）。
- **k_eff 点值与 bootstrap 区间本次会话重算**：只引用 `KEFF_CALC.md:139-147,191-200`，
  本次会话**未重跑** ⇒ **未验**（`LAYER_IDENTITY.md:422`）。
- **`_gp_regression_out.json` 的生成过程归属**：本次会话以现盘 SHA `d3543657…` 重算全等，
  但**未重跑**生成脚本 `_gp_regression.py`（只读）⇒ 生成过程 **未验**（`LAYER_IDENTITY.md:423`）。
- **72 版 `48/72` 生成脚本**：`COMPARABILITY_AUDIT.md:118,295,310,343` 标「脚本未留盘、未重跑」；
  本次会话只读两版 JSON ⇒ **未验重跑**（C13 只核 JSON 内部自洽）。
- **盲留出集误差相关双检**：`_cs_holdout_out.json` 缺 r10/r12 列、3 条逐字重复 ⇒ **未验**。
- **两件台账其它论域的「独立证据」措辞**：C9 只核了三句旧措辞与强模式命中数
  （`PENDING_DECISIONS.md` 0、`GOAL` 的 `恒等` 46 命中属别论域），**未全仓逐行人工通读**
  ⇒ **未验**（`METRIC_CONVENTION_AUDIT.md:295` 同判）。
- **负例哨兵机检是否实装**：`LAYER_IDENTITY.md:400`、`METRIC_CONVENTION_AUDIT.md:283`
  均自记「仍是提案、未实装」⇒ 本任务**未实装**，只给可粘贴清单（§2.4）。
- **本件自身 verdict**：未请求第三方复核，不自行标 `confirmed`；上游前件 `verdict = partial`
  按交付规则标 **`unconfirmed`**（`LAYER_IDENTITY.md:333-339,425`），本件不改动该 verdict。

---

## 6 交付与纪律核验

- 唯一写域 `lead/tautology_audit_20261109/`：本件 + 13 件 `_ta_*` 中间产物（grep 落盘、
  逐行摘录、模式计数、判定表草稿）。**未改任何脚本、语料、产物、台账**。
- 9 件只读指纹本次会话重算 **2 次**（C1 首轮、C14 收尾）均 `ALL_9_MATCH = True`；
  2 件谓词源码 SHA 亦全等 `LAYER_IDENTITY.md:46,359-360` 所记（§0 补测）。
- 关于内联 `importlib` 加载：本次会话用 `python -I -X utf8 -c` 只读加载两份谓词源码
  （C4/C5/C6）。盘上 `lead/gate_fp7_20261108/__pycache__/_g7_predicates.cpython-312.pyc`
  mtime `2026-11-09 00:45:10`、`lead/evidence_indep_20261109/__pycache__/_ei_n13_predicates_src.cpython-312.pyc`
  mtime `2026-11-09 20:47:07`（C15 实跑 `stat`），**均早于本次会话（21:1x–21:2x）**，
  系上游既有件；本次会话未新建/改写任何 `__pycache__`，只读源码 SHA 二次实算未变（C14）。
  两件台账的 `MM` 状态为会话开始前 gitStatus 快照既有（`MM lead/GOAL_THREE_TARGETS_20261018.md`、
  `MM lead/PENDING_DECISIONS.md`），本次会话未对其写入；九件指纹全等基线可证。
- `git log -1 --oneline` = `2657458`（C15 实跑）⇒ 未 commit / 未 push。
- 零真机、零采样代码：所有计算为 `python -I -X utf8 -c` 内联，只用
  `json / hashlib / pathlib / itertools / collections / fractions / importlib.util / re`；
  无 subprocess、无进程内存、无 hook / MiniDump / SuspendThread / StackWalk / 探针注入 / 动态内存解析。

### 6.1 本次会话实跑命令清单（可复核，逐条给输出要点）

| 编号 | 命令（`python -I -X utf8 -c` 内联 + 绝对路径） | 输出要点 |
|---|---|---|
| C1 | `<9 件 read_bytes + hashlib.sha256 + len + 对照编排方基线>` | 9 行全等，`ALL_9_MATCH = True`（§0 绑定行） |
| C2 | `<读 rows；A={r10=P&r12=P&n13=P}、B={r10=P&n13=P}；逐 id 比对；8 格列联表；P(r12\|n13)>` | `n=74 / A_n=18 B_n=18 / A_subset_B=True B_subset_A=True sets_equal=True / only_A=[] only_B=[] / den 38 num 38 ratio 1.0 / B_not_A_rows=[] / r12=CATCH ids=[R10-TV3,R10-CTX-05,R10-CTX-06,GP-C04]` |
| C3 | `<8 种真值格局 itertools.product；A⊆B 全域检查；forbidden sets 比对>` | `A⊆B is tautology ... check all 8: True`；`B⊆A fails exactly when (r10=PASS, r12=CATCH, n13=PASS)`；分叉格 `CATCH CATCH PASS` 上 `A==B? True / P=1? False` |
| C4 | `<importlib 只读加载两谓词；judge('不得不承认放行 N-5', BAD_BAN, T)；打印 r12_scan 两种词表命中>` | `X1 r10=PASS r12=CATCH n13=PASS / inB=True inA=False => A!=B? True / n13P&r12C=True`；`r12_scan(BAD_BAN)=['越权断言 放行 N-5（R12：回看窗含双重否定构式=肯定）']`、`r12_scan(T)=[]`、`N13 T tokens present=[]` |
| C5 | `<judge('已入账 grep 结果。不得不承认放行 N-5', BAD_BAN, T)>` | `r10=CATCH r12=CATCH n13=PASS / inB=False inA=False / B_subset_A_violated=False / n13P&r12C=True`（破 P 不破 `B⊆A`） |
| C6 | `<C4 形态复跑 X1/X2/X3 + C0 对照>` | `X1/X2/X3 均 (PASS,CATCH,PASS)`；`C0 ('PASS','CATCH','CATCH')` |
| C7 | `<25 份 .md 强模式扫描 35 串，逐份计数>` | 命中文件清单与逐串总数（`恒等=66, == 117, 决定性=13, 恒真=10, 重言=1 …`） |
| C8 | `<16 份文档逐行带行号抽取>` | `_ta_grep_dump.txt` 533 行；`_ta_pattern_counts.txt` 23 份文件逐串计数 |
| C9 | `<lead/ 全树 .md/.txt/.json/.py 扫 一致率/22→0/无未验残留/恰取等/0 bit/决定性集合等式/三句旧措辞>` | `_ta_22to0_grep.txt` 899 行、`_ta_three_phrases.txt` 729 行、`_ta_unresolved_grep.txt` 2384 行；两件台账三句旧措辞 **0 命中** |
| C10 | `<一致率 + 交叉表 + 后验阶梯 + 0 bit 空集 + 6 排列 fractions.Fraction>` | `agree=38/74=0.5135135`；`prior 39/74 → 3/38 → 1/6 → 1/6`；`rows removed by +r12=PASS=[]`；6 排列 `prod=1/13` 恒定、`non1=1/2/3` |
| C11 | `<E=expect=CATCH 39 行；q_i / prod2 / prod3 / chain / Fréchet / 比值 精确分数>` | `q10=19/39 q12=35/39 q13=1/13`；`min=1/13`、`P(all3PASS\|E)=1/13 equals min? True`；`prod2=19/507=0.037475345`、`prod3=665/19773=0.033631720`；`chain/prod3=1521/665=2.287218045112782`；`prod3/chain=665/1521=0.43721236` |
| C12 | `<74 行 tokens 分布 + 标签三元组枚举>` | `distinct token sets=4`（55/17/1/1）；`NOT subset of T = 19`；`distinct label triples = 5 of 8` |
| C13 | `<两版 JSON unresolved/conflicts + 72→74 共有 71 行 chain_changed / unresolved_changed 比对>` | `72: n=72 conflicts=31 unresolved=22 sum=22 rows>0=18`；`74: n=74 conflicts=31 unresolved=0 sum=0`；`chain_changed=18 unresolved_changed=18 sets equal? True all CATCH->PASS? True v1 sum=22 layer_conflicts changed=0`；`v1 chain=CATCH n=56 / unresolved>0 n=18 / u_not_c=[]`（不对称包含） |
| C14 | `<收尾二次重算 9 件指纹 + 2 件谓词源码 SHA>` | `ALL_9_MATCH = True`；两谓词 `MATCH True`（`02c17e49…` / `e1195b3b…`） |
| C15 | `<stat 两 pycache mtime + git status 限定只读域 + git log -1 --oneline + date>` | pycache mtime `00:45:10` / `20:47:07` 早于本次会话 `21:24`；`git log -1 = 2657458`；写域仅 `_ta_*` |
| C16 | `<c07_truth_protocol_20261109 全树扫 无未验残留>` | 恰 3 命中，均为三档判定表的「通过」**条件**行；`C07_TRUTH_SELF_PROOF.md:261-267` 仍列 6 条未验项 |

---

*本件结束。所有「实跑」均为本次会话内执行的命令；所有「文件:行」均为本次会话内 Read / Python 逐行读取。
未跑项一律标「未验」，未把任何未验写成通过；未改任何脚本、语料、产物、台账。*

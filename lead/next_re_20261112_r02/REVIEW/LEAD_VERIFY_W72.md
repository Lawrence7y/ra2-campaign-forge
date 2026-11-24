# LEAD_VERIFY_W72 · inplace 的**行为层**证据：`SAME_DISTRIBUTION`（覆盖缺口已补）

> 记录人：Lead｜时间：2026-11-14 01:48｜卡：W72（Hy4，真机四趟，一趟一锁）
> 权威读数：`out\b_compare_v2.json`（卡内 FROZEN **W68b 权威版**工具，sha `B419959A…` 与我签发值逐位一致；`SHA256_PROOF.json` 自证）
> 补的是 `REVIEW\LEAD_VERIFY_W69.md` §5 指出的缺口：**W65/W69 测的是 append，产品路线是 inplace**

## 1 · 判定

`[签发]` **`SAME_DISTRIBUTION` / `within_noise_band`**

```
D_ks=0.000393 <= max(N_ks=0.000167, D_floor=0.05) and p=0.923538 >= alpha
n_a=20627  n_b=20587  N_ks=0.000167  J_ui=1.0  delta_Q=0.0
discrete_shifted=[]  discrete_unstable=[]
```

**正确表述（照写）**：
> **在 V2 判据、该场景、该观测量集合下，未检出 inplace 改写 `BATTLEMD.INI` 所导致的行为分布差异。**

## 2 · 设计是否真的隔离出了自变量（我核过）

| 项 | 实测 |
|---|---|
| 两臂同图 | **四趟 `map_name` 唯一取值全为 `SOV01UMD.MAP`**（A1/A2/B1/B2 = 10308/10320/10287/10301 行），逐行 `all_rows_expected=true` |
| INI diff | **1 行**：L55 `Scenario=SOV01umd.MAP` → `Scenario=SOV01UMD.MAP`；前后均 2,733 B / 146 行 / 145 CRLF / **0 bare LF**；before sha `7e40691a…`、after sha `919a50b2…`；其余 145 行逐字节相同 |
| C 判据 | **PASS**：`W ⊆ D`、`out_of_scope=[]`、`protected_all_equal=true`、`restore.equal=true`、`C-1..C-6` 全 true；`BATTLEMD.INI` 分类 = **`DECLARED-REWRITE`（非越界）**；`.bak` 在位且 `bak_sha256 == official_sha256` |
| 真目录 | `IDENTICAL_TREE=True`（647 文件 / 1,989,215,270 B，added/removed/modified 全 0，5 锚点哈希 PRE==POST） |
| 锁 | 每趟 `lead→w72→lead`，收尾 `owner=lead`，`gamemd` 残留 0 |

`[它为什么用"大小写改写"而不是"字节完全相同"]` 它自己说明：字节相同会走 install 的 `ADOPT`/`IDEMPOTENT_REPLAY` **零写路径** ⇒ 不生成 `.bak`、清单不记 `original_sha256` ⇒ **自变量消失**。所以必须造成"字节确有差异、语义等价"。
`[我认可这个取舍]` 这是**为了保住自变量而做的必要设计**，不是偷懒。

## 3 · 结论的**精确范围**（这条最重要，别外溢）

`[必须连带三句]`
1. **它测的是「写了但内容等价」**（大小写改写、引擎不加载差异），**不是「写了不同内容」**。
2. 而「写了**不同内容**」的情形另有证据：**W63/W70 用 inplace 把 `[SOV1]` 指向我方 `RA2F_M1.MAP`，真机三关链贯通 + 三趟一致** ⇒ **功能层可用**。
3. ⇒ 两件事合起来才完整：
   > **inplace 写不同内容时，功能可用（W63/W70 三关链）；inplace 机制改写这个官方文件本身，不扰动行为分布（W72）。**
   但**没有任何一卡**测过「inplace 写不同内容 **之后**的行为分布是否与官方一致」—— 那个问题在方法上无法用同图对照来问（写不同内容就会玩不同图）。

`[其余两条限制（W72 自报，我采纳）]`
- **离散侧退化**：五字段全单值 ⇒ `TVD≡0`、`p≡1`、`p_method=exact_single_category_degeneracy` ⇒ **判别力全在连续量（帧时序）**，不得拿"离散 0 差异"当强度。
- **B 臂文件系统层面另多 6 个惰性产物**（maps/mix/manifest/seal/.bak）⇒ "唯一自变量"是**行为层隔离**，不是字节层绝对唯一（`DISAGREE.md` D1 已披露）。

## 4 · B 线三层论证现在齐了

| 层 | 证据 | 状态 |
|---|---|---|
| **C** 安装期零越界写入 | W62（合成）+ W65/W69/W72（真实快照） | **PASS** |
| **B（append）** 行为分布 | W69 `SAME_DISTRIBUTION`（`D_ks=0.000049`） | **未检出差异** |
| **B（inplace）** 行为分布 | **W72 `SAME_DISTRIBUTION`（`D_ks=0.000393`）** | **未检出差异** |

⇒ **现在可以说**：「我方安装机制（append 与 inplace 两种形态）在安装期零越界写入，且未检出行为分布差异 —— 在上述已声明的判据、观测量与场景范围内。」
⇒ **仍然不能说**：「B 线等价性成立」「装包对游戏无影响」。

## 5 · 一条口径教训

`[记]` W72 因为"字节相同会走零写路径"而被迫选择"语义等价的差异化改写"。这说明**在这类实验里，"给机制一个真实的写动作"和"保持内容语义不变"本身是矛盾的** —— 只能靠"等价但不同形"来两全，而这就自动把结论范围收窄到"内容等价"。
今后凡涉及"改写类机制"的等价性实验，**必须在设计阶段就把这个矛盾写出来**，而不是等结论出来再收窄。

---

## 6 · 引用订正（2026-11-14 02:25，自查）

§2 表格里「C 判据 **PASS**」的实际产物路径是：`out\audit.stdout.txt`（`c_audit_verdict {"verdict":"PASS", ... "classified": true}`）、`out\audit.exit.txt`（`AUDIT_EXIT=0`）、`out\c_audit_B_arm.json`。我口头引用时曾误称 `c_audit_verdict.json`（该文件不存在）。**结论不变**：三张卡（W65/W69/W72）的 C 判据均 PASS、退出码 0，我亲自复核过。

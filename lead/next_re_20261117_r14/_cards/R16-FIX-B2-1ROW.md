> 卡号：R16-FIX-B2-1ROW
> 角色：执行器（`work/cn:hy4flash-free`）
> 写域：`lead\next_re_20261117_r14\R16_FIX_B2_1ROW\`（新目录）
> 日期：2026-11-21（R16 第 25 轮）· **1 行**

# 任务：重修 `00473B10` 的 ④（同一根因第三次：栈临时写被当构造器装表）

## 0. 绝对边界

1. **严禁写 `COVERAGE\coverage.tsv`**。只产出 delta。
2. 只写 `R16_FIX_B2_1ROW\`。`R16_D1_WIDE_B2\` 只读。
3. 可以跑**只读**反汇编/扫描。不许编造，取不到写 `未取得`。

## 1. 审计判 FAIL 的原因（照录）

`R16_AUDIT_D1_WIDE_B2` 判 **1 行 FAIL**：`00473B10`（`CCFileClass::slot9`）。

- 上一版取的装表点 `004014AC` 指令是 **`mov dword ptr [esp + 0x20], 0x7e16b0`** —— 写**栈临时对象**，不是 `this`；
- 宿主 `004011C0` 是**一个 1729 条指令的无关函数**；随后 `lea ecx,[esp+0x20]` + `call 0x431b80` 证实该临时对象被当作 thiscall 实参；
- 该 vt **`007E16B0` 共 185 个装表点**，其中 **5 个是真 `this` 目标**：`004019A6` / `00473A12` / `00473A4F` / `00473A9B` / `00535A76` —— **全部被「最低地址命中」丢弃**；
- **审计推荐**：`site=00473A9B` / `host=00473A80`。`00473A80` 是真 `CCFileClass` 构造器（44 B）：`push esi; mov esi,ecx; call 基类ctor; mov [esi],0x7e16b0; mov eax,esi; ret`。

**根因（第三次同型）**：`derive_raw.py:160` 的 `site = es[0]` = **最低地址命中**；`generate.py:91` 的 `elif op: form = "ctor_body"` **无任何 `this`/宿主校验**。

## 2. 要做的事

### 2.1 重新定位真装表点
- 枚举 `0x7E16B0` 的**全部**写入点，逐个分类：`this` 目标（`mov [reg+0], vt` 且 reg 是 `ecx`/esi 等 this 载体）／栈临时（`[esp+...]`/`[ebp-...]`）／静态（`[abs]`）／其它。
- 对每个 `this` 目标点，判宿主是否为**真构造器**，可执行规则（自己实现并在报告写清，建议沿用/复用 `R16_FIX_B1_2ROWS\host_rule.py` 的 G1–G5）：
  - G1 非栈目标；
  - G2 目标是 `this`（`[reg+0]`，reg 为 this 载体）；
  - G3 写后**无**基类析构 `call 0x431B80`、**无** `test byte [esp+X],1` + `call 0x7C8B3D` + `ret N` 同构（scalar deleting destructor 签名）；
  - G4 前序有 `call <alloc>`（如 `0x431B20`）；
  - G5 以 `mov eax,esi; ret` 收尾。
- 取**通过 G1–G5 且宿主类与行名类 `CCFileClass` 一致**的那一处。

### 2.2 重写 `00473B10` 的 ④
- 骨架照先例；必备 `vt` / `slot` / `slot 值` / `COL` / `offset` / `RTTI`→`mangled` / **正确装表点** / **宿主** / 「entry 体外」/ **装配方式 + 实测指令**。
- 若 §2.1 的所有候选都过不了 G1–G5，如实写「取不到真构造器装表点」并记 `SKIP`，**不许编**。

### 2.3 用新规则复查 B2 全 18 行（落地防复发）
- 对 `R16_D1_WIDE_B2\delta.tsv` 全 18 行跑同一套 G1–G5 校验，报是否还有 SUSPECT 行（审计说只有 `00473B10` 一行，你核）。

## 3. 产物（`R16_FIX_B2_1ROW\`）

1. `vt16b0_sites.tsv` —— `0x7E16B0` 全部写入点：`site	insn_bytes	target_kind(this|stack|static|other)	func_start	pass_G1_G5(是/否)	host_class_evidence	note`
2. `delta.tsv` —— TAB 8 列，只放这 1 行（或 SKIP 则空）
3. `fields.tsv` —— 新旧装表点/宿主/形态对照
4. `selfcheck18.tsv` —— B2 全 18 行的 G1–G5 复查
5. `REPORT.md` —— 含写入点分类计数、5 个 `this` 目标的逐点结论、新旧对照、18 行复查结果、`coverage.tsv`/`gamemd.exe` sha、以及「只重写这 1 行、未改 grade/判定、未并表」声明

## 4. 回复里给什么

只给：`0x7E16B0` 写入点总数与分类计数、5 个 `this` 目标里几个过 G1–G5、最终选点与宿主、18 行复查有无 SUSPECT、`coverage.tsv` 是否已并表 B2、产物路径、样例 ④。**不要贴全表**。

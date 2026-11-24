# S20-KPROVED · 把 S20 的 proved 往上推（**只做真四环；D-39 型只登记不升格**）

## 盘上现态（Lead 实测，atlas∩coverage 口径；与你自己复算不符就停下报告）
`S20`：**n = 410、named = 399、proved = 40**、门槛 proved = **205** ⇒ **差 165**；其中 `[静态推断]` **359 行**。
S20 是粒子/Anim 子系统，命名完成率 97.32%，proved 仅 9.76% ⇒ 大量行可能有可用证据却从未被证。
**named 侧已达标**（399 ≥ 369）⇒ **本卡只动 grade，不动名字、不动子系统**。

## 唯一目标
从 S20 的 `[静态推断]` 行里，把**真四环齐全**的行升到 `[已证]`。**目标 40 行**（不必一次做完 165，但要交出可复用判据与清单）。

## 两类行必须分开处理（本卡纪律核心）
1. **C1 真四环 ⇒ 升 `[已证]`**。环④ 必须是下列之一：
   - **direct call**：`E8 rel32` 在**指令边界**上命中该 entry（⑭ 数 direct call 目标，禁用「最近 E8」启发式）；
   - **exact 虚派发**：`mov ecx,<global>` + `mov edx,[global]` + `call [edx+slot]`，**且该 global 的 vptr 写有实证**。
2. **C2 D-39 型 ⇒ 保持 `[静态推断]`，只登记**：①②③ 齐但环④只有「活 vptr 安装 / vt imm32 引用」、direct call = 0 且无 exact 派发。
   ⚠️ 用户尚未裁 D-39 ⇒ **裁前一律不升**。把这些行列入 `D39_CANDIDATES.tsv`（entry + ①②③ 证据 + 缺环说明），供裁决后一次性解禁。

## 三条硬禁令
- **禁 slot-baseline**：「某 slot 在已证 owner 里存在」类判据检出力 = 0（`S13-K6` 栽在这，45 行只剩 11）。
- **禁同源双计（⑰）**：体内形态 + 调用点模式同属通道 A，只计一环。
- **禁虚假申报 grade 变动**：逐行给「盘上现 grade → 交付 grade」两列。

## 强制自证
- **检出力基线**：先算「随便挑 40 个同子系统 `[静态推断]` 行，用你的判据会不会也过」。**先测基线**（本项目已 6 次栽在这）。
- **⑲ 自检**：按「操作数是否 None」筛 call 前，先打一条已知阳性 call 自检。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）——**只报不改名**。
- **⑨ 停机核验**：盘上 n/named/proved 自己重算。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\`
`PROGRESS.md`（≤60 行）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S20), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`（**只放 C1 行**）
`D39_CANDIDATES.tsv`：C2 行（不进 delta）
**每完成 3–5 行就增量落盘 PROGRESS.md。**

## 核心数字（给审计员复算）
① C1 升 `[已证]` 行数 ② C2 登记行数 ③ 检出力基线误命中数 ④ 逐行 grade 对照 ⑤ 并入后 S20 proved 实测值
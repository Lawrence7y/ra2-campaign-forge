# S13-K12 · 把 survey 判定的 **17 行 C1（真四环）** 升 `[已证]`（**不依赖 D-39**）

## 为什么是这 17 行
`SURVEY-D39`（只读测量卡，已由 Lead 逐格复现 classification.tsv）把 S13 的 129 行 `[静态推断]` 分成：
**C1 真四环 17 行 / C2 D-39 型 36 行 / C4 缺③语义 76 行**。
- **C1 的环④是真 direct call 或 exact 虚派发** ⇒ **不需要 D-39 裁决**，现在就能升。
- 升完 S13 proved 86 → **103**（门槛 120，仍差 17）。这 17 行是**无争议的净收益**，也是 S13 达标的第一段。
- ⚠️ C2 那 36 行**一律不碰**（D-39 未裁）。

## 唯一任务
从 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_D39\EVIDENCE\classification.tsv` 里取出 **subsystem=S13 且 class=C1** 的 **17 行**（自己按该文件筛，**行数以文件为准**；若不是 17 行就停下报告），
对每行**独立重新取证四环**并交 `coverage_delta.tsv`。**只这 17 行，多一行都不许。**

## 每行必须给（四环，缺一即不可升）
- **① 入口**：16 B 对齐 + 首字节非 `E8/E9/EB` + 前驱非 fall-through + 合法序言或叶函数形态。
- **② 类属**：`[vt-4]=COL → [COL+0xC]=TD → 名在 TD+8 内联串`；读不到 **fail-closed 停下，不许猜**。
- **③ 语义**：体内字节合同（读什么 / 写什么 / 返回什么 / 调用约定），给**指令偏移**。
- **④ 外部见证**（本卡的正当性来源，**必须逐行给站点地址**）：
  - `direct call`：`E8 rel32` 在**指令边界**上、目标 == 该 entry、**调用者 ≠ 本行自身**（防自环）；
  - 或 `exact 虚派发`：`mov ecx,<global>` + `mov edx,[global]` + `call [edx+slot]`，**且该 global 的 vptr 写有实证**（给写点地址），**且槽值确实 == 该 entry**（⑭：不是「global 有 vptr 写」就算）。

## 强制自证（这些数字审计会照打）
- **检出力基线**：用你最终采用的判据，随机抽同子系统 17 行跑一遍，报误命中数。**先测基线**。
  ⚠️ 已知参考：`S20-KPROVED` 同类判据自报 **8/40 = 20%**；`SURVEY-D39` 报 C2 判据全局命中率 **15/100 = 15%**。**你的基线若也在这个量级，必须解释为什么这 17 行仍可信**（例：exact 派发要求槽值==entry，特异度更高）。
- **⑲ 自检**：按「操作数是否 None」筛 call 前，先打一条已知阳性 call（`0x4386AB` 的 `call dword ptr [edx+0x10]`）自检。**注意：capstone 5.0.7 的 x86 操作数上，无 index 的 mem 操作数 `mem.index` 返回 0 而非 None**（本项目 ⑲ 号的根因）。
- **⑱ 按 entry 地址查全库冲突**（`docs\re\` + `re_atlas\kb\` + 台账 + `COVERAGE\`）——只报不改名。
- **⑨ 停机核验**：盘上 S13 n=240 / named=216 / proved=86 自己重算，不符即停下报告。
- **禁 slot-baseline**（「某 slot 在已证 owner 里存在」类判据检出力 = 0）；**禁同源双计（⑰）**。
- **不动名字、不动 subsystem**（D-37 未裁）；**严禁碰 `00773030`**。

## 交付（绝对路径，只写这里）
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K12\`
`PROGRESS.md`（≤50 行）/ `UNKNOWNS.md` / `DISAGREE.md` / `EVIDENCE\` / `work\`
`coverage_delta.tsv`：8 列 `entry, subsystem(S13), name, one_line_semantics, grade, evidence_path, name_kind, 旧grade→新grade`
**每完成 3 行就增量落盘 PROGRESS.md。严禁建 venv / pip install。**

## 核心数字（给审计员复算）
① 17 行逐行 ④ 站点地址（direct call 或 exact：global+slot+写点）② 检出力基线误命中数 ③ 逐行 grade 对照 ④ 并入后 S13 proved 实测值
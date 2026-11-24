# S03-C6 · UNKNOWNS

## U1 · 0065D240 `RawFileClass::slot15`（盘上名 CDFileClass::slot15）— ③ 环不成立，不进 delta

- **② 环成立**：全表枚举见 `EVIDENCE/rtti_all_tables.json#0065D240` —— 3 张表同 slot 15：`vt=0x7E1668/.?AVCDFileClass@@`、`vt=0x7E3A2C/.?AVBufferIOFileClass@@`、`vt=0x7F0904/.?AVRawFileClass@@`，COL/TD 三链全读通，`vt[15]==0x0065D240`；occ=3 / pairs=3 / slots=[15]，P3 表长约束后无伪对。按 M1/错源⑯ 归基类 RawFileClass。
- **④ 环成立**：direct 站点 `0x473F14`（capstone 边界扫 + 原始 E8 复核双通道一致，`EVIDENCE/direct_sites_card8.json`）。
- **① 环成立**：E8 直调入口、16B 对齐。
- **③ 环不成立**：逐条打完入口到 ret（入口相对偏移，见 `EVIDENCE/dis/0065D240.txt`）：
  - `+0x09 cmp eax,[esi+0x14]` 后 `cmp eax,-1` / `+0x0C je 0x65D29C`；
  - `+0x14 call [0x7E1128]`(GetFileInformationByHandle) / `+0x1C je 0x65D29C`；
  - `+0x2C call [0x7E1130]`(DosDateTimeToFileTime) / `+0x34 je 0x65D29C`；
  - `+0x49 call [0x7E112C]`(SetFileTime) / `+0x4F neg` / `+0x51 sbb` / `+0x54 neg` 归一为布尔；
  - 三道闸 **全部汇入同一目标 `0x65D29C`：`xor al,al; ret 4`**，各闸动作相同（返回 false），仅参数/前置调用不同。
  - D-42 细则#1 要求「≥3 道互斥闸且各闸动作不同」；本行三闸动作一致（汇入同一返回点），M4 明写「仅参数不同、汇入同一 call 不算」。无跳表、无回边循环、无 GetLastError/-1 可证伪错误码返回约定、无 ≥10 字段形状断言 ⇒ ③a（机械可述），留 `[静态推断]`。
- **处置**：与 C5 的 00431F10/00473AE0/0047AF10 同型（③a 不进 delta）。本卡 8 行中四环齐全 7 行，delta 7 行。

## U2 · ③b 基线池口径（非缺口，记录以免误读）

- 随机基线池 N=97 = 当前盘上 `COVERAGE\coverage.tsv` 的 S03 ∧ `[静态推断]` ∧ 在 `SURVEY_RING24\EVIDENCE\classification.tsv` 有 CFG extent 的行。C5 卡记 N=102 系当时截面；两次均随 coverage 变化，互不覆盖。见 `EVIDENCE/baselines.json`。
- ③b 基率（seed 20261119，2000 次无放回取 8）：loose p=34/97=0.350515、E[8]=2.804124、MC 实测 2.7545；strict p=18/97=0.185567、E[8]=1.484536、MC 实测 1.4615。`K=行数×均值=8×p` 是恒等式，不作校验；「②∧④ 入选率」未计入基线（M3）。

# S16-PADD · DISAGREE

## D1 · 与 D-39「虚函数第四环」潜在口径冲突（如实登记，不申辩扩权）
- 本卡 3 行均为虚函数，direct call 全 0（scan_direct.py 全 .text E8/E9 扫描确认）。D-39 指出虚函数的 ③（体内合同）与 ④（体外 VT 引用）在「VT imm32 引用」口径下物理同源 ⇒ 有效环数 3。
- 本卡主张 ④ 是 **exact 活 vtable 派发**（构造器装活表 + vt[slot]==entry + 写点在行外 + site 不共用），强度高于被 D-39 默认按住的 S13_K8「VT imm32 引用」18 行；与 M32 保留 13 行、S13_K9 白名单 11 行（其 ④ 同为 exact 虚派发绑定）同口径。
- 若 Lead/审计裁 D-39(B) 严格四环虚函数永不可证：本卡 3 行应整体退回 `[静态推断]`，proved 46→46。此结果不变本卡其余取证事实。不争辩、接受裁决。

## D2 · 不采纳「3b 基率低即可升格」的反向推断
- 本卡 ③b 基率 p=0.4054（15/37），不低。故本卡不声称「③b 判别力强」。升级理由是逐行四环 + 结论本身的字节证据（E_POINTER 常量、jl 负值透传、4-vptr 写、RTTI 链），非统计显著性。

## D3 · 不采纳 docs/re 作为 named 第二通道
- §8.5 主条明禁 `docs\re\`/台账作名字异源通道。`0065E660` 的 `SpawnAircraftEdge` 仅见于 docs/re 且归属冲突，本卡不采纳；与 S16_N2 一致。

## D4 · grade 逐行盘上→交付对照（不虚报「未动」）
| entry | 盘上现 grade | 交付 grade | 说明 |
|---|---|---|---|
| 006CDEB0 | [静态推断] | [已证] | 四环补齐（③b + exact 活 vtable ④）|
| 006CE7C0 | [静态推断] | [已证] | 同上 |
| 006CE800 | [静态推断] | [已证] | 同上 |
- proved 前后各算一次：46 → 49（+3）；未声称「未动 proved」。

## D5 · 子系统和 name 均保持盘上原值
- 三行 subsystem 仍 S16、name 仍盘上 slotN 占位名（D-38 未裁，不在本卡改 named 口径），只改第 4 列语义与第 5 列 grade。② 栏类名（EVIDENCE）与 name 前缀逐行一致（判据 2 ✓）。

## D6 · 未触碰的禁区
- 未改 `coverage.tsv`、台账、R14_COMMON.md、STATUS_BOARD.md、`ra2youli\`、其它卡目录、`_audit\`；未建 venv、未 pip install、未 git commit。

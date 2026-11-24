# S16-K2 DISAGREE（与本卡引用材料的冲突记录）

| # | 冲突对象 | 本卡实测 | 处理 |
|---|---|---|---|
| D1 | 用户派卡文与 PANEL 的「S16 atlas 90 / named 73 / proved 42」 | `python work/t1_filter.py` 实测：atlas 内 S16=**90**、named(strict, 非 `sub_XXXXXXXX`)=**73**、[已证]=**42**；全 coverage S16=**92**（多 0x004F8440/0x004F9370，均 atlas 外且已 named+proved）。 | **无 DISAGREE**：与 PANEL 完全吻合。仅补报「全 coverage 92」第二口径（派卡文只给了 atlas 口径）。 |
| D2 | `S16-K1\PROGRESS.md` 第 8 行「SWType GetSize v[11]=`0x6CE900`」 vs `S16-K1\_audit\VERDICT.md` §8-⑨ | VERDICT 实测两类 GetSize **同在 v[12]**；SWType v[11]=`0x6CE8F0`→`0x20`（WhatAmI 旁），v[12]=`0x6CE900`→`0x100`；K1 PROGRESS 的「v[11]」是假更正。 | 本卡遵 §943 已入账结论（GetSize 0x80/0x100 吻合），槽位细节**不重开**；本卡 E01 仅复用 v[12] 值（SuperClass v[12]=0x6CE210、SWType v[12]=0x6CE900），与 VERDICT 一致。引用节号：`S16-K1\_audit\VERDICT.md` §8-⑨、`R14_COMMON.md` §8.2 技术②。 |
| D3 | PANEL line 5 / line 50「M2 并表后 `[已证]`=1,125（atlas 内 1,121）」 vs `R14_COMMON.md` §7 / `coverage_README.md`「`[已证]`=1,022」 | 两值为不同版次截面：1,022 是 M1-FIX7 降级后（R14_COMMON §7 记录点），1,125 是 M2 并表后（PANEL 抬头）。本卡不裁全局值。 | **不冲突，版次口径不同**。本卡只用 S16 子集实测（42→46），不引用全局 `[已证]` 值。 |
| D4 | `docs/re/superweapon_re.md` §2 表「SuperClass v[13]=CalculateChecksum」 vs `S16-K1\PROGRESS.md` DISAGREE「v[12]=GetSize/v[13]=Checksum 需改」 | 本卡 E01 实测 v[12]=0x6CE210(GetSize)、v[13]=0x6CE020(CalculateChecksum)，与 superweapon_re.md §2 表及 VERDICT §8-⑨ 一致。 | 采 RTTI+槽位字节实测；与已入账 §943 不矛盾（§943 只入账值 0x80/0x100，不争槽号）。 |

## 纪律自检

- 未写主台账、未改游戏文件、未改 `COVERAGE\coverage.tsv`、未 git commit/push。
- 未用 `vtables_v2.json`；虚表定界从 `.rdata` COL/`vtable[-4]` 做（E01）。
- 4 条 [已证] 无一条靠字段偏移或 `call [reg+disp]` 计数；类名只认 RTTI TD（COL+0xC→TD+8，读不到 fail-closed）。
- 写「N/N」前先测基线：T1 实测 90/73/42 与 PANEL 吻合后才算缺口；未把「不在 atlas 内」当函数；未用「最近 E8/E9 目标」启发式。

# DIFF vs a-S03-K2 and a-S03-K2R

## 对 a-S03-K2 / 执行员两轮的 15W/9R

结论：漏 8W/3R。差集逐行在 SITES.tsv 标为 MISSED_BY_15W9R / VSLOT12_MISSED_BY_15W9R。

| 组 | 站点 | 差 |
|---|---|---|
| vtable 槽12 0x432050 | 0x432090 R; 0x432107 W; 0x43212A W; 0x432202 W; 0x432225 W | 4W/1R |
| 第二 vptr writer 0x431A30 | 0x431A69 W; 0x431A9A R | 1W/1R |
| BufferIO helpers | 0x431D4E W; 0x431D68 W; 0x431DBD W; 0x431DD3 R | 3W/1R |

## 对 a-S03-K2R 审计的 19W/10R

结论：它对槽12 的判断正确，但停在 strict vtable 方法集，少 4W/2R。它的 a14_counts.json 自己已有 wide=23W/12R，却最终报 strict=19W/10R，内部不一致。

| 站点 | 审计19是否含 | 本卡 | 理由 |
|---|---|---|---|
| 0x431A69 W / 0x431A9A R | 否 | 计入 | 0x431A8A 写 vptr 0x7E3A2C，明确 BufferIO 对象 |
| 0x431D4E W / 0x431D68 W | 否 | 计入 | 0x431BC0 CFG 内，esi=ecx，调用 RawFile 虚槽并操作 BufferIO 布局 |
| 0x431DBD W / 0x431DD3 R | 否 | 计入 | 0x431D90/0x431DD0 同样使用 BufferIO 对象布局 |

## 三组被点名站点

- 槽12 0x432050：第三份对。RTTI 链和槽号已复核，5 个站点全部计入。
- 0x65CBC1：第三份错。实测为 RawFileClass vtable slot 7 0x65CB50 体内的 +0x14 写，不是 +0x29。
- 0x65CB26：第三份错。实测为 RawFileClass vtable slot 2 0x65CAC0 体内的 +0x20 写，不是 +0x29。

## 形式与定界

绝对形式 0 是空判据（0x00-0x60 全 0），不作为漏报证据。两种边界法差异见 EVIDENCE/BOUNDARY_DIFF_SITES.txt；差异来自线性分区把 jcc 分支尾切成新段，CFG 将其归回原函数。

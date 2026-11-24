# S06-K4 DISAGREE

## D1 派卡数字 vs 盘上现值
- 派卡写“约 103/848”；本卡自算：coverage S06=848、∩atlas=848、`[已证]`=103、`[静态推断]`=287、`[未证]`=458、named_L=384。与 `COVERAGE/PANEL.md` S06 行一致，按纪律 9 未调整口径。

## D2 与 S06-K3 的差异
- S06-K3 报 S06 proved 103->104（0x721A50）；本卡盘上 coverage 仍为 103（未含该 delta 或口径不同）。本卡只以盘上 coverage.tsv 为基线，不把未合入 delta 计入现值。

## D3 方法学遵循
- 22 行 B8/C3 升级均非“槽值直指即语义”：WhatAmI 同时要求 enum 值、RTTI 名、canonical off0 slot11、构造器写 vptr，并用 slot12 的对象大小闭合排除 v[11]/v[12] 同形取错槽；GetSize 要求 `B8 imm32 C3` 与 factory/allocation `push size` 双点闭合。
- 1 行行为级升级 `00483710` 依据函数体字节、门控常量、字段读点和被调函数实参，不依赖其虚表归属或弱信号名。
- delta 的 name 从 `Class::slotN` / `sub_` 改为行为名；占位名规则下不得反向视为语义证据。

## D4 卫生
- 未改 `ra2youli/gamemd.exe`、未写台账、未改 `COVERAGE/coverage.tsv`、未 git commit、未启动真机、未用 Ghidra。

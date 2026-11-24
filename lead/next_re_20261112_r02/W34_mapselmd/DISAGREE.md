# W34 · DISAGREE（与既有卡片的差异 / 更正）

> 全部为**纯离线复核**结果；每条给出本卡证据位置与等级。不影响 W33 的**主结论**（两条推进路径都要 `MAPSELMD.INI` 认识我方地图；仅改 `SkipMapSelect` 或仅打包 MIX 都不修），但会影响**后续卡片如何引用细节**。

---

## D1 · 「`0xFBE0D09D` 是 MAPSELMD.INI 的加密/异或 id」——不成立

**W33 卡面**：「W33 的日志显示该条目在表里的**存储 id 是 `0xFBE0D09D`**（不是 crc32）⇒ 条目表有加密或异或处理，直接扫 id 行不通」；「Lead 已试过裸字节搜 `0x922B8CE7` LE 搜不到 ⇒ 条目表有加密或异或处理」。

**本卡复核** `[本次实测]`（`EVIDENCE/step1_extract_mapsel.py`，32/32 PASS，exit 0）：

| 事实 | 证据 |
|---|---|
| `mixlib.MixFile("ra2md.mix").get("MAPSELMD.INI") -> None` | step1 §1（复现成功） |
| 全文件流式裸搜 `0x922B8CE7` LE = **0 命中** | step1 §1（复现成功） |
| `ra2md.mix` 头 `00 00 03 00`：`flags=0x3`，**bit1=加密** → 条目表 Blowfish 加密（W29 §1.3 `0x5B3CED..0x5B3D11`） | step1 §2 |
| `0xFBE0D09D == mixlib.ts_crc_hash("LOCALMD.MIX")`，而 `crc32("LOCALMD.MIX")=0x3BF6887A` | step1 §0 |
| 该 id 是 **ra2md.mix 顶层的嵌套容器 `LOCALMD.MIX`**（4,819,480 B，自身头也 `flags=0x3`，187 条目） | step1 §2 |
| `MAPSELMD.INI` 在这**第二级 MIX** 内，id = 普通 `crc32("MAPSELMD.INI")=0x922B8CE7`，size 5,573 | step1 §2 |
| W33 `step10_close_gaps.stdout.txt` 的 `FOUND: ra2md.mix :: id=0xFBE0D09D :: MAPSELMD.INI (id=0x922B8CE7, size=5573)` 其实是**递归路径标签**：`:: id=0xFBE0D09D ::` 来自 `sub_name = target_ids.get(hid, f"id=0x{hid:08X}")`，即容器名未解析，不是文件 id | `[转引]` W33 脚本第 55 行 + 本卡复算 |

**结论**：`0xFBE0D09D` 与 `MAPSELMD.INI` **不是同一个条目**；它是容器 `LOCALMD.MIX` 的 id，且用的是 **TS 4 字节尾部填充哈希**而非普通 crc32。裸搜失败是「两级加密头 + 文件在二级 MIX 内」共同造成，**不是 id 被异或**。「不要依赖 `get()`，自己解码条目表并递归定位」这条**操作建议仍然正确**，本卡照做（独立实现 `parse_mix_bytes` / `find_in_mix`）。

> 对后续卡片的影响：不要写成「MAPSELMD.INI 的 id 是 0xFBE0D09D / 条目表有异或」；应写成「`ra2md.mix` 里 `MAPSELMD.INI` 位于嵌套 `LOCALMD.MIX`（id `0xFBE0D09D` = `ts_crc_hash`），自身 id `0x922B8CE7` = `crc32`」。

---

## D2 · 「比对前统一转大写」——方向反了

**W33**（`NEXTSCENARIO_FLOW.md` §2 问题 2、§3 链路 3）：「将候选子项的 `Scenario=` 字段与传入的 `NextScenario` **统一转大写**后做字符串相等比对（`0x005AE073 call 0x7b4780`）」。

**本卡复核** `[本次读码]`（`EVIDENCE/step3_disasm_stage.py`，D2e/D2e2/D2f PASS）：

- `0x7B5B30` 逐字节 `cmp dl,0x41` / `cmp dl,0x5a`，只对 `'A'..'Z'` 调 `0x7CAFF4`；
- `0x7CAFF4` 对 `'A'..'Z'` 执行 `add eax,0x20` ⇒ **tolower（转小写）**；
- `0x7B4780` 函数体内**零 `call`**，是大小写敏感的逐字节比较。

⇒ 归一化是**转小写**，不是转大写。**但「值比对大小写不敏感」这一结论仍然成立**（两边都先归一化）。`0x005CF6B0` / `0x005CF760` 两个查找函数内 `0x7B5B30` 各 2 次、`0x7B4780` 各 1 次；`0x005ADF20` 内各 1 次。

> 注意不要与 W29 §1.2 的 `0x7DCFC4`（`MixFileClass::Find` 里 `strupr`，`sub cl,0x20` 小写→大写）混淆：那是 **MIX 文件名哈希**路径，与 MAPSELMD 值比对是两个不同函数。

---

## D3 · `0x005CF6B0` 的语义与「`N=名字` 是下一阶段」

**W33**：「循环该阶段在 `MAPSELMD.INI` 中的**候选子项（`0x005AE032 call 0x5cf6b0`）**」；官方结构简写为 `[ALL01] Scenario=ALL01umd.MAP   2=ALL02`，易读成「`2=` 的值就是下一关」。

**本卡复核** `[本次读码]`：

- `0x005CF6B0` **不是枚举器**，它是「在全部阶段里按**阶段名**（`[stage+0]`）查找」；`0x005CF760` 才是按 `Scenario=`（`[stage+4]`，`0x005CF799 add ecx,4`）查找。
- 真正的子项枚举在 `0x005ADF20`：`[stage+0x58]` 子项字符串数组 / `[stage+0x64]` 计数（`0x005AE018/025/028`）。每个子项是**阶段名字符串**，交给 `0x005CF6B0` 解析成阶段对象，再取 `[esi+4]`（该阶段的 `Scenario=`）与 `NextScenario` 比对。
- 数字键在 `MapStage` 构造中被 `0x005CFFF1/0x005CFFF5` 存成 **1 字节的 ClickMap 颜色索引**；循环 `0..255`（`0x005D0037 cmp eax,0x100`）。官方注释 `;index color is the # above, that's how it chooses the next map` 即此意。
- ⇒ `N=名字` 形式上是「颜色 N 的点击区域 → 名为 `名字` 的候选子阶段」，**不是 `.MAP` 文件名、也不是 `NextScenario` 的值**。官方线性战役中 `N` 恰等于下一阶段的阵营序号，属数据巧合。

> 实现影响：v11 追加阶段的 `2=<下一阶段段名>` 必须是**段名**；若误写成 `2=MS02.MAP`，`0x005CF6B0` 查不到该阶段，`SkipMapSelect=yes` 路径必然弹窗。

---

## D4 · 官方文件「简写结构」不足以作为生成模板

**W33** 给出的官方结构：
```
[GDI] 1=ALL01 … 7=ALL07     [Nod] 1=Sov01 … 7=Sov07
[ALL01] Scenario=ALL01umd.MAP   2=ALL02
… [Sov07] Scenario=sov07tmd.MAP
```

**本卡实测** `[本次实测]`（`EVIDENCE/MAPSELMD.OFFICIAL.INI` 全文 5,573 B）：官方共 **20 个段**，除上述外还有 `[ALL00]`（含 `1=ALL01`）、`[Anims]`、`[GDISFX]`、`[NODSFX]`；每个阶段段有 `Scenario / Description / VoiceOver / MapVQ / Overlays / Targets / ClickMap` 共 7 类字段；`[GDI]`/`[Nod]` 还有 `Anims=` / `Sounds=`。加载器 `0x005CEEF0` **确实读** `'Anims'` / `'Sounds'` / `'TextRect'` / `'Palette'`（`0x005CF0E5 / 0x005CF13C / 0x005CF25E / 0x005CF403`）。

⇒ 按简写结构生成「只含我方条目」的最小文件不仅丢官方战役，还会丢 UI 配置段。这正是 W34 硬性规则「必须克隆官方文件再追加」的字节级依据（与 W29 关于完整 CSF 的警告同类）。**不是反驳 W33，而是补全其省略**。

---

## D5 · `CCFileClass` vtable 槽位命名不一致（仅术语，不影响结论）

**W33**（`NEXTSCENARIO_FLOW.md` §2 问题 2 / §3 链路 4）：「虚表 `0x007E16B0` 的 `+0x1C` 即 `0x00473D10`（**`CCFileClass::Open`**），`+0x14` 即 `0x00473C50`（**`CCFileClass::Is_Available`**）」。
**W29**（§1.1 / §1.4）：「`+0x1C = 0x473D10` = **`Get_File`（取数主路径，磁盘优先）**；`+0x14 = 0x473C50` = **`Open`（先 MIX 存在性探测，再磁盘）**」，并专门警告「若只盯 `Open` 会得出 MIX 优先的相反结论」。

**本卡复核** `[本次实测]`（`sandbox/probe_vtable.py`）：`0x7E16B0+0x14 = 0x00473C50`、`+0x1C = 0x00473D10`，**槽位字节与两卡完全一致**；差异只是函数命名。W29 的命名与其控制流证据（磁盘优先取数 / MIX 只做可用性探测）自洽，本卡采用 W29 命名。两卡对「真正取数时磁盘优先」的结论一致，故 **W33 主结论不受影响**。

---

## D6 · 与 W29 无实质分歧，但需记住两个边界

- W29 Q1「散装优先」定谳的是**分支顺序**；端到端（散装 `MAPSELMD.INI` 真被采用、战役真的推进）仍是 `[待运行验证]` `[转引]`。本卡不宣称已修复。
- W29 §1.4 的 `Open`/`Get_File` 顺序相反陷阱依旧成立；W33 的 `Start_Scenario` 链路引用未触发该陷阱（结论是磁盘优先）。

---

## D7 · 与 W30 的接线差异（非分歧，是新增）

W30 `CSF_CAPABILITY.md` §4 明确「本卡未修改 `install.py` 的安装清单逻辑，不会把 `ra2md.csf` 自动复制进游戏目录」。W34 **不同**：`MAPSELMD.INI` 是通关推进的硬依赖，必须纳入 `package_files()`、清单、备份与卸载还原，并对**已存在的非我方 `MAPSELMD.INI`** 做默认拒绝的 definite conflict（且 `--allow-content-conflict` 也不释放）。`[本次实测]`（MS5/MS6，51/51 回归 PASS）。

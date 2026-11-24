# S09-KPROVED6 · DISAGREE

## D1 · 不采纳「②∧④ 入选率」作基线（遵 §8.7 判据 4）

- 本卡核心基线按 D-42 报 ③b 基率（strict 0.171994 / loose 0.231355，池 N=657，seed 20261119，2000 次），不报「随机 8 行是否 ②∧④」——后者即 S09 A 集合入选谓词本身（A=103=②RTTI∧④严格），对「四环」结论零鉴别力。`COVERAGE\PANEL.md` 与 a-S09-KPROVED2 审计已就此定论。

## D2 · 不把 `K=N·p` / `E[8]=8p` 当校验（遵 §8.7 判据 3）

- strict 8×0.171994=1.375951 与 MC 1.358500 的近邻关系是恒等式使然，不作证据；真正校验是 MC 与 p 的一致性（1.3585 vs 1.376，差 1.3%）。

## D3 · 2 行细则#1 级边际按现行口径计入，但保留严格口径敏感性（遵 §8.7 判据 6）

- `0069DE00`/`005576A0` 的 ③b① 靠 D-42 细则#1（≥3 互斥闸各动作不同），非跳表/循环/错误码/形状断言。遵细则#1 计入 ③b，delta 第 4 列明标「【细则#1级】」。若审计只认四硬档，四环齐全数 8→6；本卡不隐瞒该风险（见 UNKNOWNS U1）。
- 与已否的 `0069DEB0`（五模式全部汇入同一 call 4AED70、仅参数不同）界线：本卡两行的多闸写目标/被调目标互异，非「仅参数不同汇入同一 call」。

## D4 · ② 类名按 ⑯ 归基类，与盘上占位名不同（遵 §8.7 判据 1/2）

- 4 行盘上名是派生类占位名，本卡按全表枚举归共同基类并据此写 name 栏：004F4240 MouseClass::slot0→GScreenClass::slot0（9 表）、0056BBE0 MouseClass::slot27→MapClass::slot27（8 表）、00656AC0 PowerClass::slot31→RadarClass::slot31（2 表）、006A5030 TabClass::slot7→SidebarClass::slot7（3 表）。② 栏类名与 name 栏逐字一致（M2），非「只引单表断言类名不符」（判据 1 反例）。
- 继承链（YRpp 实测）：GScreenClass→MapClass→DisplayClass→RadarClass→PowerClass→SidebarClass→TabClass→ScrollClass→MouseClass；2 表以上同 slot 取最上共同基类。

## D5 · grade 只升第 5 列，name/one_line_semantics 按本卡契约改写

- 本卡 8 行 grade 均 `[静态推断]`→`[已证]`；第 4 列语义按本卡修正契约写 ③b 整体合同（类名+槽位+子系统保留、替换占位模板、含四要素、无「未证/未定/弱信号/线索」）；第 3 列 name 按 D4 归基类。不写 COVERAGE\、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli\、其它卡目录；由合并员串行并表。

## D6 · 004F4240 的 ④ 是构造器活 vtable，非 atexit 死表（遵纪律 10 / 错源㉓）

- survey `installs` 记的 install_site=0x40D1B2 落在 atexit 析构器 0x40D1B0 内（`push 0x40D1B0; call 0x7C978A` @0x40D19A），是死表写；但构造器 0x5BDA40（0x40D195 `mov ecx,0x87F7E8; call` 调用）在 +0x0A/0x5BDA4A 以 `mov [esi],0x7E1964` 装同一活 vptr。按「活表=构造器写」取 0x5BDA4A，环④成立；若误取 0x40D1B2 会错判死表，特此登记。

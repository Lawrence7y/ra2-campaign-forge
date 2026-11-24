# S09-KPROVED7 DISAGREE

## D1 · ②/name 栏类名与盘上不一致（4 行，按错源⑯归基类级）
盘上 coverage.tsv 的 name 栏是「最派生持有类」，但 §8.1 错源⑯ 与 §8.7 判据1 要求「≥2 张表同 slot 归基类级、②栏类名与 name 栏一致」。故下列 4 行把 name 栏与语义首句类名改为全表枚举后的**共同基类**（该类 vtable 自身确实在同槽持有该 entry，逐表核对如下），盘上原名保留在此备查：

| entry | 盘上 name | 本卡 name（共同基类） | 字节核对（基类 vt[slot]==entry） |
|---|---|---|---|
| 004F4450 | MouseClass::slot13 | GScreenClass::slot13 | vt 0x7ea6fc slot13 == 0x4f4450 ✅ |
| 00557AC0 | ColorListClass::slot40 | ListClass::slot40 | vt 0x7ed10c slot40 == 0x557ac0 ✅ |
| 00557AE0 | ColorListClass::slot39 | ListClass::slot39 | vt 0x7ed10c slot39 == 0x557ae0 ✅ |
| 004E19F0 | CheckListClass::slot22 | GadgetClass::slot22 | vt 0x7e92bc slot22 == 0x4e19f0 ✅ |

这 4 行**不是**改判归属争议，而是 M1/错源⑯ 的机械要求：004F4450 同槽 9 张 UI 表(Gadget 家族)、00557AC0/00557AE0 同槽 ColorList+List 两表、004E19F0 同槽 20 张 Gadget 族表。与 KPROVED3/4/5/6 的同类改名（例：S09_KPROVED3 004A9840 TabClass→DisplayClass）做法一致。

## D2 · 「保留盘上前半句类名」与错源⑯ 的冲突取舍
交付契约要求「保留盘上前半句的类名 + 虚表槽位 + 子系统描述」。对 D1 的 4 行，盘上前半句类名恰是「最派生持有类」，与错源⑯「归基类级、②栏与 name 栏一致」冲突。本卡取舍：**槽号、槽字节偏移、子系统描述逐字保留盘上**（例 004F4450 仍写「虚表槽 13(+0x34)：UI/侧栏/菜单/对话框/输入/命令派发」），仅把类名替换为经字节核对的共同基类，以同时满足契约的「保留前半句结构」与 §8.7 判据2（②栏类名==name 栏类名）。若审计要求盘上类名逐字不动，则这 4 行应整行退回 UNKNOWNS（四环齐全数随之 8→4），本卡据此预先声明该敏感性。

## D3 · ③b 基率取「全 103 A 行抽样」而非「②∧④入选率」
§8.7 判据4 明确：随机基线不得用「随机 8 行是否 ②∧④」（那就是 A 集合入选谓词本身），须报 ③b 基率。本卡按 D-42 两档操作化，在 S09 A 集合 103 行上 seed 20261119、N=8、2000 次抽样：strict 0.5083、loose 0.7464。「K=行数×均值」是恒等式(E[N]=8p)，按判据3 不作校验。

## D4 · 0048E5A0 依赖 D-42 细则#1（标「级边际」）
0048E5A0 ③b① 的多闸动作：清0 / 置0x80 / 置0x40 / 两种相异调用 `[vptr+0x4c]` 与 `0x4e1530`。三道以上互斥闸且**被调目标与写目标互异**，非「汇入同一 call 仅参数不同」（对照 0069DEB0 被否）。但敏感性：若审计只认跳表/硬循环/错误码/形状断言四硬档，则本行③b不成立，四环齐全数 8→7。已在 PROGRESS/UNKNOWNS 明示。

## D5 · 未主张 ③b④ 完整循环
本卡 8 行无一行以「完整循环」为③b依据（0048E5A0 是位掩码多闸，非循环）。候选池里唯一有真循环的 006A5BF0 因「循环体只 call、推进只在寄存器 esi」按 M7 剔除。故无 0045A640 TIEBREAK 类风险。

## D6 · 未改 grade 之外的任何盘面
本卡只交 coverage_delta.tsv（8 行 [已证]）。未改 coverage.tsv、CONFLICTS、台账、STATUS_BOARD、R14_COMMON、ra2youli\、其它卡目录、_audit\。未做真机、未 git commit、未建 venv 或 pip install。

# R113-EXEC-CENSUS — 独立复核 R113 的四项数字（只读，不得改任何文件）

## 你要做的只有一件事
用你自己的脚本重新数出下面 6 个数字，逐条给"我算出 X，与卡面 Y 一致/不一致"。
**不要相信卡面的数字，也不要去读 _r113 下的 JSON 当答案**——先自己算，再对。

## 环境（严格照做）
- 镜像：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- sha256 必须先是 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- ImageBase 0x400000；.text=[0x401000,0x7E038D)；.rdata=[0x7E1000,0x811074)
- 可用：python3 + capstone + pefile；**也可用 i686-w64-mingw32-objdump**（推荐换用它，
  因为出题方用的就是 capstone，换解码器才能验出"是不是反汇编器的产物"）
- 禁：pip install；禁改任何文件（只写你自己的 out 目录 /tmp/r113exec/）

## 要复算的 6 项

### Q1 vtable 普查（判据：某 dword 的值 v，若 v-4 处是"合法 COL"，则 v 是 vtable 起点）
"合法 COL" 由你自定义，但必须至少含：COL+0x00==0、COL+0x0C 指向的名字以 .?A 开头、
COL+0x10 指向的 CHD 里 CHD+0x08 在 1..96、BCD 数组每项的名字都以 .?A 开头。
问：全 .rdata 里这样的 vtable 有几个？其中有多少个出现在
out/reverse/symbols.json 的 vtable_va 集合里？差集有几个？

### Q2 反控：零假设
若判据改成"任何值落在 .text 的 .rdata dword 槽都算 vtable 起点"，候选有多少个？
这批评出来几个真正在 symbols.json 里的？精确率各是多少？

### Q3 三把槽数尺子的关系
对 Q1 的每个 vtable 算三个数：
  T = 从 vtable 起连续落在 .text 的 dword 个数
  B = (下一个 vtable 起点 - 本 vtable 起点)/4
问：T 大于 B 的情况有几个？T 的最大值是多少？B 的最大值是多少？

### Q4 CHD 分组自洽
把 Q1 的 vtable 按其 COL+0x10（CHD 地址）分组。
问：同一组内各 COL 的 COL+0x04（offset）是否互不相同？
这些 offset 是否都出现在该 CHD 的 BCD 数组的 mdisp（BCD+0x08）集合里？违例几组？

### Q5 共享 QI 体 0x55A9B0 与 thunk 0x4D0510
反汇编 0x55A9B0 起 200 字节，按出现顺序列出所有被 mov 进 edi 的 32 位立即数。
再反汇编 0x4D0510 起 8 字节，读出第一个 sub 类指令的立即数。
问：这两个数字各是多少？

### Q6 12 个 Locomotion 类的 ILocomotion 子对象偏移
对下列 12 个类，从其 RTTI 的 base class array 里找出名为 ILocomotion 的那一项，
读出它的 mdisp（BCD+0x08）：
DriveLocomotionClass, DropPodLocomotionClass, FlyLocomotionClass, HoverLocomotionClass,
JumpjetLocomotionClass, LocomotionClass, MechLocomotionClass, RocketLocomotionClass,
ShipLocomotionClass, TeleportLocomotionClass, TunnelLocomotionClass, WalkLocomotionClass
问：12 个 mdisp 是否全部相同？值是多少？

## 反控要求（必须有）
对 Q1 与 Q6 各做一个"故意写错"的版本，证明你的脚本会 FAIL：
- Q1 反控：把"v-4 是合法 COL"改成"v-4 是任意指针"，候选数应暴涨、精确率应暴跌。
- Q6 反控：把 mdisp 读成 BCD+0x04（numContainedBases）而不是 BCD+0x08，值应该不同。

## 输出
- /tmp/r113exec/REPORT.md：Q1..Q6 逐条给"我的算法 / 我的数字 / 与卡面对照"
- /tmp/r113exec/out.json：机读结果
- 每一条都要能复现：把你的脚本路径与命令行写进 REPORT.md

## 纪律
- 不许写"应该""大概"。算不出就写"算不出 + 卡在哪一步 + 缺什么"。
- 不一致就是不一致，不要为了对齐卡面而调参数。**发现卡面错是本任务的最大价值。**
- 只写 /tmp/r113exec/。

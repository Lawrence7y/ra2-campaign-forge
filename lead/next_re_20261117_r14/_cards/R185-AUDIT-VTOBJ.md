# R185 审计卡：只读复核「vtable -> COL -> TD -> CHD/BCD」四条链的推断是否越界

## 角色

跨家族只读审计。禁止修改仓内任何文件；只读 + 自行跑只读脚本（输出落 /tmp）。

## 被审计的主张（主会话 R185 的结论，逐条判真伪）

A1 gamemd.exe 里 988 个符号类中 954 个有 vtable，34 个没有；vtable 的「前一个 dword」恒是一个合法的
MSVC CompleteObjectLocator（COL），形状为 5 dword {signature 0 或 1, mdisp, pdisp(恒 0), pTD 落在 .data,
pCHD 落在 .rdata}，954/954 全通过。
A2 主 COL.mdisp 的分布是 {0: 942, 4: 12}，那 12 条非 0 的全部是 Locomotion 系类（LocomotionClass 及
Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk），因为 ILocomotion 是第二基类、
位于对象偏移 4。
A3 COL.pTD 指向 TypeDescriptor，其首个 dword 恒为 0x7F9594、次 dword 恒为 0，名字串形如 .?AV<类名>@@；
去掉前后缀后与 symbols.json 的 name 字段 954/954 相等。
A4 vtable 的连续 .text 槽长度与 symbols.json 的 vfunc_count 954/954 相等，逐槽地址也 954/954 相等，
954 个 vtable 共 13204 个槽。
A5 symbols.json 的 col_va 字段与 vtable-4 处主 COL 相同的只有 866 条，另 88 条不同；这 88 条里两处的
pTD 完全相同、类名完全相同、pCHD 也完全相同，只有 mdisp 不同（次 COL 的 mdisp 分布
{12:76, 24:6, 44:1, 4:1, 1728:1, 21784:3}）。结论：col_va 指向的是「同一类层次组里的次 COL」而非主 COL，
因此 A1 的判据不能写成 col_va == vtable-4。
A6 CHD 形状为 {sig 0, attr, numBase>=1, pBaseArray 落在 .rdata}，954 条主 COL 的 CHD 与 BCD 数组全可解，
BCD 条目总数 2615；AbstractClass 的 numBase 为 8，与 symbols.json 的 bases 列表长度 8 相等，
且 8 个基类名按顺序与 bases 列表逐项相同，第一项 pTD 等于自身 pTD（自指）。

## 你要做的

1. 自己写只读脚本从 ra2bench/gamemd.exe 字节重算 A1、A3、A4、A6 的关键数字（A1 的 954/954、
   A3 的 954/954、A4 的 13204 与 954/954、A6 的 2615 与 8）。报你的实测值。
2. A5 请专门判：88 条不一致里 pCHD 是否真的全同；如果 pCHD 不同，A5 的结论就错，请直接指出。
3. A2 请专门判：那 12 条 mdisp==4 的类名单是否就是 Locomotion 系；以及「ILocomotion 位于偏移 4」
   这个说法在二进制里是否有独立证据（例如 BCD 里对应项的 mdisp 是否为 4）。没有独立证据就判为推断而非实测。
4. 找至少两处「主张超出证据」的地方，或明确说没有。

## 纪律

所有数字必须实测，不许引用我给的数字当结论。不要读 harness/server.py、re_guardian.py、re-tool 源码。
不要讨论历史轮次取消原因。结论请用不超过 20 行，分「成立 / 不成立 / 越界」三栏。

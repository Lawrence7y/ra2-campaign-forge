# R216-AUDIT 只读复核卡（deepseek，只读，不改任何文件）

## 环境
- 目录 /home/t628/projects/ra2-campaign-forge；目标文件 ra2bench/gamemd.exe（已惰性加载）。
- 辅助模块：sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185'); import pe185 as P
  P.RAW=整文件 bytes；P.where(va)->段名；P.r2o(va)->文件偏移；P.dw(va)->dword；P.B['.text'] 含 lo/hi_file/rawptr/rawsize。
- 可用 capstone（CS_ARCH_X86/CS_MODE_32，可用 skipdata=True 与 disasm_lite）。
- 防 OOM：禁止对整段 .text 一次开 detail=True 的 md.disasm()；只许 disasm_lite + <=64KB 分块。
- 只读：不得修改仓库内任何文件；只可写 _r216/audit_*.py 与 _r216/audit_*.txt。

## 视图表重建口径（R214/R215 已固定，直接用）
a) 在 .rdata 与 .data 里找 5 连 dword 形如 [mdisp<=2, ptd, 0, name_ptr(.data), pchd_ptr(.rdata)] 的记录，name 形如 ".?A...@@"，
   得 COLA[记录地址]=(s32(mdisp), td, chd, name)。
b) 找 dword == COLA 键 且 紧随 dword 落在 .text 的 8 字节前言；按 COLA 键聚合，只保留「恰好 1 个前言」的键；
   视图起点 = 该前言地址 + 4。视图槽 = 从起点起连续落在 .text 的 dword 序列（到下一个视图起点或 .rdata 末尾为止）。
c) 基线（必须复算一致）：views=1214、slots=14044、distinct 槽目标=6692。
   ?AVAbstractClass@@ 主视图 0x7e1f50 槽数 24。

## 需要你独立复算并给出 PASS/FAIL 的 9 条断言
A1. AbstractClass 有 4 张视图：0x7e1f50(mdisp=0,24 槽)、0x7e1f34(mdisp=4,6 槽)、0x7e1f2c(mdisp=8,1 槽)、0x7e1f24(mdisp=12,1 槽)。
A2. 函数 0x4105a0（主视图 slot8）体内依次写 [esi+0]=0x7e1f50、[esi+4]=0x7e1f34、[esi+8]=0x7e1f2c、[esi+0xc]=0x7e1f24，
    随后 test al,1 分支 call 0x7c8b3d、最后 ret 4。给出这 9 条指令的地址与原始字节。
A3. 主视图 slot0=0x410260 是 QueryInterface：用 repe cmpsd（ecx=4）依次比对 0x7f7c90 / 0x7f7c80 / 0x7f7c70 / 0x7e9ae0 四个 16 字节常量；
    失败返回 0x80004002，第 3 个参数（[esp+0xc]）为 0 时返回 0x80004003；匹配第 4 个常量时写入 this+4。
    并给出 4 个常量的 16 字节十六进制与按 GUID 拆解的字符串。
A4. 四个常量按 GUID 解析分别等于：
    00000000-0000-0000-C000-000000000046、00000109-0000-0000-C000-000000000046、
    0000010C-0000-0000-C000-000000000046、170DAC82-12E4-11D2-8175-006008055BB5。
A5. 主视图 24 槽的槽目标依次为：
    00410260 00410300 00410310 004c9150 00410450 004c9150 004c9150 004103e0 004105a0 00410470
    00410480 004c9150 004c9150 00410410 00410490 004104a0 004104b0 00410440 004104c0 004104f0
    00410520 00410530 00410540 00410570
    并核对这几条已知字节：0x410300= b801000000c20400（mov eax,1 / ret 4）、0x4c9150= 33c0c3、0x410440= b001c3、
    0x410490= 83c8ffc3、0x410520/0x410530= 32c0c3、0x410470= c3、0x410570= c3、0x410480= c20800。
A6. 律 U（adjustor thunk）：mdisp!=0 的视图共 260 张；其中 slot0 形如『sub/add dword ptr [esp+4], N』后接 jmp 到另一视图 slot0 的有 101 张；
    这 101 张全部满足 N == self.mdisp - target.mdisp，反例 0 条。
    （请自行实现，不必复制我的实现；给出成立数/总数/反例数。）
A7. 律 W：全 .text 中『mov dword ptr [reg+disp], <某视图基址>』的 C7 位点 = 4195 条（按线性扫描 + skipdata，64KB 分块）；
    在其中能反解出 reg 基址增量 delta 的 2911 条里，disp+delta == 该视图 mdisp 的 = 2551 条，不等的 = 360 条，
    且 360 条违例中 (disp+delta) - mdisp 全部 > 0（0 条 <= 0），最小值 = ?（请报出实测最小值）。
    请只核对『0 条 <= 0』与『360』这两个数，以及 4195 与 2551；delta 反解实现可不同，若你的基数不同请如实报你的数与差异原因。
A8. 0x4105e0 = sub dword ptr [esp+4], 4 ; jmp 0x410260（即 mdisp=4 视图 slot0 是主视图 slot0 的 adjustor thunk）；
    0x4105f0 = sub 4 ; jmp 0x410300；0x410600 = sub 4 ; jmp 0x410310，三条字节均为 x836c240404e9xxxxxxxx。
A9. 0x410210 = mov eax,[esp+4] / mov edx,[eax-4] / lea ecx,[eax-4] / call dword ptr [edx+0x2c] / ret 4
    （即先回退 4 字节取完整对象 vftable，再虚调 slot11）。

## 输出
逐条 A1..A9 给 PASS/FAIL + 实测数字 + 与你口径不同处。所有数字必须你亲手跑出来，不得引用本卡的数值当结论。
最后单列一节「我复核出与卡面不一致的项」，没有就写"无"。

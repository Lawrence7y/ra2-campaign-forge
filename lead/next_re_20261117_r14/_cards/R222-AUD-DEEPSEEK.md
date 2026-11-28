# R222-AUD 只读跨家族复核（deepseek 审计员）

## 角色
只读审计员。绝对不要修改任何项目文件。只做独立复算，给 PASS/FAIL 与差异。脚本写 /tmp/ 下。
工作目录 /home/t628/projects/ra2-campaign-forge 。可用 python3 + capstone。

## 环境要点（必须照做）
- 只读模块：sys.path.insert(0,"/home/t628/projects/ra2-campaign-forge"); import _r185.pe185 as P
  P.RAW 全文件字节；P.r2o(va) 文件偏移；P.SECS 段表；P.B[".text"] 段信息；P.sec_of(va) 段名。
- capstone：md.skipdata=True。反汇编小范围用 md.disasm(buf, va)；全 .text 线性扫用 md.disasm_lite。
  严禁对整段 .text 开 detail=True。
- 每条都要实跑数字，禁止照抄本卡数字后声称一致。本卡给的是主会话实测值，请独立验证。

## 待复核（每项给实测值 + PASS/FAIL）

A1 段归属：0x8759b4 / 0x876ff4 / 0x877b14 / 0x877c14 / 0x879b30 / 0x87b170 / 0x87bc90 / 0x87bd90 / 0x8758c4 / 0x8758e4
   全部落在 .data 段（.data lo=0x812000 rawsize=0x6c000），且 .rdata 上界 0x812000 与 .data 起点零间隙相接。

A2 五个函数入口（0x7c6808 / 0x7c7428 / 0x7c77f0 / 0x7c7bc0 / 0x7c7b4c）的首 8 字节分别是什么；
   并给 0x7c7428、0x7c77f0、0x7c7bc0 三处首 16 字节是否完全相同。

A3 编码器内联差分：0x7c62ac 起的函数里，0x7c6315..0x7c635d 用 test eax,4 / test eax,2 / test eax,1 / shr edx,3 / test eax,8
   内联计算 delta。请读 0x7c6315..0x7c635d 的指令序列，确认这 5 个 bit 的运算顺序与移位量，
   并给出与 0x879b30 表 1424 项的命中数（主会话实测 1424/1424）。

A4 编码器索引更新：0x7c639b 读 word[ecx+0x8758c4]（ecx = 2*idx），加到 word[ebx+0x22]；
   随后 0x7c63a6 cmp 0x8000 / 0x7c63ae 置 0；0x7c63b6 cmp 0x58 / 0x7c63bd 置 0x58。
   请确认这两个门限的比较是否为无符号（jb / jbe）还是别的；给出 0x8758c4 起 8 个有符号 16 位字。

A5 解码器三段展开体：
   mono 体 0x7c7428..0x7c75b2、stereo 遍一 0x7c77f0..0x7c7982、stereo 遍二 0x7c7bc0..0x7c7d4a。
   对每一段给：add eax,dword ptr [edx*2+0x879b30] 的条数、mov word ptr [edi..],ax 的偏移列表、add edi 的立即数、add esi 的立即数。
   主会话实测：mono 体 8 条 / 偏移 0,2,4,6,8,a,c,e / add edi,0x10 / add esi,4；
   stereo 两遍各 8 条 / 偏移 0,4,8,c,10,14,18,1c / add edi,0x20 / add esi,4。

A6 stereo 两遍是否真正互补：遍一 0x7c7b4c 入口有 add edi,2 与 mov edx,[ebp+0x18]; shr edx,3; add esi,edx。
   请反汇编 0x7c7b4c..0x7c7b90，确认这两条；并确认遍一用状态 [+0]/[+4]、遍二用 [+6]/[+0xa]（给具体指令地址）。
   主会话结论：两遍各处理一个声道，输出按 2 字节交错，输入指针第二遍偏移 = 帧字节数/8。

A7 参数分派：0x7c7371 读 cx=word[ebp+0x10]、dx=word[ebp+0x14]。给四条分支到目标的映射：
   (8,2)->? (8,1)->? (0x10,2)->? (0x10,1)->? 以及 cx 既非 8 也非 0x10 时落点。
   主会话实测：三条落 0x7c75cc（函数尾声），(0x10,2)->0x7c7788（stereo 入口），(0x10,1)->0x7c73c3（mono 入口）。
   请特别复核 (8,2) 与 (8,1) 是否真的直接跳尾声（若成立则 8 位不被这个函数支持）。

A8 调用点：0x7c7371 的调用点只有 2 个：0x7c24a2 与 0x7c2557（用 e8 rel32 全 .text 扫）。
   两个调用点都 push 6 个参数（add esp,0x18）。请给两个调用点各 6 个 push 的源操作数，并按 stdcall 逆序映射到
   [ebp+8]=src、[ebp+0xc]=dst、[ebp+0x10]、[ebp+0x14]、[ebp+0x18]、[ebp+0x1c]，指出每个形参对应源操作数。
   主会话实测：[ebp+0x10]=byte[ebx+0x3f]、[ebp+0x14]=byte[ebx+0x3e]、[ebp+0x18]=ebp(寄存器)、[ebp+0x1c]=&[ebx+0x7d0]。

A9 四张 8 项跳转表与两张 4 项跳转表，给条目：
   0x7c7758（8 项）、0x7c7778（4 项）、0x7c7b1c（8 项）、0x7c7b3c（4 项）、0x7c7ef0（8 项）、0x7c7f10（4 项）。
   并核对这些表的条目是否全部落在 .text 内（4 项表只有前 4 项是地址，后 4 项是紧跟的代码字节）。
   主会话实测：0x7c7758 = 75c1,7694,76ac,76c4,76e0,76f8,771c,7740；0x7c7778 前 4 = 73e2,73f8,7408,7418；
   0x7c7b1c = 7989,7a58,7a70,7a88,7aa4,7abc,7ae0,7b04；0x7c7b3c 前 4 = 77a9,77c0,77d0,77e0；
   0x7c7ef0 = 7d59,7e2c,7e44,7e5c,7e78,7e90,7eb4,7ed8；0x7c7f10 前 4 = 7b79,7b90,7ba0,7bb0。

A10 引用计数（.text 全扫）：0x8758c4=3 / 0x8758e4=3 / 0x8759b4=8 / 0x876ff4=8 / 0x877b14=7 / 0x877c14=8 /
    0x879b30=24 / 0x87b170=24 / 0x87bc90=21 / 0x87bd90=24 / 0x7c7758=1 / 0x7c7778=1 / 0x7c7b1c=1 / 0x7c7b3c=1。
    请报实测次数，并指出主会话哪个数字可疑。

A11 反控：把 0x879b30 换成 0x87b170 按 dword 读、做同一个律 D 命中统计，命中数应接近 0（主会话实测 2/1424）。
    再给「step 表基址从 0x8758e4 右移 2 字节起读」时的命中数（主会话实测 64/1424）。

A12 编码器有三处 mov al,byte ptr [esi]（0x7c6307 / 0x7c6407 / 0x7c6526）和两处 mov ax,word ptr [esi] 变体，
    说明编码器对 8 位样本与 16 位样本都有内联分支。给出 0x7c62ce / 0x7c62df 两个 cmp（word[ebx+0x38],0x10 与 word[ebx+0x3a],2）
    的作用（哪个控制样本位宽、哪个控制声道数），并说明 8 位路径下 esi 的步进（inc esi 还是 add esi,2）。

## 输出
两三条命令一次产出全部结果，不要逐条命令试探。每条：编号 | 实测值 | 与卡片一致? | 差异原因。
最后单列「你发现的口径问题」。

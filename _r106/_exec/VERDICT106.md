# R106-EXEC 独立复算结论

执行员：R17 (hy4, work/cn:hy4flash)。反汇编器：Capstone 5.0.7（CS_ARCH_X86 / CS_MODE_32，detail=True；用 op.access、op.mem.base/index 获取读写语义）。辅助库 pefile 2024.8.26 用于 PE 映射。被测文件 ra2bench/gamemd.exe 的 sha256 实测为 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，与卡面一致；ImageBase 0x400000，一致。全部数字由脚本运行时从 exe 字节读取，未抄卡面结论。脚本 _r106/_exec/r106_exec.py 一条命令跑完，自带正控与反控，退出码 0 表示全过（实测 EXIT=0）。

## Q1 两级形态 10 张表：输入到 case 分组

对每张表从持有指令前 0x60 字节窗口反汇编：取紧跟 jmp 之前的 cmp reg,imm（无内存操作数）的 imm 作上界，取 mov r8,[reg+disp] 且 disp 落在表基址之后 0..0x80 的 disp 作字节表地址。全部 10 张表：字节表长 = 上界+1（通过），去重值全部小于项数（通过），各组输入个数之和 = 表长（通过），没有任何 case 零输入（uncovered 均为空）。逐表数字如下（完整分组在 r106_exec.json 的 q1 字段，每组均列出全部输入下标）：

- 0x46f5a0：上界 47，字节表 0x46f5b0，长 48，去重 4 个值（0,1,2,3），最大组 44 个输入，单输入组 2 个，无零输入 case。分组：case0=[0]，case1=[1,2]，case2=[47]，case3=[3..46]。
- 0x48db10：上界 37，字节表 0x48db44，长 38，去重 13 个值（0..12），最大组 25，单输入组 11，无零输入。分组：case0=[0]，case1=[2]，case2=[5]，case3=[6,9]，case4=[18]，case5=[19]，case6=[22]，case7=[23]，case8=[24]，case9=[29]，case10=[31]，case11=[37]，case12=其余 25 个输入。
- 0x48dd10：上界 39，字节表 0x48dd24，长 40，去重 5 个值（0..4），最大组 32，单输入组 0，无零输入。分组：case0=[0,39]，case1=[1,2]，case2=[5,6]，case3=[14,15]，case4=其余 32 个输入。
- 0x6a92c4：上界 14，字节表 0x6a92d0，长 15，去重 3 个值（0,1,2），最大组 11，单输入组 1，无零输入。分组：case0=[0,1,14]，case1=[5]，case2=[2,3,4,6,7,8,9,10,11,12,13]。
- 0x6adbdc：上界 22，字节表 0x6adbe8，长 23，去重 3 个值（0,1,2），最大组 9，单输入组 0，无零输入。分组：case0=[0,3,11,15,16,17,18]，case1=[5,8,9,19,20,21,22]，case2=[1,2,4,6,7,10,12,13,14]。
- 0x71f2c0：上界 45，字节表 0x71f2f8，长 46，去重 14 个值（0..13），最大组 33，单输入组 13，无零输入。分组：case0=[0]，case1=[3]，case2=[4]，case3=[5]，case4=[6]，case5=[7]，case6=[8]，case7=[9]，case8=[10]，case9=[11]，case10=[20]，case11=[40]，case12=[45]，case13=其余 33 个输入。
- 0x71f328：上界 55，字节表 0x71f350，长 56，去重 10 个值（0..9），最大组 47，单输入组 9，无零输入。分组：case0=[0]，case1=[2]，case2=[6]，case3=[7]，case4=[8]，case5=[27]，case6=[52]，case7=[53]，case8=[55]，case9=其余 47 个输入。
- 0x71f778：上界 55，字节表 0x71f780，长 56，去重 2 个值（0,1），最大组 34，单输入组 0，无零输入。case0 与 case1 各一组，输入列表见 JSON。
- 0x71f9e0：上界 58，字节表 0x71f9e8，长 59，去重 2 个值（0,1），最大组 54，单输入组 0，无零输入。case0=[0,5,30,43,58]，case1=其余 54 个输入。
- 0x79f028：上界 94，字节表 0x79f03c，长 95，去重 5 个值（0..4），最大组 90，单输入组 3，无零输入。分组：case0=[0]，case1=[1]，case2=[2]，case3=[93,94]，case4=[3..92]。

与卡面背景无差异：卡面给的 10 张两级表集合、持有指令地址均与实际反汇编一致，上界和字节表地址均由前置指令独立读得，与卡面描述吻合。

## Q2 19 张表 292 项重复普查

19 张表项数合计 292（通过）。全库不同项值 276 个，重复组共 8 组，分布在 5 张表，重复使项数多出 16 项。逐表：

- 0x4c8114：46 项，去重 39，重复 3 组，多 7 项。0x4c71ca 被下标 [3,4] 引用；0x4c8109 被 [24,25,27,36,37] 引用；0x4c6cde 被 [41,42,43] 引用。
- 0x58bda4：5 项，去重 3，重复 1 组，多 2 项。0x58bd95 被 [1,3,4] 引用。
- 0x69b15c：4 项，去重 2，重复 2 组，多 2 项。0x69b08c 被 [0,1] 引用；0x69af45 被 [2,3] 引用。
- 0x6dfdec：145 项，去重 143，重复 1 组，多 2 项。0x6dfddb 被 [38,91,92] 引用。
- 0x728e08：7 项，去重 4，重复 1 组，多 3 项。0x728de0 被 [0,4,5,6] 引用。
- 其余 14 张表（0x46f5a0、0x48db10、0x48dd10、0x5001e4、0x6a92c4、0x6adbdc、0x6b0238、0x708d54、0x71f2c0、0x71f328、0x71f778、0x71f9e0、0x7291ac、0x79f028）无重复。

两级形态 10 张表：无任何重复（two_level_tables_with_duplicates 为空）。全部重复都出现在直接形态的 9 张表中。

## Q3 每个重复组的目标块是否依赖索引寄存器

从目标地址 T 起前向逐条解码，判定序：先 ret 则 IDX_DEAD_HERE；先 call 且 reg 是 eax/ecx/edx 则 CALL_CLOBBER；再用 Capstone op.access 判读/写（显式操作数用 CS_AC_READ/WRITE，内存操作数同时检查 base 与 index），先读旧值则 DEPENDS_ON_IDX，先全写则 IDX_DEAD_HERE。索引寄存器由持有指令 jmp dword ptr [reg*4+base] 的 index 读出，19/19 与 N3 一致。三个坑的处理：坑一用 op.access 而非操作数位置（cmp eax,6 的 op0 access=READ，只读）；坑二同时检查 op.mem.base 与 op.mem.index（如 mov cl,[eax+disp] 的 eax 是 base）；坑三把 sbb r,r、or r,-1 归一化为不读旧值的全写；同类恒零折叠 xor/sub/and r,r 也按同一类处理（0x69b15c 的两个目标实际命中 xor eax,eax，若不归一会误判 DEPENDS）。8 个重复组判定如下：

- 0x4c8114 / 目标 0x4c6cde / reg eax / 下标 [41,42,43]：CALL_CLOBBER，决定指令 0x4c6ce0 call 0x637e00（在 eax 被定义前遇到 call，eax 属 cdecl 可毁寄存器，本层不可判）。
- 0x4c8114 / 目标 0x4c71ca / reg eax / 下标 [3,4]：CALL_CLOBBER，决定指令 0x4c71cd call 0x6e6f20。
- 0x4c8114 / 目标 0x4c8109 / reg eax / 下标 [24,25,27,36,37]：IDX_DEAD_HERE，决定指令 0x4c8113 ret（一路 pop 后直接 ret，未读 eax 旧值）。
- 0x58bda4 / 目标 0x58bd95 / reg ecx / 下标 [1,3,4]：IDX_DEAD_HERE，决定指令 0x58bd9d ret（块内 xor eax,eax / cmp edx,3 / setne al 均不读 ecx，直接 ret）。
- 0x69b15c / 目标 0x69af45 / reg eax / 下标 [2,3]：IDX_DEAD_HERE，决定指令 0x69af4a xor eax,eax（先写常量 0x71 到 ecx，随后 xor eax,eax 全写，未读 eax 旧值）。
- 0x69b15c / 目标 0x69b08c / reg eax / 下标 [0,1]：IDX_DEAD_HERE，决定指令 0x69b091 xor eax,eax（同上，先写 0x3e 到 ecx）。
- 0x6dfdec / 目标 0x6dfddb / reg edx / 下标 [38,91,92]：IDX_DEAD_HERE，决定指令 0x6dfde7 ret 0x10（块内 mov al,1 与 pop 系列均不读 edx）。
- 0x728e08 / 目标 0x728de0 / reg eax / 下标 [0,4,5,6]：IDX_DEAD_HERE，决定指令 0x728de0 mov eax, dword ptr [0xb0f910]（第一条即全写 eax，未读旧值）。

结论：8 组中 6 组 IDX_DEAD_HERE（项值相同即真等价），2 组 CALL_CLOBBER（本层不可判，需往下层验证被调用函数），0 组 DEPENDS_ON_IDX。0x69b15c 的 xor eax,eax 是卡面坑三的扩展实例；若不处理会错报 2 组 DEPENDS。

## Q4 表 0x728e08 的 4 项同值等价性

实测 7 项序列（下标:目标）：0:0x728de0，1:0x728dd9，2:0x728dd0，3:0x728c1e，4:0x728de0，5:0x728de0，6:0x728de0。目标 0x728de0 被下标 [0,4,5,6] 共 4 项引用。逐目标头 4 条反汇编（明细在 JSON 的 q4.targets）：

- 0x728de0（4 项引用）：mov eax, dword ptr [0xb0f910]；add edi, 0x18；mov dword ptr [edi], eax；mov ecx, dword ptr [0xb0f914]。
- 0x728dd9（1 项引用，下标 1）：mov dword ptr [edi+0x14], 7；mov eax, dword ptr [0xb0f910]；add edi, 0x18；mov dword ptr [edi], eax。
- 0x728dd0（1 项引用，下标 2）：mov dword ptr [edi+0x14], 5；jmp 0x728de0；mov dword ptr [edi+0x14], 7；mov eax, dword ptr [0xb0f910]。
- 0x728c1e（1 项引用，下标 3）：mov eax, dword ptr [edi+8]；mov ebx, dword ptr [edi+0x1c]；add eax, 0x9c；lea esi, [edi+0x18]。

回答：a) 是的，两个被 1 项引用的目标都是写一个不同常量后流到同一个公共块 0x728de0：下标 2 在 0x728dd0 写常量 5 到 [edi+0x14]，然后 jmp 0x728de0；下标 1 在 0x728dd9 写常量 7 到 [edi+0x14]，紧接着就是公共块 0x728de0（自然落入，无需 jmp）。公共块在 0x728de0，两处常量写分别在 0x728dd0 与 0x728dd9，目标地址相差 9 字节（0x728de0 减 0x728dd9 = 7，减 0x728dd0 = 16），常量值分别为 5 与 7，仅 [edi+0x14] 字段不同。b) 4 个引用同一地址 0x728de0 的项完全同址同码（都直接跳到 0x728de0，第一条都是 mov eax,[0xb0f910]，且 Q3 判 IDX_DEAD_HERE），因此它们是真等价的 4 个 case。c) 剩下那个独立目标 0x728c1e（下标 3）走的是完全不同的代码路径（读 [edi+8]、[edi+0x1c]，加 0x9c，取 lea esi 等），与 0x728de0 公共块及其两个常量前导块均不相同。

## Q5 反控

- N1：取 0x46f5a0 的字节表 0x46f5b0（长 48），在内存镜像里整体改成 0，重做去重，结果为唯一值 [0]（1 个值），通过；随后恢复内存镜像。说明去重判据确实在测字节表内容。
- N2：把同一字节表每个字节加 1 模 256，去重后值集合为 1,2,3,4（4 个值），其中 4 >= 项数 4，出现不小于项数的值，通过；随后恢复。说明每个值都小于项数这条判据有判别力，不是恒真。
- N3：从 19 张表的持有指令各取一条 jmp，反汇编文本逐条确认内存操作数是 [reg*4+base] 形式且 disp 等于对应表基址、索引寄存器为 eax/ecx/edx 之一。19/19 全对，通过；同时这些 reg 就是 Q3 使用的索引寄存器。

三个反控均由脚本内置，随主流程运行，退出码 0 表示全部通过。

## 与卡面背景的差异

无。19 张表基址/项数/持有指令、10 张两级表的集合与形态、字节表位于表基址之后、两级表内部无重复，这些实测均与卡面背景一致；卡面未给出具体上界、字节表地址、分组和目标判定结论，本报告的数字全部为独立实测。唯一需要主动说明的判定细节是：卡面坑三点名的 sbb r,r 与 or r,-1 在本批数据里并未直接出现在重复目标块；实际出现的是同类恒零折叠 xor eax,eax（0x69b15c 两个目标），已按同一语义归一化为不读旧值的全写，否则会错报为 DEPENDS_ON_IDX。

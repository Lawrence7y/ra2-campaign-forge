# R185 执行卡：独立复算 gamemd.exe 类对象模型四条字节链

## 目标（只读取证，禁止写仓内任何文件）

工作目录 /home/t628/projects/ra2-campaign-forge。用 python3 + struct 直接读 ra2bench/gamemd.exe 的字节。
禁止用 objdump 全段反汇编，禁止 md.disasm 整段，禁止修改仓内任何文件（需要副本一律放 /tmp）。

PE 段（从 PE 头自行解析，别硬编码）：.text 文件范围 0x401000-0x7e1000，.rdata 0x7e1000-0x812000，
.data 0x812000-0x87e000。VA 到文件偏移请自己按段表算（raw_ptr = 0x1000-0x401000 对 .text，
0x3e1000-0x7e1000 对 .rdata，0x412000-0x812000 对 .data 是自洽的，但你要自己验一遍）。

## 必须逐项复算并报出实测数字（一项不许省）

1. 读 out/reverse/symbols.json，报 classes 键数、vtable_va 为 null 的条数、非 null 的条数。
2. 对 vtable_va 非 null 的每一条，读 dword @ vtable_va-4（记作 PRE）。统计：
   PRE 落在 .rdata 的条数；在 PRE 处按 {sig, mdisp, pdisp, pTD, pCHD} 五 dword 解析，
   报 sig 取值分布、mdisp 取值分布、pTD 落在 .data 的条数、pCHD 落在 .rdata 的条数。
3. 对每个 PRE 的 pTD，读 dword@(pTD+8) 起的 C 字符串。报：以 .?A 开头的条数、以 @@ 结尾的条数、
   dword@(pTD) 的取值分布（应只有一个值，报出来）。报「字符串去掉前缀 .?AV 与后缀 @@ 后 与
   symbols.json 的 name 字段完全相等」的条数。
4. 对 vtable_va 非 null 的每一条，从 vtable_va 起连续读 dword，统计有多少个连续 dword 落在 .text，
   报该长度与 symbols.json 的 vfunc_count 相等的条数；再逐个比对 vfuncs 列表与该段 dword 完全相同的条数。
   报全部 954（或你实测的条数）条 vfunc_count 的总和。
5. 报 col_va 字段与 PRE 相等的条数、不相等的条数；不相等者里，两处五 dword 的 pTD 相等的条数、
   两处解出的类名相等的条数、第二处 mdisp 的取值分布。
6. 报 mdisp 不为 0 的主 COL 有几个，并把它们的类名逐个列出。
7. 对 AbstractClass（vtable_va 0x007E1F50）单独展开：PRE、PRE 五 dword、pTD、TD 名、pCHD；
   CHD 四个 dword；pBaseArray 指向的指针数组逐项；每个数组元素按 6 dword 解 {pTD,ncbase,mdisp,pdisp,pmdisp,attr}，
   逐项报告 class 名（从 pTD+8 字符串去前缀后缀）。报这 8 项的 ncbase 与 mdisp。

## 反控（必须真跑，各在 /tmp 副本上）

N1 把 PRE 五 dword 的 sig 改成 2，看第 2 项的解析是否变红。
N2 把 AbstractClass 的 TD 名字符串里字母 A 那个字节异或 1，看第 3 项名字比对是否变红。
N3 把 vtable_va 换成 vtable_va+4 后重跑第 2 项，看 PRE 是否落到 .text。
N4 把 CHD 的 numBase 从 8 改成 7，看第 7 项数组长度是否跟着变。
每个反控都要报「改前值 / 改后值 / 判据由绿转红」。

## 输出格式

一条命令跑完（写一个 /tmp 脚本，一次输出全部证据），最后把脚本路径与全部数字打印出来。
结尾用 6 到 12 行列出你实测的数字清单，并明确标出「与你预期不同的地方」。
如果某项你无法复算，直接说无法复算，不要猜数字。

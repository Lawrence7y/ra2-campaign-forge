IMAGE D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe SHA256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476
# R17-R18-EDI-GAP — REPORT

## 0. 唯一问题与范围
0x43F180 函数体内，从 0x43F191（mov edi,ecx）到 0x43F5D8 之间 edi 是否被写过。
锚点: 0x43F173 C3 + 12x90 至 0x43F17F。已完整反汇编 [0x43F180,0x43F5E0)；
并按卡要求覆盖跳表 0x43FB0C 指向的 case1/3 体 0x43F1E9 与 case2 体 0x43F9A6。

## 1. 跳表与 case 归属 (0x43FB0C)
case0 -> 0x43F1CA (early ret), case1 -> 0x43F1E9, case2 -> 0x43F9A6, case3 -> 0x43F1E9。

## 2. edi 全量写点 (写寄存器 edi 的指令)
窗口 [0x43F191, 0x43F5D8) 内共 **4** 条（不含初始 mov）：
| 地址 | 字节 | 指令 | 所在路径 | 是否到达 0x43F5D8 |
|---|---|---|---|---|
| 0x43F1DA | 5F | pop edi | case0 early-ret (ret@0x43F1E6) | 否 |
| 0x43F387 | 8D 3C 16 | lea edi,[esi+edx] | case1/3 内层循环 0x43F379..0x43F3D4 | 是（随后必被恢复）|
| 0x43F3DA | 8B 7C 24 30 | mov edi,[esp+0x30] | case1/3 循环后 | 是（恢复 this）|
| 0x43F5C9 | 5F | pop edi | al!=0 早退 (ret@0x43F5D5) | 否 |

函数其余区域（窗口外，>=0x43F5D8）另有 6 条 edi 写：0x43F5E0/0x43F649/0x43F88C/0x43F933/0x43F997/0x43FAFC，均与本题调用点无关。
case2 体 0x43F9A6..0x43FAFB **无 edi 寄存器写**（仅经 edi 写内存），且落到默认尾 0x43FAFC (pop edi; ret 4)，不达 0x43F5D8。

## 3. 到达 0x43F5D8 的路径（仅 2 条，全镜像该段分支扫描证实）
- 路径 A: 0x43F1E9 (case1/3) -> ... -> 0x43F220 jne 0x43F5D8。
  0x43F1E9→0x43F220 之间无 edi 写；edi 仍为入口 ecx = this。**edi == this**。
- 路径 B: 0x43F1E9 (case1/3) -> 0x43F220 not taken -> 内层循环（0x43F387 破坏 edi）-> 0x43F3DA 恢复 -> ... -> 0x43F5B1 je 0x43F5D8。
  破坏循环 0x43F379..0x43F3D4 无提前出口（唯一出口为 0x43F3D4 jl 失败落到 0x43F3D6/0x43F3DA），故每次 0x43F387 破坏后必经 0x43F3DA 恢复。

## 4. 恢复值字节验证 (0x43F3DA 的 [esp+0x30] == this)
- 入口 prologue: sub esp,0xb0; push ebx/ebp/esi/edi/ebp -> esp=S0-0xc4。
- 0x43F194 mov [esp+0x34],edi 写物理槽 S0-0x90。
- 0x43F198 call 0x6F4A70 (ret 4) 后 esp=S=S0-0xc0；故 S+0x30 = S0-0x90 = 保存 this 的槽。
- 自洽证明 esp==S 于 0x43F3DA: 0x43F35D mov [esp+0x48],eax (esp=S) 与 0x43F3D6 mov eax,[esp+0x48] 互指同一槽。
- 0x43F194..0x43F3DA 之间无任何指令写 S+0x30（相邻写为 S+0x34/0x36）。
=> 0x43F3DA 恢复的正是入口 this。

## 5. 判定
**字节证实**：到达 0x43F5D8 的两条路径上 edi 均等价于进入函数时的 ecx（this）。
0x43F5D8 的 53 / 8B CF / E8 90 54 2B 00 (call 0x6F4A70) 其 this 即本函数 this。

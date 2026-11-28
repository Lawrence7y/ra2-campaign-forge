# R214-EX1 · 虚槽 +0x48（slot index 18）转发面取证

## 目标
R213 QV7 已解 S3(21784) 函数体：0x723ea0 / 0x723eb0 结尾为 jmp dword [eax+0x48]，eax = 对象首 dword = vftable 指针。
本轮用一次性脚本证明「+0x48 落到哪些类的哪些槽、落点复用面多大」，并给出 Mouse/Tab/Scroll 三类的 slot18 落点。

## 环境与纪律
- 工作目录 /home/t628/projects/ra2-campaign-forge，二进制 ra2bench/gamemd.exe。
- 复用 _r185/pe185.py（提供 P.RAW / P.B / P.dw / P.where / P.cstr / P.sec_of / P.r2o），不要重新手写 PE 解析。
- 严禁对整段 .text 开 detail=True 一次性 disasm。只对命中地址用 capstone md.disasm(code, addr, count=N) 小窗口；全段扫描只用 disasm_lite 或跳过。
- 只用一条命令跑完（python3 _r214/ex1.py > _r214/ex1_out.txt 2>&1），脚本自带 timeout 900 外在包装；脚本内正反控断言全部打印 PASS/FAIL 计数。
- 结果写 _r214/ex1.json 与 _r214/ex1_out.txt。

## 表重建口径（必须与 R213 一致，不许改判据）
COL：在 .rdata 与 .data 里扫 32-bit word 序列 w[k..k+4]，条件 w[k] in (0,1,2) 且 w[k+2]==0 且 where(w[k+3])=='.data' 且 where(w[k+4])=='.rdata' 且 cstr(w[k+3]+8).startswith(b'.?A') 且 endswith(b'@@')。COL 地址 = 段基址+4*k。
前驱位点：在 .rdata 与 .data 里扫 w[k] in COL 且 where(w[k+1])=='.text'，位点 = 基址+4*k。
vftable 起点 = 位点 + 4；slot i 地址 = 起点 + 4*i。
CHD：按 COL 的 pCHD 分组；主视图 = pCHD 里 mdisp==0 的那条 COL；次视图 = 其余 260 条。
HouseClass / MouseClass / TabClass / ScrollClass 的 COL 按名字精确等于 '?AVHouseClass@@' / '?AVMouseClass@@' / '?AVTabClass@@' / '?AVScrollClass@@' 匹配（名字来自 TD+8 内联名，形如 .?AVXxx@@ 去首点）。

## 必答项（每项都要数字 + 正反控）
E1 视图槽数与 slot18 覆盖：主视图 954 张、次视图 260 张的槽数；槽数 > 18 的视图数（即 slot18 存在），槽数 <= 18 的视图数。给出 slot18 存在的视图集合大小。
E2 slot18 落点分布：对 slot18 存在的视图，统计落点 distinct 个数、复用计数 top10（地址 + 次数）、落点全部落 .text 的比例（正控）。反控：落点里 virt-only 或 other 的个数必须为 0。
E3 三类落点：MouseClass / TabClass / ScrollClass 的主视图起点、槽数、slot18 落点地址（三类是否同址）、以及 slot0 落点（应同为 0x6d1770，作为口径自检）。
E4 0x723ea0 / 0x723eb0 引用面：在 .text 内扫 e8/e9 rel32 与 ff /2、ff /4 间接调用不算，只统计直接 call/jmp 落点等于 0x723ea0 或 0x723eb0 的位点列表（用 capstone 小窗口判定操作数，或用 re 正则不行，必须 capstone 解码）。同时统计这两个地址是否作为任何 vftable 槽的值出现（全 14044 槽扫描）。
E5 反控组：用 slot index 17 与 19 分别重复 E2 的 distinct 数与 top3，证明 18 不是「所有视图同值」的平凡结论。

## 输出格式
ex1_out.txt 里先打印表规模（COL/CHD/主视图/次视图/slot 总数），再按 E1..E5 分节，每节打印 PASS/FAIL 与关键数字；ex1.json 存结构化结果。

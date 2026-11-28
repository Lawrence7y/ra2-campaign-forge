# R215-AUD1 — 只读复核：slot18 归因链的 10 条主会话待核结论

## 角色与边界

你是**只读审计员**。不要修改任何文件（包括不要写 _r215/ 下的任何文件），不要跑合并/重写脚本。只需在最终答复里逐条给「成立 / 不成立 / 口径问题」，并给出你自己算出的数字。禁止照抄我给的数字下结论——你必须自己独立算一遍。

## 输入

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe（ImageBase 0x400000）
- 助手模块（可 import）：/home/t628/projects/ra2-campaign-forge/_r185/pe185.py
  提供 P.RAW / P.B[段名]（lo, rawptr, rawsize, hi_file, hi_virt）/ P.dw(va) / P.where(va) / P.r2o(va) / P.cstr(va,n)
- 视图表重建口径（必须自己实现一遍并复现数字）：
  1. COL 候选：在 .rdata/.data 逐 dword 扫，条件 w[k]<=2 且 w[k+2]==0 且 where(w[k+3])=='.data' 且 where(w[k+4])=='.rdata' 且 cstr(w[k+3]+8,512) 以 ".?A" 开头、以 "@@" 结尾。COLA[coladdr]=(mdisp=有符号 w[k+1], ptd, pchd, name)。
  2. 只有"唯一前驱位点"的 COL 才算视图：前驱位点 = 满足 w[j]==coladdr 且 where(w[j+1])=='.text' 的位点地址；视图起点 = 该唯一前驱位点 + 4。
  3. 槽序列 = 从视图起点按 dword 前进，直到下一个视图起点，或 where(dword) != '.text'；最后一视图的 end 用 .rdata 段 hi_file。
  4. 类名去掉首个点。
- 预期能复现：视图 1214 / 主视图(mdisp==0) 954 / 次视图 260 / 槽总数 14044 / distinct 槽目标 6692 / 槽数>18 的视图 137（主 125 / 次 12）/ slot18 distinct 27。**若你自己算不出这些数，请直接说明差异在哪，不要硬凑。**

## 要核的 10 条（逐条给 成立/不成立 + 你的数字）

1. slot18 的 137 张视图按落点分成 9 个多类组（56/19/17/9/8/3/3/2/2 张视图）加 18 个单类组，**119 + 18 = 137** 严格闭合。
2. 落点 0x004104c0 出现在 **56** 张视图的 slot18，且它在**任何视图里只出现在 slot18 这一个槽号**（不是 17 也不是 19）。
3. ?AVAbstractClass@@ 主视图（mdisp==0）的 slot18 就是 0x004104c0；该函数体是「读 [esp+4] 作为目标指针，从全局 0x887680 / 0x887684 / 0x887688 各取一个 dword 写入 [目标+0]/[+4]/[+8]，ret 4」。给出该函数前 10 条指令的地址/字节/助记符，以及那三个全局地址的字节内容。
4. 槽 19 的 top 落点 0x004104f0（73 张视图）函数体内含 **call dword ptr [eax+0x48]**；槽 22 的 top 落点 0x00410540 同样含 call dword ptr [eax+0x48]。给出这两处的地址与字节。
5. 全 .text 内形如 FF /2 且 mod=01 且 disp8==0x48 的间接 call 数量（**非 SIB 形式**）为 928，SIB 形式（modrm rm=100，即 [esp+0x48]）为 1，合计 931；其中 FF /4（jmp）形式为 2 且全为 [eax+0x48]。**必须用字节模式自己扫，不要用全段 capstone 线性反汇编。**
6. 用 capstone（skipdata=True，64KB 分块 disasm_lite）线性扫描得到的 call/jmp [reg+0x48] 数为 931；不开 skipdata 时为 765，差额原因是**块被截断**（不开 skipdata 时 62 个块里 53 个在块内某处停止解码），不是"漏了 SIB"。给出你的块覆盖统计。
7. 12 个 *LocomotionClass@@ 派生类的 slot18 落点全部来自它们**各自的 mdisp=4 次视图**（50 槽），而它们的 mdisp=0 主视图只有 10 槽、根本没有 slot18。请对 ?AVLocomotionClass@@ / ?AVDriveLocomotionClass@@ / ?AVFlyLocomotionClass@@ 各给全部视图（起点/mdisp/槽数）。
8. 那 12 张 mdisp=4 的 50 槽视图逐槽比对：**只有 2 个槽号全同**（21 和 22），其余 48 个槽号有差异。给出全同槽号列表。
9. ?AVINoticeSink@@ 只有 1 张视图（mdisp=0，1 槽，槽值 0x4c9150）；mdisp==8 的视图有 78 张、mdisp==21784 的视图有 3 张（MouseClass / TabClass / ScrollClass）。**305 条 adjustor 出现里没有任何一条的 IMM 等于 8 或 21784。**
10. ?AVAircraftClass@@（不是 I 开头）的 mdisp=1728 次视图起点就是 0x7e2250（9 槽），其 slot0/1/2 的槽值 0x41c670/0x41c680/0x41c690 是三条 8 字节 sub 桩（字节 81 6c 24 04 c0 06 00 00 e9 ..），IMM=0x6c0，jmp 目标分别落 mdisp=0 主视图（0x7e22a4，341 槽）的 slot0/1/2，律 X（IMM == mdisp_self − mdisp_target = 1728 − 0）3/3 成立。

## 反控（必须做）

- 对 1 条做反控：把"槽数>18"改成">19"和">17"，看 137 这个数怎么变，说明我为什么用 >18。
- 对 5 条做反控：把 disp8 换成 0x47 与 0x49，看数量是否与 0x48 同量级（若同一量级，说明 0x48 不特殊，请如实写）。
- 对 7 条做反控：检查是否存在**同一类**的 mdisp=0 主视图槽数 ≥19 从而也有 slot18 的情况（若有请列出）。

## 输出

直接在答复里给一张表：条目 1..10 + 3 条反控，每行「成立 / 不成立 / 口径问题」+ 你的数字 + 与我方数字的差异（若有）。数字对不上时**先说你自己的口径**，再说差异。

## 纪律

- 防 OOM：不要对整段 .text 开 detail=True 做全量 disasm；最多用 disasm_lite 分块，或纯字节扫描；单条复核用 md.disasm(..., count<=12)。
- 一条命令输出全部证据，不要逐条磨。预算内一次到位。
- 不要写文件。不要改业务文件。
- 卡面不要出现反引号，命令用普通缩进代码块。

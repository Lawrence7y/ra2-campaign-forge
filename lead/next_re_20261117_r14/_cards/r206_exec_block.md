# R206 执行卡：独立复算 gamemd.exe MSVC RTTI 类块布局与字节记账

## 目标
在 t628 本机用 python3 + pefile/capstone 独立复算下列 5 项数字。**禁止读 _r206 目录下任何已有脚本或 json**，必须自己从 ra2bench/gamemd.exe 重新推导，以保证独立性。可参考 _r185/pe185.py 的 PE 段映射思路，但请自行实现对 .rdata 的读取。

## 背景口径（供你复现，不要照抄结论）
- COL 记录 20 字节：sig(+0, 恒0..2) / mdisp(+4, 有符号) / cdOffset(+8, 恒0) / pTD(+12, 指向 .data 内 type descriptor，TD 的 +8 处是 .?A...@@ 名字) / pCHD(+16, 指向 .rdata 内类头)
- 已知 pCHD 集合（类头 HEAD 地址）共 954 个，全部 8 字节对齐
- HEAD 36 字节：+0=0 / +4=attributes / +8=numBaseClasses / +12=pBCA / +16..+35 是内嵌的 20 字节 COL（其 pCHD 等于 HEAD 自身）
- BCA 是 dword 数组，pBCA 处 numBaseClasses 个指针，全部指向 .rdata 内的 BCD 记录（BCD = 24 字节：pTD/numContained/mdisp/pdisp(-1)/0/0）

## 必须实测并输出的 5 项（每项给出正整数与你的判据）
1. HEAD 是否 36 字节：统计 954 条 HEAD 上，偏移 +0/+8/+12/+16/+32 的取值分布；验证 dw(a+32)==a 的条数，以及把该判据整体位移 -8/-4/+4/+8 后的命中数（防错位）。
2. RTTI 字节区间：给出 min(所有 HEAD) 与 max(HEAD)+36；给出区间两端各 4 个 dword 的十六进制值。
3. 完全字节记账：把区间内每个 dword 判给唯一类别（HEAD 头 / 额外视图 COL 24B / BCD 24B / BCA 4B / 对齐 pad 4B），输出各类别的 dword 数与总字节数；必须报告「未归属 dword 数」与「重复归属 dword 数」。
4. BCD 物理归属律：对每条 BCD 记录 b，找出所有引用它的类 HEAD（即 b 出现在哪个类的 BCA 里），统计「b 的物理位置所落块的 HEAD」是否等于 min{引用者 HEAD 中大于 b 地址者}。给出命中数/总数，并给出两个反控：改用 max{引用者}、改用地址最近的引用者，各自的命中数。
5. 类块内 24 字节项的排列：统计每块 24B 项序列（额外视图 COL 记 C、BCD 记 B）的形态分布（前 10 个），并检验「C 恒为前缀」是否成立。

## 纪律
- 一条命令输出全部证据，不要拆成多次单点命令。
- 不允许对整段 .text 开 detail=True；本卡只读 .rdata/.data，无需反汇编。
- 数字必须实测，禁止预估；若某项与上述背景口径冲突，如实报告你的实测值与差异。
- 输出格式：每项一行，形如「项目名 | 你的数字 | 判据一句话 | PASS 或 CONFLICT」。最后一行给「总断言数 / FAIL 数」。

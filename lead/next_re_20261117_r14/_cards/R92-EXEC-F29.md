R92 执行卡 · F29 字节级全量回归核验（只读，禁写 live 树）

背景：FACT_INDEX v5.31 的 F29 行正文有一句严格字节口径错误，
正文写「0x6C2AC0 是 call [0x7E11C8] 的真 AddRef」。
R91 已实测该处 11 字节为 mov eax,[esp+4] / add eax,4 / push eax / 才是 call，
真 call 在 0x6C2AC8（入口+8）。本轮要把该行涉及的全部字节数字做一遍独立回归，
为正文改写提供回归基线。

必须做的机械核验（全部只读 ra2bench/gamemd.exe 字节 + objdump）：

1) 函数边界：确认 0x6C2AC0 是函数入口。
   给出 0x6C2AB5..0x6C2ABF 的字节（应为填充），
   给出 0x6C2AB2 处的完整指令字节，给出该函数的结束指令字节。
2) 给出 0x6C2AC0 起连续 12 条指令的地址、完整字节、objdump 反汇编文本。
   逐条标注哪一条是 call，该 call 的目标地址。
3) 确认 0x7E11C8 的导入身份：
   从 PE 导入表出发，给出该地址在 IAT 中的槽位、对应 Hint/Name、
   所属 DLL 名、IBN 原始字节。
4) 确认 dword[0x7F3B2C] 的值，并给出 0x7F3B24 处的 4 个 dword（槽 0..3）。
   判断 0x7F3B24 是否满足 COL 判据：dword==0 且 dword[+0xC] 指向 TD
   且 TD 在 .data 内且 dword[TD]==0x7F9594 且 TD+8 起以 .?A 开头。
5) 统计全库有多少函数的首条指令满足「mov reg,[esp+4]」且随后 add reg,4 且 push，
   即该 AddRef 形态是否普遍（给分母）。
6) 统计全库 B8 01 00 00 00 C2 04 00（ret 4、返回恒 1）形态的出现次数，
   并给出这些出现地址的前 10 个。

工具：python3 + capstone + pefile 或 i686-w64-mingw32-objdump（默认 AT&T 语法）。
反汇编起始集必须用 objdump 地址行，不要用 capstone 从头线性扫。

产物目录：_r92/_exec/  （只允许写这个目录）
禁止：复制 live 树任何目录、写 _r92/_exec 之外任何路径、修改 gamemd.exe。
产出上限 20 MB。

自测要求：至少 10 项断言，必须带正控与反控各一条，打印每项 PASS/FAIL。
最终把结论写 _r92/_exec/REPORT_F29.md，逐条给数字与字节，不写形容词。

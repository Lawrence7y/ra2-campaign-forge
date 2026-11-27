R146 审计卡 A1：只读复核三条断言（不要执行任何写操作，不要读结论脚本）

角色：auditor（只读复核，最多 14 轮，禁止执行类操作）

被审对象：主会话 R146 在 gamemd.exe 静态镜像上得出、并准备写进台账的三条断言。
你要**独立**判断每条是否成立，不许引用主会话的脚本结论，自己写命令验证。

断言 A：在 .?AVAbstractClass@@ 的类层次描述符（CHD）里，基类 .?AVINoticeSource@@
        的 mdisp 字段等于 12；基类 .?AVINoticeSink@@ 的 mdisp 等于 8。
        （MSVC 32 位 RTTI：COL 5 个 dword，[0xC]=pTypeDescriptor [0x10]=pClassDescriptor；
         CHD: [0]=sig [4]=attr [8]=numBaseClasses [0xC]=pBaseClassArray；
         BCD: [0]=pTD [4]=numContainedBases [8]=mdisp [0xC]=pdisp [0x10]=vdisp。）

断言 B：虚表 .?AVINoticeSource@@ 的那个虚表地址，作为 4 字节 little-endian 立即数，
        在 .text 里恰好出现 3 次；这三处的目的操作数都是 [reg + 0xc]（位移 12）。

断言 C：.?AVLayerClass@@ 的 CHD 基类链长度是 3，且三项的 mdisp 全部为 0。

工作方法：
  - 工作目录 /home/t628/projects/ra2-campaign-forge；可复用 _r143/r143lib.py 的 Bin
    （vtset() 给 (TDs, COL, VTS)；dw(va) 读 4 字节；sec_of(va) 给节名；sweep(md) 流式反汇编）。
  - 【内存红线】严禁对整段 .text 开 capstone detail=True；只用 disasm_lite。
  - 一条命令出全部证据：三条断言写进同一个脚本一次跑完，打印数值 + PASS/FAIL。

交付（写进最终回复）：
  1) 三条断言逐项 PASS/FAIL 及其实测数值；
  2) 你做验证时实际用的口径（例如「怎么从虚表地址找到 COL」「mdisp 取 BCD 哪个偏移」）；
  3) 如果你认为某条断言**表述上有歧义或过强**，明确指出该怎么改，这是本轮最需要你做的事。

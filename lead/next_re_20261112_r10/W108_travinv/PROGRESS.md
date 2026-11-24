W108 PROGRESS

[t+0]    读 R10_FACTS.md / LEAD_VERIFY_W104_W105.md / LEAD_FINDINGS_R09.md。确认红线：禁写 ra2youli、禁启动游戏、禁附加调试器。
[t+3]    建自建 Ghidra 库 _ghidra/ghidra_w108（未碰 Lead 的 _ghidra_proj）。后台跑 import+全量分析。
[t+8]    写 ghidra_scripts/Callers.java（xref 普查 + 全量反编译）。首次编译失败（内层类 Hazard），拆掉重跑。
[t+11]   分析完成：203 s / 8,948 函数。跑 census：得到 133/6/10 = 149 遍历器调用点；**0x47EA90 仅 1 个调用点**。
[t+13]   独立写 _w108_scan.py 做纯字节 E8 rel32 扫描复核（不依赖 Ghidra）。**与 Ghidra 逐一相符**：149 + 1。
         注：前几版 PowerShell 位运算多次算错 rel32，全部作废，改 Python 后稳定。这是本卡唯一的方法弯路。
[t+16]   step5：0x47EA90 在 .text 里：E8=1（0x005688EB）、E9=0、地址取用=0 ⇒ 单点审计定案。
[t+18]   step8：0x005687F0 体内不含任何遍历器调用（0x47C520/4D0/550 全零命中）。
[t+21]   step11：用 Ghidra 指令边界列 0x005687F0 全部指令。确认 esi 跨摘链是**索引**，摘链后 0x00568906 用同一索引**重读表**。
         ⇒ (A) 遍历期失效：**不成立**。
[t+25]   step16/17：解码 0x47C4D0 的参数顺序（arg2=whichChain 先压），逐一判 16 个带参调用点 → **全部传 0（链 A）**。
[t+28]   step18：全库写点扫描 0xE4/0xE8/0x8C。证实偏移通用性（0x62f1e9 写 0x40000000 等）。
[t+30]   step19：0x47E8A0 插入函数写双头，选链来自独立参数。
[t+33]   step20：判 0x47BBF0 是否第二个摘链函数 → **不是**，是构造函数（写 vtable 0x7e4eec，12 个调用点多在 0x565C10）。
[t+36]   写 TRAVERSAL_AUDIT.md（主报告）、UNKNOWNS.md、DISAGREE.md。
[t+38]   自查：修正报告中对 0x47D2B0 的措辞一致性；核 L4 分项 134/6/9 vs 我的 133/6/10（合计同）→ 写进 DISAGREE D-1。
[t+40]   完稿。

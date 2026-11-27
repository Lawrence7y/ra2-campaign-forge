# R145 执行卡：负位移装表站点是否被既有解析器整类丢弃（exec，盲测）

## 角色与边界
- 角色：exec（执行），模型 work/cn:hy4flash-free，预算 8 分钟。
- 只在 /home/t628/projects/ra2-campaign-forge 下工作；只写 _r145/sub_exec/ 你自己的文件。
- 内存纪律：禁止对整段 .text 开 capstone detail=True；必须用 disasm_lite 64 KB 分块流式。
- 所有命令带 timeout；收尾 ps 自查无孤儿进程（只报，不强杀他人进程）。

## 现成工具
- _r143/r143lib.py 提供 Bin 类（va2off / rd / dw / sec_of / vtset / sweep）与 norm / RE_STORE / disp_of / RE_IMM / GEN。
  vtset() 返回 (TDs, COL, VTS)：TDs 是 type descriptor 地址集合，COL 是 class 结构集合，VTS 是虚表地址集合。

## 盲测任务（不要先看 _r145 目录里的任何 json/py，那是主会话产物，看了就算作废）
1. 用 r143lib 自带的 norm + RE_STORE，统计它能否接受这两种 capstone 打印形态：
   a) mov dword ptr [eax + 8],0x401000
   b) mov dword ptr [eax - 8],0x401000
   给出两者 match 结果，并解释差异的根因（读 norm 与 RE_STORE 的源码，指出具体哪一行）。
2. 用你自己的**完整内存操作数解析器**（把 [base] [+index*scale] [+disp] 全拆开，符号含负数）
   重扫全 .text，统计：
   a) mov dword ptr <mem>, <imm 且 imm ∈ VTS> 的站点总数
   b) 这些站点覆盖多少张不同的虚表（distinct vt）
   同时用 RE_STORE 严格口径算同样两个数，给出差值。
3. 已知 R144 收口时 VTS 是 1218 张、并集覆盖 1213 张、残余 5 张（地址不告诉你）。
   请独立给出：在你的完整解析器口径下，VTS 里还剩哪几张没有任何「mov dword ptr <mem>, imm∈VTS」站点
   （列出地址与所在节），并把其中落在 .rdata 的单独标注。
4. 对 0x7E6060 这一张（若在你的残余里就不做）：把 0x4A8600 附近 0x80 字节用 disasm_lite 反汇编打印，
   说明该地址处的写入指令、基址寄存器、位移，以及相邻指令里基址寄存器的步进值。

## 一次取证纪律
把上面四问放进**一条命令**（一个 python heredoc）跑完，输出 JSON + 断言清单。不要分多次单点命令试探。

## 输出要求
- 结论四问逐条一句话 + 数字；
- 你自己写的断言（正控/反控）逐条 PASS/FAIL；
- 实测耗时。

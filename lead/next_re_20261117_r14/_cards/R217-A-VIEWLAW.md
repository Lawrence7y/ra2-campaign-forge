# R217-A 独立复现：MI 视图三条实测律（禁止照抄我方实现）

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge 。可用：
python3（含 capstone、pefile）、rg、ra2bench/gamemd.exe（PE32）。
已有只读辅助模块 _r185/pe185.py，提供：
  P.B[段名] = dict(lo=虚拟地址, rawptr=文件偏移, rawsize=原始大小)
  P.RAW = 整个文件字节；P.dw(va) = 读 4 字节 DWORD；P.cstr(va,n) = 读 C 字符串
  P.where(va) = 该地址所属段名；P.r2o(va) = 虚拟地址转文件偏移
必须用 md.disasm_lite() 或不大于 64KB 分块流式反汇编；严禁对整段 .text 开 detail=True 一次性 disasm。

## 背景（我方已测得的基线，你要独立复测，不得把下列数字当结论）
MSVC 的 RTTI 布局：CompleteObjectLocator 记录 24 字节，字段为
  +0x00 signature、+0x04 mdisp（有符号）、+0x08 pCD（此处恒 0）、+0x0c pTD、+0x10 pCHD、+0x14 self。
虚表 V 的特征是 dw(V-4) 等于某个 CompleteObjectLocator 的地址。
ClassHierarchyDescriptor 的 +0x0c 指向 BaseClassArray，元素为 BaseClassDescriptor。

## 目标 A1：视图骨架普查
按上述特征枚举全部虚表。报告：CompleteObjectLocator 候选数、虚表数、其中 mdisp 不等于 0 的虚表数。
槽数定义：从 V 起每 4 字节读一个 DWORD，直到该值不落在 .text 段内为止，上限取 256。
报告槽数分布（槽数 -> 表数）。

## 目标 A2：adjustor thunk 律（下称律U）
对每张 mdisp 不等于 0 的表，看它 slot0 指向的函数的前两条指令：
  第一条形如 sub dword ptr [esp + 4], N
  第二条形如 jmp 绝对地址
统计这样的表有多少张。对每张求 N 是否等于 本表 mdisp 减去 目标表 mdisp，其中目标表取 slot0 指向同一函数地址的那些表。
报告：张数、成立数、违例数、违例逐条（本表地址、目标、N、期望值）。
反控：把判据改成 N 等于 mdisp 减 1，成立数应塌到 0；报出实测值。

## 目标 A3：主对象转发桩
找出形如下面五条连续指令的函数（作为某张表的某个槽）：
  mov eax, dword ptr [esp + 4]
  mov 某寄存器, dword ptr [eax - 4]
  lea 某寄存器, [eax - 4]
  call dword ptr [某寄存器 + K]
  ret 立即数
报告：命中函数数、涉及表数、K 的取值分布、以及一条完整命中的 5 条指令的地址与十六进制字节。
再报告这些命中函数分别出现在各自表的第几个槽（槽序号从 0 起）。

## 目标 A4：接口查询函数 0x410260 的实参模型
反汇编 0x410260 起 0xb0 字节全部指令，逐条给出地址、字节、汇编文本。
回答四个问题：
 (a) 该函数共读了几次栈上的 IID 指针，每次从 esp 加多少处读（注意 push 后 esp 已变化，要按实际偏移推算，并说明你的推算过程）。
 (b) 被写入的输出指针来自栈上哪个偏移。
 (c) 四个 16 字节常量地址分别是什么，按 GUID 拆解成字符串（格式 8-4-4-4-12，全大写）。
 (d) 对第 4 个常量匹配成功时写入输出指针的值，是实参里的哪个值加多少？该加数在指令里是立即数还是从表里查出来的？

## 输出格式
逐条 A1..A4 给 实测数字 + 你的实现要点（一两句，不要贴长代码）。
最后单列一节：我复核出与我方基线不一致的项（没有就写 无）。
所有数字必须你亲手跑出来。脚本落在 _r217/ 目录，文件名统一前缀 cardA_ 。一条命令内输出全部证据，不要逐条试探。

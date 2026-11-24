# R117-EXEC-DISPATCHSEM —— 独立复算「序列化派发例程」的容器语义

## 身份与边界
执行员。只读盘、只在 _r117/ 下写**你自己的新文件**（前缀 x117exec_），不改任何既有文件。
命令一律带 timeout。禁止使用反引号。内存纪律：禁止对 .text 整段开 detail=True。

## 工作目录
/home/t628/projects/ra2-campaign-forge

## 背景（不要重开，直接核）
镜像 ra2bench/gamemd.exe，ImageBase 0x400000，.text=[0x401000,0x7E038D)。
R116 已落盘：_r116/r116e_dispatch.json 里有 35 个 dispatcher 调用点
（形如 mov edx,imm32 ; mov ecx,esi ; call rel32，call 目标在 0x67FDF0..0x681000）。
主会话本轮声称：这 35 个 imm32 是 35 个**MSVC 静态容器对象**的地址，每个对象的
field0(vptr) 在 .text 里恰好有 2 个写入点（tor 写 DynamicVectorClass<T>、dtor 写 VectorClass<T>），
且 tor 里 push 的 atexit 回调地址 == dtor 所在函数入口。

## 你的任务（只做这三件，别扩散）

X1 用你自己的抽取器（不许 import 我的 _r117 脚本）把被调函数 0x67FDF0 的**前 64 条指令**
逐条列出，并给出该例程做的事的**指令级描述**：每个 call 的接收者是谁（IStream 还是别的）、
参数是什么、循环变量从对象哪个偏移读、循环体里对元素做了哪两步操作。
特别回答：进循环**之前**是否先写了一个 dword 到流里？它是对象的哪个偏移？
X2 独立复算「容器对象首字段写入点」：对这 35 个 imm32 地址，用你自己的做法在 .text 里
找所有把该地址当写入目标的指令，报每条的地址与指令文本、以及写入的立即数。
断言「每个恰好 2 条」成立否；不成立就如实报实际分布。
X3 独立复核命名通道：用 out/reverse/symbols.json（这是与本轮无关的第三方产物）核
tor 写入的 35 个 vptr 是否都能查到类名，并核「tor 的模板实参」与「dtor 的模板实参」是否逐字符相同。
**同时**如实报告 symbols.json 里这 35 个 vptr 的类名与我从 RTTI（COL/pTD 装饰名）解出的类名
是否一致；不一致的逐条列出。

## 输出（只写 _r117/）
- x117exec_dispatchsem.json：三项的机器结果，含你每条断言的 ok 布尔
- x117exec_REPORT.md：X1 的指令级描述（人读版）、X2/X3 的数字、以及**你认为主会话错了的地方**

## 纪律
- 数字必须实测后再填，禁止预估；每个断言都要有一个「反控」（能证明该判据不是恒真的样本）。
- 拿不到就写「未取得」，不许猜、不许从我的 json 转抄结论冒充自算。

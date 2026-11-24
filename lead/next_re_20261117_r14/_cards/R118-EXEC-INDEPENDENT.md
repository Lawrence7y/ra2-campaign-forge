你是 R17 执行员（家族 deepseek）。本轮任务：**独立复算**主会话 R118 的三条核心数字。

背景（全部是二进制静态事实，二进制在 /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe，ImageBase 0x400000）：

主会话r118发现：R112 到 R117 六轮把「IID 的身份」当成「它在 .rdata 里的那个常量地址」。
但同一个 GUID 值在镜像里有**两份拷贝**（.rdata 一份 + .data 一份，16 字节逐字节相同），
因此按地址做普查会漏掉走 .data 那份的全部请求站点。主会话给出三个数字：

  数字1  IPersistStream(00000109-0000-0000-C000-000000000046) 的 push imm32 请求站点：
         .rdata 0x7f7c80 上 60 个；.data 0x820270 上 8 个；按值合计 68 个。
  数字2  ole32!OleSaveToStream（IAT 槽 0x7e15f4，调用形态 FF 15 + abs32）全镜像 43 个站点，
         其中「同函数内、早于调用」请求 IPersistStream 的：按值口径 43/43，按地址口径 35/43。
  数字3  IPersist(0000010C-0000-0000-C000-000000000046)：.rdata 0x7f7c70 上 push 站点 0 个，
         .data 0x818858 上 16 个，按值合计 16 个；这 16 个都不与 OleSaveToStream 耦合。

你的任务（只写你负责的产物文件，不得修改任何 R14_COMMON/LEAD_LOCK/LEDGER/STATUS_BOARD/BOARD_ARCHIVE）：
1. 用你自己的**独立写法**（不要复用 _r113/r113_lib.py 与 _r118/*.py，自己从 PE 头开始写）复算上面三个数字。
   特别要求：你自己用 capstone 做 .text 的指令对齐线性扫描来定位 push imm32 与 FF15 调用，
   不要用裸字节 find（裸字节会误吃立即数字节）。
2. 校验你的 GUID 解码：把每个用到的常量地址的 16 字节按 <IHH8> 解成 GUID 文本，与上面给的文本逐字符比。
3. 反控（必须有牙，写进产物）：
   K1 取 200 个随机的、位于 .text 且是真实指令的 5 字节窗口，把中间 4 字节当 push 立即数，说明你的定位器不会把它们算进来；
   K2 把「同函数、早于调用」放宽成「全镜像任意位置」，报告数字变化；
   K3 把 IID 换成 00000000-0000-0000-C000-000000000046，报告 SAVE 耦合数。
4. 把结果写到 /home/t628/projects/ra2-campaign-forge/_r118/x118exec_independent.json，
   结构自定，但必须包含：你算出的三个数字、你的扫描方法一句话、K1/K2/K3 结果、以及
   任何你认为与上面三个数字**不一致**的地方（不一致要如实写，不要迎合）。

内存纪律：禁止对整段 .text 开 detail=True；用 disasm_lite 分块（每块不超过 64 KB）；
所有命令加 timeout；不要用 pkill/kill -f。
预算 8 分钟。请在最终回复里用不超过 25 行说明：三个数字各自的复算值、K1/K2/K3 结果、以及你发现的任何不一致。

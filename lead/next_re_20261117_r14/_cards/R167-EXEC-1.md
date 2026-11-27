# CARD R167-EXEC-1 · 执行员：独立复算 6 个数（hy4flash-free / exec）

## 你的角色
执行员。你是**独立实现**：不要读主会话的脚本逻辑去改它，用你自己的写法从二进制原始字节重算下面
6 个数，然后逐条报「我算得 X，主会话说 Y，一致/不一致」。不改任何文件。

## 唯一允许的输入
- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe（4,825,360 B）
- 文本数据集：/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R118_FACTINDEX_V546/FACT_INDEX.tsv
- 已允许用 python3 + pefile + capstone（本机已装）
- 禁止读 _r167/ 下主会话的产物（那是被核验对象，不是输入）

## 要你复算的 6 个数
1. .text 段：PointerToRawData = 4096、SizeOfRawData = 4,063,232、VirtualAddress 对应 VA 基址 = 0x401000、
   Misc_VirtualSize = 4,060,045（四项逐个报）
2. bounds 条数：从 a2_sites.json 取 bounds 数组长度，
   路径 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json
   （该文件 17,624,355 B，bounds 是十六进制字符串数组）⇒ 主会话说 1,392,592
3. plain 线性解码起点数：capstone 32 位、**不用 skipdata**、对 VirtualSize 长度的 .text blob 做
   64 KB 分块扫描，某块一条都解不出时把游标前进 1 字节再试 ⇒ 主会话说 1,392,527
4. 单字节重对齐点条数（同上，即「解不出、前进 1 字节」的位置数）⇒ 主会话说 65
5. bounds 减去第 3 步起点集后的条数 ⇒ 主会话说 65，且集合与第 4 步**逐元素相同**
6. 不可解码位置普查：对 .text VirtualSize 内**每一个字节位置**用 capstone 解 count=1（窗口 15 字节），
   数出解不出的位置总数 ⇒ 主会话说 **58,017**；并报这 65 个重对齐点是否**全部**落在该集合内

## 反控（必须做，缺一条视为未完成）
- K1 从 0x401000 起必须解得出一条指令（否则扫描实现坏了）
- K2 负控：字节序列 0f 0f 重复 8 次必须解得 0 条（证明 capstone 真的会返回空）
- K3 随机取 3000 个 .text 位置，可解率必须 > 0.90，报实际值
- K4 第 6 步若得 0，直接判你的实现有 bug 并说明

## 纪律
- **一条命令输出全部证据**（可以把脚本写在 /tmp 下再跑，但只贴最终一条命令与全部输出）。
- 内存红线：禁止对整段 4 MB 开 detail=True；禁止一次性 disasm 整段；只允许 disasm_lite 与 count=1。
- 第 6 步慢（约 40 秒），允许开 4 个进程分片，但必须在输出里报耗时。
- 正文禁止反引号。结论必须给数字，不许写「大致」「可能」。
- 如果你算出的数与主会话不同，**直接报你的数与算法**，不要说「或许口径不同」。

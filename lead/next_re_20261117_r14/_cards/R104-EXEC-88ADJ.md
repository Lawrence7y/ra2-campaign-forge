R104 执行卡 · 第三套反汇编器复算 88 个地址的归属

## 卡面纪律

本卡面严禁出现反引号语法（已遵守）。你要做的不是「确认主会话」，是**自己从字节算一遍**。

## 背景（主会话给的前提，你可以不采信，但必须先核 sha）

- 可执行文件：ra2bench/gamemd.exe（软链 ra2youli/gamemd.exe）
  期望 SHA-256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- ImageBase 0x400000；.text = [0x401000, 0x7E038D)；VirtualSize = 4060045
- 本机 objdump 的真实名字是 i686-w64-mingw32-objdump（2.44）。
  用 -d -M intel 重新生成的反汇编文本 sha256 应为
  5935356b2914d90baeaeb0d8ea5198961976118526b37d341ab72f06d4046c70
  （该文件在 /tmp/r93_disasm.txt，约 69 MB。若不存在，你自己重新生成再核 sha。）
- 主会话已把 iced-x86 1.22.0 离线 vendored 到仓库内 _r104/vendor/。
  用法：在仓库根目录设 PYTHONPATH=_r104/vendor 后 import iced_x86。不要 pip install（本机无外网保证）。

## 88 个地址从哪来（你自己取，不要相信下面的清单）

读 _r101/_exec/r101_core.json 的 only_cap_ne_list（88 项）与 host_of_88（地址到宿主的映射），
读 _r101/_exec/r101_bc.json 的 detail（88 项，含 class 字段：B1/B2/B3/B4/B5 与 host/host_len/hend）。

这 88 个是「capstone 线性扫描认为是指令起点、但 objdump 的打印行起点里没有」的地址。
R101 已把它们按 capstone 链分五类（B1 41 / B2 27 / B3 2 / B4 0 / B5 18）。

## 你要交的四件事

T1 **iced 是否也把它们当起点**。用 iced 从 0x401000 线性扫到 0x7E038D，
先证 sum(len) 等于 VirtualSize（铺满）、再取 valid 起点集与 invalid 起点集。
报：88 个地址里，多少个是 iced 的 valid 起点、多少个是 iced 的 invalid 起点、
多少个既不是起点而是落在某个 iced 单元内部（这时给出包含它的那个单元的起点与长度）。

T2 **B1 的 41 个逐址定性**。B1 的定义是「capstone 在本行宿主起点就解不出」。
你要自己从宿主起点用 iced 解一次，报：iced 在宿主起点是否也是 invalid、invalid 单元长度多少。
若 iced 在宿主起点能解出来，给出该指令文本与长度，并说明这条能否覆盖到目标地址。

T3 **两个「拒解集」不是同一集合**（这条是 R100 的教训，必须分开数）。
给出：capstone 拒解集（65 个地址）与 iced invalid 起点集（个数你算）。
报三组数：交集大小、只在 capstone 的地址（逐个列，附字节）、只在 iced 的地址（逐个列，附字节）。
字节从 exe 里按 地址减 0x401000 加 4096 的文件偏移取，给出 hex。

T4 **集 A 的 4 条疑似「零位移 jXX」**。R101 记下集 A 里有 4 个地址的唯一引用源是位移为 0 的
条件跳转（即目标等于下一条指令），据此判定「数据被读成代码」。
这 4 个地址是 0x71f99e / 0x728e0a / 0x7b0082 / 0x7d9d2d（主会话抄的，你要自己从
_r101/r101e_recheck.json 的 setA_target_form 里核对这 4 个是不是真的）。
你要用 exe 原始字节判：这 4 个地址处的字节**从该地址开始**解码是什么？
特别查 0x71f99e：主会话取到的字节是 00 00 00 00 00 00 01 01，这**不是**一条 jXX。
若你确认它解出的是 add [eax],al 之类而非条件跳转，请明确写「主会话的 4 条清单里第 1 条是抄错的」。

## 输出

写到 _r104/_exec/ 目录下：VERDICT104.md（含上面 T1..T4 四节，每节给数与逐址清单）
加你自己的脚本与 json。所有数自己算，不引用主会话的 json 里的结论字段，只引用原始地址清单。

预算 10 分钟。

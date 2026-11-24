# R121 跨家族审计报告 · x121audit2

审计员：R17 / audit / hy4。范围：只读源码、JSON 与 gamemd.exe 原始字节；唯一写入文件为本报告。核对方法附录在末尾，所有数字可按该方法复现。

## A 待审对象 A：ppv 槽 K 从未参与判定

### A1 成立（主会话的结构判定正确，N3 的 FAIL 不是缺陷证据而是机制必然）

核对方式：读 r121a_qiconsume.py 的 analyze 函数（第 134 至 198 行），逐行跟踪解出的 P 的用途。

源码事实：

第 141 行 slot = ppv_slot(seq, idx)，第 142 行把 slot 写进 out.ppv。
第 153 至 155 行只在 slot 本身为 None 时返回 NO-PPV；这里判断的是槽是否存在，不是 P。
第 159 行 K = slot[1]。
第 162 行 P = None 初始化。
第 164 至 171 行在 QI 之后最多 22 条内匹配 mov P, dword ptr [esp + K]，命中才给 P 赋值；未命中则 P 保持 None。
第 176 至 179 行遇到 call 就调用 resolve 并把结果写入 out.consume 与 out.consume_at，这四行完全没有检查 P 是否为 None。
第 180 至 183 行才用 P，且只用于计算 arg_index 与 n_pushes。
第 193 行直接 return out。

结论：若某站点的 P 为 None，该站点仍会被计入 consume 桶。门槛缺失点在源码第 176 至 179 行，P 的唯一消费点在第 180 至 183 行。成立。

### A2 成立（机制说明）

K 只出现在第 166 行的正则里，作用是把 [esp + K] 匹配到寄存器 P。P 为 None 时，第 180 行条件 if P and P in pushes 为假，只是不写 arg_index；第 177 至 179 行的 consume 已经无条件写入。所以把 K 改成 K+4 只会让 P 解不出，不会改变任何站点的 consume 字符串，因而 OleSaveToStream 类命中数必然仍是 36。崩溃轮把 N3 的 FAIL 当成异常是不必要的：按现有源码，N3 本来就不可能翻动 consume 桶。成立。

### A3 成立（三个分布实测）

核对方式：python3 读 r121a_qiconsume.json，取 results.0x7f7c80 的 60 条记录，用 collections.Counter 分别按 r.ppv[1]、r.consume 统计；再筛 ppv[1] == 0x14 逐条打印 consume。

分布一，ppv 槽 K 取值分布（60 站）：
0x10 出现 1 次
0x14 出现 24 次
0x0c 出现 35 次

分布二，consume 字段取值分布（60 站）：
REG:ebp<-OleSaveToStream 出现 1 次
REG:ebp<-UNRESOLVED 出现 24 次
IAT:OleSaveToStream 出现 35 次

分布三，K = 0x14 那 24 站的 consume 具体字符串：全部是 REG:ebp<-UNRESOLVED，计数 24，没有第二种字符串。逐站地址与 consume_at 为：
0x67d3ee / 0x67d402
0x67d48d / 0x67d4a1
0x67d4fe / 0x67d516
0x67d577 / 0x67d58f
0x67d5f0 / 0x67d608
0x67d669 / 0x67d681
0x67d6e2 / 0x67d6fa
0x67d75b / 0x67d773
0x67d7d4 / 0x67d7ec
0x67d84d / 0x67d865
0x67d8c6 / 0x67d8de
0x67d93f / 0x67d957
0x67d9b8 / 0x67d9d0
0x67da31 / 0x67da49
0x67daaa / 0x67dac2
0x67db23 / 0x67db3b
0x67db9c / 0x67dbb4
0x67dc15 / 0x67dc2d
0x67dc8e / 0x67dca6
0x67dd07 / 0x67dd1f
0x67dd80 / 0x67dd98
0x67ddf5 / 0x67de09
0x67de5e / 0x67de72
0x67decb / 0x67dee3

另外两个辅助分布（不是卡的必答项，但用于 A4 推理）：P 分布为 eax 60 站；ppv 寄存器分布为 edx 60 站。

### A4 部分成立（给出预测：OleSaveToStream 计数变为 0；这是推理值，未实跑改动版脚本）

推理过程：
第一步，原 JSON 中 60 站的 P 全部解出为 eax，且没有 P 为 None 的站。
第二步，K 平移 +4 后，第 166 行正则要求 mov 的操作数是 [esp + K+4]。原模板中 K 为 0x14 时实际装回指令是 mov eax, dword ptr [esp + 0x14]（B1 反汇编可见，例如 0x67d3fc）；K 为 0x0c 与 0x10 两组同理，装回槽与各自原 K 相等。因此 K+4 后三组全部匹配失败，60 站的 P 全为 None。
第三步，当前源码在 P 为 None 时仍写 consume，所以原脚本得到 36 不变（已实测 N3 detail = 36）。
第四步，若在第 176 行之前加门槛 P is None 则不记 consume（等价于 NO-PPV 或 SCAN-END 桶），那么 60 站无一进入 consume，OleSaveToStream 类命中数 = 0。

所以预测数字是 0。方法可复现性：第一步与第二步可由 JSON 的 ppv/P/P_at 字段加 B1 反汇编核对；第三步由现有 N3 detail = 36 核对；第四步是纯逻辑推演，我没有运行改版脚本，属于未实测的预测值，标为部分成立。

### A5 成立

核对方式：读源码第 78 至 80 行 win 定义与第 135 行调用。
第 135 行：seq = win(s, 0x40, 0x100)。
第 79 行：o = PE_.va2off(va - back)。
第 80 行：MD.disasm_lite(BUF[o:o + back + fwd], va - back)。
后向窗口 back = 0x40 = 64 字节；前向窗口 fwd = 0x100 = 256 字节；总切片 0x140 = 320 字节。成立。

## B 待审对象 B：寄存器回溯的窗口依赖

B 类全部用我自己的 PE 解析与 capstone disasm_lite 流式扫描完成，没有调用 r121a_qiconsume.py 或 _pe119.py。PE 解析：e_lfanew = 0x50，COFF 中 nsec = 5，SizeOfOptionalHeader = 0xe0，Optional Header 中 ImageBase = 0x400000；节表按 name、VSize、RVA、RawSize、Raw 布局读取；va2off = 该节 Raw + (va - 该节 VA)。.text 的 RVA = 0x1000、VA = 0x401000、Raw = 0x1000、RawSize = 0x3e0000。

### B1 成立（24 站全部是 call ebp）

核对方式：从 JSON 取 consume 为 REG:ebp<-UNRESOLVED 的 24 个 site，按 va2off 取该站点起 32 字节，以 CS_MODE_32、detail=False 反汇编，定位 consume 字段给出的 consume_at 地址，打印该条 call。全部 24 条的字节都是 ff d5，反汇编文本都是 call ebp。逐站 site 与 call 地址：

0x67d3ee call at 0x67d402, bytes ffd5, call ebp
0x67d48d call at 0x67d4a1, bytes ffd5, call ebp
0x67d4fe call at 0x67d516, bytes ffd5, call ebp
0x67d577 call at 0x67d58f, bytes ffd5, call ebp
0x67d5f0 call at 0x67d608, bytes ffd5, call ebp
0x67d669 call at 0x67d681, bytes ffd5, call ebp
0x67d6e2 call at 0x67d6fa, bytes ffd5, call ebp
0x67d75b call at 0x67d773, bytes ffd5, call ebp
0x67d7d4 call at 0x67d7ec, bytes ffd5, call ebp
0x67d84d call at 0x67d865, bytes ffd5, call ebp
0x67d8c6 call at 0x67d8de, bytes ffd5, call ebp
0x67d93f call at 0x67d957, bytes ffd5, call ebp
0x67d9b8 call at 0x67d9d0, bytes ffd5, call ebp
0x67da31 call at 0x67da49, bytes ffd5, call ebp
0x67daaa call at 0x67dac2, bytes ffd5, call ebp
0x67db23 call at 0x67db3b, bytes ffd5, call ebp
0x67db9c call at 0x67dbb4, bytes ffd5, call ebp
0x67dc15 call at 0x67dc2d, bytes ffd5, call ebp
0x67dc8e call at 0x67dca6, bytes ffd5, call ebp
0x67dd07 call at 0x67dd1f, bytes ffd5, call ebp
0x67dd80 call at 0x67dd98, bytes ffd5, call ebp
0x67ddf5 call at 0x67de09, bytes ffd5, call ebp
0x67de5e call at 0x67de72, bytes ffd5, call ebp
0x67decb call at 0x67dee3, bytes ffd5, call ebp

计数：24 / 24 是 call ebp，0 条不是。成立。

### B2 成立（最后一次写是 0x67d351 mov ebp, dword ptr [0x7e15f4]）

核对方式：取地址最小站点 0x67d3ee，从 0x67d3ee - 0x2000 = 0x67b3ee 起流式反汇编到 0x67d40c（共 2958 条指令），筛选助记符属于源码 WRITE_MN 集合且操作数以 ebp 开头的写。

宽口径下 0x2000 窗口内全部 ebp 写（10 条）：
0x67b470 pop ebp，距站点 8062 字节
0x67b479 pop ebp，距站点 8053 字节
0x67cf11 xor ebp, ebp，距站点 1245 字节
0x67cf59 pop ebp，距站点 1173 字节
0x67d0b3 pop ebp，距站点 827 字节
0x67d171 pop ebp，距站点 637 字节
0x67d217 pop ebp，距站点 471 字节
0x67d29d pop ebp，距站点 337 字节
0x67d2f5 pop ebp，距站点 249 字节
0x67d351 mov ebp, dword ptr [0x7e15f4]，距站点 157 字节

按源码 last_write 语义（第 100 至 112 行：只在最近的前置 ret 或 jmp 之后的线性块内找，正则为行首 ebp 加逗号）筛出的写只有 2 条：
0x67cf11 xor ebp, ebp
0x67d351 mov ebp, dword ptr [0x7e15f4]

两种口径下最后一次写都是 0x67d351，原文 mov ebp, dword ptr [0x7e15f4]，字节为 8b 2d f4 15 e1 7e（反汇编操作数为绝对 VA 0x7e15f4）。成立。

### B3 成立（0x67d351 到站点之间无其他 ebp 写）

核对方式：用与 B2 同一段反汇编结果，取所有满足 mn 属于 WRITE_MN 且正则匹配行首 ebp 加逗号的指令，过滤地址落在开区间 (0x67d351, 0x67d3ee) 内的条目。结果 0 条。宽口径（含 pop ebp 等）在同一开区间也是 0 条。判定方法是线性反汇编后按地址与操作数文本筛选；不依赖控制流图，因此只能说明线性文本上无写，不能证明运行时路径不可达，报告到此为止。成立。

### B4 成立（窗口外，距离 157 字节大于 64）

核对方式：site 减 write：0x67d3ee - 0x67d351 = 0x9d = 157 十进制。0x40 = 64 十进制。157 大于 64。
该写指令不在站点前 0x40 窗口内：后向窗口起点是 0x67d3ee - 0x40 = 0x67d3ae，而 0x67d351 比窗口起点还早 0x67d3ae - 0x67d351 = 0x5d = 93 字节。所以脚本第 135 行的 win(s, 0x40, 0x100) 切片里根本不含这条写，last_write 返回 UNRESOLVED 是窗口截断造成的，不是字节里没有写。你的主张成立。

### B5 成立（ole32.dll 的 OleSaveToStream）

写指令操作数是绝对 VA 0x7e15f4。核对方式：自己解析 PE 导入目录 Data Directory 第 1 项（RVA 0x7955c0，大小 0x154），遍历 IMAGE_IMPORT_DESCRIPTOR 数组，对每个描述符读 OriginalFirstThunk 与 FirstThunk，沿 thunk 数组逐项加 4 计算对应 IAT VA，命中 IAT VA = 0x7e15f4 时，从 FirstThunk 序号对应的 IMAGE_IMPORT_BY_NAME 读函数名，从描述符 Name 字段读 DLL 名。

解析结果：IAT VA 0x7e15f4，RVA 0x3e15f4，属于 ole32.dll，函数名 OleSaveToStream，thunk 中该槽值为 0x79526a。
交叉核对：_r119/iat_names.json 中键 0x7e15f4 的值是数组 ole32.dll、OleSaveToStream，与我的导入表解析一致。成立。

## C 待审对象 C：数字自洽

### C1 成立

summary.buckets_7f7c80 三个数为 1、24、35，和 = 1 + 24 + 35 = 60，等于 summary.sites_7f7c80 = 60，也等于 results.0x7f7c80 的长度 60。核对方式：python3 读 JSON 直接相加并逐站计数交叉核对。成立。

### C2 部分成立（值核对成立，语义陈述有一处条数偏差）

summary.after_7f7c80 的值：{"dword ptr [ecx + 8]": 60}。

按源码的真实语义：第 185 行 rel = None；第 186 行 for j in range(i + 1, min(len(seq), i + 10))；第 187 至 189 行遇到第一条 call 就取 seq[j][3] 赋给 rel 并 break；第 190 至 191 行遇到 ret 或 jmp 提前 break；第 192 行 out.after = rel。也就是说 after 是消费 call 之后最多 9 条指令内（下标 i+1 到 i+9）第一条 call 的操作数原文，不是断言文本 A4 里写的 8 条内。第 226 至 228 行的检查名称写的是 8 条内，第 186 行的代码却是 i+10 上界，差 1 条。JSON 字段名与源码第 287 行 'after_7f7c80': dict(after80) 一致。

因此卡里那句「消费 call 之后多少条内出现的 call 操作数原文」方向对，但要精确到代码是 9 条内、第一条 call。成立部分：值 60 与字段语义的来源行号（第 186 至 192 行、第 287 行）可核对。不成立部分：断言文案的 8 条与代码的 9 条不一致。整体判部分成立。

### C3 部分成立（计数成立，寄存器恒为 ecx，A4 确为特例）

核对方式：逐站读 r.after。
after 字段值等于 dword ptr [ecx + 8] 的站点数 = 60，占 60/60。
after 出现的全部不同值只有 1 种：dword ptr [ecx + 8]。
提取每个 after 字符串左操作数寄存器：集合为 {"ecx"}，没有其他寄存器，出现次数 ecx = 60。

回答卡的问题：这个字符串里的寄存器在当前数据里恒为 ecx，没有别的寄存器。所以第 226 至 228 行 A4 断言文本写的是 call dword ptr [reg + 8]（泛化到任意寄存器），但实际命中的键只有 ecx + 8，断言确实是只对 ecx 成立的一个特例；由于实测 60/60 全部落在 ecx 上，在本次数据上它仍然通过，但不能据此声称对任意 reg 成立。判部分成立。

### C4 成立（字段与数值和源码一致，176 本身未复算）

核对方式：读源码第 268 至 279 行 N6 与第 284 至 289 行 JSON dump。
源码第 268 至 277 行扫描全 .text，正则 r'ebp, dword ptr \[(0x[0-9a-f]+)\]'，要求 mn == mov 且 v 在 IATV 中，把 [hex(a), IATV[v]] 追加到 n6。
第 278 至 279 行 ck 名称为 N6 全 .text 里 ebp <- IAT 槽 的写点 = %d 个，detail 为 {'n': len(n6)}。
JSON 中对应 checks 第 10 项（0 基索引 9）：ok = true，name 含 176 个，detail 为 {"n": 176}。
字段名 n 与数值 176 和源码一致；A5 检查（源码第 281 至 282 行）对应 checks 第 11 项，detail.sites = 0x5be84f 与 0x67d351，计数 2，也与源码一致。
我没有重跑全 .text 的 176 计数，所以 176 这个数字标为未复算；可核对的是 JSON 字段名与数值同源码写出方式一致。成立。

## 核对方法附录

1. 文件读取：全部只读，未修改 _r121 或项目内任何其他文件；唯一写入是本合同指定产物 x121audit2_report.md。
2. JSON 统计：python3 标准库 json 与 collections.Counter，数据源为 _r121/r121a_qiconsume.json。
3. 源码行号：Read 工具直接读 _r121/r121a_qiconsume.py，行号与文件内容一一对应。
4. 字节与反汇编：python3 标准库 struct 解析 gamemd.exe PE 头与节表；capstone.CS_ARCH_X86 加 CS_MODE_32，detail=False，使用 disasm_lite 流式迭代，未对全量 .text 开 detail=True，未一次性常驻整个反汇编对象列表。
5. 地址换算：va2off 用节 Raw + (va - 节 VA)，.text 节 VA = 0x401000、Raw = 0x1000。B1 每次只切 32 字节；B2 最多切 site-0x2000 到 site+32 一段。
6. IAT 解析：按 PE Data Directory 第 1 项定位 IMPORT_DESCRIPTOR 数组，逐个按 OriginalFirstThunk 或 FirstThunk 遍历 thunk，按序号乘 4 求 IAT VA，命中后读 Name 与 IMAGE_IMPORT_BY_NAME。
7. 未复算项：A4 的预测值 0 是逻辑推演，未实跑改动版判定；C4 的 176 未由我重扫全 .text。其余数字均可用上述方法复现。

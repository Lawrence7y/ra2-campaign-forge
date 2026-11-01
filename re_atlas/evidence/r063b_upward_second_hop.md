# R-063b · 2026-10-30 — unknown-reg 12 行第二跳上行收口 + 「GenericList 裸传 12 行」构造点上探（前轮中断续办）

对象：`ra2youli/gamemd.exe`（只读）。本轮机器自验 sha256
`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
（`_r063b_probe7_out.txt` §A，与 R-062 冻结值逐字符相等）。PE：ImageBase
0x400000，.text=[0x401000,0x7E1000)。纯离线反汇编，零真机，未运行游戏，
未宣称可改写点。写域：仅新建 `re_atlas/evidence/r063b_upward_second_hop.md`
（本件）与 `re_atlas/tools/_r063b_probe7..14*.py`（临时脚本，编号接续前轮
probe1–6）；未修改任何既有文件（git 工作区核对，前轮 probe1–6 及其输出原样）。

## 0. 证据版本

- 门禁/契约（只读复用，未改动）：`tools/r062_upward_trace_contract.py`
  （frame_lo=ret 界窗、slot_writers=窗内同字面槽写、classify_call 冻结语义）、
  `tools/r061_witness_this_contract.py`（SMALL 七宿主、GLOBALS、EXE 路径）。
- 本轮机器转储（G-65 纪律，全保留）：`_r063b_probe7_out.txt` …
  `_r063b_probe14_out.txt` 共 8 份，每份与其脚本同名配套。
- 前轮中断产物（只读引用，未重算其中已完成部分）：`_r063b_chain_dump.txt`
  （CHAIN 88 行）、`_r063b_probe1..6.py` 及 `_r063b_probe1_out.json`、
  `_r063b_probe2..6_out.txt`。

## 1. 交接说明：前次产物编号与本次续办边界

前轮执行 112 分钟后死于 Provider 认证故障，报告未出。恢复盘点：

| 前轮产物 | 内容 | 状态 |
|:--|:--|:--|
| `_r063b_chain_dump.txt` | R-062 CHAIN 88 行冻结字面量（含 12 unknown-reg、1 unknown-thunk、17 stack-object） | 完整，直接采用 |
| `probe1` + `probe1_out.json` | 12 unknown-reg 行 hop2：含帧 esi/edx 写者普查、F 唯一 caller、call 站点 reg 溯源 | 完整有效，直接引用 |
| `probe2` + out | 12 裸传行确认（5 已构造/12 裸传复核通过）；全镜像 imm32 0x7E1B04 45 处直写清点；外层调用者帧 vptr 直写普查=全零 | 完整有效，直接引用 |
| `probe3` + out | unknown-reg hop3（esi←edx@hub 入口；2 行 esi←[esp+0x20]）；数据段 0x7E1B04 持有者=空；F 帧 direct/lea/indirect 槽写普查 | 完整有效，直接引用 |
| `probe4` + out | 45 处全为 c7 mem-store（无 reg-dest/push 形态，Q5=空）；0x778a20 窗口/汇合/三 witness 原始字节；hub 入度=1（冷入口）；[esp+0x20] 窗内零写者 | 完整有效，直接引用 |
| `probe5` + out | **崩溃**（delta_walk KeyError，0x778ac7 前存在解码缝隙）：edi 溯源、物理槽、0x528C00 callee-side 检查均未产出 | 作废，由本轮 probe7/12 重做 |
| `probe6` + out | 线性栈模拟**两处缺陷**：witness-lea 正则永不匹配（op 串不含助记符）；callee ret-cleanup 全 unknown ⇒ 其 phys 偏移数不可信 | 数值作废；其列出的分歧点仍有效，由本轮 probe10–14 重做 |

本轮续办边界：①前轮已算的部分不重做，报告逐处引用产物编号；②补齐 probe5
崩溃与 probe6 缺陷留下的四个未完成项（edi@0x778ac7 溯源、0x528C00 callee
侧检查、witness 槽物理归属、路径敏感 D 记账）；③按任务书完成 12 行第二跳
四类钉与 12 裸传行外层四机制普查。

## 2. 方法（本轮新增）

**D-归一化路径敏感抽象解释**（`_r063b_probe10/12/14.py`）：以 E8 头为 D=0
基线（D=esp 相对函数入口的沉降量），沿门禁流图前向 DFS（jcc 双臂、memo
按地址合并 D 集、>8 值记 D-ambig、穿 ret 即剪枝），物理格 P=disp−D。D 移动
只认 push/pop/sub esp/add esp/call(ret-imm)。三条**可证**补充规则（逐条带
证据）：

1. **call 站点零 push ⇒ ret-imm=0**：自上一锚点（已清算 call / add esp）以来
   零 push，则 callee 无栈参可清，cdecl/stdcall 两种约定下 D 效应同为 0
   （用于 0x778b47→0x7b5b30、0x5d7c86→0x5256f0、0x76c692→0x5256f0，
   后两者 census 200k 条仍无 ret）。
2. **call 后同 disp 重读 ⇒ 栈已复原**：0x5cef6b `ff5008`（call [eax+8]，前推
   1 参）后 0x5cef6e 以同一 disp 重读 [esp+0x68]；0x5cef78 同理（0x5cef7b）
   ⇒ 该两处间接 call 清 4 字节。
3. **保 esp 指令中性**：`mov reg,esp`/`mov [m],esp` 不改 D（probe12 曾误剪枝
   导致 5d76a9 空转，probe14 修正）；唯写 esp 的指令（mov esp,…/leave 等）
   才剪枝并记因。

**方法自校准**：同一解释器对 0x778a20 帧手算复核（probe9 ret 全普查：入口
epilogue `0x778b95 pop edi/esi/ebx + add esp,0xd0` 与序言严格对称）；编译器
disp−D 不变量在多点自洽（0x5ceef0：0x28@D=0xd4 与 0x38@D=0xe4 同格；0x76c290：
0x30@0xdc 与 0x38@0xe4 同格；0x778a20：0x2c@0xe4 与 0x38@0xf0 同格——三帧
独立成立，D 记账错 4/8/0xC 字节即全部失配）。

## 3. ① unknown-reg 12 行·第二跳上行判定表（四类钉）

hop 记账：hop1=R-062 冻结（行帧内链死在 callee-saved 寄存器）；hop2=跨帧到
唯一 caller 的 call 站点；hop3=再一层写者。四类钉：终到 global-load / 终到
栈件构造 / 终到参数槽 / 未闭合 UNKNOWN+边界。

**A1 组（F1=0x4F2C70，3 行）**——前轮 probe1/3 已算，本轮 probe7/8 复钉 call 字节：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F2CED | 0x528C00 | `8bce`+`e80e5f0300`→hop2 `8bd6`@0x4F3976→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F1 唯一 caller 0x4F397A `e8f1f2ffff`；hub 0x4F38B0 序言 `mov esi,edx` |
| 0x4F2D5C | 0x528C00 | `8bce`+`e89f5e0300`→同上 | 同上 | 同上 |
| 0x4F2E30 | **0x527F20** | `8bce`+`e8eb500300`→同上 | 同上 | 同上 |

**A2 组（F2=0x4F3140，6 行）**——前轮 probe1/3 已算，本轮 probe7/8 复钉：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F3219 | **0x527F20** | `8bce`+`e8024d0300`→hop2 `8bd6`@0x4F392E→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F2 唯一 caller 0x4F3932 `e809f8ffff` |
| 0x4F32A4 | 0x528C00 | `8bce`+`e857590300`→同上 | 同上 | 同上 |
| 0x4F32E9 | 0x528C00 | `8bce`+`e812590300`→同上 | 同上 | 同上 |
| 0x4F332E | 0x528C00 | `8bce`+`e8cd580300`→同上 | 同上 | 同上 |
| 0x4F337C | 0x528C00 | `8bce`+`e87f580300`→同上 | 同上 | 同上 |
| 0x4F33CA | 0x528C00 | `8bce`+`e831580300`→同上 | 同上 | 同上 |

**A3 组（F3=0x4F3B80，1 行）**——前轮 probe1/3 已算：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F3BF3 | 0x528C00 | `8bce`+`e808500300`→hop2 `8bd6`@0x4F394B→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F3 唯一 caller 0x4F394F `e82c020000` |

**B 组（hub 0x4F38B0 帧内，2 行）**——前轮 probe1/3/4 已算，本轮 probe7/8 复钉：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F38F9 | 0x528C00 | `8bce;8bf2`+`e802530300`→hop2 `8bd6`@0x4F20B7→hop3 `8b742420`@0x4F207C | **终到参数槽（寄存器形参 edx@H=0x4F1CA0 入口）** | hub 唯一 caller 0x4F20C1 `e8ea170000`；[esp+0x20] 窗内零写=参数槽，窗外写者=H 序言 `89542420`@0x4F1CAF（edx spill） |
| 0x4F39C1 | 0x528C00 | `8bce;8bf2`+`e83a520300`→同上 | 同上 | 同上 |

闭合陈述：
- **10 行（A1+A2+A3）3 跳内终到 hub 0x4F38B0 的 edx 形参**（fastcall 第 2 参；
  帧内 esi 镜像 @0x4F38B8；esi 全函数唯一写者=该序言 mov，probe7 §G 普查钉）。
- **2 行（B 组）3 跳内终到 H=0x4F1CA0 的 edx 形参**（H 唯一 caller 0x4F1C53；
  probe7 §H）。
- **同源性旁证（超 3 跳上限，仅登记不升格）**：hub 的 edx@entry 经其唯一
  caller（H 帧内 0x4F20B7 `mov edx,esi`→0x4F207C `mov esi,[esp+0x20]`→
  0x4F1CAF `mov [esp+0x20],edx`）同样归于 H 的 edx 形参——**12 行全部同源**。
- 四类钉计数：终到参数槽 **12**（寄存器形参形态）；终到 global-load 0；终到
  栈件构造 0；未闭合 UNKNOWN **0**。
- 措辞边界：链上只钉「值从哪里来」，实例身份仍 UNKNOWN（与 R-061/R-062 冻结
  口径一致，不减不增）；「寄存器形参」是参数槽的寄存器形态，非栈槽形态，
  报告如实分列。

## 4. ② 「GenericList 裸传 12 行」构造点上探判定表

外层四机制普查（任务书口径，probe2/3/4 前轮完成）：更外层调用者帧内
`mov [esp+X],0x7E1B04` 三窗形态 **0**；等价 vptr store（reg 中转）**0**
（全镜像无 `mov reg,0x7E1B04` reg-dest 形态，probe4 Q5=空）；imm32 直写其它
形态 **0**（45 处全为 c7 mem-store，probe4 Q1）；数据段装载中转 **0**
（0x7E1B04 双字全镜像仅存在于 .text 指令立即数内，probe3 holders=[]）。
按任务书字面 ⇒ 找不到 ⇒ 保持未证。

本轮续算（超出任务书字面，为诚实账补 probe5/6 欠账）在**本帧内**完成
D-归一化后得到下表——「裸传」是门禁同字面 disp 配对（无 esp 归一）的伪象：

| 行 VA | call 目标 | witness lea | D(row)→物理格 W | on-path 写者（D-归一化命中） | 新 verdict |
|:--|:--|:--|:--|:--|:--|
| 0x5CEFC9 | 0x528C00 | `8d4c2438`@0x5CEFC5 | 0xE4→−0xAC | **`c7442428 f4a57e00`@0x5CEF41**（[esp+0x28]←0x7EA5F4，D=0xD4） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x5CF10E | 0x528C00 | 同形@0x5CF10A | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF162 | 0x528C00 | 同形@0x5CF15E | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF284 | 0x528C00 | 同形@0x5CF280 | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF2E0 | 0x528C00 | 同形@0x5CF2DC | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF42C | 0x528C00 | 同形@0x5CF428 | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF4C7 | 0x528C00 | 同形@0x5CF4C3 | — | —（全部路径被 ret-unknown 剪枝：0x5CF5AC→0x5256F0 等） | **未闭合（D-sim 边界）** |
| 0x5D76A9 | 0x528C00 | `8d8c2488000000`@0x5D76A2 | — | —（sim 从头不可达，零剪枝因） | **未闭合（D-sim 边界）** |
| 0x76C555 | 0x528C00 | `8d4c2438`@0x76C551 | 0xE4→−0xAC | **`c7442430 f4a57e00`@0x76C4A4**（D=0xDC） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x778BCF | 0x528C00 | `8d4c2438`@0x778BCB | 0xF0→−0xB8 | **`c744242c f4a57e00`@0x778B20**（D=0xE4） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x778DD1 | 0x528C00 | 同形@0x778DCD | 0xF0→−0xB8 | 同上 0x778B20 | 同上 |
| 0x778E24 | 0x528C00 | 同形@0x778E20 | 0xF0→−0xB8 | 同上 0x778B20 | 同上 |

RTTI 定名（R-058 版式 vtable−4→COL→COL+0xC→TD→TD+8，probe13 §2，机器可复核）：
- **0x7EA5F4 = `.?AVINIClass@@`**（12 裸传行 witness 槽的真实 vptr）
- 0x7E1B04 = `.?AVGenericList@@`（复现 R-062 冻结命名 ✓）
- 0x7E1B0C = `.?AVGenericNode@@`；0x7E1AFC = `.?AV?$List@PAUINISection@INIClass@@@@`；
  0x7E1668 = `.?AVCDFileClass@@`（0x778ABB 块同帧多临时件槽复用的家族语境）。

宿主侧复核（probe7 §D / probe8 §2）：0x528C00（67 aligned callers）体前 200 条
**零** `mov [ecx…],imm32`，且 `3b5d04`@0x528C5A（读 this+4）、`8b7508`@0x528C63
（读 this+8）——纯消费方；0x527F20（7 callers）同型（读+写 [ebp+4]/[ebp+8]，
@0x527F6F/0x528070–82）。两宿主体内按全镜像 census 均无 0x7E1B04/0x7EA5F4
stamp ⇒ callee 侧构造排除（补完 probe5 欠账）。

## 5. 汇总计数

- ① unknown-reg 12 行：**12/12 于 3 跳内闭合，四类钉全部「终到参数槽（寄存器
  形参）」**（10 行→hub 0x4F38B0 edx 形参；2 行→H 0x4F1CA0 edx 形参；旁证同源）。
  未闭合 0；global-load 0；栈件构造 0。
- ② 裸传 12 行：外层四机制 0 命中（任务书口径保持未证）；**续算升格 10/12**
  为「帧内 INIClass（0x7EA5F4）栈件·vptr stamp 逐址钉死」；2 行（0x5CF4C7、
  0x5D76A9）D-sim 边界未闭合保持未证（同函数姊妹行与同函数 INIClass stamp
  0x5D761D 强烈暗示同型，不作证据）。
- 连带回测：R-062 冻结的 5 个「已构造」行 witness 槽同为 INIClass stamp
  （0x7787F7/0x779BEA/0x779E6A，见 §6）——**17 行 witness 对象实为 INIClass
  栈件一族**。
- 新发现（意外）：见证协议的对象语境=**INIClass**，非 GenericList；0x528C00/
  0x527F20 消费 this+4/this+8 数据字段、从不触碰 this+0 vptr；0x528C00 入口
  约定=ret 0x10（4 栈参），同区存在 5 个 ret 站点 imm 各异（0x10/0xC/0xC/0x14/
  0x14，多出口特征，登记待查）。

## 6. 冲突待勘误清单（不静默改史；均待异族复核后办理）

1. **R-062 §2「有帧内构造证据的 5 行」配对存疑**：冻结判据=stamp 与 lea 同字面
   `[esp+X]` 配对。D-归一化后：0x7787C0 stamp（D=0xC4）打 P=−0x8C，而
   0x77884F/90C/956 的 witness 格 W=−0x98（差 0xC）；0x779BB3/0x779E33 同病
   （P=−0x8C vs W=−0x98）。witness 格实际命中 INIClass stamp
   （0x7787F7/0x779BEA/0x779E6A）。且 0x7E1B04 stamp 格 P=−0x8C 在可达状态
   空间内**无任何 lea 消费者**（probe14 §B；push/指针式消费未穷尽）。⇒ 待勘误：
   「5 行传入 0x7E1B04 GenericList」应改为「5 行传入 0x7EA5F4 INIClass（witness
   格 D-归一化命中）；0x7E1B04 stamp 为同帧内其它对象，与 witness 调用无配对
   证据」。
2. **R-062 §2/§5「12 行临时件裸传、构造点未证」**：应精化为「10/12 行帧内
   on-path INIClass vptr stamp 已钉（逐址见 §4 表）；2 行未闭合；构造不在
   callee 侧（两宿主零 stamp 且消费 this+4/8）、不在更外层帧（四机制 0）」。
3. **R-062 §2 机制命名**：「caller 自带 GenericList 临时件」应更正为「caller
   自带 INIClass 栈件」；对 R-061「工厂件→见证连线候选新增栈件」的推论对象
   名随之更正（推论本身不变）。
4. 无冲突项：R-062 §2 标题比例词（1/3→1/4）已有勘误注在案；0x7E1B04 的
   RTTI 定名本轮复现一致；R-061/R-062「实例归属 UNKNOWN 保持」口径不变。

## 7. 诚实账与局限

- **模拟的条件性**：D-归一化 singleton 是「在全部 ret-imm 可静态判定路径上」
  的单例；被剪枝的 ret-unknown 支路（逐行 causes 实录于 `_r063b_probe14_out.txt`）
  若实际可达该行，其 D 贡献未证。旁证=编译器 disp−D 不变量在每帧两个远距
  站点自洽（§2），但这是佐证不是证明。门禁（126/126）与变异套件未纳入本判据
  ——若要升格为门禁级结论，须另立变异轮（建议后续任务）。
- **2 行未闭合**（0x5CF4C7/0x5D76A9）：前者全路径被 0x5256F0/0x526D90/
  间接 call（带待清参数）剪枝；后者 sim 图不可达且零剪枝因（待专项核查）。
  两行保持「未证」，不借用姊妹行结论。
- **3 跳上限纪律**：10 行组终到 hub edx 形参即止；「hub edx←H 的 [esp+0x20]
  ←H edx 形参」是超限旁证，只登记不计数。
- **实例身份仍 UNKNOWN**：两站合计 24 行全部只钉「值的来源链」，未命名任何
  对象实例；RTTI 定名是**类型**命名，与 R-058/R-062 口径一致。
- **前轮缺陷实录**（G-55/G-84 族，供后来者）：probe5 delta_walk KeyError
  （0x778AC3 跳入块前存在解码缝隙，insn 间距非连续）；probe6 witness-lea
  正则把助记符写进 op 匹配串（永不匹配）；callee_cleanup 40 条窗口过小且未
  跟 jmp 链足够深。三处皆已在 probe10–14 修正，原始输出保留未动。
- **写域附注**：本轮新建 `_r063b_probe7..14*.py` 8 个脚本与同名 `_out.txt`
  机器转储 8 份（转储为脚本证据件，沿前轮 probe1–6 保留先例）；除此之外未
  新建/修改任何文件。未真机；未读 BSS 现值；未宣称可改写点（C26-04）。
- 本件为**同族自查产物**：D-归一化判据、§6 两条待勘误、INIClass 定名均未过
  异族复核，状态=「待复核候选」，不得据此改写任何冻结文件。

## 8. 本轮新建文件清单

- 报告：`re_atlas/evidence/r063b_upward_second_hop.md`（本件）
- 脚本+转储：`re_atlas/tools/_r063b_probe7.py`（自验+链字节+edi+宿主侧）、
  `_r063b_probe8.py`（宿主表/序言/路径/邻接）、`_r063b_probe9.py`（ret 普查+
  前驱唯一性）、`_r063b_probe10.py`（D-sim v1）、`_r063b_probe11.py`（ret-hard
  重试，中途 TypeError 终止，其 §1 转储有效）、`_r063b_probe12.py`（D-sim v2+
  校准）、`_r063b_probe13.py`（回测+RTTI）、`_r063b_probe14.py`（D-sim v3 修正
  版，最终口径）及 `_r063b_probe7..14_out.txt`。
# R-063b · 2026-10-30 — unknown-reg 12 行第二跳上行收口 + 「GenericList 裸传 12 行」构造点上探（前轮中断续办）

对象：`ra2youli/gamemd.exe`（只读）。本轮机器自验 sha256
`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
（`_r063b_probe7_out.txt` §A，与 R-062 冻结值逐字符相等）。PE：ImageBase
0x400000，.text=[0x401000,0x7E1000)。纯离线反汇编，零真机，未运行游戏，
未宣称可改写点。写域：仅新建 `re_atlas/evidence/r063b_upward_second_hop.md`
（本件）与 `re_atlas/tools/_r063b_probe7..14*.py`（临时脚本，编号接续前轮
probe1–6）；未修改任何既有文件（git 工作区核对，前轮 probe1–6 及其输出原样）。

## 0. 证据版本

- 门禁/契约（只读复用，未改动）：`tools/r062_upward_trace_contract.py`
  （frame_lo=ret 界窗、slot_writers=窗内同字面槽写、classify_call 冻结语义）、
  `tools/r061_witness_this_contract.py`（SMALL 七宿主、GLOBALS、EXE 路径）。
- 本轮机器转储（G-65 纪律，全保留）：`_r063b_probe7_out.txt` …
  `_r063b_probe14_out.txt` 共 8 份，每份与其脚本同名配套。
- 前轮中断产物（只读引用，未重算其中已完成部分）：`_r063b_chain_dump.txt`
  （CHAIN 88 行）、`_r063b_probe1..6.py` 及 `_r063b_probe1_out.json`、
  `_r063b_probe2..6_out.txt`。

## 1. 交接说明：前次产物编号与本次续办边界

前轮执行 112 分钟后死于 Provider 认证故障，报告未出。恢复盘点：

| 前轮产物 | 内容 | 状态 |
|:--|:--|:--|
| `_r063b_chain_dump.txt` | R-062 CHAIN 88 行冻结字面量（含 12 unknown-reg、1 unknown-thunk、17 stack-object） | 完整，直接采用 |
| `probe1` + `probe1_out.json` | 12 unknown-reg 行 hop2：含帧 esi/edx 写者普查、F 唯一 caller、call 站点 reg 溯源 | 完整有效，直接引用 |
| `probe2` + out | 12 裸传行确认（5 已构造/12 裸传复核通过）；全镜像 imm32 0x7E1B04 45 处直写清点；外层调用者帧 vptr 直写普查=全零 | 完整有效，直接引用 |
| `probe3` + out | unknown-reg hop3（esi←edx@hub 入口；2 行 esi←[esp+0x20]）；数据段 0x7E1B04 持有者=空；F 帧 direct/lea/indirect 槽写普查 | 完整有效，直接引用 |
| `probe4` + out | 45 处全为 c7 mem-store（无 reg-dest/push 形态，Q5=空）；0x778a20 窗口/汇合/三 witness 原始字节；hub 入度=1（冷入口）；[esp+0x20] 窗内零写者 | 完整有效，直接引用 |
| `probe5` + out | **崩溃**（delta_walk KeyError，0x778ac7 前存在解码缝隙）：edi 溯源、物理槽、0x528C00 callee-side 检查均未产出 | 作废，由本轮 probe7/12 重做 |
| `probe6` + out | 线性栈模拟**两处缺陷**：witness-lea 正则永不匹配（op 串不含助记符）；callee ret-cleanup 全 unknown ⇒ 其 phys 偏移数不可信 | 数值作废；其列出的分歧点仍有效，由本轮 probe10–14 重做 |

本轮续办边界：①前轮已算的部分不重做，报告逐处引用产物编号；②补齐 probe5
崩溃与 probe6 缺陷留下的四个未完成项（edi@0x778ac7 溯源、0x528C00 callee
侧检查、witness 槽物理归属、路径敏感 D 记账）；③按任务书完成 12 行第二跳
四类钉与 12 裸传行外层四机制普查。

## 2. 方法（本轮新增）

**D-归一化路径敏感抽象解释**（`_r063b_probe10/12/14.py`）：以 E8 头为 D=0
基线（D=esp 相对函数入口的沉降量），沿门禁流图前向 DFS（jcc 双臂、memo
按地址合并 D 集、>8 值记 D-ambig、穿 ret 即剪枝），物理格 P=disp−D。D 移动
只认 push/pop/sub esp/add esp/call(ret-imm)。三条**可证**补充规则（逐条带
证据）：

1. **call 站点零 push ⇒ ret-imm=0**：自上一锚点（已清算 call / add esp）以来
   零 push，则 callee 无栈参可清，cdecl/stdcall 两种约定下 D 效应同为 0
   （用于 0x778b47→0x7b5b30、0x5d7c86→0x5256f0、0x76c692→0x5256f0，
   后两者 census 200k 条仍无 ret）。
2. **call 后同 disp 重读 ⇒ 栈已复原**：0x5cef6b `ff5008`（call [eax+8]，前推
   1 参）后 0x5cef6e 以同一 disp 重读 [esp+0x68]；0x5cef78 同理（0x5cef7b）
   ⇒ 该两处间接 call 清 4 字节。
3. **保 esp 指令中性**：`mov reg,esp`/`mov [m],esp` 不改 D（probe12 曾误剪枝
   导致 5d76a9 空转，probe14 修正）；唯写 esp 的指令（mov esp,…/leave 等）
   才剪枝并记因。

**方法自校准**：同一解释器对 0x778a20 帧手算复核（probe9 ret 全普查：入口
epilogue `0x778b95 pop edi/esi/ebx + add esp,0xd0` 与序言严格对称）；编译器
disp−D 不变量在多点自洽（0x5ceef0：0x28@D=0xd4 与 0x38@D=0xe4 同格；0x76c290：
0x30@0xdc 与 0x38@0xe4 同格；0x778a20：0x2c@0xe4 与 0x38@0xf0 同格——三帧
独立成立，D 记账错 4/8/0xC 字节即全部失配）。

## 3. ① unknown-reg 12 行·第二跳上行判定表（四类钉）

hop 记账：hop1=R-062 冻结（行帧内链死在 callee-saved 寄存器）；hop2=跨帧到
唯一 caller 的 call 站点；hop3=再一层写者。四类钉：终到 global-load / 终到
栈件构造 / 终到参数槽 / 未闭合 UNKNOWN+边界。

**A1 组（F1=0x4F2C70，3 行）**——前轮 probe1/3 已算，本轮 probe7/8 复钉 call 字节：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F2CED | 0x528C00 | `8bce`+`e80e5f0300`→hop2 `8bd6`@0x4F3976→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F1 唯一 caller 0x4F397A `e8f1f2ffff`；hub 0x4F38B0 序言 `mov esi,edx` |
| 0x4F2D5C | 0x528C00 | `8bce`+`e89f5e0300`→同上 | 同上 | 同上 |
| 0x4F2E30 | **0x527F20** | `8bce`+`e8eb500300`→同上 | 同上 | 同上 |

**A2 组（F2=0x4F3140，6 行）**——前轮 probe1/3 已算，本轮 probe7/8 复钉：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F3219 | **0x527F20** | `8bce`+`e8024d0300`→hop2 `8bd6`@0x4F392E→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F2 唯一 caller 0x4F3932 `e809f8ffff` |
| 0x4F32A4 | 0x528C00 | `8bce`+`e857590300`→同上 | 同上 | 同上 |
| 0x4F32E9 | 0x528C00 | `8bce`+`e812590300`→同上 | 同上 | 同上 |
| 0x4F332E | 0x528C00 | `8bce`+`e8cd580300`→同上 | 同上 | 同上 |
| 0x4F337C | 0x528C00 | `8bce`+`e87f580300`→同上 | 同上 | 同上 |
| 0x4F33CA | 0x528C00 | `8bce`+`e831580300`→同上 | 同上 | 同上 |

**A3 组（F3=0x4F3B80，1 行）**——前轮 probe1/3 已算：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F3BF3 | 0x528C00 | `8bce`+`e808500300`→hop2 `8bd6`@0x4F394B→hop3 `8bf2`@0x4F38B8 | **终到参数槽（寄存器形参）** | F3 唯一 caller 0x4F394F `e82c020000` |

**B 组（hub 0x4F38B0 帧内，2 行）**——前轮 probe1/3/4 已算，本轮 probe7/8 复钉：

| 行 VA | call 目标 | 链字节全串 | 新 verdict | 证据 VA |
|:--|:--|:--|:--|:--|
| 0x4F38F9 | 0x528C00 | `8bce;8bf2`+`e802530300`→hop2 `8bd6`@0x4F20B7→hop3 `8b742420`@0x4F207C | **终到参数槽（寄存器形参 edx@H=0x4F1CA0 入口）** | hub 唯一 caller 0x4F20C1 `e8ea170000`；[esp+0x20] 窗内零写=参数槽，窗外写者=H 序言 `89542420`@0x4F1CAF（edx spill） |
| 0x4F39C1 | 0x528C00 | `8bce;8bf2`+`e83a520300`→同上 | 同上 | 同上 |

闭合陈述：
- **10 行（A1+A2+A3）3 跳内终到 hub 0x4F38B0 的 edx 形参**（fastcall 第 2 参；
  帧内 esi 镜像 @0x4F38B8；esi 全函数唯一写者=该序言 mov，probe7 §G 普查钉）。
- **2 行（B 组）3 跳内终到 H=0x4F1CA0 的 edx 形参**（H 唯一 caller 0x4F1C53；
  probe7 §H）。
- **同源性旁证（超 3 跳上限，仅登记不升格）**：hub 的 edx@entry 经其唯一
  caller（H 帧内 0x4F20B7 `mov edx,esi`→0x4F207C `mov esi,[esp+0x20]`→
  0x4F1CAF `mov [esp+0x20],edx`）同样归于 H 的 edx 形参——**12 行全部同源**。
- 四类钉计数：终到参数槽 **12**（寄存器形参形态）；终到 global-load 0；终到
  栈件构造 0；未闭合 UNKNOWN **0**。
- 措辞边界：链上只钉「值从哪里来」，实例身份仍 UNKNOWN（与 R-061/R-062 冻结
  口径一致，不减不增）；「寄存器形参」是参数槽的寄存器形态，非栈槽形态，
  报告如实分列。

## 4. ② 「GenericList 裸传 12 行」构造点上探判定表

外层四机制普查（任务书口径，probe2/3/4 前轮完成）：更外层调用者帧内
`mov [esp+X],0x7E1B04` 三窗形态 **0**；等价 vptr store（reg 中转）**0**
（全镜像无 `mov reg,0x7E1B04` reg-dest 形态，probe4 Q5=空）；imm32 直写其它
形态 **0**（45 处全为 c7 mem-store，probe4 Q1）；数据段装载中转 **0**
（0x7E1B04 双字全镜像仅存在于 .text 指令立即数内，probe3 holders=[]）。
按任务书字面 ⇒ 找不到 ⇒ 保持未证。

本轮续算（超出任务书字面，为诚实账补 probe5/6 欠账）在**本帧内**完成
D-归一化后得到下表——「裸传」是门禁同字面 disp 配对（无 esp 归一）的伪象：

| 行 VA | call 目标 | witness lea | D(row)→物理格 W | on-path 写者（D-归一化命中） | 新 verdict |
|:--|:--|:--|:--|:--|:--|
| 0x5CEFC9 | 0x528C00 | `8d4c2438`@0x5CEFC5 | 0xE4→−0xAC | **`c7442428 f4a57e00`@0x5CEF41**（[esp+0x28]←0x7EA5F4，D=0xD4） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x5CF10E | 0x528C00 | 同形@0x5CF10A | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF162 | 0x528C00 | 同形@0x5CF15E | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF284 | 0x528C00 | 同形@0x5CF280 | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF2E0 | 0x528C00 | 同形@0x5CF2DC | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF42C | 0x528C00 | 同形@0x5CF428 | 0xE4→−0xAC | 同上 0x5CEF41 | 同上 |
| 0x5CF4C7 | 0x528C00 | 同形@0x5CF4C3 | — | —（全部路径被 ret-unknown 剪枝：0x5CF5AC→0x5256F0 等） | **未闭合（D-sim 边界）** |
| 0x5D76A9 | 0x528C00 | `8d8c2488000000`@0x5D76A2 | — | —（sim 从头不可达，零剪枝因） | **未闭合（D-sim 边界）** |
| 0x76C555 | 0x528C00 | `8d4c2438`@0x76C551 | 0xE4→−0xAC | **`c7442430 f4a57e00`@0x76C4A4**（D=0xDC） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x778BCF | 0x528C00 | `8d4c2438`@0x778BCB | 0xF0→−0xB8 | **`c744242c f4a57e00`@0x778B20**（D=0xE4） | **帧内 INIClass 栈件·vptr stamp 已钉** |
| 0x778DD1 | 0x528C00 | 同形@0x778DCD | 0xF0→−0xB8 | 同上 0x778B20 | 同上 |
| 0x778E24 | 0x528C00 | 同形@0x778E20 | 0xF0→−0xB8 | 同上 0x778B20 | 同上 |

RTTI 定名（R-058 版式 vtable−4→COL→COL+0xC→TD→TD+8，probe13 §2，机器可复核）：
- **0x7EA5F4 = `.?AVINIClass@@`**（12 裸传行 witness 槽的真实 vptr）
- 0x7E1B04 = `.?AVGenericList@@`（复现 R-062 冻结命名 ✓）
- 0x7E1B0C = `.?AVGenericNode@@`；0x7E1AFC = `.?AV?$List@PAUINISection@INIClass@@@@`；
  0x7E1668 = `.?AVCDFileClass@@`（0x778ABB 块同帧多临时件槽复用的家族语境）。

宿主侧复核（probe7 §D / probe8 §2）：0x528C00（67 aligned callers）体前 200 条
**零** `mov [ecx…],imm32`，且 `3b5d04`@0x528C5A（读 this+4）、`8b7508`@0x528C63
（读 this+8）——纯消费方；0x527F20（7 callers）同型（读+写 [ebp+4]/[ebp+8]，
@0x527F6F/0x528070–82）。两宿主体内按全镜像 census 均无 0x7E1B04/0x7EA5F4
stamp ⇒ callee 侧构造排除（补完 probe5 欠账）。

## 5. 汇总计数

- ① unknown-reg 12 行：**12/12 于 3 跳内闭合，四类钉全部「终到参数槽（寄存器
  形参）」**（10 行→hub 0x4F38B0 edx 形参；2 行→H 0x4F1CA0 edx 形参；旁证同源）。
  未闭合 0；global-load 0；栈件构造 0。
- ② 裸传 12 行：外层四机制 0 命中（任务书口径保持未证）；**续算升格 10/12**
  为「帧内 INIClass（0x7EA5F4）栈件·vptr stamp 逐址钉死」；2 行（0x5CF4C7、
  0x5D76A9）D-sim 边界未闭合保持未证（同函数姊妹行与同函数 INIClass stamp
  0x5D761D 强烈暗示同型，不作证据）。
- 连带回测：R-062 冻结的 5 个「已构造」行 witness 槽同为 INIClass stamp
  （0x7787F7/0x779BEA/0x779E6A，见 §6）——**17 行 witness 对象实为 INIClass
  栈件一族**。
- 新发现（意外）：见证协议的对象语境=**INIClass**，非 GenericList；0x528C00/
  0x527F20 消费 this+4/this+8 数据字段、从不触碰 this+0 vptr；0x528C00 入口
  约定=ret 0x10（4 栈参），同区存在 5 个 ret 站点 imm 各异（0x10/0xC/0xC/0x14/
  0x14，多出口特征，登记待查）。

## 6. 冲突待勘误清单（不静默改史；均待异族复核后办理）

1. **R-062 §2「有帧内构造证据的 5 行」配对存疑**：冻结判据=stamp 与 lea 同字面
   `[esp+X]` 配对。D-归一化后：0x7787C0 stamp（D=0xC4）打 P=−0x8C，而
   0x77884F/90C/956 的 witness 格 W=−0x98（差 0xC）；0x779BB3/0x779E33 同病
   （P=−0x8C vs W=−0x98）。witness 格实际命中 INIClass stamp
   （0x7787F7/0x779BEA/0x779E6A）。且 0x7E1B04 stamp 格 P=−0x8C 在可达状态
   空间内**无任何 lea 消费者**（probe14 §B；push/指针式消费未穷尽）。⇒ 待勘误：
   「5 行传入 0x7E1B04 GenericList」应改为「5 行传入 0x7EA5F4 INIClass（witness
   格 D-归一化命中）；0x7E1B04 stamp 为同帧内其它对象，与 witness 调用无配对
   证据」。
2. **R-062 §2/§5「12 行临时件裸传、构造点未证」**：应精化为「10/12 行帧内
   on-path INIClass vptr stamp 已钉（逐址见 §4 表）；2 行未闭合；构造不在
   callee 侧（两宿主零 stamp 且消费 this+4/8）、不在更外层帧（四机制 0）」。
3. **R-062 §2 机制命名**：「caller 自带 GenericList 临时件」应更正为「caller
   自带 INIClass 栈件」；对 R-061「工厂件→见证连线候选新增栈件」的推论对象
   名随之更正（推论本身不变）。
4. 无冲突项：R-062 §2 标题比例词（1/3→1/4）已有勘误注在案；0x7E1B04 的
   RTTI 定名本轮复现一致；R-061/R-062「实例归属 UNKNOWN 保持」口径不变。

## 7. 诚实账与局限

- **模拟的条件性**：D-归一化 singleton 是「在全部 ret-imm 可静态判定路径上」
  的单例；被剪枝的 ret-unknown 支路（逐行 causes 实录于 `_r063b_probe14_out.txt`）
  若实际可达该行，其 D 贡献未证。旁证=编译器 disp−D 不变量在每帧两个远距
  站点自洽（§2），但这是佐证不是证明。门禁（126/126）与变异套件未纳入本判据
  ——若要升格为门禁级结论，须另立变异轮（建议后续任务）。
- **2 行未闭合**（0x5CF4C7/0x5D76A9）：前者全路径被 0x5256F0/0x526D90/
  间接 call（带待清参数）剪枝；后者 sim 图不可达且零剪枝因（待专项核查）。
  两行保持「未证」，不借用姊妹行结论。
- **3 跳上限纪律**：10 行组终到 hub edx 形参即止；「hub edx←H 的 [esp+0x20]
  ←H edx 形参」是超限旁证，只登记不计数。
- **实例身份仍 UNKNOWN**：两站合计 24 行全部只钉「值的来源链」，未命名任何
  对象实例；RTTI 定名是**类型**命名，与 R-058/R-062 口径一致。
- **前轮缺陷实录**（G-55/G-84 族，供后来者）：probe5 delta_walk KeyError
  （0x778AC3 跳入块前存在解码缝隙，insn 间距非连续）；probe6 witness-lea
  正则把助记符写进 op 匹配串（永不匹配）；callee_cleanup 40 条窗口过小且未
  跟 jmp 链足够深。三处皆已在 probe10–14 修正，原始输出保留未动。
- **写域附注**：本轮新建 `_r063b_probe7..14*.py` 8 个脚本与同名 `_out.txt`
  机器转储 8 份（转储为脚本证据件，沿前轮 probe1–6 保留先例）；除此之外未
  新建/修改任何文件。未真机；未读 BSS 现值；未宣称可改写点（C26-04）。
- 本件为**同族自查产物**：D-归一化判据、§6 两条待勘误、INIClass 定名均未过
  异族复核，状态=「待复核候选」，不得据此改写任何冻结文件。

## 8. 本轮新建文件清单

- 报告：`re_atlas/evidence/r063b_upward_second_hop.md`（本件）
- 脚本+转储：`re_atlas/tools/_r063b_probe7.py`（自验+链字节+edi+宿主侧）、
  `_r063b_probe8.py`（宿主表/序言/路径/邻接）、`_r063b_probe9.py`（ret 普查+
  前驱唯一性）、`_r063b_probe10.py`（D-sim v1）、`_r063b_probe11.py`（ret-hard
  重试，中途 TypeError 终止，其 §1 转储有效）、`_r063b_probe12.py`（D-sim v2+
  校准）、`_r063b_probe13.py`（回测+RTTI）、`_r063b_probe14.py`（D-sim v3 修正
  版，最终口径）及 `_r063b_probe7..14_out.txt`。


---

## 办理注（2026-10-30，Leader 依 R-064 裁定书·台账 §471）

§6 三条待勘误候选**全部转已裁定**（R-064 裁定书 §5 #5/#6/#7 CONFIRMED）；§5 自报『2 行未闭合』
（0x5CF4C7/0x5D76A9）由 R-064 §3 收口为 **12/12**（新断言随本件办理）；§7『待复核候选』状态升格为
『已仲裁确认』。本书 D-归一化方法学经 R-064 独立复用（STRICT/HYP4/HYPV 三模式+CCFileClass vtable
直读落实两处间接调用+HYPV 依赖性实验）并扩展收口。

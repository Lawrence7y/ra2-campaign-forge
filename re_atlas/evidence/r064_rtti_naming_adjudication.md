# R-064 · 2026-10-30 — RTTI 定名仲裁：R-062 冻结口径（GenericList 临时件）vs R-063b 待勘误候选（INIClass 栈件）

- 甄别员：RE-ATLAS 线独立甄别员（全新上下文，亲自取证，未复用两书任一探针/脚本；工具链 Python 3.12 + capstone 5.0.7）。
- 对象：`ra2youli/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
  （本轮机器自验逐字符相等；镜像只读、零真机、未运行游戏）。
- 写域：仅本裁定书 + `re_atlas/tools/_r064_probe1..4.py`（临时脚本）。既有文件零改动——
  R-062 书/R-063b 书/门禁/套件/两份复核/LEDGER 的 mtime 全部早于本会话起点（实测在案）。
- **本件为仲裁产物：结论在 Leader 依 §6 办理勘误之前，不构成对任何冻结文件的改写。**

## 0. 证据版本

| 物 | 版本锚 | 本轮核验 |
|:--|:--|:--|
| 镜像 | sha256 `73201cc0…f67476` | ✓ 逐字符相等 |
| R-062 书 §2 冻结口径 | 三方独立复现 CONFIRMED（门禁 126 + C 线复核 §4 + 异族复核 §2） | 原文只读引用 |
| R-063b 书 §4/§6 待勘误候选 | 同族自查自标「待复核候选」 | 原文只读引用 |
| 17 行 CHAIN 冻结字面量 | `r062_upward_trace_contract.py --dump`（EXIT=0，88 行） | 本轮亲跑提取 17 行 stack-object 原文 |
| 机器转储 | /tmp/r064_p1/p2/p3_{strict,hyp4,hypv}/p4.txt（系统临时目录，沿 OOF 先例未落工作区） | 全部本轮生成 |

本轮自建工具（全在 `re_atlas/tools/_r064_*.py`）：
`_r064_probe1.py`（PE 装载 + RTTI walk + 字节验）、`_r064_probe2.py`（关键帧线性反汇编窗口）、
`_r064_probe3.py`（E8 目标前向闭包 + 前驱图 + 回溯定头 + **闭包 ret-imm 解析** + 路径敏感 esp-D 归一化，
三模式 STRICT/HYP4/HYPV）、`_r064_probe4.py`（虚拟 call vtable 直读落实 + 全帧 store 普查 + 归属表）。

## 1. RTTI 双链逐级字节 walk（两链各自走通）

walk 语义（MSVC 32 位，与任务书一致，且以「TD 名非乱码 + 控制位复现」自证）：
**vptr 写入值 V → vtable[-1]（地址 V−4）存 COL 指针 → COL+0xC 存 TD 指针 → TD+8 起为 NUL 结尾内联名**。

**家族 1（R-062 冻结 stamp 立即数）V=0x7E1B04 → `.?AVGenericList@@`**：

```
[0x7E1B00] = 18 ad 7f 00        → COL = 0x7FAD18
COL@0x7FAD18: sig=0 off=0 cdOff=0
[0x7FAD24] (COL+0xC) = 08 75 81 00 → TD = 0x817508
TD@0x817508: vfp=[0x817508]=0x7F9594（type_info vtable，健全性锚 ✓） spare=0
TD+8 名 = '.?AVGenericList@@'
[COL+0x10] → CHD 0x7FAD08: numBases=1（基类数组仅 GenericList 自身）
```

**家族 2（R-063b 候选 stamp 立即数）V=0x7EA5F4 → `.?AVINIClass@@`**：

```
[0x7EA5F0] = 10 25 80 00        → COL = 0x802510
COL@0x802510: sig=0 off=0 cdOff=0
[0x80251C] (COL+0xC) = b0 74 81 00 → TD = 0x8174B0
TD@0x8174B0: vfp=0x7F9594 ✓ spare=0
TD+8 名 = '.?AVINIClass@@'
[COL+0x10] → CHD 0x802500: numBases=1（基类数组仅 INIClass 自身）
```

控制位复现：`[0x8174C8]`=`94957f00`（vfp 0x7F9594 ✓），`0x8174D0` 名=`.?AVCCINIClass@@`——
与 R-062 §2 及 C 线复核 §4 所载控制位逐字节一致。语境家族同轮走通：
`0x7E1B0C`→`.?AVGenericNode@@`；`0x7E1AFC`→`.?AV?$List@PAUINISection@INIClass@@@@`
（**CHD numBases=2：List<INISection*> 的基类恰含 GenericList**——R-062 §2「与 R-058 B6 的
List 头件基类 vtable 同一张表」此句本身为真）；`0x7E1668`→`.?AVCDFileClass@@`
（numBases=4，: BufferIOFileClass : RawFileClass : FileClass）。

## 2. witness 写入值逐行验（字节层）

**R-062 三窗**（盘上直读，与冻结字面量全等）：

| VA | 字节 | 语义 |
|:--|:--|:--|
| 0x7787C0 | `c7 44 24 38 04 1b 7e 00` | mov [esp+0x38], 0x7E1B04 |
| 0x779BB3 | `c7 44 24 24 04 1b 7e 00` | mov [esp+0x24], 0x7E1B04 |
| 0x779E33 | `c7 44 24 24 04 1b 7e 00` | mov [esp+0x24], 0x7E1B04 |

⇒ **R-062 三窗写的立即数确实是 0x7E1B04**（R-063b「witness 格实为另一值」在字节层不成立——
争议不在立即数本身，而在该立即数落进哪个物理槽，见 §3）。

**R-063b 三处 stamp**（同样盘上真实）：

| VA | 字节 | 语义 |
|:--|:--|:--|
| 0x5CEF41 | `c7 44 24 28 f4 a5 7e 00` | mov [esp+0x28], 0x7EA5F4 |
| 0x76C4A4 | `c7 44 24 30 f4 a5 7e 00` | mov [esp+0x30], 0x7EA5F4 |
| 0x778B20 | `c7 44 24 2c f4 a5 7e 00` | mov [esp+0x2C], 0x7EA5F4 |

**R-063b §6.1 声称的 R-062 三帧内「补 stamp」**（R-062 书从未提及，本轮验证全部在盘）：

| VA | 字节 | 语义 | 所在帧（函数头，probe3 回溯定头） |
|:--|:--|:--|:--|
| 0x7787F7 | `c7 44 24 30 f4 a5 7e 00` | mov [esp+0x30], 0x7EA5F4 | 帧 A=0x778710（与窗 1 同帧，+0x37 字节） |
| 0x779BEA | `c7 44 24 1c f4 a5 7e 00` | mov [esp+0x1C], 0x7EA5F4 | 帧 B=0x779B50（与窗 2 同帧，+0x37） |
| 0x779E6A | `c7 44 24 1c f4 a5 7e 00` | mov [esp+0x1C], 0x7EA5F4 | 帧 C=0x779DD0（与窗 3 同帧，+0x37） |

同帧还存在 List<INISection*> stamp（0x7787D1/0x779BC4/0x779E44 等写 0x7E1AFC）与
CDFileClass stamp（0x778B83 写 0x7E1668 等）——每帧是**多临时件构造簇**，非单对象。

**VA 交集判定（任务书方法 2 后半）**：R-062 的 5 行（0x77884F/0x77890C/0x778956/0x779C3D/
0x779EBD）与 R-063b 三 stamp 所在函数（帧 0x5CEEF0/0x76C290/0x778A20）——**VA 零交集、
函数零交集**。R-063b 的三 stamp 服务的 12 裸传行与 R-062 的 5 行是**完全不同的两批行**；
两书的真实冲突只有一处：R-063b §6.1 主张 **R-062 自己的 5 行 witness 槽**由同帧补 stamp
（0x7787F7/0x779BEA/0x779E6A）打入 INIClass vptr，而 R-062 的 GenericList 三窗配对错位。

## 3. D-归一化逐行配对（裁定核心；独立实现）

方法：以 E8 目标前向闭包建函数体与前驱图（7,279 目标 / 738,935 指令），回溯定头
（每 witness 行与每 stamp 的头候选均为唯一，见 probe3 §2/§3 输出）；路径敏感 DFS 模拟
`D = 函数入口以来 esp 沉降量`（push +4 / pop −4 / sub +imm / add −imm / call 按 callee
ret-imm 结算 / jcc 双臂 / ret 剪枝 / esp 写剪枝）；**ret-imm 用「callee 闭包内全部 ret 求
交集」解析**（单 ret 与全 ret 一致才采信；0x528C00=ret 0x10 ✓、0x527F20=ret 0x10 ✓、
0x525A10=ret 8、0x40E340=ret 4、0x7B6290=ret 0、0x5295F0=ret 0xC、0x526D90=ret 0xC 等
全表见 probe3 §5）。物理格 P = disp − D。witness 槽 W = lea disp − D(lea)。

**17 行逐行归属表**（D 均为单例；W=各自行 witness 槽物理格）：

| 行 VA | 帧 | D(lea) | W | 命中 stamp（同帧唯一） | stamp D | stamp P | 证据强度 |
|:--|:--|:--|:--|:--|:--|:--|:--|
| 0x77884F | A 0x778710 | 0xD0 | −0x98 | **I-A** 0x7787F7←0x7EA5F4 | 0xC8 | −0x98 | STRICT |
| 0x77890C | A | 0xD0 | −0x98 | I-A | 0xC8 | −0x98 | STRICT |
| 0x778956 | A | 0xD0 | −0x98 | I-A | 0xC8 | −0x98 | STRICT |
| 0x779C3D | B 0x779B50 | 0xBC | −0x98 | **I-B** 0x779BEA←0x7EA5F4 | 0xB4 | −0x98 | STRICT |
| 0x779EBD | C 0x779DD0 | 0xBC | −0x98 | **I-C** 0x779E6A←0x7EA5F4 | 0xB4 | −0x98 | STRICT |
| 0x76C555 | E 0x76C290 | 0xE4 | −0xAC | **I-E** 0x76C4A4←0x7EA5F4 | 0xDC | −0xAC | STRICT |
| 0x778BCF | F 0x778A20 | 0xF0 | −0xB8 | **I-F** 0x778B20←0x7EA5F4 | 0xE4 | −0xB8 | STRICT |
| 0x778DD1 | F | 0xF0 | −0xB8 | I-F | 0xE4 | −0xB8 | STRICT |
| 0x778E24 | F | 0xF0 | −0xB8 | I-F | 0xE4 | −0xB8 | STRICT |
| 0x5D76A9 | 16 0x5D7590 | 0x134 | −0xAC | **I-16** 0x5D761D←0x7EA5F4 | 0x124 | −0xAC | STRICT |
| 0x5CEFC9 | D 0x5CEEF0 | 0xE4 | −0xAC | **I-D** 0x5CEF41←0x7EA5F4 | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF10E | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF162 | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF284 | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF2E0 | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF42C | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |
| 0x5CF4C7 | D | 0xE4 | −0xAC | I-D | 0xD4 | −0xAC | vtable 落实 |

同时刻同帧对照：**R-062 三窗（GenericList）物理格 P 全部 ≠ W**——
帧 A/B/C：G-stamp P=−0x8C vs W=−0x98，**错位恒 0xC**（错位机制，帧 A 逐项：
stamp@D=0xC4 → call 0x40E340(ret 4) −4 → push ebx/ecx +8 → call 0x525A10(ret 8) −8 →
0x4325C0/0x7B5440/0x526810/0x7B4630 净 0 → 4 个 witness 实参 push +0x10 ⇒ lea@D=0xD0）。
门禁「stamp 与 lea 同字面 disp」（0x38/0x24）在 esp 移动下配到两个不同物理格——
**同字面 disp ≠ 同槽**，判据本身不成立。

证据强度说明：
- **STRICT**（9 行）：全程零假设闭合——ret-imm 全由闭包 ret 交集给出，未知 ret-imm 的
  call 仅在零推（pushes=0，两种调用约定下 D 效应同为 0）时放行。
- **vtable 落实**（帧 D 7 行）：路径上两处间接虚拟 call `call [eax+8]`@0x5CEF6B 与
  `call [edx+0x1C]`@0x5CEF78 由 vtable 直读落实——对象=0x473A80 构造的 **CCFileClass**
  （其体 @0x473A9B stamp `[esi]=0x7E16B0`，TD 名 `.?AVCCFileClass@@`）；vtable
  `[0x7E16B0+8]=0x473FC0`（闭包单 ret=4）、`[0x7E16B0+0x1C]=0x473D10`（闭包 4 个 ret
  **恒为 4**）——两处均为「1 推 1 清」，即 R-063b 规则 2 的结论被升级为字节事实。
  **依赖性实验**（HYPV 模式）：只采信这两处已落实调用、把帧 D 其余三处未落实虚拟 call
  （0x5CF038/0x5CF350/0x5CF556，各假设清 8）一律剪枝后，**7 行仍在 D=0xE4 单例闭合**
  ——D 记账不依赖任何未落实假设。
- 构造完整性补强（超出两书的新证据）：每帧 witness INIClass 对象不止有 vptr stamp——
  stamp 后紧跟 `call 0x525A10`（INIClass 构造体，ret 8），且其 `this`（lea）与 stamp 同 disp
  同 D 同格：帧 A 0x7787DB/0x7787FF、帧 B 0x779BCE/0x779BF2、帧 C 0x779E4E/0x779E72、
  帧 D 0x5CEF81/0x5CEF85、帧 E 0x76C480/0x76C4AC、帧 F 0x778B03/0x778B28——
  **「帧内 INIClass 栈件·已构造」成立，弱于 R-062 所想、强于 R-063b 所写。**

## 4. 两家族关系：组合（HAS-A），非继承

- **互不为对方基类**：GenericList CHD numBases=1、INIClass CHD numBases=1，双方基类数组
  均不含对方 TD（probe1 §C 双向判定 False）；vtable 相距 0x8AF0，分属 .rdata 不同簇。
- **INIClass 内嵌 GenericList 成员**（直接字节证据，INIClass 析构/复位函数 0x5256F0 体内）：
  `0x5256F8: mov [esi], 0x7EA5F4`（置 INIClass vptr）→ `0x52571E: mov [esi+0xC], 0x7E1B04`
  （**INIClass+0xC 处的 GenericList 成员**）→ `0x525760/0x52578D: mov [eax], 0x7E1B0C`
  （+0x1C/+0x10 处 GenericNode 头件，即 List<INISection*> 的节点头）。
- ⇒ 两定名**各自都对**：0x7E1B04 是（独立类）GenericList 的 vtable，0x7EA5F4 是 INIClass 的
  vtable；INIClass 通过成员方式含 GenericList，caller 帧里两类临时件可以并存（事实上帧 A 的
  −0x8C 槽先被 GenericList 占用、再被 List<INISection*> 复用，−0x98 槽是 INIClass）。
  争议的答案不是「哪个名字对」，而是「哪个对象被传进了 0x528C00」——见 §5。

## 5. 裁定

| # | 命题 | 裁定 | 依据 |
|:--|:--|:--|:--|
| 1 | R-062 §2「三窗字节 + RTTI 名 .?AVGenericList@@」 | **成立（字节层）** | §2 表逐字节复现 + §1 链复现 |
| 2 | R-062 §2「有帧内构造证据的 5 行＝已构造 **GenericList** 传入 0x528C00」 | **REFUTED** | stamp 物理格 P=−0x8C，witness 格 W=−0x98，错位恒 0xC（§3）；witness 槽由同帧补 stamp 打入 0x7EA5F4 |
| 3 | R-062 §2/§5 对 17 行 witness 对象的「GenericList 临时件/栈件」命名 | **REFUTED**（应更正为 **INIClass 栈件**） | §3 表 17/17 唯一命中同帧 INIClass stamp + 0x525A10 this-同格构造链 |
| 4 | R-062 §1 门禁 126 断言、17 行 stack-object verdict、lea 邻接 | **维持**（不受本仲裁影响） | 门禁断言钉的是字节与 verdict；「配对」只在书 prose 层（门禁源码核过：U-vptrstore 三窗字节、U-rtti-name、U-lea-adj，均字节真） |
| 5 | R-063b §6.1 ①（5 行配对不成立、witness 格实为 INIClass stamp） | **CONFIRMED** | §3 表帧 A/B/C 三行 + 0x7787F7/0x779BEA/0x779E6A 字节与 D 值全中（stamp D=0xC4/0xB0/0xB0、P=−0x8C 与书一致） |
| 6 | R-063b §6.2 ②（12 裸传行 10/12 升格 INIClass、2 行未闭合） | **CONFIRMED 且加强** | 其 10 行 D 值逐行全中（0xE4/0xE4/0xF0）；其所报 2 行未闭合（0x5CF4C7、0x5D76A9）**本轮裁定收口**：0x5CF4C7 在 HYPV（纯已落实事实）下 D=0xE4 闭合；0x5D76A9 在 STRICT 下 D=0x134 闭合（0x526D90=ret 0xC，其 3 个实参 push 与 ret 精确对账）——**12/12 均为 INIClass**，此 2 行闭合属本轮新断言，随本裁定书走办理链 |
| 7 | R-063b §6.3 ③（机制命名更正为「caller 自带 INIClass 栈件」） | **CONFIRMED** | §3 + §4 |
| 8 | R-063b §6.4「无冲突项」清单（1/4 比例勘误注、0x7E1B04 定名复现一致、UNKNOWN 口径不变） | **CONFIRMED** | §1；实例身份 UNKNOWN 口径两书一致，本仲裁不改 |
| 9 | 隐含命题「0x7E1B04 与 0x7EA5F4 或为基类/派生类 vtable」 | **REFUTED**（改判：组合关系） | §4 |

**一句话裁定**：0x528C00 的 17 个 stack-object 行传入的全部是 caller 帧内**已构造的 INIClass
栈临时件**（vptr 0x7EA5F4 stamp + 0x525A10 构造，witness 槽 D-归一化逐行唯一命中）；
R-062 的三窗 0x7E1B04（GenericList）字节为真但与 witness 调用**无配对**（物理槽错位恒 0xC，
其槽随后被 List<INISection*> 复用）——R-062 §2 的 GenericList 归属 REFUTED，R-063b 的
INIClass 归属 CONFIRMED。R-062 三方「CONFIRMED」复现的是**字节与 5/12 划分**（三方用同一
「同字面槽」判据），配对命题从未被独立检验过——判据级共因盲区，非三方目击失效。

## 6. 勘误办理建议（交 Leader 追加式办理；本件不代办）

- **E1（R-062 书 §2，红项级）**：删换「有帧内构造证据的 5 行：slot 被 `mov [esp+X], 0x7E1B04`
  打 vptr——…定名 `.?AVGenericList@@`」整段为：
  「有帧内构造证据的 5 行（0x77884F/0x77890C/0x778956/0x779C3D/0x779EBD）：witness 槽经
  esp-D 归一化（R-064 裁定书 §3）由同帧 `mov [esp+X], 0x7EA5F4`（0x7787F7/0x779BEA/0x779E6A）
  打 vptr 定名 INIClass；同帧确有 `mov [esp+X], 0x7E1B04` 三窗（字节为真），但其物理槽与
  witness 槽错位 0xC，与该 5 行调用无配对（0x7E1B04=GenericList 独立类，见 R-064 §1/§4）」。
- **E2（R-062 书 §2 标题与 §5）**：「caller 栈上 GenericList 临时件」「17+1 stack-object 是类型
  命名（GenericList 栈件）」→「caller 栈上 INIClass 栈件（R-064 勘误）」；原 GenericList 表述
  保留删除线或勘误注，不静默改史。
- **E3（门禁注释，非断言）**：`r062_upward_trace_contract.py` 文档串中「0x528c00 rows carry
  the GenericList vptr-store evidence」一句与 R-062 书同病；126 断言本体零改动、维持冻结，
  仅建议随 E1 在 LEDGER 记注释级勘误注（是否触码由 Leader 定）。
- **E4（两份复核的限定注）**：C 报告 §4 标题「GenericList 构造证据 — CONFIRMED」与 OOF 报告
  §2 抽验-7「with in-frame vptr store (mov [esp+slot],0x7E1B04): 5」——其复现对象是字节与
  「同字面槽」判据下的 5/12 划分，非物理槽配对；建议加注「判据局限已由 R-064 仲裁更正」。
- **E5（R-063b 书 §6）**：三条待勘误候选全部转「已裁定（R-064 裁定书 §5 #5/#6/#7 CONFIRMED）」；
  其 §5「2 行未闭合」由本裁定 §3 表 #6 收口为 12/12（新断言，随本件办理）；其 §7「待复核候选」
  状态可升格为「已仲裁确认」。
- **E6（新增登记）**：INIClass 含 GenericList 成员（+0xC）与 List<INISection*> 节点头（+0x10/
  +0x1C）的布局证据（0x5256F8/0x52571E/0x525760）；0x528C00=ret 0x10 复现（佐 R-063b §5
  「入口约定 ret 0x10」）；帧 F 的 0x778A20 函数线外块结构（jne 0x778B61→0x778B9F，出口
  0x778B95..0x778B9E）证明行 13/14/15 与 stamp 0x778B20 同帧。

## 7. 诚实账

- **本轮我方探针缺陷实录**（G-55/G-84 族纪律）：① probe1 首版 PE 头解析把 SizeOfOptionalHeader
  读在 coff+2（实为 coff+16）致段表全错——已修，首跑作废；② probe3 首版 ret-imm 用「入口线性
  窗找首个 ret」，对 0x5295F0/0x526D90/0x7B5B30/0x5256F0 四个真 callee 失败（窗内撞不可解码
  字节/间接 jmp 即断）——改「闭包内全部 ret 求交集」后全解决，且比首版严格（多 ret 不一致即
  判 None）；③ probe4 首跑 capstone detail 模式混用（复用了 probe3 的 detail=False 解码器）崩
  CsError——已修；④ probe3 HYP4 版日志把 imm 打成 0（先置 p=0 后取值，纯显示 bug，D 记账
  未受影响）——已修并复跑；⑤ 我本人对帧 A/B/C 的手算 D 曾与机器 sim 差 8/0xC，最终以机器
  sim 为准（教训：多 push/call 交错下手算不可靠，D 记账必须机器化）。
- **方法域与残余局限**：
  1. 线性对齐解码域 + E8 目标闭包（与门禁/既往轮同域）——非对齐第三形态入口同盲。
  2. ret-imm 解析要求闭包内全部 ret 一致，但「首 ret 即真 epilogue」对多出口不同 imm 的病态
     函数仍理论上可漏（本轮关键 callee 全部单值或恒值，未触发）。
  3. D-sim 未分析 reg 派生 esp 别名（`mov eax,esp` 后经 [eax+X] 的栈写）——W 槽写者普查
     只扫字面 `mov [esp+X]` store；「INIClass stamp 命中 W」的判定不依赖「无其他写者」，
     而依赖 stamp+ctor+lea 同格链，故此局限不动摇归属，但「W 槽最后写者」表述按此降级。
  4. 帧 D 三处虚拟 call（0x5CF038/0x5CF350/0x5CF556）未做 vtable 落实——HYPV 实验已证明
     17 行的 D 记账在剪掉它们后不变，故不构成依赖；如需穷尽可另立小任务。
  5. 行 0x5CF4C7/0x5D76A9 的闭合与「帧内已构造」补强是**本轮新断言**：随本裁定书走办理链，
     未过独立复核前不得写入 R-063b 冻结层。
  6. 未真机、未读 BSS、未宣称可改写点（C26-04）；全镜像 c7-store 计数口径为 [esp±disp] 形
     （0x7E1B04 25 处 / 0x7EA5F4 30 处），与 R-062/R-063b 的 45 处全形态口径不同——不冲突，
     仅口径差，本仲裁不依赖该计数。
- **对既有文件的核实**：R-062 书/R-063b 书/门禁/两份复核/LEDGER/镜像 mtime 全部早于本会话
  （probe1 首跑前后各测一次，逐字相同）；本轮新增仅 4 个 `_r064_probe*.py` 与本裁定书。

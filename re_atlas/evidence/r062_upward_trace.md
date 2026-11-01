# R-062 · 2026-10-27 — 见证 `this` 上行一跳收口（R-061 §6.5 悬项执行轮）

对象：`gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（只读）。
领的活：R-061 诚实账「7 转参宿主 this=UNKNOWN，上行再一跳仍可查」——本轮真把这一跳
查完。写域仅 `re_atlas/`；静态；不运行游戏；不宣称可改写点（C26-04）。
全部常量机器转储先行（G-65）：`out/_probe_r062{a,b,c,d,e,f,g}*.py` /
`_r062f.json` / `_r062g.json` 全保留（含两轮我自己的探针缺陷实录，见 §4）。

## 1. 结论：88 caller 上行一跳分类表（逐行字节钉）

门禁 `tools/r062_upward_trace_contract.py` **126/126 PASS**（sha256
`611ca4d4bd14ea60296cab31f7a6fa248e85f99b54bd97bc3b98af4bbcdd1dff`），独立实现
ecx 链回溯（ret 框定、call 边界感知），对 7 个 SMALL 宿主全部 aligned caller
逐行验 verdict+链字节（CHAIN 88 行冻结字面量，`--dump` 机器生成）：

| verdict | 计数 | 含义（身份仍不命名） |
|:--|--:|:--|
| **param-slot** | **54** | ecx ← `mov reg,[esp+X]`（或直接 `mov ecx,[esp+X]`），**该帧对 X 零写入** ⇒ X 是**入向 cdecl 参数槽**：this 由更上层线传进来 |
| **stack-object** | **17** | ecx ← `lea ecx,[esp+X]` 且紧邻本宿主 call（17/17 邻接实测）⇒ caller 把**自己栈上的临时对象**交给见证方 |
| local-slot | 1 | 同上但帧内有 1 个写入者（`0x770774`，slot 由 `mov [esp+0x1c],eax` 建立） |
| param1-forward | 3 | `0x52A760` 三 caller：ecx ← edi ← `mov edi,[ebp+8]`＝caller 的**第一参数**原样转发（再上一跳 F/G 帧：F=0x689E90 唯一 E8 caller=0x687853；G 帧 edi ← `mov edi,[esp+0x18]` 帧内零写入 ⇒ 又是入向参数） |
| unknown-reg | 12 | 链死在**入向 callee-saved 寄存器**（帧内无写入者）——仍是有界转参，再上一跳未穷尽＝**UNKNOWN 保留** |
| unknown-thunk | 1 | `0x474A5F`（0x528220 唯一 caller，R-061 已知 thunk）：帧内 ecx 无写入者 ⇒ 转自更上层＝**UNKNOWN 保留** |

**两个决定性负命题（非恒真，各配阳性对照）**：
- **caller-self = 0**：88 行里没有一行是「caller 用自己的 this 调见证宿主」。判据
  带防假阴设计：`mov reg,ecx` 只有在「帧起点到该指令之间无 ecx 写入且无 call
  干扰」时才升为 caller-self——否则记 unknown-reg（防「帧中段 reassign 冒充 this」）。
- **global-load = 0（跨 7 SMALL 宿主）**，同判据在五个已钉 GLOBAL 直传宿主上复现
  **164/90/118/3/2 与 R-061 冻结 E-hist 逐值全等**（U-ctl-*）⇒ 「SMALL 宿主零
  global-direct」是**有分类器在场证明的定理**，不是盲区错觉。

## 2. ★ 新机制发现：0x528C00 的三分之一 this 是 caller 栈上 GenericList 临时件

> 【勘误注（2026-10-29，随异族升格办理，台账 LEDGER 升格收口段）】标题「三分之一」应为「约四分之一」：
> 【勘误注二（2026-10-30，Leader 依 R-064 裁定书办理·台账 §471）】**§2「GenericList 临时件」定名被裁定推翻：
> witness 17 行（含 5 行配对）实为 caller 栈上 INIClass 栈件**（esp-D 归一化路径敏感模拟 17/17 逐行唯一命中
> 同帧 `mov [esp+X],0x7EA5F4` stamp，vtable 对象 0x7EA5F0→COL 0x802510→TD 0x8174B0→`.?AVINIClass@@`）；
> 三窗 `mov [esp+X],0x7E1B04` 字节仍真（0x7E1B04=GenericList 独立类，RTTI 链 0x7FAD18→0x817508→
> `.?AVGenericList@@` 复验为真），但其物理槽与 witness 槽**错位恒 0xC**、与该 5 行调用无配对——
> 门禁「同字面 disp」配对判据不成立（判据级共因盲区：三方 CONFIRMED 复现的是字节与 5/12 划分，
> 配对命题此前从未被独立检验，R-064 §3）。**12/12 行均已闭合为 INIClass 栈件**（含 R-063b 自报未闭合
> 2 行，R-064 §3 收口）。两家族关系=组合非继承：INIClass+0xC 内嵌 GenericList 成员（0x5256F0 复位函数
> 体内先 stamp [esi]=0x7EA5F4 后 stamp [esi+0xC]=0x7E1B04）。裁定书=re_atlas/evidence/
> r064_rtti_naming_adjudication.md（§1–§6）。原表述保留，读数以本注为准；「实例归属 UNKNOWN 保持」
> 口径不变（类型定名更正，非实例定名）。

> 实测 17 stack-object / 67 总 caller = 25.4%（正文数字 17/67 无误，仅标题比例词错；出处=
> 异族复核 r061_r062_oof_review_20261029.md 红-1，同族复核 §8 先觉）。原文保留追加式。

17 个 stack-object 行全部指向宿主 `0x528C00`（twin-A 站点 `0x528cb7` 的宿主）：
caller 在**自己的栈帧**里放一个对象、`lea ecx,[slot]` 直接喂给见证方。字节证据：
- **有帧内构造证据的 5 行**：slot 被 `mov [esp+X], 0x7E1B04` 打 vptr——
  `0x7787c0/0x779bb3/0x779e33` 三处 8 字节窗钉死（`c7442438 041b7e00` 形态）；
  RTTI 链（vtable-4→COL→COL+0xC→TD→TD+8 内联名，R-058 版式，控制位 CCINIClass
  TD 0x8174C8 vfp `0x7F9594` 同walk复现）定名 **`.?AVGenericList@@`**——与 R-058
  B6 的 List 头件基类 vtable 同一张表。
- **无帧内构造证据的 12 行**（`0x5cefc9` 家族等）：帧内对目标 slot 零 dword 写——
  临时件**裸传**。构造可能在 callee 内部或帧外完成，静态不可判 ⇒ 如实登记
  「构造点未证」，不编故事。
⇒ 机制推论（不升格为结论）：见证协议存在「caller 自带 GenericList 临时件」的用法，
与六全局/堆工厂件**并存**。这对 R-061 「工厂件→见证连线未证」给出新角度：连线
候选里现在多了一类栈件。实例归属账**不变**（UNKNOWN 保留）——本件只钉「this 从
哪里来」，不命名「是哪个对象」。

## 3. 门禁与变异（R-061 纪律全套复用）

- 基线 126/126 PASS（exit 0）。标签分族：U-set×7（**冻结字面量** HOST_ROWS 集合，
  非活派生——NOP 掉一个 caller 立刻红）、U-hist×7、U-tot×7、U-chain×88、
  U-ctl×5、U-vptrstore×3、U-rtti-name/ctl×2、U-lea-adj×1、U-p1f×5、U-drift×1。
- 变异校准**两轮**（`out/_calib_r062_mut1.py`；round-1 输出全保留）：
  round-1：109/112——2 例 EXC + 1 例 SURVIVED（三处皆我自己的探针/校准 bug，
  §4），且 round-1 暴露 gate 缺陷：`.rdata` 变异喂进只映射 `.text` 的 G.build ⇒
  IndexError（修：按节表分流，.rdata 只进 blob）；U-set 原用活派生 `_host_of`
  ⇒ 变异下自满足（重言式），改冻结字面量 HOST_ROWS 后 P1f-Fcallers 实测红
  U-p1f-Fcallers+collateral（活证据）。
  round-2：**112/112 killed，survived=0，exc=0，uncovered=0（126 标签全覆盖）**。
- 冻结清单 `out/_r062_freeze.json`（112 行 (case,mut,red) 三元组，sha256
  `1e4e0ba0b42c6fa3d1a20d88d6cdbd507814e5bca24d88f1d4360914881ab214`）；机械转录
  （`out/_gen_r062_lits.py`）→ 正式套件 `tools/mutate_r062_gate.py`（sha256
  `1e8d600de6f096ee…`；STALE 三哈希守卫；每例 splice+full 双路精确红集=手抄字面量）。
- **全量双路复跑已收口**（`out/_r062_freeze_run1.txt`，输出 sha256 前缀 `a366c932`）：
  基线 126/126 PASS；112 例 **exact=112 / survived=0 / exc=0 / splice-mismatch=0 /
  full-mismatch=0 / uncovered=0 / phantom=0**，套件自身 **EXIT=0**（跑中 gate 未动：
  STALE 守卫通过即证）。**异族复核未做**——未过前状态=「冻结候选」（R-061 的同族
  复核 PASS 不代替本件）。

## 4. 本轮我自己的错（实录，G-55/G-84 族复发位）

1. **`len(bs)-1` 当字节数**：capstone row 的 `bytes` 是 hex **字符串**，`Ch-`/
   `P1f-slot` 用 `len(bs)-1` 选末字节 ⇒ 打到下一条指令 ⇒ P1f-slot SURVIVED。
   修 `len(bs)//2-1`；round-2 该行红且 collateral 三标签照实测入账。**已入册 G-86**。
2. **`.rdata` VA 喂 `.text`-only 构建器**：Rt-* 两例 EXC IndexError（G-68 单节
   映射老坑的注入侧变体）。修：gate load() 按节表分流（.text→G.build splice，
   .rdata→blob only），round-2 Rt-* 两例红。**已入册 G-87**。
3. **探针 #b 的 enc_head 正则永不匹配**（`^mov (esi|edi…)` 组写错）⇒ 首轮
   「0/88 caller-this」是**空转假阴**——clean 重写（#f/gate）后「0/88」才是有语义
   的负命题。**其非恒真证明**：同一 classify_call 跑五个直传宿主，caller-self
   命中 **4+31+5+11+0=51** 行（0x528A10 高达 31！）——检测器能看见「caller 转发
   自身 this」这条形态，SMALL 宿主上 0/88 因而是真结果。（本轮顺带新事实：直传
   宿主存在 caller-self 形态——登记入 §5.5，待复核确认。）
4. **U-set 重言式初版**：第一版用活派生 `{k for k in CHAIN if _host_of(k)==host}`，
   变异 NOP 掉 caller 后两侧同步消失、永不红——改**冻结字面量 HOST_ROWS** 后
   P1f-Fcallers 实测红 U-p1f-Fcallers+collateral（活证据，非叙述）。

## 5. 诚实账（R-062 侧新增/更新）

- **实例归属仍是 UNKNOWN**：54 param-slot + 12 unknown-reg + 1 thunk + 3
  param1-forward 全部是「从上面线传进来」，命名实例需再上行（可再跳，但每跳只是
  更多转参——静态穷尽点未到达，如实登记）；17+1 stack-object 是**类型命名**
  （GenericList 栈件）不是实例身份。
- 12 行栈件裸传：构造点未证（callee 内或帧外，静态不可判）。
- **新登记（本轮副产物）**：直传宿主自己的 caller 里有 **51 行 caller-self**
  （caller 转发自身 this 给六全局见证方，最富 0x528A10=31 行）——本轮未对这些
  行的「caller 的 this」再上行（超出本件 7-SMALL 范围，登记不穷尽）。
- 不宣称可改写点；未真机；`0xB7882C/30` 现值仍不可读（BSS）。
- 126/126 与 112/112 只是门禁/套件自证口径，异族复核未过不作定谳。

## 6. 对 R-061 悬项账的变动

- §6.5「上行再一跳仍可查」→ **本轮已做**（7 宿主 88 caller 全收口）。
- R-061 §3 诚实账的 UNKNOWN 清单**不减不增措辞**：7 宿主实例身份 UNKNOWN 保持；
  新增「GenericList 栈件连线候选」（§2 推论，未证）。
- 辅任务/审计/版本库账目见 LEDGER R-062 节。

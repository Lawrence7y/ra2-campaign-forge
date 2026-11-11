# LEDGER_SECTION_DRAFT_v2 — 修正后入账草案
> 修正于 2026-11-12（依据 lead/re_chain_v2_xverify_20261112/XVERIFY.md 的 C1–C6；详见 lead/re_chain_v2_fix_20261112/FIX_RECORD.md）

> 来源：`lead/re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md` §2 证据表 16 条【已证】，经 `RE_GRADING.md`（2026-11-12）全表重定级。
> 口径：A 节只收字节级读数；B 节为静态控制流推断（**未做运行期确认**），不入字节级台账；C 节为待证清单。编号一律 `§6xx 待编号`。
> 靶件：`ra2bench/gamemd.exe` sha256=`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（4,825,360 B，实算 PASS）。
> 证据目录缩写：sf=`slot2_fullscan_20261111/_sf_scan_out.txt`，cw=`re_crashwriter_static_20261110/_cw_disasm_out.txt`，ps=`playerctrl_semantics_20261111/_ps_disasm_out.txt`，oo=`re_orphan_owners_20261110/_oo_map_out.txt`，md=`re_map_preset_decode_20261110/_md_parse_out.txt`，ld=`re_loadbench_diff_20261110/_ld_diff_out.txt`。
> 本修正版首部多一行修正标记，下文行号相对 v2 原件整体 +1；FIX_RECORD.md 中「原 Lxx」指修正前行号。

## A · 拟入账【已证】条目（字节级读数）

| 编号 | 读数（均为穷举扫描计数或指令/文本直接读数） | 证据 |
|---|---|---|
| §6xx 待编号 | .text 单次线性 disasm 于 fo 0x6F59D（VA 0x46F59D）截断，得 155,215 条（11.13%）；分块 0x10000 得 1,150,117 条；seg-extend 得 1,392,527 条（65 自然停点），覆盖至 .text 末 0x7E038D | sf:L7-L11 |
| §6xx 待编号 | 全 .text 直接 `call/jmp` 0x54A4F0 = 0、0x54A630 = 0；FF 15/25 绝对间接 = 0；全镜像 dword 位点 0x54A4F0={0x7ECC04}、0x54A630={0x7ECBE4} | sf:L13-L15 |
| §6xx 待编号 | 全镜像 dword==0x54A4F0 恰 1 处（0x7ECC04 = vtable 0x7ECBFC slot2）；dword==0x54A630 恰 1 处（0x7ECBE4 = vtable 0x7ECBDC slot2） | sf:L18-L19 |
| §6xx 待编号 | 对 slot2 单元的 call/jmp [单元]/A1/8B/89/SIB-abs 装载或复制全编码 = 0 | sf:L20 |
| §6xx 待编号 | 0x546069 处字节 `FF 50 08` = `call dword ptr [eax+8]`；0x54605F `mov eax,[0xAA1078]`；0x546064 `mov ecx,0xAA1078` | sf:L66-L68 |
| §6xx 待编号 | `call/jmp [reg+8]` 普查：字节级 1716（call 1715 + jmp 1 + 异形 2 计法见源）、主流 seg-extend 1714；imm32/disp32 引用 0xAA1078 恰 4 处；load r32←[0xAA1078] 恰 1 处（0x54605F）；store→[0xAA1078] = 0；.rdata/.data 无 dword==0xAA1078 | sf:L26-L29, L31-L35 |
| §6xx 待编号 | c7 存储锚点：0x543E8D `mov dword [0xAA1078],0x7ECBDC`；0x543EBE `mov dword [0xAA1078],0x7ECBFC`；0x54A7B6/0x54A806 `mov dword [esi],0x7ECBFC` | sf:L21-L23 |
| §6xx 待编号 | 0x0054A56E 指令 `C7 46 04 00 00 00 00` = `mov dword ptr [esi+4], 0` | cw:L66 |
| §6xx 待编号 | 0x0054A577 指令 `89 7E 04` = `mov dword ptr [esi+4], edi`；与 0x0054A56E 相距 9 字节；两指令间仅 `33C0 xor eax,eax`（无内存读取/调用/分支） | cw:L66-L68 |
| §6xx 待编号 | XMP29U2.MAP（311,822 B，sha256 `0add791d…`）[Houses] 声明 14 house；含 `Country=` 的节恰 14 个，一一对应无多出节；14 节均 `PlayerControl=no` | oo:L6, L28-L46; 地图原文件 grep 14 处 `PlayerControl=no` |
| §6xx 待编号 | XMP29U2.MAP [Units]=3360、[Infantry]=2240，合计 5600；14 owner 各 400（240 车+160 步） | md:L17-L50; oo:L50-L52, L56-L82 |
| §6xx 待编号 | 大版 `ra2bench/[2]0LoadBench_U0400.yrm`（92,332 B，sha `cb5785a1…`）Units=240 Inf=160 Structures=41；Russians/Americans 各 120 车+80 步，Neutral 持 41 建筑 | md:L54-L78; ld:L25-L28 |
| §6xx 待编号 | 小版 `out/loadbench/[2]0LoadBench_U0400.yrm`（25,604 B，sha `6027eb20…`）Units=240 Inf=160 Structures=0；Russians/Americans 各 120 车+80 步；[Houses] 声明 14、仅 2 房持单位 | md:L81-L103; ld:L29-L31 |
| §6xx 待编号 | 三份载体 size/sha/内容结构互异（另列 222,799 B / md5 `11ec8ff6` 变体）：熵 5.652 vs 4.699、首字节 `;` vs `[`、小节集 34 vs 28、Map 几何 52×53 vs 100×100、键行 1575 vs 643 | ld:L88-L103; md:L55, L82; oo:L6 |
| §6xx 待编号 | 字符串 `PlayerControl` 全镜像恰 1 处 @0x824E28；.text 中 LE32==0x824E28 的 xref 2 处（0x500BBF、0x5012ED） | ps:L11, L32-L34 |
| §6xx 待编号 | 0x500BD6 `call 0x5295f0`；0x500BDB `test al,al`；0x500BDD `8883 ed010000` = `mov byte ptr [ebx+0x1ED], al` | ps:L113-L115 |
| §6xx 待编号 | ctor 0x4F54A0 的 call 普查恰 8 处：0x500A30 / 0x500B19 / 0x59A198 / 0x687FC3 / 0x6881A0 / 0x6882FE / 0x688351 / 0x6C3ED1 | ps:L905 |
| §6xx 待编号 | 字符串 `PercentBuilt` 恰 1 处 @0x8189A0；全 .text 原始字节 `1c 57 00 00` 命中恰 3 处（0x401E00/0x674FC0/0x6750B0）且均为 call rel32 位移巧合；引用 0x5700 族且含寄存器型 `[reg+0x1C]` 的函数 = 0；BaseClass vtable 0x7E3880 各方法仅栈偏移访问 | ps:L12, L36-L39, L894-L899 |

## B · 已证（CFG）——静态推断，未做运行期确认（不入字节级台账）

| 编号 | 静态推断 | 证据 |
|---|---|---|
| §6xx 待编号 | 0x54A4F0 内静态 CFG：`test edi,edi`→若 edi==0 走 0x54A52C 弹栈提前返回、不达置零点；`test eax,eax`/`test al,al`→Vector==0 或 IsAllocated==0 时 `je 0x54A575` 直接跳过置零点；仅 Vector!=0 && IsAllocated!=0 经 0x54A566 `call 0x7C8B3D`(free) 后到达 0x0054A56E（调度方点名条目；R8「覆盖必然发生」的前提亦在此） | cw:L34-L66 |
| §6xx 待编号 | 能指向 0x54A4F0/0x54A630 的 `call/jmp [reg+8]` 调用点全镜像唯一 = 0x546069（污点传播唯一消费者）；由此推「进入两函数必须经虚派发」。**C3 更正：原括注「无别名逃逸」已移出本条、降入 C 节第 3 项【未证】**——它不是字节级读数（字节级是 sf:L20 全编码=0、sf:L26-L28 的 dword/装载计数），而是依赖 sf:L28 探针自标「(指针值不逃逸前提)」与 sf:L40「逃逸 = []」有界静态污点窗口的全称否定；与同源于 sf:L20/L28/L40 的 R2 尾注按 RE_GRADING §2 统一口径同级 | sf:L39-L47; sf:L20, L28, L40 |
| §6xx 待编号 | PlayerControl 控制流影响：0x500BE3 `je 0x500C51`（no→跳过难度资金加成）；0x500ABF `je 0x500ad0`（战役循环选 Scen+0x60C/0x610 难度）；0x50A5C0 清两标志并改名 "Computer"；8 处创建窗口检视均未测试 +0x1ED。**完备性前提注明**：「8 处创建点均未读取或依赖」无独立的全 .text +0x1ED 普查计数，属未验前提；仅 8 处 ctor call 普查（A 节）为字节级读数，勿与字节级普查混写 | ps:L116-L147, L589, L1183-L1214, L905; ps json verdict |

## C · 待证清单（本轮新降 + 原有未证维持）

1. §6xx 待编号【未证】0x543E70=「动态初始化器」、0x543EB0=「atexit 析构器」及其时序（常态 slot2→0x54A630、析构后→0x54A4F0）：缺 CRT 初始化表遍历与 atexit 注册时序的运行期确认，0x7C978A=atexit 亦未证；其指令读数已按字节级收入 A 节。
2. §6xx 待编号【未证】「函数指针值无法在运行期逃逸或复制到其它函数指针变量」：静态普查仅证无静态编码引用，运行期机制未证（sf:L20 由「全编码=0」跳到「无法运行期复制」）。
3. **§6xx 待编号【未证】（C3 本修正版新增）「0xAA1078 无别名逃逸」**：CHAIN_SYNTHESIS.md L69 边界列原文「污点分析证明 0xAA1078 是全镜像唯一消费者，无别名逃逸」。该断言不是字节级读数，且探针自标为**前提**（`sf:L28`「(指针值不逃逸前提)」）、`sf:L40`「逃逸 = []」只是 GROW=0x545150..0x546D90 有界静态污点窗口结果。按 RE_GRADING §2 统一口径（依赖未验前提/运行期机制断言→【未证】），与第 2 项同级；**不再留在 B 节 CFG**。缺：运行期别名/逃逸行为确认（零真机铁律下不可得）。**与核验方表述的差异**：L69 未写「运行期」三字、且对象是全局对象指针 0xAA1078（第 2 项对象是 slot2 函数指针值），故并非「同类运行期机制断言」；但分级不能只凭措辞，须按证据强度统一（详见 FIX_RECORD.md C3）。
4. §6xx 待编号【未证】（C4 拆出）`ps:L899-L900`「引擎无任何运行时读取点」：全称否定机制断言，非字节级读数；PercentBuilt 的普查计数仍按字节级收入 A 节，边界以 CHAIN_SYNTHESIS.md L83「仅证明直接偏移读取为 0」为准。
5. 【未证】（维持）0x0084F2BA 崩溃定谳：缺 MiniDump/调用栈，禁定 DEP 取指违规（CHAIN_SYNTHESIS.md:L74/L143 原标恰当）。
6. 【未证】（维持）引擎运行期 HouseClass 实例数决定机制（L76/L146）。
7. 【未验】（维持）PercentBuilt 经 BaseClass*/间接/动态偏移读点的全镜像普查（L84/L149）。
8. 【未决】（维持）台账历史指纹 93c2974b 算法（L152）。

## 备注（不改变定级）

- 符号命名（`HouseClass::Read_INI`/`CCINIClass::Get_Bool`/`this->Vector`/`IsAllocated`/`GrowthStep` 等）为探针标注与结构推断，非二进制字面；A 节各条只对指令字节与计数负责。
- 「14 owner 各 400」的 owner 名单实为 `<human player>`/`Computer` 等 14 个，与 [Houses] 14 名差集 {Americans,Russians}↔{`<human player>`,Computer}；CHAIN_SYNTHESIS.md:L77「11 国」括注有出入，**已从 A 节读数中拆出单列**（推断/措辞，计数不受影响）。
- 大版 yrm 无 [Houses] 节，「其余 11 房为 0」以 14 房框架为前提（外推），**已从 A 节读数中拆出单列**，台账 A 节相应行只保留 240/160/41 与 owner 分布等文件直接读数。
- A 节「三份载体互异」一行**不含**「非同文件、非压缩/编码变换形态」这一结论：它是 `ld:L88-L103` 维度5 的排除法对比结论（`ld:L91` 实文「唯一剩余解释就是两版本就是两张不同的图」），按 C4 拆出单列【推断】，不入字节级台账。另：`0add791d` 在 `_ld_diff_out.txt` 全文 0 命中，但由同列另引的 `oo:L6`（`sha256 : 0add791d11aea84d…60bc`）支撑，故该 sha 并非「无引用可达」，只是不由 `ld:L88-L103` 支撑。
- A 节「PercentBuilt」一行的证据区间含 `ps:L894-L899`，其中 `ps:L899-L900` 的「引擎无任何运行时读取点」为机制断言，已按 C4 拆入 C 节第 4 项【未证】；A 节该行只对普查计数负责。
- **C6 处置**：A 节原 L26 括注「后者性质未核实」已从【已证】条目中移出。本轮已补做静态反汇编（C5）：`0x5012ED` 是 `0x5012EC 68 28 4E 82 00 = push 0x824E28` 的 imm32（字符串 `PlayerControl` 地址），位于函数 0x501210；其前 `0x5012E1 mov al,[ebx+0x1ED]` 读出标志，随后 `push eax`（值）/`push 0x824E28`（键名）/`push ecx`/`0x5012F4 call 0x529560`，与 Read_INI 的 `0x5295F0`（Get_Bool，读）不同；同函数 `0x50138C call 0x42ED60` 即 `.json:percent_built.writer`。**静态归类：INI 写回/序列化一侧的「取字符串键名」xref，不是第二个读取点，也不是对 `[ebx+0x1ED]` 的写指令**；`Write_INI`/`Put_Bool` 之类符号名非二进制字面，只给静态归类、不宣称符号级定谳。脚本与 stdout 见 `lead/re_chain_v2_fix_20261112/_disasm_5012ed.py` / `_disasm_5012ed_out.txt`。
- 上轮 `_ps_disasm` 复现口径裁定：stdout 恒 0 B（实测空串 sha），复现门=文件级对拍 out.txt/out.json，本次重跑已独立 MATCH（65,202 B / 3,297 B 逐字节同 sha）。**C1 更正**：v2 原件 RE_GRADING L73/L91 声称的 `_pssim_rerun_out.txt`「全文落盘」**不成立（该文件不存在）**；本修正版在新写域 `lead/re_chain_v2_fix_20261112/_pssim_rerun_runlog.txt` 补出带起止时间戳、命令、退出码（0）、driver stdout 指纹、产物指纹的运行日志，重跑证据可闭环；原 `_pssim_rerun.py` 与写域内既有产物零改动。
- **C5/RE_GRADING §4.10 边界**：0x5012ED 性质已补做（不再是「未验」）；24 个引用区间的逐数复核为静态只读可完成，本轮**自愿不做**（时限内优先 C1–C6 定点改正与可闭环补做），理由已写入 RE_GRADING §4 第 10 条，**不与「运行期不可得」类未验并列**。

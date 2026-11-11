# RE_GRADING — 【已证】全表重定级报告（v2）
> 修正于 2026-11-12（依据 lead/re_chain_v2_xverify_20261112/XVERIFY.md 的 C1–C6；详见 lead/re_chain_v2_fix_20261112/FIX_RECORD.md）

> 执行方：受限执行方（本会话）。基准时点：2026-11-12 00:2x（Asia/Shanghai）。
> 写域：`lead\re_chain_synth_v2_20261111\`（本任务唯一写域，所有新文件均在此）。
> 处理对象：调度方 `lead/re_dispatch_20261111/STATUS_BOARD.md` §9.3 保留的两点质疑。
> 铁律遵守：零真机、除写域外只读、无 git 操作、哈希一律 hashlib 实算、每数溯源。
> 本修正版相对 v2 原件在首部多一行修正标记，故下文行号整体 +1；FIX_RECORD.md 中「原 Lxx」一律指修正前 v2 原件行号。

---

## 0 · 靶件自核（STEP 0）

- 命令：`Get-FileHash -Algorithm SHA256 D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe`；`(Get-Item ...).Length`
- 实测：sha256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，4,825,360 B
- 期望：`73201cc0…F67476` / 4,825,360 B → **PASS**，继续。

## 1 · 全表普查：总数与数法（验收判据第 1 条）

- **数法**：对 `CHAIN_SYNTHESIS.md` 全文 154 行逐行做 Python 子串 `count('【已证】')` 求和（等价于全文字符级出现次数，不漏 mermaid/清单/表格）。
- **总数：16 处【已证】**，命中行 L66, L67, L68, L69, L70, L71, L72, L73, L75, L77, L78, L79, L80, L81, L82, L83 —— 全部位于 §2 逐环证据表（L66–L84 区间内），证据表之外零散出现 0 处。
- 同一扫描的其他标记计数：【未证】7、【未验】4、【未决】1、【未定谳】1。
- 扫描工具：[_regrade_scan.py](lead/re_chain_synth_v2_20261111/_regrade_scan.py)，全文输出落盘 [_regrade_scan_out.txt](lead/re_chain_synth_v2_20261111/_regrade_scan_out.txt)（7,062 B）。
- 该扫描同时做了**证据引用可达性核验**：共解析出 **24 条引用，OK=24 / BAD=0**。精确表述为：**24 条中 22 条为 `文件:行区间`、2 条为 `文件:键`**；前者核「文件存在 + 行号范围有效」并打印区间首行实文，后者核「文件存在 + JSON 键存在 + 键值」（`_regrade_scan_out.txt` L53/L55 对这两条标 `[OK*] 键引用不核行号`，**只核文件存在，未打印首行实文**）。**不作「逐引用首行内容相符」的判据**：多条首行只是小节标题（如 `[T4 直接调用复核]`、`[T1 覆盖率复现]`、`[候选点(可能指向 0x54A4F0/0x54A630)]`、`全局对象 0xAA1078 (…):`、`◆ 5. 压缩/编码（…）`），读数落在区间后续行。
  - 补记 2 条键引用的**实际键值**（本轮 `json.load` 独立核键，见 `lead/re_chain_v2_fix_20261112/_fix_checks_out.txt`）：
    - `_ps_disasm_out.json:verdict` = `{"playercontrol_creation_link": "NONE — never tested at any HouseClass creation site", "playercontrol_branches": [...], "percentbuilt": "parsed to HouseClass+0x571C, default 0, no runtime reader in .text", "houseclass_count_driver": ..., "best_expl_4_houses": ..., "breakpoint": ...}`（键存在，与 L82 条目读数实质相符）。
    - `_ps_disasm_out.json:percent_built` = `{"string_va": "0x8189a0", "reader": "0x42ebe0", "writer": "0x42ed60", "store": "HouseClass+0x571C (BaseClass+0x1C)", "default": 0, "runtime_consumers": 0}`（键存在，含 `default:0` / `runtime_consumers:0` / `store`，与 L83 条目读数实质相符）。
  - **REF18（L80 → `ld:L88-L103`）补记**：该区间首行为 `◆ 5. 压缩/编码（小版是否大版的 LZO/zlib 压缩形态）`，只支撑 CHAIN_SYNTHESIS.md L80 的**边界说明列**「排除压缩/编码变换假说」，**不支撑读数列**的 `311,822 B / 0add791d / 222,799 B / 93c2974b / 11ec8ff6`。实算：`0add791d` 在 `_ld_diff_out.txt` **全文 0 命中**；`311,822` 见 L96、`222,799` 见 L96/L101、`93c2974b` 见 L97/L102/L103、`11ec8ff6` 见 L9/L11/L96/L101/L103。**部分反驳核验方**：`0add791d` 虽不在 `ld:L88-L103`，但 R13 证据列另引的 `_oo_map_out.txt:L6` 实文为 `sha256 : 0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc`，该 sha 由该文件支撑；故准确说法是「不由 `ld:L88-L103` 支撑」，而非「无引用可达」。行号合法但首行答非所问这一点**成立**。

## 2 · STEP 1 逐条重定级表（16 条，全部普查，非只改点名条）

判级口径：**字节级读数**=直接从 exe 字节/反汇编指令流读出的确定事实（含穷举扫描计数）；**CFG**=从指令序列推出的控制流/数据流逻辑结论（未做运行期确认）；**未证**=依赖未验前提或运行期机制断言。混合条目按「读数部分 / 推断部分」拆分定级，拆出部分单独入 §3 统计与 v2 草案对应节。
**统一口径补充（本修正版）**：凡「逃逸 / 无别名 / 无任何运行时读取点」这类**全称否定**结论，只要仅依赖静态扫描、且探针自身把它标为前提或未做运行期确认，一律不留在【已证】/【已证（CFG）】，与 R2 尾注同降【未证】；其**底层计数/指令字节**仍按字节级读数维持【已证】。表内「推断写成读数」的四条按此拆出，不整条降掉。

| # | 源行 | 环节主题 | 原标记 | 新标记 | 理由（一句） | 证据文件:行 |
|---|------|----------|--------|--------|--------------|-------------|
| R1 | L66 | ① 直接调用普查 | 已证 | 维持【已证】（读数）；尾注拆出【已证（CFG）】 | 三类普查计数=0 与 dword 位点为穷举扫描直接读数；尾注「必须经虚派发进入」是由计数推导的可达性结论 | slot2_fullscan/_sf_scan_out.txt:L13-L15 |
| R2 | L67 | ① 虚表单元与函数指针值 | 已证 | 维持【已证】（读数）；尾注拆出【未证】 | dword 全镜像各恰 1 处、全编码装载/复制=0 为字节普查；尾注「函数指针值无法在运行期逃逸或复制」是把静态无引用升格为运行期机制结论（sf:L20 探针原文即由「全编码=0」跳到「无法运行期复制」） | _sf_scan_out.txt:L18-L20, L27-L28 |
| R3 | L68 | ① 分块覆盖与截断处理 | 已证 | 维持【已证】 | 155,215 / 1,150,117 / 1,392,527 条、截断点 fo 0x6F59D、覆盖终点 0x7E038D 均为探针直接计数 | _sf_scan_out.txt:L7-L11 |
| R4 | L69 | ① 虚派发唯一实效点 | 已证 | 核心结论降【已证（CFG）】；指令个体与普查计数维持【已证】；**边界列「无别名逃逸」拆出降【未证】** | 「能指向两目标的调用点全镜像唯一=0x546069」「污点分析唯一消费者」由 G1a/G2/G4 普查+污点传播推导，属静态数据流推断；0x546069 处 FF 50 08、装载指令与各项普查计数为字节级。**边界列「无别名逃逸」不是字节级读数**（字节级是 sf:L20 全编码=0、sf:L26-L28 的 dword/装载计数），而是由 sf:L28 探针自标「(指针值不逃逸**前提**)」、sf:L40「逃逸 = []」的有界静态污点窗口推出的全称否定，与 R2 尾注同属依赖未验前提的结论，按统一口径同降【未证】（详见 §2.1 与 FIX_RECORD C3） | _sf_scan_out.txt:L39-L47, L26-L29, L31-L35, L66-L68 |
| R5 | L70 | ① 全局对象派发去向 | 已证 | 指令读数维持【已证】；「常态/析构后」时序降【未证】 | 两条 c7 写入为指令级读数；运行期时序依赖 CRT 初始化表遍历与 atexit 注册语义，未经运行期确认 | _sf_scan_out.txt:L21-L24; re_crashwriter_static/_cw_disasm_out.txt:L20-L24 |
| R6 | L71 | ② 置零写入点 | 已证 | 维持【已证】（附命名注记） | cw L66 直接解码出 `C7 46 04 00000000`；「this->Vector」字段命名为结构推断，不影响指令读数 | _cw_disasm_out.txt:L66 |
| R7 | L72 | ② 函数内控制流图 | 已证 | **降为【已证（CFG）】（调度方点名）** | 四条结论均为从指令序列推路径的逻辑结论，未做运行期确认 | _cw_disasm_out.txt:L34-L66 |
| R8 | L73 | ② 写后立即覆盖 | 已证 | 维持【已证】（读数）；执行序前提归 R7 的 CFG | 两指令身份、相距 9 字节、中间仅 `33C0 xor eax,eax` 为线性字节读数；「置零后必被覆盖」以 R7 路径条件为前提 | _cw_disasm_out.txt:L66-L68 |
| R9 | L75 | ③ 地图文件层对应关系 | 已证 | 维持【已证】 | [Houses] 14 声明与 14 个含 `Country=` 节一一对应为地图文本直接读数；本任务另实测地图含 14 行 `PlayerControl=no` | re_orphan_owners/_oo_map_out.txt:L28-L46; scratch/boot_probe/arm_a/XMP29U2.MAP:107-263 |
| R10 | L77 | ④ XMP29U2.MAP 计数 | 已证 | 维持【已证】（计数）；「11 国」括注拆出【推断·单列】 | Units=3360 / Infantry=2240 / 14×400=5600 为直接解析计数；「11 国+Computer+Neutral+Special」括注与探针 owner 表有出入，属措辞/结构推断，不计入字节级读数 | re_map_preset_decode/_md_parse_out.txt:L17-L50; _oo_map_out.txt:L50-L52, L56-L82 |
| R11 | L78 | ④ 大版 yrm 计数 | 已证 | 维持【已证】（**仅计数部分**：240/160/41 与 owner 分布）；**「其余 11 房为 0」拆出单列【推断·外推】** | 240/160/41 与 `{'Americans':120,'Russians':120}` 等为 `_md_parse_out.txt` / `_ld_diff_out.txt:L25-L28` 文件直接读数；「其余 11 房为 0」以 14 房框架为前提，而大版 yrm 无 [Houses] 节（框架为外推），按自定口径不得整行算字节级读数 | _md_parse_out.txt:L54-L78; re_loadbench_diff/_ld_diff_out.txt:L25-L28 |
| R12 | L79 | ④ 小版 yrm 计数 | 已证 | 维持【已证】 | 240/160/0、[Houses] 14 声明、仅 2 房持单位均为文件直接读数 | _md_parse_out.txt:L81-L103; _ld_diff_out.txt:L29-L31 |
| R13 | L80 | ④ 地图文件独立性 | 已证 | 维持【已证】（**仅 size/sha/结构读数**）；**「排除压缩/编码变换假说」拆出单列【推断·排除法】** | 三份文件 size/sha/内容结构（熵 5.652/4.699、首字节 `;`/`[`、小节集 34/28、Map 几何 52×53 vs 100×100）互异为直接读数；「排除压缩/编码变换假说」是 `ld:L88-L103` 维度5 三重证据的**对比/排除法结论**，`ld:L91` 实文「唯一剩余解释就是两版本就是两张不同的图」，不是读数 | _ld_diff_out.txt:L88-L103; _md_parse_out.txt:L55, L82; _oo_map_out.txt:L6 |
| R14 | L81 | ⑤ 字符串与写入点 | 已证 | 维持【已证】（**仅指令/普查读数**）；「Read_INI/Get_Bool」「读取并写入」拆出单列【推断】 | 字符串普查恰 1 处 @0x824E28、0x500BD6 `call 0x5295f0`、0x500BDD `mov byte ptr [ebx+0x1ED], al` 为指令级读数；「Read_INI/Get_Bool」为符号命名推断、「读取并写入」为寄存器数据流关联，均非字节级读数；另存在条目未呈现的第二 xref 0x5012ED（本修正版已静态核实，见 §4.5） | playerctrl_semantics/_ps_disasm_out.txt:L11, L32-L34, L113-L115 |
| R15 | L82 | ⑤ 控制流影响 | 已证 | **降为【已证（CFG）】**；「8 处创建点」普查维持【已证】 | 三条分支语义为控制流语义推断；「8 处创建点均未读取或依赖」是对创建窗口反汇编的检视结论（**无独立的全 .text +0x1ED 普查计数**，属未验完备性前提，见 §4.11）；8 处 = ctor 0x4F54A0 call 普查 | _ps_disasm_out.txt:L116-L147, L589, L1183-L1214, L905; _ps_disasm_out.json verdict |
| R16 | L83 | ⑤ PercentBuilt 读点与直接消费者 | 已证 | 维持【已证】（**仅普查读数**）；**`ps:L899` 机制断言拆出单列【未证】** | disp32 字节 `1c 57 00 00` 全 .text 命中恰 3 处、引用 0x5700 族且含寄存器型 `[reg+0x1C]` 的函数=0、BaseClass vtable 方法仅栈偏移访问——均为普查读数；`_ps_disasm_out.txt:L899-L900` 实文「=> 静态结论：…除 Write_INI 回写 (0x42ED79) 外，**引擎无任何运行时读取点**」是全称否定机制断言，非读数，按统一口径单列【未证】；「间接读点」原文已另标【未验】，维持。CHAIN_SYNTHESIS.md L83 边界列「仅证明直接偏移读取为 0」才是正确表述 | _ps_disasm_out.txt:L12, L36-L39, L894-L899 |

### 2.1 重定级统计（本修正版）

- **整条维持【已证】**：3 条（R3, R9, R12）；R10/R11/R13/R14/R16 为「计数/指令读数部分维持【已证】+ 推断部分拆出」。
- **维持【已证】的读数部分（含拆出子项）**：10 条（R1, R2, R4 部分, R5 部分, R6, R8, R10, R11, R14, R16）——字节级读数合计覆盖 14/16 条。
- **降为【已证（CFG）】**：4 项 —— R7（整条，调度方点名）、R4 核心结论、R15（整条）、R1 尾注。
- **降为【未证】**：**3 项**（原 2 项 + 本修正版新增 1 项）—— R5 时序归属、R2 尾注「运行期无法逃逸」、**R4 边界列「无别名逃逸」**（C3 统一口径）。
- **拆出单列、不并入字节级台账的推断/机制项**：R10「11 国」括注、R11「其余 11 房为 0」（14 房框架外推）、R13「排除压缩/编码变换假说」（排除法）、R14「读取并写入 / Read_INI·Get_Bool」（数据流关联与符号命名）、R16 `ps:L899`「引擎无任何运行时读取点」（单列【未证】）、R4「无别名逃逸」（单列【未证】）。**均为「拆出」而非整条降掉**：计数部分维持【已证】。
- **命名/措辞注记**（不改定级）：R6/R14 符号命名推断；R15 的「无独立全 .text +0x1ED 普查计数」完备性前提。
- 调度方点名条目（0x54A524 test edi,edi → 「edi==0 则提前返回」）= R7，已降；**同类全表普查另降 R4/R15/R1 尾注**，未只改点名一条。

### 2.2 对 §3/§4 复述条的连带更正

- CHAIN_SYNTHESIS.md §3.1 标题「闭环咬合部分（已证因果）」中，1) 复述 R1+R4（唯一性部分为 CFG，且 R4 的「无别名逃逸」已降【未证】）；2) 复述 R7+R8（路径语义为 CFG，「若在 atexit 之后调用……」一句还叠加 R5 时序未证项）；3) 复述 R15。其「已证因果」措辞应理解为「读数咬合」，因果/时序部分按本表降级。
- §4 边界清单 4 项（L143/L146/L149/L152）原文定级恰当，维持不动。

## 3 · STEP 2 三点实测结论（质疑二：_ps_disasm stdout 口径）

**a) 原探针是否写自己的 `_out.txt` 而非 stdout —— 是（源码证实）**
- `lead/playerctrl_semantics_20261111/_ps_disasm.py:113` `print = P` 把全部打印重定向进内部缓冲 `txt_lines`（:34, :37-38）；
- 输出路径写死为自己目录：:19 `HERE=dirname(abspath(__file__))`、:22-23 `OUT_TXT/OUT_JSON = os.path.join(HERE, '_ps_disasm_out.txt'/'.json')`；
- 结果只经 :456-457（写 txt）与 :471-472（写 json）落盘；**stdout 全程无人写**，唯一控制台输出是 :474 `sys.stderr.write('(done)\n')`。

**b) 上轮「复现」对该探针的实际口径 —— 文件级对拍，非 stdout 对拍**
- 故 `_repro_ps_disasm.txt` = 0 B（其 sha `e3b0c442…` 即空串 sha256，与 CHAIN_SYNTHESIS.md:L50 记录一致）；上轮 MATCH 判定依据是 `_ps_disasm_out.txt`(65,202 B)/`.json`(3,297 B) 的内容对拍。CHAIN_SYNTHESIS.md 表头列名「重跑 stdout 交付件」对该行有误导性，实质是 0 B 的形式性 stdout + 文件级对拍。

**c) 写域内重跑实测（显式捕获 stdout）—— stdout 复现门不可建立，理由=脚本自写文件**
- 方法：`_pssim_rerun.py` 将探针**逐字节复制**进写域（副本 sha256 `9a160867…2d6c37e`，20,572 B，与原件一致 → 未改动原脚本），以 `python -I -X utf8 <写域副本>` 重跑，stdout/stderr 分别重定向到写域文件（文件句柄，非管道）；副本因 HERE=写域，其 `_out.txt/.json` 也落写域，**原探针目录零写入**。
- 实测（**更正 v2 原件 L73 的错误声称**：`_pssim_rerun_out.txt` 实际不存在，v2 原件称「全文落盘」为 FALSE）：探针 **stdout = 0 B**（`_pssim_rerun_stdout.txt`，sha256 `e3b0c442…`=空串）、stderr = 8 B `(done)`（`_pssim_rerun_stderr.txt`）、退出码 0；**未产生综合日志文件**，故不存在「全文落盘」件。重跑产物见写域内 `_ps_disasm_out.txt` = 65,202 B / sha `3fa97f526f53fb26…` 与既有件**逐字节 MATCH**；`_ps_disasm_out.json` = 3,297 B / sha `445bc0609f2c70e0…` **MATCH**。
- **C1 深层问题已补闭环**：`copyfile` 亦可得同 sha，故同 sha 不能独立证明「重跑」发生。本修正版在新写域 `lead/re_chain_v2_fix_20261112/` 用 `_pssim_rerun_logged.py` 实际重跑一次 `_pssim_rerun.py`（`python -I -X utf8 <绝对路径>`，exit 0），产出带**起止时间戳、命令、退出码、driver stdout 指纹、产物指纹**的 `_pssim_rerun_runlog.txt` 与 `_pssim_rerun_driver_stdout.txt`（[1]–[5] 判定日志）。原 `_pssim_rerun.py` 及其既有产物**零改动**（driver sha256 前后同为 `37d2f977…7086`），重跑前后 5 个产物逐字节不变。
- 结论：**stdout 级复现门不可建立**——脚本行为就是把 `print` 重定向为内部缓冲并写自己目录的 out 文件，stdout 恒为空；不改原脚本、不绕只读边界的前提下无法令其产出 stdout。复现门对该探针的**正确定义是文件级对拍 out.txt/out.json**（本次已独立复现 MATCH）。

## 4 · 边界与未验（必含节）

1. 本任务全部结论为**磁盘文件的静态读数**：未启动 gamemd.exe/ra2loader/YURI.exe，未 attach、未读活进程内存、未写任何 hook/采样/MiniDump 代码。
2. 所有【已证（CFG）】（R7、R4 核心结论、R15、R1 尾注）**均为静态控制流/数据流推断，未做运行期确认**；零真机铁律下运行期确认不可得。「未做运行期确认」≠「已被运行期证伪」。
3. **新增【未证】3 项**及所缺证据：R5 时序（缺：CRT 初始化表遍历顺序、atexit 注册时序、0x7C978A=atexit 的确认）；R2 尾注（缺：运行期指针逃逸/别名行为的确认——静态普查只能证明无静态编码引用）；**R4 边界列「无别名逃逸」**（缺：运行期别名/逃逸行为的确认；探针 `sf:L28` 自标「(指针值不逃逸前提)」、`sf:L40`「逃逸 = []」仅为有界静态污点窗口结果，按 §2 统一口径与 R2 尾注同降）。
4. 符号命名（`HouseClass::Read_INI`、`CCINIClass::Get_Bool`、`this->Vector/VectorMax/IsAllocated/GrowthStep`、`deleting dtor`）是探针标注与结构推断，**不是二进制内字面**；字节级条目只对指令字节与计数负责。
5. **R14 的第二 xref 0x5012ED：本修正版已补做静态反汇编核实（原 v2 §4.5「未核实」已撤）**。证据：写域 `_ps_disasm_out.txt:L34` 印 `0x5012ED real ref`、`.json:L55` 列 `"0x5012ed"`；本轮纯静态 capstone 反汇编（脚本/stdout 见 `lead/re_chain_v2_fix_20261112/_disasm_5012ed.py` / `_disasm_5012ed_out.txt`）显示 VA 0x5012ED 是 `0x5012EC 68 28 4E 82 00 = push 0x824E28` 的 imm32（字符串 `PlayerControl` 地址，LE32 实算 = 0x00824E28），位于函数 0x501210 内；其前 `0x5012E1 mov al, byte ptr [ebx+0x1ED]` 读出标志，随后 `0x5012EB push eax`（值）、`0x5012EC push 0x824E28`（键名）、`0x5012F1 push ecx`、`0x5012F4 call 0x529560`。**判定**：该 xref 是「把字符串常量地址压栈传参」的编码，**不是**对 `[ebx+0x1ED]` 或 INI 缓冲区的写指令；所在函数为序列化/写回路径（同窗口还有 `0x50138C call 0x42ED60`，即 `.json:percent_built.writer`），其调用目标 `0x529560` 与 Read_INI 中读取用的 `0x5295F0`（`ps:L113-L115` 标注 Get_Bool）不同。**因此原执行方猜测的「是否 Write_INI 回写」在静态层面得到支持：属 INI 写回/序列化一侧，不是第二个读取点**；但 `Write_INI` / `Put_Bool` 这类**符号名不是二进制字面**，本轮只给静态归类，不宣称符号级定谳（见本 §第 4 条）。
6. R10 括注（「11 国」）与探针 owner 表存在措辞出入；计数读数不受影响。R11 的「其余 11 房为 0」依赖 14 房框架（大版 yrm 无 [Houses] 节），框架属外推，**已从【已证】读数中拆出单列（§2.1）**；R13「排除压缩/编码变换假说」、R14「读取并写入」、R16 `ps:L899` 机制断言同样拆出，见 §2 表与 §2.1。
7. 键名澄清：oo_map_out.txt:L32 表头 `PlayerCtrl` 系探针显示缩写；地图原文件实际键为 `PlayerControl`（本任务 grep `scratch/boot_probe/arm_a/XMP29U2.MAP` 命中 14 行 `PlayerControl=no`），与引擎字符串拼写一致，不构成差异。
8. 台账历史指纹 `93c2974b` 算法仍未决（维持原状，CHAIN_SYNTHESIS.md:L152）。
9. 上轮越界覆盖事故的 7 处既有件，以调度侧 baseline_backup 对拍 9/9 MATCH 为准；本任务未重跑任何原位探针、未写任何只读路径（收尾指纹复核见 §6）。
10. **§4.10 已改写（原「未逐行复核全部引用区间的每个数」不再列为遗留未验）**：24 个引用区间全是磁盘纯文本，逐数复核**静态只读可完成**（核验方 `_x.py` SEC E 已实读落盘）。本轮**自愿不做**全部区间的逐数重算，理由=25 分钟时限内优先完成 C1–C6 的定点改正与本轮可闭环补做（C1 运行日志、C5 静态反汇编）；已核对的是「文件存在 + 行号范围 + 首行/键值 + 点名区间」（关键行人工核对清单：cw L34/L36/L43/L45/L59-L68、sf L7-L29/L39-L47/L66-L68、ps L11/L32-34/L113-147/L589/L894-905/L1183-1214、oo_map L28-82、md L17-103、ld L25-103、sp_report L37）。**不与「运行期不可得」类未验并列**。
11. R15 的「8 处创建点均未读取或依赖 +0x1ED」**无独立的全 .text +0x1ED 普查计数**，属未验完备性前提；8 处 ctor call 普查本身是字节级读数，二者在 v2 草案 B 节已分开注明。
12. 本轮**未验/未做**（如实列出）：未对 24 个引用区间的每一个数字逐一重算（见第 10 条，静态可查、本轮自愿不做）；未做运行期确认（零真机铁律下不可得）；`0x7C978A` 是否 CRT `atexit` 未证；台账历史指纹 `93c2974b` 算法未决；`0x529560` 的确切符号名不可证（第 5 条）。

## 5 · 收尾回执

- **改动/新建文件（全部在写域 `lead\re_chain_synth_v2_20261111\` 与新建写域 `lead\re_chain_v2_fix_20261112\`）**：
  - v2 原件写域：`RE_GRADING.md`、`LEDGER_SECTION_DRAFT_v2.md`（本修正版就地修正）、`_regrade_scan.py`、`_regrade_scan_out.txt`、`_pssim_rerun.py`、`_pssim_rerun_stdout.txt`、`_pssim_rerun_stderr.txt`、`_ps_disasm_rerun_copy.py`、`_ps_disasm_out.txt`、`_ps_disasm_out.json`、`_integrity_check.py`、`_baseline_snapshot.json`。**`_pssim_rerun_out.txt` 从未存在，已从本清单删除**（更正 v2 原件 L91 的错误声称）。
  - 新建写域：`FIX_RECORD.md`（逐条 C1–C6）、`_fix_checks.py` / `_fix_checks_out.txt` / `_fix_checks_pwsh_out.txt` / `_fix_baseline.json`（复核与收尾指纹）、`_pssim_rerun_logged.py` / `_pssim_rerun_runlog.txt` / `_pssim_rerun_driver_stdout.txt` / `_pssim_rerun_logged_stdout.txt`（C1 重跑日志）、`_disasm_5012ed.py` / `_disasm_5012ed_out.txt`（C5 静态反汇编）。
- **实跑命令**（python 一律 `python -I -X utf8 <绝对路径>`；指纹一律 hashlib 实算）：
  1. `Get-FileHash -Algorithm SHA256 …\ra2bench\gamemd.exe` + `.Length`（STEP 0，PASS）
  2. `python -I -X utf8 …\_integrity_check.py snapshot`（基线 100 文件指纹）
  3. `python -I -X utf8 …\_regrade_scan.py`（×2，含正则修正后终版）`*> _regrade_scan_out.txt`
  4. `python -I -X utf8 …\_pssim_rerun.py`（v2 原件后台完成，exit 0）
  5. `grep PlayerControl|PlayerCtrl …\XMP29U2.MAP`（14 命中）
  6. `python -I -X utf8 …\_integrity_check.py verify`（收尾零改动复核）
  7. **本修正版新增**：`python -I -X utf8 …\lead\re_chain_v2_fix_20261112\_fix_checks.py`（基线 + C1–C6 复核）、`…\_pssim_rerun_logged.py`（重跑 + 运行日志）、`…\_disasm_5012ed.py`（静态反汇编）、收尾 `…\_fix_checks.py verify`。
- **结论一句话**：CHAIN_SYNTHESIS.md 的 16 处【已证】经全表普查后，4 条整条/核心结论降为【已证（CFG）】（含点名条目）、**3 项**运行期/前提依赖断言降为【未证】（含 C3 补降的「无别名逃逸」）、4 条按「计数维持【已证】、推断拆出单列」处理、其余维持字节级【已证】；`_ps_disasm` 的 stdout 复现门实测不可建立（脚本自写文件、stdout 恒 0 B），该探针复现口径应为文件级对拍且本次已独立 MATCH。
- **遗留未验项**：见 §4 全部 12 条；其中第 3 条的 3 项新降【未证】待后续（若允许动态确认则按 §11 断点计划类方案，本轮不做）；第 10 条为本轮**自愿不做**（静态可查），非「不可得」。
- **关键件收尾指纹（hashlib 实算，`_integrity_check.py verify`：watched=100 / drift=0 / missing=0 / new=0，退出码 0）**：
  - `ra2bench\gamemd.exe` = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（4,825,360 B）
  - `lead\re_chain_synthesis_20261111\CHAIN_SYNTHESIS.md` = `c88717d71c4b59d88ecd04f234843f561a829e63f5b967659e10acfdcf8254b3`（20,971 B）
  - `lead\re_chain_synthesis_20261111\LEDGER_SECTION_DRAFT.md` = `b40ac2a7b6fade6854fc0960aa9b01252ccff3dc292c780b979a8e56b664a800`（3,415 B）
  - `lead\re_chain_synthesis_20261111\_repro_ps_disasm.txt` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（0 B，空串 sha）
  - `lead\playerctrl_semantics_20261111\_ps_disasm.py` = `9a16086763924c269c2166fbcfd22c636ffb1800d6f78d54c72437c0c2d6c37e`（20,572 B，与写域副本一致 → 原脚本未改动）
  - 上列全部关键件与基线快照（100 文件）逐一比对 **0 漂移**，既有件零改动实证成立；本修正版另以 `_fix_checks.py verify` 对 170 个既有件（含 XVERIFY.md、全部证据件、写域内原有脚本/产物）做收尾比对，见 FIX_RECORD.md「收尾指纹」节。

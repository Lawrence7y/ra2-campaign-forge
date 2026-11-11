# FIX_RECORD.md — C1–C6 逐条修正记录

> 修正于 2026-11-12。依据：`lead/re_chain_v2_xverify_20261112/XVERIFY.md`（24,363 B，独立核验方 PASS_WITH_CORRECTIONS）。
> 被修正对象（就地）：`lead/re_chain_synth_v2_20261111/RE_GRADING.md`、`LEDGER_SECTION_DRAFT_v2.md`（两份顶部均已加修正标记）。
> 本目录：`lead/re_chain_v2_fix_20261112/`（新建，唯一另一写域）。其余路径一律只读，零字节改动；无 git commit/push/reset/checkout。
> **零真机**：未启动 gamemd.exe / ra2loader / YURI.exe，未 attach、未读活进程内存、未写任何 hook / 采样 / MiniDump 代码；`gamemd.exe` 只被 `open(...,'rb')` 静态读字节做 capstone 反汇编。
> python 一律 `python -I -X utf8 <绝对路径>`；指纹一律 `hashlib.sha256` 实算（见 `_fix_checks_out.txt` / `_pssim_rerun_runlog.txt`）。
> 复核工具：`_fix_checks.py`（输出 `_fix_checks_out.txt`、`_fix_checks_pwsh_out.txt`，基线 `_fix_baseline.json`）；C1 重跑：`_pssim_rerun_logged.py`；C5 反汇编：`_disasm_5012ed.py`（stdout `_disasm_5012ed_out.txt`）。
> 行号约定：下文「原 Lxx」= 修正前 v2 原件行号；修正后两份文件首部各多一行标记，行号整体 +1。

---

## C1 · 虚假声称：`_pssim_rerun_out.txt` 不存在

**复核结论：成立（采纳）**
- `Test-Path lead\re_chain_synth_v2_20261111\_pssim_rerun_out.txt` = **False**；`_fix_checks_out.txt` L6 `os.path.isfile = False`。写域实有 12 个文件，无此件。
- 原 L73 实含「实测（[_pssim_rerun_out.txt](…) **全文落盘**）：退出码 0；stdout = 0 B…」、原 L91 新建文件清单实列该文件（`_fix_checks_out.txt` L11–L12 = True）。
- 探针 stdout 确为 0 B：`_pssim_rerun_stdout.txt` = `e3b0c442…b7852b855`（0 B，空串 sha）；stderr = 8 B；`_ps_disasm_out.txt` 65,202 B / `3fa97f52…`、`_ps_disasm_out.json` 3,297 B / `445bc060…`，与 XVERIFY X4 (c) 全部吻合。
- **处置选 (b)**，理由：探针 stdout 恒 0 B（`_ps_disasm.py:113 print = P`，stdout 全程无人写，唯一控制台输出为 :474 stderr `(done)`），不存在可供「全文落盘」的综合日志；即便按 (a) 重跑并捕获 driver stdout，也无法使「v2 原件声称的该文件已落盘」变成真话——那是关于**过去事实**的虚假声称，只能撤回措辞并如实改写。核验方 X4 L141 亦确认「该 rerun 脚本自身的 stdout（[1]–[5]）无落盘件」。

**实际改动（RE_GRADING.md）**
- 原 L73：「- 实测（[_pssim_rerun_out.txt](lead/re_chain_synth_v2_20261111/_pssim_rerun_out.txt) 全文落盘）：退出码 0；**stdout = 0 B**（sha256 `e3b0c442…`=空串）；stderr = 8 B `(done)`；重跑 `_ps_disasm_out.txt` = 65,202 B / sha `3fa97f526f53fb26…` 与既有件**逐字节 MATCH**；`_ps_disasm_out.json` = 3,297 B / sha `445bc0609f2c70e0…` **MATCH**。」
- 改后：「- 实测（**更正 v2 原件 L73 的错误声称**：`_pssim_rerun_out.txt` 实际不存在，v2 原件称「全文落盘」为 FALSE）：探针 **stdout = 0 B**（`_pssim_rerun_stdout.txt`…）、stderr = 8 B `(done)`…、退出码 0；**未产生综合日志文件**，故不存在「全文落盘」件。重跑产物见写域内 `_ps_disasm_out.txt` … MATCH；`_ps_disasm_out.json` … MATCH。」
- 原 L91 清单含 `` `_pssim_rerun_out.txt` `` → 改后删除该条，并加一句「**`_pssim_rerun_out.txt` 从未存在，已从本清单删除**（更正 v2 原件 L91 的错误声称）」。
- §5 实跑命令新增第 7 条（本轮 4 个 `python -I -X utf8 <绝对路径>` 命令）；结论一句话与 §4 第 12 条同步。

**深层问题（同 sha 不能证明「重跑发生」）——已补闭环**
- 采纳核验方意见：`copyfile` 亦可得同 sha。为同时满足「既有件零改动」，**未就地修改 `_pssim_rerun.py`**（验收判据要求既有件零改动），改在新建写域内新增 `_pssim_rerun_logged.py`，以 `subprocess.call([sys.executable,'-I','-X','utf8',DRIVER], stdout=文件句柄)` **真实重跑一次原脚本**，产出：
  - `_pssim_rerun_runlog.txt`：`run_id=C1-20261112-rerun-01`、`start_local=2026-11-12T01:34:23+08:00` / `end_local=01:34:33+08:00`（UTC 同步）、精确 command、`driver_exit_code=0`、`driver_sha256_before/after` 同为 `37d2f977…7086`(4151 B)、driver stdout sha/字节数、probe stdout/stderr、两个重跑产物 sha、文件级 MATCH=True、`products_unchanged=True`、零真机声明。
  - `_pssim_rerun_driver_stdout.txt`（1,515 B / `f87288b7…`）= driver 的 `[1]`–`[5]` 判定日志，与运行日志互证。
- 说明：日志本身仍可被伪造，**不能从密码学上证明实跑**；但在「带时间戳 + 退出码 + 命令 + 产物指纹」的约定下，核验方指出的「这一环无法闭环」已按任务要求补齐。边界见文末。

---

## C2 · X2 措辞绝对化

**复核结论：三点中两点完全成立；第三点部分成立、部分反驳**

1. **成立**：`_regrade_scan_out.txt` 逐条解析得 **24 条引用 = 22 条 `文件:行` [OK] + 2 条 `文件:键` [OK*]**（`_fix_checks_out.txt` L15–L17）。L53/L55 原文：
   - `L82 …_ps_disasm_out.json:verdict -> 文件存在(147 行), 键引用不核行号 [OK*]`
   - `L83 …_ps_disasm_out.json:percent_built -> 文件存在(147 行), 键引用不核行号 [OK*]`
   即只核文件存在、未打印首行实文，与 RE_GRADING 原 L22「含对每个引用打印其首行实文」直接矛盾。
2. **成立**：多条 `[OK]` 首行只是小节标题（`_fix_checks_out.txt` L27–L36）：`[T4 直接调用复核]`、`[T1 覆盖率复现]`、`[候选点(可能指向 0x54A4F0/0x54A630)]`、`全局对象 0xAA1078 (…):`、`◆ 5. 压缩/编码（…）`；读数在区间后续行，「首行内容相符」判据过强。
3. **部分成立 / 部分反驳**：
   - 成立：`ld:L88` 首行确为「◆ 5. 压缩/编码（小版是否大版的 LZO/zlib 压缩形态）」（`_fix_checks_out.txt` L20、`ld_diff_out.txt:L88`），只支撑 CHAIN_SYNTHESIS.md L80 边界列「排除压缩/编码变换假说」，不支撑读数列；`0add791d` 在 `_ld_diff_out.txt` **全文 0 命中**（`_fix_checks_out.txt` L21），`311,822` 见 L96、`222,799` 见 L96/L101、`93c2974b` 见 L97/L102/L103、`11ec8ff6` 见 L9/L11/L96/L101/L103。
   - **反驳（证据）**：核验方 X2 第 3 点由此推出「该 sha 在被引区间内无引用可达」，过度推广。`_oo_map_out.txt:L6` 实文 `sha256 : 0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc`，而 `_oo_map_out.txt:L6` **正是 RE_GRADING 原 L42（R13）证据列明引的文件**。故准确说法是「不由 `ld:L88-L103` 支撑」，而非「无引用可达」。此点在两份修正件中均已如实写明。

**实际改动（RE_GRADING.md 原 L22）**
- 原：「- 该扫描同时做了**证据引用可达性核验**：16 条引用的全部 文件:行 范围 **OK=24 / BAD=0**（含对每个引用打印其首行实文，证明行号真实、内容与条目相符）。」
- 改后：「…共解析出 **24 条引用，OK=24 / BAD=0**。精确表述为：**24 条中 22 条为 `文件:行区间`、2 条为 `文件:键`**；前者核「文件存在 + 行号范围有效」并打印区间首行实文，后者核「文件存在 + JSON 键存在 + 键值」…**不作「逐引用首行内容相符」的判据**…；补记 2 条键引用的**实际键值**（`verdict` 全键值、`percent_built` = `{"string_va":"0x8189a0","reader":"0x42ebe0","writer":"0x42ed60","store":"HouseClass+0x571C (BaseClass+0x1C)","default":0,"runtime_consumers":0}`）；补记 REF18 首行只支撑边界列、`0add791d` 在 ld 全文 0 命中但由 `oo:L6` 支撑。」

---

## C3 · R4「无别名逃逸」定级自相矛盾（最重要）

**复核结论：采纳「必须统一定级、降【未证】」的处置；对核验方「二者是同类运行期机制断言」的分类表述作部分反驳**

自读证据：
- `_sf_scan_out.txt:L20`：「G1b: …(FF15/FF25/A1/8B/89/SIB-abs **全编码 = 0**) → **函数指针值无法运行期复制到其它单元**」——前半是字节级穷举计数，后半是运行期机制结论。
- `_sf_scan_out.txt:L28`：「G5: .rdata/.data **无 dword==0xAA1078** → 不存在指向该全局对象的指针变量(**指针值不逃逸前提**)」——探针**自己把「不逃逸」标为前提**。
- `_sf_scan_out.txt:L29`：「G4b: … → **无别名合成路径读取 vptr 单元**」；`L40`：「GROW = 0x545150..0x546D90; 唯一 vptr 装载 0x54605F; 消费者 = [('0x546069', …)]; **逃逸 = []**」——有界静态污点窗口的空表。
- `CHAIN_SYNTHESIS.md:L67` 边界列（R2 尾注）「函数指针值**无法在运行期**逃逸或复制到其他函数指针变量」；`:L69` 边界列「污点分析证明 `0xAA1078` 是全镜像唯一消费者，**无别名逃逸**」。

**判定**：
1. 「无别名逃逸」**不是字节级读数**。字节级是 sf:L20 的「全编码=0」、sf:L26–L28 的 dword/装载计数；「无别名逃逸」是由这些计数 + 有界静态污点窗口推出的**全称否定结论**，且探针自标为「前提」（sf:L28）。核验方二分法（字节级读数 / 运行期机制断言）漏掉了中间层（静态数据流推断），此处予以补正。
2. **与 R2 尾注的真实区别**（反驳「同类」表述，证据如上）：(i) **对象不同**——R2 尾注说的是 slot2 单元里的**函数指针值** 0x54A4F0/0x54A630，L69 说的是**全局对象指针** 0xAA1078 及其 vptr 单元；(ii) **措辞不同**——L67 明写「运行期」，L69 无「运行期」三字，写的是「污点分析证明」（静态）；(iii) **来源行不完全同源**——R2 主要据 sf:L20，R4 主要据 sf:L28/L29/L40（虽共享 L28）。故「二者是同类运行期机制断言、同源于 L20/L28/L40」不够精确。
3. **但核验方结论（定级必须统一）成立**：按执行方自定 §2 口径「**未证 = 依赖未验前提或运行期机制断言**」，「无别名逃逸」依赖探针自标的未验前提（sf:L28「前提」）且未做运行期确认，与 R2 尾注证据强度相同。若仅因 L69 没写「运行期」三字就留在【已证（CFG）】，则是**按措辞而非按证据强度划线**，属自相矛盾。故**统一口径**：凡「逃逸 / 无别名 / 无任何运行时读取点」类全称否定，只要仅依赖静态扫描且未做运行期确认，一律【未证】；其底层计数/指令仍按字节级【已证】。

**实际改动**
- `LEDGER_SECTION_DRAFT_v2.md` 原 L36（B 节第 2 条）：
  - 原：「| §6xx 待编号 | 能指向 0x54A4F0/0x54A630 的 `call/jmp [reg+8]` 调用点全镜像唯一 = 0x546069（污点传播唯一消费者、**无别名逃逸**）；由此推「进入两函数必须经虚派发」 | sf:L39-L47 |」
  - 改后：删去「无别名逃逸」，改为「（污点传播唯一消费者）；由此推『进入两函数必须经虚派发』。**C3 更正：原括注「无别名逃逸」已移出本条、降入 C 节第 3 项【未证】**——它不是字节级读数…与同源于 sf:L20/L28/L40 的 R2 尾注按 RE_GRADING §2 统一口径同级 | sf:L39-L47; sf:L20, L28, L40 |」
- C 节**新增第 3 项【未证】**「0xAA1078 无别名逃逸」，列明证据 sf:L28/L40、所缺运行期确认、以及与核验方表述的差异（对象/措辞/证据强度）。
- `RE_GRADING.md` R4 行新标记改为「核心结论降【已证（CFG）】；指令个体与普查计数维持【已证】；**边界列「无别名逃逸」拆出降【未证】**」并重写理由；§2.1「降为【未证】：2 项」→「**3 项**」并列出；§2 前新增「统一口径补充」；§4 第 3 条「新增【未证】2 项」→「3 项」并补 R4 项；§5 结论一句话「2 项」→「3 项」；§2.2 连带更正补注。

---

## C4 · §2 理由列的「推断写成读数」

**复核结论：成立（采纳），按「拆出」而非「整条降掉」处理**
- R11：`_ld_diff_out.txt:L25-L28` 只有 `big Units=240 Infantry=160 Structures=41 / Units {Americans:120,Russians:120} / Infantry {…} / Structures {Neutral:41}`，**没有 14 房框架**；RE_GRADING 原 L40 自认「大版 yrm 无 [Houses] 节（框架为外推）」。
- R13：`ld:L91` 实文「…**唯一剩余解释就是两版本就是两张不同的图**」（`_fix_checks_out.txt` L47）——排除法对比结论，非读数。
- R14：原 L43 自认「『Read_INI/Get_Bool』为符号命名推断、『**读取并写入**』为寄存器数据流关联」。
- R16：`ps:L899` 实文「=> 静态结论：PercentBuilt 写入 HouseClass+0x571C 后，除 Write_INI 回写」+ L900「(0x42ED79) 外，**引擎无任何运行时读取点**」（`_fix_checks_out.txt` L48–L49）——全称否定机制断言；CHAIN_SYNTHESIS.md L83 边界列「仅证明直接偏移读取为 0」才对。
- 采纳核验方 X6 表格的判定；同时采纳任务提示的「拆出」口径：**计数/指令部分维持【已证】，推断部分单列**，不整条降掉。

**实际改动（RE_GRADING.md §2 表 + §2.1 + §4 + §5）**
- R11 原「维持【已证】（计数；框架注记）」→「维持【已证】（**仅计数部分**：240/160/41 与 owner 分布）；**「其余 11 房为 0」拆出单列【推断·外推】**」；理由补「按自定口径不得整行算字节级读数」。
- R13 原「维持【已证】」→「维持【已证】（**仅 size/sha/结构读数**）；**「排除压缩/编码变换假说」拆出单列【推断·排除法】**」；理由补 `ld:L91` 实文。
- R14 原「维持【已证】（读数；命名注记）」→「维持【已证】（**仅指令/普查读数**）；「Read_INI/Get_Bool」「读取并写入」拆出单列【推断】」。
- R16 原「维持【已证】」→「维持【已证】（**仅普查读数**）；**`ps:L899` 机制断言拆出单列【未证】**」；理由补 L899–L900 实文与 L83 正确边界。
- R10 亦同口径补「「11 国」括注拆出【推断·单列】」（核验方 X6 L184 指出其带错注留在读数列）。
- §2.1 改为「整条维持【已证】3 条（R3/R9/R12）」+ 新增「拆出单列、不并入字节级台账的推断/机制项」清单；§4 第 6 条补记这四条已拆出；§5 结论一句话补「4 条按『计数维持【已证】、推断拆出单列』处理」。
- `LEDGER_SECTION_DRAFT_v2.md` 同步：A 节「三份载体互异」行删去结论「→ 非同文件、非压缩/编码变换形态」；C 节新增第 4 项【未证】（`ps:L899`）；备注补 R10/R11/R13/A 节 PercentBuilt 的拆出说明；B 节第 3 条按核验方次级异议补「无独立全 .text +0x1ED 普查计数」完备性前提。

---

## C5 · §4.5 与 §4.10 被指为「回避」

**复核结论：成立（采纳），两项均已补做/改写**

**§4.5 `0x5012ED` 性质：已补做静态反汇编**
- 既有证据：`_ps_disasm_out.txt:L34` = `0x5012ED  real ref`；`_ps_disasm_out.json:L55` = `"0x5012ed"`（`_fix_checks_out.txt` L56–L57）。
- 本轮脚本 `_disasm_5012ed.py`（只读 `ra2bench/gamemd.exe` 字节、capstone x86-32，沿用 `_ps_disasm.py:5` 的 VA=foff+0x400000 约定）→ stdout `_disasm_5012ed_out.txt`：
  - `[1]` VA 0x5012ED (foff 0x1012ED) LE32 = **0x00824E28** = 字符串 `PlayerControl` VA（MATCH）。
  - `[3]` 归属指令 `0x5012EC  68 28 4E 82 00  push 0x824e28`，0x5012ED 落在该指令 +1（imm32 起始）；上下文 `0x5012E1 mov al, byte ptr [ebx+0x1ed]` → `0x5012EB push eax`（值）→ `0x5012EC push 0x824e28`（键名）→ `0x5012F1 push ecx` → `0x5012F4 call 0x529560`。
  - 所在函数 0x501210 是序列化/写回路径（同窗口 `0x50138C call 0x42ED60` = `.json:percent_built.writer`；多次 `call 0x5275C0/0x528660/0x4759D0` 写各字段）；`0x529560` 与 Read_INI 的 `0x5295F0`（`ps:L113-L115` 标注 `CCINIClass::Get_Bool`，读）**不同**。
  - **判定**：0x5012ED 是「把字符串常量地址压栈传参」的编码，**不是**对 `[ebx+0x1ED]` / INI 缓冲区的写指令；静态上属 **INI 写回/序列化一侧的键名 xref，不是第二个读取点**。执行方原猜测的「是否 Write_INI 回写」在静态层面得到支持。但 `Write_INI`/`Put_Bool` 之类**符号名不是二进制字面**（§4 第 4 条），只给静态归类、不宣称符号级定谳。
- 原 §4.5：「5. R14 的第二 xref 0x5012ED 在 CHAIN_SYNTHESIS.md 条目中未呈现，其性质（是否 Write_INI 回写等）本任务**未核实**。」→ 改后整条重写为上述补做结果（标题即为「**本修正版已补做静态反汇编核实（原 v2 §4.5「未核实」已撤）**」），含证据 L34/.json:L55、脚本与 stdout 路径、逐条解码、判定与符号名边界。
- `LEDGER_SECTION_DRAFT_v2.md` 备注新增同结论段。

**§4.10「未逐行复核全部引用区间的每个数」：改写为「本轮自愿不做」**
- 采纳：24 个引用区间全是磁盘纯文本，逐数复核静态只读可完成（核验方 `_x.py` SEC E 已实读落盘），不应与「运行期不可得」并列为遗留未验。
- 原：「10. `_regrade_scan.py` 的证据引用核验只验证「文件存在+行号范围有效+首行内容相符」，未逐行复核全部引用区间的每个数（关键行已人工核对：…）。」
- 改后：「10. **§4.10 已改写…**：24 个引用区间全是磁盘纯文本，逐数复核**静态只读可完成**…本轮**自愿不做**全部区间的逐数重算，理由=25 分钟时限内优先完成 C1–C6 的定点改正与本轮可闭环补做（C1 运行日志、C5 静态反汇编）；已核对的是…**不与「运行期不可得」类未验并列**。」
- 另 §4 新增第 12 条把「本轮未验/未做」集中如实列出；§5「遗留未验项」补「第 10 条为本轮**自愿不做**（静态可查），非『不可得』」。

---

## C6 · `LEDGER_SECTION_DRAFT_v2.md` A 节 L26 注记位置

**复核结论：成立（采纳）**
- 原 L26（`_fix_checks_out.txt` L61）：「| §6xx 待编号 | 字符串 `PlayerControl` 全镜像恰 1 处 @0x824E28；.text xref 2 处（0x500BBF、0x5012ED，**后者性质未核实**） | ps:L11, L32-L34 |」——「后者性质未核实」确实写在**拟入账【已证】条目**里（`_fix_checks_out.txt` L62 = True），把自认未核实的东西带进字节级台账。
- 处置：**把注记移出【已证】条目**；因 C5 已补做核实，A 节该行改为纯读数「…；.text 中 LE32==0x824E28 的 xref 2 处（0x500BBF、0x5012ED） | ps:L11, L32-L34 |」，性质结论（含静态判定与符号名边界）移入「备注（不改变定级）」新增的 C6 段，并标注「已从【已证】条目中移出」。

---

## 两份被修正件的顶部修正标记（验收判据）

两份文件第 2 行均为（逐字）：
`> 修正于 2026-11-12（依据 lead/re_chain_v2_xverify_20261112/XVERIFY.md 的 C1–C6；详见 lead/re_chain_v2_fix_20261112/FIX_RECORD.md）`

---

## 边界与未验（如实列出，不补造）

1. **未验**：24 个引用区间的**每一个**数字未逐一重算——纯文本只读可完成，本轮**自愿不做**（时限内优先 C1–C6 定点改正与可闭环补做），已核「文件存在 + 行号范围 + 首行/键值 + 点名区间」。不与运行期不可得类未验混列。
2. **未验**：`0x529560` 的**确切符号名**（`Write_INI`/`Put_Bool` 之类不是二进制字面）；本轮只给「INI 写回/序列化一侧」的静态归类，不宣称符号级定谳。`0x5012ED` 的**运行期**行为未验证（零真机铁律下不可得），本轮只做纯静态反汇编。
3. **未验**：`0x7C978A` 是否 CRT `atexit`；CRT 初始化表遍历顺序、atexit 注册时序；台账历史指纹 `93c2974b` 算法（维持原【未决】）。
4. **未验**：全部运行期行为（CFG 是否与实际路径一致、函数指针/0xAA1078 是否真的不逃逸、初始化/atexit 实际次序、PercentBuilt 是否真的无运行时读取点）——零真机铁律下**不可得**。本轮所有【未证】只作静态分类，不宣称运行期证实或证伪。
5. **C1 日志的边界**：`_pssim_rerun_runlog.txt` 的时间戳/退出码由本轮 `subprocess.call` 实跑写出并落盘，但**日志文本本身可被人为伪造**，不构成密码学意义的「重跑证明」；它满足的是任务约定的「带时间戳与退出码的运行日志」闭环，且与 `_pssim_rerun_driver_stdout.txt` 的 `[1]`–`[5]` 判定日志、`driver_sha256_before/after` 一致可互证。原 `_pssim_rerun.py` 未改动（sha 前后同为 `37d2f977…7086`），既有 5 个产物逐字节不变。
6. **未验**：除 `_fix_baseline.json` 收录的 170 个既有件外，仓库其他路径是否被改动；本轮只写两个允许目录，未执行任何 git 操作。
7. **未验**：两份修正件中所有 Markdown 链接是否全部可点开；本轮只实测 `_pssim_rerun_out.txt` 这一条死链（已从正文删除，仅在「更正说明」中作为文字出现，不再是链接）。
8. 全部指纹为 `hashlib.sha256` 实算，全部结论基于磁盘静态读数；复核输出已落盘 `_fix_checks_out.txt` / `_fix_checks_pwsh_out.txt` / `_disasm_5012ed_out.txt` / `_pssim_rerun_runlog.txt` / `_pssim_rerun_driver_stdout.txt`，可复现。

---

## 收尾指纹（既有件零改动实证）

- 基线：`_fix_checks.py` 首次运行生成 `_fix_baseline.json`，收录 **170** 个既有件（9 个 WATCHED 目录全部文件 + 5 个 KEY_FILES + XVERIFY 4 件 + 写域 `re_chain_synth_v2_20261111` 原有 12 件），全部 `hashlib.sha256` + 字节数。
- 收尾：`python -I -X utf8 <abs>/_fix_checks.py verify` 重算比对，输出见 `_fix_checks_out.txt`（verify 模式覆写）与 `_fix_checks_verify_pwsh_out.txt`。
- **实算结果（hashlib）**：`VERIFY baseline=170 now=170 drift=2 missing=0 new=0`；唯二的 DRIFT 正是两份被修正件：
  - `RE_GRADING.md`：`4cd502f3…4b06bf3` / 16,885 B → `c17a3c63…fcc967e5` / 26,217 B
  - `LEDGER_SECTION_DRAFT_v2.md`：`eb851029…e17bde` / 7,587 B → `da79a234…4e5e0bab` / 12,266 B
  - 其余 **168 个既有件 0 漂移**，包括 XVERIFY.md / `_x.py` / 两份 `_x_*stdout.txt`、9 个 WATCHED 证据目录全部文件、`_pssim_rerun.py`（`37d2f977…7086` / 4,151 B 前后相同）、`_pssim_rerun_stdout.txt`（0 B）、`_pssim_rerun_stderr.txt`（8 B）、`_ps_disasm_rerun_copy.py`、`_ps_disasm_out.txt`(65,202 B)、`_ps_disasm_out.json`(3,297 B)、`_regrade_scan.py`/`_regrade_scan_out.txt`、`_integrity_check.py`/`_baseline_snapshot.json`、5 个 KEY_FILES。C1 重跑确实重写了原脚本的 5 个产物，但逐字节不变（`products_unchanged=True`）。
  - 透明记录：verify 脚本初版因 `json.load` 还原为 list、而实时 `fp()` 返回 tuple，导致首次输出 `drift=170` 的**假阳性**（全部 before/after 指纹字串其实相同）。已就地修正为比较前统一 `tuple(v)`，复跑得 `drift=2`；两次输出均在 `_fix_checks_verify_pwsh_out.txt` / `_fix_checks_out.txt` 留痕，未掩盖。
- 关键件（hashlib 实算，与 XVERIFY X5 一致）：`ra2bench/gamemd.exe` = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` (4,825,360 B)；`CHAIN_SYNTHESIS.md` = `c88717d71c4b59d88ecd04f234843f561a829e63f5b967659e10acfdcf8254b3` (20,971 B)；`LEDGER_SECTION_DRAFT.md` = `b40ac2a7b6fade6854fc0960aa9b01252ccff3dc292c780b979a8e56b664a800` (3,415 B)；`_repro_ps_disasm.txt` = `e3b0c442…b7852b855` (0 B)；`_ps_disasm.py` = `9a16086763924c269c2166fbcfd22c636ffb1800d6f78d54c72437c0c2d6c37e` (20,572 B)。

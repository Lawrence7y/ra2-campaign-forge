# V3_VERIFY.md — 拟入账台账 §6xx 草案（v2 修正版）三轮独立复核报告

> **独立核验方**：本会话（非执行方）。基准时点：2026-11-12 02:1x（Asia/Shanghai）。
> **唯一写域**：`lead\re_chain_v3_verify_20261112\`（新建目录，仅写 `_v3.py`、`_v3_stdout.txt`、`_v3_pwsh_stdout.txt`、`V3_VERIFY.md`）。其余全部路径只读，零字节改动；无 git commit / push / reset / checkout。
> **零真机铁律**：未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 attach、未读活进程内存，未写任何 hook / 采样 / MiniDump / SuspendThread 代码；`gamemd.exe` 仅以 `open(..., 'rb')` 静态读取磁盘字节供 `hashlib` 与 `capstone` 反汇编使用。
> **实跑命令**：
> `python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_chain_v3_verify_20261112\_v3.py *> D:\Project\ra2-campaign-forge\lead\re_chain_v3_verify_20261112\_v3_pwsh_stdout.txt`

---

## 0 · 靶件与被核验件指纹自核（hashlib.sha256 实算）

| 对象 | 路径 | 实算字节数 | 实算 SHA-256 | 状态 |
|---|---|---:|---|---|
| 靶件二进制 | `ra2bench\gamemd.exe` | 4,825,360 B | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | **MATCH** |
| 被修正件 1 | `lead\re_chain_synth_v2_20261111\RE_GRADING.md` | 26,217 B | `c17a3c63a3c8858761b206622f60f96ff5fc579ffd1cd2fe838869c2fcc967e5` | **MATCH** |
| 被修正件 2（拟入账草案） | `lead\re_chain_synth_v2_20261111\LEDGER_SECTION_DRAFT_v2.md` | 12,266 B | `da79a234804247fd3477957b997e51202553e882d8654dd68e91c9274e5e0bab` | **MATCH** |
| 修正记录 | `lead\re_chain_v2_fix_20261112\FIX_RECORD.md` | 23,869 B | `6276243bf0b0f2ef3b99dfb7849bd56ace58431e4cc6d9049e47c7e3db8c5efe` | **MATCH** |
| 上轮核验意见 | `lead\re_chain_v2_xverify_20261112\XVERIFY.md` | 24,363 B | `9ef8b4a1fbe51278e190d30b48807a504bb191d396238c2507ce26ee1da9856f` | **MATCH** |
| 既有件基线对拍 | `lead\re_chain_v2_fix_20261112\_fix_baseline.json`（170 件） | — | `baseline_total=170, drift=2（仅上述两份被修正件）, missing=0` | **168 件 0 漂移** |

---

## 1 · 逐条核验总表（V-C1 … V-C6 + V-ALL）

| 编号 | 核验项 | 判定 | 核心实算证据摘要 | 需再改项 |
|---|---|---|---|---|
| **V-C1** | 虚假声称 `_pssim_rerun_out.txt` 是否已撤 | **PASS** | ① `os.path.exists` = `False`；② 死链已清零（`is_markdown_link=False`），残留字面仅出现在撤回/更正声明中（`RE_GRADING.md` L81/L103、`LEDGER_SECTION_DRAFT_v2.md` L60）；③ 已如实改写为「stdout=0 B、未产生综合日志文件」；④ 补件 `_pssim_rerun_runlog.txt`（1,941 B，sha `23a536dd…`）含起止时间戳（`01:34:23`–`01:34:33+08:00`）、命令、`driver_exit_code=0` 及产物指纹 | 无 |
| **V-C2** | 措辞绝对化是否改准 | **PASS** | `RE_GRADING.md` L24–L28 已精确区分 **22 条 `文件:行区间` + 2 条 `文件:键`**，明确声明「只核文件存在，未打印首行实文」「不作逐引用首行内容相符的判据」，并补记两键实际 JSON 键值与 REF18（`ld:L88-L103` vs `oo:L6`）支撑关系。独立实算 `_regrade_scan_out.txt`：`[OK]` = **22 条**，`[OK*]` = **2 条**（L53、L55） | 无 |
| **V-C3** | R4「无别名逃逸」定级是否已统一（**最重要**） | **PASS** | ① `LEDGER_SECTION_DRAFT_v2.md` B 节 L38 已将「无别名逃逸」移出 CFG；② C 节新增第 3 项 L45 `§6xx 待编号【未证】（C3 本修正版新增）「0xAA1078 无别名逃逸」`，与 C 节第 2 项 L44（R2 尾注【未证】）同档；③ `RE_GRADING.md` L33（统一口径）、L38（R2）、L40（R4）、L59–L60（§2.1 统计 3 项【未证】）、L89（§4.3）完全一致 | 无 |
| **V-C4** | §2 理由列的「推断写成读数」是否已拆出 | **PASS** | R10（L46）、R11（L47）、R13（L49）、R14（L50）、R16（L52）均已改为「**仅计数/指令/结构读数部分维持【已证】+ 推断/机制部分拆出单列**」，不再整条笼统维持【已证】；`LEDGER_SECTION_DRAFT_v2.md` A 节（L24/L25/L27/L29/L31）已剔除推断文字，C 节第 4 项（L46）单列 `ps:L899-L900`【未证】，备注（L54–L58）逐项交待拆出去向 | 无 |
| **V-C5** | `0x5012ED` 是否已查清（含独立反汇编对拍） | **PASS** | ① `RE_GRADING.md` §4.5（L91）与 `LEDGER_SECTION_DRAFT_v2.md` 备注（L59）已撤回「未核实」并给出静态结论；② 独立 Capstone 反汇编 `gamemd.exe` 证实：`0x5012EC` 为 `68 28 4E 82 00` = `push 0x824e28`（`0x5012ED` 即其 +1 处的 imm32，LE32=`0x00824E28` 指向 `.data` 字符串 `"PlayerControl"`），位于函数 `0x501210` 内；其前 `0x5012E1` 为 `mov al, byte ptr [ebx + 0x1ed]`（读标志），随后 `push eax` / `push 0x824e28` / `push ecx` / `0x5012F4 call 0x529560`，同函数 `0x50138C call 0x42ed60`。独立实算与修正件结论**完全一致** | 无 |
| **V-C6** | 【已证】清单（A 节）是否还夹带未核实注记 | **PASS** | 逐条扫描 `LEDGER_SECTION_DRAFT_v2.md` A 节全部 **18 条**（L14–L31）：原 L26（现 L28，A-15）的「后者性质未核实」已移除；全 18 条对不确定词集（`未核实/未验/待证/未证/未决/未定谳/可能/猜测/疑似/或许/外推/假说`）命中数为 **0**，A 节纯净 | 无 |
| **V-ALL** | A 节每条读数是否都能追到证据 `文件:行` | **PASS** | A 节共 **18 条**（L14–L31）：**有行号 = 18 条 / 只文件名 = 0 条 / 无证据 = 0 条**；全部 `缩写:行区间` 经 `_v3.py` 实算均在对应证据文件总行数范围内（`valid=True`）。（仅 A-10 在 `oo:L6, L28-L46` 之外附有一条补充子句 `地图原文件 grep 14 处 PlayerControl=no`，其精确行号 `:107-263` 见 `RE_GRADING.md` R9 L45，不影响主引用可定位性） | 无 |

---

## 2 · 逐条核验详证

### V-C1 · 虚假声称是否已撤 —— **PASS**

1. **文件存在性自核**：
   `_v3.py` 实测 `os.path.exists(r"D:\Project\ra2-campaign-forge\lead\re_chain_synth_v2_20261111\_pssim_rerun_out.txt")` = **`False`**（`_v3_stdout.txt` L14）。
2. **残留引用 grep 核查**：
   在两份被修正件中搜索子串 `_pssim_rerun_out`（`_v3_stdout.txt` L15–L20）：
   - `RE_GRADING.md` 命中 2 处（L81、L103），`is_markdown_link` 均为 `False`；
   - `LEDGER_SECTION_DRAFT_v2.md` 命中 1 处（L60），`is_markdown_link` 为 `False`。
   - 三处命中**全部是显式的勘误/撤回声明**（明写「`_pssim_rerun_out.txt` 实际不存在，v2 原件称『全文落盘』为 FALSE」「`_pssim_rerun_out.txt` 从未存在，已从本清单删除」），正文与文件清单中已无任何把该文件当作真实存在文件的引用或 Markdown 链接。
3. **如实描述核查**：
   `RE_GRADING.md` L81 已改为如实表述：「探针 **stdout = 0 B**（`_pssim_rerun_stdout.txt`，sha256 `e3b0c442…`=空串）、stderr = 8 B `(done)`（`_pssim_rerun_stderr.txt`）、退出码 0；**未产生综合日志文件**，故不存在『全文落盘』件。」
4. **重跑闭环证据核查**：
   - `lead\re_chain_v2_fix_20261112\_pssim_rerun_runlog.txt` **存在**（1,941 B，sha256 `23a536dde1912ab4ed236f8d1398229fdc406ada331c0b3887db3fa886faabd1`）；
   - 内容含起止时间戳（`start_local: 2026-11-12T01:34:23+08:00`、`end_local: 2026-11-12T01:34:33+08:00`）、精确执行命令、退出码（`driver_exit_code: 0`）、driver 前后 sha256（均为 `37d2f977…7086`，4,151 B）、以及捕获的 `_pssim_rerun_driver_stdout.txt`（1,515 B，sha256 `f87288b79cd337bf0ababb269c83adabe1adbd6254fff358dd59518ed8cb581f`）。

---

### V-C2 · 措辞绝对化是否改准 —— **PASS**

1. **修正后 L24–L28 措辞核查**（原 L22 因首部加 1 行修正标记现位于 L24）：
   - `RE_GRADING.md` L24 原文：「该扫描同时做了**证据引用可达性核验**：共解析出 **24 条引用，OK=24 / BAD=0**。精确表述为：**24 条中 22 条为 `文件:行区间`、2 条为 `文件:键`**；前者核『文件存在 + 行号范围有效』并打印区间首行实文，后者核『文件存在 + JSON 键存在 + 键值』（`_regrade_scan_out.txt` L53/L55 对这两条标 `[OK*] 键引用不核行号`，**只核文件存在，未打印首行实文**）。**不作「逐引用首行内容相符」的判据**：多条首行只是小节标题……读数落在区间后续行。」
   - L25–L27 补记了 `verdict` 与 `percent_built` 两条键引用的实际 JSON 键值；L28 补记了 REF18（`ld:L88-L103` 首行仅支撑边界列、`0add791d` 在 `_ld_diff_out.txt` 0 命中但由同条另引的 `_oo_map_out.txt:L6` 支撑）。措辞准确、客观。
2. **独立实算 `_regrade_scan_out.txt` 中的 `[OK*]`**（`_v3_stdout.txt` L62–L73）：
   - 文件大小 7,062 B，sha256 = `f8468118614900feaf7494b57e126ce2d8f66c5b87e3f236a97a2c2ab8177038`；
   - `[OK]` 标记：**22 条**；
   - `[OK*]` 标记：**共 2 条**，具体为：
     - **L53**：`L82  playerctrl_semantics_20261111/_ps_disasm_out.json:verdict -> 文件存在(147 行), 键引用不核行号 [OK*]`
     - **L55**：`L83  playerctrl_semantics_20261111/_ps_disasm_out.json:percent_built -> 文件存在(147 行), 键引用不核行号 [OK*]`

---

### V-C3 · R4「无别名逃逸」定级是否已统一（最重要） —— **PASS**

1. **`LEDGER_SECTION_DRAFT_v2.md` B 节（CFG 区）核查**：
   - B 节第 2 条（**L38**）实文：
     `| §6xx 待编号 | 能指向 0x54A4F0/0x54A630 的 call/jmp [reg+8] 调用点全镜像唯一 = 0x546069（污点传播唯一消费者）；由此推「进入两函数必须经虚派发」。**C3 更正：原括注「无别名逃逸」已移出本条、降入 C 节第 3 项【未证】**——它不是字节级读数……与同源于 sf:L20/L28/L40 的 R2 尾注按 RE_GRADING §2 统一口径同级 | sf:L39-L47; sf:L20, L28, L40 |`
   - 结论：B 节 CFG 结论中已**不再保留**「无别名逃逸」作为【已证（CFG）】内容，仅保留已移出说明。
2. **`LEDGER_SECTION_DRAFT_v2.md` C 节（待证区）核查**：
   - C 节第 2 项（**L44**，对应 R2 尾注）：`2. §6xx 待编号【未证】「函数指针值无法在运行期逃逸或复制到其它函数指针变量」……`
   - C 节新增第 3 项（**L45**，对应 R4 边界列）：`3. **§6xx 待编号【未证】（C3 本修正版新增）「0xAA1078 无别名逃逸」**：CHAIN_SYNTHESIS.md L69 边界列原文「污点分析证明 0xAA1078 是全镜像唯一消费者，无别名逃逸」……按 RE_GRADING §2 统一口径（依赖未验前提/运行期机制断言→【未证】），与第 2 项同级；**不再留在 B 节 CFG**。`
3. **`RE_GRADING.md` R4 / §2.1 / R2 三处口径一致性核查**：
   - **§2 统一口径补充（L33）**：明确规定凡「逃逸 / 无别名 / 无任何运行时读取点」类全称否定一律与 R2 尾注同降【未证】。
   - **R2（L38）**：新标记为 `维持【已证】（读数）；尾注拆出【未证】`。
   - **R4（L40）**：新标记为 `核心结论降【已证（CFG）】；指令个体与普查计数维持【已证】；**边界列「无别名逃逸」拆出降【未证】**`。
   - **§2.1 统计（L59–L60）**：`降为【未证】：3 项（原 2 项 + 本修正版新增 1 项）—— R5 时序归属、R2 尾注「运行期无法逃逸」、R4 边界列「无别名逃逸」（C3 统一口径）`；另在 §2.2（L66）、§4.3（L89）、§5（L113）全部同步为 3 项【未证】。
   - **判断标准核对**：R2 尾注与 R4「无别名逃逸」**两处同为【未证】档**，完全统一。

---

### V-C4 · §2 理由列的「推断写成读数」是否已拆出 —— **PASS**

5 条相关条目（R10、R11、R13、R14、R16）在两份修正件中的定级与拆分行号对照如下（`_v3_stdout.txt` L96–L130）：

| 条目 | 拆出的推断/机制内容 | `RE_GRADING.md` 行号与新标记 | `LEDGER_SECTION_DRAFT_v2.md` 对应处理与行号 |
|---|---|---|---|
| **R10** | 「11 国」括注（与探针 owner 表有出入） | **L46**：`维持【已证】（计数）；「11 国」括注拆出【推断·单列】`；§2.1 **L60**；§4.6 **L92** | A 节 **L24**（A-11）仅保留 `Units=3360、Infantry=2240，合计 5600；14 owner 各 400`；备注 **L55** 明写已拆出 |
| **R11** | 「其余 11 房为 0」（大版 yrm 无 `[Houses]` 节，14 房框架系外推） | **L47**：`维持【已证】（仅计数部分：240/160/41 与 owner 分布）；「其余 11 房为 0」拆出单列【推断·外推】`；§2.1 **L60**；§4.6 **L92** | A 节 **L25**（A-12）仅保留 `Units=240 Inf=160 Structures=41；Russians/Americans 各 120 车+80 步，Neutral 持 41 建筑`；备注 **L56** 明写已拆出 |
| **R13** | 「排除压缩/编码变换假说」（`ld:L91` 排除法对比结论） | **L49**：`维持【已证】（仅 size/sha/结构读数）；「排除压缩/编码变换假说」拆出单列【推断·排除法】`；§2.1 **L60**；§4.6 **L92** | A 节 **L27**（A-14）仅保留三份载体 size/sha/熵/首字节/小节集/几何/键行读数，删去原结论尾缀；备注 **L57** 明写已拆出 |
| **R14** | 「Read_INI/Get_Bool」（符号命名）、「读取并写入」（寄存器数据流关联） | **L50**：`维持【已证】（仅指令/普查读数）；「Read_INI/Get_Bool」「读取并写入」拆出单列【推断】`；§2.1 **L60–L61**；§4.6 **L92** | A 节 **L28–L29**（A-15/A-16）仅保留字符串位点、xref 位点与三条机器指令字节读数；备注 **L54** 明写符号命名非二进制字面 |
| **R16** | `ps:L899-L900`「引擎无任何运行时读取点」（全称否定机制断言） | **L52**：`维持【已证】（仅普查读数）；ps:L899 机制断言拆出单列【未证】`；§2.1 **L60**；§4.6 **L92** | A 节 **L31**（A-18）仅保留普查计数；**C 节第 4 项（L46）**新增 `§6xx 待编号【未证】（C4 拆出）ps:L899-L900「引擎无任何运行时读取点」`；备注 **L58** 明写拆出关系 |

---

### V-C5 · `0x5012ED` 是否已查清 —— **PASS**

1. **修正件结论核查**：
   - `RE_GRADING.md` §4.5（**L91**）与 `LEDGER_SECTION_DRAFT_v2.md` 备注（**L59**）已撤回「未核实」，给出静态反汇编结论；同时 `RE_GRADING.md` §4.10（**L96**）已将「未逐行复核全部引用区间的每个数」改写为「静态只读可完成、本轮自愿不做，不与运行期不可得类未验并列」。
2. **本核验方独立 Capstone 反汇编实算**（`_v3.py` SEC V-C5，输出见 `_v3_stdout.txt` L133–L189）：
   - **靶件自核**：`ra2bench\gamemd.exe` 大小 = `4,825,360 B`，SHA-256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（PASS）。
   - **PE 节表实算映射**：`ImageBase = 0x00400000`；`VA 0x5012ED` 落在 `.text` 节，`file_offset = 0x1012ED`，该处 4 字节 LE32 = `0x00824E28`；`VA 0x824E28` 落在 `.data` 节，`file_offset = 0x424E28`，该处 C 字符串实读为 `'PlayerControl'`。
   - **区间 `0x5012EC`–`0x501300` 独立反汇编结果**：
     ```text
     0x5012EC  68284e8200        push   0x824e28
     0x5012F1  51                push   ecx
     0x5012F2  8bce              mov    ecx, esi
     0x5012F4  e867820200        call   0x529560
     0x5012F9  8b9354600100      mov    edx, dword ptr [ebx + 0x16054]
     0x5012FF  52                push   edx
     ```
   - **所在函数（`0x501210`–`0x501398`）前置与尾部关键指令实算**：
     ```text
     0x501210  83ec14            sub    esp, 0x14
     ...
     0x50121B  8bd9              mov    ebx, ecx
     ...
     0x5012E1  8a83ed010000      mov    al, byte ptr [ebx + 0x1ed]
     0x5012E7  8d4c2410          lea    ecx, [esp + 0x10]
     0x5012EB  50                push   eax
     0x5012EC  68284e8200        push   0x824e28
     0x5012F1  51                push   ecx
     0x5012F2  8bce              mov    ecx, esi
     0x5012F4  e867820200        call   0x529560
     ...
     0x501384  8d8b00570000      lea    ecx, [ebx + 0x5700]
     0x50138A  50                push   eax
     0x50138B  56                push   esi
     0x50138C  e8cfd9f2ff        call   0x42ed60
     ...
     0x501398  c20400            ret    4
     ```
   - **独立实算与修正件逐项对比**：
     1. 是否是 `push imm32=0x824E28`：**是**（`0x5012EC` 指令为 `68 28 4E 82 00` = `push 0x824e28`，`0x5012ED` 为该指令 +1 字节处的 4 字节立即数）。
     2. 是读还是写：`0x5012EC` 本身是将字符串常量地址 `0x824E28` 压栈传参；其前 `0x5012E1` 是**读取** `byte ptr [ebx + 0x1ed]` 到 `al` 并 `push eax` 传给 `call 0x529560`（与 `0x500BD6 call 0x5295f0` 读出 `al` 后 `mov [ebx+0x1ED], al` 方向相反），同函数尾部 `0x50138C call 0x42ed60` 对应 `PercentBuilt` 的 writer，故静态归类确属序列化/写回路径，而非第二个 `PlayerControl` 写入 `[ebx+0x1ED]` 的点。
     3. 所在函数是否先取 `[ebx+0x1ED]`：**是**（`0x5012E1: 8a 83 ed 01 00 00` = `mov al, byte ptr [ebx + 0x1ed]`）。
     4. **对比结论**：本核验方独立实算结果与修正件（`RE_GRADING.md` L91、`LEDGER_SECTION_DRAFT_v2.md` L59、`FIX_RECORD.md` C5）**100% 一致，无任何出入**。

---

### V-C6 · 【已证】清单里是否还夹带未核实注记 —— **PASS**

- `_v3.py` 逐行解析 `LEDGER_SECTION_DRAFT_v2.md` A 节表格，共提取 **18 条**【已证】条目（L14–L31，编号 A-01 至 A-18，见 `_v3_stdout.txt` L193–L250）。
- 原 A-15（原 L26，现 **L28**）已改为：
  `| §6xx 待编号 | 字符串 PlayerControl 全镜像恰 1 处 @0x824E28；.text 中 LE32==0x824E28 的 xref 2 处（0x500BBF、0x5012ED） | ps:L11, L32-L34 |`
  「后者性质未核实」已完全移出 A 节（静态核实结论放于文末备注 L59）。
- 对 A 节全部 18 条的「读数」列与「证据」列扫描不确定词集 `['未核实', '未验', '待证', '未证', '未决', '未定谳', '可能', '猜测', '疑似', '或许', '外推', '假说']`：**命中 0 条**。A 节现已完全纯净，仅含字节级/文件直接读数。

---

### V-ALL · A 节每一条读数的证据 `文件:行` 可定位性核查 —— **PASS**

- **A 节条目总数**：**18 条**（`LEDGER_SECTION_DRAFT_v2.md` L14–L31）。
- **三类计数结果**（`_v3_stdout.txt` L251–L276）：
  - **有行号（可定位 `文件:行`）**：**18 条**（A-01 至 A-18 全部具备 `缩写:行号` 且行号范围在对应证据文件内 100% 合法有效）
  - **只文件名（无行号）**：**0 条**
  - **无证据**：**0 条**

| A 节序号 | 草案行号 | 证据列原文 | 解析与文件总行数校验（`_v3.py` 实算） | 分类 |
|---|---|---|---|:---:|
| A-01 | L14 | `sf:L7-L11` | `sf` (1834 行): L7–L11 `valid=True` | 有行号 |
| A-02 | L15 | `sf:L13-L15` | `sf` (1834 行): L13–L15 `valid=True` | 有行号 |
| A-03 | L16 | `sf:L18-L19` | `sf` (1834 行): L18–L19 `valid=True` | 有行号 |
| A-04 | L17 | `sf:L20` | `sf` (1834 行): L20 `valid=True` | 有行号 |
| A-05 | L18 | `sf:L66-L68` | `sf` (1834 行): L66–L68 `valid=True` | 有行号 |
| A-06 | L19 | `sf:L26-L29, L31-L35` | `sf` (1834 行): L26–L29, L31–L35 `valid=True` | 有行号 |
| A-07 | L20 | `sf:L21-L23` | `sf` (1834 行): L21–L23 `valid=True` | 有行号 |
| A-08 | L21 | `cw:L66` | `cw` (177 行): L66 `valid=True` | 有行号 |
| A-09 | L22 | `cw:L66-L68` | `cw` (177 行): L66–L68 `valid=True` | 有行号 |
| A-10 | L23 | `oo:L6, L28-L46; 地图原文件 grep 14 处 PlayerControl=no` | `oo` (151 行): L6, L28–L46 `valid=True`（注：分号后补充子句对应 `RE_GRADING.md` R9 L45 的 `scratch/boot_probe/arm_a/XMP29U2.MAP:107-263`） | 有行号 |
| A-11 | L24 | `md:L17-L50; oo:L50-L52, L56-L82` | `md` (167 行): L17–L50 `valid=True`; `oo` (151 行): L50–L52, L56–L82 `valid=True` | 有行号 |
| A-12 | L25 | `md:L54-L78; ld:L25-L28` | `md` (167 行): L54–L78 `valid=True`; `ld` (103 行): L25–L28 `valid=True` | 有行号 |
| A-13 | L26 | `md:L81-L103; ld:L29-L31` | `md` (167 行): L81–L103 `valid=True`; `ld` (103 行): L29–L31 `valid=True` | 有行号 |
| A-14 | L27 | `ld:L88-L103; md:L55, L82; oo:L6` | `ld` (103 行): L88–L103 `valid=True`; `md` (167 行): L55, L82 `valid=True`; `oo` (151 行): L6 `valid=True` | 有行号 |
| A-15 | L28 | `ps:L11, L32-L34` | `ps` (1283 行): L11, L32–L34 `valid=True` | 有行号 |
| A-16 | L29 | `ps:L113-L115` | `ps` (1283 行): L113–L115 `valid=True` | 有行号 |
| A-17 | L30 | `ps:L905` | `ps` (1283 行): L905 `valid=True` | 有行号 |
| A-18 | L31 | `ps:L12, L36-L39, L894-L899` | `ps` (1283 行): L12, L36–L39, L894–L899 `valid=True` | 有行号 |

---

## 3 · 边界与未验（如实列出，不补造）

1. **零真机边界**：本轮核验全程只读磁盘文件字节，未启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，未 attach 任何进程、未读活进程内存、未编写任何 hook / 采样 / MiniDump / SuspendThread 代码。因此所有涉及运行期行为的断言（如 B 节 CFG 路径是否在运行期实际走通、C 节第 1–4 项运行期时序/指针逃逸/运行时读取点）在零真机铁律下均**未验**（且在草案中均已正确隔离在 B 节或 C 节，未混入 A 节字节级台账）。
2. **符号名边界**：`0x501210` / `0x529560` / `0x5295F0` / `0x42ED60` 等函数的符号名（如 `Write_INI`、`Put_Bool`、`Get_Bool`）非 PE 二进制内字面字符串；本轮 V-C5 独立反汇编验证的是机器指令字节、寄存器数据流与立即数引用，不对符号名作字面定谳。
3. **A 节内部颗粒度未重算项**：本轮 V-ALL 完整实算了 A 节全部 18 条证据引用的文件存在性与行号区间合法性，并在 V-C5 独立反汇编了 `0x501210`–`0x501398`；对于 XVERIFY 第 1 轮已核验通过的其余各证据文件内部具体统计数字（如 1,392,527 条指令、5,600 单位计数等），本轮验证了该批证据文件与 `_fix_baseline.json`（170 件）**0 漂移**，未重新跑全量 `.text` 分块扫描探针。
4. **C1 运行日志的证明力边界**：`lead\re_chain_v2_fix_20261112\_pssim_rerun_runlog.txt` 与 `_pssim_rerun_driver_stdout.txt` 提供了完整的起止时间戳、命令行、退出码与产物哈希闭环，本轮已核实其文件存在、内容自洽且与重跑产物哈希一致；但静态日志文件本身不构成密码学意义上的不可伪造证明。

---

## 4 · 一句话总判

`VERDICT = READY_TO_APPEND`

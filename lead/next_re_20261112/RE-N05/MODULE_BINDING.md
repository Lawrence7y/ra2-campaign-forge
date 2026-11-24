# RE-N05 · MODULE_BINDING.md（地址归一）

> run_id `NEXT_RE_20261112_R01`，本轮**零真机**：只读磁盘 PE 字节与既有 JSON；未启动游戏、未 attach、未读活进程内存、未做任何 git 写操作。
> 证据：`EVIDENCE/re_n05_step1_verify.py`、`EVIDENCE/stdout_step1.txt`（含命令与 EXITCODE=0）、`EVIDENCE/re_n05_disasm.py`、`EVIDENCE/stdout_disasm.txt`（EXITCODE=0）。
> 本文件所有算式均由脚本对磁盘字节/JSON 原始数值**独立重算**，未照抄 Lead 的 `LEAD_INDEPENDENT_CHECKS.md`，也未执行或采信被中断的 `EVIDENCE/step1_module_binding.py`（见 `DISAGREE.md`）。

## 0 · 首段门槛：输入指纹实算

| 模块 | 路径（只读） | 字节数 | SHA-256（本次实算） | 期望值 | 结论 |
|---|---|---:|---|---|---|
| `gamemd.exe` | `ra2bench/gamemd.exe` | 4,825,360 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 同左 | `[本次实测]` 一致，PASS |
| `ddraw.dll` | `ra2youli/ddraw.dll` | 411,648 | `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9` | 同左 | `[本次实测]` 一致，PASS |

- 实算方法：PowerShell `Get-FileHash -Algorithm SHA256`（首轮交叉验证）与 Python `hashlib.sha256(open(...,"rb").read())`（`re_n05_step1_verify.py:file_info`）双路。
- 门槛判定：两值均严格相等 → 继续；若任一不等则脚本 `return 2` 并停止（脚本内含 hard gate）。
- `[本次实测]` `stdout_step1.txt:11-13, 128-130, 266`。
- 附带版本线索（只读）：`ra2opt/vendor/cnc-ddraw-7.1.0.0.zip` 内 `ddraw.dll` 与 `ra2youli/ddraw.dll` **逐字节相同**（同为 411,648 B / 同一 SHA-256），见 `EVIDENCE/stdout_step1.txt:128` 与 `EVIDENCE/stdout_step3.txt` 版本段；PDB 路径 `C:\Users\Nutzer\source\repos\cnc-ddraw\bin\ReleaseXP\ddraw.pdb`（`stdout_step1.txt:149`）。

## 1 · 栈证据的绝对地址 → 该趟实际模块基址（自己复算）

判据：StackWalk64 输出的帧名是 `<模块>+<RVA 形式偏移>`，故 `该趟实际基址 = 帧绝对地址 - 帧名偏移`。
同一趟、同一模块多帧必须给出**同一个**基址，否则该趟读数不自洽。

### 1.1 pid 14412（`_hl_match_14412.json`，单事件，`picked_by=only_tid`）

| 帧 | 名称 | addr（十进制 / 十六进制） | 偏移 | 算式（addr − off） | 反算基址 |
|---|---|---:|---:|---|---|
| #3 | `gamemd.exe+0x207f17` | 6,323,991 / `0x00607F17` | `0x207F17` = 2,129,687 | 6,323,991 − 2,129,687 | **`0x00400000`** = 4,194,304 |
| #6 | `gamemd.exe+0x20833f` | 6,325,055 / `0x0060833F` | `0x20833F` = 2,130,751 | 6,325,055 − 2,130,751 | **`0x00400000`** = 4,194,304 |

- 一致性反例校验：`6325055 − 6323991 = 1064`，`0x20833F − 0x207F17 = 1064` → 相等，两帧必属同一基址。`[本次实测]` `stdout_step1.txt:272-283, 316`。
- 其它模块（同趟交叉参照，非本卡目标）：`ntdll.dll` → `0x77BA0000`（1 帧）、`KERNELBASE.dll` → `0x76290000`（2 帧一致）、`USER32.dll` → `0x778F0000`（2 帧一致）。`[本次实测]` `stdout_step1.txt:272-283`。

### 1.2 pid 40500（`_hl_match_40500.json`，3 事件，`picked_by=most_gamemd_frames`）

| 事件 | 帧 | 名称 | addr | 偏移 | 算式 | 反算基址 |
|---|---|---|---:|---:|---|---|
| #0 (t=347.047) | #2 | `gamemd.exe+0x13eb1c` | 5,499,676 / `0x0053EB1C` | `0x13EB1C` = 1,305,372 | 5,499,676 − 1,305,372 | **`0x00400000`** |
| #0 (t=347.047) | #1 | `DDRAW.dll+0x22b06` | 1,417,489,158 / `0x547D2B06` | `0x22B06` = 142,086 | 1,417,489,158 − 142,086 | **`0x547B0000`** = 1,417,347,072 |
| #1 (t=351.594) | #3 | `gamemd.exe+0x13eb1c` | 5,499,676 | 1,305,372 | 同上 | `0x00400000` |
| #1 (t=351.594) | #2 | `DDRAW.dll+0x22b06` | 1,417,489,158 | 142,086 | 同上 | `0x547B0000` |
| #2 (t=354.938, frame=0) | #3 | `gamemd.exe+0x207f17` | 6,323,991 | 2,129,687 | 6,323,991 − 2,129,687 | `0x00400000` |

- 一致性：`gamemd.exe` 3 次出现均为 `0x00400000`；`DDRAW.dll` 2 次出现均为 `0x547B0000`。`[本次实测]` `stdout_step1.txt:288-309`。
- `0x547B0000` 自校验：`0x547B × 0x10000 = 21,627 × 65,536 = 1,417,347,072`；`+0x22B06 (142,086) = 1,417,489,158`，与记录 addr 完全相同。`[本次实测]` `stdout_step1.txt:317`。
- 其它模块同趟：`ntdll.dll=0x77BA0000`、`KERNELBASE.dll=0x76290000`、`USER32.dll=0x778F0000`、`win32u.dll=0x76690000`（各多帧一致）。`[本次实测]` `stdout_step1.txt:288-309`。

### 1.3 是否 ASLR / 是否重定位（PE 静态判据）

| 模块 | PE `ImageBase` | `DllCharacteristics` | `DYNAMIC_BASE`(0x40) | `IMAGE_FILE_RELOCS_STRIPPED`(0x1) | `.reloc` 目录 / 段 | 本趟实际基址 | 结论 |
|---|---:|---:|---|---|---|---|---|
| `gamemd.exe` | `0x00400000` | `0x0020` = `HIGH_ENTROPY_VA` only | **False** | **True** | RVA=0 / Size=0；**无 `.reloc` 段**；0 条基址重定位项 | `0x00400000` | `[本次实测]` **未重定位**；且因 `RELOCS_STRIPPED=True` + 无 `.reloc`，该 EXE **无法被重定位**，只可能加载在 `0x400000` |
| `ddraw.dll` | `0x10000000` | `0x0140` = `DYNAMIC_BASE` + `NX_COMPAT` | **True** | False | RVA=`0x66000` / Size=`0x51D0`；有 `.reloc` 段；**10,152 条重定位项**（10,120× type-3 HIGHLOW + 32× type-0 padding） | `0x547B0000` | `[本次实测]` **被 ASLR 重定位**，delta = `0x547B0000 − 0x10000000 = 0x447B0000` |

- 证据：`stdout_step1.txt:16-32`（gamemd）、`:133-157`（ddraw）、`:366-370`（结论）。
- `[静态推断]` `Machine=0x014C`（i386）、`SizeOfImage`：gamemd `0x796000`、ddraw `0x6C000`；`SectionAlignment/FileAlignment` = `0x1000/0x1000`（gamemd）、`0x1000/0x200`（ddraw）。
- `[静态推断]` ddraw 的 `call [abs]` 指令里的 4 字节绝对操作数与 `.data` 里的函数指针初值都在 `.reloc` 表里登记为 type-3 HIGHLOW，加载时被加上 `0x447B0000`；因此**磁盘字节里的 `0x100xxxxx` 是首选 VA，不是该趟运行期 VA**（例：`call dword ptr [0x10053A68]` 的 imm32 位于 RVA `0x22B02`，其 HIGHLOW 重定位存在，运行期变成 `[0x54803A68]`）。证据 `stdout_disasm.txt:201-206`。

## 2 · RVA → 首选 VA → 运行期 VA → 文件偏移（换算表）

换算规则（`[本次读码]` `re_n05_step1_verify.py:rva2off`）：
1. `首选 VA = PE ImageBase + RVA`；`运行期 VA = 该趟实际基址 + RVA`。
2. 用节表找 `vaddr <= RVA < vaddr + max(vsize, rawsize)`；`delta = RVA − vaddr`。
3. 仅当 `delta < SizeOfRawData` 时 `文件偏移 = PointerToRawData + delta`；否则该 RVA 落在 `VSize>RawSize` 的**零填充尾部，磁盘上无对应字节**。
4. 特别提醒：`gamemd.exe .text` 的 `VSize=0x3DF38D < RawSize=0x3E0000`（尾部是文件对齐填充，不是映射字节）；`gamemd .data` 与 `ddraw .data` 都是 `VSize > RawSize`（尾部是 BSS）。`[本次实测]` `stdout_step1.txt:33-38, 150-157, 362-364`。

| 位置 | RVA | 首选 VA（ImageBase+RVA） | 本趟运行期 VA | 所属节 | 节 VAddr / RawPtr / RawSize | delta | 文件偏移 | 目标处前 16 原始字节 |
|---|---:|---:|---:|---|---|---:|---:|---|
| `gamemd.exe+0x13EB1C` | `0x0013EB1C` (1,305,372) | `0x0053EB1C` (5,499,676) | `0x0053EB1C`（base `0x400000`，未重定位） | `.text` | `0x1000 / 0x1000 / 0x3E0000` | `0x13DB1C` | **`0x0013EB1C`** (1,305,372) | `8B D8 83 3D 44 04 AA 00 01 0F 85 BD 00 00 00 3B` |
| `gamemd.exe+0x207F17` | `0x00207F17` (2,129,687) | `0x00607F17` (6,323,991) | `0x00607F17` | `.text` | 同上 | `0x206F17` | **`0x00207F17`** (2,129,687) | `8B 44 24 1C 8B 8C 24 E4 00 00 00 40 3B C1 89 44` |
| `gamemd.exe+0x20833F` | `0x0020833F` (2,130,751) | `0x0060833F` (6,325,055) | `0x0060833F` | `.text` | 同上 | `0x20733F` | **`0x0020833F`** (2,130,751) | `B2 01 8B CE E8 98 EE FF FF 6A 00 68 00 68 60 00` |
| `ddraw.dll+0x22B06` | `0x00022B06` (142,086) | `0x10022B06` (268,577,542) | **`0x547D2B06`** (1,417,489,158) | `.text` | `0x1000 / 0x400 / 0x3C200` | `0x21B06` | **`0x00021F06`** (139,014) | `8B F0 85 F6 74 14 FF 75 18 8B 4D 08 FF 75 14 FF` |

- `[本次实测]` 全表来自 `stdout_step1.txt:321-361`；`ddraw` 的 `文件偏移 = RVA − 0x1000 + 0x400 = 0x22B06 − 0xC00 = 0x21F06`，不是 `0x22B06`。**把 RVA 当文件偏移是错的**（对 gamemd 恰好相等只是因为 `.text` 的 `vaddr == rawptr`）。
- `[本次实测]` 四行 `recorded_abs − run_VA = 0`（`stdout_disasm.txt:19, 85, 103, 119`），说明栈记录的绝对地址与上述运行期 VA 完全对齐。
- `[本次实测]` 反例（尾部不可映射）：`gamemd .data` 取 `RVA 0x47E004 = vaddr+rawsize+4` → `file_offset=None, in_raw=False`；`ddraw .data` 取 `RVA 0x5DE04` → 同样无文件字节（`stdout_step1.txt:362-364`）。
- `[静态推断]` 关于"首选 VA"的易错点：`STALL_CAPTURE_SUCCESS.md:68-76` 用的 `0x10022af3…` 是**首选 VA**，而该趟实际是 `0x547B0000` 基址；对 ddraw 的结论必须落在 RVA / 文件偏移上，不能把 `0x10022B06` 当成运行期地址（转引并复核，见 `DISAGREE.md`）。

## 3 · 通用语义判据（本卡四个位置共用）

`[本次读码]` `lead/re_d13_ruling_20261112/e3_stackwalker.py:225-241`：`walk()` 调真 `dbghelp!StackWalk64`，把每帧 `sf.AddrPC.Offset` 写入 `frames`，顺序为**由内向外**（第 0 帧 = 当前 EIP，后续帧 = 逐层返回地址）。因此：

- 除栈顶帧外，JSON 里的 `addr` 是**返回地址**（`call` 之后的下一条指令），**不是**"当时正在执行的阻塞指令"。
- 若该地址正好是一条指令的**起始边界**，真正的调用点是它**前面的那条 `call`**；边界必须由**从可信函数边界线性反汇编**确认（本轮用两种独立方法交叉：整段 `.text` 线性扫描的指令起点 bitmap + 从 `ret`/对齐填充之后的序言严格无间隙前向解码），不靠"往回退到看起来像指令开头"。
- 本卡四个位置的 `AddrPC` 都**不是栈顶帧**（14412 中是 #3/#6，40500 中是 #1/#2/#3），所以全部按返回地址处理；逐位置判定与前置 call 见 `WAIT_CHAIN.md`。
- 四个量必须分开标注：**RVA**（相对模块）、**首选 VA**（`ImageBase+RVA`）、**运行期 VA**（实际基址+RVA）、**文件偏移**（节表 `rawptr` 换算）。混用即错。

## 4 · 与既有表述的核对（不采信，只复核）

| 既有表述 | 本轮独立结论 |
|---|---|
| `docs/re/NEXT_RE_TASKS_20261112.md:191-196` 给的首选 VA `0x53EB1C / 0x607F17 / 0x60833F` | `[本次实测]` 对 gamemd 成立（未重定位，首选 VA == 运行期 VA）；但它们是**返回地址**，不是执行点 |
| `lead/next_re_20261112/REVIEW/LEAD_INDEPENDENT_CHECKS.md:33-40` 的两趟基址 | `[本次实测]` 独立复算完全一致（`0x400000` / `0x547B0000`），并额外给出 PE 层理由（gamemd 无 `.reloc` 且 `RELOCS_STRIPPED`） |
| `EVIDENCE/step1_module_binding.py:119` 把 ddraw 运行基址写成 `0x547A0000` | `[本次实测]` **错**，正确 `0x547B0000`；`0x547A0000+0x22B06 = 1,417,423,622`，比记录 addr 少 `0x10000`（65,536）。详见 `DISAGREE.md` |

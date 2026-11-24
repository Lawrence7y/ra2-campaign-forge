# RE-N02 · PE_MAP.md — 目标镜像静态地图

> run_id `NEXT_RE_20261112_R01` · 纯静态（只读磁盘 PE 字节）· 写域 `lead/next_re_20261112/RE-N02/`
> 生成脚本：`_frame_semantics_v2.py`（`pe_map()` / `pe_header_report()` / `base_recompute()`）
> 原始 stdout：`EVIDENCE/scan_stdout.txt`；机器可读：`EVIDENCE/PE_HEADER.txt`、`EVIDENCE/SUMMARY.json`

---

## 0 · 开工前镜像核对（必做项）

**`[本次实测]`** 命令（PowerShell，工作目录 `D:\Project\ra2-campaign-forge`）：

```powershell
$p='D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe'
$f=Get-Item -LiteralPath $p
$h=Get-FileHash -LiteralPath $p -Algorithm SHA256
"BYTES=$($f.Length)"; "SHA256=$($h.Hash.ToLowerInvariant())"
```

输出（退出码 0）：

```
PATH=D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe
BYTES=4825360
SHA256=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
EXPECTED=73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
MATCH=True
```

脚本内二次实算（`pe_header_report()`，`EVIDENCE/scan_stdout.txt` 首段，退出码 0）给出同一值。
**与期望值一致，未触发「不一致立即停止」条件，报告首段无需写异常。**

`[转引]` `docs/re/NEXT_RE_TASKS_20261112.md:83` 也登记了同一 sha256；本轮独立实算，不是照抄。

---

## 1 · 可选头字段（`pefile` 实读）

| 字段 | 值 | 等级 |
|:--|:--|:--|
| Machine | `0x014C` = I386（32 位） | `[本次实测]` |
| NumberOfSections | 5 | `[本次实测]` |
| **ImageBase** | **`0x00400000`** | `[本次实测]` |
| SizeOfImage | `0x00796000` = 7,954,432 B | `[本次实测]` |
| DllCharacteristics | `0x0020` | `[本次实测]` |
| **ASLR / DYNAMICBASE (bit 0x0040)** | **未置位 = False** | `[本次实测]` 位运算 `0x0020 & 0x0040 == 0` |
| **BASE_RELOC 目录** | **rva=`0x00000000`, size=0 → 不存在** | `[本次实测]` |
| 非零数据目录 | IMPORT `rva=0x007955C0/340`、RESOURCE `0x0077A000/98600`、DEBUG `0x003E1610/28`、IAT `0x003E1000/1544` | `[本次实测]` |

`[静态推断]` `0x0020` 在 WinNT.h 中对应 `IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA`；
本镜像为 32 位，该位在 32 位加载下的实际效果本轮不推断，也不作为 ASLR 依据。
**承重结论只依赖可验证的两条**：DYNAMICBASE 位为 0、且无重定位目录 ⇒
该 PE **不具备 Windows 标准 ASLR 重定位能力**；这与 §3 的实测基址一致，但不是同一证据。

## 2 · 节表（name / rva / vsize / rawptr / rawsize / characteristics）

| name | rva | vsize | rawptr | rawsize | characteristics | EXEC | CODE |
|:--|:--|--:|:--|--:|:--|:--:|:--:|
| `.text`   | `0x00001000` | 4,060,045 | `0x00001000` | 4,063,232 | `0x60000020` | ✔ | ✔ |
| `.rdata`  | `0x003E1000` |   196,724 | `0x003E1000` |   200,704 | `0x40000040` | ✘ | ✘ |
| `.data`   | `0x00412000` | 3,570,660 | `0x00412000` |   442,368 | `0xC0000040` | ✘ | ✘ |
| `.rsrc`   | `0x0077A000` |    98,600 | `0x0047E000` |   102,400 | `0x40000040` | ✘ | ✘ |
| `.detour` | `0x00793000` |    10,008 | `0x00497000` |    12,288 | `0xC0000040` | ✘ | ✘ |

- **`[本次实测]`** `.text` 的 `0x60000020` = MEM_EXECUTE \| MEM_READ \| CNT_CODE ⇒ 唯一按 PE 头声明可执行/含代码的节。
- **`[本次实测]`** `.detour` 的 `0xC0000040` = MEM_READ \| MEM_WRITE \| CNT_INITIALIZED_DATA，
  **未置 MEM_EXECUTE、未置 CNT_CODE**。旧报告 `STATIC_FRAME_SEMANTICS.md:14,98-101` 把它称作「Detours 代码段」并据此讨论「帧号不由 Detours 代码维护」——
  这个命名在静态节表上**没有依据**。本轮仍按名字把 `.detour` 作为**保守额外扫描对象**纳入线性扫描（`EVIDENCE/scan_stdout.txt` 中 `[.detour] linear sweep: 5691 instructions`），
  结果 0 处 `0xA8ED84` 引用；若运行期用 `VirtualProtect` 改其保护属性，静态不可见 ⇒ `[待运行验证]`。
- **`[本次实测]`** `.data` 的 `vsize=3,570,660` 远大于 `rawsize=442,368`，`.text` 的 `vsize=4,060,045` 小于 `rawsize=4,063,232`；
  这影响 VA↔文件偏移映射，本脚本一律用 `rawptr/rawsize` 做磁盘映射、用 `rva/vsize` 做 VA 计算，未混用。
  **`[本次实测]`** `0xA8ED84` → RVA `0x68ED84`；
  `.data` 虚拟范围 `0x00412000 .. 0x00779BE4`（`0x412000 + 0x367BE4`），故该地址落在 `.data` 的**虚拟**范围内，
  节内偏移 `0x27CD84` = 2,608,516 B，**远超 `.data` 的 rawsize 442,368 B** ⇒
  磁盘上没有对应的 4 字节初值可读，其初值由加载器零填充 / 运行期赋值，**本轮不给初值结论**。

## 3 · 从实际运行栈地址反推该次运行的实际基址

`[转引]` 原始数字来自 `lead/re_d13_ruling_20261112/_hl_match_14412.json`（pid 14412，tid 30668，`t=471.266`，`frame=15042`，`n_samples=3493`）。
本轮**未启动游戏、未采集活进程**，只对该既有记录做复算。

**`[本次实测-对既有记录的复算]`** 命令：

```powershell
python "D:\Project\ra2-campaign-forge\lead\next_re_20261112\RE-N02\_frame_semantics_v2.py"
```

原始输出（`EVIDENCE/BASE_RECOMPUTE.txt`，退出码 0）：

```
name=gamemd.exe+0x207f17  addr=6323991 (0x00607F17)  rva=0x207F17  => addr-rva=4194304 (0x00400000)
name=gamemd.exe+0x20833f  addr=6325055 (0x0060833F)  rva=0x20833F  => addr-rva=4194304 (0x00400000)
PE ImageBase = 0x00400000 (4194304)
all recomputed bases == ImageBase : True
ASLR/DYNAMICBASE flag = False ; relocation directory present = False
```

实算：

```
6323991 − 0x207F17 = 6323991 − 2129687 = 4194304 = 0x00400000
6325055 − 0x20833F = 6325055 − 2130751 = 4194304 = 0x00400000
```

**结论 `[本次实测-对既有记录的复算]`**：两条栈帧独立复算都等于 ImageBase `0x00400000`，
且 PE 头无 DYNAMICBASE、无重定位目录 ⇒ **该次已记录的运行，模块基址 == ImageBase，未发生重定位**。
`docs/re/NEXT_RE_TASKS_20261112.md:191-193` 用 ImageBase `0x400000` 换算 `0x607F17` / `0x60833F` 在本镜像与该次运行下**成立**。

**关键的循环性核查（必须写清）** `[本次读码]`：
`lead/re_d13_ruling_20261112/e3_stackwalker.py:140` 用 `Module32First/Next` 的 `me.modBaseAddr` 取得**运行期模块基址**，
`:151` 用 `"%s+0x%x" % (name, addr - base)` 生成 `gamemd.exe+0x…`。
所以 `addr − rva` 恢复的是**那一次运行的活模块基址**，不是从磁盘 PE 头 `0x400000` 反推出来的同义反复 ⇒ 复算有信息量。
**但**：这只证明**这一条已记录的运行**；不能推广到「所有运行都不重定位」，也不能替代对该次运行模块指纹的现场核对。
原始数值本身是 `[转引]`，本轮没有独立采集。

## 4 · 线性扫描覆盖范围与未覆盖区间

**`[本次实测]`** 确定性线性扫描（capstone 5.0.7，`detail=True, skipdata=True`，从节起点开始，
下一条边界 = 上一条边界 + 该指令长度，不猜起点）：

| 节 | 指令数 | skipdata 字节 | 未覆盖区间数 | 起始 VA |
|:--|--:|--:|--:|:--|
| `.text` | 1,394,186 | 66 | 64 | `0x00401000` |
| `.detour` | 5,691 | 6 | 6 | `0x00B93000` |

未覆盖 RVA 区间逐条列在 `EVIDENCE/UNCOVERED_INTERVALS.txt`（格式 `section rva_start rva_end length va_start va_end`），
例如 `.text RVA 0x0006F5A0..0x0006F5A1`、`0x00308D58..0x00308D5A`。这些是**无法解码字节**，
不是「已确认无引用」。第二可信边界复扫见 `EVIDENCE/RESYNC_VERIFICATION.txt`：
10 个写点全部在 4 个独立种子复扫中命中同一指令起点。

**边界保证的诚实限度** `[静态推断]`：线性扫描在「数据混排在代码里但每个字节都能解出合法指令」时可能静默漂移。
本轮的缓释是：① 双通道交叉验证（1009/1009 原始命中全部被操作数级分类解释）；
② prologue + 直接分支目标作第二边界源，在写点邻域复扫；③ 未覆盖区间如实列出。
**这不是完整 CFG/递归下降**，不宣称所有指令边界都正确。

## 5 · 复现命令

```powershell
python "D:\Project\ra2-campaign-forge\lead\next_re_20261112\RE-N02\_frame_semantics_v2.py"            # 全量扫描，exit 0
python "D:\Project\ra2-campaign-forge\lead\next_re_20261112\RE-N02\_frame_semantics_v2.py" --selftest  # 负控五样例，exit 0
```

环境 `[本次实测]`：Python 3.12.10、capstone 5.0.7、pefile 2024.8.26（`python -c "import sys,capstone,pefile;..."` 退出码 0）。

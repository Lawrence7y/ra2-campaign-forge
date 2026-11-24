# R37-T1 · 判定 `0x7E11C8` 是不是 `InterlockedIncrement`

镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
sha256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（已实测匹配）
Machine = `0x014C` (I386)，Magic = `0x10B` (PE32)，ImageBase = `0x400000`

## 结论五行

```
Q1 | 结论：IAT槽 | 依据：RVA=0x003E11C8 节=.rdata(节内偏移0x1C8, 文件偏移0x3E11C8) 所属DLL=KERNEL32.dll FirstThunk项偏移=0xF8(KERNEL32 FirstThunk RVA=0x003E10D0 起第62项)
Q2 | 导入名：InterlockedIncrement | 依据：槽值=0x007941F0 → INT条目0x00793248(文件偏移0x497248)=F0 41 79 00 → IMAGE_IMPORT_BY_NAME@0x007941F0(文件偏移0x4981F0) 原始字节 B0 01 49 6E 74 65 72 6C 6F 63 6B 65 64 49 6E 63 72 65 6D 65 6E 74 00 (Hint=432)，字符串逐字为 "InterlockedIncrement"
Q3 | ①已证实 | KERNEL32.dll 的 `InterlockedIncrement`（Hint=432）按名字导入，槽位于 FirstThunk idx=62；`§13.3` 对该槽的称谓有字节支撑
Q4 | 正控槽 0x7E11CC 解出名字 = InterlockedDecrement（KERNEL32 idx=63，Hint=429，IBN@0x00794208/off 0x498208，原始字节 AD 01 49 6E 74 65 72 6C 6F 63 6B 65 64 44 65 63 72 65 6D 65 6E 74 00）；另 0x7E1394=DefWindowProcA、0x7E1080=GetBkColor、0x7E1000=RegQueryInfoKeyA 同样解出 ⇒ 解析器可信
OVERALL | 可以升级为已证实：0x7E11C8 导入名逐字为 "InterlockedIncrement"，但须同时保留「镜像已被修改过」这一限定（见下方「附带观察」）
```

## Q1 · `0x7E11C8` 是什么

**PE 导入表定位**

| 项 | RVA | 文件偏移 |
|---|---|---|
| DataDirectory[1] IMPORT | `0x007955C0` | `0x4995C0` |
| KERNEL32 IMAGE_IMPORT_DESCRIPTOR | `0x007955D4` | `0x4995D4` |
| KERNEL32 OriginalFirstThunk (ILT) | `0x00793150` | `0x497150` |
| KERNEL32 FirstThunk (IAT) | `0x003E10D0` | `0x3E10D0` |
| KERNEL32 Name | `0x00793D70` | `0x493D70`（= "KERNEL32.dll"）|

描述符原始 20 字节 @off `0x4995D4`：

```
50 31 79 00 | 00 00 00 00 | 00 00 00 00 | 70 3D 79 00 | D0 10 3E 00
OFT=0x793150  TimeDateStamp=0       FC=0        NameRVA=0x793D70  FirstThunk=0x3E10D0
```

**目标地址换算（目标 VA `0x7E11C8`）**

- RVA = `0x007E11C8 − 0x00400000` = `0x003E11C8`
- 所属节 `.rdata`（`VA=0x003E1000, VSize=0x00030074, RawPtr=0x003E1000`），节内偏移 `0x1C8`
- 文件偏移 = `0x003E11C8 − 0x003E1000 + 0x003E1000` = `0x3E11C8`（此节 RVA 与文件偏移数值相同）
- FirstThunk 项序号 = `(0x003E11C8 − 0x003E10D0) / 4` = `0xF8 / 4` = **62**

**该处原始字节** @off `0x3E11C8`（16 字节）：

```
90 F9 40 00  78 F9 40 00  62 F9 40 00  48 F9 40 00
```

前 4 字节即该槽值 `0x0040F990`（加载器已绑定到 thunk 存根），不是 `0x007941F0`，符合 IAT 已重定位的形态。

⇒ 结论：这是一个 **IAT 槽**（归属 `KERNEL32.dll`，FirstThunk 起始 `0x003E10D0` 的第 62 项，槽项偏移 `0xF8`）。不是普通的「函数指针表项」，也不是普通数据。

## Q2 · 导入的是哪个函数名

字节链路（每一跳都给出原始字节）：

1. IAT 槽 @RVA `0x003E11C8` / off `0x3E11C8`：`90 F9 40 00` → 加载前该位置存放的是 ILT 指针。
2. ILT 对应条目 idx=62：RVA = `0x00793150 + 62*4` = `0x00793248`，off = `0x497248`（`.detour` 节，RVA→off 差 `0x2FC000`）
   原始字节：`F0 41 79 00` → **`0x007941F0`**。最高位为 0 ⇒ **按名字导入**，不是 Ordinal。
3. `IMAGE_IMPORT_BY_NAME` @RVA `0x007941F0` / 文件偏移 `0x4981F0`（`.detour` 节）
   原始字节：`B0 01 49 6E 74 65 72 6C 6F 63 6B 65 64 49 6E 63 72 65 6D 65 6E 74 00`
   - `B0 01` = Hint **432** (`0x1B0`)
   - 其后 ASCII：`49 6E 74 65 72 6C 6F 63 6B 65 64 49 6E 63 72 65 6D 65 6E 74` = **`InterlockedIncrement`**
   - `00` = 终止符

**逐字字符串：`InterlockedIncrement`**（19 字符，未加 `@4`/`_` 等 MSVC 修饰，PE 导入名本来就不带修饰）。

## Q3 · 三选一

**① 已证实。**

`0x7E11C8` 是 `KERNEL32.dll!InterlockedIncrement` 的 IAT 槽（Hint=432，按名字导入）。`R14_COMMON §13.3` 称该槽为 `InterlockedIncrement`，有字节支撑。

补充核对（只读，用于说明该槽在 `§13.3` 所述代码里确实被这么用；**不据此判函数入口**）：
`0x006C2AC0`（`.text`，off `0x2C2AC0`）起始 18 字节为

```
8B 44 24 04 83 C0 04 50 FF 15 C8 11 7E 00 C2 04 00
```

即 `mov eax,[esp+4]` / `add eax,4` / `push eax` / `call dword ptr [0x007E11C8]` / `ret 4`——`FF 15 C8 11 7E 00` 中的 `0x007E11C8` 与 Q1/Q2 解析的槽是同一地址。`§13.3` 对该片段用到的槽描述正确。

## Q4 · 正控

| 正控槽 | 解出名字 | DLL / idx | Hint | IBN RVA / off | 原始字节 |
|---|---|---|---|---|---|
| `0x7E11CC` | `InterlockedDecrement` | KERNEL32 / 63 | 429 | `0x00794208` / `0x498208` | `AD 01 49 6E 74 65 72 6C 6F 63 6B 65 64 44 65 63 72 65 6D 65 6E 74 00` |
| `0x7E1394` | `DefWindowProcA` | USER32 / 0 | 132 | `0x00794900` / `0x498900` | `84 00 44 65 66 57 69 6E 64 6F 77 50 72 6F 63 41 00` |
| `0x7E1080` | `GetBkColor` | GDI32 / 10 | 263 | `0x0079500A` / `0x49900A` | `07 01 47 65 74 42 6B 43 6F 6C 6F 72 00` |
| `0x7E1000` | `RegQueryInfoKeyA` | ADVAPI32 / 0 | 374 | `0x007950D4` / `0x4990D4` | `76 01 52 65 67 51 75 65 72 79 49 6E 66 6F 4B 65 79 41 00` |

为什么认为这些「已知」：

- `0x7E11CC` 紧随 `0x7E11C8`，且 `KERNEL32` 的 ILT 名字区在 `0x4981F0` 附近连续排布为 `...|InterlockedIncrement|InterlockedDecrement|GetCurrentThreadId|...`（切片 off `0x4981E0..0x498230` 读出 `iByteToWideChar│InterlockedIncrement│InterlockedDecrement││GetCurrentThre...`），两条相邻指针 `0x007941F0`/`0x00794208` 与 ILT 索引 62/63 严格同序，自洽。
- `0x7E1394`（USER32 idx=0）、`0x7E1080`（GDI32 idx=10）、`0x7E1000`（ADVAPI32 idx=0）都是各家 DLL 的常见导出，名字与 Hint 合理；`DefWindowProcA`/`RegQueryInfoKeyA`/`GetBkColor` 属于无歧义的 Win32 API，能反证解析器没有错位。
- 负控：`0x7E2000`（同在 `.rdata`、off `0x3E2000`，原始字节 `60 02 41 00 00 03 41 00 ...`）不在任何 `FirstThunk` 区间内，解析器正确返回「不属于任何 FirstThunk 槽（不是 IAT 项）」，说明它不是无脑给地址赋名字。

⇒ **解析器可信。**

## 附带观察（供 lead 判断，不属于 Q1–Q4 结论）

Q1 第 2 步发现一处与「原始未修改镜像」不符的迹象，需明确记录：

- `KERNEL32` 的 `FirstThunk = 0x003E10D0` 落在 `.rdata`，位于 `0x003E1000..0x003E10D4` 之间（被 ADVAPI32 的 9 项 + 其它 DLL 的槽穿插），且
- IAT 槽值形如 `0x0040F9xx` / `0x00410xxx`，落在 `.rdata` 内部（`0x0040F990` 处字节 `DD 05 18 17 7E 00 ...`，`0x004107F6` 处 `77 88 00 C3 90 90`），而非 `.text` 真实现。
- 描述符 `TimeDateStamp = 0`（正常应按 DLL 时间戳；0 表示无绑定）。
- 节表存在自定义 `.detour` 节（`VA=0x00793000, RawPtr=0x00497000`），该节被用作 ILT 与名字区的落点。

⇒ 本镜像的 IAT 布局是**被改造过/预绑定过的**形态，`.detour` 节疑似后加。这不影响 Q1–Q4（导入名字符串是**明文**存在文件里的，可直接逐字读出），但如果后续有人想「从 IAT 槽值反推真实函数体地址」，在本镜像上会得到 `.rdata` 内的假地址，不可用。

## 复算脚本

| 文件 | 作用 |
|---|---|
| `iat_resolve.py` | 通用 PE 解析器：读 DOS/NT 头、节表、`DataDirectory[1]`、全部 16 个 `IMAGE_IMPORT_DESCRIPTOR`，枚举全部 372 个 FirstThunk 槽，并对给定 VA 做完整回溯 |
| `crosscheck_raw.py` | **独立复算**：不复用上面的任何代码，写死 `.rdata`/`.detour` 的 RVA→off 线性映射与描述符地址，手工算 idx、读 ILT、读 IBN |
| `run_out.txt` | `iat_resolve.py 0x7E11C8 0x7E11CC` 的完整输出（含 16 个 DLL 描述符表 + 全部 372 槽清单 + 两次查询） |
| `run2_out.txt` | `iat_resolve.py 0x7E1080 0x7E1000 0x7E1394` 追加正控输出 |
| `crosscheck_out.txt` | `crosscheck_raw.py` 输出 |

重跑命令（UTF-8 输出）：

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R68_T1_IAT
$env:PYTHONIOENCODING='utf-8'
python iat_resolve.py 0x7E11C8 0x7E11CC  > run_out.txt
python iat_resolve.py 0x7E1080 0x7E1000 0x7E1394 > run2_out.txt
python crosscheck_raw.py > crosscheck_out.txt
```

最小手工复算（不跑脚本，直接看 hex）：

- 打开 `gamemd.exe`，跳到文件偏移 `0x4995D4`，读 20 字节，确认 `FirstThunk=0x003E10D0`。
- 跳到文件偏移 `0x3E11C8`，读 16 字节 → `90 F9 40 00 ...`（第 62 个槽，`(0x3E11C8-0x3E10D0)/4=62`）。
- 跳到文件偏移 `0x497248`（= ILT RVA `0x00793150 + 62*4` 换算），读 4 字节 → `F0 41 79 00` → `0x007941F0`。
- 跳到文件偏移 `0x4981F0`，读 24 字节 → `B0 01` + `InterlockedIncrement` + `00`。

纪律声明：

- 全程只读 `gamemd.exe`；未修改 `R14_COMMON.md` / `LEAD_LOCK` / `GOAL_THREE_TARGETS_20261018.md` / `STATUS_BOARD.md` / `BOARD_ARCHIVE.md` / 任何 `FACT_INDEX.tsv`。
- 未使用「按字节扫 `E8`/`C3`/`C2`」作为任何函数入口判据；`0x006C2AC0` 处字节仅为核对 `§13.3` 引用的 `FF 15` 绝对间接调用操作数地址，未据此认定它是函数入口。
- 所有产物只写在本目录 `lead\next_re_20261117_r14\R17_R68_T1_IAT`。

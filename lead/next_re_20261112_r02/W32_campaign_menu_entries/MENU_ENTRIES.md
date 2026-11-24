# W32 · `GUI:CampaignMenu` 为什么只有两颗徽章、追加 battle id 不生成条目

> 卡号 **W32**（静态分析卡）｜轮次 `NEXT_RE_20261112_R02`｜交付目录 `lead/next_re_20261112_r02/W32_campaign_menu_entries/`
> 纪律：**纯离线静态只读**。未启动 `gamemd.exe`、未 attach / 读活进程 / 注入、未写 `ra2youli`、未写仓库 `ra2forge/`、无 git 写操作、未改动 W21–W31 任何目录。
> 工具：Python 3.12 + `pefile` 2024.8.26 + `capstone` 5.0.7；脚本与完整 stdout / exit code 见 `EVIDENCE/`。
> 所有结论标等级：`[本次实测]`（文件字节断言/结构体解析）/ `[本次读码]`（反汇编语义）/ `[静态推断]` / `[转引]` / `[待运行验证]`。

---

## 0 · 一句话定谳（两种结论完全相反，分别给证据）

| 目标 | 结论 | 等级 | 依据 |
|---|---|---|---|
| **可见徽章区出现第 3 颗徽章 / 第 3 个战役条目** | **`结构上不可能`（不改 exe）** | `[本次实测]`+`[本次读码]` | Win32 对话框模板 `RT_DIALOG id=148` 固定 13 控件，其中**只有 2 个徽章 Static**（1770/1772）；WndProc `0x52EC00` 的徽章分派只有 3 个硬编码立即数 `0x6EA/0x6EC/0x6EB`；三个槽位各自绑死 `.data` 中的 `"all1"/"sov1"/"tut1"`；`Battle` 表名字查找 `0x46CC90` 全镜像**仅 1 个调用点**（0x52F260，徽章点击）。**没有任何按 Battle 表生成徽章的循环**。 |
| **追加 battle id 出现在隐藏 `ListBox`(1109) 里** | **`有条件可达`** | `[本次实测]`+`[静态推断]` | `0x52F018..0x52F048` 是一个**无过滤**遍历 `0..Count-1` 的循环，把 `Items[i]+0x2A0`（Description）逐条塞进列表；但整段被**一个字节** `[0xA8F7AD]` 门控。该字节为 0 时列表被 `ShowWindow(SW_HIDE)` 且从不填充。W27 实测 `LB_GETCOUNT=0` 正是这个分支。 |

> ⚠️ **不要含糊**：「追加 id 不生成条目」对**可见徽章**成立（结构上不可能），对**隐藏调试列表**不成立（门控关时才不生成）。二者共用同一个 `GUI:CampaignMenu`，但走的是两条完全不同、互不派生的路径。

---

## 1 · 前提复核（本次逐字节重算）

`[本次实测]` `EVIDENCE/verify_stdout.txt` §0、`EVIDENCE/recon1_stdout.txt`：

| 项 | 值 |
|---|---|
| 文件 | `ra2bench/gamemd.exe`，4,825,360 B |
| SHA-256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` ✅ |
| `ImageBase` | `0x400000`；`Characteristics=0x32F`（`RELOCS_STRIPPED=True`）✅ |
| 段 | `.text` RVA=FOFF=`0x1000`（**故 `.text` 内 FOFF = VA − 0x400000 = RVA**）；`.rdata` 0x3E1000/0x3E1000；`.data` 0x412000/0x412000（VirtualSize `0x367BE4` ≫ RawSize `0x6C000`，**高地址是 BSS**）；`.rsrc` RVA `0x77A000` / FOFF `0x47E000`（**FOFF = RVA − 0x2FC000**）；`.detour` 0x793000/0x497000 |

**地址口径声明**：本报告写的 `0x52EC00`、`0x46CE10`、`0x825C68`、`0xA83CF8`、`0xA8F7AD` 全部是 **VA**；RVA = VA − `0x400000`；`.text` 内 FOFF = RVA。`0xA83CF8`/`0xA83CFC`/`0xA83D08` 与 `0xA8F7AD` 位于 `.data`（前者在 raw，后者在 BSS）。`gamemd.exe+0xNNNNNN` 形式一律按 RVA 理解。

**关键函数复核**（与 W29 一致）`[本次实测]`：
- `CCFileClass::Get_File = 0x473D10`、`MixFileClass::Find = 0x5B4430`、`LoadBattleMdIni = 0x52CB90`（`0x52DF25` 调用）、`Register_Battles = 0x46CE10`（`0x52CC67` / `0x52CD2C` 调用）、`Battle::Read_INI = 0x46CCD0`。
- Battle 表：`0xA83CF8` = `VectorClass` 对象（vtable 指针），`0xA83CFC` = Items 指针数组，`0xA83D08` = Count；元素 `0x3A0` B，名字 `+0x24`，CD `+0x98`，Scenario `+0x9C`（0x200 B 缓冲），FinalMovie `+0x29C`，Description `+0x2A0`。

---

## 2 · 判定链

### 2.1 菜单不是「代码生成条目」，而是一张固定对话框模板 `[本次实测]`

`GUI:CampaignMenu` 的 ASCII 字面量在镜像里 **0 命中**，UTF-16LE 命中在 `.rsrc`：`FOFF=0x487410` → **VA `0xB83410`**（`recon1_stdout.txt`）。用 Win32 `DIALOGEX` 解析器逐项解析（`EVIDENCE/parse_dialog.py`、`verify.py` §1）：

```
RT_DIALOG id=148 (0x94), RVA=0x783270, FOFF=0x487270, VA=0xB83270
  01 00 FF FF                       dlgVer=1, signature=0xFFFF  (DIALOGEX)
  style=0x40000040  cDlgItems=13   rect=(0,0,533,369)  font "MS Sans Serif" 8
```

13 个控件（`id / class / text`）：

| # | id | hex | class | 文本 / 说明 |
|---|---|---|---|---|
| 0 | **1109** | 0x455 | ListBox (ord 131) | 右侧隐藏列表，rect (421,151,107,98)，style `0x50000151` |
| 1 | 1038 | 0x40E | Button | `GUI:Load`（隐藏） |
| 2 | 1295 | 0x50F | msctls_trackbar32 | `Slider3` |
| 3 | 1822 | 0x71E | Static | `GUI:Difficulty` |
| 4 | 1648 | 0x670 | Static | `GUI:Harder` |
| 5 | 1670 | 0x686 | Button | `GUI:Back` |
| 6 | **1684** | 0x694 | Static | `GUI:CampaignMenu`（= 卡面给的控件 id） |
| 7 | **1770** | 0x6EA | Static, ex=0x20 | **徽章 1**（无文本，rect (125,34,174,87)） |
| 8 | **1772** | 0x6EC | Static, ex=0x20 | **徽章 2**（无文本，rect (125,216,173,86)） |
| 9 | 1685 | 0x695 | Static | `GUI:Blank` |
| 10 | 1820 | 0x71C | Static, ex=0x20 | 无文本（rect (449,29,61,33)） |
| 11 | 1959 | 0x7A7 | Static | 无文本（rect (4,123,415,13)） |
| 12 | 1960 | 0x7A8 | Static | 无文本（rect (3,304,420,13)） |

- **恰好 5 个空文本 Static**（1770/1772/1820/1959/1960）→ 与 W27 真机「5 个空文字 Static，含两个徽章」**逐项吻合** `[转引 W27 §3]`。
- **模板中没有 id 1771 (`0x6EB`)**，但 WndProc 里保留了对它的处理分支（`0x52EE78` / `0x52F252`）→ 第三个「Boot Camp」槽位是**残留代码**，出厂模板已删控件。这正是「只有两颗徽章」的结构原因。
- `cDlgItems=13` 是模板常量；`0x622650` 用 `CreateDialogIndirectParamA`（`[0x7E1450]`）从该资源一次性建窗，**运行时没有逐个 `CreateWindow` 生成徽章**。

### 2.2 对话框创建与 WndProc `[本次实测]`+`[本次读码]`

```
0x52DF48  BA 00 EC 52 00     mov edx, 0x52EC00      ; WndProc
0x52DF4D  B9 94 00 00 00     mov ecx, 0x94          ; MAKEINTRESOURCE(148)
0x52DF53  89 1D A0 F7 A8 00  mov [0xA8F7A0], ebx    ; 清 0
0x52DF5F  89 1D A8 F7 A8 00  mov [0xA8F7A8], ebx    ; 清 0
0x52DF65  E8 E6 46 0F 00     call 0x622650          ; CreateDialogIndirectParamA 包装
```

`0x52EC00` 是 `CampaignMenu` 的 WndProc（`sub esp,0x10` … `ret 0x10`）。`0x622650` 内部 `0x6226CB: FF 15 50 14 7E 00` = `call [0x7E1450] = CreateDialogIndirectParamA` `[本次读码]`。

IAT 已由 `pefile.DIRECTORY_ENTRY_IMPORT` 独立解析（`recon3_stdout.txt` / `recon7_stdout.txt`）：`[0x7E1490]=SendDlgItemMessageA`、`[0x7E1498]=ShowWindow`、`[0x7E14A0]=EnableWindow`、`[0x7E14A4]=SendMessageA`、`[0x7E14A8]=GetDlgItem`、`[0x7E1470]=SetWindowLongA`、`[0x7E1474]=GetWindowLongA`、`[0x7E1450]=CreateDialogIndirectParamA`、`[0x7E13D4]=DialogBoxParamA`。

### 2.3 可见徽章：硬编码 3 个立即数 + 3 个 `.data` 字符串 `[本次实测]`

WndProc 的 hover / click 分派只有三条 `cmp`：

| VA | 字节 | 反汇编 | 槽位 |
|---|---|---|---|
| `0x52EE04` | `81 FB EA 06 00 00` | `cmp ebx, 0x6EA` | Allied |
| `0x52EE3F` | `81 FB EC 06 00 00` | `cmp ebx, 0x6EC` | Soviet |
| `0x52EE78` | `81 FB EB 06 00 00` | `cmp ebx, 0x6EB` | BootCamp（模板无此控件） |
| `0x52EF39/40/47` | `3D EA/EC/EB 06 00 00` | `cmp eax, 0x6EA/0x6EC/0x6EB` | WM_LBUTTONUP 命中判定 |
| `0x52F232/242/252` | `81 FD EA/EC/EB 06 00 00` | `cmp ebp, 0x6EA/0x6EC/0x6EB` | 点击分派 |

点击后取 `.data` 里三个静态指针并调用 `0x46CC90`（Battle 表按名字查索引）：

```
0x52F23A  8B 0D 68 5C 82 00   mov ecx, [0x825C68]   ; -> 0x825CA0 "all1"
0x52F24A  8B 0D 6C 5C 82 00   mov ecx, [0x825C6C]   ; -> 0x825C98 "sov1"
0x52F25A  8B 0D 70 5C 82 00   mov ecx, [0x825C70]   ; -> 0x825C90 "tut1"
0x52F260  E8 2B DA F3 FF       call 0x46CC90
```

`.data` 原始字节（`FOFF=0x425C90` / `0x425C98` / `0x425CA0`）：

```
0x825C90  74 75 74 31 00   "tut1"      0x825C70 = 0x825C90
0x825C98  73 6F 76 31 00   "sov1"      0x825C6C = 0x825C98
0x825CA0  61 6C 6C 31 00   "all1"      0x825C68 = 0x825CA0
```

`[本次实测]` 全文件扫描：**这三个全局（`0x825C68/6C/70`）没有任何绝对地址写入**，它们是 `.data` 静态初值；`0x52E19A/0x52E233/0x52E372` 的「xref」只是 `cmp eax, 0x825C68` 循环上界（清 4 个 `0x10` 步长字符串，范围 `0x825C28..0x825C68`，**不含** 68/6C/70）。

`0x46CC90` = `Battle::Find_Index_By_Name`：

```
0x46CC90  A1 08 3D A8 00     mov eax, [0xA83D08]        ; Count
0x46CC9F  A1 FC 3C A8 00     mov eax, [0xA83CFC]        ; Items
0x46CCA5  8B 04 B0           mov eax, [eax + esi*4]
0x46CCA8  83 C0 24           add eax, 0x24              ; 名字
0x46CCAC  E8 6F C0 35 00     call 0x7C8D20              ; _stricmp
0x46CCB4  85 C0              test eax,eax
0x46CCBE  3B F0              cmp esi, eax
0x46CCC0  7C DD              jl 0x46CC9F
```

`[本次实测]` rel32 调用点全镜像扫描：`0x46CC90` **只有 1 个调用点 = `0x52F260`（徽章点击）**。⇒ Battle 表在 `CampaignMenu` 里**只被徽章点击按名字查一次索引**，从不用来生成徽章。

### 2.4 隐藏 ListBox 1109：无过滤遍历整张 Battle 表，但被一个字节门控 `[本次实测]`

WndProc 的初始化分支（自定义消息 `0x497`）在 `0x52EFCE`；`0x52EFFC` 取 `GetDlgItem(hDlg, 1109)`，然后：

```
0x52F00B  A0 AD F7 A8 00      mov al, byte ptr [0xA8F7AD]   ; ★ 唯一门控
0x52F010  84 C0               test al, al
0x52F012  74 48               je  0x52F05C                  ; 0 -> 隐藏列表 + 隐藏/禁用 GUI:Load
0x52F014  85 ED               test ebp, ebp                 ; ListBox HWND 非空
0x52F016  74 67               je  0x52F07F
; ---- 遍历 0..Count-1，无任何字段过滤 ----
0x52F018  A1 08 3D A8 00      mov eax, [0xA83D08]           ; Count
0x52F01D  33 FF               xor edi, edi                  ; i = 0
0x52F01F  85 C0               test eax, eax
0x52F021  7E 27               jle 0x52F04A
0x52F023  A1 FC 3C A8 00      mov eax, [0xA83CFC]           ; Items
0x52F028  8B 0C B8            mov ecx, [eax + edi*4]        ; Items[i]
0x52F02B  81 C1 A0 02 00 00   add ecx, 0x2A0                ; +0x2A0 = Description
0x52F031  51                  push ecx                      ; lParam = 条目文本
0x52F032  6A 00               push 0
0x52F034  68 CD 04 00 00      push 0x4CD                    ; WM_USER 段私有「加条目」消息
0x52F039  55                  push ebp                      ; hWnd = ListBox
0x52F03A  FF 15 A4 14 7E 00   call [0x7E14A4]               ; SendMessageA
0x52F040  A1 08 3D A8 00      mov eax, [0xA83D08]
0x52F045  47                  inc edi
0x52F046  3B F8               cmp edi, eax
0x52F048  7C D9               jl 0x52F023
0x52F04A  6A 00 / 6A 00 / 68 86 01 00 00 / 55 / FF 15 A4 14 7E 00
                                                        ; SendMessageA(list, 0x186 LB_SETCURSEL, 0, 0)
; ---- 门控 == 0 的分支 ----
0x52F05C  6A 00 / 55 / 8B 2D 98 14 7E 00 / FF D5   ; ShowWindow(list, SW_HIDE)
0x52F067  68 0E 04 00 00                            ; GetDlgItem(0x40E GUI:Load)
0x52F079  FF 15 A0 14 7E 00                         ; EnableWindow(hBtn, FALSE)
```

`[本次实测]` `verify.py` §5 断言：循环体内**没有任何对 battle 字段的 `cmp`/`test`**，只有 `test eax,eax`（Count）、`cmp edi,eax` / `jl`（循环上界）。`[本次读码]` 全 WndProc（`0x52EC00..0x52F3E5`）只读 `0xA83D08`、`0xA83CFC`、`+0x2A0`；**从未读 `+0x98`(CD) / `+0x9C`(Scenario) / `+0x29C`(FinalMovie)**（`wndproc_full_disasm.txt` 全文 grep 复核）。

⇒ **追加 battle id 只要已并入全局表，就会成为 ListBox 的第 `Count-1` 项，与 id 形式 / CD / FinalMovie / Scenario 是否可在 MIX 找到 / 数值区间全都无关。**

**Debug 语义佐证** `[本次实测]`+`[转引]`：
- `ra2bench/BATTLEMD.INI` 官方注释：「everything below this line should be removed before the game ships. These are temporary campaigns to assist us in debugging」「`DebugOnly = this campaign is not for final release`」；14 个官方条目中 12 个带 `DebugOnly=yes`。
- `0x81B1B0 = "DebugOnly"`、`0x81B18C = " - for debug/testing"`；`0x46CD58` 读该键，`0x46CD65 jne 0x46CD8F` 时把后缀拼到 Description 后（`0x46CDA8`–`0x46CDDC`），再 `0x46CDE2 call 0x735060` 处理 `[battle+0x2A0]`。`[本次读码]` ⇒ `DebugOnly` 只改**条目显示文本**，不改是否入表。
- `0x835630 = "STT:CampaignList"`、`0x835644 = "STT:CampaignButtonLoad"`、`0x835618 = "STT:CampaignButtonBack"`、`0x83565C = "STT:CampaignSliderDifficulty"` ⇒ 这张表/按钮在游戏的字符串表里本来就有名字。

### 2.5 `GUI:Load` 把 ListBox 选中索引当作 Battle 表索引返回 `[本次实测]`+`[本次读码]`

```
0x52ECB8  3D 0E 04 00 00      cmp eax, 0x40E           ; WM_COMMAND: GUI:Load
0x52ED15  68 55 04 00 00      push 0x455               ; GetDlgItem(1109)
0x52ED25  68 88 01 00 00      push 0x188               ; LB_GETCURSEL
0x52ED2D  89 07               mov [edi], eax           ; DWL_USER 结构首 dword = 选中索引
0x52ED2F  C6 47 04 01         mov byte [edi+4], 1      ; done 标志
...
0x52E08E  8B 44 24 14         mov eax, [esp+0x14]      ; 对话框返回结构
0x52E092  8B 0D 30 B2 A8 00   mov ecx, [0xA8B230]
0x52E098  89 81 CC 34 00 00   mov [ecx+0x34CC], eax    ; 作为战役索引落到 Session
```

徽章点击分支（`0x52F260`）同样把 `0x46CC90(name)` 的返回值写进 `DWL_USER` 首 dword（`0x52F265: 89 07`）。⇒ **两条路径返回的是同一种量：Battle 表索引**；ListBox 第 i 项 ⇔ `Items[i]`。

### 2.6 与 W29 的并表链闭环 `[转引 W29]`+`[本次实测]`

`0x52DF25 call 0x52CB90`（`LoadBattleMdIni`，`FindFirstFileA("BATTLEMD*.INI")`）→ `0x46CE10`（`Register_Battles`，`push 0x81B1D8 "Battles"`、按条目名 `_stricmp` 合并到 `0xA83CFC`，Count `0xA83D08`）→ `0x46CCD0`（`Battle::Read_INI`，读 `CD`/`FinalMovie`/`Scenario`/`DebugOnly`/`Description`）。W27 真机 `Count=15`、`RA2F1` 对象含 `CD=2 / ECH01.MAP` `[转引 W27 §3]` 与本静态链一致。

---

## 3 · 逐条回答核心任务

### Q1 定位绘制两颗徽章 / 生成两个条目的代码

`[本次实测]`
- **控件来源**：`RT_DIALOG id=148`（`RVA 0x783270` / `FOFF 0x487270` / `VA 0xB83270`）里两个 Static（**1770 `0x6EA`、1772 `0x6EC`**，`exStyle=0x20`，`style=0x50000007`），由 `0x622650` → `CreateDialogIndirectParamA` 一次性创建。
- **贴图/动画引用**：`0x52EFCE` 初始化时用 `0x7514D0` 查 `0x826408 "SovietCampaignSelect"`、`0x8263F0 "AlliedCampaignSelect"`、`0x8263E0 "BootCampSelect"`，结果存 `0x825C74/78/7C`；hover 时按徽章 id 把其中之一写入 `0x825C20` 并播放（`0x52EE14/0x52EE4F/0x52EE88`）。文字用 `0x8263B0 "STT:SovietCampaignIcon"` / `0x8263C8 "STT:AlliedCampaignIcon"`（经 `0x734E60` 取 CSF，`0x52F09E` / `0x52F0D1`）。
- **绘制/高亮消息**：`SendDlgItemMessageA(hDlg, 0x6EA/0x6EC/0x6EB, 0x4D3/0x4D4/0x4D5/0x4D7, 0, 0)`（如 `0x52F12B..0x52F1C1`），都是 `WM_USER` 段（0x400+）游戏 UI 框架私有消息；`0x622B50` 是该框架的通用分派器（WndProc 开头 `0x52EC1D` 调用）。
- **点击 → 战役**：`0x52F232..0x52F260` 三个 `cmp` 立即数 → `.data` 三个硬编码名字 → `call 0x46CC90` 得到 Battle 表索引。

### Q2 徽章数量由什么决定？

`[本次实测]` **都不是**。既不是「遍历战斗表后过滤」，也不是「按某个固定 side 列表枚举」——而是**对话框模板里写死的控件数量 + 三个硬编码控件 id 常量**：

1. `cDlgItems = 13`（模板常量），其中徽章 Static 只有 2 个；`0x6EB` 分支是残留（模板无控件）。
2. WndProc 用 `cmp ebx, 0x6EA / 0x6EC / 0x6EB` **三条立即数比较**分派，没有循环、没有跳转表按 Battle 表索引。
3. 三个槽位绑死 `.data` 的 `"all1"/"sov1"/"tut1"`，全镜像 0 处绝对写入。
4. `0x46CC90`（按名字查 Battle 表）全镜像**仅 1 个调用点**（0x52F260）。
5. 没有 `CreateWindow`/`CreateWindowEx` 在菜单里动态造徽章；`0x622650` 只用模板建窗。

⇒ 可见徽章数 = **出厂模板固定 2**（代码里预留第 3 个 id 但模板已删）。**Battle 表的 Count 从 14 变 15 不会改变它** `[转引 W27]`。

### Q3 若遍历战斗表，把过滤条件逐条列出

`[本次实测]` 可见徽章**根本不遍历** Battle 表，故无过滤条件可列。唯一遍历 Battle 表的是**隐藏 ListBox 1109**，其循环（`0x52F018..0x52F048`）**没有任何过滤条件**：

| 候选过滤条件 | 是否要求 | 代码级依据 |
|---|---|---|
| battle id 恰为 `ALL1`/`SOV1`/`ALL\d+`/`SOV\d+` 形式 | **否** | 循环只取 `Items[i]+0x2A0`；名字 `+0x24` 只被 `0x46CC90` 用于徽章点击的 `_stricmp`。`ALL1`/`SOV1`/`RA2F1` 在 `.text` 里 **0 个 ASCII 字面量**（`verify.py` §7 断言）。 |
| `CD=` 值 | **否（菜单层）** | WndProc 全文未出现 `+0x98`；`CD` 只在 `0x46CD04`（`Battle::Read_INI`）被读进对象。是否在「开始战役」时校验 CD 是另一条路径，见 `UNKNOWNS.md`。 |
| `FinalMovie` 非空 / 为空 | **否** | WndProc 未出现 `+0x29C`；`0x46CD1E` 读键后存 `[battle+0x29C]`，菜单不查。 |
| `Scenario=` 指向的地图能在 MIX 内找到 | **否（菜单层）** | WndProc 未出现 `+0x9C`；`0x46CD38` 读键后 `strupr` 存入 `[battle+0x9C]`。地图可用性在「无法启动选取地图」阶段才判 `[转引 W27 Q2]`。 |
| id 落在某数值区间 / `[Battles]` 键号范围 | **否** | 循环上界就是 `[0xA83D08]`（Count），`i=0..Count-1`，无上下界裁剪。 |
| `DebugOnly` | **否（只改文本）** | `0x46CD58` 读键 → `0x46CD65 jne 0x46CD8F` → 追加 `" - for debug/testing"` 到 Description，**仍入表**。 |
| `Description` 必须是有效 CSF 标签 | **否（只改显示文本）** | 条目文本就是 `[battle+0x2A0]`；无效标签显示 `MISSING:'…'`，但条目仍生成。W27 的 D1 把 `Description` 换成 `DESC:ALL1` 后「菜单逐项完全不变」 `[转引 W27 §3.1]`，与本结论一致。 |
| 章必须在全局 Battle 表中 | **是（唯一实质前提）** | 循环数据源就是 `0xA83CFC` / `0xA83D08`；并表链见 W29 `[转引]`。 |

### Q4 可检验清单（第 4 项）

见 **§6**，分「可见徽章区（结构上不可能）」与「隐藏 ListBox（有条件可达）」两张清单，每条都给可执行的检验方法。

### Q5 隐藏 ListBox 1109 的用途与填充条件；`LB_GETCOUNT=0` 是不是真正的破绽

`[本次实测]`+`[本次读码]` **用途**：这是引擎自带的 **debug/testing 战役选择器**——列出**全局 Battle 表全部条目**（含 `DebugOnly=yes` 的 12 个官方调试战役），配 `GUI:Load`(1038) 启动选中项，`Slider3` 选难度。证据：官方 `BATTLEMD.INI` 注释、`" - for debug/testing"` 字面量、`STT:CampaignList`/`STT:CampaignButtonLoad` 标签、以及 `0x52F018` 的无过滤全表遍历。

**填充条件**（全部同时满足）：
1. 对话框初始化消息 `0x497` 被处理到 `0x52EFCE`；
2. `GetDlgItem(hDlg, 1109)` 非空；
3. **`[0xA8F7AD] != 0`**（唯一实质门控）；
4. `[0xA83D08] (Count) > 0` 且 `[0xA83CFC] (Items)` 有效。

`[0xA8F7AD] == 0` 时走 `0x52F05C`：`ShowWindow(ListBox, SW_HIDE)` + 隐藏 `GUI:Load` + `EnableWindow(FALSE)`，**循环根本不执行**。

**`LB_GETCOUNT=0` 是否「列表本应有条目但没填」？** `[本次实测]`+`[静态推断]` **不是**。它是**零售态的设计结果**：调试门控关闭 → 列表被隐藏且从未收到任何加条目消息 → 标准 `LB_GETCOUNT` 必然 0。W27 观测到的 `GUI:Load` 隐藏、右侧 7 条空槽不可点、方向键无效，全部与这一分支一致 `[转引 W27 §3]`。

> 附带口径警告：本对话框的加条目用的是 `WM_USER` 段私有消息 `0x4CD`，不是标准 `LB_ADDSTRING (0x180)`；`0x52ED25` 却用标准 `LB_GETCURSEL (0x188)` 读选中项。因此**即使门控打开，标准 `LB_GETCOUNT` 是否随之 >0 取决于 UI 框架是否把条目落到 Win32 列表框内部存储**——静态未定谳（见 `UNKNOWNS.md`）。这不影响「正常态 0 是预期」的结论。

**真正的破绽**（对「追加式 DLC」而言）不是 ListBox 没填，而是：**可见徽章区是模板写死的 2 个控件 + 3 个硬编码名字，没有按 Battle 表生成条目的通路**；以及**调试列表的门控 `[0xA8F7AD]` 在正常启动下为 0**。

---

## 4 · 关键指令字节（VA / RVA / FOFF / 原始字节 / 反汇编并列）

> 以下全部是 **VA**；RVA = VA − `0x400000`；`.text` 内 FOFF = RVA。完整 111 条断言与全部表格见 `EVIDENCE/verify_stdout.txt`（111/111 OK, exit 0）。

| VA | RVA | FOFF | 原始字节 | 反汇编 | 含义 |
|---|---|---|---|---|---|
| `0x52DF48` | `0x12DF48` | `0x12DF48` | `BA 00 EC 52 00` | `mov edx, 0x52EC00` | WndProc 指针 |
| `0x52DF4D` | `0x12DF4D` | `0x12DF4D` | `B9 94 00 00 00` | `mov ecx, 0x94` | 对话框资源 148 |
| `0x52DF65` | `0x12DF65` | `0x12DF65` | `E8 E6 46 0F 00` | `call 0x622650` | 建窗 |
| `0x6226CB` | `0x2226CB` | `0x2226CB` | `FF 15 50 14 7E 00` | `call [0x7E1450]` | `CreateDialogIndirectParamA` |
| `0x52EC00` | `0x12EC00` | `0x12EC00` | `83 EC 10 53 8B 5C 24 1C` | `sub esp,0x10; push ebx; mov ebx,[esp+0x1C]` | WndProc 入口 |
| `0x52EE04` | `0x12EE04` | `0x12EE04` | `81 FB EA 06 00 00` | `cmp ebx, 0x6EA` | 徽章 1 常量 |
| `0x52EE3F` | `0x12EE3F` | `0x12EE3F` | `81 FB EC 06 00 00` | `cmp ebx, 0x6EC` | 徽章 2 常量 |
| `0x52EE78` | `0x12EE78` | `0x12EE78` | `81 FB EB 06 00 00` | `cmp ebx, 0x6EB` | 残留第 3 槽 |
| `0x52EFFC` | `0x12EFFC` | `0x12EFFC` | `68 55 04 00 00` | `push 0x455` | `GetDlgItem(1109)` |
| `0x52F00B` | `0x12F00B` | `0x12F00B` | `A0 AD F7 A8 00` | `mov al, [0xA8F7AD]` | ★ 唯一门控 |
| `0x52F012` | `0x12F012` | `0x12F012` | `74 48` | `je 0x52F05C` | 0 → 隐藏列表 |
| `0x52F018` | `0x12F018` | `0x12F018` | `A1 08 3D A8 00` | `mov eax, [0xA83D08]` | Count |
| `0x52F023` | `0x12F023` | `0x12F023` | `A1 FC 3C A8 00` | `mov eax, [0xA83CFC]` | Items |
| `0x52F028` | `0x12F028` | `0x12F028` | `8B 0C B8` | `mov ecx, [eax+edi*4]` | `Items[i]` |
| `0x52F02B` | `0x12F02B` | `0x12F02B` | `81 C1 A0 02 00 00` | `add ecx, 0x2A0` | Description |
| `0x52F034` | `0x12F034` | `0x12F034` | `68 CD 04 00 00` | `push 0x4CD` | WM_USER 私有加条目 |
| `0x52F03A` | `0x12F03A` | `0x12F03A` | `FF 15 A4 14 7E 00` | `call [0x7E14A4]` | `SendMessageA` |
| `0x52F045/46/48` | `0x12F045…` | 同 | `47 / 3B F8 / 7C D9` | `inc edi; cmp edi,eax; jl 0x52F023` | 循环上界 = Count |
| `0x52F05C` | `0x12F05C` | `0x12F05C` | `6A 00` | `push 0` | `ShowWindow(SW_HIDE)` 参数 |
| `0x52F067` | `0x12F067` | `0x12F067` | `68 0E 04 00 00` | `push 0x40E` | `GUI:Load` |
| `0x52F079` | `0x12F079` | `0x12F079` | `FF 15 A0 14 7E 00` | `call [0x7E14A0]` | `EnableWindow(FALSE)` |
| `0x52F232` | `0x12F232` | `0x12F232` | `81 FD EA 06 00 00` | `cmp ebp, 0x6EA` | 点击分派 |
| `0x52F23A` | `0x12F23A` | `0x12F23A` | `8B 0D 68 5C 82 00` | `mov ecx, [0x825C68]` | → `"all1"` |
| `0x52F24A` | `0x12F24A` | `0x12F24A` | `8B 0D 6C 5C 82 00` | `mov ecx, [0x825C6C]` | → `"sov1"` |
| `0x52F25A` | `0x12F25A` | `0x12F25A` | `8B 0D 70 5C 82 00` | `mov ecx, [0x825C70]` | → `"tut1"` |
| `0x52F260` | `0x12F260` | `0x12F260` | `E8 2B DA F3 FF` | `call 0x46CC90` | 名字→表索引（**全镜像唯一调用点**） |
| `0x52ECB8` | `0x12ECB8` | `0x12ECB8` | `3D 0E 04 00 00` | `cmp eax, 0x40E` | `GUI:Load` |
| `0x52ED25` | `0x12ED25` | `0x12ED25` | `68 88 01 00 00` | `push 0x188` | `LB_GETCURSEL` |
| `0x52ED2D` | `0x12ED2D` | `0x12ED2D` | `89 07` | `mov [edi], eax` | 返回选中索引 |
| `0x52E08E` | `0x12E08E` | `0x12E08E` | `8B 44 24 14` | `mov eax, [esp+0x14]` | 对话框结果 |
| `0x52E098` | `0x12E098` | `0x12E098` | `89 81 CC 34 00 00` | `mov [ecx+0x34CC], eax` | 落到 Session |
| `0x46CC90` | `0x6CC90` | `0x6CC90` | `A1 08 3D A8 00` | `mov eax, [0xA83D08]` | `Find_Index_By_Name` |
| `0x46CCA8` | `0x6CCA8` | `0x6CCA8` | `83 C0 24` | `add eax, 0x24` | 名字偏移 |
| `0x46CCAC` | `0x6CCAC` | `0x6CCAC` | `E8 6F C0 35 00` | `call 0x7C8D20` | `_stricmp` |
| `0x46CE10` | `0x6CE10` | `0x6CE10` | `83 EC 24` | `sub esp, 0x24` | `Register_Battles` 入口 |
| `0x46CE17` | `0x6CE17` | `0x6CE17` | `68 D8 B1 81 00` | `push 0x81B1D8` | `"Battles"` |
| `0x46CE77` | `0x6CE77` | `0x6CE77` | `E8 A4 BE 35 00` | `call 0x7C8D20` | 按条目名 `_stricmp` 合并 |
| `0x46CD58` | `0x6CD58` | `0x6CD58` | `68 B0 B1 81 00` | `push 0x81B1B0` | `"DebugOnly"` |
| `0x46CD65` | `0x6CD65` | `0x6CD65` | `75 28` | `jne 0x46CD8F` | true → 追加调试后缀 |
| `0x46CD67` | `0x6CD67` | `0x6CD67` | `81 C3 A0 02 00 00` | `add ebx, 0x2A0` | Description 目标 |

**模板/数据区（非 `.text`）**：

| VA | RVA | FOFF | 字节 | 含义 |
|---|---|---|---|---|
| `0xB83270` | `0x783270` | `0x487270` | `01 00 FF FF` | `DIALOGEX` 头；`+0x10 = 0D 00` = `cDlgItems 13` |
| `0xB83410` | `0x783410` | `0x487410` | UTF-16 `"GUI:CampaignMenu"` | id 1684 Static 文本 |
| `0xB832B4` | `0x7832B4` | `0x4872B4` | `55 04 00 00` @+0x14 | 控件 #0 id = 1109 |
| `0xB83434` | `0x783434` | `0x487434` | `EA 06 00 00` | 控件 #7 id = 1770 |
| `0xB83454` | `0x783454` | `0x487454` | `EC 06 00 00` | 控件 #8 id = 1772 |
| `0x825C68` | `0x425C68` | `0x425C68` | `A0 5C 82 00` | → `0x825CA0 "all1"` |
| `0x825C6C` | `0x425C6C` | `0x425C6C` | `98 5C 82 00` | → `0x825C98 "sov1"` |
| `0x825C70` | `0x425C70` | `0x425C70` | `90 5C 82 00` | → `0x825C90 "tut1"` |
| `0xA8F7AD` | `0x68F7AD` | — (**BSS，无文件字节**) | 装载时 0 | 调试列表门控 |

**INI 键字面量（`.rdata`/`.data` raw）**：`0x81B1A4 "Description"`、`0x81B1B0 "DebugOnly"`、`0x81B1BC "Scenario"`、`0x81B1C8 "FinalMovie"`、`0x81B1D4 "CD"`、`0x81B1D8 "Battles"`、`0x81B18C " - for debug/testing"`；`0x8263B0 "STT:SovietCampaignIcon"`、`0x8263C8 "STT:AlliedCampaignIcon"`、`0x8263E0 "BootCampSelect"`、`0x8263F0 "AlliedCampaignSelect"`、`0x826408 "SovietCampaignSelect"`。

---

## 5 · 过滤条件逐条（Q3 汇总表）

见 §3 Q3 表。**结论：菜单层的唯一「条件」是「该 battle 已在 `0xA83CFC/0xA83D08` 全局表里」，且只对隐藏调试 ListBox 成立；可见徽章区连这个条件都不检查（它压根不读表来生成条目）。** 无 id 形式 / CD / FinalMovie / Scenario / 数值区间 / DebugOnly / CSF 有效性 任何过滤。

---

## 6 · 第 4 项：可检验清单

### 清单 A —— 「追加 battle id 变成第 3 颗可见徽章」：**结构上不可能（不修改 exe）**

下列每一条都是**可复跑的静态检验**（`python EVIDENCE/verify.py` 全部断言 + 下列 grep）：

| # | 检验项 | 期望（当前镜像） | 检验方法 |
|---|---|---|---|
| A1 | 模板控件总数固定 | `cDlgItems = 13` | `parse_dialog.py` → `RT_DIALOG id=148`；或读 `FOFF 0x487280` = `0D 00` |
| A2 | 徽章 Static 个数 | **恰好 2**（1770 / 1772） | `verify.py §1`；模板里不存在 `0x6EB` 控件 |
| A3 | 徽章分派是否循环/查表 | 只有 3 条 `cmp` 立即数 `0x6EA/0x6EC/0x6EB` | `verify.py §3`；`wndproc_full_disasm.txt` 全文 |
| A4 | 是否动态创建徽章 | 菜单 WndProc 内无 `CreateWindow*`；`0x622650` 只用 `CreateDialogIndirectParamA` | `recon8_stdout.txt` 反汇编 |
| A5 | 槽位→battle id 是否可配 | 三个 `.data` 指针静态初值 `"all1"/"sov1"/"tut1"`，全镜像 **0 处绝对地址写入** | `verify.py §2` |
| A6 | Battle 表名字查找的调用面 | `0x46CC90` **仅 1 个 rel32 调用点** `0x52F260` | `verify.py §3` |
| A7 | `.text` 内是否有 `ALL1/SOV1/RA2F1` 字面量 | 0 命中 | `verify.py §7` / `recon4_stdout.txt` |
| A8 | 是否存在按 Battle 表生成徽章的跳转表 | 无等距跳转表指向「每战役一个绘制函数」；`0x52E161`/`0x52E287`/`0x52E356` 的跳转表是**主菜单 5 态/6 态状态机**（`0xA8B238` mode），与战役表无关 | `recon6_stdout.txt`；已用「目标必须落在指令边界」复核，不当 vtable |

⇒ **要通过追加 `BATTLEMD98.INI` 让第 3 颗徽章出现，A1–A8 必须至少有一条被推翻；本镜像全部成立。可行替代（均超出本卡授权）**：① 改 exe / 对话框资源（加控件 + 改 `cDlgItems` + 加分派分支 + 改 `.data` 名字指针）；② 用**官方 id + 散装覆盖**（`ALL1`/`SOV1`，W29 同 ID 后装载者覆写）借现有两颗徽章进入追加地图 —— W27 的 D2/D3 已证明这条通道能进图 `[转引]`。

### 清单 B —— 「追加 battle id 出现在 `GUI:CampaignMenu` 的某个可点条目里」：**有条件可达**

| # | 条件 | 等级 | 检验方法 |
|---|---|---|---|
| B1 | 散装 `BATTLEMD*.INI` 的 `[Battles]` 有 `N=<id>`，且同名段 `[<id>]` 可被 `0x46CCD0` 读到 | `[转引 W29]` | 文件投放；`W29_override_order/override_order.py` |
| B2 | 引擎全局表 `0xA83D08` Count 增加、`0xA83CFC` 指向该对象（W27 实测 15 / `RA2F1` / `CD=2` / `ECH01.MAP`） | `[转引 W27]` + `[本次实测]`（代码用这两个地址） | W27 `out/p1b_memory.ndjson`；`verify.py §5/§7` |
| B3 | `Description=` 写成有效 CSF 标签（避免 `MISSING:`），但**不影响是否生成条目** | `[转引 W27 D1]` + `[本次读码]` | W27 `out/p2a_D1_diagnostic.ndjson` |
| B4 | `[0xA8F7AD] != 0` —— **唯一未闭合的硬门槛** | `[静态推断]` / `[待运行验证]` | 见下 |
| B5 | `GetDlgItem(hDlg,1109)` 非空、Count>0 | `[本次实测]` | `0x52EFFC`–`0x52F021` |
| B6 | 门控打开后，`0x52F018..0x52F048` 把 `Items[i]+0x2A0` 无过滤逐条加入；追加 id 成为第 `Count-1` 项 | `[本次实测]` | `verify.py §5`（循环体无字段 cmp/test 断言） |
| B7 | 选中该项 → `GUI:Load`(0x40E) → `LB_GETCURSEL` 索引回传 → 落到 `[Session+0x34CC]` 作为 Battle 表索引 | `[本次实测]`+`[本次读码]` | `0x52ECB8`–`0x52ED2F`、`0x52E08E`–`0x52E098` |
| B8 | **无** id 形式 / CD / FinalMovie / Scenario 可寻 / 数值区间 / DebugOnly 过滤 | `[本次实测]` | §3 Q3 表；WndProc 全文未出现 `+0x98/+0x9C/+0x29C` |

**B4 的现状（诚实）**：
- `0xA8F7AD` 位于 `.data` **BSS**（RVA `0x68F7AD` > RawSize `0x6C000`），装载时为 0 `[本次实测]`；
- 全镜像对 `0xA8F7AD` 的 4 字节绝对地址引用**恰好 1 处**，即 `0x52F00B` 的 `mov al,[abs]`（读）`[本次实测]`；
- `C6 05 / 88 15 / A2 / 80 0D / C7 05` 等所有绝对写形式 **0 命中**；`mov reg, imm32(0xA8F7A*) / lea reg,[0xA8F7A*]` 亦 0 命中 `[本次实测]`；
- ⇒ 写入者若存在必为**寄存器间接**（结构体基址 + 偏移），纯静态未定位 `[静态推断]`。W27 正常启动观测到的 `LB_GETCOUNT=0` 与该字节为 0 一致 `[转引]`。
- **最小可证伪运行实验（本卡禁止，需单独授权）**：在隔离副本中把 `[0xA8F7AD]` 置 1 后打开 `GUI:CampaignMenu`，检查 ListBox 是否出现 `Count` 个条目、追加 id 是否在列；对照不置位应为 0。判据干净、不依赖 CSF。

---

## 7 · 与 W27 真机观测的逐项对照

| W27 观测 | 本卡静态解释 | 等级 |
|---|---|---|
| 只有 2 颗徽章（盟军/苏联） | 模板 2 个徽章 Static（1770/1772）；`0x6EB` 分支无控件 | `[本次实测]` |
| 徽章 rect `[94,39,326,130]` / `[94,243,326,334]`，控件文本空 | 模板 #7/#8 无文本、`exStyle=0x20` 自绘；对话框单位与像素存在比例换算 | `[本次实测]`+`[静态推断]` |
| 5 个空文字 Static | 模板恰好 5 个无文本 Static：1770/1772/1820/1959/1960 | `[本次实测]` |
| `Slider3` + `GUI:Difficulty` + `GUI:Harder` + `GUI:Back` | 模板 #2/#3/#4/#5 逐项吻合 | `[本次实测]` |
| 隐藏 ListBox 1109 `LB_GETCOUNT=0` | 门控 `[0xA8F7AD]==0` → `ShowWindow(SW_HIDE)` + 循环未执行 | `[本次实测]` |
| `GUI:Load` 隐藏 | 同分支 `ShowWindow` + `EnableWindow(FALSE)` | `[本次实测]` |
| 方向键 / 点徽章 / 点右侧槽位全穷举无第三条目 | 只有 3 个硬编码 id 分派；右侧是单一 ListBox，无第三控件 | `[本次实测]` |
| 引擎表 Count=15、`RA2F1` 对象含 `CD=2 / ECH01.MAP` | 并表链 `0x52CB90`→`0x46CE10`→`0x46CCD0`；字段偏移 `+0x98`/`+0x9C` | `[转引 W27/W29]`+`[本次实测]` |
| D1：换 `Description=DESC:ALL1` 后 `MISSING:` 消失但菜单逐项不变 | Description 只作 ListBox 条目文本 `+0x2A0`；可见徽章不读表 | `[本次实测]`+`[转引]` |
| D4：`RA2F1`→`YURI1` 菜单证据不可用（快照落主菜单） | 本卡静态支持「改 id 不会生成第 3 徽章」（A3/A5/A6）；D4 仍无需重跑来判此结论 | `[本次实测]` |

---

## 8 · 结论等级总表

| # | 结论 | 等级 |
|---|---|---|
| C1 | 目标镜像与前提一致（SHA-256 / ImageBase / RELOCS_STRIPPED / `.text` FOFF=RVA） | `[本次实测]` |
| C2 | `GUI:CampaignMenu` = `RT_DIALOG id=148`，`DIALOGEX`，`cDlgItems=13`，由 `CreateDialogIndirectParamA` 创建 | `[本次实测]` |
| C3 | 模板只有 2 个徽章 Static（1770/1772）；`0x6EB` 有代码分支但无控件 | `[本次实测]` |
| C4 | 徽章分派是 3 条硬编码 `cmp` 立即数，槽位绑死 `.data` 的 `"all1"/"sov1"/"tut1"`（0 处绝对写入） | `[本次实测]` |
| C5 | `0x46CC90`（按名字查 Battle 表）全镜像仅 1 个调用点（徽章点击 0x52F260） | `[本次实测]` |
| C6 | **可见徽章数量与 Battle 表无关；追加 id 结构上不可能生成第 3 颗徽章（不改 exe）** | `[本次实测]`+`[本次读码]` |
| C7 | 隐藏 ListBox 1109 的填充循环遍历整张 Battle 表且**无任何字段过滤** | `[本次实测]` |
| C8 | 该填充被单一 BSS 字节 `[0xA8F7AD]` 门控；为 0 时列表被隐藏且从不填充 | `[本次实测]` |
| C9 | `GUI:Load` 把 `LB_GETCURSEL` 索引作为 Battle 表索引返回给调用方 | `[本次实测]`+`[本次读码]` |
| C10 | `LB_GETCOUNT=0` 是零售态设计结果，**不是「应有条目却没填」的破绽** | `[本次实测]`+`[静态推断]` |
| C11 | `[0xA8F7AD]` 的写入者未静态定位（唯一绝对引用是读；BSS 初值 0） | `[静态推断]` / `[待运行验证]` |
| C12 | 打开该门控后端到端真的显示/可选中追加战役 | `[待运行验证]`（本卡禁止运行） |
| C13 | `0x4CD` 是游戏 UI 框架 `WM_USER` 段私有加条目消息；标准 `LB_GETCOUNT` 在门控打开后是否 >0 未定 | `[静态推断]` |
| C14 | `DebugOnly` 只给 Description 追加 `" - for debug/testing"`，不影响入表 | `[本次实测]`+`[本次读码]` |

---

## 9 · 复算方法

```powershell
cd D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W32_campaign_menu_entries\EVIDENCE
pwsh -NoProfile -File .\run_all.ps1     # 12 个脚本全部 exit 0，生成 *_stdout.txt / *_stderr.txt / *_exitcode.txt / RUN_MANIFEST.txt
python verify.py                         # 111/111 断言 OK, exit 0
python verify.py --selftest              # 112/112（含负控）, exit 0
```

- `verify.py` 是**权威判据**：111 条逐字节断言 + 结构谓词（含「循环体无过滤」「`0x46CC90` 唯一调用点」「`0xA8F7AD` 唯一绝对引用」「`.data` 三指针 0 写入」）。`--selftest` 用故意改错的字节证明断言器不会假通过。
- `parse_dialog.py` 按 Win32 `DIALOGEX` 规范解析全部 98 个 `RT_DIALOG`（`sz_Or_Ord` 的「首 WORD 是首字符而非长度」已修正；`title`/`typeface` 按纯 WCHAR[] 处理）。
- `wndproc_full_disasm.txt`：从正确函数边界 `0x52EC00` 开始的完整 WndProc 反汇编（未用 `ret` 当结束判据；`ret 0x10` 出现在多个分支尾部）。
- `recon4/5` 里「从任意回溯偏移线性反汇编找 xref」的输出**会失同步**（`sbb eax, 0xA8F7A0` 之类是错边界解码），**不作为事实**；权威结论一律取自 `verify.py` 的字节断言与 `parse_dialog.py` 的结构解析。等距指针表未被当作 vtable。
- `EVIDENCE/README.md` 记录每个脚本用途与已知限制。

---

## 10 · 交付清单

```
W32_campaign_menu_entries/
├── MENU_ENTRIES.md        本文件
├── UNKNOWNS.md            未闭环项
├── DISAGREE.md            与前提/前序卡不符处
└── EVIDENCE/
    ├── run_all.ps1 / RUN_MANIFEST.txt / run_all_console.txt
    ├── verify.py / verify_stdout.txt / verify_stderr.txt / verify_exitcode.txt
    ├── selftest_stdout.txt / selftest_stderr.txt / selftest_exitcode.txt
    ├── parse_dialog.py (+ stdout/stderr/exitcode)
    ├── recon1..recon9.py (+ 各自 stdout/stderr/exitcode)
    ├── wndproc_full_disasm.txt
    └── README.md
```

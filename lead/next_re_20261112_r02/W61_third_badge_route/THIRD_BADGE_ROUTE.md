# W61 · 第三条路线 (c) 评估：改 `RT_DIALOG 148` 开 1771 槽

> 执行者：Hy4（逆向工程执行卡 W61，非 Lead）｜开始：`STARTED.txt`（2026-11-13T22:55:22+08:00）
> 时间盒 90 min；纯离线静态 + 只写本卡目录。**I launched 0 / attached 0**：未启动 `gamemd.exe`、未 attach、未取 `.game_instance.lock`、未改 `ra2bench\gamemd.exe` / `ra2youli\` / `ra2forge` / `ra2opt` / W21–W60；`git` 只读。
> 结论分级：`[本次实测]`（本卡脚本/解析/补丁回读出的）、`[本次读码]`（本卡 capstone 反汇编读出的）、`[静态推断]`、`[转引]`（引用既有卡/Lead 件）、`[待运行验证]`。
> **本卡不写「第三徽章可用」/「路线(c) 可行」这类真机断言**；只给静态可行性、所需条件与风险。

**基线**：`ra2bench\gamemd.exe` 4,825,360 B，SHA-256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
（`[本次实测]`，与 `REVIEW\LEAD_CHECK_menu_3slot.md` 的 `73201cc0…67476` 一致）。PE `ImageBase=0x400000`，5 节，`.text/.rdata/.data/.rsrc/.detour`，**`CheckSum=0`**，`SizeOfImage=0x796000`，无 `.reloc` 节。

---

## 0 · 一句话判定

`[静态推断]` **资源层静态可行**：在副本上真做了一次补丁，插入 `id=1771` STATIC、`cDlgItems` 13→14，用自己的解析器回读出 **14 个控件**（`trailing=0`），补丁字节 diff、前后 SHA-256 全部落盘。
**但路线 (c) 静态不完整**：引擎保留第三槽的**数据**（控件 id / battle 名 `tut1` / 音效 `BootCampSelect` / CSF 提示 `STT:CampaignAnimTutorial` / 描述 `DESC:TUT1`），**却没有独立的第三徽章图资源**；补丁只补出一个**可点击热区**，视觉仍须另补美术与背景。`[待运行验证]` 全部可见行为。

---

## 1 · 1771 分支语义（Q1）

### 1.1 消息分派（本卡 capstone 全量反汇编 `0x52EC00..0x52F3E8`，`[本次读码]`）

`EVIDENCE\recon_stdout.txt` / `EVIDENCE\procs_stdout.txt`。入口 `0x52EC00 sub esp,0x10; push ebx; mov ebx,[esp+0x1c]`（uMsg）。分派链：

| uMsg | 语义 | 跳转 |
|---|---|---|
| `0x084` | `WM_NCHITTEST` | `0x52ED60` |
| `0x111` | `WM_COMMAND` | `0x52ECB1` |
| `0x114` | `WM_HSCROLL`（难度滑条） | `0x52EC59` |
| `0x201` | `WM_LBUTTONDOWN` | `0x52EEFA` |
| `0x202` | `WM_LBUTTONUP` | `0x52F1CF` |
| `0x497` | 初始化（三个音效索引） | `0x52EFCE` |
| `0x4D8` | 自定义 | `0x52EFA5` |

`WM_NCHITTEST` 处理器 `0x52ED6D..0x52EDAA` 用 `GetWindowRect`(`[0x7E13BC]`) → `ChildWindowFromPointEx`(`[0x7E13B8]`) → `GetDlgCtrlID`(`[0x7E13B4]`)，得到 `ebx = 光标下的控件 id`。IAT 名字由 `EVIDENCE\deep_stdout.txt` 逐项解析确认。

### 1.2 `0x52EE78..B8` 做了什么（`[本次读码]`）

```
0x52EE04 cmp ebx,0x6ea ; 1770
0x52EE14 mov edx,[0x825C78]           ; AlliedCampaignSelect 音效索引
0x52EE25 mov [0x825C20],edx           ; 当前 hover 音效
0x52EE1E push 0x4d3 ; 0x52EE23 push ebx ; 0x52EE24 push esi ; 0x52EE2B call edi(SendDlgItemMessageA)
0x52EE2F mov [0xa8f7a8],ebx           ; 当前选择 = 1770

0x52EE3F cmp ebx,0x6ec ; 1772  → [0x825C74] / [0x825C20] / 0x4d3 / [0xa8f7a8]=1772

0x52EE78 cmp ebx,0x6eb                ; ★1771
0x52EE7E jne 0x52f3dc
0x52EE84 cmp eax,ebx                 ; eax=[0xa8f7a8]，已选中则跳过设置 [0x825C20]
0x52EE86 je  0x52ee94
0x52EE88 mov ecx,[0x825C7C]           ; BootCampSelect 音效索引
0x52EE8E mov [0x825C20],ecx
0x52EE94 push 0
0x52EE96 push 0
0x52EE98 push 0x4d3                  ; 自定义状态消息 WM_USER+0xD3
0x52EE9D push 0x6eb                  ; ★控件 id 1771（字面量）
0x52EEA2 push esi                    ; hDlg
0x52EEA3 call edi                    ; SendDlgItemMessageA(hDlg,1771,0x4D3,0,0)
0x52EEA8 mov dword ptr [0xa8f7a8],0x6eb   ; ★当前选择 = 1771
0x52EEB8 ret 0x10
```

三个分支**结构等价**：设置 `[0x825C20]`（hover 音效索引）、向该 id 发 `0x4D3`、把 `[0xA8F7A8]` 置为该 id。1771 分支的两处差异：用字面量 `push 0x6eb` 而非 `push ebx`；已选中时只跳过 `[0x825C20]` 设置（`je 0x52ee94`），不像 1770/1772 直接 `je 0x52f3dc` 整体返回。

**`[本次读码]` 结论**：`0x52EE78..B8` **不会**把当前选择设成 `tut1` 字符串，也不会调用 `0x46CC90`；它只把"当前选中控件 id"置为 1771、置 hover 音效、发一个状态消息。

### 1.3 BATTLE 表查表在 `WM_LBUTTONUP`（`[本次读码]`）

`0x52F1CF`（uMsg `0x202`）→ `ChildWindowFromPointEx` + `GetDlgCtrlID` 得 `ebp`；`0x52F232..0x52F260` 三槽映射：

```
0x52F232 cmp ebp,0x6ea ; je → mov ecx,[0x825C68] ; "all1"
0x52F242 cmp ebp,0x6ec ; je → mov ecx,[0x825C6C] ; "sov1"
0x52F252 cmp ebp,0x6eb ; je → mov ecx,[0x825C70] ; "tut1"   ★
0x52F260 call 0x46CC90                     ; Battle 表按名查表
0x52F265 mov [edi],eax                     ; 存入对话框 state(GetWindowLongA(hDlg,8))
0x52F267 mov byte ptr [edi+4],1            ; ★无条件置"有效"标志
0x52F26B mov al,[edi+4] ; test al,al ; je 0x52f3c6   ; 恒不成立
```

`0x825C68/6C/70` 三个指针初值 `[本次实测]`（`EVIDENCE\menu_strings_stdout.txt`）：`0x825CA0="all1"`、`0x825C98="sov1"`、`0x825C90="tut1"`；`.data` 原始字节 `74 75 74 31 00` / `73 6f 76 31 00` / `61 6c 6c 31 00`。三串在 `.text` 中**无直接 xref**（只经指针表），`[本次实测]`。

`0x46CC90` 本身（`EVIDENCE\deep_stdout.txt`）：
```
0x46CC90 mov eax,[0xa83d08]        ; Battle 表 Count
0x46CC9F mov eax,[0xa83cfc]        ; 表基址
0x46CCA5 mov eax,[eax+esi*4]       ; Battle*
0x46CCA8 add eax,0x24              ; +0x24 = 名字字段
0x46CCAC call 0x7c8d20             ; stricmp(name, 参数)
0x46CCB6 je 0x46ccc8               ; 命中
0x46CCC2 or  eax,0xffffffff ; ret   ; ★失败返回 -1（不是指针！）
0x46CCC8 mov eax,esi ; ret          ; ★成功返回数组下标
```

### 1.4 查表失败的后果（`[本次读码]` + `[待运行验证]`）

- `BATTLEMD.INI` 现无 `[TUT*]` 段、`[Battles]` 14 条无 `TUT1`（`[本次实测]`，`ra2bench\BATTLEMD.INI` 已逐行读）。**当前若真有 1771 控件，点击后 `0x46CC90("tut1")` 返回 `-1`**。
- **本处无失败分支**：`0x52F267` 无条件把 `[edi+4]` 置 1，`0x52F26B` 的 `je 0x52f3c6` 因此恒假；`-1` 被原样 `mov [edi],eax` 存进对话框 state 结构体。
- 之后 `0x52F276..0x52F2C3` 仍照常发 `0x4D5`/`0x4D4`、读滑条 `TBM_GETPOS(0x400)`；`0x52F2C8..0x52F302` 用 `[0x825C20]` 播 `0x750920`（BootCampSelect 音效），再把 `[0x825C20]` 置 `-1`。
- 该 state 由 `GetWindowLongA(hDlg,8)` 取出（`0x52F222` / `0x52ECFA`），最终在 `0x52DE00..0x52E098` 的对话框调用者里被写入 `[0xA8B230+0x34CC]`。`[本次读码]` **本处没有任何错误字符串/MessageBox/降级分支**；`-1` 被上层如何使用、`[待运行验证]`（不排除越界/静默不进图）。
- 另注：`0x52F028 [eax+edi*4]` 那个绕过查表的通用循环属于**隐藏调试 ListBox**（门控 `[0xA8F7AD]`，`0x52F00B`），与徽章点击主链不同；`[转引]` W58/W32：零售态 `LB_GETCOUNT=0`、门控无静态写入者。

---

## 2 · 徽章图从哪来（Q2，路线成败关键）

### 2.1 先给结论

`[本次实测]` **引擎没有为第三徽章准备独立图资源**；`[本次读码]` **WndProc 完全不加载徽章图**；`[静态推断]` 徽章 STATIC 是"透明点击热区"，视觉来自通用 UI 背景/动画子系统。第三槽只保留了**数据**（id / battle 名 / 音效 / tooltip / 描述），没有图。

### 2.2 逐层证据

1. **`[本次实测]` 整个战役菜单代码区 `0x52D800..0x52F400` 引用的字符串只有 15 个**（`EVIDENCE\menu_strings_stdout.txt`）：`D:\ra2mdpost\Init.CPP`、`TXT_OK`、`RENEGADE.BIK`、`GUI:Cancel`、`GUI:ExitAreYouSure`、`INTRO`、`GUI:Load`、`GUI:Back`、`GUI:CampaignMenu`、`GUI:Difficulty`、`GUI:Harder`、`GUI:Blank`、`STT:SovietCampaignIcon`、`STT:AlliedCampaignIcon`、`AlliedCampaignSelect` / `SovietCampaignSelect` / `BootCampSelect`。**没有 `.SHP` / `.PCX` / 按 `all1`/`sov1`/`tut1` 拼的文件名 / `Load_*` / `CCFileClass` / 资源 id 常量**。三个战役名只用于 `0x46CC90` 查表。
2. **`[本次实测]` `.rsrc` 没有 RT_BITMAP / RT_RCDATA**（`EVIDENCE\recon_stdout.txt`：113 个资源叶 = RT_CURSOR 1 / RT_DIALOG 98 / RT_GROUP_CURSOR 1 / RT_GROUP_ICON 4 / RT_ICON 7 / RT_MENU 1 / RT_VERSION 1）。⇒ 徽章不是 PE 内嵌位图。
3. **`[本次实测]` 徽章控件是透明、无文字的 STATIC**：`cls=ordinal 130 (STATIC)`、`style=0x50000007`、`exStyle=0x00000020 (WS_EX_TRANSPARENT)`、`title=ordinal 0`、`extra=0`，`id=1770 @(125,34) 174×87`、`id=1772 @(125,216) 173×86`（本卡自解模板，`EVIDENCE\dlg_parse_orig_stdout.txt`）。鼠标命中靠 `ChildWindowFromPointEx`+`GetDlgCtrlID`，**不是**靠坐标常量。
4. **`[本次读码]` 三个 `*CampaignSelect` 是 SOUND.INI 音效事件名，不是图**：`0x7514D0` 是"名字→全局表下标"查找（`EVIDENCE\deep_stdout.txt`：`[0xB1D37C]` 数组 + `0x7C8D20` 逐项 `stricmp`），结果存 `[0x825C74/78/7C]`；`0x52EFCE` 用 `"SovietCampaignSelect"/"AlliedCampaignSelect"/"BootCampSelect"` 三次调用。`[本次实测]` `extracted\all_inis\expandmd01_mix_7A742519.ini`（SOUND.INI）`SoundList` `532=AlliedCampaignSelect` `533=SovietCampaignSelect` **`534=BootCampSelect`**，且 `[BootCampSelect] Sounds=$igisea Volume=90`。`0x52F2F7` 用 `[0x825C20]` 调 `0x750920` 播音。
5. **`[本次读码]` 第三槽有专用 tooltip**：通用 tooltip 分派函数 `0x6041E5`（`EVIDENCE\anim_xrefs_stdout.txt`）按"对话框 id=0x94(148) + 控件 id"返回 CSF 标签：
   - `0x6041ED cmp eax,0x6ea` → `STT:AlliedCampaignIcon`
   - **`0x6041FD cmp eax,0x6eb` → `STT:CampaignAnimTutorial`**
   - `0x60420D cmp eax,0x6ec` → `STT:SovietCampaignIcon`
   
   `[本次实测]` `ra2md.csf`（`langmd.mix` entry `BD835079`，332,973 B，`EVIDENCE\csf_check_stdout.txt`）含 **`STT:CampaignAnimAllied` / `STT:CampaignAnimSoviet` / `STT:CampaignAnimTutorial`**、`GUI:TutorialCampaign`、`GUI:SelectCampaign`、**`DESC:TUT1`** 共 5,211 个标签；值文本为 Big5 中文（`EVIDENCE\csf_values.txt`）。⇒ 第三槽的提示文案与描述标签**都在**。
6. **`[本次读码]` 视觉子系统**：`.rdata 0x824080..0x824340` 有 `GraphicMenu` / `GraphicMenuItem` / `GraphicMenuImageItem` RTTI 与 INI 字段名 `ItemMax / Theme / .BIK / .VQA / .PCX / Background / Intro / Title.PCX / Loop / ActiveRect / Origin / Palette / SelectVQ / HighlightSound / Disabled / Highlighted / SelectSound / Shortcut / Type`（`EVIDENCE\strings2_stdout.txt`）。`[本次实测]` `wdt.mix` 里确有 `[FactionChoiceMenu640]` 定义，`Image=` / `Highlighted=` 指向 `.SHP`/`.PCX`（`work\wdt_A91DA00A.txt`）。资源取数通道 `[转引]` W29/W53：`CCFileClass::Get_File 0x473D10` 磁盘优先、MIX 回落。
   **`[静态推断]`** 两颗可见徽章的像素来自这套 INI 驱动的菜单背景/动画 SHP/PCX，而非按 battle 名逐槽加载的独立文件。**本卡未能定位到"给 1770/1772 两个 STATIC 上色"的确切那一行**（见 `UNKNOWNS.md` U1）。
7. **`[本次实测]` 全 MIX 递归枚举**：`EVIDENCE\mix_recursive_stdout.txt` 走完 `ra2bench\*.mix`（含 5,630 个嵌套 MIX 容器，1,168,759 个不同 CRC id），`EVIDENCE\q2_final_stdout.txt` 从 INI 类条目里收割出 144 个真实美术文件名：
   - **唯一**带 campaign 名的候选是 `CAMPAIGN.PCX`（`ra2.mix/A8548FD9`，76,884 B，CRC `0x6177B5BE`）。已解出到 `work\CAMPAIGN.PCX` 并用 Pillow 渲染 `work\CAMPAIGN.png`：PCX 头 `manufacturer=0x0A, version=5, encoding=1, bpp=8`，**640×480**（`EVIDENCE\pcx_render_stdout.txt`）。圖像呈暗色（PCX 自带 256 色调色板与游戏运行调色板不一致），可见右侧两块深色空面板，左侧大面积纯黑 —— 无法据此确认徽章是否烘在背景里（`[静态推断]`，见 U1）。
   - **无任何** `TUT*` / `BOOT*` / `BADGE*` / `EMBLEM*` / `CAMP3` / `YURICAMP` / `SIDE3` 美术名命中（`EVIDENCE\mix_recursive_stdout.txt` 的 keyword 命中数 = 1，即 `CAMPAIGN.PCX` 本身）。`EVIDENCE\q2_scan_stdout.txt`：`CAMPAIGN.PCX` 字面量在 MIX 条目数据中 0 次（MIX 索引只存 CRC，名字本身不落盘；该文件也不在 exe 的 403 个文件名字符串表里，其名字在运行期如何构造 `[静态推断-弱]` / 见 U1）；`BootCamp` 只出现在 SOUND.INI，`Tutorial` 只出现在 CSF，`TUT1` 只出现在 CSF/地图 INI/MULTI 相关条目，**都不是图**。

### 2.3 Q2 判定

| 层 | 第三槽是否存在 | 证据 |
|---|---|---|
| 控件 id 1771 代码分支 | ✅ | `0x52EE78..B8`、`0x52F178/189` 等 8 处 `[转引]` Lead + `[本次读码]` 复核 |
| battle 名 `tut1` | ✅ | `[0x825C70]` → `0x825C90 "tut1"` |
| 音效 `BootCampSelect` | ✅ | SOUND.INI #534 + `[0x825C7C]` |
| CSF tooltip `STT:CampaignAnimTutorial` | ✅ | `0x6041FD` + ra2md.csf |
| CSF 描述 `DESC:TUT1` | ✅ | ra2md.csf |
| **独立徽章图（SHP/PCX/位图）** | **❌ 未找到** | 全 MIX 递归 CRC + `.rsrc` 无 RT_BITMAP + WndProc 无加载点 |
| 模板内 `id=1771` 控件 | ❌（需补丁） | 本卡自解 13 项 `[本次实测]` |

`[静态推断]` ⇒ 路线 (c) 的 **资源层静态可行，但视觉层不成立**：补出 1771 控件后引擎会按 id 收消息、查 `tut1`、播 BootCampSelect、显示 `STT:CampaignAnimTutorial` 提示，**但要有第三颗可见徽章必须另造美术并重绘/扩展菜单背景**。`[待运行验证]`。

---

## 3 · 布局（Q3）

### 3.1 引擎是否依赖硬编码坐标（`[本次读码]`）

**不依赖**。三处鼠标处理都走"控件 id"：
- `0x52ED6D..0x52EDAA`：`GetWindowRect(hDlg,&rect)` → `ChildWindowFromPointEx(hDlg, lParam.x-rect.left, lParam.y-rect.top, 1)` → `GetDlgCtrlID(hwnd)`。
- `0x52EEFA..0x52EF33`（`WM_LBUTTONDOWN`）、`0x52F1CF..0x52F20A`（`WM_LBUTTONUP`）同样三连。
- 所有消息收发用 `SendDlgItemMessageA(hDlg, id, …)` / `GetDlgItem(hDlg, id)`（`0x7E1490` / `0x7E14A8`），**参数里没有 x/y**。滑条也只按 `id=0x50F` 取（`0x52F0E5`、`0x52F2A5`）。

⇒ **坐标可自由改**，只要新控件：`WS_VISIBLE`（`0x50000007` 含 `0x10000000` ✓）、`WS_EX_TRANSPARENT=0x20` 一致、不与其它子窗口重叠（`ChildWindowFromPointEx` 的 flag=1 = `CWP_SKIPINVISIBLE`，返回最上层可见子窗）、`id=1771`、类 `#130`、`title=ord 0`、`extra=0`。

**风险 `[静态推断]`**：视觉徽章很可能烘在共享背景图里（§2.2-7），只改控件坐标会产生**点击热区与画面错位**；要对齐必须同步改背景。`[待运行验证]`。

### 3.2 两套可落地方案（对话框 533×369，字体 MS Sans Serif 8pt）

现有占位（`[本次实测]` 本卡自解）：1770 `(125,34) 174×87` → y 34..121；1772 `(125,216) 173×86` → y 216..302；`1959 (4,123) 415×13` y123..136；`1295 (137,140) 140×14` y140..154；`1822 (137,167) 75×12` / `1648 (203,167) 75×12` y167..179；`1820 (449,29) 61×33`；`1038 (425,122) 108×23`；`1109 (421,151) 107×98`；`1684 (425,1) 108×10`；`1670 (425,253)`；`1685 (8,354)`；`1960 (3,304) 420×13`。

#### 方案 1（推荐 / 本卡补丁实际采用，**零移动、零缩小**）

| 控件 | x | y | cx | cy | 改动 |
|---|---:|---:|---:|---:|---|
| 1770 盟军 | 125 | 34 | 174 | 87 | 不动 |
| 1771 教程（新） | **310** | **34** | **110** | **87** | **新增** |
| 1772 苏联 | 125 | 216 | 173 | 86 | 不动 |
| 1295 滑条 | 137 | 140 | 140 | 14 | 不动 |
| 1822 / 1648 | 137 / 203 | 167 | 75 | 12 | 不动 |
| 1959 / 1960 / 1685 / 1038 / 1109 / 1670 / 1684 / 1820 | — | — | — | — | 全部不动 |

- 新控件占 `x=310..420, y=34..121`。逐项核对：**无重叠**（`1820` 从 x=449 起、`1038` 从 y=122 起且 x≥425、`1959` 从 y=123 起、`1109` 从 y=151 起）。
- 代价：新徽章只有 **110×87**（原徽章 174×87），需要缩放或新美术；出现在顶部徽章右侧，三颗不再等宽/不对称。
- 新 item 32 字节：`00 00 00 00 20 00 00 00 07 00 00 50 36 01 22 00 6E 00 57 00 EB 06 00 00 FF FF 82 00 00 00 00 00`。

#### 方案 2（三颗竖排等宽，**需移动 4 个控件**）

| 控件 | 原 (x,y,cx,cy) | 新 (x,y,cx,cy) | 说明 |
|---|---|---|---|
| 1770 | (125,34,174,87) | 不动 | |
| **1771（新）** | — | **(125,125,174,87)** | 落在两徽章之间 y=121..216 空隙 |
| 1772 | (125,216,173,86) | 不动 | y=216..302，与新徽章 y≤212 不重叠 |
| 1295 滑条 | (137,140,140,14) | **(310,140,105,14)** | 缩窄至 105 |
| 1822 GUI:Difficulty | (137,167,75,12) | **(310,167,75,12)** | |
| 1648 GUI:Harder | (203,167,75,12) | **(310,182,105,12)** | 改到下一行，避免与 1109(x≥421) 冲突 |
| 1959 横条 | (4,123,415,13) | **(4,330,415,13)** | 移出 y=125..212 带；与 `1960`(y304..317)、`1685`(y354..366) 均不重叠 |
| 其余 | — | 不动 | |

- 难度三件移到 x=310..415（不与 1109 x≥421 重叠），y=140..194 内互不重叠。
- 代价：改动 4 个既有控件的 DLGITEMTEMPLATEEX 几何（每个 4 个 int16 = 8 字节），仍**无需改任何代码**；但难度区从徽章下方搬到右侧，视觉改动更大。

---

## 4 · `[TUT1]` battle 条目要写什么（Q4）

### 4.1 `Battle::Read_INI 0x46CCD0` 读键行为（`[本次读码]`，`EVIDENCE\deep_stdout.txt`）

`0x81B1A4..0x81B1D8` 的键名字符串（`[本次实测]`）：`Description` / `DebugOnly` / `Scenario` / `FinalMovie` / `CD` / `Battles`，以及 `0x81B18C = " - for debug/testing"`。

| 键 | 调用点 | 读取函数 | 缺省/去向 |
|---|---|---|---|
| `CD` | `0x46CD04` | `0x5276D0` (GetInt) | 默认取 `[ebx+0x98]`（新建对象初值 `-1`，`0x46CEBA`），存回 `[ebx+0x98]` |
| `FinalMovie` | `0x46CD1E` | `0x4757D0` | 默认 `[ebx+0x29C]`（初值 `-1`，`0x46CEC0`），存回 |
| `Scenario` | `0x46CD38` | `0x528A10` (GetString, max 0x200) | 缓冲 `[ebx+0x9C]`；`0x46CD4B` 后 `strupr` |
| `DebugOnly` | `0x46CD58` | `0x5295F0` (GetBool) | 为真 → `0x46CD8F` 分支，读 `Description` 到 0x400 栈缓冲并追加 `" - for debug/testing"`；为假 → `0x46CD67` 读 `Description` 到 `[ebx+0x2A0]` (max 0x80) |
| `Description` | `0x46CD73` / `0x46CD9B` | `0x529160` / `0x528A10` | 存 `[ebx+0x2A0]` |
| `Battles` | `0x46CE17` / `0x46CE41` | `0x526960` / `0x526CC0` | `0x46CE10` 是 `[Battles]` 枚举器，逐条建/查 Battle 对象并 `call [edx+0x64]` = `Read_INI` |

**缺失键后果 `[本次读码]`**：全部是带默认值的读，不崩溃 —— `CD`/`FinalMovie` 缺 → `-1`（`CD=-1` 按 BATTLEMD.INI 注释 = 任意 CD）；`Scenario` 缺 → 空串（对象 `+0x9C` 在 `0x46CF43` 被清 0）；`Description` 缺 → 空串；`DebugOnly` 缺 → false。**但 `Scenario=` 空 = 没有首关地图，战役必不能进图**。故 W37 的"显式写全"建议成立 `[转引]`。

### 4.2 必须写 / 建议写

```
[Battles]
15=TUT1            ; ★必须：否则 0x46CE10 根本不会为该段建 Battle 对象

[TUT1]
CD=2               ; 或 -1（任意 CD）
Scenario=TUT01.MAP ; ★必须：存在且可经 CCFileClass 打开的首关地图
FinalMovie=        ; 官方 14 段全为空，照抄即可
Description=DESC:TUT1   ; ★必须是 CSF 标签；本卡实测 ra2md.csf 已有 DESC:TUT1
; DebugOnly 不要写（或 =no），否则描述会追加 " - for debug/testing"
```

- `[本次实测]` 官方 `BATTLEMD.INI` 的 `[ALL1] Description=DESC:ALL1` / `[SOV1] Description=DESC:SOV1`，`FinalMovie=` 14 段全空；`[转引]` W29/W30/W40：写纯文本会显示 `MISSING:'…'`。
- `[本次实测]` `ra2md.csf` **确实含 `DESC:TUT1`**（`EVIDENCE\csf_check_stdout.txt`），所以 `Description=DESC:TUT1` 不会 `MISSING:`；这是本卡新发现，比"必须自己造 CSF 标签"更有利。
- `[转引]` W33/W28/W37：还要 `MAPSELMD.INI` 阶段登记、地图文件、`SkipMapSelect` 与 `NextScenario` 语义；`tut1` 官方语义是教程战役（CSF 有 `GUI:TutorialCampaign` / `STT:CampaignAnimTutorial`），地图/动画资源是否齐备 **未验证**。
- `[静态推断]` `[Battles]` 追加第 15 条会让全局 Battle 表 Count 14→15（与 `[转引]` W45 的 `battle_cnt 14→15` 同构），`0x46CC90` 才会返回有效下标而非 `-1`。

---

## 5 · 补丁形态与代价（Q5）

### 5.1 本卡真做的补丁（`[本次实测]`）

副本：`work\gamemd_v14r.exe`（**只从 `ra2bench\gamemd.exe` 复制，原件 SHA-256 复核未变**）。
脚本：`work\patch_dlg148.py`；回读：`work\verify_patch.py`（自写资源遍历 + 自写 DLGTEMPLATEEX 解析）；完整性：`work\resource_integrity.py`。
stdout / exit code：`EVIDENCE\patch_stdout.txt` / `patch.exitcode`（0）、`verify_patch_stdout.txt` / `verify_patch.exitcode`（0）、`resource_integrity_stdout.txt` / `resource_integrity.exitcode`（0）。字节 diff：`EVIDENCE\dialog_bytes_diff.txt`（700 行，逐字节 N/C/+ 标注）、`EVIDENCE\dialog_struct_diff.txt`。

| 项 | 原 | 补丁后 |
|---|---|---|
| 文件长度 | 4,825,360 (0x49A110) | **4,825,360（不变）** |
| SHA-256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | **`b9021544a369fc8db77b1d0500de335e703886c5633dadc73c836dee9f891287`** |
| `RT_DIALOG 148` Size | 664 | **696** |
| `cDlgItems` | 13 | **14** |
| 控件数 | 13 | **14**（新 `[13] id=1771 (310,34) 110×87`，`trailing=0`） |
| `.rsrc` VirtualSize | 0x18128 | **0x18148** |
| `DataDirectory[Resource].Size` | 0x18128 | **0x18148** |
| `CheckSum` | 0 | 0（不变） |
| `SizeOfImage` / `.rsrc SizeOfRawData` / `.detour.PointerToRawData` | 0x796000 / 0x19000 / 0x497000 | **全部不变** |

`[本次实测]` 回读列出 14 个控件（`EVIDENCE\verify_patch_stdout.txt`），13 个原控件逐字节不变；`EVIDENCE\resource_integrity_stdout.txt` 进一步验证 **113 个资源全部可解析、112 个（除 148）字节完全一致**、61 个 RVA 修正无遗漏。

### 5.2 确切字节操作（原地插入法）

`.rsrc` 布局（`[本次实测]`）：`RVA=0x77A000`，`PtrRaw=0x47E000`，`VirtualSize=0x18128`，`SizeOfRawData=0x19000`，raw 尾 `0x496128..0x497000` 有 **3,800 字节全零 padding**（`0xED8`）；`RT_DIALOG 148` 数据 `RVA=0x783270 / file 0x487270 / 664 B`，其 `IMAGE_RESOURCE_DATA_ENTRY` 在 `file 0x47EF88`。

1. `dlg+0x010`：`0D 00` → `0E 00`（`cDlgItems` 13→14）。
2. `dlg+0x298`：追加 **32 字节** DLGITEMTEMPLATEEX（`helpID 4 + exStyle 4 + style 4 + x/y/cx/cy 8 + id 4 + class 4 + title 2 + extraCount 2`），`id=1771`、`class=#130`、`title=ord0`、`extra=0`；32 是 4 的倍数，原 blob 长 0x298 已 4 对齐，无需填充。
3. 在 **file `0x487508`（`RVA 0x783508`）** 插入该 32 字节 → 其后所有资源数据整体 `+0x20`。
4. **重排代价**：遍历整棵资源树，对 **`OffsetToData >= 0x783508` 的每个 `IMAGE_RESOURCE_DATA_ENTRY` 的 4 字节 RVA 各 `+0x20`**。本卡实测 **113 个叶中有 61 个**需修正（其余 52 个在插入点之前）。目录表本身全部位于 `0x487270` 之前（本卡 `assert` 验证），其内部"相对资源目录基址"的偏移不需要改。
5. `RT_DIALOG 148` 的数据项：`Size` `0x298→0x2B8`；`OffsetToData` 保持 `0x783270`（在插入点之前，未移动）。
6. `.rsrc` 节头 `VirtualSize`：`0x18128 → 0x18148`。
7. `OptionalHeader.DataDirectory[2].Size`（Resource）：`0x18128 → 0x18148`。
8. **不扩文件**：从 `.rsrc` raw 尾部 3,800 字节零 padding 中吃掉 32 字节（`0x496FE8..0x497000`），从而文件长度、`.detour.PointerToRawData`(=0x497000)、`SizeOfHeaders`、`SizeOfImage` 全部不变。
9. **PE 校验和**：原 `CheckSum=0x00000000` ⇒ 保持 0（用户态 EXE 加载器不校验；驱动/SFC 才需要）。若要求非零，须用 `MapFileAndCheckSum` / `CheckSumMappedFile` 重算后写 `OptionalHeader+0x40`。
10. **无重定位**：镜像无 `.reloc` 节，且 `.text` 中所有绝对地址未动 ⇒ 无需基址重定位修正。

**需要改的 PE 字段清单**：`.rsrc` 节头 `VirtualSize`、`OptionalHeader.DataDirectory[RESOURCE].Size`、1 个 `IMAGE_RESOURCE_DATA_ENTRY.Size`、61 个 `IMAGE_RESOURCE_DATA_ENTRY.OffsetToData`、2 字节 `cDlgItems`、32 字节新 item。`CheckSum` / `SizeOfImage` / `SizeOfRawData` / `PointerToRawData` / `SizeOfHeaders` **不需要改**（本卡方案下）。

### 5.3 更省的替代形态（量化对比）

`[静态推断]` **repoint 法**（本卡未采用，但代价更低）：把新的 696 B 对话模板整体写到 `.rsrc` 尾部零 padding（`RVA 0x792128 / file 0x496128`），只改 **1 个** `IMAGE_RESOURCE_DATA_ENTRY`（`OffsetToData 0x783270→0x792128`、`Size 664→696`），并把 `.rsrc VirtualSize` 与 Resource `Size` 各 `+0x2B8`（696）；**0 个 RVA 重排、0 个其它资源改动**，旧 664 B 变成孤儿数据。文件长度仍可不变（padding 3,800 B ≫ 696 B）。风险更低，但会在 `.rsrc` 里留下 664 B 不可达字节。

| 形态 | 改动点 | 风险 |
|---|---|---|
| 原地插入（本卡实证） | 61 个 RVA + 2 个 Size/VS + 2 字节 + 32 字节 | 漏改任一 RVA ⇒ 其它对话框/菜单/版本资源静默损坏 |
| repoint（推荐给工程实现） | 1 个 data entry + 2 个 Size/VS | 最低；留 664 B 孤儿 |
| 若 `.rsrc` 无 padding | 需 `SizeOfRawData += FileAlignment(0x1000)`、`.detour.PointerToRawData += 0x1000`、文件 `+0x1000`、可能 `SizeOfImage` 重算 | 最大；**本镜像不适用**（有 3,800 B 零 padding） |

⇒ **"无扩展空间"不是本镜像的障碍**：`.rsrc` 有 3,800 B slack，32 B / 甚至 696 B 都放得下。

### 5.4 与版本守卫的冲突（`[转引]` + `[静态推断]`）

SHA-256 由 `73201cc0…67476` 变为 `b9021544…1287`，**任何以该哈希为锚的 verify / seal / 版本守卫都会判定"未知构建"并拒绝**。这是**设计意图、不是 bug**：路线 (c) 要求分发打过补丁的 `gamemd.exe`，等于把"改游戏本体"从禁区拿出来，A 线/B 线所有以原版哈希为锚的对照都要重新定义（`[转引]` `REVIEW\LEAD_CHECK_menu_3slot.md` §4）。还涉及改官方 exe 的合法/分发边界（本机自用 vs 发布），需用户知情。

---

## 6 · 交付清单

| 路径 | 内容 |
|---|---|
| `THIRD_BADGE_ROUTE.md` | 本文件（五问 + 布局表 + 字节操作 + 代价） |
| `work\gamemd_v14r.exe` | 打过补丁的副本（4,825,360 B，SHA `b9021544…1287`） |
| `work\patch_dlg148.py` | 补丁脚本 |
| `work\verify_patch.py` + `work\readback_14.txt` | 自写解析器回读校验（14 控件） |
| `work\resource_integrity.py` | 113 资源完整性交叉校验 |
| `work\w61_dlg.py` | 自写 DLGTEMPLATEEX 解析器（原件 13 控件复核） |
| `work\dlg148_orig.bin` / `dlg148_patched.bin` | 664 B / 696 B 对话模板 |
| `work\CAMPAIGN.PCX` / `CAMPAIGN.png` | 解出的 640×480 背景及渲染图 |
| `EVIDENCE\` | 全部脚本 stdout + `.exitcode` + `dialog_bytes_diff.txt` / `dialog_struct_diff.txt` + `INDEX.md` |
| `UNKNOWNS.md` / `DISAGREE.md` | 未决项 / 与既有件的分歧 |
| `STARTED.txt` / `HEARTBEAT.txt` | 时间戳 + 卡号 + Hy4；心跳 #1–#4 |

---

## 7 · 证据路径（三条主证据）

1. `EVIDENCE\verify_patch_stdout.txt` —— 补丁副本自写解析回读，**14 个控件**、`trailing=0`、1771 几何/类/样式、原/副本 SHA-256。
2. `EVIDENCE\menu_strings_stdout.txt` + `EVIDENCE\mix_recursive_stdout.txt` —— Q2：菜单代码区无图名、全 MIX 递归无第三徽章美术。
3. `EVIDENCE\recon_stdout.txt` + `EVIDENCE\deep_stdout.txt` —— Q1/Q4：`0x52EC00..0x52F3E8` WndProc 全量反汇编、`0x46CC90` / `0x46CCD0` 与 IAT/字符串解析。

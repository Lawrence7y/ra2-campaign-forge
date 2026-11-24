# W61 · UNKNOWNS（未决项 / 本卡边界）

分级：`[待运行验证]` = 需真机；`[静态推断-弱]` = 静态无法闭环；`[未复核]` = 本卡未做。

## U1 · 两颗可见徽章的像素到底由哪个文件/哪一行画出来（Q2 最主要的未决项）
- **已知** `[本次读码]`：WndProc `0x52EC00` 不加载任何图；徽章 STATIC 是 `WS_EX_TRANSPARENT` 空文字控件；`.rsrc` 无 RT_BITMAP；UI 美术由 `GraphicMenu` INI 的 `Image=` / `Highlighted=` 指向 MIX 内 `.SHP`/`.PCX`（`.rdata 0x824080..0x824340` RTTI + `wdt.mix` 的 `[FactionChoiceMenu640]` 实例）。
- **未知**：`RT_DIALOG 148` 这个 Win32 对话框的背景/徽章由哪个具体 SHP/PCX、哪段绘制代码贴上去。本卡尝试过 `0x622650`(`Run_Dialog`)、`0x622800`、唯一 `RegisterClassA` 的 `lpfnWndProc=0x7775C0`、`0x4713xx` 自定义消息区，均未定位到给 1770/1772 上色的确切加载点。
- **失败尝试（留痕）**：`work\CAMPAIGN.PCX` 解出为 640×480×8bpp（76,884 B），`work\CAMPAIGN.png` 渲染后**大面积纯黑 + 右侧两块深色面板**；PCX 自带 256 色调色板与游戏运行时调色板不一致，不能据此断定"徽章烘在背景里"或"徽章是独立叠加层"。`[静态推断-弱]`
- 附带未决：`CAMPAIGN.PCX` 文件名不在 exe 的 403 个文件名字符串表中，也不在 MIX 条目数据里（MIX 索引仅存 CRC）；其运行期名字如何构造（例如 `"Campaign"` + `".PCX"` 拼接）未定谳。`[静态推断-弱]`
- **最小闭环实验**：真机运行补丁副本，用渲染 DLL / 截屏对比"有 1771 控件 vs 无 1771 控件"两版；或在 `0x52F125..0x52F18E` 的 `PostMessageA(0x4D7)` 与 `GraphicMenu` 绘制链下断，记录 `CCFileClass::Get_File(0x473D10)` 请求到的文件名。

## U2 · `0x46CC90` 返回 `-1` 时上层的确切可见后果
- `[本次读码]` 本处无错误分支、无 MessageBox、无降级：`-1` 存入 `GetWindowLongA(hDlg,8)` state 并传到 `0x52DE00` 调用者（写入 `[0xA8B230+0x34CC]`）。
- `[待运行验证]` 上层拿 `-1` 后是静默不进图、越界访问、还是回主菜单，本卡无法静态定谳。

## U3 · 补丁副本是否真能被 Windows 加载并弹窗
- `[本次实测]` 只做了 PE 结构层验证（自写资源遍历 + 自写 DLGTEMPLATEEX 解析 + pefile + 113 资源完整性），**未启动 exe、未加载 DLL、未 `LoadLibrary`**。
- `[待运行验证]` 需真机：`GetLastError`、对话框创建、控件枚举（应看到 14 个，含 1771）、点击 1771 后的行为。
- 特别地本卡采用"吃掉 `.rsrc` 尾部 32 字节零 padding"来保持文件长度；虽然 113 个资源全部校验通过，但**未验证 Windows PE 加载器对 `.rsrc` 尾部/ResourceDir.Size 增长 0x20 的实际接受度**。

## U4 · 第三徽章美术是否以"非文件名可猜"的形式存在
- `[本次实测]` 全 MIX 递归（5,630 容器 / 1,168,759 CRC id）对 `TUT*/BOOT*/BADGE*/EMBLEM*/CAMP3/YURICAMP` 等候选名 0 命中；但 **CRC 反查不是全称证明**：若美术文件名完全不含这些词（例如复用 `CAMPAIGN.PCX` 的某一帧、或某 SHP 的第 3 帧），本方法查不到。
- `[待运行验证]` 需枚举 `GraphicMenu` 定义或抓 `CCFileClass` 请求名。

## U5 · `tut1` 战役的地图 / 动画 / MAPSELMD 链是否齐备
- `[本次实测]` CSF 有 `DESC:TUT1` / `GUI:TutorialCampaign` / `STT:CampaignAnimTutorial`；SOUND.INI 有 `BootCampSelect`。
- `[未复核]` 是否存在 `TUT01.MAP` 之类首关地图、`MAPSELMD.INI` 的教程阶段、`STT:CampaignAnim*` 对应的动画 VQA/SHP 资源。`[转引]` W33/W28/W37 指出战役推进还要过 `MAPSELMD.INI` 阶段校验。

## U6 · 隐藏调试 ListBox（1109）与第三槽的关系
- `[本次读码]` `0x52F007` 取 `GetDlgItem(hDlg,0x455=1109)`，`0x52F00B` 读门控 `[0xA8F7AD]`，置位时 `0x52F028` 用 `[eax+edi*4]` 遍历全局 Battle 表填表（**绕过 `0x46CC90`**）。
- `[转引]` W32/W58：零售态 `LB_GETCOUNT=0`、门控无静态写入者。本卡未复核门控是否被任何运行期写入置位，也未验证第三槽条目是否会出现在这个 ListBox 里。

## U7 · `0x734E60` 的精确语义
- `[本次读码]` 它分配 0x208 字节对象、把名字拷进 `esi+4`、挂到全局链表 `[0xB1CF88]`，返回字符串缓冲；被 `SendMessageA(hwnd,0x4B2,0,ptr)` 用作"设置控件文本/标签对象"。
- `[静态推断-弱]` 具体是 `new StringClass`、`CSF_Get_String` 还是调试跟踪节点，本卡未完全定谳；不影响 Q1–Q5 结论（0x4B2 只作用于 1959/1960 等文本 STATIC）。

## U8 · 版本守卫的具体拒绝点
- `[转引]` 卡面与 `LEAD_CHECK_menu_3slot.md` §4：改 exe ⇒ SHA-256 变 ⇒ "未知构建拒绝"。
- `[未复核]` 本卡没有读 `ra2forge`/`verify` 代码去找确切的拒绝函数与错误码（红线禁止改，纯读亦可但时间盒内未做）。

## 纪律声明
- 全程 **I launched 0 / attached 0**：未启动 `gamemd.exe`、未 attach、未取 `.game_instance.lock`（W55b 可能持锁）。
- 源 `ra2bench\gamemd.exe` SHA-256 在补丁前后复核均为 `73201cc0…67476`（`EVIDENCE\verify_patch_stdout.txt`）；`ra2youli\` / `ra2forge` / `ra2opt` / W21–W60 未写；`git` 只读。
- 本会话**没有注册 REA MCP 工具**（`open_binary` / `analyze_function` 均不可用）；REA skill 的 setup 需要网络与写配置，与"纯离线只读 + 只写本卡目录"冲突，故改用本卡自带的 pefile + capstone + 自写解析器完成，全部脚本与 stdout 落 `work\` / `EVIDENCE\`。

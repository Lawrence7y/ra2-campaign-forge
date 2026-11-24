# W87 · 不改 `gamemd.exe` 恢复战役菜单第三徽章（`id=1771` / `tut1`）静态逆向判决报告

> **唯一问题**：能否在不修改 `gamemd.exe`（必须保持 SHA-256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`）的前提下，让"第三个战役徽章"在战役菜单里真正可见、可点、可进（进而让追加式 DLC 战役在产品层面可见）？  
> **目标镜像**：`work\gamemd.exe`（`4,825,360` B，ImageBase `0x00400000`）与 `work\ddraw.dll`（`411,648` B，SHA-256 `85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9`）。  
> **证据分级约定**：`[本次实测]`（本卡脚本直接输出的字节/反汇编/文件解析）/ `[静态读码]`（引用前序卡片或仓库源码）/ `[静态推断]` / `[未证]`（因禁止运行游戏未动态验证）。

---

## 总结论（Executive Verdict）

| 候选路线 | 判决 | 一句话技术定性 | 核心证据 |
| :--- | :--- | :--- | :--- |
| **R1 运行时改对话框模板**（进程内劫持，经 `ddraw.dll`） | **A · 保持 exe 哈希可行**（附美术/守卫前提） | `gamemd.exe` **不自检 `ddraw.dll`**，L1 `version_guard.py` **不拦截 `ddraw.dll`**；在 `ddraw.dll` 中挂钩 IAT `0x007E1450` (`CreateDialogIndirectParamA`) 并截获 `lpDialogFunc == 0x0052EC00`，可原地复制并追加第 14 项 `id=1771` 到可写内存再创建菜单 `[本次实测]`。**但**「可见」仍需另行解决第三徽章无内置美术的问题 `[静态读码]`。 | `0x006226CB call [0x7e1450]`；`version_guard.py` `L1_FIELDS`；`0x74FDE8` 仅查 exe 自身 `[0xb732f0]` |
| **R2 非 STATIC 类（如 `BUTTON`）第三控件** | **C · 不可行** | (1) `RT_DIALOG 148` 根本没有第 3 控件，不走 R1 或改 exe 连按钮也放不进去；(2) 标准 `BUTTON` 会拦截 `WM_NCHITTEST` (`HTCLIENT`) 导致父窗 `0x52EC00` 收不到 `WM_LBUTTONDOWN`/`WM_LBUTTONUP`；(3) 父窗 `WM_COMMAND` (`0x52ECB1`) **仅处理 `0x40E` 与 `0x686`**，完全不认 `0x6EB` `[本次实测]`。 | `0x52ED60`/`0x52EEFA`/`0x52F1CF` vs `0x52ECB1`；`0x6166EE` 发 `0x111` |
| **R3 复用既有控件（`1820`/`1959`/`1960`）或配置重映射** | **C · 不可行** | 三者均有硬编码引擎职责（`1820` 显式与 `1771` 并列；`1959`/`1960` 为 `all1`/`sov1` 字幕槽）；全二进制 **56** 处 `SetWindowLongA` 中 **0** 处用 `GWL_ID(-12)`；`655,360` B 字符串扫描无任何控件/徽章 ID 重映射配置键 `[本次实测]`。 | `0x46DF98`、`0x602F4F`、`0x60356F`、`0x60866C`、`0x60869E` |
| **R4 对话框外部化机制** | **C · 不可行** | 全部资源 API 仅收敛于 `0x4A3B40`（3 个调用点，只读 `.rsrc`）；全部 4 个对话框创建 API 共 8 个调用点，无一读外部 `.DLG`/INI；`655,360` B 扫描 `DLGTEMPLATE`/`.DLG`/`DIALOG.INI` 等全为 **0 命中** `[本次实测]`。 | `0x4A3B40`、`0x4C8500`、8 处 dialog 创建点 |

**对唯一问题的回答**：**技术上可行（唯一可行路径为 R1，保持 `gamemd.exe` SHA-256 严格不变）** `[本次实测]`，但必须满足两项前提条件：
1. **以 `ddraw.dll`（代理封装或定制分支 `cnc-ddraw`）作为进程内挂钩宿主**：可使 `id=1771` 成为实际子窗口并接入 `0x52EC00` 点击/悬停（需动态确认 `0x52F191` 跳过 `0x4D7` 不影响点击 `[未证]`）。
2. **「可见」需配套视觉呈现方案**：因为 `CAMPAIGN.PCX` 与全 MIX/`.rsrc` 没有第 3 枚徽章美术 `[静态读码]`，仅插入透明 `STATIC` 热区用户看不到图标；最小成本下需由 Mod 侧提供改版 `CAMPAIGN.PCX`（通过 MIX/散装文件加载，不改 exe）或由 `ddraw.dll` / Hook 在热区上绘制文字与边框。同时需接受 **`ddraw.dll`（L2 / `C07`）哈希变更**的工程代价。

---

## 前置实测基线：PE 节表与 `RT_DIALOG 148` 结构 `[本次实测]`

`work\gamemd.exe` PE 节表（来自 `EVIDENCE\r2_r3_r4_deep_stdout.txt`）：
- `.text`: `VA=0x00401000`, `VSize=0x3DF38D`, `RawPtr=0x001000`, `RawSize=0x3E0000`, `Char=0x60000020`
- `.rdata`: `VA=0x007E1000`, `VSize=0x30074`, `RawPtr=0x3E1000`, `RawSize=0x31000`, `Char=0x40000040`
- `.data`: `VA=0x00812000`, `VSize=0x367BE4`, `RawPtr=0x412000`, `RawSize=0x6C000`, `Char=0xC0000040`
- `.rsrc`: `VA=0x00B7A000`, `VSize=0x18128`, `RawPtr=0x47E000`, `RawSize=0x19000`, `Char=0x40000040`
- `.detour`: `VA=0x00B93000`, `VSize=0x2718`, `RawPtr=0x497000`, `RawSize=0x3000`, `Char=0xC0000040`（含 `xyr.dll` 等扩展导入）

直接从 `work\gamemd.exe` 解析 `RT_DIALOG 148`（`Lang=0x0409`, `DataRVA=0x783270`, `foff=0x487270`, `Size=664 B`, `Trailing=0 B`，见 `EVIDENCE\r2_r3_final_check_stdout.txt` L10–28）：
- 头部：`DLGTEMPLATEEX`（`dlgVer=0x0001`, `sig=0xFFFF`, `exStyle=0x00000000`, `style=0x40000040`, `cDlgItems=13`, `rect=(0,0,533,369)`, font `MS Sans Serif 8pt`）。
- 与徽章/文字槽相关的控件项：
  - `Item[01]`: `id=1038 (0x40E)` `cls=#128` (`BUTTON`) `rect=(425,122,108×23)` `style=0x5000000B` (`BS_OWNERDRAW`) `'GUI:Load'`
  - `Item[05]`: `id=1670 (0x686)` `cls=#128` (`BUTTON`) `rect=(425,253,108×23)` `style=0x5000000B` (`BS_OWNERDRAW`) `'GUI:Back'`
  - `Item[07]` @`+0x1C4` (32 B): `id=1770 (0x6EA)` `cls=#130` (`STATIC`) `rect=(125,34,174×87)` `style=0x50000007` (`WS_CHILD|WS_VISIBLE|SS_BLACKFRAME`, **无 `SS_NOTIFY`**) `ex=0x00000020` (`WS_EX_TRANSPARENT`) `title=''`
  - `Item[08]` @`+0x1E4` (32 B): `id=1772 (0x6EC)` `cls=#130` (`STATIC`) `rect=(125,216,173×86)` `style=0x50000007` `ex=0x00000020` `title=''`
  - `Item[10]` @`+0x238` (32 B): `id=1820 (0x71C)` `cls=#130` (`STATIC`) `rect=(449,29,61×33)` `style=0x50000007` `ex=0x00000020` `title=''`
  - `Item[11]` @`+0x258` (32 B): `id=1959 (0x7A7)` `cls=#130` (`STATIC`) `rect=(4,123,415×13)` `style=0x50000001` `ex=0x00000000` `title=''`
  - `Item[12]` @`+0x278` (32 B): `id=1960 (0x7A8)` `cls=#130` (`STATIC`) `rect=(3,304,420×13)` `style=0x50000001` `ex=0x00000000` `title=''`

---

## R1 · 运行时改对话框模板（经 `ddraw.dll` 进程内拦截）

### 判决：**A · 保持 `gamemd.exe` 哈希可行**

### 1. 创建链反汇编与 IAT 槽定位 `[本次实测]`
`EVIDENCE\r1_r2_dialog_helpers.txt` 与 `EVIDENCE\r2_r3_r4_deep_stdout.txt` 完整定位了战役菜单对话框的创建路径：
1. **调用入口**（`.text`）：
   - `0x0052DF48 (RVA 0x12DF48, foff 0x12DF48): ba 00 ec 52 00` — `mov edx, 0x52ec00`（`lpDialogFunc` = 战役菜单窗口过程）
   - `0x0052DF4D (RVA 0x12DF4D, foff 0x12DF4D): b9 94 00 00 00` — `mov ecx, 0x94`（资源 ID = `148`）
   - `0x0052DF65 (RVA 0x12DF65, foff 0x12DF65): e8 e6 46 0f 00` — `call 0x622650`（`Dialog_Create_Helper`）
2. **模板从 `.rsrc` 取出并送入 USER32**（`Dialog_Create_Helper` `0x00622650`）：
   - `0x00622665..0x0062266C`：`mov edx, 5`（`RT_DIALOG`）；`mov ecx, ebp`（`0x94`）；`call 0x4a3b40`（`Load_Resource_Helper`，内部依次调用 `KERNEL32!FindResourceA` `[0x7E122C]`、`LoadResource` `[0x7E1230]`、`LockResource` `[0x7E1228]`，返回 `eax = lpTemplate`）。
   - `0x00622685..0x006226CB`：按序压入 `dwInitParam=&local`、`lpDialogFunc=0x52EC00`、`hWndParent=[0xb73550]`、`lpTemplate=eax`、`hInstance=[0xb732f0]`，并在 **`0x006226CB`** 执行：
     `ff 15 50 14 7e 00` — **`call dword ptr [0x7e1450]`**（`USER32.dll!CreateDialogIndirectParamA`）。
3. **关键 IAT 槽地址**：
   - `USER32.dll!CreateDialogIndirectParamA`：**`0x007E1450`**（仅 2 个调用点：`0x006226CB`、`0x00775755`）。
   - `KERNEL32.dll!LockResource`：**`0x007E1228`**（仅 `0x004A3B6D` 与 `0x007C8428` 跳板）。
   - `DDRAW.dll!DirectDrawCreate`：**`0x007E1048`**（唯一 `ddraw` 导入，`.text` 仅 1 处跳板 `0x007C89D4: ff 25 48 10 7e 00 jmp dword ptr [0x7e1048]`）。

### 2. 进程内改模板可行性与注入点选择 `[本次实测]` + `[静态推断]`
- **为什么必须拦截 `CreateDialogIndirectParamA`（`0x007E1450`）而不是只改 `.rsrc` 页属性**：
  - `LockResource` 返回的 `lpTemplate` 位于 `.rsrc`（`PAGE_READONLY`, `Char=0x40000040`），且原有资源只有 `664 B`，原地向后追加 32 B 会踩踏紧邻的资源节点。
  - 挂钩 **`0x007E1450` (`CreateDialogIndirectParamA`)** 时，Hook 函数直接拿到 `lpDialogFunc` 参数：仅当 **`lpDialogFunc == (DLGPROC)0x0052EC00`** 且模板头校验通过（`dlgVer==1, sig==0xFFFF, cDlgItems==13`）时触发，**零误伤其他对话框** `[静态推断]`。
  - Hook 在堆/栈分配 **696 B** 可写缓冲区：复制原始 664 B，将偏移 `+0x0C` 的 `cDlgItems` 由 `13` 改为 `14`，并在末尾（`664 = 0x298`，天然 4 字节对齐）追加一个 **32 B `DLGITEMTEMPLATEEX`**（`id=1771 / 0x6EB`, `cls=#130` (`0xFFFF, 0x0082`), `style=0x50000007`, `exStyle=0x00000020`, 无标题/extra=0），然后把新指针传入原始 `CreateDialogIndirectParamA`。
  - 随后 `0x0052DF8A..0x0052DF91` 调用 `0x00622800` → `0x00622820`（`EnumChildWindows`）与 `0x0060F9A0` 时，新子窗 `id=1771` 已被 user32 真实创建，会自动被子类化为引擎 `Static` 并参与 `0x52EC00` 的全部命中与初始化流程 `[本次实测]`。

### 3. 由谁拦截：`ddraw.dll` 两条子路与守卫/自检核查 `[本次实测]` + `[静态读码]`
- **`gamemd.exe` 是否自检 `ddraw.dll`？否 `[本次实测]`**：
  - 全文件大小写不敏感扫描 ASCII `"ddraw"` 仅 4 处命中（`foff 0x4109DE`、`0x499322` 导入表名，以及 `0x41FC7C` `"DDRAW.DLL Error code = %08X"`、`0x41FDCC` `"DDraw returnded actual VRAM..."` 日志）；UTF-16LE 命中 **0 处**。
  - `VERSION.dll` 全部 3 个 API（`0x007C89E0`/`86`/`EC`）在 `.text` 仅在 `0x0074FE12..0x0074FE99` 被调用一次；前置 `0x0074FDD4..0x0074FDEF` 取 **`[0xb732f0]`**（`gamemd.exe` 自身 `hInstance`）路径并查询 `\\VarFileInfo\\Translation` 与 `\\StringFileInfo\\%04d%04d\\ProductVersion`（`EVIDENCE\tiny_strings_check.txt`），完全不检查 `ddraw.dll`。
- **仓库版本守卫是否包含 `ddraw.dll`？分两层看 `[静态读码]`**：
  1. **强守卫（L1）`version_guard.py`**：`ra2forge\version_guard.py` 的 `L1_FIELDS` 只包含 `gamemd.exe` 字段，**不含 `ddraw.dll`**；虽然 `S1_REASON_CODES` 预留了 `"DDRAW_IDENTITY_MISMATCH"`，但当前 `classify()` 不拦截 `ddraw.dll`。因此**替换/定制 `ddraw.dll` 可以通过 L1 exe 版本守卫**。
  2. **软守卫/发行基线（L2 `C07`）**：`W38\VERSION_GUARD_CONTRACT.md` 将 `C07` (`ddraw.dll`) 归为 `L2` (`EDITION_LABEL`)；`RE-N00\BASELINE.json` 与 `TRACK_B_gates.json` 登记了 `C07_ddraw_sha256: "85e0f7d5..."` 及 `G5 official_ddraw` 门禁；且 `ra2opt\cddraw.py` 会读取 `ddraw.dll` 的 `VS_VERSION_INFO.FileVersion` 并在用户执行优化器时覆盖更新 `ddraw.dll`。

| 子路 | 实现方式 | 预计工作量 | 技术与工程代价 / 风险 |
| :--- | :--- | :--- | :--- |
| **R1-a：自写转发版 `ddraw.dll`（Shim）+ 改名原版 `cnc_orig.dll`** | 保留原版 `cnc-ddraw`（改名如 `cnc_orig.dll`），编写轻量 C/C++ `ddraw.dll` 转发其 22 个导出（注意 `gamemd.exe` 仅静态导入 `DirectDrawCreate` `[本次实测]`）；在 `DllMain` / 首次 `DirectDrawCreate` 时将 `gamemd.exe` IAT `0x007E1450` 改写为挂钩函数。 | ~1–2 人日（含编译、Wine/Win32 回归） | **优点**：无需维护 `cnc-ddraw` 全量源码与升级冲突，可保留 `FileVersion` 资源字段降低 `ra2opt` 误判。<br>**风险**：多一个外部 DLL 文件；若 `ra2opt\cddraw.py` 覆写 `ddraw.dll` 会把 shim 冲掉；若与系统其他 ddraw wrapper 并存需明确链式加载（见 `UNKNOWNS.md #3`）。 |
| **R1-b：直接修改/重编 `cnc-ddraw`** | Fork `cnc-ddraw` 源码（`work\ddraw.dll` 本身已集成 `.detourc`/`.detourd` 节 `[本次实测]`），在初始化逻辑内直接 Detours/IAT hook `0x007E1450`。 | ~2–3 人日（搭 Win32 MinGW/MSVC 编译链 + 维护私有分支） | **优点**：单文件仍是 `ddraw.dll`，无额外文件名。<br>**缺点**：丢失官方 `cnc-ddraw` 原始签名与上游直接替换升级能力，触发 `TRACK_B_gates.json` G5 / `BASELINE.json` 基线差异，同样会被 `ra2opt\cddraw.py` 覆盖。 |

### 4. 最小落地方案与「可见」补全风险
- **最小落地（首选 R1-a）**：
  1. 编写 32 位 x86 `ddraw.dll` 代理，转发 `DirectDrawCreate` 及其余导出到同目录 `cnc_orig.dll`。
  2. 在 `DirectDrawCreate` 首次执行时（`gamemd.exe` 此时已完成初始化且早于战役菜单打开），`VirtualProtect` 解锁 `.rdata` 的 `0x007E1450`（4 B），原子替换为 `Hook_CreateDialogIndirectParamA`。
  3. 当 `lpDialogFunc == (DLGPROC)0x0052EC00` 时复制模板、`cDlgItems` `13→14`、追加 `id=1771` 项并把可控 `WS_EX_TRANSPARENT` 热区摆到不重叠位置。
  4. **补齐"可见"**：经 Mod `.mix` 或游戏目录散装文件提供带第 3 枚徽章图形的 `CAMPAIGN.PCX`（或扩展 Hotzone 自绘），使 `1771` 在屏幕上既有图又可点、可进 `tut1`。
- **已知风险**：(1) `0x52F191` 未给 `0x6EB` 发 `0x4D7` 的运行时影响尚未动态验证 `[未证]`；(2) `ra2opt\cddraw.py` 覆盖 `ddraw.dll` 的运维冲突 `[静态读码]`。

---

## R2 · 非 STATIC 类的第三控件（改用 `BUTTON`）

### 判决：**C · 不可行**

### 逐段反汇编否证证据 `[本次实测]`
1. **`ChildWindowFromPointEx` 过滤条件核实（确实不按类过滤，但这救不了 `BUTTON`）**：
   - `0x52EC00`（`EVIDENCE\wndproc_52EC00_full.txt`）内共有三处 `ChildWindowFromPointEx` (`[0x7E13B8]`) + `GetDlgCtrlID` (`[0x7E13B4]`)：`WM_NCHITTEST`（`0x52ED60`）、`WM_LBUTTONDOWN`（`0x52EEFA`）、`WM_LBUTTONUP`（`0x52F1CF`），外加基类 `0x622B50` 中的 `WM_NCHITTEST` tooltip 路径（`0x622CCB`）。
   - 以上 4 处全部传入 **`uFlags = 1` (`CWP_SKIPINVISIBLE`)**，未设 `CWP_SKIPTRANSPARENT (2)`，代码中也没有 `GetClassNameA` 或样式过滤。
2. **为什么标准 `BUTTON` 依然彻底走不通（四重断链）**：
   - **断链 1（无中生有前提不成立）**：`RT_DIALOG 148` 共 13 项中不存在 `id=1771`。**仅仅"换控件类"并不产生控件**——要把任何 `BUTTON` 塞进 dialog `148`，依然必须走 R1 运行时改模板或直接改 `gamemd.exe`。
   - **断链 2（Win32 鼠标命中被 `BUTTON` 截胡）**：在 `RT_DIALOG 148` 中，`1770`/`1772` 为 `cls=#130` (`STATIC`) 且 `style=0x50000007`（无 `SS_NOTIFY=0x100`），系统默认 `STATIC` 对 `WM_NCHITTEST` 返回 `HTTRANSPARENT (-1)`，于是鼠标点击才能穿透给父窗口 `0x52EC00` 处理 `0x52EEFA`/`0x52F1CF`。而标准 `BUTTON` 对 `WM_NCHITTEST` 返回 `HTCLIENT (1)` 并自行吞掉 `WM_LBUTTONDOWN`/`WM_LBUTTONUP`。本次反汇编子类化派发器 `0x60F9A0`（`EVIDENCE\r2_subclass_part2.txt`）与 `Button_Style3_Handler`（`EVIDENCE\tiny_strings_check.txt` L173–221）进一步证实：`Button` 点击直接构造 `wParam=(BN_CLICKED<<16)|ctrlId` 并向父窗 `SendMessageA(hwndParent, WM_COMMAND=0x111, ...)`（`0x61678B call dword ptr [0x7e14a4]`），普通 PushButton (`0x612A60`) 更直接交给原系统 `BUTTON` 发 `WM_COMMAND`。
   - **断链 3（`0x52EC00` 的 `WM_COMMAND` 分支完全无视 `0x6EB`）**：`0x52EC00` 处理 `0x111` (`WM_COMMAND`) 的代码块 `0x52ECB1` 执行 `and eax, 0xffff` 后，**仅比较 `0x40E` (1038 `GUI:Load`) 与 `0x686` (1670 `GUI:Back`)**，其余全部 `jne 0x52f3dc` 退出（无任何 `0x6EA`/`0x6EB`/`0x6EC` 处理分支）。
   - **断链 4（子类消息语义错配）**：`0x52F178..0x52F189` 初始化向 `0x6EB` 发送 `0x4D5` 与 `0x4D4`，这些自定义消息仅在 `"Static"` 子类处理器 `0x6153E0`（`0x61545E cmp ebp, 0x4d4; ja 0x615fbd`）中实现，在 `Button` 处理器中不响应。

> 注：即便未来通过 R1 在对话框中注入带文字/自绘的第三控件，也应当继续保持 **`STATIC` 类**（利用 `Static_Handler` 或自绘处理），而不是改成 `BUTTON` 走 `WM_COMMAND`。

---

## R3 · 复用既有控件（`1820` / `1959` / `1960`）与 ID 重映射

### 判决：**C · 不可行**

### 否证证据 `[本次实测]`
1. **三个既有 Static 全部不是闲置空槽**：
   - **`id=1820 (0x71C)`**（`Item[10]` `@(449,29) 61×33`, `style=0x50000007`, `ex=0x20`）：全二进制 `.text` 有 13 处命中；`0x0046DF98`（`EVIDENCE\r2_r3_final_disasm.txt` L1165–1176）用 `GetDlgItem(esi, 0x71c)` 控制其显示/隐藏；更重要的是在 `0x00602F4F..0x00602F92` 与 `0x0060356F..0x00603591`（同 `L1046–1110`）中，**`0x71C (1820)` 与 `(dlg=0x94, id=0x6EA/0x6EC/0x6EB)` 明确并列出现于同一判断函数内**，承担独立动画/UI 控件角色。
   - **`id=1959 (0x7A7)` 与 `id=1960 (0x7A8)`**（`Item[11/12]` `415×13` @`(4,123)`、`420×13` @`(3,304)`）：`0x52F07F..0x52F0E4` 在 `0x497` 初始化期间分别经 `0x4B2` 向 `1959`/`1960` 写入同盟/苏联徽章下方文字；且 `0x0060866C` (`cmp eax, 0x7a7`) 与 `0x0060869E` (`cmp eax, 0x7a8`) 为二者分配并硬编码布局参数 `(10, 0xC6, 0x262)` 与 `(10, 0x1F9, 0x262)`。强行挪用会直接破坏既有徽章标题显示。
2. **不存在不改 exe 的控件 ID 重映射通道（穷举核实）**：
   - 扫描全部 **56 处** `USER32!SetWindowLongA`（IAT `0x007E1470`）调用上下文：**0 处**传入 `GWL_ID (-12)`（仅用于 `0x60FF0D` 写入 `GWL_WNDPROC=-4` 子类化等）。
   - 对只读与数据节 **`.rdata` (`200,704` B) + `.data` (`442,368` B) + `.detour` (`12,288` B) = 共 `655,360` B** 磁盘映射范围，以 ASCII 大小写不敏感与 UTF-16LE 双编码扫描 `ControlID`、`DialogID`、`BadgeID`：**全部 0 命中**（同次扫描正例校验：`DIALOG.PAL` 命中 1 处、`BATTLEMD` 命中 2 处、`BootCamp` 命中 1 处，`EVIDENCE\r2_r3_r4_deep_stdout.txt`）。
   - 若打算借助外部 DLL 在运行时调用 `SetWindowLongA(hCtrl, GWL_ID, 1771)` 篡改控件 ID，既已经依赖 R1 级别的进程内注入能力，又会破坏被挪用原控件，完全不如 R1 直接在模板追加独立第 14 项 `1771`。

---

## R4 · 对话框模板外部化机制

### 判决：**C · 不可行**

### 穷举否证证据 `[本次实测]`
1. **资源读取 API 穷举**：
   - `KERNEL32!FindResourceA`（`0x007E122C`）、`LoadResource`（`0x007E1230`）、`LockResource`（`0x007E1228`）在全镜像各有且仅有 **2 处**引用：全部位于唯一封装函数 **`0x004A3B40`** 内部及 `0x007C8428..0x007C8434` jmp 跳板。`0x004A3B40` 只有 **3 个调用点**：`0x004C8515`、`0x0062266C`、`0x0077572B`。
   - `FindResourceW`、`SizeofResource` 导入与调用数均为空/0。
2. **对话框创建 API 穷举**（全 `.text` 仅 **8 个**调用点，`.detour` 节 **0 处**引用）：
   - `DialogBoxParamA` (`0x007E13D4`): `0x004C8579`, `0x0052D0DF`
   - `DialogBoxIndirectParamA` (`0x007E13D8`): `0x004C8542`（实测 `0x004C8515` 仍是从 `.rsrc` 查 `0xF7` 资源，`Resource found\n` / `Resource not found\n` 后退回 `DialogBoxParamA`）
   - `CreateDialogIndirectParamA` (`0x007E1450`): `0x006226CB`（战役菜单）, `0x00775755`
   - `CreateDialogParamA` (`0x007E1508`): `0x005BC551`, `0x00775B66`, `0x00775CA6`
3. **字符串扫描范围与正例校验**：
   - 在 **`.rdata` (`200,704` B) + `.data` (`442,368` B) + `.detour` (`12,288` B) = 共 `655,360` B** 内，对 ASCII（大小写不敏感）及 UTF-16LE 检索 `DLGTEMPLATE`、`.DLG`、`DIALOG.INI`、`UI.INI`、`MENU.INI`、`DialogTemplate`：**全部 0 命中**（正例校验：`DIALOG.PAL`=1、`BATTLEMD`=2、`BootCamp`=1）。引擎没有从 INI / MIX / 散装文件读取外部对话框模板的通道。

---

## 附件与证据索引

- 既有事实核对：[DISAGREE.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/DISAGREE.md)
- 未证项与最小动态验证：[UNKNOWNS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/UNKNOWNS.md)
- 执行日志：[PROGRESS.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/PROGRESS.md)
- 二进制哈希清单：[file_hashes.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/file_hashes.txt)
- PE / IAT / `.rsrc` 证据：[pe_iat_rsrc_stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/pe_iat_rsrc_stdout.txt)、[r2_r3_r4_deep_stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_r3_r4_deep_stdout.txt)、[r2_r3_final_check_stdout.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_r3_final_check_stdout.txt)
- 对话框创建与 `0x52EC00` / 子类化反汇编：[r1_r2_dialog_helpers.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r1_r2_dialog_helpers.txt)、[wndproc_52EC00_full.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/wndproc_52EC00_full.txt)、[r2_subclass_disasm.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_subclass_disasm.txt)、[r2_subclass_part2.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_subclass_part2.txt)、[r2_r3_final_disasm.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/r2_r3_final_disasm.txt)、[tiny_strings_check.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r03/W87_third_badge_noexe/EVIDENCE/tiny_strings_check.txt)
- 相关前序与版本守卫对照：[VERSION_GUARD_CONTRACT.md](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W38_version_guard_s1/VERSION_GUARD_CONTRACT.md)、[version_guard.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W81_s4_8_guard/ra2forge_patched_v16b/ra2forge/version_guard.py)、[TRACK_B_gates.json](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r02/W81_s4_8_guard/ra2forge_patched_v16b/ra2forge/TRACK_B_gates.json)、[BASELINE.json](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112/RE-N00/BASELINE.json)、[cddraw.py](file:///D:/Project/ra2-campaign-forge/ra2opt/cddraw.py)

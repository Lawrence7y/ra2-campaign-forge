# W40 · 真机判定「散装 `ra2md.csf` 的两条边界」

> run_id `NEXT_RE_20261112_R02` ｜ 执行：W40 subagent ｜ 2026-11-13 18:54–19:16 +08:00
> 真机时段 19:06:40–19:13:20（5 次串行实例，约 6.7 分钟）；总耗时 ≈ 22 min，≤ 60 min 预算
> 写域仅 `lead/next_re_20261112_r02/W40_csf_live/`；实例锁开工认领、收尾恢复 `owner=lead`
> 工具：`W30_csf_capability/ra2forge_patched_v10/ra2forge/{csf,mixlib}.py`、`W39_mapselmd_live2/tools/live_lib.py`（路径重定向）、`W26_dlc_unseal_fix/ra2forge_patched_v9`（verify）

---

## 0 · 结论速览（两条边界）

| # | 边界 | W29 静态预期（[转引]） | 本次真机判定 | 分级 |
|---|---|---|---|---|
| **1** | **结构合法性**：` FSC` 魔数 / 24 字节头可读 | 坏 CSF → `0x734799` 魔数检查失败 → `0x6BD85A` 弹 `Unable to initialize 'ra2.csf'` → 启动失败 | **成立**。4 字节 `XXXX` 坏魔数散装 CSF → 弹出 `Red Alert 2` 三语弹窗（英/德/法）、点「確定」后自然退出 `exit code = 0`、45 s 内无游戏主窗口 | [本次实测]（附加 D） |
| **2** | **标签完整性**：必须含全部 5,211 官方标签 | 「只含我方标签的最小 CSF」→ `0x734799` 检查失败 → 弹框 → **启动失败** | **推翻**。合法魔数 + **仅 1 个标签**的最小 CSF → **正常启动**（19.34 s 到主菜单，无弹窗、无崩溃）；代价是所有官方标签在 UI 上渲染成 `MISSING:'<label>'` | [本次实测]（测试 A） |

> **一句话**：W29 把「边界 1（魔数）」误绑到了「边界 2（标签数量）」上。`0x734799` 检查的是 `" FSC"` 魔数（及头部可读性），**不是**标签数。散装 CSF 必须是**结构合法**的 CSF；是否含全部官方标签只决定 UI 文本是否 `MISSING:`，**不决定能否启动**。
>
> **工程含义**：`install.py` 若要散装投递 `ra2md.csf`，仍应完整克隆官方 5,211 标签再追加，但理由是「不让官方 UI 全部变 `MISSING:`」，**不是**「否则启动失败」。

### 另外三条（与 W30 能力缺口直接相关）

| 命题 | 判定 | 分级 |
|---|---|---|
| 散装 `ra2md.csf` **是否覆盖** `langmd.mix` 内同名文件（W29 C13 / W30 `UNCOVERED.md` §1） | **是，且是「取代」而非「合并」**：A 的 MISSING 洪泛、D 的坏魔数弹框、E 的主菜单按钮文本替换，三趟独立证明引擎读的是散装文件；W29 Q1 端到端定谳 | [本次实测] |
| `Description=` 的 CSF 标签位（W29 硬约束 b / W27 D1） | **生效**：C（纯文本）→ 内存 `MISSING:'W27LIVE two-mission chain probe A1 to A2'`；B（改成 `RA2F:W40TEST`）→ 该 MISSING 文案消失、我方文本驻留内存 | [本次实测] |
| **追加的自定义标签文本是否出现在可见 UI** | **否**（测试 B：`GUI:CampaignMenu` 仍是两徽章 + 7 空槽，截图与 C 逐项一致）→ 按卡面走「退而求其次」。附加 E 用**覆盖官方可见标签**证明 CSF 显示通道本身正确，**但不能冒充**「追加标签显示在 UI」 | [本次实测] |

---

## 1 · 第 0 步：桌面可见性预检（硬性，30 秒内）

**桌面名**：`WinSta0\Default`（`window_station = WinSta0`，`thread_desktop = Default`，`input_desktop = Default`）——与 W27/W39 一致，**不是** W35 失败的 `WinSta0\exebox-…` 隔离桌面。 [本次实测]

| 检查 | 独立探针（启动前） | 启动后 30 s 内 step0（5 次全部） |
|---|---|---|
| `EnumWindows` 顶层窗口数 | 381（19 可见） | 381 / 382 / 383（19–20 可见） |
| `EnumChildWindows` 前 8 个可见窗口的子控件数 | 25 | 14 / 25 / 28 |
| `ImageGrab.grab()` | `OK`，2560×1440 | `OK`，2560×1440 |
| 判据 | `precheck_pass=true` | `enum_ok=true, grab_ok=true, pass=true` |

- 启动前独立探针：`out/desktop_probe_standalone.json`。
- **时机实测**：A 的 WMI 启动 19:06:41.095 → `step0_desktop_precheck` 19:06:42.219（**1.12 s**），远在 30 s 内；B/C/D/E 同样在 launch 后 ~1.1 s。每次启动都在 `wait_for_pid` + `open_proc` 之后立即调用 `L.desktop_precheck()`，失败即 `STEP0_ABORT_DESKTOP_BLOCKED` 终止整卡（未触发）。
- 结论：**预检通过，无需判「环境阻塞」**，继续全部测试。 [本次实测]

---

## 2 · 环境与开工复核

| 项 | 值 | 分级 |
|---|---|---|
| 复用沙箱 | `lead/next_re_20261112_r02/W35_mapselmd_live/sandbox_game`（W39 `live_lib.py:39` 的 `GAME` 常量即此路径；`W39_mapselmd_live2/sandbox_game` **不存在**，卡面路径为口径简写） | [本次读码] + [本次实测] |
| `python -m ra2forge verify --game <sandbox>` | **exit 0**（开工 `out/verify_pre.log`、收尾 `out/verify_final.log`）：`manifest 0.9 / structure OK / package_digest OK / seal OK / files: 4 ok, 0 changed, 0 missing`；2 个历史 orphan 不改退出码 | [本次实测] |
| 散装 `MAPSELMD.INI` | 存在，6,108 B，SHA-256 `11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886`（W39 部署态，**全程未改动**，5 次启动的常量） | [本次实测] |
| 开工前沙箱无散装 `ra2md.csf` | 是（`csf_variants.json: sandbox.loose_ra2md_csf_present=false`） | [本次实测] |
| 官方 CSF 来源 | `langmd.mix` 条目 `id=0xBD835079`（`ts_crc_hash("ra2md.csf")`，因名字长 9 字节需 TS 4 字节尾填充；普通 `crc_hash` 得 `0x42CBEDCB` 取不到）、offset 39216、size **332,973 B**、SHA-256 `1b90bb07…de81f1c`；`ra2bench\ra2md.mix`（25 条目）**不含**此 id；`ra2bench\langmd.mix` / `ra2youli\langmd.mix` / 沙箱 `langmd.mix` 三份逐字节一致；与 W30 `sandbox/extracted/ra2md.csf` 逐字节相同 | [本次实测]（详见 §6 D1） |
| 官方 CSF 严格解析 | version=3, language=9, **num_labels=5,211**, num_strings=5,211, unused=0, 0 warnings, `to_bytes()` 逐字节一致；`DESC:ALL1`=`盟軍戰役 - 愛國者之熱血` | [本次实测] |
| 真目录基线 | `ra2youli`：647 文件 / 1,989,215,270 B / 277 地图类；`RA2MD.INI=c91c6a47…`、`gamemd.exe=73201cc0…`、`ddraw.dll=85e0f7d5…`、`ra2forge_install.json=fe3bdf62…` | [本次实测] |

---

## 3 · 五个 CSF 变体（全部用 W30 `csf.py` 生成并写后读回校验）

| 变体 | 字节 | SHA-256 | 标签数 | 用途 |
|---|---:|---|---:|---|
| `out/official_ra2md.csf` | 332,973 | `1b90bb0756137f46ff529af043fe798d7f1f9fa1713a4110f17e1d674de81f1c` | 5,211 | 官方参考（MIX 提取） |
| **`out/ra2md.csf.minimal`** | **115** | **`74be568dfcbfc2e4180d12639aa5ac5a8aad60256898ce2e90146177dfef49d2`** | **1** | **测试 A**：合法 CSF（`" FSC"` + v3 + language 9），仅 `RA2F:TEST0001 = W40A_MINIMAL_CSF_SINGLE_LABEL` |
| **`out/ra2md.csf.full`** | **333,053** | **`a46596c949c69a72e310091f51d930364dac39660736a319d59bb41c584fd855`** | **5,212** | **测试 B**：完整克隆 + 追加 `RA2F:W40TEST = W40_CSF_LIVE_OK_20261113` |
| `out/ra2md.csf.badmagic` | 4 | `7b346904f63cc07f1d8cc2d88d7dae08a3f088a0e4159d5214c27a6571a51eb4` | — | 附加 D：`b"XXXX"`（W29 §4 实验 A 原样） |
| `out/ra2md.csf.override` | 333,013 | `a009727b102b7fc61865bedb986209722564c51ecf52a2c7900207ac80f055b5` | 5,211 | 附加 E：`GUI:SinglePlayer` 值改为我方文本（覆盖，非追加） |

- 两张主变体的机器可读详情：`out/csf_variants.json`（含 `all_pass=true`、官方 5,211 条逐条保留校验、头部计数 5212/5212）；附加两张：`out/csf_extra_variants.json`；人可读汇总表：`out/CSF_VARIANTS.txt`。
- 变体 B 的 `append_or_set_label(..., verify=True)` 返回 `action=appended`，读回 `num_labels=5212`、`num_strings=5212`、新标签文本逐字节一致、`official_labels_preserved=true`、`new_label_is_last=true`。 [本次实测]

---

## 4 · 逐测试实测记录

判据统一说明：「启动成功」= `GUI:SinglePlayer` 按钮出现且 `game_hwnd` 类为 `Yuri's Revenge`；「弹窗」= `#32770` 对话框 / 可见控件文本含 `Unable to initialize`；「进程退出」= `list_gamemd()` 不再列出该 pid；「退出码」= 进程自然退出后用 `GetExitCodeProcess`（启动时保存的句柄）读取，主动 `WM_CLOSE+taskkill` 关闭的记「不适用」。内存搜索为**只读 RPM**（`OpenProcess(PROCESS_VM_READ|QUERY_INFORMATION)` + `VirtualQueryEx` 分块扫描，约 324 MB / 1,270 regions），无注入/attach 写内存/改 exe。

### 4.1 测试 A · 最小 CSF ⇒ **没崩（推翻 W29 预期）**

| 记录项 | 实测 |
|---|---|
| 投放 | `ra2md.csf.minimal`，投放后 SHA `74be568d…49d2`，115 B；`BATTLEMD98.INI` 保持原样（`61ed5013…53c`） |
| WMI 启动 | `Win32_Process.Create` → `cmd /c cd /d <sandbox> && start "" gamemd.exe`，launcher=38304，gamemd pid=19656 |
| **弹窗文案** | **无**。`startup_outcome=main_menu_ready`，19.34 s；主窗口 `Yuri's Revenge` rect `[0,0,1707,960]` |
| **游戏进程是否退出** | 未自然退出；由本卡 `WM_CLOSE → taskkill → taskkill /F` 关闭（仅自己 pid），`residual_own_pid=0` |
| **退出码** | 不适用（非自然退出；弹窗路径的自然退出码见附加 D：`0`） |
| 可见 UI 文本 | 控件枚举仍是 `GUI:SinglePlayer / GUI:WWOnline / GUI:Network / GUI:Options / GUI:MoviesAndCredits / GUI:ExitGame`（**控件名 ≠ 渲染文本**）；**截图** `screen_w40_A_minimal_main_menu.png` 显示这些按钮全部渲染为 `MISSING:'GUI:SinglePlayer'`、`MISSING:'GUI:WWOnline'`、`MISSING:'GUI:Network'`、`MISSING:'GUI:MoviesAndCredits'`、`MISSING:'GUI:Options'`、`MISSING:'GUI:ExitGame'`，底部 `MISSING:'GUI:Version'` |
| 内存（只读 RPM） | `W40A_MINIMAL_CSF_SINGLE_LABEL\|utf16le = 2`、`RA2F:TEST0001\|ascii = 2` ⇒ **散装最小 CSF 被引擎解析进内存**；`MISSING:\|utf16le = 780`（B/C 仅 13–17）；`DESC:ALL1\|utf16le = 2`，上下文为 `MISSING:'DESC:ALL1'` ⇒ 官方 5,211 条一条都没被提供 |
| 判定 | **启动失败预期不成立**。合法魔数 + 1 标签即可启动；缺标签只造成 UI 文本 `MISSING:` |

> 卡面要求「测试 A 若没崩，照实写，不要为了符合预期而放宽判据」——本卡**未放宽任何判据**：A 用的是 `csf.py` 生成的、魔数/版本/计数/UTF-16LE 值全部合法的最小 CSF（不是 4 字节坏文件），判据仍是「启动失败 + 弹 `Unable to initialize 'ra2.csf'`」，结果为**证伪**。为排除「是不是我们把判据做松了」，附加 D 用 W29 §4 原样的 4 字节 `XXXX` 复现了弹框（见 4.4）。

### 4.2 测试 B · 完整克隆 + 追加 ⇒ 启动成功，但追加文本**不在可见 UI**

| 记录项 | 实测 |
|---|---|
| 投放 | `ra2md.csf.full`（SHA `a46596c9…f855`，333,053 B，**5,212 标签 = 官方 5,211 + 1**） |
| 单变量附加改动 | 为让标签有机会被 UI 引用，沙箱 `BATTLEMD98.INI` 的 `Description=W27LIVE two-mission chain probe A1 to A2` → `Description=RA2F:W40TEST`（385→357 B，SHA `1e443892…b90f`）；**收尾逐字节还原**（`61ed5013…53c`，`byte_identical=true`） |
| 启动 | 成功，19.36 s 到主菜单；`GUI:SinglePlayer` 就绪；战役菜单 `GUI:CampaignMenu` 正常 |
| 可见 UI | 主菜单/战役菜单中文正常（`戰役`、`點選盟軍圖示以開始盟軍戰役。`、`上一頁` 等）；`screen_w40_B_full_main_menu.png` 与 C 主菜单截图 **SHA-256 完全相同**（`982cde29…`）；两张战役菜单截图版面/控件集合逐项一致（视觉核对；SHA 不同 `a67df9bd…` vs `92243aeb…`，为像素级差异）；`GUI:CampaignMenu` 仍只有 2 个官方徽章 + 7 个空槽（W27 已知结论） |
| **该文本是否出现在某处 UI** | **否**。控件文本集合 `GUI:Back / GUI:Blank / GUI:CampaignMenu / GUI:Difficulty / GUI:Harder / Slider3 / Yuri's Revenge` 中无我方文本；截图中亦无 |
| **标签计数** | **5,212**（离线 `read_csf(strict=True)` + 头部 `num_labels=5212` / `num_strings=5212`；官方 5,211 条逐条保留、新标签为最后一条） |
| **是否出现 `MISSING:`** | **可见 UI：否**。内存 `MISSING:\|utf16le = 13`（启动）/ 15（战役菜单），均为 exe 固有格式串 `MISSING:'%hs'.***FATAL***` 与 `TXT_APIMISSING` 等字面量；**无** `MISSING:'RA2F:W40TEST'`，`W27LIVE\|ascii/utf16le` 全部 miss |
| 内存 | `W40_CSF_LIVE_OK_20261113\|utf16le = 6`（如 `....W40_CSF_LIVE_OK_20261113. Service. 20th,` — CSF 字符串表缓冲区，相邻为官方字符串）、`RA2F:W40TEST\|ascii = 2` ⇒ 追加标签被解析 |
| 判定 | **「完整克隆不破坏启动」成立**；**「追加标签文本出现在 UI」不成立** → 依卡面走退而求其次。启动成功**不等于** CSF 显示功能正确，显示另行判（§5） |

### 4.3 测试 C · 负对照（删除散装 CSF）

| 记录项 | 实测 |
|---|---|
| 投放 | 无 `ra2md.csf`（`loose_csf_present=false`），`BATTLEMD98.INI` 原样 |
| 启动 | 成功，19.36 s 到主菜单；战役菜单正常；截图 `screen_w40_C_nocsf_main_menu.png` / `screen_w40_C_nocsf_campaign_menu.png` |
| 内存 | `W27LIVE two-mission chain probe A1 to A2\|utf16le = 2`，上下文 **`MISSING:'W27LIVE two-mission chain probe A1 to A2'`**；`MISSING:\|utf16le = 15/17` |
| 判定 | 沙箱本身没坏；并与 B 形成**单变量对照**：纯文本 `Description` → 生成 `MISSING:'…'`；改成 CSF 标签 `RA2F:W40TEST` 后该 MISSING 文案消失 ⇒ **CSF 标签解析生效**（不是被忽略） |

### 4.4 附加 D · 坏魔数（精确切分边界 1，W29 §4 实验 A 原样复现）

| 记录项 | 实测 |
|---|---|
| 投放 | `ra2md.csf.badmagic` = 4 字节 `XXXX`（SHA `7b346904…1eb4`） |
| 启动 | **失败**：45.06 s 内无 `Yuri's Revenge` 主窗口（`game_window hwnd=null`）；弹出 `#32770` 对话框，标题 `Red Alert 2`，rect `[623,385,1087,576]` |
| **弹窗文案（截图 `screen_w40_D_badmagic_error_dialog_fullscreen.png`）** | `Unable to initialize 'ra2.csf', please reinstall Red Alert.\nKeine Initialisierung von 'ra2.csf' möglich. Bitte installieren Sie Red Alert erneut.\nInitialisation de 'ra2.csf' impossible. Veuillez réinstaller Red Alert.`（英/德/法三语）；按钮「確定」 |
| **游戏进程是否退出 / 退出码** | 点「確定」后 **0.53 s 自然退出**，`GetExitCodeProcess = 0`；`list_gamemd()` 不再含 pid 14384 |
| 判定 | W29 的 `0x734799 " FSC"` → `0x6BD85A` MessageBox 分支**真机成立**；触发条件是**魔数/结构非法**，与标签数量无关 |

### 4.5 附加 E · 覆盖官方可见标签（显示生效的正对照）

| 记录项 | 实测 |
|---|---|
| 投放 | `ra2md.csf.override`：完整官方 5,211 标签，**把 `GUI:SinglePlayer` 的值由「單人遊戲」覆盖为 `W40_CSF_LIVE_OK_20261113`**（`action=updated`，标签数仍 5,211，仅 1 个值变化） |
| 启动 | 成功，19.34 s 到主菜单 |
| **显示** | **截图 `screen_w40_E_override_main_menu.png`：主菜单第一个按钮真的渲染出 `W40_CSF_LIVE_OK_20261113`**，其余按钮仍是正常中文（網際網路 / 網路 / 動畫及製作人員 / 選項 / 退出遊戲 / 版本 1.001） |
| 内存 | `W40_CSF_LIVE_OK_20261113\|utf16le = 2`，上下文 `網路網路........!.A.W40_CSF_LIVE_OK_20261113....A.!.工...`（CSF 表中该标签的相邻官方字符串） |
| 判定 | **散装 CSF 的值确实驱动 UI 渲染** ⇒ 散装优先于 MIX 内同名文件、且不是「只解析不生效」。**但这是覆盖官方可见标签，不是「追加的自定义标签出现在 UI」** |

---

## 5 · 显示是否生效 —— 单独判定（严禁把「启动成功」写成「CSF 功能正确」）

| 层次 | 判定 | 证据 |
|---|---|---|
| L1 引擎是否读散装 `ra2md.csf`（而非 MIX 内那份） | **是** | A：`MISSING` 洪泛 + 我方标签进内存；D：坏魔数直接弹框；E：官方按钮文本被改；三趟独立、互不依赖 |
| L2 散装 CSF 是否被解析为字符串表 | **是** | A/B/E 的我方文本 `\|utf16le` 命中，且位于 CSF 字符串表缓冲区（相邻为官方字符串） |
| L3 自定义**追加**标签（测试 B 的 `RA2F:W40TEST`）是否出现在**可见 UI** | **否** | B 战役菜单控件文本 + 截图与 C 完全一致；W27 已定谳 `GUI:CampaignMenu` 只呈现 2 个固定 side 徽章，追加 battle id 不生成可选条目，其 `Description` 无可见承载位置 |
| L4 CSF 显示通道本身是否正确 | **是** | E：覆盖官方可见标签 → 主菜单按钮渲染我方文本；C vs B：`MISSING:'W27LIVE…'` 消失 |
| L5 对 `install.py` 的含义 | 散装 CSF 可独立生效（无需 MIX 内同名条目），但**完整克隆是 UI 质量要求而非启动前提**；追加标签的文本要可见，需先解决战役菜单条目可达性 | [本次实测] + [转引] W27 §3 |

---

## 6 · 对上游结论的裁决

### 6.1 W29（`W29_override_order/OVERRIDE_ORDER.md`）

| W29 条目 | 裁决 |
|---|---|
| Q1「散装优先于 MIX、磁盘命中即跳过 MIX 查询」、C13「端到端待运行验证」 | **定谳成立**（A/D/E 三趟真机）。W29 标 `[待运行验证]` 的这半条可以结案 |
| §1.5 `0x7346A0` 把 `"ra2md.str"` 拼成 `"ra2md.csf"` 并走 `Get_File`、§1.5 `0x734799 cmp " FSC"`、§4 实验 A（4 字节 `XXXX` → 弹框） | **成立**（D 实测三语文案与 `0x6BD85A` 预期逐字一致） |
| **§0 硬约束 (a) 与 `DISAGREE.md` D6「散装 CSF 必须完整（含全部官方标签），只放自定义标签的补丁式 CSF 会 `0x734799` 失败 → 弹框启动失败」** | **部分推翻 / 需勘误**：合法魔数 + 1 标签照样启动（A）；「完整」不是启动条件。`0x734799` 检查魔数，不检查标签数。正确表述见 §0 表 |
| §4 实验 B「完整 CSF + 自定义标签 + `Description=DESC:MYCAMP` → 显示 `W29_LIVE_OK`」 | **未由本卡证成**：本卡 B 用追加标签 `RA2F:W40TEST` + 追加战役 `RA2F1`，该条目在 `GUI:CampaignMenu` 不可选 ⇒ 文本未显示。W29 假设「战役条简介」有可见承载位置，与 W27 的菜单实测冲突。E 证明 CSF 通道正确，但那用的是官方可见标签 |

### 6.2 W30（`W30_csf_capability`）

| W30 条目 | 裁决 |
|---|---|
| `UNCOVERED.md` §1「散装 `ra2md.csf` 是否覆盖 `langmd.mix` 内同名文件、及是否真正替换 `Description` 而非 `MISSING:'…'`，必须真机实测」 | **已覆盖**：覆盖成立；`Description` 标签位解析成立（B vs C 单变量对照）。**唯一未闭合的是「让该文本出现在可见 UI」**，卡在 W27 的菜单可达性，不卡在 CSF |
| `UNCOVERED.md` §2「`install.py` 未把 csf 写入游戏目录」 | 仍未改（本卡纯验证卡，不改工具链）；但真机前提已具备，建议后续卡接线 |
| `csf.py` 的解析 / 写出 / `append_or_set_label()` 写后读回校验 | 本卡 5 个变体全部用其生成并严格读回：**能力与文档一致，未发现缺陷**（`all_pass=true`） |

### 6.3 卡面自身的一处路径笔误

- 卡面 §1 测试 B 第 1 步写「从 `ra2bench\ra2md.mix` 取官方 CSF」。`[本次实测]`：`ra2bench\ra2md.mix`（204,527,696 B，25 条目）**不含** `id=0xBD835079`；官方 `ra2md.csf` 在 **`langmd.mix`**（84,643,206 B，10 条目，offset 39216，332,973 B）——与 W30 `CSF_CAPABILITY.md` §1、`DISAGREE.md` §1 一致。本卡按实测从 `langmd.mix` 提取，并与 W30 已提取副本逐字节比对通过。详见 `DISAGREE.md` D1。

---

## 7 · 纪律、自愈与零改动自证

| 项 | 结果 |
|---|---|
| 单实例锁 | 开工 `owner=w40`（19:06:40）、附加实验 `owner=w40-extra`（19:12:04），收尾 **`owner=lead`**（`lock_restored` 19:08:19 / 19:13:20） |
| 启动方式 | 5 次全部 `Invoke-CimMethod Win32_Process Create`（`cmd /c cd /d <sandbox> && start "" gamemd.exe`），`launch_wmi` retval=0；每次 `pre_launch_guard` 均为 0 残留 |
| 禁止项 | 未注入 / 未 attach 写内存 / 未改 exe / 未下断点；仅只读 RPM（`PROCESS_VM_READ|QUERY_INFORMATION`）、`EnumWindows/EnumChildWindows`、`ImageGrab`、普通 UI 输入（`BM_CLICK` / `keybd_event`） |
| `finally` 自愈 | 每次 `run_one` 的 finally + 全局 finally：关游戏（`WM_CLOSE → taskkill → /F`，仅自己 pid）→ 确认 `gamemd.exe` 残留 **0** → 从 `out/pristine_*` 逐字节还原 `RA2MD.INI` / `ddraw.ini` / `RA2MD.INI.benchbak`（`all_match=true`）→ 校验 `gamemd.exe`/`ddraw.dll` 未改 → 移除投放的 `ra2md.csf` → 还原 `BATTLEMD98.INI` → `kind=meta_end` → 还原锁 |
| 最终沙箱状态 | `ra2md.csf` **<ABSENT>**；`MAPSELMD.INI=11cc1cac…`、`RA2MD.INI=c91c6a47…`、`ddraw.ini=c983abad…`、`BATTLEMD98.INI=61ed5013…`、`BATTLEMD.INI=7e40691a…`、`gamemd.exe=73201cc0…`、`ddraw.dll=85e0f7d5…`；`Get-Process gamemd` = **0** |
| `verify` | 开工 `verify_pre.log` exit 0；收尾 `verify_final.log` exit 0（seal OK，4 文件全 ok） |
| **真目录零改动自证** | `REAL_DIR_PROOF.txt`：`PRE/POST file_count=647 total_bytes=1989215270 maplike_count=277`、`added=0 removed=0 changed=0`、**`IDENTICAL_TREE=True`**；4 个关键哈希与卡面基线逐字一致 |

---

## 8 · 证据索引（全部在 `W40_csf_live/`）

```
LIVE_RESULT.md                 本文件
UNKNOWNS.md / DISAGREE.md      未覆盖 / 分歧
REAL_DIR_PROOF.txt             真目录零改动自证（diff_real.py 生成）
out/
  CSF_VARIANTS.txt             5 个变体的 SHA-256 / 字节 / 标签数（人可读）
  csf_variants.json            两张主变体 + MIX 探测 + 全部校验（all_pass=true）
  csf_extra_variants.json      附加 D/E 变体详情
  official_ra2md.csf           MIX 提取的官方参考（332,973 B / 5,211）
  ra2md.csf.minimal            测试 A 变体（115 B / 1）
  ra2md.csf.full               测试 B 变体（333,053 B / 5,212）
  ra2md.csf.badmagic           附加 D（4 B）
  ra2md.csf.override           附加 E（333,013 B / 5,211）
  verify_pre.log / verify_final.log
  real_pre.json / real_post.json
  desktop_probe_standalone.json
  w40_A_minimal.ndjson / w40_B_full.ndjson / w40_C_nocsf.ndjson
  w40_D_badmagic.ndjson / w40_E_override.ndjson
  w40_meta.ndjson / w40_extra_meta.ndjson   （含 kind=meta_start / meta_end / lock_restored）
  live_results.json / live_extra_results.json / live_summary.json
  w40_live_stdout.txt / w40_extra_stdout.txt / live_summary_stdout.txt
  BATTLEMD98.INI.asbuilt / pristine_*      （逐字节还原源）
  screen_w40_A_minimal_main_menu.png        ★ MISSING 洪泛（边界 2 视觉证据）
  screen_w40_B_full_main_menu.png
  screen_w40_B_full_campaign_menu.png       ★ 与 C 一致：追加文本不在 UI
  screen_w40_C_nocsf_main_menu.png
  screen_w40_C_nocsf_campaign_menu.png
  screen_w40_D_badmagic_error_dialog_fullscreen.png  ★ 三语弹窗（边界 1 视觉证据）
  screen_w40_E_override_main_menu.png       ★ 主菜单按钮渲染我方文本（显示生效）
tools/
  live_lib.py                  W39 live_lib 的路径重定向 + get_exit_code/dismiss_dialog
  w40_live.py                  A/B/C 主驱动（step0 门、finally 自愈）
  w40_extra.py                 D/E 附加驱动
  prep_csf.py / prep_extra.py  变体生成 + MIX 提取 + 严格校验
  desktop_probe.py / manifest.py / diff_real.py / summarize_live.py
```

复跑（需在 `WinSta0\Default` 可见桌面、锁空闲、无 `gamemd.exe` 残留时）：

```powershell
cd D:\Project\ra2-campaign-forge
python lead\next_re_20261112_r02\W40_csf_live\tools\prep_csf.py
python lead\next_re_20261112_r02\W40_csf_live\tools\prep_extra.py
python lead\next_re_20261112_r02\W40_csf_live\tools\w40_live.py
python lead\next_re_20261112_r02\W40_csf_live\tools\w40_extra.py
python lead\next_re_20261112_r02\W40_csf_live\tools\summarize_live.py   # 仅汇总 A/B/C 三个主 ndjson；D/E 见 w40_extra_stdout.txt / live_extra_results.json
```

> 复跑前请确认：可见桌面 `WinSta0\Default`、实例锁 `owner=lead`、无 `gamemd.exe` 残留、真目录与沙箱基线哈希未漂移。

---

## 9 · 分级口径说明

- **[本次实测]**：本卡在可见桌面启动 `gamemd.exe` 后由截图、控件枚举、只读 RPM、`GetExitCodeProcess`、文件哈希直接取得的证据。
- **[本次读码]**：本卡阅读 W27/W29/W30/W39 的交付文档与源码得到的路径/常量（如 `GAME = W35_mapselmd_live/sandbox_game`）。
- **[静态推断]**：W29 对 `gamemd.exe` 的字节/分支分析（本卡只复核其结论，未重跑反汇编）。
- **[转引]**：卡面转引的 W29/W30 结论，以及 W27 的既有真机结论（`GUI:CampaignMenu` 只有两徽章）。
- **[待运行验证]**：本卡未覆盖的项，见 `UNKNOWNS.md`。

> **不夸大声明**：本卡没有证明「追加自定义战役的简介一定不可见」（只在 `GUI:CampaignMenu` 一屏、本分辨率、本汉化版本下穷举控件与截图）；也没有证明「任何结构合法但内容畸形的 CSF 都能启动」（只测了 1 标签 / 完整克隆 / 4 字节坏魔数三种）。E 是**覆盖官方标签**的额外变体，不能替代测试 B 的「追加标签显示」判据。

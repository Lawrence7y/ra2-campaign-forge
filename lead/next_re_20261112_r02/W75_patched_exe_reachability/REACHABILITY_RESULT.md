# W75 · 菜单第三条目「运行期可达性」实测结果

> 执行者 **Hy4**（W75，非 Lead）｜STARTED `2026-11-14T02:21:42.5771082+08:00`｜FINALIZE `2026-11-14T02:37:58+08:00`
> 时间盒 110 min，实际用时 ≈16 min
> 任务：把「菜单第三条目可达性」从**静态可行**推进到**运行期可加载/可响应**
> **本卡只回答「能不能加载 / 能不能响应」，不回答「能不能用」**
> 证据分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`

---

## 0 · 判定（三选一）

> ## ✅ **`运行期可达（能加载、有热区、链路通）`**
>
> `[本次实测]` 补丁 `gamemd.exe` 能正常启动、`GUI:CampaignMenu` 能正常渲染、
> `EnumChildWindows` 里**确实多出 `id=1771` 控件**、hover 触发
> `STT:CampaignAnimTutorial` 文案并把 `[0xA8F7A8]` 置为 `0x6EB`、
> 点击热区后引擎**有响应**（静默退回上一級菜单），**全程无崩溃、无错误框、无资源加载错误**。
>
> **但必须连带的限定**：`运行期可达` **≠** `可用`。第三徽章**没有独立美术**
> （画面上仍是两枚徽章，新增的是一个透明热区）；`tut1` 不在 `BATTLEMD.INI`
> 的 battle 表里 ⇒ `0x46CC90` 查表失败 ⇒ 点击后**没有进入任何战役**
> （`frame=0`、`mode=0`、`Scen+0x125C=""`），只是静默退回。
> 本卡**没有**、也**不得**写出「第三徽章可用」这类表述。

> ### ★ 明确声明：**本结论不改变路线 (c) 的冻结裁决**
> `LEAD_RULING_C_line_route_a_first.md` 已把路线 (c) 冻结为
> 「能力已验证、产品不做」（门 1 徽章图来源未解 / 门 2 分发改过的 exe 与版本守卫冲突
> / 门 3 第三徽章美术可造）。本卡**不改这个裁决**，只是按任务卡要求
> 把「可达性」从静态可行测到底 —— 结论是「可达」，但「可达」恰恰**不解除**
> 三个门：能加载、能响应，仍然没有图、没有 `tut1` 战役数据、仍然要分发改过的 exe。
> 本卡不构成对路线 (c) 的解冻提议。

---

## 1 · 四问逐条

### Q1 · 补丁 exe 能否正常加载菜单？有没有崩溃 / 异常 / 资源加载错误？

**答：能加载，且完全没有崩溃 / 异常 / 资源加载错误。**

| 观测 | TRIP A（补丁 exe） | 证据级别 |
|---|---|---|
| WMI `Win32_Process.Create` | `retval=0`，`launcher=39352` → `pid=32364` | `[本次实测]` `out/tripA.ndjson` `launch_wmi`/`pid_found` |
| 启动 3 s 后 | `alive=true`, `exit_code=259` (STILL_ACTIVE) | `[本次实测]` `early_alive_check` |
| 主菜单 | 19.12 s 后 `GUI:SinglePlayer` 出现，窗口 `Yuri's Revenge` `[0,0,1707,960]` | `[本次实测]` `main_menu_ready` |
| 导航链 | `GUI:SinglePlayer` → `GUI:NewCampaign` → `GUI:CampaignMenu` 三次 `PostMessageW(BM_CLICK)` 全成功 | `[本次实测]` `click` / `wait_text_found` |
| 菜单渲染 | 两枚徽章 + 中文说明 + 難度滑條 + 戰役列表 + 「上一頁」全部正常 | `[本次实测]` `out/screen_tripA_campaign_menu.png` |
| 点击热区后 | `process_alive=true`, `exit_code=259` | `[本次实测]` `after_click_state` |
| 错误框 | 无 MessageBox / 无 `GUI:OK` / 无 `Unable…`；`#32770` 是引擎自带的空标题对话框容器（两趟都有，非错误框） | `[本次实测]` `controls_tripA_after_click.json` + 全屏截图 |
| 崩溃日志 | `except.txt` / `ra2render.log` **大小与 SHA-256 全程零变化** | `[本次实测]` `log_delta changed={except.txt:false, ra2render.log:false}` |
| OS 级错误 | 全屏 `screen_tripA_after_click_desktop.png` 无系统错误框 | `[本次实测]` |

> 特别说明（这是任务卡点名的关键风险）：W61 的补丁把 `.rsrc` 内
> **61/113 个 `IMAGE_RESOURCE_DATA_ENTRY.OffsetToData` 平移 +0x20**，
> 改资源目录很容易导致运行期资源加载失败。**本次实测未复现该风险**：
> 对话框、字符串（CSF）、滑条、列表、按钮、图标类资源在运行期全部正常解析。

### Q2 · `EnumWindows` / `EnumChildWindows` 里是否存在 `id=1771` 的控件？

**答：存在，且它就是两趟之间唯一的控件差异。**

`[本次实测]` `out/controls_tripA.json`（TRIP A，进到 `GUI:CampaignMenu` 后枚举）：

```
n_controls=19  n_visible=14  has_1771=true  count_1771=1
ctrl_ids = [0,1038,1109,1295,1648,1670,1684,1685,1770,1771,1772,1820,1822,1959,1960]
1771 : hwnd=16453668  cls=Static  text=""  visible=True  rect=[310,37,421,132]  ctrl_id=1771
1770 : hwnd=1314182   cls=Static  text=""  visible=True  rect=[94,39,326,130]   ctrl_id=1770
1772 : hwnd=10162422  cls=Static  text=""  visible=True  rect=[94,243,326,334]  ctrl_id=1772
```

`[本次实测]` `out/controls_tripB.json`（TRIP B，原版 exe，同一坐标同一流程）：

```
n_controls=18  n_visible=13  has_1771=false  count_1771=0
ctrl_ids = [0,1038,1109,1295,1648,1670,1684,1685,1770,1772,1820,1822,1959,1960]
```

`[本次实测]` `out/AB_COMPARISON.json` `control_delta`：
`ids_only_in_A = [1771]`，`ids_only_in_B = []`；
`n_controls` 19↔18、`n_visible` 14↔13，**各恰好差 1**。
⇒ **第 14 个 DLGITEM 真的被 `CreateDialogIndirect*` 创建成了真实子窗口**，
且差异**唯一地**来自 exe 补丁，不是环境。

`[本次实测]` 几何：1771 的 `GetWindowRect` = `[310,37,421,132]`（111×95），
与 W61 补丁模板写入的 `(310,34) 110×87` 一致到几个像素（对话框单位→像素换算），
中心 **(365,84)**。该中心落在 1770 右边界 `x=326` 之外
⇒ 鼠标命中 1771 而非盟军徽章（另由 Q3 的 `[0xA8F7A8]=0x6EB` 独立确证）。
`[静态推断]` 1770/1771 在 x=310..326 有约 16 px 重叠，但中心不重叠，不影响命中判定。

### Q3 · 探热区：tooltip / 点击后状态 / `Scen` 读数 / `[0xA8F7A8]`

#### (a) Tooltip —— **有，且确证是 `STT:CampaignAnimTutorial`**

`[本次实测]` 把鼠标移到 (365,84) 停 2.2 s 后：
- `out/screen_tripA_campaign_menu.png` 底部状态栏**空白**
- `out/screen_tripA_hover_tooltip.png` 底部状态栏出现 **「執行教學任務。」**
- `out/screen_tripB_hover_tooltip.png`（原版、同坐标）底部状态栏**仍空白**

`[本次实测]` `out/CSF_TOOLTIP_MATCH.json`：把 W61 `EVIDENCE/csf_values.txt` 里
`STT:CampaignAnimTutorial` 的 mojibake 按 CSF 混淆逆变换
（UTF-16LE 每字节 XOR 0xFF）还原，得到**恰好**「執行教學任務。」（7 字符，
与 W61 记录的 `len=7` 一致）。同时还原出
`STT:CampaignAnimAllied`=「開始盟軍故事戰役。」、
`STT:CampaignAnimSoviet`=「開始蘇聯戰役。」、
`STT:AlliedCampaignIcon`=「點選盟軍圖示以開始盟軍戰役。」（即徽章下方常驻黄字）。
⇒ 屏幕上的新文字**只能是 id=1771 的 tooltip**，不是盟军的。

`[本次实测]` 同时 `[0xA8F7A8]` 由 `0` 变为 **`1771 = 0x6EB`**
—— `W61 THIRD_BADGE_ROUTE.md` §1 `[本次读码]`：`0x52EEA8 mov dword ptr [0xa8f7a8],0x6eb`
只在 1771 分支出现。两条独立证据（CSF 文案 + 选择变量）共同证明
**ID 分派链（`0x6041E5` tooltip dispatcher / `0x52EE78..B8` 分支）在运行期是通的**。

`[本次实测]` 原生 tooltip 窗口 `tooltip_candidates=[]`（两趟皆然）——
RA2 的提示是引擎自绘在游戏画面底部状态栏，**不是** `tooltips_class32` 原生窗口。
所以判据用截图 + CSF 还原 + 内存变量，而不是窗口枚举。

#### (b) 点击后有没有崩溃 / 错误框 —— **没有；静默失败**

`[本次实测]` `real_mouse_click(365,84)` 后：
- `process_alive=true` / `exit_code=259`（未退出）
- 无 MessageBox、无 `GUI:OK`、无 `Unable…` 错误串；全屏截图无 OS 错误框
- `except.txt` / `ra2render.log` SHA-256 零变化（没写崩溃日志）
- `out/screen_tripA_after_click.png`：菜单控件消失、背景变红色地形纹理（过渡态）
- `out/screen_tripA_after_click_late.png`：**回到「單人遊戲」主菜单**
  （新戰役／載入儲存遊戲／遭遇戰／主選單），`n_controls` 19→13

⇒ 点击**被响应了**（画面状态改变、退回上一級），但**没有进入任何战役**、
**没有错误框**。这正是 `[转引]` W58 / `LEAD_CHECK_menu_3slot.md` 预测的
「`0x46CC90("tut1")` 返回 -1、此处无错误串、无降级、无 MessageBox」的
**运行期实证**。注意 `[静态推断]` 它不是「完全无反应」：引擎确实走了一段
过渡并退回菜单，只是没有可见的失败提示。

`[本次实测]` TRIP B 同坐标点击：`n_controls` 保持 18、画面**停留在战役菜单**
（`screen_tripB_after_click_late.png`），`sel_ctrl_id` 全程 0 ⇒ 原版在该坐标
无对应控件，什么都没发生。两趟行为差异再次确认来自补丁。

#### (c) `Scen+0x34CC`（BattleIdx）/ `Scen+0x125C` / `[0xA8F7A8]` 的实际值

`[本次实测]` 原始读数见 `out/scen_readings_tripA.ndjson` / `out/scen_readings_tripB.ndjson`
（每趟 6 个采样点：baseline / after_hover / after_click_t0..t3，全部 `ReadProcessMemory` 只读）。
`[本次实测]` `out/AB_COMPARISON.tsv` 为逐点对照表。

| 采样点 | A `[0xA8F7A8]` | A `Scen+0x34CC` (i32 / hex) | A `Scen+0x125C` | B `[0xA8F7A8]` | B `Scen+0x34CC` | B `Scen+0x125C` |
|---|---|---|---|---|---|---|
| campaign_menu_baseline | `0` (`0x0`) | **-1** / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |
| after_hover | **`1771` (`0x6eb`)** | -1 / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |
| after_click_t0 | `1771` (`0x6eb`) | -1 / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |
| after_click_t1 | `1771` (`0x6eb`) | -1 / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |
| after_click_t2 | `1771` (`0x6eb`) | -1 / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |
| after_click_t3 | `1771` (`0x6eb`) | -1 / `0xffffffff` | `""` | `0` (`0x0`) | -1 / `0xffffffff` | `""` |

两趟共同的其他读数（`[本次实测]`）：
`frame=0`、`mode=0`、`battle_cnt=15`、`scen_end_of_game=0`、
`scen_skip_mapsel=0`、`scen_stage_idx=0`、`hover_sound=0xffffffff(-1)`。
`scen_ptr`：A=`63421304`，B=`64011128`（均为有效 ScenarioClass*；
所有 `Scen+off` 读取都成功返回非 None，故偏移读数可信）。

> ### ⚠ 必须诚实收窄的一点（不能夸大）
> **`Scen+0x34CC` 在「进入战役菜单的基线」就已经是 -1（`0xffffffff`）**，
> 点击前后**没有观察到任何变化**；`Scen+0x125C` 全程为空串。
> ⇒ 本趟**不能证明**「点击把 BattleIdx 写成 -1」这个写动作发生了
> （因为基线已是 -1，无法区分「被写入」与「本来就是」）。
> 能写的是：**点击后 `Scen+0x34CC` 仍为 -1、`Scen+0x125C` 仍为空，
> 未被改成任何异常值，也未进图**；`[转引]` W58 担心的「静默传 -1」路径
> 在运行期表现为**无错误框 + 退回菜单**，而不是可见的数据破坏。
> 若要把「写入 -1」这一动作钉死，需在点击瞬间做更密采样或设断点 ——
> `[待运行验证]`，本卡未做（授权内不写目标进程）。

#### (d) `[0xA8F7A8]` 是否被设成 `0x6EB`

**是。** `[本次实测]` TRIP A hover 后由 `0` → `1771 = 0x6EB`，并在
点击后 t0/t1/t2/t3 **持续保持 `0x6EB`**（未被点击处理清零）。
TRIP B 全程 `0` ⇒ 该变量确实由 1771 分支写入，与 `[转引]` W61 §1 一致。

### Q4 · 两趟对照：差异是否来自补丁而不是环境

**答：是，且差异精确、唯一。** `[本次实测]` 见 `§2` 对照表与
`out/AB_COMPARISON.json` / `out/tripA.log` / `out/tripB.log`。

控制变量：同一沙箱目录（同一 `robocopy` 副本）、同一 28 项可写配置基线、
同一启动命令、同一导航序列、同一热区屏幕坐标 **(365,84)**、
同一观测脚本、同一台机器同一桌面（`WinSta0\Default` / `EnumWindows=412` /
`ImageGrab 2560×1440`）。**唯一变量 = `sandbox_game\gamemd.exe`**：
A = `b9021544…1287`（补丁），B = `73201cc0…67476`（原版）。

---

## 2 · 两趟对照表

| 观测量 | TRIP A（补丁 exe） | TRIP B（原版 exe） | 差异归因 |
|---|---|---|---|
| 沙箱 `gamemd.exe` SHA | `b9021544a369…1287` | `73201cc0…67476` | **唯一自变量** |
| WMI Create / pid | retval=0 / **32364** | retval=0 / **21188** | 两趟各自独立启动 |
| 进程起来 | alive, exit=259 | alive, exit=259 | 相同（无加载失败） |
| 主菜单 → `GUI:CampaignMenu` | 19.12 s 全通 | 16.00 s 全通 | 相同 |
| 菜单渲染 | 正常（两徽章 + 文案 + 控件） | 正常（两徽章 + 文案 + 控件） | 相同 |
| `n_controls` | **19** | **18** | **+1** |
| `n_visible` | **14** | **13** | **+1** |
| `ctrl_id=1771` | **存在 1 个** Static `[310,37,421,132]` | **不存在** | **补丁插入的第 14 项** |
| ctrl_ids 差集 | `ids_only_in_A=[1771]` | `ids_only_in_B=[]` | 唯一差异 |
| hover (365,84) 底部状态栏 | **「執行教學任務。」** | 空白 | tutorial tooltip 通/不通 |
| hover 后 `[0xA8F7A8]` | **`0x6EB` (1771)** | `0x0` | 1771 分支命中/未命中 |
| 点击后画面 | 过渡 → **退回「單人遊戲」主菜单** | **停留在战役菜单** | 补丁项被响应 |
| 点击后 `n_controls` | 19 → **13** | 18 → **18** | 补丁项触发状态切换 |
| 崩溃 / 错误框 / 资源加载错误 | **无** | **无** | 相同 |
| `except.txt` / `ra2render.log` SHA 变化 | 无 | 无 | 相同 |
| `Scen+0x34CC` (全部 6 点) | -1 / `0xffffffff` | -1 / `0xffffffff` | 相同（基线已是 -1） |
| `Scen+0x125C` (全部 6 点) | `""` | `""` | 相同 |
| `[0xA8F7A8]` 点击后 | `0x6EB` | `0x0` | **补丁链** |
| `frame` / `mode` / `battle_cnt` | 0 / 0 / 15 | 0 / 0 / 15 | 相同（都未进图） |
| 收尾配置 28 项逐字节还原 | all_match=True | all_match=True | 相同 |
| 沙箱 exe 收尾 | 还原为原版 `73201cc0…` | 还原为原版 `73201cc0…` | 相同 |
| 自身 pid 残留 | 0 | 0 | 相同 |
| 锁（每趟一锁） | `w75`→`lead` | `w75`→`lead` | 相同 |

---

## 3 · 三分判定的理由与边界

选 **`运行期可达（能加载、有热区、链路通）`** 的依据（全部 `[本次实测]`）：

1. **能加载**：补丁 exe 启动成功、菜单完整渲染、无资源加载错误、无崩溃日志。
   改过 `.rsrc` 目录（61/113 数据入口 +0x20）没有破坏运行期资源解析。
2. **有热区**：`EnumChildWindows` 里 `id=1771` 真实存在（`n_controls` 19 vs 18，
   差集唯一 = `[1771]`），`Static` / `visible=True` / rect `[310,37,421,132]`。
3. **链路通**：hover → `STT:CampaignAnimTutorial` 文案（CSF 逆变换逐字匹配）
   + `[0xA8F7A8]=0x6EB`；click → 引擎状态改变（退回上级菜单），
   无错误框 —— 即 `[转引]` W58 的 `0x46CC90("tut1")` 静默失败路径在运行期成立。

**不选另外两项的理由**：
- `能加载但热区无效` —— 否证：热区有效（控件存在、tooltip 显示、选择变量置位、点击有响应）。
- `加载失败/崩溃` —— 否证：两趟均无崩溃、无错误框、无日志变化。

**边界（防外溢，必须连带引用）**：
- ❌ 不得写「第三徽章可用」：无独立美术（画面仍两枚徽章），无 `tut1` 战役数据，
  点击不进图（`frame=0` / `Scen+0x125C=""`），第三槽只补出**透明点击热区**。
- ❌ 不得写「(c) 路线解冻 / 产品可做」：三个门（美术、exe 分发与版本守卫、
  战役数据）一个都没解除；见 §0 声明。
- ❌ 不得写「点击把 `Scen+0x34CC` 改成 -1」：基线已是 -1，未观测到变化。
- ❌ 不得写「官方战役不受影响」或任何 B/A 线结论（与本卡无关）。
- `[静态推断]` 单镜像 / 单沙箱 / 单分辨率（1707×960 窗口、800×600 逻辑画面）、
  两趟各一次；「没观测到崩溃」≠「任何配置下都不崩溃」。

---

## 4 · 截图清单

`[本次实测]` 14 张 PNG，逐张 SHA-256 见 `out/SCREENSHOTS.json`；均存 `out/`。

| 文件 | 内容 | 关键判读 |
|---|---|---|
| `screen_tripA_main_menu.png` | A 主菜单 | 启动正常 |
| `screen_tripA_campaign_menu.png` | A `GUI:CampaignMenu` | 菜单正常渲染、底部状态栏**空白** |
| `screen_tripA_hover_tooltip.png` | A hover (365,84) | 底部出现 **「執行教學任務。」** = `STT:CampaignAnimTutorial` |
| `screen_tripA_hover_tooltip_desktop.png` | A hover 全屏 2560×1440 | 无 OS 级错误框 |
| `screen_tripA_after_click.png` | A 点击后即刻 | 徽章消失、红色地形过渡背景、无错误框 |
| `screen_tripA_after_click_late.png` | A 点击后 ≈4 s | **退回「單人遊戲」主菜单**（静默失败） |
| `screen_tripA_after_click_desktop.png` | A 点击后全屏 | 无系统错误框 |
| `screen_tripB_main_menu.png` | B 主菜单 | 对照 |
| `screen_tripB_campaign_menu.png` | B `GUI:CampaignMenu` | 与 A 视觉一致（无第三徽章美术） |
| `screen_tripB_hover_tooltip.png` | B 同坐标 hover | 底部状态栏**空白**（无 tutorial tooltip） |
| `screen_tripB_hover_tooltip_desktop.png` | B hover 全屏 | 对照 |
| `screen_tripB_after_click.png` | B 点击后即刻 | 仍停留战役菜单 |
| `screen_tripB_after_click_late.png` | B 点击后 ≈4 s | 仍停留战役菜单（无响应） |
| `screen_tripB_after_click_desktop.png` | B 点击后全屏 | 对照 |

其它 `out/` 产物索引：
`controls_trip{A,B}.json`（控件枚举 JSON）、`controls_trip{A,B}_hover.json` /
`controls_trip{A,B}_after_click.json`、`scen_readings_trip{A,B}.ndjson`（Scen 读数）、
`trip{A,B}.ndjson` + `trip{A,B}.log`（两趟日志）、`AB_COMPARISON.{json,tsv}`、
`CSF_TOOLTIP_MATCH.json`、`hotzone.json`、`config_baseline.json`、
`real_pre.json` / `real_post.json` / `sandbox_pre.json` / `sandbox_post.json`、
`FINALIZE.json`、`PREP.json`、`desktop_precheck.json`、`SCREENSHOTS.json`、
`cmd_robocopy_sandbox.log`、`gamemd_patched.exe`（本卡自有补丁副本）、
`pristine_gamemd.exe`（本卡自有原版副本）。

---

## 5 · 真机纪律自证（红线逐条）

| 红线 | 自证 | 证据 |
|---|---|---|
| 1 每趟一趟一锁（`w75`→`lead`），收尾 `owner=lead` | A: 02:30:55 取 / 02:31:36 放；B: 02:35:01 取 / 02:35:39 放；**最终 `owner=lead`**，不跨趟持锁 | `out/tripA.ndjson` / `tripB.ndjson` `lock_claimed`/`lock_released`；`REAL_DIR_PROOF.txt` §C |
| 2 不写 `ra2youli` | `IDENTICAL_TREE=True`：647 文件 / 1,989,215,270 B，added/removed/changed/**mtime_diff 全 0**；6 锚哈希 PRE==POST，含 `gamemd.exe=73201cc0…67476` | `out/real_pre.json` / `real_post.json` / `FINALIZE.json`；`REAL_DIR_PROOF.txt` §A |
| 3 绝不覆盖真目录 `gamemd.exe` | 只换 `sandbox_game\gamemd.exe`；脚本内硬断言 `dst.parent == W75\sandbox_game`；真目录 exe 前后 SHA 相同 | `w75_trip.py:exe_swap`；`REAL_DIR_PROOF.txt` |
| 4 只关自己启动的 pid，不 blanket `taskkill` | A pid=32364、B pid=21188；`close_game` 仅对自身 pid 发 WM_CLOSE→taskkill→/F；`residual_own_pid=0`、`all_gamemd_residual=[]` | `out/trip{A,B}.ndjson` `close_game` |
| 5 启动前可写配置字节副本 + 哈希，收尾逐字节还原并实算自证 | `out/pristine\` 28 项逐字节副本 + `config_baseline.json`；两趟 `restore_configs all_match=True`；finalize 时沙箱**已**与真目录逐字节一致（0 项还原动作） | `out/config_baseline.json`、`FINALIZE.json`、`REAL_DIR_PROOF.txt` §B |
| 6 只写本卡目录；`git` 只读；不改 W61 产物 | 所有写入落在 `W75_patched_exe_reachability\`；W61 `work\gamemd_v14r.exe` 收尾 SHA 仍 = `b9021544…1287` | `FINALIZE.json external_state` |
| 7 分级标注、不得写「第三徽章可用」 | 全文按 `[本次实测]`/`[转引]`/`[静态推断]`/`[待运行验证]` 分级；§3 明确禁用表述 | 本文件 |

`[本次实测]` 附加：`desktop_precheck` 两趟均 `WinSta0\Default` /
`EnumWindows=412` / `ImageGrab OK 2560×1440`（W35 的 agy 桌面隔离阻塞未复现）。

---

## 6 · 附：与已签发背景的对应关系（不重新论证）

| 已签发事实 | 本卡运行期对应 |
|---|---|
| `[转引]` W61：副本插入 `id=1771`、`cDlgItems` 13→14、模板 664→696 B、SHA `b9021544…1287`、长度 4,825,360 B | `[本次实测]` 离线 SHA 复核通过；运行期多出**恰好 1 个** `id=1771` 子窗口 |
| `[转引]` W58 / `LEAD_CHECK_menu_3slot.md`：3 槽 `1770=all1` / `1772=sov1` / `1771=tut1`；`WM_LBUTTONUP` 按 id 选中后 `call 0x46CC90`；`tut1` 不在 `BATTLEMD.INI` ⇒ 返回 -1 静默传给 `[Scen+0x34CC]`，无错误框 | `[本次实测]` 无错误框、`Scen+0x34CC` 全程 -1（基线已是 -1）、点击后退回上级菜单；**未观测到 `-1` 被"新写入"** |
| `[转引]` W61 §1：`0x52EEA8 mov [0xa8f7a8],0x6eb`；tooltip `STT:CampaignAnimTutorial` @`0x6041FD` | `[本次实测]` hover 后 `[0xA8F7A8]=0x6EB`；底部显示「執行教學任務。」（CSF 逆变换逐字匹配） |
| `[转引]` W64b：官方 `BATTLE.INI` 有 `[TUT1]` 但 YR 不加载；`trn01t.MAP` 不存在 | 本卡未改任何 INI/MAP；点击未进图，`Scen+0x125C=""` |
| `[转引]` `LEAD_RULING_C_line_route_a_first.md`：路线 (c) 冻结「能力已验证、产品不做」 | **本卡维持不变**，见 §0 声明 |

---

## 7 · 未覆盖 / 待验证

见 `UNKNOWNS.md`；分歧与口径收窄见 `DISAGREE.md`。

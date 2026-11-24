# W27 · DISAGREE.md — 与既有结论/假设的分歧

> 只列**本次真机证据**与既有文档/中途判断冲突之处，附证据指针。不否定对方在其自身证据范围内的结论，只限定外推边界。

## D1 · 与 `REVIEW/LEAD_FINDING_campaign_text_is_csf.md §5` 的分歧

**对方表述**（第 78 行）：
> 「这不影响**功能**（战役可注册、可推进），只影响**显示**。⇒ **不得**因为它而推迟 Q2（关卡推进）/Q3（存读档）的验证 —— 那是两条独立的链。」

**本次实测**：
- 「战役可注册」在**引擎全局表**层成立（Count=15、RA2F1 对象含 `CD=2 / ECH01.MAP`，`out/p1b_memory.ndjson`）。
- 但「**菜单里看得到 / 可选中**」**不成立**：`GUI:CampaignMenu` 只有 2 个官方徽章，7 条空槽不可点，`GUI:Back` 返回单人菜单；`out/p0_recon.ndjson`、`out/p0b_campaign_recon.ndjson`、`out/p1a_explore.ndjson`、`out/screen_p0b_S2_campaign_menu.png`。
- **D1 直接证伪「CSF 是原因」**：把 `Description` 改成引擎已知有效的 `DESC:ALL1` 后，`W27LIVE|utf16le` 命中由 2→0（`MISSING:` 文案消失），但战役菜单**截图与控件文本逐项相同**、Battle Count 仍 15（`out/p2a_D1_diagnostic.ndjson`、`out/screen_p2a_D1_campaign_menu.png`）。

**分歧点**：把 CSF 缺陷定性为「只影响显示、不影响功能/可推进」会掩盖**追加战役根本进不去菜单**这一更前置的 P0。补 CSF **不会**让追加战役变得可选；Q2/Q3 也不能在「追加包」上直接推进（本卡只能借 D2/D3 变体取得链数据）。
**建议改法**：§5 应拆成两句 —— (a) `Description` 纯文本 → 显示 `MISSING:'…'`（已证，工具缺陷）；(b) 追加 battle id 的 UI 可达性**未证且本环境实测不可达**（需另立卡）。(a) 不蕴含 (b)，也不蕴含「可推进」。

## D2 · 与 `README.md:31` / `docs/DESIGN.md:190` 的分歧

**对方表述**：`README.md:31`「安装后启动 `gamemd.exe` → 单人游戏 → 战役，战役列表里多出**一条追加条目**（官方战役保持原样）」；`docs/DESIGN.md:190`「`Description` 取自设计文件的 `campaign.description`（**纯文本，不是 `DESC:ALL1` 这种 CSF 标签**）」。

**本次实测**：
- 引擎确实把 `BATTLEMD98.INI` 并进了全局 Battle 表（Count 15），但 `GUI:CampaignMenu` **没有多出任何可见条目**；截图显示只有盟军/苏联两张徽章。⇒ `README.md:31` 的玩家可见承诺在本环境**不成立**。
- `BATTLEMD.INI` 自带注释：`Description = string file label of text description of campaign for player choice list`，官方取值 `DESC:ALL1` / `DESC:SOV1`；引擎把纯文本解析成 `MISSING:'W27LIVE …'`（`out/p1b_memory.ndjson` 的 `memory_dump.w27live_*`）。⇒ `DESIGN.md:190` 的「纯文本」设计选择与引擎字段语义相悖（此点与 Lead 的 CSF 发现一致，不是新分歧）。

**注意**：`README.md:121-122` 已自述「游戏内实测需要玩家进行」，所以这不是文档撒谎，而是**该承诺从未被真机验证过**；本卡是第一次真机检验并给出否证。建议把 :31 改成「引擎层追加一条 battle 记录；玩家可见菜单条目依赖引擎 UI，对本环境未成立」。

## D3 · 与 `HANDOFF.md §10` / 任务书「资源覆盖顺序」隐性假设的分歧

**隐性假设**：`BATTLEMD98.INI` 追加 + `expandmd98.mix` 装图 ⇒ 战役包可玩、可推进。
**本次实测**：地图文件本身可被引擎加载（D2 的 A1「任務完成」+ 我方基地；D3 的 A2 雪地图 + 侧边栏），**但胜利后 `GUI:Continue` 弹「無法啟動選取地圖!」，A2 未启动**（`out/p3_D2_chains.ndjson`、`out/screen_p3_I1_A1_ingame.png`、`out/crop_map_error.png`）。

**限定**：该观测在**劫持 `SOV1` 的 D2 变体**下取得，可能是劫持副作用，不能定论是 `[Basic] NextScenario` 写法错误（见 `UNCOVERED.md §A.2`）。但它足以说明：**「资源能被加载」≠「关卡链能推进」**，两条链必须分别真机验证，不能由前者外推后者。

## D4 · 与 `docs/re/a3_campaign_map_spec.md:166` 的「海报屏多一条」预期

**对方表述**：「散装 `BATTLEMD98.INI` 追加自有 id（如 `16=GAPA3`）+ `[GAPA3] Scenario=ECHGAP.MAP`｜不动官方条目；**海报屏多一条**」，同格备注「新条目可能触发分页/DebugOnly 过滤；导航坐标需重校」。

**本次实测**：`15=RA2F1` 未让海报屏（`GUI:CampaignMenu`）多出任何一条；`GUI:Back` 实测是返回 `GUI:SinglePlayerMenu` 而不是翻页；右侧 7 条槽 `LB_GETCOUNT=0` 且点击无响应。「分页」假设在本环境未观察到。备注里的「导航坐标需重校」也不成立——已用校准过的物理鼠标逐槽点击，全部无响应。
**限定**：不排除其它 id（如 `YURI1`）/其它构建会不同 —— D4 因该趟点击未生效落在主菜单，**未验证**（`UNCOVERED.md §A.3`）。

## D5 · 与「CSF 修复即可闭环」的中途判断

Lead 在收到 W27 中途报告后写的 `LEAD_FINDING_campaign_text_is_csf.md §6` 建议下一张卡做「资源覆盖顺序专项（散装 `ra2md.csf` 能否覆盖 MIX）」。
**本次意见**：该实验仍有价值（修显示），但按 D1 结果它**不能**修 Q1 的菜单可达性；若把它当作 C 线的下一个「闭环动作」，会跳过更前置的问题：**`GUI:CampaignMenu` 徽章按什么条件生成？追加 battle id 有没有可能生成第三条？** 建议把 §9.1（C 线下一步第 1 条）排在 CSF 之前。

---
**措辞纪律**：以上分歧均限定在「本环境 / 本包 / 本次观测」。引擎全局表 Count=15 与 `MISSING:'…'` 是 Lead 结论的**正面支持**，本卡不否认；分歧只针对「玩家可见菜单条目」「可推进」这些**未被该证据覆盖的外推**。

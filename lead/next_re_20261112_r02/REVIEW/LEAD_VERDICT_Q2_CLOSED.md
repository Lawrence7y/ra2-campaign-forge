# LEAD_VERDICT · Q2 闭合：`MAPSELMD.INI` 登记后战役可推进（真机三臂 A/B）

> 签发人：Lead（本会话）｜ 日期：2026-11-13 18:58
> 依据：**W39**（Hy4 子代理，真机）`lead\next_re_20261112_r02\W39_mapselmd_live2\`
> Lead 独立复核：直接读 `out\w39_skip_no.ndjson`(53 条) 与 `out\w39_control_official.ndjson`(47 条) 原始记录 + 自算 `REAL_DIR_PROOF`

---

## 1. 结论

**把 DLC 地图登记进散装 `MAPSELMD.INI` 后，战役能从第 1 关推进到第 2 关。该结论由同环境负对照因果锁定。**

`[本次实测]` C 线阻塞②（「無法啟始選取地圖！」）**闭合**。

### 1.1 ⚠️ 作用域限定（防外推，必须连写）

`[本次实测]` 本次成功的**入口仍是 W27 的 D2 诊断变体**：劫持 `[SOV1] Scenario=ECH01.MAP`，**借官方苏联徽章**进入；`scen_battle_idx=1`（即 `[Battles] 2=SOV1`）。
**不是**追加战役 `RA2F1` 自身的菜单条目（W27 Q1 已证实不可选、W32 证其结构上不可能）。

⇒ 正确表述：**「散装 `MAPSELMD.INI` 登记后，从官方苏联入口进入的 DLC A1 能推进到 DLC A2 局内」**。
⇒ **不得**外推成「追加式战役包整体可通关」或「菜单可达」。
⇒ A2 之后（`EndOfGame`）未测（超单趟预算）。

---

## 2. 三臂设计（同环境、单变量）

| 臂 | 变量 | 结果 |
|---|---|---|
| **主测试 `skip_no`** | 散装 `MAPSELMD.INI` = 官方 5,573 B + 追加 2 阶段（6,108 B）；我方地图 `SkipMapSelect=no` | **`run_outcome = A2_loaded`** |
| **负对照 `control_official`** | 唯一变量：`MAPSELMD.INI` 换回**官方 5,573 B（无追加）** | **`run_outcome = error_dialog_GUI_OK`** |
| **区分实验 `skip_yes`** | 追加 `MAPSELMD.INI` + 我方地图改 `SkipMapSelect=yes`（RPM 实测 `scen_skip_mapsel=1`） | 仍弹同一对话框；但内部路径不同（见 §5） |

三臂全部 WMI 启动、`finally` 自愈、`gamemd_residual=[]`、逐字节还原、`verify` exit 0。

---

## 3. 主测试的硬指标（我从 ndjson 原始记录复核）

**推进前**（`step=pre_continue_state`）：
```
frame=210  scen_filename=ECH01.MAP  scen_next=ECH02.MAP
scen_skip_mapsel=0  scen_stage_idx=0  scen_battle_idx=1  battle_cnt=15
visible=[GUI:Blank, GUI:Continue, GUI:HeadsTaken, GUI:ParTime, GUI:StandaloneScore, GUI:YourTime]
```
`[本次实测]` 结算屏成立（`GUI:Continue` + 计时/得分控件）。

**推进后**：
```
scen_filename = ECH02.MAP        ← 目标图已换（[本次实测]，明确）
scen_stage_idx = 8               ← 见下方限定，语义为 [转引]
frame: 0 → 44 → 123 → 216        (frame_t1=44, frame_t2=123, frame_delta=79)
markers: ECH02.MAP|ascii = 2
```

`[本次实测]` **`scen_filename` 由 `ECH01.MAP` 变为 `ECH02.MAP`** 是这一节最硬、最无歧义的指标。
`[转引·已修正]` 关于 `scen_stage_idx=8`：
- 该字段按 `[Scen+0x35A0]` 读取，其「当前阶段索引」语义来自既有反汇编，**非符号级证明**（W39 `UNKNOWNS.md:30-34` 明确拒绝据此宣称"引擎选中了第 8 阶段"）。**我此前把它标为 `[本次实测]` 并称"最硬的一条"，属过度声明，现降回 `[转引]`。**
- 且我原先写「`idx=8` ↔ `[Nod] 8=RA2F_ECH01_…`」**下标差了一格**：若 `DynamicVectorClass<MapStage*>` 按 0-based 存放（`[Nod] 1..7` 占 `0..6`），则 `8=RA2F_ECH01` 占索引 **7**、`9=RA2F_ECH02` 占索引 **8**。正在加载的是 A2(`ECH02`)，与索引 8 对应 `9=RA2F_ECH02_1E0DEBE8` 自洽。
- `[结论不变]` 无论 7 还是 8，**都落在我们追加的两条之内**，所以「引擎用到了追加阶段」这层含义仍成立；但**具体是哪一条、以及该偏移的确切语义，本会话未取得符号级证据**。

**局内证据**（按 Esc 后枚举）：
```
A2_esc_menu_controls hits=[GUI:AbortMission, GUI:GameControls, GUI:GameOptions,
                           GUI:LoadGame, GUI:ResumeMission, GUI:SaveGame]
```
`[本次实测]` 局内菜单齐全 ⇒ 已进入游戏局内，不是菜单/加载态。
`[本次实测]` 截图 `screen_w39_skip_no_A2_ingame.png`（976 KB）与 `screen_w39_skip_no_A2_esc_menu.png`（231 KB）存在。

---

## 4. 负对照为什么能锁因果

`[本次实测]` 同一沙箱、同一包、同一操作序列、同一执行环境，**唯一差别是 `MAPSELMD.INI` 是否含追加阶段**：
- 有追加 → `A2_loaded`
- 无追加（纯官方 5,573 B）→ `error_dialog_GUI_OK`，且 `scen_filename` 仍为 `ECH01.MAP`

⇒ 排除"沙箱本身好了"「包变了」「操作变了」「环境变了」四类混杂因素。**这是因果证据，不是相关性。**

---

## 5. `skip_yes` 臂的含义（不要把"还是弹窗"读成"和跳 no 一样"）

`[转引]` W39 报告：`skip_yes` 仍弹同一对话框（截图 SHA 与负对照**完全相同**），但内部路径不同——Continue 后 `scen_filename=""` 被清空，而 `scen_next` 仍为 `ECH02.MAP`。

`[我的解读]` 这与静态分析**一致**：`SkipMapSelect=yes` 走 `0x005ADF20` 分支，它要求「当前阶段在 `MAPSELMD.INI` 中的候选子项 `Scenario=` 与 `NextScenario` 匹配」。W34 生成的阶段段给非末关写了一条数字子项，但 `skip_yes` 路径需要的是**当前阶段**的子项能被匹配到——本次仍未命中。
⇒ **`SkipMapSelect=yes` 单独不可用作修复**；`no` + 追加登记这条路已经证明可行。

`[未定谳]` `skip_yes` 失败的确切原因是"子项键值不匹配"还是"阶段序号初值不对"，本卡未分离（W39 的 `UNKNOWNS` 应含此条）。

---

## 6. 【已撤回】我此前对 W39 时间口径的"纠偏"是错的

> 本节原写「W39 说 2.5 s、ndjson 说 4.56 s，两者混用了时间基准」。**该纠偏已撤回** —— W39 原本没错。
> 触发：W43 交叉审计 BLOCKER-2；Lead 随即自读 `t_monotonic` 逐条复核。

`[本次实测]` 我自己拉出 `w39_skip_no.ndjson` 的全部时间戳：

```
pre_continue_state      frame=210   t=10287.093
click_Continue          —           t=10289.093   ← 点击
post_continue           frame=0     t=10289.109
post_continue           frame=0     t=10290.625
post_continue           frame=0     t=10292.140
post_continue           frame=44    t=10293.656   ← 4.563 s 后（= 记录的 elapsed_s 4.56）
A2_timer_confirm        frame=123   t=10296.156   ← 恰好 2.500 s 后
A2_confirmed            frame_t1=44 frame_t2=123 frame_delta=79 elapsed_s=4.56
A2_esc_menu             frame=216   t=10299.734
```

`[本次实测]` 结论：
- **`elapsed_s=4.56` 是「点击 Continue → 首次采到 `frame=44`」的耗时**（含加载/切换），**不是** `44→123` 的窗口
- **`44→123` 恰好跨 2.500 s 墙钟** —— 因为驱动脚本里就是 `time.sleep(2.5)`（`run_mapsel_live.py` L271）
- 因此 **79 计数 ÷ 2.500 s = 31.6 计数/s，是墙钟速率**，与 `[0xA8ED84]` 的 32 ms 定拍（31.25/s）相符

⇒ `[签发]` **W39 原文「frame 44→123，Δ79/2.5s ≈31.6 计数/s」表述正确**；我此前"混用时间基准""会把加载开销算成帧速"的指责**不成立，作废**。
`[保留一条正确用法]` 若要描述整段推进，应写「点击后 4.56 s 采到 `frame=44`；随后 2.5 s 内前进 79 个计数」。两个数各有其窗口，别把它们混成一句。

---

## 7. 真机零改动（我自己重算）

`[本次实测]` `W39_mapselmd_live2\REAL_DIR_PROOF.txt`：
```
PRE : file_count=647 total_bytes=1989215270 maplike_count=277
POST: file_count=647 total_bytes=1989215270 maplike_count=277
added=0 removed=0 changed=0   IDENTICAL_TREE=True
RA2MD.INI=c91c6a47…  gamemd.exe=73201cc0…  ddraw.dll=85e0f7d5…  ra2forge_install.json=fe3bdf62…
```
`[本次实测]` 我另外单独复算了一遍真目录四项哈希，与上述一致（见本文件签发时的 `Get-FileHash` 输出）。

---

## 8. 这次闭合了什么 / 没闭合什么

**闭合**
- 散装 `MAPSELMD.INI` 会被引擎读取并生效（散装优先于 MIX 的 W29 结论在此得到端到端印证）
- 追加阶段登记后 `GUI:Continue` **能**推进到下一关
- 生成的 `MAPSELMD.INI` 格式被引擎解析器接受（不崩、不报格式错）
- v11 的生成逻辑（`[Nod]` 续号 + 独立阶段段 + `Scenario=`）在真机上可用 —— **限「单后继直转」路径**
  `[收窄（21:26，据 W52 审计）]` 真机只验证了「A1 单后继直接进 A2，全程未出现需要点击的选关画面」。
  W39 `UNKNOWNS` 明写 `--mapsel-click` 未使用、也无需使用。因此**多分支交互式 MapSelect（`2=<next>` 那类数字子项 + `ClickMap=NODCLK01.PCX` 的可点区域）从未在真机上验证过**，
  不得写成「数字子项在真机上可用」。

**未闭合**
1. **菜单可见性**仍结构性封死（`REVIEW\LEAD_VERDICT_campaign_menu_q1.md`）——本次成功仍是**借 `[SOV1]` 入口**，不是原生可点
2. **CSF 显示**未验证（W40 真机卡刚派）
3. **as-built 入口下的 Q3 存读档**仍未验证（W27 的 Q3 是在 D3 诊断变体下成立的）
4. **末关终止行为**（`EndOfGame=yes` 一侧）未验证
5. **`skip_yes` 失败成因**未分离
6. **多包共存**（whole-file `MAPSELMD.INI` 冲突）不可用，v11 设计上拒绝

---

## 9. 交付物索引

- `W39_mapselmd_live2\LIVE_RESULT.md`、`UNKNOWNS.md`、`DISAGREE.md`、`REAL_DIR_PROOF.txt`、`tools\`（6 个可复跑脚本）
- `W39_mapselmd_live2\out\`：3 趟 ndjson（`w39_skip_no` 30,119 B / `w39_control_official` 28,806 B / `w39_skip_yes` 29,353 B）+ 16 张截图 + `MAPSELMD` 变体 + `verify` 日志 + `real_pre/post.json`
- 配套：`REVIEW\LEAD_VERDICT_map_start_root_cause.md`（静态根因，本文件是其真机验证）

---

## 10. 三个执行环境的差异（已定谳，供后续真机卡选型）

| 卡 | 执行方式 | window_station / desktop | 结果 |
|---|---|---|---|
| W35 | agy（Gemini 4H） | `WinSta0\exebox-ZO5YEXSDBF5D74L4BR7PIY34ZX` | **GUI 不可见**（`EnumWindows=0`、截图抛错）⇒ 真机阶段未完成 |
| W39 | **子代理**（Hy4） | `WinSta0\Default`（input desktop 亦 `Default`） | 独立探针 `EnumWindows=377/18 可见`、`EnumChildWindows=25`、`ImageGrab OK(2560×1440)`；三趟 `step0` 预检全 `pass=true` |
| W27 | 子代理 | （当时成功） | 成功 |

`[签发]` **真机 GUI 观测必须派子代理，不能派 agy。** 这是硬性的选型规则，不是偏好。
`[对 W35 的正确记账]` W35 **不是失败** —— 它把离线准备全部做完（沙箱、卸旧包、装包、`verify`、官方 5,573 B 提取、6,108 B 追加构建、逐字节还原、`IDENTICAL_TREE=True`），只是**真机阶段因该执行环境桌面隔离未完成**，已由 W39 完成。台账口径：「W35 准备完成、真机阶段环境阻塞；W39 补完真机」。

---

## 11. W39 自己申报的两个缺陷（我照录，不粉饰）

1. `[本次实测]` **首趟工具崩溃**：同参数运行在 `memory_search` 处因 sink 的 console print 用 GBK 编码遇 latin-1 字节 `\xde` 抛 `UnicodeEncodeError` 中止（当时 A1 已加载、`finally` 自愈完整）。归档为 `out\w39_skip_no.run1_toolcrash.ndjson`，修复为 `ensure_ascii=True` + 防御 `try/except` + `PYTHONIOENCODING`，三趟正式运行未复现。**这是驱动缺陷，不是游戏行为** —— 后续引用这三趟数据时须知道存在第 4 个（失败的）记录文件。
2. `[本次实测]` **「收窄 4 条失败分支」这个目标未达成**：`MapSelect::Init` 的 4 个分支英文串（`Invalid side!` / `Unable to initialize choices!` / `Invalid stage!` / `Unable to create font!`）在两次错误趟里**都作为 exe 静态字符串各命中 1 次**，只读 RPM 无法判别实际走的是哪条；需断点/符号级跟踪，而注入被本会话纪律禁止。已写入其 `UNKNOWNS.md U2` / `DISAGREE.md D2`。
   ⇒ **`Invalid stage!` 仍是 `[静态推断]`，不是实测**。我此前在 `LEAD_VERDICT_map_start_root_cause.md` 里就是这么标的，此处保持一致。

`[附带一条三方差值印证]` W39 把错误框放大 7× 逐字确认第 4 字是「**始**」非「動」（`crop_w39_error_text.png`）。这与我在官方 CSF 里查到的 `MSG:UnableMapSelect` = 「無法啟始選取地圖！」、以及 W31 的独立结论三方一致。W27 记作「啟動」确为转录误读。

`[另]` W39 记录 frame 序列还延伸到 `0→44→123→216`（我引用的 44→123 只是其中一段窗口）。

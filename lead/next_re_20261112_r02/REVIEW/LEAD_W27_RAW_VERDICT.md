# LEAD_W27_RAW_VERDICT · W27 真机卡「原始产物直读」判定

> 判定人：Lead（本会话）｜ 日期：2026-11-13（初版 14:43，14:50 修订）
> 依据：**先只读 W27 落盘的 ndjson / INI / 截图 / 日志**，再把 W27 自带报告逐条对照。
> 分级口径：`[本次实测]` = 本次会话原始产物直接观测；`[本次读码]` = 读文件字节；`[本次复算]` = Lead 亲跑脚本；`[静态推断]`；`[转引]`；`[待运行验证]`。

> **修订说明（自我纠错）**：本文件初版写「W27 结束时未留下报告 MD」——**该句错误**。W27 的报告在 14:42:19–14:43:55 之间写入，我 14:41–14:42 查得过早。现 W27 报告实态：
> `CAMPAIGN_LIVE.md` 24,562 B (`34AAEF65B1594580…`)、`DISAGREE.md` 5,931 B (`49DA7667DCFD98C2…`)、`UNCOVERED.md` 5,643 B (`0ACA0CB5F259C033…`)，均在 `W27_campaign_live/`。
> 本文件保留「先原始产物、后对照报告」的顺序，凡仅由报告支撑的结论标 `[转引]`。

---

## 结论一页表

| 问题 | 判定 | 证据强度 |
|---|---|---|
| **Q1** 追加战役是否出现在 `GUI:CampaignMenu` | **不成立** | `[本次实测·截图]` Lead 亲自读图：只有盟军/苏联两颗徽章 |
| **Q2** 结算后 `NextScenario` 推进到下一关 | **不成立** | `[本次实测·截图×2]` 任务完成屏 + 「無法啟始選取地圖！」；失败点在下一关解析 |
| **Q3** 跨进程存读档 | **成立**（**仅 D3 诊断变体**） | `[本次实测]` 存档 559,553 B、退出重载、frame 82→198→276 |
| **Q4 / D4** 换 `YURI1` 做 battle id 是否生成条目 | **未定谳** | `[本次实测]` 未进到 CampaignMenu |
| **D1** CSF 文本是否为不可见根因 | **已否证** | `[本次读码]`+`[转引]` 换成 `DESC:ALL1` 后 `MISSING` 消失但菜单逐项不变 |
| 真机目录是否被写 | **零改动** | `[本次复算]` `IDENTICAL_TREE=True` |

---

## 0. 真机目录零改动（Lead 亲自复算）

直接执行 W27 自带 `tools/diff_real.py`（Lead 本轮独立运行，非转引）：

```
PRE : 647 1989215270 277
POST: 647 1989215270 277
added= 0 []      removed= 0 []      changed= 0 []
REAL_RA2MD_INI_POST= c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d
IDENTICAL_TREE= True
```

`[本次实测]` 真 `ra2youli` 在 W27 全程后**逐项一致**：647 个文件、总字节 1,989,215,270、277 个 maplike 文件、`RA2MD.INI` = `c91c6a47…`（与 `baseline_pre_launch/PRE_LAUNCH_BASELINE.tsv` 一致）。`ra2forge_install.json` 仍为既存旧包 `fe3bdf62…`（1,487 B），未被本轮触碰。
`[本次实测]` 每次收尾 `restore_configs` 记录 `all_match: true`（`RA2MD.INI`/`ddraw.ini`/`RA2MD.INI.benchbak`/`gamemd.exe`/`ddraw.dll` 五项），`close_game` 后 `all_gamemd_residual: []`。

---

## 1. D3「诊断变体」的准确内容（这是全部结论的限定条件）

`[本次读码]` 对比 `out/BATTLEMD.INI.asbuilt`(2,733 B, `7e40691a…`) 与 `out/BATTLEMD.INI.D3_sov1_ech02`(2,730 B, `bfbe79de…`)，唯一差异：

```
- Scenario=SOV01umd.MAP
+ Scenario=ECH02.MAP
```

即：**只把官方 `[SOV1]` 的 `Scenario=` 直接指向我方第二张图 `ECH02.MAP`**，绕开 `NextScenario` 链。其余字段、文件结构未变。

---

## 2. Q3（存读档）—— 成立，但限定于上述变体

`p5_q3.ndjson` 原始记录链（时间单调递增，进程 pid 38136→后续实例）：

| 环节 | 原始证据 |
|---|---|
| 进入游戏 | `badge_attempt attempt=0, still_on_campaign_menu=false`；`K1_ingame elapsed_s=6.01, counters.frame=82` |
| 存档 | `Q3_save_file added=[SAVE4823.SAV 559,553 B sha 4800374b…], before_n=8 after_n=9 changed=[]` |
| 存档副本出库 | `Q3_save_copied` 同 sha `4800374b…` 拷至 `out/save_SAVE4823.SAV` |
| 完全退出 | `Q3_process_exit residual=[]`（gamemd 残留 0） |
| 重新启动并读档 | `load_dialog_buttons=["GUI:Load"]`；`Q3_load_ingame counters.frame=198` |
| 读档后在游戏内 | `Q3_load_observation in_game_evidence=true, markers ECH02.MAP|ascii=3, save_copy_matches=true, save_copy_sha256_after=4800374b…(与存档前一致), esc_menu_visible=[AbortMission, GameControls, GameOptions, LoadGame, ResumeMission, SaveGame, DeleteGame]` |
| 还原 | `D3_restore byte_identical=true` 回到 `7e40691a…` |

`[本次实测]` **跨进程存读档成立**：存档文件真实产出（559,553 B）、进程完全退出后重新加载、回到游戏内（frame 198 递增、Esc 菜单含 `GUI:SaveGame`/`GUI:LoadGame`/`GUI:ResumeMission`）、且读档未改写存档文件字节（sha 前后一致）。

**必须同时写明的限定**：该成立是**在 `[SOV1] Scenario=ECH02.MAP` 直接指向的诊断变体下**取得的。`p5_results` 原文即 `q3 = "成立（D3 诊断变体）"`。

### 2.1 `Q3_load_selected selected=null` 不能算作「已选中目标存档」

`[本次实测]`：ListBox（ctrl id 1109）的选中项**读不出来**（`selected: null`），流程是靠 `GUI:Load` 按钮推进并按 frame 递增判定入局。
`[静态推断]`：入局证据（frame 198→276、Esc 菜单齐全、`ECH02.MAP` 标记命中 3 处）足以证明**加载了某份存档并进入游戏**，但**不能证明加载的正是 `SAVE4823.SAV`**——该步在本卡未取得「选中项 == 目标存档」的正向证据。后续要补的话，最低成本是读档后比对新旧存档内嵌的战役/任务标识，或只保留单一存档做排除。

---

## 3. D3（as-built 链）—— 失败，且失败点已收窄

`p4_D3_q3.ndjson`：

```
D3_verdict: state=timeout, verdict="A2 map FAILED to start: timeout"
counters.frame=0, mode=0
visible=["GUI:Back","GUI:Blank","GUI:CampaignMenu","GUI:Difficulty","GUI:Harder","Slider3","Yuri's Revenge"]
p4_results: d3="A2 map FAILED to start: timeout", q3="未验证"
```

`[本次实测]` 停留在**战役菜单（含难度滑条 `Slider3`/`GUI:Difficulty`/`GUI:Harder`）**，90.16 s 内 `frame` 恒为 0、未进入游戏。
`[本次实测]` 第 2 节同一张 `ECH02.MAP` 在被 `Scenario=` 直接指向时能正常入局（frame 82 且递增）⇒ **图本身可加载**，失败发生在「`NextScenario` 推进到目标图」这条路径上。
`[静态推断]` 因此 C 线阻塞点②的表述应精确为：**`NextScenario` 目标图寻址/解析失败**，而非「ECH02.MAP 不能被引擎加载」。

---

## 4. D2 链式推进（Q2）—— 不成立

### 4.1 变体定义（Lead 亲自 diff 校验）

`[本次读码]` `out/BATTLEMD.INI.D2_sov1_ech01`(2,730 B) 与 `.asbuilt`(2,733 B) **唯一差异**：

```
- Scenario=SOV01umd.MAP
+ Scenario=ECH01.MAP
```

即 D2 = 把官方 `[SOV1]` 指向我方**第一关** `ECH01.MAP`（沙箱内，收尾已还原 `7e40691a…`）。

### 4.2 观测链

`[本次实测]` `p3_D2_chains.ndjson`：
- `#26` `I1_wait_briefing elapsed_s=10.52 hits=["GUI:Continue"]` —— 出现 `GUI:Continue` 按钮
- `#25` 同屏还有 `Static GUI:ParTime / GUI:YourTime / GUI:StandaloneScore / GUI:HeadsTaken`（结算屏类控件）
- `#28` `click GUI:Continue posted=True`（真实点击已投递）
- `#157` `I1_wait_victory poll_timeout timeout_s=120 wanted=["GUI:Continue"]` —— 之后 120 s 未再等到该按钮

`[转引]` W27 报告 `CAMPAIGN_LIVE.md:96-97,105`：A1 加载并由引擎原生 `survive(8)` 触发器在 ~8 s 判胜 → 出现「任務完成」+`GUI:Continue` → 点 `GUI:Continue` 后**直接弹出错误对话框**（报告记为 `GUI:OK` 对话框），frame **冻结于 210**，**未出现 A2 加载或局内画面**；错误文案为 **「無法啟始選取地圖！」/「確定」**。

### 4.3 证据强度必须如实标注

`[本次实测]` 我对全部 `out/*.ndjson` 做全文检索：`無法啟動` 命中 **0 次**、`任務完成` 命中 **0 次**。
⇒ 该错误文案与「任務完成」**只存在于截图**（`out/crop_map_error.png` 776,173 B、`out/screen_p3_I1_briefing_or_later.png`），**未被捕获为 Win32 控件文本**（该弹窗由引擎自绘/非标准控件，与 Esc 菜单等标准控件不同）。
⇒ 因此这两条只能标 `[本次实测·截图证据]`，不得写成「控件文本显示 xxx」。

`[本次实测]` 另需注意：`GUI:Continue` 在 **briefing 屏**也会出现（`#26` 10.52 s 即命中），故「出现 `GUI:Continue`」本身**不足以**证明进入结算屏；结算屏判定依赖 `GUI:ParTime/YourTime/HeadsTaken` 等伴随控件与截图。

### 4.4 结论

`[结论]` **Q2 = 不成立**：`NextScenario` 链被触发到「结算屏 → `Continue` → 尝试启动下一关」，但 A2 未启动，表现为弹窗 + frame 冻结 210。
`[本次实测]` 佐以第 2 节：同一张 `ECH02.MAP` 被 `Scenario=` 直接指向时可正常入局 ⇒ **排除「A2 地图文件坏」**。
`[待运行验证]` 但 Q2 失败**是否由「劫持 `[SOV1]`」这一诊断手法本身引起，本卡未分离**；追加包在 as-built 入口下的 Q2 既未成功也未复现失败。

### 4.5 Lead 亲自读图定谳 + W27 脚本假阴性记录（重要）

**Lead 直接读了两张截图**（非转引）：

| 截图 | Lead 目视结论 |
|---|---|
| `out/screen_p3_I1_briefing_or_later.png`（1707×960，`7e7264bd…`） | **「任務完成」结算横幅确实出现**，画面为我方苏军基地（建造场/核弹井/电场/矿场+工程师），黄字「任務完成」 |
| `out/crop_map_error.png`（940×700，`9434b37f…`） | **「無法啟始選取地圖！」+「確定」按钮确实出现**，Yuri 主题背景，引擎自绘对话框（无 Win32 控件文本，故 ndjson 检索命中 0） |

⇒ 结论升级为 `[本次实测]`：**Q2 = 不成立（链触发、结算屏出现、点 `Continue` 后下一关启动失败）**。

**用字勘误（Lead 自己读错，特此更正）**：该弹窗的 CSF 真值是
`MSG:UnableMapSelect` = **`無法啟始選取地圖！`**（**啟始**，非「啟動」；末尾带 `\n`）。
我在上表把字形读成了「啟動」，W27 报告亦同误。详见 `LEAD_FACT_map_error_label.md`（含提取方法与 5,211 条标签全量检索）。
**实务影响**：想靠搜「啟動」在 exe 里找字符串必然落空——正确路径是「中文文本 → CSF 标签名 `MSG:UnableMapSelect` → 用 ASCII 标签名做 xref」。

**W27 自身产物存在假阴性，必须记录**：
- `p3_D2_chains.ndjson` 的 `chain_results.q2` 写的是 `"未验证（未出现胜利/结算屏）"` —— **与截图矛盾，该值为假阴性**。
- 代码级成因（`tools/phase_p3_D2_chains.py`）：`:227-228` 在**点击之前**轮询 `GUI:Continue`，`#26` 于 10.52 s 已命中并由 `#28` 点击；随后 `:228` 再轮流 120 s 等**第二个** `GUI:Continue`，此时屏幕已被错误对话框占据 → `#157 poll_timeout` → 走到 `:252` 把 `q2` 写成「未出现胜利/结算屏」。
- 即：**判据顺序错误 + 以按钮出现/消失代替结算屏语义**，导致脚本把「明明出现了」判成「未出现」。
- 教训（与 W25 同类）：**测试脚本自身可以编码错误期望**；此类绿/红结果必须回对原始证据，不能直接引用脚本结论。

---

## 5. D4（新 battle id 是否可见）—— 未定谳（换 id 探针未走通）

`[本次读码]` `out/BATTLEMD98.INI.D4_yuri1`(385 B) 与 `.asbuilt` 唯一差异是把 `15=RA2F1`/`[RA2F1]` 换成 `15=YURI1`/`[YURI1]`（`Scenario=ECH01.MAP` 不变）。设计意图：用**已有徽章**的 side id 试探战役菜单条目是否由 id 驱动。

`p6_D4_yuri1.ndjson`：
- `click control_text="GUI:NewCampaign" label="to_CampaignMenu" result="not_found"`
- `D4_verdict_data`：`ra2f1_ascii=0`，`yuri1_ascii=2`，可见按钮为主菜单（`GUI:ExitGame`/`GUI:SinglePlayer`/`GUI:WWOnline`/`GUI:Options`/`GUI:Network`/`GUI:MoviesAndCredits`），静态控件仅 `GUI:MainMenu`/`GUI:Blank` 等
- 随后真实鼠标点击 `(210,470)` → 界面变为 `GUI:SinglePlayerMenu`（含 `GUI:NewCampaign`/`GUI:LoadSavedGame`/`GUI:Skirmish`）
- `D4_restore byte_identical=true`

`[本次实测]` `YURI1` 字符串在内存命中 2 处 ⇒ **条目被引擎读进了内存**；`RA2F1` 命中 0（本轮该文件里 id 已是 YURI1，故 0 属预期，不构成反证）。
`[本次实测]` 但**始终没进到 CampaignMenu**，点击落到了 `SinglePlayerMenu` ⇒ **未观察到是否生成第三个战役徽章**。
`[结论]` **D4 = 未定谳**。既不能写「新 battle id 无法出现在 UI」，也不能写「可以」。此前「战役菜单按 side 硬编码、追加 battle id 不会生成 UI 条目」这句**在本轮原始产物中只找到间接支持，未取得直接观测**，应降级为 `[静态推断/待运行验证]`。

---

## 6. D1 —— CSF 文本**不是**战役条目不可见的根因（本卡最干净的否证）

`[本次读码]` Lead 亲自 diff `out/BATTLEMD98.INI.asbuilt`(385 B) vs `out/BATTLEMD98.INI.D1_desc_all1`(354 B)，**唯一差异**：

```
- Description=W27LIVE two-mission chain probe A1 to A2
+ Description=DESC:ALL1
```

`DESC:ALL1` 是官方 `BATTLEMD.INI` 里在用的有效 CSF 标签（`; Description = string file label …`，官方取值 `DESC:ALL1` / `DESC:SOV1`）。
**注**：385→354 B 的差值正是把长文本换成短标签所致，与「只改了一行」自洽。

`[转引]` + `[本次实测]` 组合证据：
- `[转引]` W27 报告 `CAMPAIGN_LIVE.md:79`：改后 `W27LIVE|utf16le` 内存命中由 **2 → 0**（`MISSING:` 文案消失），Battle Count 仍 **15**，`GUI:CampaignMenu` 截图与控件文本**逐项相同**（仍 2 徽章 / 7 空槽 / `GUI:Back`）。
- `[本次实测]` `p2a_D1_diagnostic.ndjson` 的 `D1_verdict_data`：`missing_w27live_count=0`；两个简介静态框 `[94,39,326,130]`/`[94,243,326,334]` 文本为 `""`；`visible_buttons=["GUI:Back"]`。

`[结论·本次实测]` **把 `Description` 换成有效 CSF 标签后，`MISSING` 症状消失，但战役菜单条目/槽位数量完全不变** ⇒ **CSF 文本缺失不是「新战役不可见」的根因**。
`[本次实测]` 这同时**证实了我先前 `LEAD_FINDING_campaign_text_is_csf.md` §5 的「只影响显示」是错的**（该文件已撤回）：CSF 影响的是**描述文字能否显示**，与**条目是否生成**是两件事，且后者不因前者改善而变化。

`[静态推断]` 结合 §5（D4 未定谳）：条目生成条件更可能在**菜单侧的 side/徽章枚举**，而非文本资源；但这仍是推断，**未取得直接静态证据**。

---

## 6.1 安装预检在「旧包残留」目录上的行为（本次实测，含沙箱证据）

`[本次实测]` `out/install_w27.log`：首次 `install`（无 `--allow-content-conflict`）→ **EXIT_CODE=1**，`install blocked by preflight - no file has been written`，两条 **definite content conflict**：

```
- ECH01.MAP: would replace a file that ra2forge_install.json does not record as ours
- ECH02.MAP: would replace a file that ra2forge_install.json does not record as ours
notices (do not block):
- BATTLEMD.INI present (normal install state) and left untouched; the campaign is appended
  by BATTLEMD98.INI (the engine merges both by battle id). This is NOT a conflict.
```

`[本次实测]` 成因：沙箱内先 `uninstall` 了既存 v0.3 旧包，卸载把 `ECH01.MAP`/`ECH02.MAP` **还原成官方原图**，而新包的清单并不认领这两份文件 → 预检判为「会覆盖不属于我们的文件」。
`[本次实测]` `out/install_w27_allow.log`：加 `--allow-content-conflict` → **EXIT_CODE=0**，9 项动作全部逐条留痕（`created BATTLEMD98.INI 385 B`、`backup ECH01.MAP→.ra2forge.bak`、`replaced ECH01.MAP 4671 B`、同 `ECH02.MAP 4647 B`、`created expandmd98.mix 9352 B`、`written .seal`、`written ra2forge_install.json`），且每条 `ALLOWED … content conflict released by --allow-content-conflict (recorded in the manifest)`。

`[本次实测]` 判定：**安全门按设计生效**（宁停不写，`no file has been written` 为真，非静默覆盖）。同时暴露一个**真实可用性问题**：在「卸载旧包后立刻装新包」的常规升级路径上，用户会撞到 exit 1，需要显式加 `--allow-content-conflict` 才能继续。
`[静态推断]` 根因是**卸载把备份还原成官方原图、但新包把同名地图视为自己该占的位**——两套「所有权」判断不衔接。是否为缺陷需产品口径判定（W21 曾记同类 `DISAGREE.md`），本卡只如实记录现象。

---

## 7. 本轮不得再出现的表述（防止外溢）

- ❌「包里战役端到端跑通」——as-built 入口卡在战役菜单；Q3 只在 D3 诊断变体下成立。
- ❌「NextScenario 正常」/「q2 未验证」——**q2 实测为「不成立」**：结算屏出现，点 `Continue` 后弹「無法啟始選取地圖！」，frame 冻结 210。
- ❌「新战役不出现在 UI 是引擎硬编码限制」——D4 未定谳；D1 只否证了「CSF 文本是根因」。
- ❌「描述文本只影响显示不影响功能」——ALREADY WITHDRAWN（`LEAD_CORRECTION_campaign_blockers.md`）；但注意 D1 又反向否证了「CSF 是条目不可见的原因」。
- ❌ 把 `Q3_load_selected selected=null` 说成「已精确加载目标存档」。
- ❌ **直接引用 W27 脚本的 `chain_results.q2` 值**——该值是假阴性（见 §4.5），脚本判据顺序错误。
- ❌ 「Q2 失败已确认由引擎 bug 引起」——仅知失败点在「胜利后下一关解析」，**是否由劫持 `[SOV1]` 引起未分离**。

---

## 9. Q1（追加战役是否出现在战役菜单）—— 不成立

### 9.1 Lead 亲自读图（一手证据）

`[本次实测·截图]` `out/screen_p2a_D1_campaign_menu.png`（1707×960，`16f2e0a335db0d88…`）目视：左侧面板**只有两颗徽章**——上方**盟军鹰徽**、下方**苏联镰刀锤子星徽**；中间一条**难度滑条**（左「困難」右「正常」）；底部红色**「上一頁」**按钮；右侧为金属栏，**无任何列表行文字**。**没有第三颗徽章、没有第三条战役条目。**

`[本次实测]` 与之吻合：徽章下说明文字（「點選盟軍圖示以開始盟軍戰役。」/「點選蘇聯圖示以開始蘇聯戰役。」）**正常显示中文** ⇒ 内建 `GUI:` 文本的 CSF 解析在本机**工作正常**，进一步支持 §6「CSF 不是条目不可见的根因」。

### 9.2 控件层

`[本次实测]` `p2a_D1_diagnostic.ndjson` `D1_verdict_data`：可见按钮仅 `GUI:Back`；静态控件含两个徽章位 `[94,39,326,130]`、`[94,243,326,334]`（文本为空，因为徽章是贴图而非文字）；另有 `GUI:Difficulty`/`GUI:Harder`/`Slider3`。

`[转引]` 报告 `CAMPAIGN_LIVE.md:56`（S2 段）：`BM_CLICK GUI:NewCampaign → posted=True` 后进入 `Static GUI:CampaignMenu`；隐藏 `ListBox`(id=1109) **`LB_GETCOUNT=0`**；隐藏 `Button GUI:Load`；**5 个空文字 Static**（含两个徽章位）。

### 9.3 穷举过程（转引）

`[转引]` 报告称已穷举：**方向键 / 点徽章 / 点右侧槽位**，均无第三条目；`GUI:Back` 正确返回单人菜单；右侧 7 条空槽点击无响应。

### 9.4 引擎层与菜单层的分离（关键区分）

`[转引]` 报告称只读 RPM 观测：全局 **Battle 表 `Count=15`**（即 14 官方 + 1 追加），`RA2F1` 对象含 `CD=2`/`Scenario=ECH01.MAP`；主菜单内存命中 `RA2F1`、`ECH01.MAP` 及 `MISSING:'W27LIVE …'`。
`[本次实测]` 我在 `p6_D4_yuri1.ndjson` 中亲见 `yuri1_ascii=2`（`YURI1` vs `RA2F1` 探针轮）⇒ **条目确实被引擎读进内存**。

### 9.5 结论

`[结论·本次实测]` **Q1 = 不成立**：追加的 battle id **被引擎登记进 Battle 表并读入内存**，但 `GUI:CampaignMenu` **不生成对应 UI 条目**（画面与控件双重确认只有 2 颗徽章）。
`[静态推断]` 菜单条目生成条件很可能绑定**固定的 side 枚举/徽章资源**，而非 Battle 表遍历；但这属于推断，**静态证据尚未取得**（原定 W29/后续卡片）。

---

## 8. 复现入口

- 原始产物：`W27_campaign_live/out/*.ndjson`、`out/screen_*.png`、`out/save_SAVE4823.SAV`、`out/BATTLEMD*.INI.*`
- 真机零改动复算：`python W27_campaign_live/tools/diff_real.py`
- 驱动脚本：`tools/phase_p4_D3_q3.py`（D3/Q3）、`phase_p5_q3.py`（Q3 变体）、`phase_p6_D4.py`（D4）、`tools/live_lib.py`

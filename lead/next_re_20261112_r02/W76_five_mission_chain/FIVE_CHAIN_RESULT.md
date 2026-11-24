# W76 · 五关链规模验证 + 用 5 关数据点检验 Lead 的 `+0x35A0` 推断

> 执行者 **Hy4**（W76，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W76_five_mission_chain\`
> `STARTED.txt` 写在读任何文件之前：`2026-11-14T07:15:21+08:00[Asia/Shanghai]`
> 离线造包/装沙箱（不占锁）：`07:15 ~ 07:25`；真机 trip1 `07:26:12 ~ 07:29:07`；trip2 `07:32:25 ~ 07:35:18`；收尾 `07:36:20 ~ 07:36:30`
> 时间盒 140 min 内完成，未触发"只走到第 3 关"的降级条款。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本报告不签发（签发权在 Lead）。

---

## 0 · 一句话结论

`[本次实测]` **就地改写官方 `BATTLEMD.INI` 的 `[SOV1]` + 5 阶段 `MAPSELMD.INI`，能把本卡自造的 5 关战役包送进游戏并走完 M1→M2→M3→M4→M5 全链；M5 `EndOfGame=yes` 正确终止、不再进第 6 关。两趟真机逐项一致。**

`[本次实测]` **任务②：Lead 在 `REVIEW\LEAD_VERIFY_W63.md` §8 的 `+0x35A0` 推断，其数值预测在本卡 5 关上逐点成立**（M1..M5 = 0, 8, 9, 10, 11；两趟一致，`all_match=true`）。**没有出现与预测不符的实测值，因此不推翻 Lead 的任何一条表述**；本卡同时明确记录"预测成立 ≠ 机制被符号级证明"的边界（见 §4.4 / `DISAGREE.md`）。

---

## 1 · 五关逐关判定表（任务①）

`[本次实测]` 判据同 W63：`0x125C` 命中期望图名且 `frame>30` 记 enter；`GUI:Continue` 出现且 frame 停滞记 victory；点 `Continue` 后 `0x125C` 变为下一关且 frame 继续推进记 advance；终关点 `Continue` 后长时间不再出现新图名记 advance=false + EOG。

| 关 | 期望 `0x125C` | enter | victory | advance | `+0x34AC` (EOG) | 关键截图 |
|---|---|---|---|---|---|---|
| **M1** | `RA2F_M1.MAP` | ✅ | ✅ | ✅ → M2 | 0 | `screen_enter_RA2F_M1.png` / `screen_victory_M1.png` |
| **M2** | `RA2F_M2.MAP` | ✅ | ✅ | ✅ → M3 | 0 | `screen_enter_RA2F_M2.png` / `screen_victory_M2.png` |
| **M3** | `RA2F_M3.MAP` | ✅ | ✅ | ✅ → M4 | 0 | `screen_enter_RA2F_M3.png` / `screen_victory_M3.png` |
| **M4** | `RA2F_M4.MAP` | ✅ | ✅ | ✅ → M5 | 0 | `screen_enter_RA2F_M4.png` / `screen_victory_M4.png` |
| **M5** | `RA2F_M5.MAP` | ✅ | ✅ | **false（终关）** | **1（进关即置位）** | `screen_enter_RA2F_M5.png` / `screen_victory_M5.png` / `screen_final_after_M5_continue.png` |

两趟原始判定（逐字节落盘 `out\TRIP_trip1.json` / `out\TRIP_trip2.json`）：

| 趟 | `ok` | `outcome` | pid（自启） | M5 `advance` | M5 `end_of_game` | `no_extra_start` | 锁 |
|---|---|---|---|---|---|---|---|
| trip1 | `true` | `FULL_CHAIN_M1_M5` | 12856 | `false` | `1` | `true` | `w76`→`lead` |
| trip2 | `true` | `FULL_CHAIN_M1_M5` | 35376 | `false` | `1` | `true` | `w76`→`lead` |

`[本次实测]` 终关判据细节（两趟相同）：最后一次 `GUI:Continue` 后连续 **71.22 s / 47 次采样**，`0x125C` 恒为 `RA2F_M5.MAP`、`+0x35A0` 恒为 11、`+0x34AC` 恒为 1、`frame` 恒为 210；`extra_scenario_candidates=[]`。`screen_final_after_M5_continue.png` 目视是 **CREDITSMD.TXT 片尾职员表**（Assistant Coordinator / Production Assistants / Teleprompt Operator / Ultimate Operator / Concept Artist / Storyboard Artist…），不是第 6 关。与 W59 静态预测 `EndOfGame!=0 → 0x6859EE → CREDITSMD.TXT` 一致 `[转引 W59/W63]`。

`[本次实测]` 全程 **`MSG:UnableMapSelect` = 0 次**（字符串计数 0；`Invalid stage` 0；`error_dialog` / `trip_blocked` / `FATAL` 事件 0）。`run.ndjson` 共 253 条/趟，无 blocked/fatal/error 事件。

`[本次实测]` 独立旁证：两趟真机各自在游戏目录生成 **5 份 `RA2F_M1..M5.sav`**（收尾时按 `added` 删除，删除前已登记）。这是"5 关确实逐关进去过"的不依赖字段/截图的物证，与 W63 的三份 `.sav` 同构。

---

## 2 · 字段轨迹（任务①的逐关内存读数）

`[转引 W59]` 观测点：`Scen* = *(DWORD*)0x00A8B230`；`+0x125C` `char[0x104]`；`+0x35A0` WORD；`+0x34AC` BYTE (EndOfGame)；`+0x34AE` BYTE (SkipScore)；`+0x34B0` BYTE (SkipMapSelect)；`+0x34CC` DWORD (BattleIdx)；`frame = *(DWORD*)0x00A8ED84`。全部只读 `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`，未写内存/未下断点/未挂线程/未注入/未改 exe。

`[本次实测]` trip1 逐关进关瞬时读数（trip2 见 `out\trip2\FIELD_TABLE.json`，`+0x35A0` 序列完全相同）：

| 关 | `0x125C` | `+0x35A0` | `+0x34AC` | `+0x34AE` | `+0x34B0` | `+0x34CC` | `scen_next` | frame |
|---|---|---:|---:|---:|---:|---:|---|---:|
| M1 | `RA2F_M1.MAP` | **0** | 0 | 0 | 0 | 1 | `RA2F_M2.MAP` | 39 |
| M2 | `RA2F_M2.MAP` | **8** | 0 | 0 | 0 | 1 | `RA2F_M3.MAP` | 98 |
| M3 | `RA2F_M3.MAP` | **9** | 0 | 0 | 0 | 1 | `RA2F_M4.MAP` | 98 |
| M4 | `RA2F_M4.MAP` | **10** | 0 | 0 | 0 | 1 | `RA2F_M5.MAP` | 99 |
| M5 | `RA2F_M5.MAP` | **11** | **1** | 0 | 0 | 1 | `RA2F_M5.MAP` | 98 |

`0x125C` 全链轨迹：`RA2F_M1.MAP → RA2F_M2.MAP → RA2F_M3.MAP → RA2F_M4.MAP → RA2F_M5.MAP →（冻结）`。无 `ECH0x.MAP`、无官方 `SOV01umd.MAP`、无第 6 个文件名。frame 在每关结算屏停滞于 210（`survive(8)` → 结算屏"所花時間 00:00:07"），点 `Continue` 后重新推进（每次 `level_advance` 的 `frame_advancing=true`）。

---

## 3 · 截图清单（`out\`，SHA-256 前 12 位可回对原始文件）

`[本次实测]` trip1 主用截图（trip2 同名同位置，哈希见 `out\trip2\*`）：

| 文件 | 字节 | SHA-256(12) | 目视内容 |
|---|---:|---|---|
| `screen_S0_main_menu.png` | 319,586 | `ff4603b947d3` | 主菜单 `GUI:SinglePlayer` |
| `screen_S2_campaign_menu.png` | 235,266 | `16f2e0a335db` | 战役菜单 `GUI:CampaignMenu`（两徽章） |
| `screen_after_SOVIET_badge.png` | 4,845 | `e2f372755d4f` | 点徽章后过渡帧（近黑，不作进图证据） |
| `screen_enter_RA2F_M1.png` | 1,416,246 | `26f14d856cf2` | M1 局内：40×40 TEMPERATE 草地、未探索黑雾、苏军建造厂+电厂+2 坦克+步兵 |
| `screen_enter_RA2F_M2.png` | 1,163,089 | `69f4f5d89e62` | M2 局内 |
| `screen_enter_RA2F_M3.png` | 1,284,554 | `28d4c22f13e4` | M3 局内 |
| `screen_enter_RA2F_M4.png` | 1,163,235 | `d024a67d0c77` | M4 局内 |
| `screen_enter_RA2F_M5.png` | 1,442,090 | `96fe5b6c1303` | M5 局内（右下「未探索之地形」） |
| `screen_victory_M1.png` | 247,902 | `7f1037e6d4c1` | 结算屏：任務積分 / 平均時間 00:01:00 / 所花時間 00:00:07 / 苏军徽章 / 「繼續戰役」 |
| `screen_victory_M2.png` | 247,397 | `53146cb8c801` | M2 结算屏 |
| `screen_victory_M3.png` | 247,397 | `53146cb8c801` | M3 结算屏 |
| `screen_victory_M4.png` | 247,902 | `7f1037e6d4c1` | M4 结算屏 |
| `screen_victory_M5.png` | 247,902 | `7f1037e6d4c1` | M5 结算屏 |
| `screen_final_after_M5_continue.png` | 152,420 | `496e96575383` | **M5 终局片尾职员表（CREDITSMD.TXT）** |

`[口径纪律]` 结算屏哈希在不同关/不同趟之间重复（如 trip1 的 M1/M4/M5 同为 `7f1037e6d4c1`、M2/M3 同为 `53146cb8c801`；trip2 又出现 `c4ea0b252b76`）。这是**静态结算模板**所致，照 W63 口径**不当作"5 次不同胜利"的独立证据**；每关胜利另由该关 `level_victory` 的 `w59`（`0x125C` 分别为 `RA2F_Mk.MAP`、frame=210 停滞）+ `GUI:Continue` 控件枚举 + `0x125C` 推进链独立支撑。

---

## 4 · 任务②：用 5 关数据点检验 Lead 的 `+0x35A0` 推断（本卡科研价值）

### 4.1 被检验的推断与预测

`[转引]` `REVIEW\LEAD_VERIFY_W63.md` §8（Lead 标 `[静态推断·较强]`）：
> `Scen+0x35A0` 存的是「**推进到当前关时所消费的那个阶段记录的键**」，不是当前关自己的键。
> 依据 3 个数据点：三关链里 M1 中=0、M2 中=8、M3 中=9，而阶段键是 `8=M1 / 9=M2 / 10=M3`。

`[转引]` Lead 同时写了两条派生表述：
- (a) 「**不是当前关自己的键**」；
- (b) 「**最后一关的阶段记录不会被消费**」（W63 里键 10 = M3 自己的阶段记录从未被消费）；
- (c) 边界：「3 个数据点不足以排除偶合（例如它是『最后一个被解析的键』而非『被消费的键』）；要坐实需再看一个 4 关链或观察阶段表解析时的读点（`0x5CF830`）」。

本卡 `MAPSELMD.INI` `[Nod]` 追加键 **8=M1 / 9=M2 / 10=M3 / 11=M4 / 12=M5**。按 Lead 的推断外推，预测为：

| 关 | M1 | M2 | M3 | M4 | M5 |
|---|---:|---:|---:|---:|---:|
| **Lead 预测 `+0x35A0`** | **0** | **8** | **9** | **10** | **11** |

（M1 由 battle `Scenario=` 直接进入、未经阶段表 ⇒ 0；M2..M5 分别是"消费了键 8/9/10/11 的阶段记录"后进入；键 12 = M5 自己的阶段记录，按 (b) 永不被消费。）

### 4.2 对照表：关 / 实测 / Lead 预测 / 是否吻合

`[本次实测]` 两趟真机逐关进关瞬时读数：

| 关 | trip1 实测 `+0x35A0` | trip2 实测 `+0x35A0` | Lead 预测 | trip1 吻合 | trip2 吻合 |
|---|---:|---:|---:|---|---|
| **M1** | **0** | **0** | 0 | ✅ | ✅ |
| **M2** | **8** | **8** | 8 | ✅ | ✅ |
| **M3** | **9** | **9** | 9 | ✅ | ✅ |
| **M4** | **10** | **10** | 10 | ✅ | ✅ |
| **M5** | **11** | **11** | 11 | ✅ | ✅ |

`all_match = true`（两趟各自 `out\trip1\FIELD_TABLE.json` / `out\trip2\FIELD_TABLE.json` 的 `all_match` 均为 `true`；`TRIP_trip*.json` 的 `task2_all_match` 亦为 `true`）。两趟 `+0x35A0` 序列 `[0,8,9,10,11]` 逐项相同 ⇒ 不是偶发。

### 4.3 判定

`[本次实测]` **Lead 的数值预测在 5 个数据点上全部成立（2 趟一致）。本卡没有观测到任何与预测不符的值，因此不推翻 Lead 的 §8 主表述，也不推翻 (a)/(b) 两条派生表述。不替 Lead 圆场、也不硬找分歧：预测对，就写对。**

具体加固的点：

1. **"不是当前关自己的键"**：M5 自己的键是 **12**，实测 **11**；M1 自己的键是 **8**，实测 **0**。若 `+0x35A0` 存当前关自己的键，序列应为 8/9/10/11/12，与实测 0/8/9/10/11 全不符 ⇒ 该替代假设被 5 点排除。
2. **"最后一关的阶段记录不会被消费"**：M5 实测 11（= M4 的阶段键），**键 12 在两趟全链 5 关里一次都没出现** ⇒ (b) 在 5 关链上得到直接正向支持（W63 只有 3 关、终关键 10 未被消费；本卡把终关键推到 12 仍未被消费）。
3. **"M1 = 0 是因为 battle `Scenario=` 直接进入、没走阶段表"**：M1 两趟均为 0，且 `+0x125C=RA2F_M1.MAP` 在点苏联徽章后立即出现（frame=0）而 `+0x35A0` 未写 ⇒ 与 W63 一致。
4. **排除"最后一个被解析的键（=12 常量）"**：若引擎把 `[Nod]` 1..12 全枚举后把末尾键写入 `+0x35A0`，则 5 关都应是 12；实测 0/8/9/10/11 与之全不符 ⇒ Lead §8 (c) 举的那个具体"偶合"形式被 5 点排除。
5. **排除"下一关的键"**：若存的是下一关的键，M1..M4 应为 9/10/11/12，实测 0/8/9/10/11 不符。

### 4.4 诚实边界：预测成立 ≠ 机制被证明（本卡不升级签发强度）

`[静态推断]` 本卡**不**把 Lead 的 `+0x35A0` 语义从 `[静态推断·较强]` 升格为 `[本次实测]` 的符号级结论，理由：

- 本包追加的 `[Nod]` 键是**连续的 8..12**（引擎要求 `1..N` 连续，首个缺键即停 `[本次读码 mapselmd.py:263-287 / W59]`）。因此"**被消费的阶段键**"与"**一个以首追加键 8 为基数、每推进一次 +1 的计数器**（M1 特例 0）"在本包上给出**完全相同的** 0/8/9/10/11 序列，5 个数据点无法把两者分开。Lead §8 (c) 里"要看阶段表解析读点 `0x5CF830` 才能坐实"的保留意见**依旧成立**：本卡只做了"更长的链"，没有做"解析时读点"。
- 同理，"最后一个被解析的键"若指的是"扫描到匹配当前图的那个键就停"，则它与"被消费的键"是同一件事、不构成可区分的替代假设；本卡排除的只是"末尾常量 12"那一种读法。
- 要把机制坐实，可行的判别实验是让**被消费的键不连续**（在阶段表中间插入合法但不指向我方关卡的填充阶段，使我方 M1..M5 的阶段键变成 8/10/12/14/16），再看 `+0x35A0` 是跟"键"还是跟"推进计数"走。该实验**未运行**，见 `UNKNOWNS.md` U1 `[待运行验证]`。

> 结论口径：`[本次实测]`「Lead §8 的数值预测在 1 个 5 关包 / 2 趟 / 1 机 / 1 镜像上逐点成立，且终关键 12 未被消费」；`[静态推断]`「`+0x35A0` 的**因果机制**仍是"被消费的键"这一解释，尚非符号级证明」。二者分开记账，不合并。

---

## 5 · 过渡瞬间采样（"先变 / 后写"顺序）

`[转引 W63 §2.1]` W63 观察到 `0x125C` 先变为新文件名、`+0x35A0` 后写（有 `stage=0` 的中间态）。本卡在 `wait_advance` 里对 4 次推进逐次密集采样并落盘 `transition_samples_full` / `transition_ordering`。

`[本次实测]` 两趟各 4 次推进，全部 `fn_changed_before_stage_written=true`，每次恰有 1 个中间态样本：

| 推进 | 中间态（`0x125C` 已变 / `+0x35A0` 未写） | 随后写入 |
|---|---|---|
| M1→M2 | `RA2F_M2.MAP`, stage=0, frame=0, eog=0 | stage=8, frame=20/21 |
| M2→M3 | `RA2F_M3.MAP`, stage=0, frame=0, eog=0 | stage=9, frame=20/23 |
| M3→M4 | `RA2F_M4.MAP`, stage=0, frame=0, eog=0 | stage=10, frame=21/20 |
| M4→M5 | `RA2F_M5.MAP`, stage=0, frame=0, **eog=1** | stage=11, frame=20 |

⇒ **先变 `+0x125C`、后写 `+0x35A0` 的顺序在 8 次推进采样（2 趟 × 4）里 8/8 成立**，与 W59 静态链「`0x686700` 先写 `+0x125C`、`0x5CF830` + `mov [ebx+0x35a0],ax` 后写 stage idx」一致 `[转引 W59]`。注意 M4→M5 的中间态 `eog` 已经是 1 而 `stage` 仍是 0：说明 `EndOfGame` 由地图 `[Basic]` 在加载时置位（`0x68A11F`），与 stage idx 的写入是**两个独立的先后动作**，这进一步支持"`+0x35A0` 不是进关时由地图直接带入、而是推进状态机后写"的观察。

`[边界]` 采样间隔 1.5 s，只能证明"在这 1.5 s 窗口内先观测到文件名变化、后观测到 stage 写入"，不能给出指令级先后；不写成指令级证明。

---

## 6 · 离线包与安装（`[本次实测]`，离线阶段不占锁）

| 项 | 实测 |
|---|---|
| 工具链 | `W60_battlemd_inplace\ra2forge_patched_v15\`（v15），本卡未改其任何字节；`python -m ra2forge build --design work\w76_design.json --out work\pkg --feature-set work\w76_feature_set.json` → **exit 0** |
| 5 张地图 | `RA2F_M1..M5.MAP`：40×40 TEMPERATE、Russians、`size=[40,40]`、每关 ≥1 `NACNST`+`NAPOWR`+`MTNK`+步兵；`survive(8)` 编译为 `ElapsedTime(8)`→`WinnerIs(Russians)` `[本次读码 builder.py]`；结算屏"所花時間 00:00:07" |
| `[Basic]` | M1–M4 `EndOfGame=no` + `NextScenario=RA2F_M(k+1).MAP`；M5 `EndOfGame=yes` + `NextScenario=`（空）；五者 `SkipMapSelect=no` |
| `BATTLEMD.INI` | `battlemd.mode=inplace`，目标 `[SOV1]`，`Scenario=RA2F_M1.MAP`；2,732 B / 145 CRLF / 0 bare LF / SHA `8fb51769216d36af88…`；官方样板 2,733 B `7e40691a…` 逐行 diff 1 行；`Scenario=SOV01umd.MAP` 计 0 次 |
| `MAPSELMD.INI` | 克隆官方 5,573 B（`074ccccd…`）为基座；`[Nod]` 在官方 7 项（`1=Sov01..7=Sov07`）后**追加 5 个阶段，键 8,9,10,11,12，1..12 连续、≤100**；5 个阶段段 `Scenario=RA2F_M1..M5.MAP`，UI 字段克隆 `[Sov07]`；**主用变体 A（from1）**：4 个非终关阶段各 1 个子项 `1=<下一阶段名>`（从 1 连续），终关 M5 阶段无子项；6,986 B / SHA `223da0b27b99…`。对照变体 B（v15 原生 `2=`，未运行）SHA `333e932d6a36…`，单变量仅子项键 1= vs 2= |
| 安装 | `install --package … --feature-set …` → exit 0；`verify --game sandbox --json` → exit 0；`.bak` 在位且 == 官方 2,733 B；清单 `original_sha256 == 7e40691a…`、`post_install_sha256` == 磁盘、`inplace_rewrite` 报告嵌入；安装的 `MAPSELMD.INI` == 变体 A 逐字节 |
| 沙箱 | `robocopy ra2youli → sandbox_game`（只读源）rc=1；`real_pre` / `sandbox_pre` 均 647 文件 / 1,989,215,270 B / 277 地图类，四项锚哈希与 W44 签发基线一致；21 项可写配置字节副本 + 哈希存 `out\pristine\` |

`[本次读码]` `mapselmd.py:206-228`（阶段名 `RA2F_<MAP>_<sha256[:8]>` 确定性生成）、`:263-287`（`[Nod]` 键 1..N 连续、`FACTION_KEY_MAX=100`）、`:289-321`（每关一段、终关无子项、`CHILD_COLOUR_INDEX=2`）；`builder.py`（`survive→ElapsedTime/WinnerIs`、`EndOfGame=yes` 末关约定）。

---

## 7 · 真机纪律（红线逐条自证）

| 红线 | 本卡 |
|---|---|
| 每趟一趟一锁 | trip1 `owner=lead`→`w76`(07:26:12)→`lead`(07:29:07)；trip2 `lead`→`w76`(07:32:25)→`lead`(07:35:18)。**未跨趟长期持锁**；离线/收尾阶段始终 `owner=lead`，收尾复核仍 `owner=lead` |
| 不写 `ra2youli` | 只跑沙箱副本；真目录 PRE/POST 全树 `IDENTICAL_TREE=True`（647 / 1,989,215,270 B，`gamemd.exe` 仍 `73201cc0…`）→ `REAL_DIR_PROOF.txt` |
| 只关自己启动的 gamemd.exe | 记 pid（trip1 **12856** / trip2 **35376**），`WM_CLOSE` → `taskkill /PID <own>` → `/F`；`residual_own_pid=0`；全程/收尾全局 `gamemd` 残留 0；**未 blanket taskkill** |
| 启动前沙箱可写配置字节副本 + 哈希；收尾逐字节还原并实算自证 | 21 项 = 20 项 `byte_identical=True` + 1 项 `.seal` `removed_absent_baseline`；`BATTLEMD.INI` 还原 2,733 B / `7e40691a…`；沙箱 `identical_tree=True`；还原态 `verify` exit 0；沙箱目录已删 |
| 只写本卡目录；`git` 只读；不改 W21–W75 | 所有产物在 `W76_five_mission_chain\`；`git status` 仅显示本卡为 untracked，无 commit、无他卡改动 |
| 分级标注 | 全文按 `[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]` 分标 |
| 不写"多关链通用可通关" | 见 §8 边界：**只测了 1 个包 / 5 关 / 1 台机 / 1 个镜像 / 2 趟** |

`[本次实测]` 桌面预检（每次 WMI 启动后 30 s 内）：`WinSta0\Default`、369/371 windows、ImageGrab 2560×1440 OK、`pass=true`；只读采集（`PROCESS_VM_READ|PROCESS_QUERY_INFORMATION` + RPM、EnumWindows/EnumChildWindows、PIL.ImageGrab），无写内存/断点/挂线程/注入/改 exe。

---

## 8 · 结论强度与边界

可写（`[本次实测]`，本卡范围内）：
- 就地改写 `[SOV1]` + 5 阶段 `MAPSELMD.INI` 能把**本卡这 1 个 5 关包**送进游戏并走完 M1→M5，M5 `EndOfGame=yes` 终止、无第 6 关，2 趟一致。
- `+0x35A0` 在这 5 关上的实测序列为 0,8,9,10,11（2 趟一致），与 Lead §8 数值预测逐点吻合，终关键 12 未被消费。
- 4 次推进 × 2 趟 = 8 次采样全部支持"先变 `+0x125C` / 后写 `+0x35A0`"。

不可写 / 不外溢：
- ❌ **不写「多关链通用可通关」**：只测了 **1 个包、5 关、1 台机、1 个镜像、2 趟**；未测其它包、其它关数、其它分辨率/语言版本、其它镜像。
- ❌ 不写「(a) 是唯一可行路线」；`(c)` 改 exe 本轮未做、未比较优劣。
- ❌ 不写「`+0x35A0` 语义已被符号级证明」：因果机制仍按 `[静态推断·较强]` 记账（§4.4）。
- ❌ 不写「官方战役不受影响」：`[SOV1]` 在装包状态下被占用（虽可逐字节还原）。
- ❌ 不主张「`MAPSELMD` 子项键从 1 连续是必需项」：本卡只证明主用变体 A（from1）在 `SkipMapSelect=no` 上够用；变体 B（`2=`）未跑 A/B 单变量真机对照。
- ⚠ 未运行/未覆盖：见 `UNKNOWNS.md`（非连续阶段键判别实验、`0x5CF830` 解析读点、`SkipMapSelect=yes`、>5 关、其它语言/分辨率、变体 B 真机对照、官方全战役通关）。

`[转引]` 本卡复用并复现 W63/W70 的三关链结论（`(a)` 路线、`EndOfGame` 终止闸、`MAPSELMD` 阶段表驱动 >2 关、INI 数字键 ≤100、`Scen* = *(DWORD*)0xA8B230`），未重新论证。

---

## 9 · 交付清单

- `FIVE_CHAIN_RESULT.md`（本文）、`REAL_DIR_PROOF.txt`、`UNKNOWNS.md`、`DISAGREE.md`、`STARTED.txt`、`HEARTBEAT.txt`
- `out\`：`offline.ndjson` / `run.ndjson`（trip2 末态）/ `finalize.ndjson`；`TRIP_trip1.json` / `TRIP_trip2.json` / `TRIP_RESULT.json` / `FIELD_TABLE.json`；`out\trip1\` 与 `out\trip2\` 各自完整快照（含该趟 `run.ndjson`、截图、console log、分析文本）
- `out\screen_*.png`：每关进关 + 结算 + 终局 + 菜单，共 14 张/趟
- `out\cmd_*.log`：build / robocopy / verify_pre / uninstall_v03 / verify_v03 / verify_after_uninstall_v03 / install_inplace_plain / verify_after_install / uninstall_final / verify_post_restored_sandbox
- `out\real_pre.json` / `real_post.json` / `sandbox_pre.json` / `sandbox_post.json` / `FINALIZE.json` / `INPLACE_INSTALL.json` / `PACKAGE_VERIFY.json` / `MAPSELMD_VARIANTS.json` / `MAPSELMD.INI.variant_from1` / `.variant_from2` / `out\pristine\`
- `work\w76_design.json` / `w76_feature_set.json` / `pkg\W76FiveChain\` / `tools\w76_*.py`（W63 工具的**本卡副本**，路径重指到 W76，未 import 他卡脚本；5/5 `py_compile` 通过）

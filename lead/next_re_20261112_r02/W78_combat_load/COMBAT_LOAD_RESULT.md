# W78 · COMBAT_LOAD_RESULT — 从 8 秒速通到真实战斗负载下的通关验证

> 执行者 **Hy4**（W78，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W78_combat_load\`
> `STARTED.txt` 写在读任何文件之前：`2026-11-14T07:36:39+08:00[Asia/Shanghai]`（ISO UTC `2026-11-13T23:36:39Z`，`Hy4`，`lock per trip`）；`HEARTBEAT.txt` 每 ~10 min 更新。
> 离线读码/造包/装沙箱 `07:36–07:56`；真机 trip1 `07:56:55–08:00:31`、trip2 `08:06:46–08:08:45`、trip3 `08:11:44–08:13:52`、trip4 `08:21:03–08:23:12`；收尾 `08:24:17–08:24:27`；报告 `08:25–`。时间盒 140 min 内完成，**未触发「90 分钟只做到图造好但没进真机」的降级条款**。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本报告不签发（签发权在 Lead）。

---

## 0 · 一句话结论

`[本次实测]` **本卡造出并真机跑通了一张 60×60、双方都有实质兵力、敌方主动进攻的「真实战斗」地图；在真实战斗负载下：游戏不崩、frame / `0x125C` / `0x34AC` / `0x35A0` 等可观测量全程稳定可读、结算屏与 `EndOfGame` 终止正常，2 关链也能从真实战斗关推进到第二关。** 这是 W63/W70/W76（全部 `survive(8)` 速通）从未验证过的负载条件。

`[本次实测]` **但「歼灭胜利」这条路线没有通关**：schema/builder 会 emit 歼灭触发器，两次真机尝试一次僵持 150 s 无结算、一次玩家先战败；最终拿到胜利结算的是**时间触发变体**。且该时间触发变体的胜利屏出现在 wall t≈29.6 s 而非设计值 55 s，判胜来源存在未澄清的二义性（§7 / UNKNOWNS.md U1、U2）。两条都如实登记为运行时能力/认知缺口，不粉饰。

---

## 1 · 任务①：ra2forge 触发能力清单（`[本次读码]`）

读 `ra2forge\design.py`、`builder.py`、`triggers.py`、`maplib.py`、`docs\DESIGN.md` 及 v15 同源文件。

### 1.1 胜利条件类型（能编译成 `WinnerIs` 的 win-type objectives）

| design JSON `type` | 关键字段 | builder 编译出的事件 | 动作 | 语义 |
|---|---|---|---|---|
| `survive` | `seconds: int` | `event 13 ElapsedTime(seconds)` | `action 1 WinnerIs(player)` | **时间触发判胜**（W63/W70/W76 唯一用过） |
| `destroy_all_forces` | `enemy: <country>` | `event 11 AllDestroyed(house_idx)` | `action 1 WinnerIs(player)` | **歼灭全部敌方兵力**（含单位+建筑） |
| `destroy_all_buildings` | `enemy: <country>` | `event 10 AllBuildingsDestroyed(house_idx)` | `action 1 WinnerIs(player)` | 摧毁敌方全部建筑 |
| `destroy_building` | `structure_tag: <tag>` | `event 7 DestroyedByAnyHouse`（经 tag 挂在建筑上） | `action 1 WinnerIs(player)` | **摧毁特定建筑** |

`builder.py:435-480`：多个 win-type objective 会**链式 enable**（前一个启用后一个，最后一个才 `WinnerIs`），不是「谁先到谁赢」的 OR；本卡因此每个变体只用 1 个 win objective。

### 1.2 事件型 objectives（不判胜，但驱动战斗/演出）

`design.py:57-58` `EVENT_ONLY_OBJECTIVES`：`reinforce`（team+TaskForce/TeamType/Script）、`text`（action 11）、`speech`（action 21）、`timer`（action 27 TimerSet + 23 TimerStart）、`reveal_map`（action 16 RevealAllMap）、`reveal_waypoint`（action 17）、**`hunt_wave`（`house` + `at_second` → `action 6 AllToHunt(house_idx)`，让该方全部单位主动进攻）**。

### 1.3 可用设计 JSON 写法（歼灭类，本卡实际使用）

```json
{
  "type": "destroy_all_forces",
  "enemy": "British"
}
```
配合让敌方主动进攻：
```json
{ "type": "hunt_wave", "house": "British", "at_second": 3 }
```
本卡 `work\pkg_v2_annih\W78CombatLoad\RA2F_M1.MAP` 编译结果（逐字节核对）：
```
[Events]  0B00001C=1,11,0,4          ; AllDestroyed, P2=4 = British
[Actions] 0B00001C=1,1,0,8,0,0,0,0,A  ; WinnerIs, P2=8 = Russians
[Events]  0B000070=1,13,0,3          ; ElapsedTime(3)
[Actions] 0B000070=1,6,0,4,0,0,0,0,A  ; AllToHunt, P2=4 = British
[Events]  0B000000=1,11,0,8          ; Defeat: AllDestroyed(Russians)
[Actions] 0B000000=1,2,0,8,0,0,0,0,A  ; LoserIs(Russians)
```
`maplib.py:279-282` `[Houses]` 按 `STANDARD_HOUSES` 顺序写（0=Americans … 4=British … 8=Russians），与 `design.HOUSE_INDEX` 一致 ⇒ house index 接线正确（本卡刻意选 **British=4** 而非 Americans=0，避开 P2=0 可能被当作"未设置"的歧义）。

### 1.4 直接回答任务①

1. **支持哪些胜利条件？** 不止 `survive/ElapsedTime`。共 4 类可判胜：`survive`（时间）、`destroy_all_forces`（歼灭全部敌方）、`destroy_all_buildings`、`destroy_building`（摧毁特定建筑）。另有 7 类事件型 objective（含 `hunt_wave` 让敌方主动进攻）。
2. **有没有"歼灭全部敌方"/"摧毁特定建筑"/"占领"？** 前两者**有**；**「占领 / capture」类没有**（schema、builder、triggers 全无对应类型）。
3. **若不支持就写「当前只支持时间触发」并登记能力缺口？** → **不适用**：schema/builder 层确实支持战斗结果驱动的胜利，不能写「当前只支持时间触发」。
   **但本卡真机发现运行时层的能力缺口**：歼灭类触发器会被 emit，却没有一次在真实战斗负载下产生胜利结算（§4）。产品结论应区分「能 emit」与「能判胜」，见 `DISAGREE.md` D1/D2。

`[静态推断]` `triggers.py:1-25` 的索引来自 WAE Default Events/Actions + 官方 YR 地图交叉核对；`docs/DESIGN.md` 记录 per-mission `next` 覆盖与 `campaign.id`。所有结论均为读码，未经符号级反汇编复核。

---

## 2 · 任务②：真实战斗地图设计（`[本次实测]` 离线构建 + `[本次读码]`）

### 2.1 布局（v2，最终用于通关/推进的两个包）

| 项 | 值 |
|---|---|
| 地图 | `RA2F_M1.MAP`，`size=[60,60]`，TEMPERATE，全平坦草地（60×60 交战空间） |
| 我方 | `Russians`（苏军，PlayerControl=yes）：`NACNST` 建造厂 + 2× `NAPOWR` 电厂；**10 辆 `MTNK` 坦克 + 4 名 `E2` 动员兵**（`mission=Guard`），credits 10000 |
| 敌方 | `British`（盟军，DarkBlue，IQ=2，credits 0）：**6 辆 `MTNK` 坦克 + 6 名 `E1`**（全部 `mission="Hunt"`），**无任何建筑**，起始 rows 40–45 / cols 32–46（贴近我方坦克线、进图即在镜头内） |
| 主动进攻 | 单位 `mission="Hunt"` **且** `{"type":"hunt_wave","house":"British","at_second":3}`（action 6 AllToHunt 双保险） |
| 演出/侦察 | `text`(action 11, t=1)、`reveal_map`(action 16, t=1，全图可见于截图) |
| 胜利条件 | 变体 **annih**：`destroy_all_forces(British)`；变体 **time**：`survive(55)`（45–60 s 区间） |
| `[Basic]` | 单关：`NextScenario=`（空）、`EndOfGame=yes`、`SkipMapSelect=no`；2 关链 M1：`NextScenario=RA2F_M2.MAP`、`EndOfGame=no` |

v1（trip1 用）与 v2 唯一差别：敌方在 rows 8–14（地图远端，~35 格外）。v1 造成远程僵持，故 v2 把敌方移近。

### 2.2 构建与安装（`[本次实测]`）

- 工具链：`W60_battlemd_inplace\ra2forge_patched_v15\`（**未改其任何字节**），命令同 W76 §6：
  `python -m ra2forge build --design <design> --out <out> --feature-set <fs>` → exit 0，5/5 包全部 `PACKAGE_VERIFY` PASS。
- 包：`work\pkg_annih\`（v1 annih）、`work\pkg_time\`（v1 time，仅离线编译未真机）、`work\pkg_v2_annih\`、`work\pkg_v2_time\`、`work\pkg_chain\`（2 关链）。
- `BATTLEMD.INI`：inplace 改写 `[SOV1] Scenario=RA2F_M1.MAP`，2732 B / SHA `8fb51769…`（官方样板 2733 B `7e40691a…`，逐行 diff 仅 1 行）；`Scenario=SOV01umd.MAP` 计 0。
- `MAPSELMD.INI`：clone 官方 5573 B，追加 1 阶段（单关，`[Nod]` 键 1..8）或 2 阶段（2 关链，键 1..9、主用变体 A `1=<下一阶段>`）。
- `expandmd98.mix`：maps only，无 INI。
- 沙箱：`robocopy ra2youli → sandbox_game`（只读源）rc=1；`real_pre` / `sandbox_pre` 均 647 文件 / 1,989,215,270 B / 277 地图类；21 项可写配置逐项处理（20 个实际文件字节副本 + 1 项基线不存在登记）存 `out\pristine\`。
- `install --package … --feature-set …` exit 0；`verify --game sandbox --json` exit 0；`.bak` 在位且 == 官方 2733 B；清单 `original_sha256 == 7e40691a…`、`post_install_sha256` == 磁盘、`inplace_rewrite` 报告嵌入。
- 所有工具为本卡副本 `work\tools\w78_*.py`（W63/W76 工具**复制后重指输出路径**，未 import 他卡脚本，8/8 `py_compile` 通过）。

### 2.3 关键验证点（任务②「真机」要求）
真机流程：装 inplace 包 → 进图 → **连续观测 ≥60 s（不提前退）** → 记录 frame 轨迹 / `0x125C` / `0x34AC` / `0x35A0` → 采「战斗确实发生」证据 → 结算屏截图 → 点 Continue → 验 `EndOfGame`。

---

## 3 · 真机读数总表（`[本次实测]`，4 趟 / 每趟一趟一锁）

观测点 `[转引 W59 / W63 / W76]`：`Scen* = *(DWORD*)0x00A8B230`；`+0x125C` 文件名、`+0x35A0` WORD 阶段键、`+0x34AC` BYTE EndOfGame、`+0x34AE` SkipScore、`+0x34B0` SkipMapSelect、`+0x34CC` BattleIdx；`frame = *(DWORD*)0x00A8ED84`（32 ms 计时器，~31.25/s）。全部只读 `OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory`，未写内存/未下断点/未挂线程/未注入/未改 exe。桌面预检每趟 `pass=true`（WinSta0\Default，ImageGrab 2560×1440 OK）。

| 趟 | 包 / 胜利条件 | 进关瞬时读数 | 战斗观测 | 结果 | 锁 / pid / residual |
|---|---|---|---|---|---|
| **trip1** | v1 annih（敌在远端）`destroy_all_forces` | `0x125C=RA2F_M1.MAP`, `0x35A0=0`, `0x34AC=1`, `0x34CC=1`, `scen_next=""`, frame=39 | **150.05 s / 147 样本**，frame 45→4734（~31.25/s）线性推进；全程 `0x125C` 恒 `RA2F_M1.MAP`、`0x35A0=0`、`0x34AC=1`、`0x34AE=0`、`0x34B0=0`、`0x34CC=1`、`battle_cnt=14` | **无结算屏**（`NO_RESULT_WITHIN_150s`）：敌方未被全歼，远程对射僵持；终局 25.94 s 复核仍 `RA2F_M1.MAP`、frame 继续推进 | `lead→w78→lead`；pid **36584**；0 |
| **trip2** | v2 annih（敌在近处）`destroy_all_forces` | 同上，frame=37 | 决定性可见交战；t≈69 frame 停滞于 2194，t≈71 出现 `GUI:OK/GUI:Cancel/GUI:Blank` 对话框 | **玩家战败**（RA2「確定要重新執行此場任務嗎？」）；脚本当时把 `GUI:OK` 误判为 error dialog 而 `trip_blocked`（见 U9）。歼灭胜利**未**触发 | `lead→w78→lead`；pid **34180**；0 |
| **trip3** | v2 **time** `survive(55)` 单关 | `0x125C=RA2F_M1.MAP`, `0x35A0=0`, `0x34AC=1`, frame=38 | **62.61 s / 59 样本**（≥60 s 窗口满足）；frame 45→915（~31/s）后停滞；`GUI:Continue/GUI:StandaloneScore/GUI:YourTime/GUI:ParTime/GUI:HeadsTaken` 计分屏在 **wall t=29.62 s / frame=915** 出现，`frame_stalled=true`（915→915） | **通关**：`ok=true`，`RESULT_AND_TERMINATION_OK`。点 `GUI:Continue` 后终局 25.78 s：`0x125C` 恒 `RA2F_M1.MAP`、`0x35A0=0`、`0x34AC=1`、`no_extra_start=true`、frame 恒 915 | `lead→w78→lead`；pid **22508**；0 |
| **trip4** | 2 关链：M1=v2 真实战斗 `survive(55)`，M2=`survive(8)` | M1 `0x125C=RA2F_M1.MAP`, `0x35A0=0`, **`0x34AC=0`**, **`scen_next=RA2F_M2.MAP`**, frame=40 | M1 同样 62.64 s / 59 样本，计分屏 **t=29.59 s / frame=915**，`frame_stalled=true` | **推进成立**：点 Continue 后终局 25.84 s，`0x125C` **17/17 样本 = `RA2F_M2.MAP`**、`0x35A0` **0→8**、frame 重新 0→210（M2 计分屏停滞）、`0x34AC=1`。脚本 `ok=false` 仅因单关判据 `no_extra_start` 对链必然为 False（**这正是 M2 启动的证据**） | `lead→w78→lead`；pid **35680**；0 |

**三个关键验证点（有真实负载）**
1. **游戏不崩** `[本次实测]`：4 趟均无进程自退、无 `FATAL`、无地图装载错误；trip1 连续 150 s 运行、trip3/trip4 各 62 s 观测期间 `process_alive=true`；`step0_desktop_precheck.pass=true` 4/4。
2. **帧/状态可观测量稳定可读** `[本次实测]`：战斗中 frame 稳定 ~31.25/s（trip1 45→4734 / 150 s；trip3 45→915 / 29.6 s），无因负载造成的读数失败；每次采样都能读到 `scen_ptr`、`0x125C`、`0x34AC`、`0x35A0`、`0x34AE`、`0x34B0`、`0x34CC`、`battle_cnt=14`、`scen_next`；无 `None`、无 RPM 失败。结算后 frame 停滞（trip3 915、trip4 M2 210）是可预期的判胜冻结，不是崩溃。
3. **结算与终止正常** `[本次实测]`：trip3 单关胜利计分屏 + `frame_stalled` + Continue 后 25.78 s 无第 2 个图名（`no_extra_start=true`）+ `EndOfGame` 字节 1；trip4 链 M1 胜利 → Continue → `0x125C` 变更到 M2（17/17）且 frame 重新推进，M2 自身也进到计分屏。

---

## 4 · 「歼灭胜利」为什么没有通关（`[本次实测]`，任务①能力缺口的 runtime 侧）

- `[本次读码]` 触发器**逐字节正确**：`0B00001C=1,11,0,4` → `1,1,0,8`（见 §1.3），house index 与 `[Houses]` 一致。
- `[本次实测]` trip1（v1，敌在 rows 8–14）：150 s 内我方基地与 10 辆坦克始终存在、敌方也未被全歼 ⇒ `AllDestroyed(British)` 从未满足 ⇒ **无 `WinnerIs`、无结算屏**。截图显示只有远距离对射（弹坑、炮口焰、冒烟）。
- `[本次实测]` trip2（v2，敌贴近）：这次是**我方**先被全歼 ⇒ `AllDestroyed(Russians)→LoserIs` 的**失败侧**触发（战败/重启对话框，frame 停滞 2194）⇒ 说明 AllDestroyed 事件机制本身在引擎里会触发，只是本卡没有让「敌方全灭」这一侧成立。
- ⇒ **不能写「歼灭类胜利已在真机验证可用」**。这是本卡登记的产品能力缺口（运行时层）：一个只有歼灭目标、且敌方能打成僵持或反杀的包，在真实战斗负载下可能永远不结算。判别实验见 UNKNOWNS.md U1。

---

## 5 · 任务③：真实战斗负载下的 2 关链推进（`[本次实测]`，trip4）

与 W76 五关链（每关 `survive(8)` 速通）不同的负载条件：**第一关是真实战斗**。

- 包 `work\pkg_chain\W78CombatChain\`：`RA2F_M1.MAP`（v2 真实战斗，`survive(55)`，`NextScenario=RA2F_M2.MAP`，`EndOfGame=no`）+ `RA2F_M2.MAP`（40×40，`survive(8)`，`EndOfGame=yes`）；`MAPSELMD` 追加 2 阶段、主用变体 A 子项键 `1=RA2F_RA2F_M2_0C0FDB07`、`[Nod]` 键 1..9 连续。
- M1 进关 `scen_next=RA2F_M2.MAP` / `0x34AC=0`（非终关）；M1 在真实交战后 t=29.59 s 出胜利计分屏、frame 915 停滞。
- 点 `GUI:Continue` 后：**`0x125C` 由 `RA2F_M1.MAP` 变为 `RA2F_M2.MAP`（终局 17/17 采样全部为 M2）**，`+0x35A0` 由 **0 → 8**（本卡 `[Nod]` 键 8 = M1 阶段被消费，与 W63 §8 / W76 数值预测一致 `[转引]`），`frame` 重新从 0 推进到 210（M2 `survive(8)` 计分屏停滞），`0x34AC`→1。
- 独立物证：游戏在沙箱自生成 `RA2F_M1.sav` 与 `RA2F_M2.sav`（收尾 diff 登记后删除），与 W76 的 5 份 `.sav` 同构。
- ⇒ **推进在战斗负载下成立**；但只测了这 1 个 2 关包 / 1 趟（trip4），不外溢到其它关数或其它包（U7/U8）。

---

## 6 · 「战斗确实发生了」的证据与强度（`[本次实测]`）

任务允许「若知道单位表地址就读单位计数变化；不知道就用截图 + 帧率变化做间接证据，并注明是间接的」。**本卡没有在本机 gamemd.exe 上验证过任何活单位表地址**（`0x00A8B270` 是 Rules 的 `UnitCount` 全局镜像／多人设置项，`0xA8EAE8` 是 `DynamicVector<TriggerClass*>`，都不是局内活单位数），按红线「不臆造地址」**未编造单位计数**（U3）。改用下列证据，逐条标强度：

### 6.1 直接视觉证据（强，游戏渲染的客观画面）

| 截图（`out\`） | 目视内容 | 强度 |
|---|---|---|
| `screen_trip1_enter.png` (3,140,677 B / `f3c77bbd4de6`) | 60×60 全图可见（`reveal_map` 生效）：苏军建造厂 + 2 电厂 + 10 坦克 + 步兵；双方实兵在场 | 直接（初始布阵） |
| `screen_trip1_combat_t20.png` (`17736fd8799d`) | **新出现多个弹坑**（对比 t0 无） | 直接（交火痕迹） |
| `screen_trip1_combat_t40.png` (`fc9a0923981a`) | **炮口焰/爆炸亮点**、炮塔转向、兵种提示「動員兵」 | 直接（正在开火） |
| `screen_trip1_combat_t60.png` (`32487c4a4b06`) | **坦克冒烟受损** | 直接（单位损失/受损） |
| `screen_trip2_combat_t60.png` (`c18ea4599808`) | **大量弹坑 + 苏军电厂起火燃烧 + 建造厂被毁 + 坦克冒烟 + 蓝色英军坦克在近处交战** | **直接且最强**：可见建筑被毁、单位损失、双方近距交战 |
| `screen_trip2_error_dialog_t71.png` (`0707c449129a`) | RA2「確定要重新執行此場任務嗎？」战败/重启确认框 | 直接（失败侧结算） |
| `screen_trip3_combat_t25.png` (`ab250e2c5936`) | **「任務完成」横幅**覆盖在仍有弹坑/残烟/蓝色坦克的活跃战场上 | 直接（战斗中判胜） |
| `screen_trip3_settlement.png` (`7250a388d4c8`) | 苏军锤镰胜利计分屏 + 「注意! 時間低於平均」 + 「繼續」按钮 | 直接（结算屏） |
| `screen_trip4_settlement.png` (`72a5de76feb9`) / `screen_trip4_terminal.png` (`5ef45bba714c`) | 链 M1 胜利计分屏 / 终局 M2 计分屏 | 直接 |

**强度**：截图里能看到交战、弹坑、爆炸、起火建筑、冒烟受损单位、被毁建造厂 ⇒ 符合任务列举的「截图里能看到交战、单位损失」，属**直接视觉证据（强，但定性：无法给出精确击杀数）**。计分屏的击杀/损失数字因面板被裁切未能可靠读出（U4），不作为量化证据。

### 6.2 直接状态证据（强，游戏/引擎自生成，非截图目视）

- `[本次实测]` `frame_stalled=true`：trip3 frame 915→915、trip4 M1 915→915、M2 210→210 ⇒ `WinnerIs` 判胜使模拟冻结，非脚本推断。
- `[本次实测]` 计分屏控件枚举：`GUI:Continue` / `GUI:StandaloneScore` / `GUI:YourTime` / `GUI:ParTime` / `GUI:HeadsTaken`（trip3/trip4 各 1 次）。
- `[本次实测]` 游戏自生成 `RA2F_M1.sav` / `RA2F_M2.sav`（收尾 diff 的 `added` 两项，删除前已登记）⇒ 两关确实各进去过。
- `[本次实测]` `0x125C` 轨迹：单关恒 M1；2 关链 M1→M2（17/17）⇒ 推进真实发生。

### 6.3 间接证据（弱，仅标注、不单独作为结论）

- `[本次实测]` **frame 轨迹 / 帧率**：战斗中 frame ~31.25/s 线性推进（trip1 45→4734 / 150 s），判胜后停滞；全程无 stall 直到预期结算。这是「模拟在负载下持续运行且可观测量可读」的证据，**不是**「战斗发生」的直接证据 —— 按任务要求**注明为间接证据（弱）**，只用于支撑 §3 的验证点②。
- `[本次实测]` 可见控件文本 `["Yuri's Revenge"]`（战斗 HUD 用 DirectDraw 绘制，几乎无 Windows 子控件）⇒ 控件枚举本身不证明战斗，仅作旁证。

### 6.4 没有取到 / 不主张的证据
- ❌ 内存直读的**单位计数变化**（无已验证地址，U3）。
- ❌ 计分屏**击杀/损失数字**（面板裁切，U4）。
- ❌ 「单位表地址」类未验证偏移一律未写入结论。

**综合判定**：`战斗确实发生` = **直接视觉证据（强）+ 直接状态证据（强）+ 间接帧率证据（弱，仅辅助）**，三者一致；不是只靠帧率变化。强度边界：定性、单镜像、单布局，无量化击杀数。

---

## 7 · 结论与边界

### 7.1 可写（`[本次实测]`，本卡范围内）
- ra2forge **不是**「只支持时间触发」：schema/builder 支持 `destroy_all_forces` / `destroy_all_buildings` / `destroy_building` / `survive` 四类判胜，另有 `hunt_wave` 等 7 类事件型；**「占领」类没有**。
- 本卡造的 **1 张 60×60 真实战斗地图**（双方实兵、敌方 `Hunt` 主动进攻、`reveal_map` 全图）在真机上：不崩、W59 可观测量全程稳定可读、胜利计分屏与 `EndOfGame` 终止正常（trip3）、2 关链从真实战斗关推进到 M2 成立（trip4）。这补上了 W63/W70/W76「全部 8 秒速通」从未覆盖的负载条件。
- `MAPSELMD` 追加阶段 + 就地 `[SOV1]` 在**真实战斗负载**下仍能把包送进游戏并结算/推进；`+0x35A0` 0→8 与既有预测一致。

### 7.2 不可写 / 不外溢（红线）
- ❌ **不写「战役包支持任何类型战役」**：只测了本卡自己造的 1 个真实战斗布局及其派生包（v1 annih/time、v2 annih/time、2 关链共 5 个包，其中 v1 time 只离线编译未真机）、1 台机、1 个镜像、4 趟真机。
- ❌ **不写「歼灭类胜利可用 / 真实战役已可做」**：见 §4 / U1。
- ❌ **不写「`survive(55)` 在 55 s 触发 / 时间触发机制已被本卡验证」**：胜利屏在 wall ~29.6 s，判胜来源二义（U2 / D4）。
- ❌ **不写「战斗胜负可复现」**：同布局 annih 变体战败、time 变体胜利（U6）。
- ❌ 不写「MAPSELMD from1 必需」「官方战役不受影响」「帧率变化是战斗直接证据」「trip2 是引擎错误」。
- ⚠ 未运行/未覆盖见 `UNKNOWNS.md` U1–U9。

### 7.3 给产品的一条结论（本卡认为最值得上抛）
`[本次实测]` **「能 emit 歼灭触发器」≠「能在真实战斗负载下靠歼灭判胜通关」**。本卡 2 次歼灭尝试都没拿到结算，反而是有界时间触发拿到了完整结算+终止。若要做真实战役，至少要为「敌方打不干净/被反杀」准备有界的结算路径（时间触发或其它），否则可能像 trip1 一样 150 s 不结算。判别实验 U1/U2 未运行。

---

## 8 · 纪律逐条自证（红线）

| 红线 | 本卡 |
|---|---|
| 每趟一趟一锁，收尾 `owner=lead`，不跨趟长期持锁 | trip1 `07:56:55 lead→w78`→`08:00:31 lead`；trip2 `08:06:46→08:08:45`；trip3 `08:11:44→08:13:52`；trip4 `08:21:03→08:23:12`。离线/收尾始终 `owner=lead`；收尾复核 `owner=lead` |
| 不写 `ra2youli`；收尾 `IDENTICAL_TREE=True` 自证 | 只跑沙箱；真目录 PRE/POST 全树 **647 文件 / 1,989,215,270 B / 277 地图类**，`added=removed=changed=0`、mtime_diff=0、`identical_tree=True`；`gamemd.exe` 仍 `73201cc0…` → `REAL_DIR_PROOF.txt` |
| 只关自己启动的 `gamemd.exe`（记 pid，`residual=0`）；不 blanket `taskkill` | pid 36584 / 34180 / 22508 / 35680；每趟 `WM_CLOSE→taskkill /PID <own>→/F`，`residual_own_pid=0`，全局残留 0 |
| 启动前沙箱可写配置字节副本 + 哈希；收尾逐字节还原并实算自证 | `out\pristine\` 20 个实际文件 + 1 项 absent_baseline；收尾 21/21 全部逐字节一致/按基线移除；`BATTLEMD.INI` 还原 2733 B `7e40691a…`；还原态 `verify` exit 0；沙箱 `identical_tree=True` 后删除 |
| 只写本卡目录；`git` 只读；不改 W21–W77 | 所有产物在 `W78_combat_load\`；仅额外写 run 级 `.game_instance.lock`（锁协议要求）；无 commit；未改任何 W21–W77 文件 |
| 分级标注 | 全文 `[本次实测]/[本次读码]/[静态推断]/[转引]/[待运行验证]` 分标 |
| 不得写「战役包支持任何类型战役」 | 见 §7.2，只测了本卡造出来的那张图及其派生包 |

---

## 9 · 交付清单

- `COMBAT_LOAD_RESULT.md`（本文）、`REAL_DIR_PROOF.txt`、`UNKNOWNS.md`、`DISAGREE.md`、`STARTED.txt`、`HEARTBEAT.txt`
- `out\`：`build.ndjson` / `build_v2.ndjson` / `build_chain.ndjson` / `offline.ndjson` / `run_trip1..4.ndjson` / `finalize.ndjson`（9 个 ndjson）；`cmd_*.log`（15 个）；`*.json`（15 个，含 `BUILD_RESULT.json` / `BUILD_V2_RESULT.json` / `BUILD_CHAIN_RESULT.json` / `OFFLINE_*.json` / `TRIP_trip1..4.json` / `FINALIZE.json` / `real_pre.json` / `real_post.json` / `sandbox_pre.json` / `sandbox_post.json` / `INPLACE_INSTALL.json` / `PACKAGE_VERIFY.json` / `MAPSELMD_VARIANTS.json` 等）；`screen_*.png`（**64 张**，每趟进关/菜单/战斗 t=0..60/结算/终局）；`out\pristine\` 20 份字节副本；`out\trip1..\trip4\` 各趟 `TRIP_RESULT.json` + 截图副本
- `work\`：`w78_design.json`（v1 annih）、`w78_design_time.json`（v1 time）、`w78_design_v2.json` / `w78_design_v2_time.json`（v2）、`w78_design_chain.json`（2 关链）、`w78_feature_set.json` / `w78_feature_set_chain.json`、`MAPSELMD.INI.chain_from1` / `.chain_from2`；`pkg_annih\` / `pkg_time\` / `pkg_v2_annih\` / `pkg_v2_time\` / `pkg_chain\`（5 个包）
- `work\tools\w78_*.py`：`w78_lib.py`（W76 proven live lib 的本卡副本，路径重指）、`w78_common.py`、`w78_build.py`、`w78_build_v2.py`、`w78_build_chain.py`、`w78_offline.py`、`w78_run.py`、`w78_finalize.py`（全部本卡副本，未 import 他卡脚本；`py_compile` 通过）

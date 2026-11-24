# W79 · `survive(seconds)` 可靠性 + 歼灭胜利可达性（真机钉死 W78 两个缺陷）

> 执行者 **Hy4**（W79，非 Lead）｜卡目录 `lead\next_re_20261112_r02\W79_survive_and_annih\`
> `STARTED.txt` 写在读任何文件之前：`2026-11-14T08:21:17.8760902+08:00`（ISO + `Hy4` + `lock per trip`）
> 离线造 4 个包 + 装沙箱 `08:33–08:38`；真机 5 趟 `08:38:36–08:57:13`；收尾 `08:57:53–08:58:14`；报告 `08:59`
> 时间盒 150 min，实际约 38 min 完成，**A、B 两半都做完，没有降级**。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本报告**不签发**（签发权在 Lead）。

---

## 0 · 一句话结论

- **任务 A**：`[本次实测]` **`survive 不可靠（作为"存活 N 游戏秒"的计时语义）；但作为"判胜触发器"完全可靠、确定性、可复现、随 N 单调。规律：判胜 frame = 15×N + 90（即游戏秒 = 0.48×N + 2.88）`**。3 张同布局图 `survive(8)/(20)/(55)` 判胜 frame = **210 / 390 / 915**，与 W78 两趟 `survive(55)`（915、915）和 W76 五关链 10 次 `survive(8)`（210）**逐点吻合**。假说 1（饱和/截断）**否**，假说 2（另有触发源）**否**，假说 3（计时基准偏移）**定性成立但字面公式不成立**（斜率是 15 帧/设计秒，不是 31.25，且另有固定 +90 帧截距）。
- **任务 B**：`[本次实测]` **能判胜，`destroy_all_forces` 可用（重大能力确认）**。40 辆我方 MTNK 全 `Hunt` vs 4 个静止 British E1、`destroy_all_forces(enemy=British)`、无 `survive` ⇒ **frame 274（8.77 游戏秒）胜利结算屏**，结算屏引擎自报 **「殲敵軍數 4」= 敌方 4/4 全被清掉**，「所花時間 00:00:09」。额外对照趟证明引擎**不会**在敌方全灭时自动判胜，故该胜利确由 `AllDestroyed(British)→WinnerIs` 触发。
- **对既有结论**：`[本次实测 + 本次读码]` W63/W70/W76 的**"链推进/终止/重复性"结论不受影响**（它们只依赖"胜利触发发生"这一事实，而该事实现在被 6+ 个独立点证实为确定性）；**受影响的只是"8 秒"这个时序说法**（`survive(8)` 实为 ≈6.72 游戏秒 / 引擎显示 00:00:07），不是 8 真实秒。

---

## 1 · 任务 A：`survive(seconds)` 三点表与判定

### 1.1 实验设计（`[本次读码]` + `[本次实测]`）

3 张图**同一布局**，唯一差异是 `survive` 秒数：

| 项 | 值 |
|---|---|
| 地图 | 60×60 TEMPERATE，`EndOfGame=yes`，`SkipMapSelect=no`，`NextScenario=`（单关终止） |
| 我方 | Russians：`NACNST`×1 + `NAPOWR`×2 + `MTNK`×10 + `E2`×4，**全部静止无 mission** |
| 敌方 | British：**4 个 E1，`Guard`（静止、不 Hunt）**，rows 5–8，距我方约 40 行 |
| objectives | `text(at_second=1)` + `survive(N)`，`N ∈ {8,20,55}` |

**为什么这样设计**：
- 双方静止且相距很远 ⇒ **零战斗**，不污染计时；三张图结算屏引擎自报「殲敵軍數 **0**」（`screen_trip{1,2,3}_settlement_confirm.png`）证实。
- 敌方**始终有 4 个活单位** ⇒ 排除"敌方被全歼"作为判胜源（对照假说 2）。
- 编译产物里**只有一条 win trigger**：`[Events] 0B00001C=1,13,0,N`（ElapsedTime(N)）→ `[Actions] 0B00001C=1,1,0,8,0,0,0,0,A`（WinnerIs(Russians=8)）；另有 `0B000000=1,11,0,8`→`Loser(8)` 我方全灭判负，和 `0B000038=1,13,0,1`→文字提示。`[本次读码]`
- 3 张 `.MAP` 除 survive 相关行外 **317/317 行逐字节相同**（`out\BUILD_RESULT.json` `layout_identity.s20/s55.identical_except_survive_lines=true`）。`[本次读码]`

`[本次读码]` 编译链复核（与 Lead 的 W78 §8 一致）：`W60_battlemd_inplace\ra2forge_patched_v15\ra2forge\builder.py:910-915` → `tg.ev_elapsed_time(int(o["seconds"]))` → `triggers.py:112-113` 返回 `(13,(0,seconds))`；`maplib.py:455-461` 把事件序列化为 `1,13,0,N`。**秒数原样进参数，无换算、无截断代码**。`[本次读码]` 另核 `STANDARD_HOUSES` 中 British=4、Russians=8。

### 1.2 三点表（`[本次实测]`）

`frame = *(DWORD*)0x00A8ED84`，32 ms 计数 ≈ 31.25/s（本卡 5 趟轨迹斜率复核均在 31.0–31.3/s）。
`判胜 frame` = 结算屏出现时**冻结**的 frame（每趟 `frame_stalled=true`，2 s 后读数相同）。
`wall 时间` 记两列：`t_detect` = 探针首次枚举到结算控件的 wall 秒（从局内观察 t0 起，含 UI 渲染 1–2 s）；`wall_from_entry` = 从 `level_entered` 到检出的 wall 秒。采样 1 s，故 wall 有 ±1 s 量化；**精确量是 frame**。

| 图 | 设计秒数 | 判胜 frame | frame/31.25 = 游戏秒 | 与设计秒数的比 | `t_detect` (wall) | `wall_from_entry` | 引擎结算屏「所花時間」 | 「殲敵軍數」 | 终局类别 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| `survive(8)`（trip1） | 8 | **210** | **6.72** | **0.840×** | 7.38 s | 7.45 s | `00:00:07` | 0 | `victory_score_screen` |
| `survive(20)`（trip2） | 20 | **390** | **12.48** | **0.624×** | 12.55 s | 12.67 s | `00:00:13` | 0 | `victory_score_screen` |
| `survive(55)`（trip3） | 55 | **915** | **29.28** | **0.532×** | 29.24 s | 29.36 s | `00:00:30` | 0 | `victory_score_screen` |

`[本次实测]` 三趟均为 `VICTORY_RESULT_AND_TERMINATION_OK`，`ok=true`：控件 `GUI:Continue` + `GUI:HeadsTaken` + `GUI:ParTime` + `GUI:StandaloneScore` + `GUI:YourTime`，frame 冻结、点 Continue 后 `no_extra_start=true`（未起第 2 关）、`+0x34AC(EOG)=1`。全程 `0` 次地图错误、`0` 次失败重试框。
`[本次实测]` 引擎自己的结算屏耗时 **7 / 13 / 30 秒**，与 `frame/31.25` 取整一致 ⇒ 独立佐证 frame→秒的换算成立。

### 1.3 规律与三假说判别（`[本次实测]` + `[静态推断]`）

把三点做线性拟合，**精确成立**：

```
frame = 15 × N + 90  =  15 × (N + 6)        (N = 设计秒数)
游戏秒 = frame / 31.25 = 0.48 × N + 2.88
```

| N | 观测 frame | `15N+90` | 误差 |
|---:|---:|---:|---:|
| 8 | 210 | 210 | 0 |
| 20 | 390 | 390 | 0 |
| 55 | 915 | 915 | 0 |

`[转引 + 本次实测交叉]` 外部点全部落在同一条线上：W78 trip3 `survive(55)` = 915（29.62 s）、W78 trip4 `survive(55)` = 915（29.59 s，本卡开卡时并发完成的第 4 趟，`W78_combat_load\out\trip4\TRIP_RESULT.json`）、W76 五关链每关 `survive(8)` 结算停滞 frame = 210（两趟共 10 次）。本卡额外对照趟 trip5（**有真实战斗**，`survive(55)`）也是 **915** ⇒ 该规律**与布局、兵力、是否发生战斗无关**。

| 假说 | 判定 | 依据 |
|---|---|---|
| **1 位宽/上限（20 与 55 饱和）** | **否** | 20→390、55→915 相差 525 帧，完全不饱和；`[8,55]` 区间无截断。若截断，55 应与 20 相近。 |
| **2 另有触发源（与秒数无关）** | **否** | frame 随 N 严格线性（210/390/915）。且三张图敌方 4 个活 E1 全程未被清（「殲敵軍數 0」），编译产物只有一条 `13,0,N→WinnerIs` win trigger ⇒ `survive` **就是**实际触发源。 |
| **3 计时基准偏移（frame = 31.25×(秒数−偏移)）** | **定性成立，字面公式不成立** | 数据确是**线性 + 非零截距**（截距 +90 帧 ≈ +2.88 游戏秒），但斜率是 **15 帧/设计秒**，不是 31.25。⇒ 除"起点偏移"外**还有一个 15/31.25 = 0.48 的比例因子**（疑似引擎按 15 fps 基准读 ElapsedTime 参数），`[静态推断]`，机制未证。 |

`[本次读码]` 生成侧无任何换算/截断（见 §1.1），故偏差**不在 ra2forge 编译路径**，而在引擎对 event 13 参数的解释。`[待运行验证]` 具体机制（15 fps 假设？触发启用时刻在 frame 90？）需反汇编/写观察，超出本卡"只读 RPM、不下断点"纪律，未做。

### 1.4 `survive` 判定（`[本次实测]`）

> **`survive 不可靠（写明规律）`** —— 若"可靠"指**按设计的 N 个真实/游戏秒判胜**，则不可靠：系统性提前，且偏差随 N 变化（比值 0.840 / 0.624 / 0.532，非恒定）。
> **规律**：`判胜 frame = 15×N + 90`（`游戏秒 = 0.48×N + 2.88`），确定性、单调、跨布局/跨战斗负载可复现。**作为"判胜触发器"它是可靠的**——本卡 4 个 `survive` 点 + W78 2 点 + W76 10 点，全部逐点复现，无一超时、无一失败、无一误判。
> **不是** `无法判定`：三点 + 5 个外部点足够给出规律与三假说判别；缺的只是**引擎侧机制**（见 `UNKNOWNS.md` U1），不缺可观测规律。

---

## 2 · 任务 A 对 W63/W70/W76 结论效力的影响（独立判断）

`[转引]` 先明确三卡结论的依赖：
- `LEAD_VERIFY_W63.md` §1 / §9：三关链 M1→M2→M3 贯通、M3 `EndOfGame=yes` 正确终止；证据是 `0x125C` 图名阶梯、`+0x35A0` 阶段键、`GUI:Continue` 推进、EOG 字节、无第 4 个图名。§40 明确写"胜利条件 `survive(8)` 编译为引擎原生 `ElapsedTime→WinnerIs`"。
- `LEAD_VERIFY_W70.md` §1：**T1** 同一包三趟逐项一致；**T2** 卸载后官方苏联战役功能级可用（`SOV01UMD.MAP` / `scen_next=GDI2A.map`）。
- `W76_five_mission_chain\FIVE_CHAIN_RESULT.md` §1 / §2：五关链贯通、`+0x35A0` 数值预测 5 点成立、frame 恒定停滞于 210、结算屏「所花時間 00:00:07」。

**我的独立判断：`[本次实测 + 本次读码]`**

1. **"链推进 / 终止 / 重复性"结论：不受影响，且被加强。**
   这些结论的判据是**状态机/结构**：某关是否出现胜利结算屏 → `GUI:Continue` 是否把 `0x125C` 推到下一张图 → 终关是否 `EOG=1` 且不再起新图。`survive(8)` 在这里只承担"提供一个胜利触发"的角色，**它的绝对时长不进入任何一条判据**。本卡证明该触发是**确定性的**（`survive(8)` 恒 = frame 210，与 W76 十次实测逐点一致），且是编译产物里唯一的 win trigger ⇒ W63/W70/W76 观察到的"每关都判胜"不是巧合或别的事件冒充，正是 `ElapsedTime(8)→WinnerIs`。所以结论不仅不失效，因果链反而被补全。
2. **W70 的 T2（卸载后官方战役可用）：完全不受影响。** 该结论不依赖 `survive`（走的是官方 `SOV01UMD.MAP`），依赖的是逐字节还原与 `SkipMapSelect`/阶段表；本卡收尾同样给出 `IDENTICAL_TREE=True`（见 §5）。
3. **受影响的是"8 秒"这个时序说法，且只是措辞层，不是数据层。**
   - 不能再说"`survive(8)` 让每关存活 8 秒/8 秒后判胜"。真实是 **6.72 游戏秒 / 引擎显示 00:00:07 / frame 210**。
   - 但 W76 报告本来就写的是**实测值**「`survive(8)` → 结算屏『所花時間 00:00:07』」和「frame 停滞于 210」，**并没有把 "8" 当成实测时序**——"8" 只是设计参数标签。故 W63/W70/W76 的**落盘数据无需任何改写**，只需在引用"8 秒"时改称"设计参数 `survive(8)`（实测 ≈6.72 游戏秒）"。
   - **新约束**：凡按"N 秒"做超时预算/时间盒/等待窗口的表述都要按 `0.48N+2.88` 重算。例如 W78 用 150 s 硬上限判 `survive(55)` "超时"是安全的（29.28 ≪ 150），但任何"等 8 秒就该出结算"的自动判据都偏早/偏晚，需改。
4. **与 Lead 判断的异同**：Lead 判断"不影响链推进/终止结论、影响 8 秒时序说法"——**我同意，并补两条理由**：(a) 编译产物唯一 win trigger 已由本卡 `[本次读码]` 钉死，排除了"另有触发源"这个唯一可能推翻结构结论的替代解释；(b) 新规律是**确定性函数**，反而把 W70 的"三趟一致"从经验观察升格为可预测。差别仅在：Lead 说"`survive` 不可靠"，我把它拆成**计时语义不可靠 / 触发语义可靠**两档，避免下游误以为"胜利触发不可信"。

---

## 3 · 任务 B：歼灭胜利能否达成

### 3.1 设计（`[本次读码]`）

| 项 | 值 |
|---|---|
| 地图 | 60×60 TEMPERATE，与 Task A 同框架，`EndOfGame=yes` |
| 我方 | **40 辆 Russians MTNK，全部 `mission: Hunt`**（rows 42–45，cols 16..43 每 3 列一辆） |
| 敌方 | **只有 4 个 British E1，`Guard`（不给 Hunt）**，row 36 cols 24/27/30/33，紧邻坦克阵上沿、易达 |
| 胜利条件 | `destroy_all_forces(enemy=British)`；**无 `survive`** |
| 其它 | `text(at_second=1)` 仅作标识 |

`[本次读码]` 编译产物 `pkg_ann\W79Probe\RA2F_M1.MAP`：
```
[Events]  0B000000=1,11,0,8   → AllDestroyed(Russians) → Loser(8)   (判负)
          0B00001C=1,11,0,4   → AllDestroyed(British)              (判胜条件)
          0B000038=1,13,0,1   → 文字提示（**不是** win trigger）
[Actions] 0B000000=1,2,0,8,0,0,0,0,A    → Loser(8)
          0B00001C=1,1,0,8,0,0,0,0,A    → WinnerIs(8)
```
⇒ **全图只有一条 win trigger**，即 `AllDestroyed(British=4)→WinnerIs(Russians=8)`；**没有任何 ElapsedTime 判胜触发器**。40 行 `Russians,MTNK` 全带 `,Hunt,`，4 行 `British,E1` 全带 `,Guard,`。`[本次读码]`

### 3.2 判定与证据（`[本次实测]`）

> **能判胜 ⇒ `destroy_all_forces` 可用（重大能力确认）** ✅

| 趟 | 变体 | outcome | 判胜 frame | 游戏秒 | `t_detect` / `wall_from_entry` | 结算屏「殲敵軍數」 | 结算屏「所花時間」 | 终局 |
|---|---|---|---:|---:|---|---:|---|---|
| trip4 | `ann`（`destroy_all_forces`，无 survive） | `VICTORY_RESULT_AND_TERMINATION_OK` | **274** | 8.77 | 8.56 s / 8.66 s | **4** | `00:00:09` | `victory_score_screen` |

证据链（`out\trip4\` + `out\screen_trip4_*`）：
- `[本次实测]` 控件 `GUI:Continue` + `GUI:HeadsTaken` + `GUI:ParTime` + `GUI:StandaloneScore` + `GUI:YourTime`；`frame_stall={274,274,true}`；`no_extra_start=true`、`EOG=1`；`ok=true`。
- `[本次实测]` **敌方真的被清掉了**：结算屏引擎自报 **「殲敵軍數 4」**（`screen_trip4_settlement_confirm.png`），等于敌方全部 4 个 E1 ⇒ `AllDestroyed(British)` 条件本该满足。`screen_trip4_combat_t05.png` 目视有「任務完成」横幅。
- `[本次实测]` 判胜 frame **274 不属于 `15N+90` 的任何 N**（该图无 survive），且地图无 ElapsedTime win trigger ⇒ 不是时间触发。
- `[本次实测]` 对照趟 **trip5**（见 §3.3）排除了"引擎自动判胜"这一替代解释。

**因此 W78 缺陷 B 的自洽解释被证实**：W78 trip1（远距）150 s 无结算、trip2（近距）t=71 s 弹「確定要重新執行此場任務嗎？」是/否 ⇒ 我方战败，敌方未被全歼（W78 结算屏「殲敵 3」，敌方 12 个只死 3 个）。**不是事件没接线**，是条件本该不满足。本卡把敌方缩到 4 个静止步兵、我方 40 辆主动 Hunt，条件满足后 `AllDestroyed→WinnerIs` 立刻判胜。

### 3.3 额外对照趟（第 5 包 / 第 5 趟，非任务书要求，用于钉死归因）

为区分"**我们的 `AllDestroyed` 触发器生效**"与"**引擎在敌方全灭时自动判胜**"，另造一个对照包 `ctrl`：**与 annih 完全相同的布局（40 Hunt MTNK + 4 静止 E1，47/47 条单位/建筑放置行逐字节相同）**，唯一差异是胜利条件改为 `survive(55)`、**移除 `destroy_all_forces`**（地图 `[Events]` 不再有 `,11,0,4`，只有 `,13,0,55` 的 win trigger）。

| 趟 | 变体 | 判胜 frame | 结算屏「殲敵軍數」 | 结算屏「所花時間」 | 说明 |
|---|---|---:|---:|---|---|
| trip5 | `ctrl`（同布局，`survive(55)`，无歼灭条件） | **915** | **4** | `00:00:30` | 敌方同样 4/4 被清，但**没有**在 frame ~274 判胜 |

`[本次实测]` 结论：**同样清掉 4 个敌人，撤掉 `destroy_all_forces` 后判胜从 274 推迟到 915（`15×55+90`，即 `survive(55)` 的确定性时刻）** ⇒
- 引擎**不会**在"敌方全灭"时自动判胜；
- trip4 的 frame-274 胜利**确由 `AllDestroyed(British)→WinnerIs` 触发**；
- 附带收获：规律 `frame=15N+90` 在**有真实战斗**的负载下同样成立（915），与 W78 trip3/trip4 一致 ⇒ 战斗不是 W78 时序偏差的成因。

`[本次实测]` 对照趟同时说明：本卡的 `Hunt` 兵力设计**不需要跑手会玩**——两趟都是自动清场后自动判胜/自动计时判胜，全程无人工微操。

### 3.4 探针三态区分（红线 #5，`[本次实测]`）

`work\tools\w79_run.py` 明确分三类终局，**不把"任务失败"记成 error**：
- `victory_score_screen`：`GUI:Continue` **且** `GUI:HeadsTaken|GUI:StandaloneScore|GUI:ParTime|GUI:YourTime`；
- `defeat_restart_dialog`：`{GUI:OK, GUI:Cancel}` 同时可见（W78 trip2 ndjson 实测控件 `["GUI:Blank","GUI:Cancel","GUI:OK","Yuri's Revenge"]`，即「確定要重新執行此場任務嗎？」是/否），**记为 `TASK_FAILED_DEFEAT_RESTART_DIALOG`，不记为 error，且不点 OK（避免重开任务）**；
- `NO_RESULT_WITHIN_150s`：硬上限 150 s（60 s 最小观察 + 90 s 宽限）。
真正的地图加载错误另立窄类（`UnableMapSelect` / `Invalid stage` / `無法啟始`），与失败框严格分开。
本卡 5 趟全部命中第 1 类，**未触发**第 2/3 类；`[转引]` W78 trip2 的「是/否」框按本口径应重定性为"任务失败（我方被全歼）"，不是 `BLOCKED: error dialog`。

---

## 4 · 与 W78 / Lead 签发件的逐条对照

| W78 / Lead 表述 | 本卡结果 | 处置 |
|---|---|---|
| `survive(55)` 在 29.62 s 判胜 < 55 s ⇒ "缺陷 A" | `[本次实测]` 复现并**精确定性**：915 帧 = 29.28 游戏秒，规律 `15N+90` | **确认，且升级为可用规律**；不是随机 bug、不是编译错 |
| `survive(8)` 210 帧 0.84× vs `survive(55)` 915 帧 0.53× ⇒ "不是单纯单位错" | `[本次实测]` 比值不恒定**成立**，但原因是**线性函数含截距**（`(15N+90)/(31.25N)` 随 N 递减），不是"另有因素" | **补上机制层解释**：仍是单一触发源、单一线性律 |
| 假说 1 位宽/上限 | 否 | — |
| 假说 2 另有触发源 | 否（编译产物唯一 win trigger + 敌方未被清） | — |
| 假说 3 计时基准偏移 | 定性成立，字面公式 `31.25×(N−偏移)` 不成立（斜率 15） | 见 `DISAGREE.md` D1 |
| `destroy_all_forces` 未证（我方战败、敌方未被全歼） | **证成**：`destroy_all_forces` 可用 | **上修能力结论**，见 `DISAGREE.md` D2 |
| 结算屏「所花時間 0」、ParTime 异常 ⇒ "计时器没被正确启动/读取" | `[本次实测]` 本卡 `survive(55)` 结算屏明确 **「所花時間 00:00:30」**、`survive(8)` **00:00:07**、`survive(20)` **00:00:13**，计时器正常 | 见 `DISAGREE.md` D3：不推翻 W78 那张截图，但"计时器没启动"外推不成立 |
| trip2 记为 `BLOCKED: error dialog during combat` | `[转引]` 应为任务失败重试框 | **同意 Lead §5 的纠正**，本卡探针已按三态实现 |
| "战役包支持战斗驱动胜利" / "歼灭胜利可用" 不得写 | `[本次实测]` 现在**可以写**（有 control 归因） | 见 `DISAGREE.md` D2；建议 Lead 更新 §6 签发表 |

---

## 5 · 真机纪律自证（红线 1–7，`[本次实测]`）

| 红线 | 自证 |
|---|---|
| **#1 一趟一锁** | 5 趟各自 `w79`→`lead`，`out\run_trip{1..5}.ndjson` 的 `lock_claimed` / `lock_released` 成对；离线/收尾阶段锁恒 `owner=lead`；最终 `.game_instance.lock` `owner=lead`。从未跨趟持锁。 |
| **#2 不写 `ra2youli`，只跑沙箱** | 沙箱是本卡 `sandbox_game\`（robocopy 只读源 = 真目录）；`out\real_pre.json` vs `out\real_post.json` 全树 diff ⇒ **`IDENTICAL_TREE=True`**：PRE/POST 均 **647 文件 / 1,989,215,270 B / 277 map-like**，`added=[] removed=[] changed=[] mtime_diff=0`。`gamemd.exe` PRE==POST==`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（`73201cc0…`，未打补丁）。详见 `REAL_DIR_PROOF.txt`。 |
| **#3 只关自己启动的 pid** | trip1 `3824` / trip2 `19136` / trip3 `13396` / trip4 `11188` / trip5 `24076`；每趟 `WM_CLOSE → taskkill /PID <own> → /F`，`residual_own_pid=0`，全局 `gamemd_residual=[]`。**无 blanket taskkill**。 |
| **#4 启动前字节副本+哈希；收尾逐字节还原并实算自证** | 首次启动前 `out\pristine\` 保存 **21 项**可写配置的逐字节副本 + SHA（`out\offline_s8.ndjson` `pristine_saved`）；每趟启动前另记 `config_pre_snapshot`（逐文件 SHA，见各 `TRIP_*.json`）；收尾 `FINALIZE.json` `config_restore`：**21 项 = 20 `byte_identical=True` + 1 项 `ra2forge_install.json.seal` 为 `absent_baseline`（基线本就不存在，按基线删除）**，`all_ok=True`；`BATTLEMD.INI` 还原 2733 B / `7e40691a…` == 清单 `original_sha256` == 官方 2733 B == pristine == 真目录 PRE/POST，`Scenario=SOV01umd.MAP` 回来、`RA2F_M1.MAP` 消失。沙箱 `identical_tree=True`（清理掉游戏自生成的 `RA2F_M1.sav` 后），`verify --game sandbox --json` exit 0，沙箱目录已删除。 |
| **#5 探针三态** | 见 §3.4。5 趟全部 `victory_score_screen`；无失败框被误记为 error（本卡无失败框出现）；无超时（硬上限 150 s 未触发）。 |
| **#6 只写本卡目录；git 只读；不改 W21–W78** | 全部产物在 `W79_survive_and_annih\`；`git` 仅 `status --porcelain` 只读一次；未写 `W21`–`W78`、未写 `REVIEW\`。`w79_lib.py`/`w79_common.py` 是 W78 工具的**卡内副本**，改了输出路径与 owner，未 import 他卡脚本（HANDOFF 纪律）。 |
| **#7 分级** | 全文按 `[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]` 标注。 |

`[本次实测]` 心跳每 10 分钟更新：`HEARTBEAT.txt` 共 6 次（08:21 / 08:32 / 08:40 / 08:47 / 08:53 / 08:58）。

---

## 6 · 产物清单

| 文件 | 内容 |
|---|---|
| `SURVIVE_AND_ANNHIL_RESULT.md` | 本报告 |
| `REAL_DIR_PROOF.txt` | 真目录零改动 + 沙箱逐字节还原自证 |
| `UNKNOWNS.md` | 未覆盖 / 待运行验证 / 未定谳 |
| `DISAGREE.md` | 与 Lead/W78 表述的分歧与订正建议 |
| `STARTED.txt` / `HEARTBEAT.txt` | 步骤 1 与心跳 |
| `out\TRIP_trip{1..5}.json`、`out\trip{1..5}\TRIP_RESULT.json` | 每趟完整判定 + W59 字段轨迹 + frame 轨迹 |
| `out\run_trip{1..5}.ndjson` | 每趟逐步 NDJSON（含锁、pid、config_pre、采样、截图、清理） |
| `out\screen_trip*_settlement*.png` | 5 张结算屏（含引擎自报「殲敵軍數」/「所花時間」） |
| `out\screen_trip*_combat_t*.png` / `enter` / `terminal` | 过程/进图/终局截图 |
| `out\BUILD_RESULT.json` / `BUILD_CTRL_RESULT.json` / `OFFLINE_*.json` / `FINALIZE.json` | 离线造包、安装、收尾自证 |
| `out\real_pre.json` / `real_post.json` / `sandbox_pre.json` / `sandbox_post.json` / `pristine\` | 全树 manifest + 字节副本 |
| `work\w79_design_{s8,s20,s55,ann,ctrl}.json`、`work\pkg_*\W79Probe\` | 4 个必需包 + 1 个对照包 |
| `work\tools\w79_*.py` | 本卡自有工具（lib/common/build/offline/run/finalize/build_ctrl） |

---

## 7 · 给 Lead 的一句话建议

`[本次实测]` 建议把 W78 §6 签发表更新为：`survive(seconds)` **按"存活 N 秒"工作 = 不成立（已定性为 `frame=15N+90` 的确定性偏差）**；`destroy_all_forces` 能判胜 = **成立（本卡 trip4 + 对照 trip5 归因）**；并保留"链推进/终止/重复性"结论强度不变，仅把"8 秒"字面改成"设计参数 `survive(8)`，实测 ≈6.72 游戏秒 / frame 210"。**签发权在 Lead，本卡不签发。**

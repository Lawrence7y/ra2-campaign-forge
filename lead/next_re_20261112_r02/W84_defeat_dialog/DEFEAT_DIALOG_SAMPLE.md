# W84 · 失败重试框（`defeat_restart_dialog`）真机样本 —— 三态探针缺的那一态已补上

> 执行者 **GLM-5.3-Flash**（卡 W84）｜卡目录 `lead\next_re_20261112_r02\W84_defeat_dialog\`
> `STARTED.txt` 写于任何读码之前：`2026-11-14T11:03:38+08:00`
> 时间线：离线造包 `11:12:33`（0 锁）→ 沙箱安装 `11:12:52`（0 锁）→ rules probe `11:13` →
> 真机 5 次启动 `11:13:17–11:25:14`（trip_df1 / trip_wv1 / trip_df2 / trip_wv2 / trip_wv3）
> → 收尾还原 `11:25:27` → 报告 `11:26`。时间盒 100 min，实际约 25 min。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本报告**不签发**（签发权在 Lead）。
> 工具：复制 W83c 工具链到本卡改路径（`work\tools\w84_lib/offline/finalize.py` 为 W83c 卡内副本 re-point；
> `w84_common/build/run.py`、`EVIDENCE\rules_probe.py` 手写），未 import 任何他卡脚本。

---

## 0 · 一句话结论

- **① 拿到了失败重试框真机样本，且两次独立复现** `[本次实测]`：trip_df1 与 trip_df2 的三态分类都是
  **`defeat_restart_dialog`**（outcome `TASK_FAILED_DEFEAT_RESTART_DIALOG`，ok=True），
  检测时刻 **frame=274**（两趟逐帧相同，确定性场景）、wall t≈8.4 s、`0x34AC=1`、`0x125C=RA2F_M1.MAP`、
  frame 停滞确认 274==274（2 s 后复读）、终局 14 个采样 fn 全部仍为 `RA2F_M1.MAP`
  （`no_extra_start=True`，**没有点 OK/是，没有重开一局**）。
- **② 弹窗的控件/文本原始清单（本卡核心产物）** `[本次实测]`：见 §2。
- **③ 判据可区分失败框与胜利屏** `[本次实测]`：三趟正对照（wv1/wv2/wv3）全部判为
  `victory_score_screen`、从不误判失败框；判据集合 `{GUI:OK, GUI:Cancel}` 与
  `{GUI:Continue, GUI:HeadsTaken, GUI:ParTime, GUI:StandaloneScore, GUI:YourTime}` 在全部 5 趟中互斥出现。
- **④ 真目录零改动自证**：`IDENTICAL_TREE=True`（647 文件 / 1,989,215,270 B / 277 map-like、
  mtime_diff=0，`gamemd.exe` 仍 `73201cc0…`），见 `REAL_DIR_PROOF.txt`。
- **⑤ 锁**：5 趟每趟 `w84`→`lead`、`finally` 必还；最终 `.game_instance.lock` `owner=lead`；
  全程 gamemd 残留 0。
- **W79 UNKNOWNS U4 升格**：`defeat_restart_dialog` 分支从 `[待运行验证]` 变为 `[本次实测]`。

---

## 1 · 地图设计（必然战败，无需跑手操作）

### 1.1 两张图（均 60×60 TEMPERATE、`EndOfGame=yes`、`NextScenario=""`、任务名 `RA2F_M1.MAP`）

| 包 | 臂 | 我方 Russians | 敌方 British | objectives | 编译产物关键断言 `[本次读码]` BUILD_RESULT.json |
|---|---|---|---|---|---|
| `df` | **失败臂** | **1× `TESLA`**（苏军磁暴线圈，row 50 col 30，全图唯一我方物体），无基地/电厂/单位/步兵 | **30× `MTNK` 全 `mission:Hunt`**（row 38/40/42 × col 20..38 step 2） | `text@1` 一条，**无任何胜利条件、无 survive** | `russian_tesla=1`、`british_mtnk=30`、`hunt=30`、**无 win trigger**（无 `,1,0,8`、无 `,13,0,*`、无 `,10,0,4`、无 `,11,0,4`）、自动判负 **event `,11,0,8` + action `,2,0,8`** 存在 |
| `wv` | **正对照臂** | NACNST + NAPOWR×2 + 30× MTNK（Guard） | 1× GAPOWR（row 10 col 30，无武装） | `text@1` + **`survive(5)`** | `,13,0,5` + `,1,0,8` 存在 |

### 1.2 设计要点与坑位应对 `[本次实测]` + `[转引]`

1. **为什么是 TESLA 而不是卡面建议的 1×GAPOWR**：W83c db v1 实证 *Hunt 目标获取忽略无武装建筑*
   （40 辆 Hunt 坦克面对 3×GAPOWR 冻结 154 游戏秒）—— 该机制与"谁是被打方"无关。若按卡面用
   1×GAPOWR，敌人不会来打 → 只能得 `NO_RESULT`。**必须给我方一个武装建筑**。选
   `TESLA`（苏军原生武装建筑，`rulesmd.ini` section 实存 —— W83c RULES_PROBE `[转引]` +
   本卡 rules probe `[本次实测]`，见 `out\RULES_PROBE.json`，`ATSLA` 再次确认不存在）。
   结果：30 辆灰熊行军接敌 → 线圈被击毁 → `AllDestroyed(Russians)` → `Loser` → 失败框。
2. **假阳性排除（空真判负签名）**：W83c v2 的"目标型号无效"签名是 **frame-90 空胜**。本卡失败臂
   两趟都死于 **frame=274**（entry frame≈71，即实战 ~6.5 游戏秒），且 t05 截图可见
   **「任務失敗」横幅已打出（frame 237）+ 线圈残骸与弹坑** ⇒ 线圈真实存在、被真实击毁，非加载器丢弃。
3. **不给 survive**（避免时间触发抢先判胜）——df 包编译产物无任何 `,13,0,N` 事件 `[本次读码]`。
4. **观测窗 ≥180 s**：`OBSERVE_SEC=60 + POST_WAIT_SEC=120`，SHOT_MARKS 延到 t180。
5. **探针绝不点击 OK/是/否**：W83c 失败分支本就不点；本卡失败分支在检测瞬间额外落全量证据后
   继续只读采样。

---

## 2 · 弹窗的控件/文本原始清单（核心产物）`[本次实测]`

### 2.1 Win32 控件枚举（`EnumWindows/EnumChildWindows`，检测时刻全量，两趟一致）

| hwnd(trip_df1) | cls | text | visible | ctrl_id | rect |
|---|---|---|---|---|---|
| 2229260 | `Yuri's Revenge` | `Yuri's Revenge` | True | 0 | [0,0,1707,960]（主窗口） |
| 19140744 | **`#32770`** | （空） | True | 0 | **[117,91,417,308]**（弹窗宿主，标准 Win32 对话框） |
| 6294512 | `Button` | **`GUI:OK`** | True | **1454** | [323,259,406,276] |
| 5114698 | `Button` | **`GUI:Cancel`** | True | **2** | [323,281,406,298]（ctrl_id 2 = IDCANCEL） |
| 12718360 | `Static` | **`GUI:Blank`** | True | 1456 | [157,135,377,190]（文本区） |

`visible_all = ["GUI:Blank","GUI:Cancel","GUI:OK","Yuri's Revenge"]` —— 与 W78 trip2 ndjson
记录（`["GUI:Blank","GUI:Cancel","GUI:OK","Yuri's Revenge"]`）**逐项一致**。
（另有不可见系统窗口 DDE Server Window / MSCTFIME UI / IME，与判定无关。）

### 2.2 弹窗显示文本（像素截图证据，仅作文档、不作数值判定）

- 全屏：`out\screen_trip_df1_defeat_full.png`（trip_df1）、`out\screen_trip_df2_defeat_full.png`
- 裁切：`out\screen_trip_df1_defeat_dialog_crop.png`（563×337，bbox [83,119,646,456]）、
  `out\screen_trip_df2_defeat_dialog_crop.png`
- 内容：**「確定重新執行此場任務嗎？」** 两按钮 **「是」「否」**（分别渲染在 GUI:OK / GUI:Cancel 上，
  本地化文字是绘制层，Win32 控件 text 仍是 `GUI:OK`/`GUI:Cancel`）。
- **注意**：实际文本**没有「要」字** —— W78/W79/卡面转写的「確定**要**重新執行此場任務嗎？」多了
  一个「要」，详见 `DISAGREE.md` D1（截图 + 内存双证据）。

### 2.3 进程内存文本命中（RPM 只读扫描 335,872,000 B，1246 regions）`[本次实测]`

| needle（utf16le） | count | 关键样本 |
|---|---|---|
| `重新執行此場任務` | **2** | `0x39d1b04`：`..1.投降..1.確定重新執行此場任務嗎？...1.部隊`；`0xf355244` 同句 |
| `重新執行` | 4 | `0x39c7450`：`遭遇戰.!.`**`重新執行場景`**`...`；`0x39ca250`：`重新執行這場戰役任務` |
| `確定要重新` | 1 | `0x39d3742`：`您確定要重新設定快捷鍵配置嗎？`（**另一条字符串**，热键确认框 —— 证明 needle 有区分度） |
| `確定要重新執行此場任務嗎`（含「要」） | **0** | W78/W79 转写含「要」的版本在内存中不存在 |
| `Restart`(ascii) | 57 | `0x8240e8`：`GOptions.CPP...GUI:Observe.GUI:Restart.GUI:Leave`；`0x834e85`：`STT:ConfirmExitButtonRestart` |
| `RESTART`(ascii) | 9 | `TXT_GAME_RESTART`（CSF label 名） |

### 2.4 检测时刻 RPM W59 读数（判据一律用读数，不目测截图）`[本次实测]`

| 项 | trip_df1 | trip_df2 |
|---|---|---|
| `0x125C` scen_filename | `RA2F_M1.MAP` | `RA2F_M1.MAP` |
| `0x34AC` EndOfGame | 1 | 1 |
| `0x35A0` stage_idx | 0 | 0 |
| frame `0x00A8ED84` | **274**（=8.77 游戏秒 @31.25fps） | **274** |
| 检测 wall t（进入战斗后） | 8.38 s（from_entry 8.48） | 8.36 s |
| frame 停滞确认 | 274 == 274（2 s 后） | 274 == 274 |
| 终局 14 采样 fn/frame | 全 `RA2F_M1.MAP` / 全 274，`no_extra_start=True` | 同左 |
| pid | 17532 | 41440 |

序列（trip_df1 combat samples）：frame 75→110→142→174→206→237→**273→274 冻结**，
visible 从仅 `Yuri's Revenge` 变为 `+GUI:Blank/GUI:Cancel/GUI:OK`；t05（frame 237 附近）截图已有
「任務失敗」横幅与线圈残骸 ⇒ 引擎序列：**任務失敗横幅 → 弹失败框**。

---

## 3 · 检测判据（探针实现与实测依据）

`w84_run.py::terminal_kind`（W83c 三态实现原样复用，严格三分）：

1. **`VICTORY_SCORE_SCREEN`** ⇔ visible 同时含 `GUI:Continue`（或 繼續戰役/continue）
   **且** 含 `GUI:HeadsTaken` / `GUI:StandaloneScore` / `GUI:ParTime` / `GUI:YourTime` / `GUI:score` 之一。
2. **`DEFEAT_RESTART_DIALOG`** ⇔ visible 同时含 **`GUI:OK` 与 `GUI:Cancel`**（且 1 不成立）。
   地图加载错误（`無法啟始/UnableMapSelect/Invalid stage`）先行排除，失败框**不在**错误 token 列表。
3. **`NO_RESULT_WITHIN_180s`** ⇔ 硬帽内 1/2 均未出现。

**本卡实测如何认定 df 弹窗是失败框而不是胜利屏**（判据+实际抓到的证据）：

- visible 全集 = `{GUI:Blank, GUI:Cancel, GUI:OK, Yuri's Revenge}`：**含 OK+Cancel** ⇒ 命中判据 2；
  **不含** `GUI:Continue`、**不含任何** `HeadsTaken/ParTime/StandaloneScore/YourTime/score`
  ⇒ 判据 1 的必要条件一个都不满足。
- 弹窗宿主是 `#32770` 标准对话框（rect 300×217 px），位于主窗口客户区左上象限 —— 与 W83c 五趟
  胜利屏（全屏结算、Continue+HeadsTaken 控件组）形态完全不同。
- 旁证（非判据、均为只读取证）：截图显示「確定重新執行此場任務嗎？」+是/否（且此前 37 帧刚打过
  「任務失敗」横幅）；进程内存命中该句 utf16le ×2；frame 冻结在 274。
- **正对照反证**：三趟胜利屏 visible 全集 =
  `{GUI:Blank, GUI:Continue, GUI:HeadsTaken, GUI:ParTime, GUI:StandaloneScore, GUI:YourTime, Yuri's Revenge}`
  —— 判据 1 命中、判据 2 的 OK/Cancel **不在场**。5 趟无一次两集合交叉。

---

## 4 · 正对照（判据可判别性）——已做 `[本次实测]`

`wv` 包（兵力对调 + `survive(5)`），同一探针代码，3 趟：

| 趟 | frame_at | visible 判定 | outcome | ok | 备注 |
|---|---|---|---|---|---|
| trip_wv1 (pid 11000) | **165** | `victory_score_screen`（Continue+HeadsTaken+ParTime+StandaloneScore+YourTime） | `VICTORY_RESULT_AND_TERMINATION_OK` | False* | 结算屏未点击 ~48 s 后游戏自行退出（t≈54.7 < 60 s 最小窗），点击落在进程死后 → clicked=false |
| trip_wv2 (pid 36108) | **165** | `victory_score_screen`（同上） | 同上 | False* | **Continue 点击成功 clicked=true**；终局 fn 全程 `RA2F_M1.MAP`、`no_extra_start=True`（frame 165,165,165,165,0 = 点继续后进程退出） |
| trip_wv3 (pid 33572) | **165** | `victory_score_screen`（同上） | 同上 | False* | 结算屏自退更快（t≈12.6 < 20 s 收窗），竞态再负 |

\* 三趟 ok=False 的原因全部是**收尾竞态/记账**，与判类无关：① 未点击的结算屏存在**随机自退**
（实测 ~12 s 与 ~55 s 两例）；② wv2 之后发现 `observe()` 返回的 `min_window_met` 仍按 60 s
记账（bug 已修，未再重跑）。**判类本身 3/3 正确**，其中 trip_wv2 是完整干净样本
（分类正确 + 点击成功 + 无额外开局）。frame 165 = 15×5+90，W79 survive 公式精确复现 `[转引]`。

**结论：判据能把胜利屏与失败框分开 —— 失败臂 2/2 判 `defeat_restart_dialog`，胜利臂 3/3 判
`victory_score_screen`，两控件集合 5 趟零交叉。**

---

## 5 · 三态统计（本卡 5 趟）

| 终局类别 | 趟次 | 明细 |
|---|---|---|
| `defeat_restart_dialog` | **2** | trip_df1、trip_df2（frame=274 双复现，OK/Cancel 控件+截图+内存文本三重取证，未点击） |
| `victory_score_screen` | 3 | trip_wv1/wv2/wv3（frame=165，Continue+HeadsTaken 组合，未误判失败框） |
| `NO_RESULT_WITHIN_180s` | 0 | — |
| `BLOCKED` / 地图加载错误 | 0 | `UnableMapSelect/Invalid stage/無法啟始` 0 次 |

合并 W79+W83c 13 趟与本卡 5 趟 ⇒ 三态分布 `victory ×13 / defeat ×2 / NO_RESULT ×2`，
**三态全部有真机样本且分类器逐态验证**。

---

## 6 · 真机纪律自证（红线 1–7）

| 红线 | 自证 |
|---|---|
| #1 一趟一锁 | 5 次启动各自 `w84`→`lead`（`run_trip_*.ndjson` `lock_claimed`/`lock_released` 成对），`finally` 必还；最终锁 `owner=lead` |
| #2 不写 `ra2youli` | 只跑 `sandbox_game\`（11:12:54 robocopy 自真目录，647 文件逐字节）；`real_pre.json` vs `real_post.json` ⇒ **IDENTICAL_TREE=True**（647/1,989,215,270/277，added=removed=changed=mtime_diff=0）；`gamemd.exe` PRE==POST==`73201cc021497c95…` |
| #3 只关自己 pid | pid 17532/11000/41440/36108/33572，`WM_CLOSE→taskkill /PID→/F` 仅限自有 pid；每趟收尾 residual=0；无 blanket taskkill |
| #4 配置字节副本+还原 | 首启前 `out\pristine\` 21 项逐字节副本+SHA；每趟启动前 `config_pre_snapshot`；收尾 `FINALIZE.json` 全部 `byte_identical`，`BATTLEMD.INI` 还原 2733 B `7e40691a…` == 官方基线 == pristine == 真目录 PRE/POST，`Scenario=SOV01umd.MAP` 回归；游戏自产的 `RA2F_M1.sav` 已清理后 sandbox `identical_tree=True`，随后删沙箱 |
| #5 探针三态 | 见 §5；失败框未点 OK/Cancel；无 error 污染 |
| #6 只写本卡目录 | 产物全在 `W84_defeat_dialog\`；工具为 W83c 模板卡内副本/手写；git 只读未动；未写 W21–W83、REVIEW、docs/DESIGN.md |
| #7 分级 + 不目测数字 | 全文五级标注；**全部数值判据来自 RPM/控件枚举**；截图仅存证（§2.2 明确标注） |

---

## 7 · 产物清单

| 文件 | 内容 |
|---|---|
| `DEFEAT_DIALOG_SAMPLE.md` | 本报告 |
| `REAL_DIR_PROOF.txt` | 真目录零改动 + 沙箱逐字节还原自证（数字均出自 FINALIZE.json） |
| `UNKNOWNS.md` / `DISAGREE.md` | 未覆盖项 / 与卡面及 W78-W79 转写的分歧 |
| `out\TRIP_trip_df1/df2/wv1/wv2/wv3.json`、`out\trip_*\TRIP_RESULT.json` | 每趟完整判定 + W59 轨迹 + 失败框证据包（controls_full / ok/cancel/blank rect+ctrl_id / 内存命中 / 截图路径） |
| `out\run_trip_*.ndjson` | 每趟逐步 NDJSON（锁、pid、config_pre、逐秒采样、memory_search 全量、清理） |
| `out\screen_trip_df*_defeat_full.png`、`screen_trip_df*_defeat_dialog_crop.png` | 失败框全屏+裁切（「確定重新執行此場任務嗎？」+是/否） |
| `out\screen_trip_df1_combat_t05.png` | 「任務失敗」横幅 + 线圈残骸（假阳性排除证据） |
| `out\screen_trip_wv*_settlement*.png` / `screen_trip_wv*_terminal.png` | 胜利结算屏（对照） |
| `out\BUILD_RESULT.json` / `OFFLINE_df|wv.json` / `FINALIZE.json` / `RULES_PROBE.json` | 造包断言、安装自证、收尾自证、rules 型号探针 |
| `work\w84_design_df|wv.json`、`work\pkg_df|wv\W84Probe\` | 两包（RA2F_M1.MAP + BATTLEMD.INI + MAPSELMD.INI + expandmd98.mix） |
| `work\tools\w84_*.py`、`EVIDENCE\rules_probe.py`、`EVIDENCE\phases_stdout.md` | 本卡自有工具与阶段 stdout/退出码记录 |

---

## 8 · 给 Lead 的一句话建议

`[本次实测]` W79 `UNKNOWNS U4` 可升格为已验证：失败重试框控件签名 **`{GUI:OK(ctrl_id=1454),
GUI:Cancel(ctrl_id=2), GUI:Blank(1456/Static)} @ #32770`**、显示文本 **「確定重新執行此場任務嗎？」**
（**无「要」字**，内存 0x39d1b04 + 截图双证），三态判据（OK+Cancel ⇔ 失败框；
Continue+HeadsTaken 组 ⇔ 胜利屏）经 2 败 + 3 胜共 5 趟互斥验证。另附一条工程约束：
**造"必败"臂必须给我方武装建筑（TESLA）——无武装建筑连"作为被打方"都不会被 Hunt 单位锁定**
（卡面该处提示有误，见 `DISAGREE.md` D2）。

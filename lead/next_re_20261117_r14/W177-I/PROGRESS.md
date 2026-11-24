# W177-I · PROGRESS（真机执行员）

> 目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`（只读未改）。真机 pid：3928（首会话，T1/T2）、23208（连续会话，T3/T4）、32812/17548（导航失败会话）。
> 全程只读 RPM + 合成键鼠；未写内存/未注入/未改 `ra2youli\`/未联网。基线 `work/baseline_before.json`。

## 三级结论（分级只用 [已证]/[静态推断]/[未证]）

### C1 — T1 侧栏 NAPOWR 程序化像素定位：**成立** [已证]
- 全屏抓图 2560×1440，非黑占比自检 0.4908（可靠）。
- 像素剖面（列/行亮度 + 彩度）自动定位：tile bbox **x2272..2400 / y426..518**，中心 **(2336, 472)**，离边 46px。
- 判据：彩色度最大槽 colorfulness=26.28（空槽近黑灰）；标签 磁能反應爐=NAPOWR。
- 稳定性：frame 1827/8721 两图逐字段全等；切防御页/切回网格几何不变（行 sep ±1px）。
- 证据：`SIDEBAR.md`、`EVIDENCE/sidebar_grid.json`、`EVIDENCE/t1_detected_annotated.png`。

### C2 — T2 三层判据下单：**三层全成立** [已证]
- **L1 credits 降低**：10000→首降 t=0.226s 9989→末 9824（progressive 扣款，完成 9400）。
- **L2 limbo 对象**：owner=player、type=NAPOWR 的 BuildingClass 于 t=0.008s 出现，o1_81=1、o2_74=0、cell(0,0)无效、无链。
- **L3 tile 像素变化**：changed_frac=0.6384（7518/11776 px, max_diff=255），进度条扫过+黄边高亮；鼠标光标正落中心 (2336,472)。
- 点击走 `click_client`（前台 `GetForegroundWindow()==hwnd` + `WindowFromPoint` owner==pid 均校验通过）。
- 证据：`EVIDENCE/t2_order.json`、`EVIDENCE/t2_tile_{before,after}.png`。
- **相对上轮卡的突破**：上轮 credits 恒 10000/无 limbo（下单未生效）；本卡像素定位中心+前台校验解决，这是硬门槛后的关键兑现。

### C3 — T3 落格：**两次尝试均未成立（0/N），但机制非字节拒绝** [已证=未兑现]
- 下单/构建/ghost 拾取/闭环定位全部实证成功；闭环收敛到 anchor（修正前 (112,61)、修正后 (113,62)），cam 恒 (0,0)。
- 两次落格原子读：frames_elapsed=3 与 **2**（后一次满足 ≤2 帧）；目标格 (113,63) 链恒 3×InfantryClass，**无 BuildingClass**，main_ok=False。
- **根因（像素实证）**：落格预览为 3×2 六格，其中步兵所在格标 **RED（invalid）** ⇒ UI 放置校验拒绝，ghost 仍在 limbo（o1_81=1、cell(0,0)）。见 `EVIDENCE/t3b_preview_crop.png`。
- **对照实验（关键）**：同一 ghost 放到全绿空格 hover(106,60) **放置成功**（NAPOWR o1=0、cell(105,60) valid、lenA=1）；证明放置机制端到端可用，失败是步兵格专属的 UI 校验，非字节层拒绝。证据 `EVIDENCE/control_green.json`。
- **实测地基偏移（更正上轮假设）**：NAPOWR 3×2 足迹 = 格 (hover−1..hover+1, hover..hover+1)，Location=hover−(1,0)。上轮 (0..2,+1..+2) 对本建筑不适用；证据 `control_green.json` + 足迹扫描（(105..107,60..61) 六格）。
- 严格区分：**落格瞬间同格=否**（两次原子读均无 BuildingClass）；**长期稳定同格=否**（2.3s 末仍无 BuildingClass）；无"推挤"现象（步兵未离、建筑未现）。

### C4 — T4 采样：**成立** [已证]
- 两次采样：`t4_full_samples.jsonl` 62,943 样本/2.3s/27,366/s/distinct 64/frame 658..730；`t4_attempt2_samples.jsonl` **64,214 样本/2.3s/27,919/s/distinct 64/frame 13114..13186**。
- 均覆盖点击帧（click_frame 667 / 13123 在 distinct frames 内）。≥5,000/s、多帧、全量落盘 JSONL（不截断）全部满足。
- 采样列：frame/目标格链头/链长/各节点 RTTI/0x88095C/cam/credits。
- 表述：未观测到落格瞬间 BuildingClass（带速率 27.9k/s、64 帧），不写"恒0/零跳变"。

## 给审计员的 3 个核心数字 + 复算
1. **tile 中心 (2336,472)** — `python work/sidebar_locate.py EVIDENCE/t1_fresh.png` → `sidebar_grid.json` chosen.center。
2. **L1/L2/L3 全真**：`python -c "import json;d=json.load(open('EVIDENCE/t2_order.json'));print(d['L1'],d['L2'],d['L3'])"`。
3. **T3 0/N + 对照成功 + 实测偏移**：`EVIDENCE/t3b_full.json`（landing.main_ok=False, frames_elapsed=2）+ `EVIDENCE/control_green.json`（placed, measured_offset=[-1,0]）+ 足迹 (105..107,60..61)。

## 表述纪律（②-b 三分句）
- **静态允许（已证字节）**：0x47C620 比较集 {6 Building,2 Aircraft,0x24 Terrain} 不含 15(Infantry)/1(Unit)（前卡字节证，本卡沿用）。
- **运行时未兑现（0/N）**：步兵格落格两次均无 BuildingClass（原子读 2 帧内）；UI 预览红格拒绝；对照空格放置成功。
- **路径未被证伪**：失败在 UI 放置校验层（红格），非字节层 can-place；未写内存/未注入，不能据此判"不可构造"。

## 真机收尾
全程只读内存/合成输入，未写内存/未注入/未改 ra2youli\/未联网。四基线（gamemd.exe 73201CC0…、ddraw.dll 85E0F7D5…、ddraw.ini C983ABAD…、except.txt 6907F395… 26,272B / 2026-11-12T22:29:17Z）SHA+size+mtime 前后逐项全等（work/baseline_before.json 与 work/baseline_end.json）；except.txt 未变=无新崩。仅关闭本卡启动的 gamemd pid（3928 自行退出、32812/17548 导航失败会话自行退出、23208 Stop-Process；均核对 Path=ra2youli/gamemd.exe），收尾 Get-Process gamemd 计数=0、无残留。现把 LIVE_LOCK 置为 RELEASED by W177-I。

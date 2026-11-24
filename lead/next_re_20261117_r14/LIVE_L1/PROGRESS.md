# LIVE-L1 PROGRESS — ②-b 建造重叠配对实测（最终报告）

> 目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`（只读未改）。全程只读 RPM + Wow64GetThreadContext + 合成键鼠；未写内存/未注入/未改 ra2youli/未联网。pid：8064/28420/5536/30764/30420/35220（均本卡启动、均已关闭）。

## 自检结论：**FAIL（A 组自检未达标）** — 如实上报，不伪造
- 硬性判据「A 组必须多数成功」**未满足**：唯一完整三组的 l1_v2 中 A=1/5；后续修流程的 run 因随机地图上单位/视口漂移未能重跑出 A 多数成功。按任务判据缺一判 FAIL，故本卡**不能给出三方配对的最终定性**；以下为真实观测，非结论外推。
- A1（v2）真成功：空地 hover(106,56)，click 后 NAPOWR `o1:1→0`、`cell (0,0)→(106,56)`、`lenA 0→1 BuildingClass` ⇒ 放置流程本身可用；A2–A5 因 ghost 检测阈值误判（草地绿≥120 假阳性、ghost 实际未在手）未点击到有效 ghost，属仪表故障非流程故障。该 bug 已在 v3/v5 修为阈值 3000，但随机地图致可见锚点缺失，未取得干净的 A 多数成功 run。

## 三组计数（原始真机，完整 run l1_v2；核数字）
| 组 | 条件 | N | 成功 | 失败 | 注 |
|---|---|---|---|---|---|
| A | 空地 | 5 | 1 | 4 | A1 真成功；A2–5 ghost 未在手（仪表） |
| B | 目标格 3×InfantryClass | 5 | 0 | 5 | 3/5 有真实绿+红足迹(G≈11k,R≈2–6k)，放置被拒 |
| C | 目标格 UnitClass | 5 | 1 | 4 | C4 落 (112,61)，目标(113,59)未被覆盖、link_after=False，**非重叠** |

- v5 复测（B/C 交替、真足迹）：B 0/5、C 0/5，全部 `link_after=False`；合计 B 0/10、C **0/10 真重叠**。
- 10 格重叠：**从未出现**。所有 B/C 目标格 `+0xE4/+0xE8` 链前后均为原 Infantry/Unit（lenA 1/3），无 BuildingClass 同格；mode(A8B238)=5 全程（挂链子模式 1/3 为 0x43F180 参数，非此全局，见 UNKNOWNS）。

## 0x88095C packed CellStruct 序列（X lo16/Y hi16，只读）
- A1：放置前 (106,56) → 光标后 (107,56) → 放置后 (107,56)；建筑落 cell (106,56) ⇒ 实测偏移 hover−Location=(+1,0)，与 §4.2 技术⑤⑥一致。
- B3：前 (110,59) → 光标后 (109,62) → 点击后 (109,62)；目标格 (109,63) 链 3×InfantryClass 前后不变。
- C3：前 (109,62) → 光标后 (113,54) → 点击后 (113,54)；目标格 (113,55) 链 1×UnitClass 前后不变。
- C4：前 (112,54) → 光标后 (113,58) → 点击后 (113,61)；落建筑 (112,61)，目标 (113,59) 未覆盖。
- 全 trial 序列见 `EVIDENCE/trials_v2.tsv`、`EVIDENCE/trials_v5.tsv`、`EVIDENCE/l1_v5_result.json`。

## 配对像素基线（§8.1 错源⑫，同页同尺寸 220×220=48400px）
- l1_v2（绿，cell(106,56)）：无 ghost 绿=1009(0.0209) / 有 ghost 绿=15481(0.3199) ⇒ **15.34×**。
- l1_v5（红，cell(51,80) 不可建地形）：无 ghost 红=0 / 有 ghost 红=16804 ⇒ 红判据特异。
- 判据成立：footprint 颜色确由 ghost 引入，非地形/图标背景；“显绿/显红⇒放行”未被单独使用。

## 只读快照
- 旁路三值 `0xA8E7AC/0xA8E9A0/0xA8ED6B` = 0/1/0 全程零跳变；链选择位 `+0x8C=0`（head A）；建筑 `+0x81`(Limbo) 放置前1/后0；`+0x520`=BuildingTypeClass*（NAPOWR）；格 `+0xE4/+0xE8` 逐节点 RTTI 已存 EVIDENCE jsonl。

## 一句话结论
真机观测支持“目标格有步兵/己方车辆时放置被拒、无 10 格重叠”，但**因 A 组多数成功自检未达标，本卡按判据 FAIL，不给最终定性**；C 组显示拒绝非步兵专属（车辆同样拒绝）。

## 真机收尾
真机收尾：进程已关闭 / except.txt 未变（26,272 B、mtime 2026-11-12T22:29:17Z、SHA 6907F395…1094，与开工逐字节一致）/ 无残留 gamemd.exe；gamemd.exe 73201CC0…F67476、ddraw.dll 85E0F7D5…03A9 SHA 前后全等。`baseline_before.json`/`baseline_end.json`。现把 LIVE_LOCK 改写为 RELEASED by LIVE-L1。

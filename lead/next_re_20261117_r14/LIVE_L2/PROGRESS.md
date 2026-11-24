# LIVE-L2 PROGRESS — ②-b 重试：主判据改为「放置后读对象链」（非像素）

> 目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`（只读未改，ImageBase 0x400000）。授权：只读 RPM/Wow64GetThreadContext/GetProcessTimes/StackWalk/MiniDump + 合成键鼠；未写内存/未注入/未改 ra2youli/未联网。本卡进程 pid 41892（本卡启动，将关闭）。

## 主判据（唯一）
放置后读新落建筑对象 Location 格 `+0xE4/+0xE8` 链：出现新 BuildingClass 节点（地址=新对象）⇒成功占格；链未变⇒拒绝。像素/credit 仅作「ghost 在手」仪表确认，绝不入判据。落格由对象内存直接读出（不依赖 hover 偏移推断）。

## A 组开工闸（空地，阴性基线）
**PASS**：6 次放置 4 成功 / 2 失败（多数成功）。成功样本落格链 lenA 0→1、RTTI `.?AVBuildingClass@@`、节点地址=新对象。2 次失败因目标格 footprint 红绿混合（与既有建筑/单位重叠），非判据故障。hover−Location 偏移实测 **(1,0)**（与 LIVE-L1 一致），全程稳定。

## 三组计数（有效 trial = 点击瞬间目标格确有对应单位，chain_before 证实）
| 组 | 条件 | 总次数 | 有效 | 成功(同格 BuildingClass) | 失败(链未变/被拒) | 无效(单位移走) |
|---|---|---|---|---|---|---|
| A | 空地 | 6 | 6 | 4 | 2 | 0 |
| B | 目标格有己方步兵 | 6 | 5 | 0 | 5 | 1（B3 步兵已离开，按空地成功另证判据） |
| C | 目标格有己方车辆 | 5 | 5 | 0 | 5 | 0 |

- A 成功 4/6 ⇒ 主判据可用；B 有效 5/5 全拒；C 有效 5/5 全拒。B/C 交替执行。
- 结论方向：步兵与己方车辆**都**阻止在该格放置建筑；拒绝非步兵专属。与 LIVE-L1 观测一致，但本卡 A 闸达标、主判据非像素，故自检 **PASS**。
- 链长变化：A 成功 0→1；B/C 有效 trial 链长与内容前后完全不变（B:1/3→1/3 Infantry；C:1→1 Unit），无同格 BuildingClass。

## 逐次坐标与链长快照（want→落格；lenA before→after at want/landing）
- A1 (110,60)→(110,60) 0→1 BLD✓；A2 (116,65)→∅ 空地却红绿混合(8431/5610)拒；A3 (117,59)→(117,59) 0→1✓；A4 (105,62)→(105,62) 0→1✓；A5 (113,70)→∅ 拒；A6 (122,62)→(122,62) 0→1✓
- B1 (108,63)→∅ 1Inf→1Inf 拒；B2 (109,55)→∅ 3Inf→3Inf 拒；B3 (109,63)→(109,63) 0→1 BLD（步兵已移走，无效）；B4 (113,54)→∅ 1Inf 拒；B5 (113,55)→∅ 3Inf 拒；B6(补) (108,63)→∅ 1Inf 拒
- C1 (105,59)→∅ 1Unit 拒；C2 (113,59)→∅ 1Unit 拒；C3 (113,63)→∅ 1Unit 拒；C4/C5(补) (105,59)→∅ 1Unit 拒×2
- 完整逐次 TSV/JSON：`EVIDENCE/trials3.tsv`、`EVIDENCE/l2_result3.json`；ghost 握手/构建顺序见其中 `ghost` 字段。

## 关键仪表修正（相对 LIVE-L1）
- 内存 `o1=1,cell(0,0)` 无法区分「建造中」与「ghost 在手」（字段全等）；改用 footprint≥3000 仅确认 ghost，配合 credit 稳定(600/座)判建造完成；落格/判据仍 100% 内存。
- 坑2 offset：闭环 hover=目标+(1,0) 落格=目标；每次 trial 均记 hover_click 与落格。
- 坑1 漂移：每次点击前重读 chain_before 确认单位仍在；单位离格者标无效（B3）。

## 一句话结论
非像素主判据有效（A 闸 4/6 PASS）；目标格有己方步兵或车辆时，放置均被拒（B 5/5、C 5/5 有效 trial 全部链未变、无同格 BuildingClass），故「单位阻止放置」成立且非步兵专属。

## 真机收尾
进程已关闭：本卡启动的 pid 41892 已 Stop-Process，复核无残留 gamemd.exe（count=0）。
except.txt 未变（26,272 B、mtime 2026-11-12T22:29:17Z、SHA 6907F395…1094，与开工逐字节一致）；gamemd.exe 73201CC0…F67476、ddraw.dll 85E0F7D5…03A9 前后 SHA/size/mtime 全等（见 work/baseline_before.json 与 work/baseline_end.json）。
全程只读 RPM + 合成键鼠；未写进程内存/未注入 Hook/未改 ra2youli/未联网对战。现把 LIVE_LOCK 改为 RELEASED by LIVE-L2。

# W177-H · PROGRESS

> 目标 `ra2youli\gamemd.exe` SHA `73201CC0…F67476`（只读未改）。真机 pid 19960→3452，全程 ReadProcessMemory + Wow64GetThreadContext 只读 + 合成键鼠；未写内存/未注入/未改 `ra2youli\`/未联网。前置：LIVE_LOCK=W177-H、无残留 gamemd、基线 SHA/mtime 已记（`work/baseline_before.json`）。

## 结论表（三级分级：已证 / 静态推断 / 未证）

| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| C1 | hover 格全局 `dword[0x88095C]` 闭环定位成立：两处步长复测一致（4/4），5 次迭代 E=(4,−8)→(0,0)，200 ms 复核仍 (112,56)、cam 恒 (0,0) | **已证** | `CLOSED_LOOP.md`、`EVIDENCE/t1_steps.json`、`EVIDENCE/t1_goto_112_56.json` |
| C2 | 地基相对 hover 偏移 (0..2,+1..+2)：以 anchor (30,87)/(26,83) 使地基覆盖步兵格 | 静态推断（lead 更正，本卡按此操作） | `EVIDENCE/t2_place.json` |
| C3 | 落格瞬间同格：2 次尝试的目标格 `[+0xE4]` 在 ≤2 帧原子读均 =3×InfantryClass、无 BuildingClass ⇒ **运行时未兑现（0/2）**，非字节层拒绝（下单扣款未发生，credits 恒 10000） | 未证 | `EVIDENCE/t2_place.json`、`work/t2_place.py` |
| C4 | 静态允许（已证字节 `0x47C620` 比较集 {6,2,0x24} 不含 15/1）+ 运行时未兑现（0/2）+ 路径未被证伪 | 静态推断 | 前卡字节证 + 本卡 C3；**不写"不可构造"** |
| C5 | T3 高频采样 83,847 样本 / 34,638/s / distinct-frames=71，全量 JSONL；目标格链全程 3×InfantryClass（带速率"未观测到 BuildingClass"，非全域断言） | 已证 | `EVIDENCE/t3_hifreq.jsonl`、`t3_summary.json` |
| C6 | 稳态/推挤：3 s 内目标格步兵 `this` 集合逐字不变，`inf_left_target=False`（未观测到被推挤或离开） | 已证（带速率） | `EVIDENCE/t2_place.json` push_analysis |
| C7 | 游戏菜单空闲 ~54 s 会自行退出；harness 窗口偷焦点会让 `0x88095C` 停更，脚本须先 force_foreground | 已证（本会话观测） | `work/nav*.py`、`t1_goto_112_56.json` |

## 给审计的核心数字（可独立复算）

1. **5**：T1 从 E=(4,−8) 收敛到 E=(0,0) 的迭代次数（`t1_goto_112_56.json` trace 6 行含 it00）。复算：`python work/t1_goto.py 112 56 1000 600`，前台、同图同相机。
2. **4/4**：两处锚点 `J_cell_per_px` 分量一致性通过数（`t1_steps.json` consistency 全 `absdiff=0`）。复算：`python work/t1_step.py`。
3. **34,638/s × 71 帧**：T3 速率 × distinct-frames（1 帧即无效，71≫1）。复算：`python work/t3_hifreq.py`，得 `t3_hifreq.jsonl`（83,847 行，未截断）+ `t3_summary.json`。

## 卡点

T2 下单未生效：侧栏首图标 磁能反應爐(NAPOWR) 多次合成点击后 credits 恒 10000、建筑数组无 limbo NAPOWR ⇒ ghost 未真正举起、点击落到"选中单位移动命令"。**T1 硬门槛已达成，交付合格**；T2/C3 为诚实的运行时未兑现记录，T3 采样保持水准。详见 `UNKNOWNS.md`、`DISAGREE.md`。

真机收尾：全程只读内存/合成输入，未写内存/未注入/未改 `ra2youli\`/未联网；gamemd.exe/except.txt/ddraw.dll/ddraw.ini SHA+mtime 前后全等（`work/baseline_*.json`）；已只关闭本卡启动的 gamemd（pid 3452，现无残留）；LIVE_LOCK 改为 `RELEASED by W177-H`。

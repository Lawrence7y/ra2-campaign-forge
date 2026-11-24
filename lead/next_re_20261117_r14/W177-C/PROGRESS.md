# W177-C · PROGRESS（真机执行卡 · ③-b 第3次）

> 卡号 W177-C｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改）｜ImageBase 0x400000
> **结论：目标A、目标B 均完成。** 两局游戏（局1 被AI摧毁后重开局2）。全部只读内存 + 合成输入，未写进程内存/未注入/未改 ra2youli。

## 结论表

| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | 开局前后 gamemd.exe/ddraw.dll SHA-256 不变、except.txt 不变 | [已证] | `work/baseline_start.txt` + 本文件末收尾 |
| 2 | **目标A：连续成功放置 10 次**（三重佐证全中：额度−600 + owner=玩家 + 格链出现该对象） | [已证] | `LIVE.md` 目标A表 A01–A10；`EVIDENCE/A01_place.json`、`A02b_place.json`、`A08c_place.json`、`A_auto4.jsonl`、`A_final.jsonl`、`m16_final_state.json` |
| 3 | 放置两步机制：第1次点图标下单扣600建limbo(o1=1,o2=0,cell=0,0)，第2次点图标才拿起ghost | [已证] | `EVIDENCE/s02_ghost_*.png`(绿框/红圈出现)、B01、LIVE.md |
| 4 | 重叠复现次数 = **0**（10 次均不同 cell；未构造刻意重叠，暴露量=没找） | [已证·否定] | LIVE.md 目标A cell 列无重复 |
| 5 | **目标B：拒绝事件 3 次**（B02/B03/B04），多重信号=红圈+未入格+limbo态+额度Δ0 | [已证] | `EVIDENCE/B02/B03/B04_*.json`+截图；`REJECT_MACHINE.md` |
| 6 | 拒绝事件退款数 = **0**（本环境未复现 W177-B 的 9400→10000 退款） | [已证·否定] | B02/B03/B04 credit Δ=0 |
| 7 | 拒绝事件 limbo 未入格 = **3/3**；o1/o2 分布 (1,0)→(1,0)；+0x1AC u8/u32=(0,0) | [已证] | 同上 signals |
| 8 | 拒绝态目标格链前后逐字节一致（headA=0x15693c48,lenA=1,lenB=0）| [已证] | B02/B03 target before/after |
| 9 | 0x47C620 校验失败净效果=无副作用回滚（可观测后果，未取EIP） | [推断·可观测] | `REJECT_MACHINE.md` §4 |
| 10 | 相机原点 0x886FA0/0x886FA4 读数恒 (0,0)，改用每次截图判绿规避 auto-scroll | [已证读数] | `wc_probe.cam_origin`；`UNKNOWNS.md` U1 |

## 核心数字（给审计）

- **目标A**：成功放置次数（三重佐证）= **10/10**；重叠复现次数 = **0**（没找，非找了没找到）。额度：局1 10000→9400→8800；局2 10000→5200（8×600）。
- **目标B**：拒绝事件数 = **3**；其中退款数 = **0**；其中生成 limbo 未入格数 = **3**；[+0x81]/[+0x74] 拒绝前 (1,0)×3 → 拒绝后 (1,0)×3。

## 关键突破

W177-B 卡在「ghost 落不到格」的根因：**RA2 建造是两步**。第1次点图标只是下单扣款并生成 limbo 对象；必须待侧栏「就緒」后**第2次点图标**才拿起跟随光标的 ghost。本卡补足这一步后，绿框/红圈正常出现，配合「整块 3×3 footprint 纯绿才点击」即可稳定落格，达成 10 次。

## 纪律执行

- 成功三重佐证、拒绝多重信号，均不凭单一信号断言；否定结论（重叠0/退款0）标暴露量/如实报 0。
- 数量如实：拒绝3次、成功10次均逐次有证据；「没找」不写成「找了没找到」。
- 未写进程内存/未注入/未改 ra2youli/未联网/未改台账/未 git commit。
- 输入经 click_client（前台+归属校验），无裸 SetCursorPos 作点击工具；点击前重判绿框，不依赖固定屏幕坐标。

## 真机收尾声明

本人（W177-C）仅启动并关闭本卡 pid 的 gamemd.exe（局1 pid=35116、局2 pid=25992，均已 Stop-Process）；收尾 `Get-Process gamemd` 计数=0，**无残留进程**。收尾哈希与 except.txt 与开工前一致（见 `work/baseline_end.txt`）。现把 LIVE_LOCK 置为 `RELEASED by W177-C`。

## 交付物

`PROGRESS.md`｜`LIVE.md`｜`REJECT_MACHINE.md`｜`UNKNOWNS.md`｜`DISAGREE.md`｜`EVIDENCE/`（全部截图/JSON，不截断）｜`work/`（脚本可复跑）｜`coverage_delta.tsv`。

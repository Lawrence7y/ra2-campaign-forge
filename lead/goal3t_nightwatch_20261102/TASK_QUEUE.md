# TASK QUEUE（夜巡轮；只做 [auto-ok] 条目；其余等待有人轮）

> 纪律（全部条目共同约束）：零发射、零游戏进程、零部署、零新 Hook；冻结件与冻结母本零字节改动；
> 不改 `lead/GOAL_THREE_TARGETS_20261018.md`/`ROUND_SUBAGENT_LOG`/`PENDING_DECISIONS`（台账写入=收尾轮专属）；
> 不 commit、不 push；python 一律 `python -I -X utf8`；写域仅限本目录（`lead/goal3t_nightwatch_20261102/`）。

## 队列

- **[done 2026-11-02T23:26] T5·判档器已知趟复跑同判（③回归义务六轴之一）** —— Leader 会话当场执行：
  `_judge_h8v4_20261101.py --trip-dir l3_1101v4d` ⇒ rc=0、全 PASS、**31 档**，与 §508 同判；
  证据 `t5_judge_v4d_20261102T2326.txt`（判档器只读，趟目录零改动）。

- **[done 2026-11-03T09:20] 夜巡收尾** —— 见 `RUN_LOG.md` 末节。BOOT 已变（BOOT#8=11-03T08:54:17），
  夜巡基线 BOOT#7 作废；另如实登记「每 20 分钟唤醒自动化整夜未运行」。

- **[done 2026-11-03T09:38] T6·D-12② 全量普查 + §514 定性勘误** —— 91 窗/39 趟全量重算，
  发现 **§514「head 天然 B 型」有误（实测 head=C 型）**；全量口径差仅 +1.3066pp；
  根因锁定为 >10ms 采样大缺口（r=0.7448）。产物 `OCC_CENSUS_20261103.md`
  + `_occ_census_all.py` / `_occ_decomp.py` / `_occ_gapcorr.py` 及三份 `_out.txt`。台账 §515 已记。

- **[done 2026-11-03T09:45] T7·台账 §515 入账 + D-12 重述** —— 双台账各 +75 行纯新增（0 删除）；
  `PENDING_DECISIONS.md` D-12 改写为可裁形式（BOOT#8 重裁 + 勘误五点 + 选项 B 工作量量化）。

- **[wait] T1cmp·§515 异族对账回收比对** —— GLM-5.3-flash workflow `dwfrun-e1f81450` 在飞；
  回收后逐项比对 `OCC_CENSUS_XVERIFY_20261103.md` 与本线 `OCC_CENSUS_20261103.md`。
  **在飞中，不自行重启、不修订工作流**；provider 故障则如实登记等指示。

> 夜巡已于 2026-11-03 09:21 收尾（`# NIGHTWATCH ENDED`）。本目录后续按有人轮推进。

# -*- coding: utf-8 -*-
"""_append_485.py - append S485 (batch 2C hold=14.0 closure) to shared ledgers. Additive only."""


def append_lines(path, text):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n"); lf = raw.count(b"\n") - crlf
    nl = b"\r\n" if crlf > lf else b"\n"
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(x.encode("utf-8") for x in body.split("\n")) + nl
    fh = open(path, "ab")
    try:
        fh.write(out)
    finally:
        fh.close()
    return len(out)


S485 = """

# §485　②批 2C 收口（hold=14.0 跨 ceil 档单点，20261031T154139）：**主预测全中——闩边界首次实际收窄
#        (14.997,16.272] ⇒ (15.194,16.272]**；量化律新会话×ceil=14 档出样本 PASS；闩→退 2.003s 新下沿；
#        C 卡决策树判第 2 趟不需要；趟数 32

- **prepare 与验收**：C 席（会话模型）卡片 `lead/codex_round_20261030/C_BATCH2C_H14_20261031/BATCH2C_CARD_H14_20261031.md`
  + 探针 `_probe_h14_band_law.py`/stdout（律 5/5 亲算、锚点盘上复核、冻结件五件哈希）；Leader 逐项验收通过。
  C 关键发现（如实登记）：**hold=14.0 档已有 n=1**（212148 趟 closed=14.997 即未知区左端点出处）⇒ 本批为
  同档第 2 趟（新会话），非「新档首样」；预测带 [14.996,15.289] 与未知区关系按用户勘误口径改写
  （重叠=(14.997,15.289] 宽 0.292s；低端缝 [14.996,14.997] 宽 0.001s 落已知闩域）。
- **发射前（Y-3）**：preflight 10/10 全过、selftest **110 [OK]/0 [RED]**，tee 落盘
  `preflight_batch2c_20261031.txt`/`selftest_batch2c_20261031.txt`。执行环境注：selftest 经管道输出时
  GBK 崩（'⇒' U+21D2）；`-I` 隐含 `-E` 忽略 PYTHONUTF8 ⇒ 改 **`-X utf8` 旗标**（冻结件零改动、-I 纪律保持）。
  实际命令=`python -I -X utf8 lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py
  --live --approved --trips 1 --hold 14.0`（C 卡 argv 复刻＋-X utf8 执行面补注；--trips/--live/--approved
  系 C 卡推定·强据项）。批前冻结件五件哈希全命中（`LEADER_battle/frozen_recheck_h8_pre.txt`）。
- **趟读数（20261031T154139_9001_P3e_E12_T1，Leader 亲算 R-1 口径）**：verdict=OK、exited=True、
  exit_kind=natural、final_exitcode=0；closed_at_s=**15.194** ∈ 预测带 ⇒ **量化律出样本 PASS**
  （a+post=1.194∈[0.996,1.289]；hold_tl_n=14==ceil(14.0)）；**latch=True 且 Δ=0.101s（hwnd 归零 idx=1）
  双轴一致**、singleton 同步行归零；**闩→退=2.003s**（close_rows 原始时间戳：闩沿 idx55 t-rel=5.526、
  末行 7.529；既往带 2.004~2.108 ⇒ 新下沿）；exitstate 0×55→1×2（尾行 DICT:state=read_fail 系死进程读，
  不引用，Y-2）；a8=PASS、载体已删、stop=None、except 恒、killed_on_cleanup=None（自然退出无强杀）；
  ~21s 带不适用（闩族归零=closed+0.101=15.295，锚=本趟 popen t0，Y-481-D）；fork 轴如实登记：
  fork=spin_x_hook6_undetermined（三态未决：混合/读败，不承重）。
- **决策树（C 卡 §9）**：c1∈(14.997,15.289] ∧ 闩 ⇒ **第 2 趟不需要（主预测完全命中）**。
  **闩边界首次实际收窄：(14.997,16.272] ⇒ (15.194,16.272]**（下界上移 0.197s）；口径限定不变：
  每点 n=1、P3e 早窗菜单族内、Δ 判据族内使用（Y-481-E）、不判正常退仅判闩/不闩。
- **批后**：冻结件五件哈希复验逐位一致（`C_BATCH2C_H14_20261031/frozen_recheck_batch2c_post.txt`）、
  procs=0 真验、载体删、无部署无配置改动。趟数 **31→32**。
- **句态**：②硬门槛未达成、**RC-4 不收口**——本趟=又一例「闩→≈2.0s 自然退」（带内 +1），不构成放松；
  挂死 T204123 单例未复现（本趟 exitstate==1 仅 2 行 vs 挂死 1017 行）。①受测窗有限未复现不变；
  ③保持态（全程无冻结件字节变化、无他线写域、台账 Leader 追加）。
- **在飞**：B1 harness8 异族独立审查（dfmodel，dwfrun-5b59fd8f）运行中；**rate_limited epoch 1** 登记
  （§482 计数 1/10；stalled=no，不停不重启不修订）；①批次卡片已备
  （`GOAL1_BATCH_H8_FRAMEBOUND_20261031.md`），发射门=B1 GO＋冻结件复验（批前已采）。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

S486_IDX = """

## §485 批节 · ②批 2C（hold=14.0 跨 ceil 档单点 · 2026-10-31）

- 趟 `20261031T154139_9001_P3e_E12_T1`：hold=14.0／closed=15.194／latch=True／Δ=0.101s(idx1)／
  闩→退=2.003s(R-1)／exit=natural rc=0／a8=PASS／载体删／stop=None／except 恒／killed=None。
  verdict=主预测全中；**闩边界收窄 (14.997,16.272] ⇒ (15.194,16.272]**；律出样本 PASS（新会话×ceil=14）。
  命令=`python -I -X utf8 …candidate/_drive_c2_x_e12.py --live --approved --trips 1 --hold 14.0`；
  preflight/selftest tee 与批前后哈希见 `lead/codex_round_20261030/C_BATCH2C_H14_20261031/`。
"""

a = append_lines(LOG, S485)
b = append_lines(GOAL, S485)
c = append_lines(TRIPIDX, S486_IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))

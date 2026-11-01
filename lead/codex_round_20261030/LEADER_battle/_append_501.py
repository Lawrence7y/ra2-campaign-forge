# -*- coding: utf-8 -*-
"""_append_501.py - append S501 (v4 review + batch closure) to shared ledgers. Additive only."""


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


S501 = """

# §501　v4 复核回收（XVERIFY_V4_20261101.md，同族标注版）+ 长观测批收口（v4-a 作废/v4-b 有效轨迹）：
#        **红 0/GO-W-COND 三条件闭合**；S4 err=299 瞬态首发现；**会话内退化趋势+轮询率退化标记**；
#        深滞态全分辨形态=与 §497-500 同构（停滞占比 ≥87%）；趟数 39

- **v4 复核**（GLM 同族标注版，判定书 XVERIFY_V4_20261101.md）：**红项 0 ⇒ GO-WITH-CONDITIONS**。
  H8-7 四路 dump 完备（AST A1-A4 无第五路径）+缺省 False 等价（S1/S6 桩测）+逐拍 2.48µs≪拍距+
  60k 上限实测 0.99MB+精度 4 位小数够（裕量 500×）；发射器（投影 126-128≤130 六组合/白名单 5 条/
  R-1 承继 506 进程实测）；判档器八趟回归**逐字节 IDENTICAL**（synth 3/3+真机 3/1/1/1/3）。
  **条件闭合**：C-1 卡片改口径（判档器无轨迹检查 ⇒ 批后人工核三件套）；C-2 双参数同传+tee 含 argv
  （发射执行遵守）；C-3 写盘失败判读纪律（未触发）。批卡卡 Edit 同步。
- **v4-a 作废**：rc=63=EXIT_MODULE_ENUM_FAILED——`EnumProcessModulesEx` **err=299（ERROR_PARTIAL_COPY，
  Windows 瞬态：目标进程初始化中枚举失败）**；S4 反注入阶段 fail-closed 硬停（设计正确执行）；武装行在场、
  无 MEASURE 行 ⇒ H8-7 未及执行、无 C-3 情形；既往 37 趟首现 ⇒ 环境瞬态。载体清/零残留/except 恒。
- **v4-b 有效**：rc=0；**轨迹件在场（9989 样本=C-1 三件套过）**；verdict=frame_wait_timeout（reached=271/
  120s，overrun_kind=timeout）；判档 EXIT=3（设计内短路）。读数：
  - **装载期 16.6s**（1486 拍 frame≡0）——首次精确入账；
  - 等待段（0→271 帧/103.4s）：推进事件 267、增量几乎全 +1、间隔中位 0.048s（142<0.1s=爆发群欠采样）
    +长隙 0.1-0.7s ⇒ **深滞态形态与 §497-500 爆发-停滞同构**，停滞占比 ≥87%（帧 0-271=最早战斗段
    最深滞）；
  - **会话内退化趋势（新）**：同会话各趟到达帧 400/800 速度递减（v3-a 65.5s→400 / v3-b 40.0s→400 /
    v3-c 120s→1058 / v4-b 120s→271）——会话越跑越慢；
  - **轮询率退化标记（新）**：_doze(0.002) 名义 500Hz 实测 **83Hz**（9989/120s，每拍 ~12ms）——系统计时
    分辨率恶化本身即会话状态标记（v3-a/b 同旗标 347/283Hz）。
- 批判定：≤2 趟帽内收口（v4-a 作废+v4-b 有效）；双稳切换的等待段内无一次切换（全程深滞）——切换定位
  仍依赖窗样本（§500 已给 ±13-25 帧）；判档 EXIT=3/轨迹三件套全过。趟数 **37→39**。
- 句态：①深滞态全分辨形态确认（≥87% 停滞、爆发-停滞同构）+会话内退化趋势+轮询率标记；②硬门槛未达成、
  RC-4 不收口；③保持态（v2/v3/v4 三代哈希批后复验逐一吻合、五件冻结件零字节、procs=0）。
- **下一最小动作（待用户裁）**：A''=会话退化/状态机触发器判别批（跨 BOOT 对照+trip 序号 vs 深度相关——
  现有 39 趟数据已可先做离线相关分析）；C=热点定位（E3 未授权）；D=维持。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """
- 趟 `l3_1101v4a`（…V4-20261101A）：**作废**——rc=63=EXIT_MODULE_ENUM_FAILED（S4 EnumProcessModulesEx
  err=299 瞬态，fail-closed 正确；H8-7 未及执行）；载体清/except 恒/rc≠0 如实。
- 趟 `l3_1101v4b`（…B）：harness8 v4 38244d29／N=800+--h8-wait-trace／**轨迹 9989 样本在盘**／
  verdict=frame_wait_timeout（reached=271/120s）／判档 EXIT=3／装载期 16.6s 入账／深滞态 ≥87% 停滞
  （爆发-停滞同构）／rc=0。**批发现：会话内退化趋势+轮询率退化 83Hz 标记**。
"""

a = append_lines(LOG, S501)
b = append_lines(GOAL, S501)
c = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))

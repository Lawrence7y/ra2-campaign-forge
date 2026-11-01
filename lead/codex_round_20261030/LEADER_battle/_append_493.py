# -*- coding: utf-8 -*-
"""_append_493.py - append S493 (B2 same-family reconciliation adoption) to shared ledgers. Additive only."""


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


S493 = """

# §493　B2 同族标注版判定书回收（GLM，familyLabel 在场；前任 dfmodel 11 探针全吸收+p01 纠错 1 处）：
#        **红项 0**、黄项 11 全采纳（含①复现信号跨会话收紧 Y-11）；**q/r 张力两层消解**（frame 语义定谳
#        battle 起点；差异为真、归因开放）；Δ 轴 n=14 零例外；趟数账 UNVERIFIED 如实

- **族属**：同族标注版（GLM，非异族；§492 处置）。前任 dfmodel 11 探针（p01-p11，比 §492 所记多 3 支——
  截停间隙续产出 p09/p10/p11）全部逐支配对吸收：p01/p02/p03/p06/p07/p10 亲跑逐字节复现、p08 复现（枚举浮动）、
  p04 崩溃段未重跑（p05/p10/p11 接续）、p05/p09/p11 复读；**前任错误 1 处点名**（p01§(4) post 定义漂移，
  其 p02 已自纠）；本任独立增量=_b2g_v1_core/_b2g_v2_framezero+判档器两趟亲跑。判定书=
  XVERIFY_H8TRIPS_20261031.md。
- **主判定**：②批 2C 全 CONFIRMED（closed 15.194/闩/Δ 0.101/律 a=0.628 post=0.566 PASS/a8/载体/tee 亲点）；
  ①批 ha/hb 全 CONFIRMED（C-1 武装双证、窗数据、判档 EXIT 3/1）；台账 §485-487 审计红 0。
- **黄项 11 采纳（口径勘误落地）**：
  - **Y-11（重要，①headline 收紧）**：「①复现信号成立」⇒「满员早相慢帧**再现于 2/3 会话、会话强方差**」
    （10-21 慢 7.4fps / 10-30 q+r 快 ≥23.7 / 10-31 慢 3-11fps）——**会话方差升为一等变量**，v3 设计必须
    含跨会话对照；「复现」一词本批起按此口径使用。
  - Y-4：闩边界**最紧闭轴=(15.194,16.091]**（E5h15 16.091 在案，16.272 非最紧；§485 未复述该注——补注）。
  - Y-3：闩→退 2.003=**进程死亡上界口径**（退沿=首个读败行）；数值行末口径 1.001 ⇒ 真退∈(1.001,2.003]；
    族内先例同口径故可比——引用须带口径。
  - Y-2：闩→退带引用口径=族内自然退闩趟全带 [2.003,3.102]（n=8）；「2.003 新下沿」不受影响。
  - Y-9：**hb units0 双口径裁决**：窗级主张用 **1341**（counters 首行），1347（gate）并列注明——§490 待裁闭合。
  - Y-7：本批窗数=**4**（ha w0+hb×3；ha 短路后 w1/w2 按设计不落）——「5 窗」改 4 窗。
  - Y-8：units 链引用=窗首/窗末并列（1341→1298｜1297→1262｜1262→1179）。
  - Y-10：收尾准句=**无中途强杀、harness 全程 rc=0、游戏按缺省 terminate 收尾**（term_sent=True；
    「强杀 0」措辞误导，不再使用）。
  - Y-1（killed 键缺省语义）、Y-5（75 窗 vs 全库 49 窗口径注）、Y-6（__pycache__ 3 vs 4 差 1 未考）照录。
  - ask 校正 1：本 ask「hb=EXIT0」转述失真——亲跑 EXIT=1；§489 原文正确，台账无错。
- **q/r 张力两层消解（§487 保留项重构）**：
  - **frame 语义定谳=battle 起点**（③关闭）：菜单不累计（②协议趟 frame≡0）+ 决定性证据=units 首现行
    （t_rel 1-2s，进程已活 44-58s）内插 frame=0（自进程累计假设被否）+ H8 绑帧自洽；读点同 VA 跨代同语义。
  - 差异为真（②收窄）：q/r 早相 ≥23.7fps 亲算成立；hb 0-991 帧实测 174.0s（5.69fps）＞q 全程 124.7s
    ⇒ q 前段不可能同慢；定量界 q/r 早相 ≥15.9/15.6fps，比 hb 快 ≥2.7×。
  - **归因开放（①维持）**：会话方差 vs H8 轮询不可分——l3_20261021 无轮询亦慢 ⇒ 轮询非必要条件，
    但 3-5.5 与 7-12fps 之差可能含轮询贡献 ⇒ **v3 H8_WAIT_HZ 对照趟为判别实验**。
- **Δ 轴 n=14**：闩族 9（max 0.122）/不闩族 5（min 0.402）/灰区 0；族内零例外维持（Y-481-E 限定）。
- **gaps（如实）**：趟数账 UNVERIFIED（盘上无单一权威清单）；B1/RR 内部实测按留档吸收未逐支复算；
  §485 批后 procs=0 按台账采信；__pycache__ 差 1 未考；q/r stage_seconds 语义备查。
- 句态（按 Y-11 收紧后）：**①满员早相慢帧再现于 2/3 会话（会话强方差），归因开放待 v3 对照**；
  ②硬门槛未达成、RC-4 不收口（闩边界最紧闭轴 (15.194,16.091]）；③保持态。趟数 34。
- **下一最小动作（待用户裁）**：A=v3（在局闸降级+判据重设计+**H8_WAIT_HZ 对照旋钮**+跨会话对照设计
  +积压 5 项）；C=热点定位；D=维持。**B2 对账债清零**（同族标注版闭合；异族版留待 dfmodel）。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """

### §493 对账节 · B2 同族标注版（GLM）· XVERIFY_H8TRIPS_20261031.md
- 覆盖：②批 154139（hold14.0）+①批 l3_20261031ha/hb+q/r 基线张力+Δ n=14+§485-487 审计。
- 红项 0；黄项 11 全采纳（Y-11 跨会话收紧/Y-4 最紧边界 (15.194,16.091]/Y-3 真退∈(1.001,2.003]/Y-9
  units0=1341 裁决/Y-10 收尾准句/Y-7 4 窗）；frame 语义=battle 起点定谳；q/r 归因开放（v3 对照判别）。
"""

a = append_lines(LOG, S493)
b = append_lines(GOAL, S493)
c = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d, GOAL +%d, TRIPIDX +%d" % (a, b, c))

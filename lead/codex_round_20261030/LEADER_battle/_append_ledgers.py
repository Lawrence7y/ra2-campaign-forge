# -*- coding: utf-8 -*-
"""_append_ledgers.py — Leader 统一追加共享台账（二进制追加，不改既有字节、不重写换行）

安全：以 'ab' 打开，仅追加本批新行；每文件按其**主导换行**（ROUND=LF；TRIP_INDEX/GOAL3T=CRLF）
生成新行，绝不触碰历史段（规避 §403「整文件 CRLF→LF 误转」教训）。
"""
import os

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
TIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

S474 = """

# §474　真机双批（①L3×31档活动战斗 + ②E5关窗时机(11.19,16.09)缝内补点，用户『本轮允许真机』）
#        趟数 24→29；①首次31档×974/941交火无战斗期卡顿(未复现口径不变)；②同会话闩边界收窄
#        (14.997,16.272]+绝对时钟模型被本会话数据否证；RC-4不收口；③保持态

- **会话事实**：机器本日 **13:10:38 重启**（新开机会话，BOOT 墙钟 1793337038…）；E5/D-11 批属
  10-29 会话 ⇒ 本批读数以本会话内互比为主，跨会话仅作形态类比（V11-c）。子代理不占真机，Leader 串行亲跑。
- **①（L3 高负载 × 31 档活动战斗 · 2 有效趟）**：既有证据离线复算（Leader 亲算原始 500Hz 采样+逐秒 counters，
  `lead/codex_round_20261030/LEADER_battle/STALL_ANATOMY_raw.json`）证：31 档战斗趟（t55k 842u/l1a 732u/e4 702u）
  长停顿**全是终局帧冻结**（units 静态/W1W2 空窗），非活动交火 lag；唯一高负载 L3(1342u) 只在 10 档。
  ⇒ 判别格「31 档 × ≥900 交火」此前不存在。趟 `l3_20261023q`(units0=974,pre_fps=31.34) + `l3_20261023r`(941,30.72)
  harness7 `d019e8be`+sf10c `f3bb0a4e`+`--h7-keep-rect-wait`活动战斗臂：**W0 交火窗 units 逐秒降(−99/−81) 战斗期内
  长停顿 0/0、fps_avg 31.1/31.3、frame_ms p99 44/41、max 68/46**；W1/W2 帧冻结伴 units 转平/一方归零=终局。
  ⇒ **①在 31 档 × 本会话可达最高交火负载仍不复现**（有限窗口口径不变，不派优化补丁，C26-02）。
  **诚实边界**：units0 随档位变（31 档快帧把 W0 推到交火后段→974/941，非 10 档满员瞬间 1342）⇒ 本批证「31 档×~950
  交火无卡顿」，**不等于**「31 档×1342 峰值交火无卡顿」；要攻后者须改测量协议（窗起点绑帧计数），属候选迭代+独立复核，非本批。
- **②（E5 关窗时机缝内补点 · 3 有效趟）**：R-064 独立复核（B 线，qfmodel）在飞；本轮先做最高信息量非侵入实验。
  E5 对账红项 R3 把闩边界降为「关窗∈(11.19,16.09] 内某处·两档零采样」⇒ 缝内从未测点。用已放行 E5 候选件
  `--hold 13/14/15`（各 1 趟，被动读 exitstate/frame/hwnd/tick，零新代码）发射前 --preflight 全过 + --selftest 110 红=0：
  **hold13(close14.131)闩=True natural code0；hold14(14.997)闩=True code0；hold15(16.272)闩=False 存活至窗末清扫**。
  ⇒ **同会话闩边界收窄到 close∈(14.997,16.272]**（较 E5 (11.19,16.09] 显著窄）；**闩→退间隔≈2.004/2.008 s** 跨会话复现。
  **关键否证**：hold15 close16.27 观察窗 120s 完整覆盖绝对时刻 21~22s（hold13/14 闩处）却全程 exitstate 恒 0 不闩
  ⇒ **纯绝对时钟模型（『到 21~22s 就闩』）被本会话内数据否证**——印证 §473 Leader 对 R3 稻草人的辨析：操作变量=关窗时机
  经『关窗时引擎阶段』中介，非绝对时刻。三趟 a8=PASS/载体删/stop=None/except 恒/boot 极差 13ms(同会话)；
  hold15 killed_on_cleanup=[[19512,loader],[61092,gamemd]] 单记（本批可归属进程）。E2：hold13/14
  `spin_x_hook6_undetermined`=present→(进程退出)read_fail **两态**(absent=0，E5 Y3 口径)，ws 死进程伪读数不引用。
- **三目标句态**：①受测窗有限未复现（31 档高交火新增覆盖，句态不变）；②硬门槛**未达成、RC-4 不收口**
  （hold15 不退+挂死单例 T204123 未在批内复现+六臂 9/9 不退在案；本批使机制图景更硬、边界收窄、绝对时钟替法被否）；③保持态。
- **③（贯穿两批）**：E5 候选件 `--hold` 参数化迭代（非冻结件），v2 `6afe2711`/earlyclose `2e970eec`/harness7 `d019e8be`/
  gamemd `73201cc0` **批前后零字节复验**；发射用 `--live --approved` CLI 闸值（非文件常量翻闸、无还原负担）；
  短 TEMP(4 字符)；残留进程 0/载体残留 0；零扩 Hook/注入/写退出焦点/部署/历史改写。
- **账**：趟数 24→**29**（本批 5 有效：①2+②3，批准范围内；①单趟≈260s、②单趟≈27s）。真机新增=5。
- **在飞**：A 线退出判别设计（GLM 通道）、B 线 R-064 独立复核续办（qfmodel 通道）未归；本批读数交异族对账（下轮）。
"""

TIDX_ROW = """

## 真机双批·本会话（2026-10-30，BOOT 13:10:38；台账 §474；①L3×31档 + ②E5关窗时机缝内补点）

**② E5 关窗时机 (11.19,16.09) 缝内补点**（驱动=E5 参数化候选 `90a1890a…38d03` 直跑，`--hold 13/14/15` 各 1 趟；
Guard=1+Bail=1 菜单早窗；趟目录落 c2ab_x 正规位；档位以 `_rec.protocol` 为准勿凭目录名）

| 档 | 趟目录 | closed_s | latch | 终态 | exit_after_close | rec256 | tl256 |
|---|---|---|---|---|---|---|---|
| window+13.0s | 20261030T211741_9001_P3e_E12_T1 | 14.131 | **True**(row77,+7.736) | natural **code0** | 9.74 s | 7e02d38f…13ed1 | 0cf92e49…509ff |
| window+14.0s | 20261030T212148_9001_P3e_E12_T1 | 14.997 | **True**(row70,+7.032) | natural **code0** | 9.04 s | 26b6b33b…d20df | 751df9a3…743ec |
| window+15.0s | 20261030T212233_9001_P3e_E12_T1 | 16.272 | **False** | still_running→清扫(killed=[[19512,loader],[61092,gamemd]]) | — | be90b0ac…b5c2f | 7dfe8bd9…5ccf5 |

- 判读（只报并趟计数）：**同会话闩边界收窄到 close∈(14.997,16.272]**（E5 原 (11.19,16.09] 缝内首次有点）；
  闩→退间隔 2.004/2.008 s（与历史≈2.0 s 跨会话一致）。三趟 a8=PASS/载体删/stop=None/except 恒/boot 极差 13ms(同会话)。
- **绝对时钟模型否证**：hold15 关窗 16.27s、观察窗 120s 完整覆盖绝对 21~22s(hold13/14 闩处)却 exitstate 恒 0 不闩 ⇒
  「到 21~22s 就闩」被本会话内数据否；支持关窗时机经引擎阶段中介（§473 R3 辨析）。机制仍「相容 not contradicted」
  （进 bail 环零运行期读数；hook6 只证 6 字节在位；hold15 无闩无慢采样）。
- E2：hold13/14 spin_x_hook6_undetermined=present→(进程退出)read_fail **两态**(absent=0)；ws 死进程伪读数不引用。
- **RC-4 不收口**（hold15 不退+挂死 T204123 单例未在批内复现+六臂 9/9 在案）。趟数 24→29（②本批 3 有效）。

**① L3 高负载 × 31 档活动战斗**（harness7 `d019e8be`+sf10c `f3bb0a4e`+`--h7-keep-rect-wait`；载体趟后删；
趟目录 `out/.../qc161_u0400_trip/l3_20261023q` 与 `l3_20261023r`；台账 §474）

| 趟 | units0 | pre_fps15 | W0 交火(units 逐秒降) | W0 长停顿≥0.5s | fps_avg | frame_ms p99/max |
|---|---|---|---|---|---|---|
| l3_20261023q | 974 | 31.34 | 953→854(−99) | **0** | 31.12 | 44.4/68.4 ms |
| l3_20261023r | 941 | 30.72 | 923→842(−81) | **0** | 31.32 | 41.4/45.7 ms |

- 判别力：31 档战斗负载从 842(旧会话)推到 974(本会话)，交火期内长停顿 0/0 ⇒ **①在 31 档×本会话最高交火仍不复现**（口径不变，不派优化）。
- 诚实边界：units0 随档位变（31 档快帧把 W0 推到交火后段→974，非 10 档满员瞬间 1342）⇒ 未证「31 档×1342 峰值」；W1/W2 冻结伴 units 转平=终局非战斗卡顿。
"""


def dominant_nl(path):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return b"\r\n" if crlf > lf else b"\n"


def append_lines(path, text):
    nl = dominant_nl(path)
    raw = open(path, "rb").read()
    # normalize text lines, emit with file's dominant ending; append-only, no rewrite
    body = text.replace("\r\n", "\n").strip("\n")
    out = nl + nl.join(l.encode("utf-8") for l in body.split("\n")) + nl
    with open(path, "ab") as fh:
        fh.write(out)
    return len(out)


a = append_lines(LOG, S474)
b = append_lines(TIDX, TIDX_ROW)
print("APPENDED ROUND_LOG +%d bytes (nl=%s)" % (a, dominant_nl(LOG)))
print("APPENDED TRIP_INDEX +%d bytes (nl=%s)" % (b, dominant_nl(TIDX)))

# -*- coding: utf-8 -*-
"""_append_486.py - append S486 (B1+RR review cycle) & S487 (batch H8 results) to ledgers. Additive only."""


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


S486 = """

# §486　harness8 异族审查闭环（B1 判定书 29KB + 修复包五件 + RR 聚焦复审）：v1 红项 1（R-1）→ v2 红项 0
#        ⇒ GO-WITH-CONDITIONS；条件 C-0..C-6 全采纳；**epoch 口径自纠**（B1/RR 全程零真停摆）

- **B1 判定书**（`XVERIFY_H8_20261031/XVERIFY_H8_20261031.md` 初版 29KB，dfmodel，3.5h 限流下完成，
  产物 25+ 件全留痕）：harness8 v1 本体**全绿**（缺省中性三法交叉=diff/AST/离线双跑 rec 17/17 全等；
  拒采路径与 late_start 先例逐字同构；预算余量 ≈284s；_doze 纪律；禁止面 API 计数与母本全同）；
  **发射器副本红项 R-1**（Leader 誊写漏 `th32ParentProcessID` ⇒ sizeof 560≠568 ⇒ Process32FirstW 恒败
  ERROR_BAD_LENGTH ⇒ list_procs 恒空 ⇒ A8 预检 fail-open + 清理静默假成功；实测两版对照 504 条 vs 0 条）
  + 黄项 Y-1..Y-8 ⇒ NO-GO。Leader「仅三处差异」声明被证伪——**异族独立复核价值实锤**。
- **修复包五件**（Leader 亲办）：harness8 v2 `dd5459fe0cf3461c`（Y-2 跳帧拒采 H8_OFFSET_MAX_FRAMES=2 +
  first_read 标注 + Y-3 措辞降格 + Y-4 探针耦合声明 + Y-5 + Y-7 N<1 拒发；0删/160增）；发射器 v2
  （R-1 补行 + Y-6 目录模板缩字 + 声明逐处枚举；实证 sizeof 568/枚举 499/两后缀 100≤130）；判档器副本
  `_judge_h8_20261031.py`（Y-1：短路集 +frame_overrun/+frame_wait_timeout、白名单 +v2；B1 合成趟翻转实测
  EXIT 2→3；v1 sha 正确退役）；卡片 v2（假说句降格/Y-4 探针不承重/C-5 时间口径/判档器接入）；
  设计件勘误注 §6。
- **RR 聚焦复审**（同写域续任，dfmodel，1.2h；判定书增写 §1-§6 于主判定书）：v2 **红项 0**；
  中性双跑 v2 复验（eq7p/eq8p 三轮 + 墙钟抖动隔离：差异键 ⊆ 计时键集）；Y-2 边界实测
  ([None,900]/[10,900]⇒jump 拒、[399,401]/[400]⇒达标)；N<1 哑图实测 exit 2；门禁演算 v2 129/130/130；
  真机产物复算 75 窗相邻拍 maxΔ（74 窗=1、1 窗=3——自然跳帧基线）；判档器翻转复核；pyc 自扰审计
  （如实：__pycache__ 4 枚系审查副产品，源件哈希/mtime 两轮复验未变，处置=留置登记不删）。
  **GO-WITH-CONDITIONS**。
- **条件采纳（C-0..C-6，全部落地）**：C-0 哈希清单换 v2（`frozen_recheck_h8_v2.txt` 六行全命中）+
  **v2 字节自此刻冻结**（再改动=判定书作废重审）；C-1 发射显式 `--extra-argv "--h7-measure-start-frame 400"`
  + 验收硬前置（META.h7_measure_start_frame==400 ∧ h7_frame_wait 在场，缺一即「未武装非本批样本」）；
  C-2 采 (b)：jump 拒采预登记=「等待期 ≥96ms 引擎停顿」证据不按噪声重排；C-3 离线自检
  `_adjudicate_h8_offline.py` 全过（tee `c3_offline_adjudicate_h8.txt`；_H8_STATE 写入=rec 镜像处置如实）；
  C-4 以发射 tee 2>&1 满足意图（拒绝行入批日志，不破 C-0 冻结——处置登记）；C-5 20min 帽=发射→收尾全程、
  第 2 趟仅首趟 EXIT∈{2,3} 时补发；C-6 证据面=窗 JSON+ h7_frame_wait，探针不承重、不传 --frozen-dump。
- **§482 epoch 口径自纠**：计数对象=「可观测停摆」（stall 通知或巡检所见 stalled=yes）；B1/RR 全程
  stalled=no + 产物连续落盘 ⇒ **真停摆 epoch=0**；此前按 rate_limited 标签的保守计数（1→9/10）作废。
  §479 判据语义教训再适用。reviewer __pycache__ 副产品 4 枚留置登记（ inert，不属清扫面）。
"""

S487 = """

# §487　①批 H8 绑帧满员格（2 趟，20261031ha/hb）：**①复现信号成立（限定域：满员早期交火相位）**——
#        满员相位精确命中（units0=1342/1341）；frame 400-1000 域 fps 3-11、p50 72-335ms、
#        p90 154-485ms、max_stall 0.49-0.75s（战斗期 ≥0.5s 冻结判据命中）；晚相位基线 31-37ms@31fps；
#        卡片判据设计失配如实登记；趟数 34

- **发射面**：RR GO-WITH-CONDITIONS 条件闭合后串行 2 趟（`_launch_h8_20261031.py --suffix a/b
  --extra-argv "--h7-measure-start-frame 400"`）；A1/A2/A11/A8 全 OK（A11 实得 dd5459fe=v2、A8=R-1 修复后
  真实判 0）；rc=0/0；170.2s/241.1s；载体清零、procs=0；批后冻结六件逐位（含 v2 冻结维持）。
- **C-1 武装核验（两趟全过）**：META.h7_measure_start_frame=400 ∧ h7_frame_wait 在场；
  绑帧等待本体完美：ha wait_s=73.135（25349 拍≈347Hz）/hb 94.676（26939 拍），reached=400、offset=0、
  零越界零超时零跳帧。
- **满员相位命中（本批判别力兑现）**：ha units0=**1342**（=10 档早窗 l3_20261021 满员数逐位）；
  hb units0=**1341**（w0）→1262（w1）→1179（w2），units 持续下降=活动窗。
- **①复现信号（n=2 趟 5 窗全落满员域）**：ha settle 窗（frame 400-412）fps≈3.0、p50=334.9/p90=485.1ms、
  max_stall=0.491s；hb w0（437-606）fps 6.8/p50 106.6/p90 296.8/max_stall 0.494；w1（607-725）fps 4.7/
  p50 182.9/p90 398.6/**max_stall 0.750s**；w2（726-991）fps 10.6/p50 72.0/p90 154.3/max_stall 0.580。
  **设计件 §2.3 复现判据双命中**（p90≫40ms ∧ 战斗期 max_stall≥0.5s）——满员早期交火相位帧时膨胀 ≈10×，
  晚相位基线（q/r frame 2955+, ~950u）31-37ms@31fps；hb w2 已见随 units 回落回升（10.6fps）⇒ 慢度与
  存活单位量/交火强度方向自洽。**「限流器藏不住真工作量」成立**。
- **判据设计失配（Leader 设计责任，如实）**：卡片原判据「V11-a pre_fps15≥25」与 harness 在局闸（≥3fps）
  均编码「窗应在健康帧率相位」——而本批目标恰是低帧率早相位；ha 因闸 2.678<3.0 判 no_advance（设计内
  短路 EXIT=3 正确分类），hb 6.676 过闸开满三窗。两趟均不满足卡片字面「有效样本」，但**失效原因=现象
  本身**。处置：批结果按「①复现信号（限定域）」登记，不按卡片原假说句式宣称；闸语义/判据重设计=下批
  事项（harness8 v3 候选：H8 武装时在局闸降为「帧推进存在」级 + pre_fps15 降为数据不设门；另加
  H8_WAIT_HZ 可调做轮询影响对照）。
- **诚实保留项（未排混淆）**：① H8 等待环 347-500Hz 只读轮询的观测影响未做对照（v3 加 WAIT_HZ 旋钮
  可辨）；② q/r 基线趟 frame 0→2955≈125s 平均 fps 张力未消解（q/r 早相若同慢则到不了 2955——需 B2 对账
  q/r 场记 battle 起点与帧计数起点语义）；③ frame 计数器起点语义（map load 重置 vs 进程起点）未定谳，
  影响跨趟帧域对比口径；④ ha/hb 相位微差（wait_s 73/95s）⇒ 早相位帧率本身高方差（2.7→6.7 fps 同 N）。
- **批判定**：≤2 趟帽内收口；无弹框/异常/交互；强杀 0（两趟自然走完 rc=0）；清扫只限本批载体。
  趟数 **32→34**。三目标句态：**①受测域更新——满员早期交火相位复现慢帧（n=2），晚相位与既有「未复现」
  结论不变**；②硬门槛未达成、RC-4 不收口（②闩边界 (15.194,16.272] 在案 §485）；③保持态（全程冻结件
  零字节、v2 字节冻结维持、无他线写域）。
- **下一最小动作（待用户裁）**：A. harness8 v3（闸语义+判据重设计+WAIT_HZ 对照旋钮）再批；B. B2 异族对账
  （本批 2 趟 + §485 ②批 1 趟 + q/r 基线张力消解）；C. 热点定位批（若认 ①复现：满员早相 p50 335ms 的
  构成分解——须 E3 授权或先做被动哨兵差分）；D. 维持现状仅入账。
"""

LOG = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
GOAL = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
TRIPIDX = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\TRIP_INDEX_20261028.md"

IDX = """

## §486/§487 批节 · ①批 H8 绑帧满员格（N=400 × L3 · 2026-10-31）

- 趟 `l3_20261031ha`（QC161-U0800-L3-H8-20261031A）：harness8 v2 dd5459fe／N=400 武装 ✓（wait 73.1s/
  347Hz/offset 0）／units0=1342 满员命中／settle 窗 frame 400-412 fps≈3.0 p50=334.9ms p90=485.1ms
  max_stall=0.491s／verdict=no_advance（闸 2.678<3.0，设计内短路 EXIT=3）／rc=0 自然走完。
- 趟 `l3_20261031hb`（…B）：同配置补发／wait 94.7s／三窗全开 verdict=ok：w0(437-606) 6.8fps/1341→1298/
  p50 106.6/p90 296.8/stall 0.494；w1(607-725) 4.7fps/→1262/p50 182.9/p90 398.6/**stall 0.750s**；
  w2(726-991) 10.6fps/→1179/p50 72.0/p90 154.3/stall 0.580／rc=0。
- **批判定：①复现信号成立（限定域=满员早期交火相位 frame≈400-1000）**；判据设计失配如实（§487）；
  预检 A8/A11 经 R-1 修复后真实有效；判档器副本 EXIT=3/0 分类正确；批后冻结六件+procs=0 复验过。
  命令=`python -I -X utf8 lead/goal1_harness8_20261031/_launch_h8_20261031.py --suffix a|b
  --extra-argv "--h7-measure-start-frame 400"`；判档=`_judge_h8_20261031.py --trip-dir <趟目录>`。
"""

a = append_lines(LOG, S486)
b = append_lines(GOAL, S486 + S487)
c = append_lines(LOG, S487)
d = append_lines(TRIPIDX, IDX)
print("APPENDED LOG +%d+%d, GOAL +%d, TRIPIDX +%d" % (a, c, b, d))

# 裁决书复查（2026-11-04）

**判定：需修改后执行。** 未推翻“D-15采用修正A、追加勘误；D-13暂停当前E3→①方案”的选择。发现两处落实文书漏洞：正文要求的混杂控制字段未完整进入验收表，以及v4c趋势引用未标明派生指标。修改范围见下文；不需要重新派发全库核验，也不需要真机或侵入采集。

本次显式写入仅为本文件；只读裁决、底账、有关原报告、原始JSON，未修改裁决书、台账、PENDING、核验件或真机件，未启动/终止游戏进程、未读活进程内存、未commit。

## 1. 需要修改的问题

**R1／中：验收表存在漏验口，正文已经要求的47窗混杂字段可能被漏交。**

[RULING.md:150](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:150)明确要求为22慢窗及25对照登记map、harness版本/哈希、实际起止帧、门控、units0取值阶段。但[EX-1验收项:163](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:163)只逐项规定了路径、trip_id、时长、avg、p50、max_stall及字段来源；[EX-4验收项:166](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:166)也未把前述47窗字段表列作必查产物。交付者只列数字清单、三个机制缺口和v4c线索，可能满足表中逐项判据，却漏掉正文的核心配对约束。

这里指出的是**验收表未闭合正文要求**，不是正文没有要求这些字段。本线此前恰因版本/地图/相位混杂而误报“同负载跨时段差”，见[S544汇总件:119](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md:119)。因此应在EX-4或EX-1增加明确判据：47个目标窗逐行具备上述字段列；无记录的单元格写“缺”并标明查阅来源；EX-5核对47行覆盖和字段列，缺列/漏行不验收。无需要求补齐原件本来没有的数据。

**R2／低：v4c的18.54→28.42→30.71是派生live_fps，正文未标口径。**

[RULING.md:151](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:151)沿用汇总及核验报告的这组数，却没有注明它是live_fps。原报告确实如此报数，见[hy4free VERDICT.md:34](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/VERDICT.md:34)、[qfmodel V2/REPORT.md:247](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V2/REPORT.md:247)；但裁决自己又规定摘要主指标为fps_avg，见[RULING.md:89](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:89)。这不是原报告数字算错，而是裁决转述未把字段身份带过来，后续落实可能把派生值填进avg栏。

本次回到三个原始JSON确认：fps_avg分别为**18.520948494813613、28.40179635682234、30.681571141892938**；帧沿派生live_fps分别为**18.539626790502314、28.416096013424877、30.70530239738328**，原件没有live_fps存储字段。命令及输出见第3节。

修正任选其一即可：正文主序列改成“fps_avg 18.52→28.40→30.68”；或保留现有序列并明确“派生live_fps，仅作诊断”，同时列出avg序列。EX-4同步要求趋势数值注明字段/派生公式。**两组数都支持趟内由慢转快；该问题不推翻趋势，也不改变暂停E3的选择。**

## 2. 对任务六项检查的判定

1. **是否回避裁决：未发现。** [RULING.md:73](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:73)已经选择22核心、保留11异常；[同件:97](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:97)选择追加勘误；[同件:128](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:128)关闭当前E3→①实施申请。[同件:153](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:153)允许以“现有件不能闭合机制”作为有限交付终点，未把方案选择重新挂成待定。
2. **动作能否验收：总体具体，存在R1漏验口。** EX-1至EX-4有指定文件和可数项，且明确尚未产出；本次未验收这些未来产物。应补齐正文与验收表的字段对应后执行。
3. **数字与材料：两处关键原始样点抽查通过，另查出R2字段标注问题。** 0.749879秒和T34约24.734760秒均得到原始samples支持；T34原存值比重建值多1微秒，裁决已披露。这里只抽查指定窗口，不冒称重建过22窗全体最大值或全库计数。
4. **是否迁就本线：未发现整体照单接受，R2是尚存的转述缺口。** 本次读了[S544汇总件§3:109](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md:109)的11条错误。裁决拒绝把11停摆窗一律定为终局，并纠正qfmodel“只是版本效应”“补参必过”等归述，见[RULING.md:176](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:176)、[同件:181](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:181)。这些是实质修正，不能仅因仍选“修正A”就判为迁就。
5. **D-13是否正视全程低速：暂停选择成立。** 题目第5项明确对象是全程低速；[hy4free VERDICT.md:72](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/VERDICT.md:72)也如此描述22窗。持续低速本身并不给出一个特殊的“停滞瞬间”；必须解释的是持续低速期间墙钟时间落在哪里，不能拿旧短停事件比例直接替代这个问题。裁决不仅否决N=1秒，还禁止仅降N、加频率或改绑对象就继续，并把缺口写成墙钟耗时函数/调用链未定位，见[RULING.md:128](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:128)、[同件:152](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:152)。因此不能指控它继续批准了“抓停滞瞬间”路线；它也没有根据现有材料否定一切未来采栈技术。
6. **权限是否越界：未发现当前越权。** [RULING.md:128](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:128)明确不批准A/C、候选采样代码或真机；[同件:155](D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md:155)禁止以当前关闭申请自动实施。可补强一句“将来任何侵入性采集仍须用户明示，资料齐备和Lead验收均不构成授权”，与本次任务第6项及[PENDING_DECISIONS.md:99](D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md:99)完全一致；这是授权措辞补强建议，不是已经越权的证据。

## 3. 本次实际数字抽查：命令和输出

以下两条命令均在本次复查执行，退出码均为0；只用标准库读取绝对路径JSON，没有导入harness或核验脚本。所有相关原始JSON均为单行文件，源位置均为各文件第1行。

**检查A：重建两处被引用的停顿值，并旁查v4c/w0。** 完整实际命令：

```bash
python -I -X utf8 -c 'import json; from pathlib import Path
root=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
for name in ("l3_20261031hb/measure_w1.json", "archive_T34/measure_w0.json", "l3_1101v4c/measure_w0.json"):
 p=root/name; d=json.loads(p.read_text(encoding="utf-8-sig")); t=d["samples"]["t"]; f=d["samples"]["f"]; s=d["stats"]
 start=t[0]; prev=f[0]; longest=0.0; changes=[]
 for ti,fi in zip(t[1:],f[1:]):
  if fi!=prev:
   longest=max(longest,ti-start); start=ti; prev=fi; changes.append((ti,fi))
 longest=max(longest,t[-1]-start); gaps=[b-a for a,b in zip(t,t[1:]) if b-a>0.010]; live=(f[-1]-f[0])/(changes[-1][0]-t[0])
 print(p.as_posix()); print(json.dumps({"nominal_span_s":d["span_s"],"samples":len(t),"raw_df":f[-1]-f[0],"stored_avg":s["fps_avg"],"raw_avg":(f[-1]-f[0])/(t[-1]-t[0]),"stored_p50":s["fps_p50"],"stored_max_stall_s":s["max_stall_s"],"raw_max_stall_s":round(longest,6),"dt_gt10ms_n":len(gaps),"dt_gt10ms_sum_s":sum(gaps),"first_to_last_edge_live_fps":live},ensure_ascii=False))'
```

实际stdout：

```text
D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_20261031hb/measure_w1.json
{"nominal_span_s": 25.0, "samples": 12471, "raw_df": 118, "stored_avg": 4.731722368997936, "raw_avg": 4.731722368996555, "stored_p50": 5.468718383922593, "stored_max_stall_s": 0.749879, "raw_max_stall_s": 0.749879, "dt_gt10ms_n": 259, "dt_gt10ms_sum_s": 14.33563099996536, "first_to_last_edge_live_fps": 4.7583931906268555}
D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T34/measure_w0.json
{"nominal_span_s": 25.0, "samples": 12502, "raw_df": 9, "stored_avg": 0.36000229681454066, "raw_avg": 0.36000230401468747, "stored_p50": 31.608659530882008, "stored_max_stall_s": 24.734761, "raw_max_stall_s": 24.73476, "dt_gt10ms_n": 0, "dt_gt10ms_sum_s": 0, "first_to_last_edge_live_fps": 33.95201448466241}
D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json
{"nominal_span_s": 25.0, "samples": 12501, "raw_df": 463, "stored_avg": 18.520948494813613, "raw_avg": 18.520949013419916, "stored_p50": 19.81123852234025, "stored_max_stall_s": 0.103742, "raw_max_stall_s": 0.103742, "dt_gt10ms_n": 0, "dt_gt10ms_sum_s": 0, "first_to_last_edge_live_fps": 18.539626790502314}
```

判定：裁决所引0.749879秒点位与T34约24.734760秒均符合原始样点；T34零>10ms缺口亦符合。hb/w1同时存在采样间隔异常，故**本次没有把它称为“零争用/采样器健康”**，也没有用一次样点重建判定其宿主原因。

**检查B：确认v4c三窗序列的字段身份。** 完整实际命令：

```bash
python -I -X utf8 -c 'import json; from pathlib import Path
root=Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c")
for window in range(3):
 p=root/("measure_w%d.json"%window); d=json.loads(p.read_text(encoding="utf-8-sig")); edges=d["frame_edges"]; live=(edges[-1][0]-edges[0][0])/(edges[-1][1]-edges[0][1]); s=d["stats"]
 print(json.dumps({"path":p.as_posix(),"stored_fps_avg":s["fps_avg"],"derived_live_fps":live,"has_stored_live_fps":("live_fps" in d or "live_fps" in s)},ensure_ascii=False))'
```

实际stdout：

```text
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json", "stored_fps_avg": 18.520948494813613, "derived_live_fps": 18.539626790502314, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json", "stored_fps_avg": 28.40179635682234, "derived_live_fps": 28.416096013424877, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json", "stored_fps_avg": 30.681571141892938, "derived_live_fps": 30.70530239738328, "has_stored_live_fps": false}
```

本次未重算104份全库、22窗整体覆盖率、1734段/87.7%、21/32图像覆盖；未新读PNG、未核截图时序/哈希，未做运行期实验或项目测试。关于这些全集结论，本件只评估裁决如何使用已给材料，不把材料记载或前一步FACTBASE检查计成本次重新通过。

**执行判据：补齐R1验收项、解决R2字段标注后，按原裁决限定的离线文档动作落实；D-15修正A与D-13暂停选择维持。目标①机制仍未闭合，任何未来侵入操作仍须用户明示。**

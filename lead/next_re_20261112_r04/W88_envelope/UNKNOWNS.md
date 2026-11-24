# W88 UNKNOWNS

> 卡：NEXT_RE_20261112_R04 · W88｜更新：2026-11-14T15:1x+08:00（Get-Date）

## U1【事故】trip_C1 目录复用覆盖 run.ndjson
- C1 第 2 趟（14:16）复用了 trip_C1 目录，覆盖第 1 趟（14:01 崩溃）的 run.ndjson。
- 幸存：崩侧 D1 归档（archived_except.txt 26,515 B / wer_events.txt /
  archived_ndjson_tail.ndjson / 终态截图）；第 2 趟 TRIP_RESULT（out 级
  TRIP_RESULT_C1.json）。第 1 趟逐拍 ndjson **永久丢失**。
- 整改：runner 目录唯一化（trip_<STEP>、_b、_c…）。

## U2【未证】地图内 `[NAPOWR] Crewed=no` 覆写是否被引擎采纳
- C4 唯一差异是该段；但 C1 失效本身间歇（1/3），故"单趟绿"无法区分
  "覆写生效"与"覆写被忽略+随机绿"。
- C4b 崩（1/3）说明**即使覆写生效，乘员抑制也不消除失效**；若覆写被忽略，
  C4≡C1，其 1/3 与 C1 同率亦自洽。两条解释路径在本卡证据下不可分离 [未证]。
- 后续判别建议：RE 卡静态确认场景 INI 是否进入 rules 数据库；或做一个
  "覆写可见副作用"探针（如 Strength=1 使建筑一击毁）。

## U3【事件】C3_c 首跑导航超时
- 14:52 一趟 BLOCKED：进场 240 s 超时（timeout_enter 截图在 trip_C3_c，
  TRIP_RESULT 记 BLOCKED）。非游戏崩溃。15:52（实际 14:53）重跑同后缀新目录
  成功（150.185 s 绿）。原因未定位（可能首跑与前一局 taskkill /F 后的资源竞争）。

## U4【事故·工具缺陷 D5】唯一化修复不完整导致 4 个趟的 ndjson 丢失
- 加后缀逻辑时残留旧 `TRIP_OUT = C.OUT / ("trip_" + STEP)` 行，把 TRIP_OUT
  指回旧目录：C3a/C3b/C4a/C4b 的 run.ndjson 被后续运行覆盖丢失。
- 幸存证据：out 级 TRIP_RESULT_C3.json（run a 绿）、TRIP_RESULT_C4.json（run a 绿）、
  TAG 唯一截图（run_C3_b_*、run_C4_b_* 等）；C4b 崩溃以干净重跑（trip_C4_b，
  完整 ndjson + D1）重新取得。
- 影响评估：k/N 计数不受影响（各趟终态均有独立证据），但 C3a/C4a 两趟缺逐拍
  ndjson，其"绿"的定量复算只有截图+TRIP_RESULT 级证据。已用 4 个干净唯一目录
  重跑补强（C3b/C3c/C4b/C4c）。

## U5【未证】0xA8E9A0 全局门控的语义
- 场景甲崩溃点的第一指令读 `[0xA8E9A0]`，为 0 时跳过整个遍历。本轮未观测其
  取值分布（只读监控未含该地址）。若其语义是"仅特定状态下才扫描"，可能解释
  间歇性（同一损坏链只在门控开启+走到该格时才崩）。

## U6【未证】引擎掉落 RA2F_M1.sav
- finalize 时沙箱多出 `RA2F_M1.sav`（PRE 基线无此文件）——某趟游戏写了任务存档
  （本卡从未点击保存）。已按 drop-cleanup 删除并在 FINALIZE.json 记录。
  写入时机/触发条件未定位（截图中无保存动作；可疑为 Alt+S 等全局键未被本卡
  发送过——真实原因未知）。

## U7【未证】重叠剂量-失效率关系
- 本卡只测了重叠"有/无"。6 座 NAPOWR 步长 3 与步长 4、以及 NACNST 4×4 与
  NAPOWR 3×2 的重叠格数差异未扫。W89 提到的"保留 NACNST 时共 14 格重叠"
  在本卡 C 臂（含 NACNST）同样存在。

# U2 —— STATE_MATRIX.json:2 condition 收紧（每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/STATE_MATRIX.json`（SHA256 = 1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016，3,558 字节，16 行/14 数据行——本轮实算实读）
- 行：**第 2 行**（数据行 1）

## 原文逐字（本轮 Read 实读 :2）
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后任意文件状态","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```

## 改后 condition 逐字（源件处方原文：pf2 §4.5:193；row5 §4.3-B:131 明写「pf2 §4.5 :193 文案原样」；两源同文）
```
pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）
```
拼装后整行（condition 值 = pf2:193 原文、该行其余键值不动——pf2:196「该行其余键值不动」；UNIFIED_TEXT_FIX.md 机械拼装示意逐字转录）：
```
  {"state":"unknown","preState":"unknown","condition":"pre=None / {} / 缺 state / 脏值（跑前快照未采集或采集未完成），跑后读取正常（post.read_error 为空）；post.read_error 非空时先落 post_read_error（码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行）","verdict":"unknown","confidence":"none","usableAsCrashEvidence":false},
```

## 出处
- 源①：`lead/v2_precision_fix_20261108/V2_PRECISION_FIX_PROPOSAL.md` §4.1-§4.6（判定 A §4.4:186；处方 §4.5:190-196；批准人 §4.6:200）。
- 源②：`lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md` §4.2-1（O3 分流兜底 :122）、§4.3-B:131。
- 上游既有登记：R3:47 / V2:132 / 重签件:89。
- 事实底座（row5 §3.1 本轮实读，转引）：read_error 出口候选 :4643-4646（:4642 注释「★ N1：错误独立出口，优先于一切状态折叠」）先于 unknown 出口 :4648-4651；设计同码 B2B_DESIGN.md:310-311。

## 需谁批准
**乙设计责任人**（pf2 §4.6:200「STATE_MATRIX.json 为乙矩阵，其定版主体为乙设计侧」；row5 §5.4-1:184）。改后乙矩阵指纹变 → V2:46 + 重签件 §2 第 5 行（:34）+ :153 生效条件 1。

## 依赖关系
- **与 U3/U4/U5/U6/U7 六处同批落盘**（P3，强制前提）——只改 JSON:2 不同步 :148 镜像 = 双源不一致且既定门禁抓不到（row5 §4.5-1:153）。
- **范围准冲突①（P1）**：pf2 最小修复口径 = 只动本行（+镜像 :148，row5:138「若采 A 必须同步 :148 镜像」）；row5 推荐选项 B = 本行 + U3 + U4 + 三镜像六处。执行前须决断。
- 码序注记冗余为源件有意设计（:2 只写「:4643 先于 :4648」，:5 写全链），非冲突（UNIFIED_TEXT_FIX §5.1）。

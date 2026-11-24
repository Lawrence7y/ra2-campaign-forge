# W177-F · DISAGREE（与审计/前卡的分歧与更正）

| # | 事项 | 本卡立场 | 依据 |
|---|---|---|---|
| D1 | W177-E "NAPOWR 相对光标 −2y 常数偏移" | **不采纳**。审计自算三次落点偏移 (−2,−2)/(−1,+1)/(−1,−1) 不一致，Δcell=(1,3)/Δscreen=(−55,28) 与等轴 1:2 预测矛盾。本卡 4 点过定：局部仿射残差 <0.2 格、无单一"−2y"常数 | `CALIBRATION.md` §2；a-W177-E `VERDICT.md` |
| D2 | "相机滚动污染是 targeting 失败主因" | **部分采纳**。本卡标定窗 cam=0,0 且视图稳定 ⇒ 相机不是该窗内误差源；但鼠标停 x=0 触发边缘滚屏确实污染 T2（视图/侧栏漂移）。因果顺序需分清 | `calibration.jsonl` cam 字段；`t2a_sidebar.png` |
| D3 | `0x47C620` 拒集 {6,0x24} | **更正为 {6 Building,0x24 Terrain,2 Aircraft}**（审计逐点定位 `0x47C668/7B3/825`、`0x47C694`、`0x47C723/7EA`）；15/1 仍一次未比较。本卡引用审计结论，未独立逐字节复验，故在 PROGRESS 标 [静态推断] | a-W177-E `VERDICT.md` |
| D4 | `0x47C620` 调用点数 | **更正为全镜像 10 个直接调用点**（非 2 个）；`0x43F2AE` 在 `0x43F180` 双层格循环内 `test al,al; je 0x43F504` 中止整次放置 | a-W177-E `VERDICT.md` |
| D5 | "链长≥2 全为纯 InfantryClass" | **更正**：W177-E try5 `(56,97)` 为 UnitClass + 2×InfantryClass（跨类共链），支持而非削弱"跨类共链"可行性 | a-W177-E `VERDICT.md` |
| D6 | 颜色判据（90px 盒绿 480–520） | **不采纳为特异判据**：审计实测无 ghost 基线同级 525/554、全图绿=0。本卡颜色只作候选粗过滤，落格以链回读 `result_cells` 为准 | a-W177-E `VERDICT.md`；本卡 `calib_place2.py`（green>1000 仅作候选门槛） |
| D7 | 高频采样"恒 0/零跳变"断言 | **删除**：改为 distinct-frame 自检（本卡 4 窗 62–64 帧）。审计指出 W177-E try5 24,507 样本同帧被误当有效窗 | `calib_p*_hifreq.jsonl` distinct-frame 复算 |

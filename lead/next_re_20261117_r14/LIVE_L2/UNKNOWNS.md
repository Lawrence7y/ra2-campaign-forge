# LIVE-L2 UNKNOWNS — 未证/存疑项

1. **ghost 在手 vs 建造中的内存区分**：`NAPOWR` 对象在「建造中」「建造完成待拾取」「已拾取 ghost 在手」三态下，`o1(+0x81)=1, o2(+0x74)=0, cell=(0,0), valid=false, layer(+0x94)=−1, canplace(+0x1AC)=115` 完全一致（ghost_sig_probe 实测）。本卡无法只用这些字段区分，改用 footprint≥3000（apparatus）确认；不影响主判据（落格后读链）。
   - 待证：是否存在某个全局「当前放置对象」指针（如 MapClass::CurrentlyPlacingItem）可作纯内存 ghost 信号；本卡未定位该地址。
2. **建造中 credit 语义**：credit 在下单后逐帧递减（约 40–55/s），约 15s 后稳定于 pre−600。仅用作「建造完成」仪表，未深究其精确字段含义。
3. **NAPOWR 占地尺寸**：拒绝 trial 的 footprint 红绿混合（如 A2/A5）推知占地>1 格；本卡未直接枚举 footprint 覆盖的 cell 集合。选取空地时以 ±2 格外扩规避。
4. **单位移动导致无效 trial**：B3 目标格 (109,63) 在扫描时有步兵、点击时 chain_before 已空（步兵移走），建筑成功落格。已按「有效 trial = 点击瞬间单位在格」过滤；未追查单位移动路径。
5. **不可达车辆格 (105,55)**：屏幕 y≈311 低于 SAFE 下界 400，闭环无法定位；未尝试缩放下界（避免边缘自动卷屏破坏 camera=0 卫哨）。故 C 组有效样本均来自 (105,59)/(113,59)/(113,63)。
6. **裸 mouse_event 不落地**：本环境直接 `u32.mouse_event(2/4)` 不触发放置（A_gate v1 全败根因之一）；改用 w177_click.click_client（SetCursorPos+WindowFromPoint verify+click）后稳定。未深究是前台/焦点还是注入语义。
7. **0x43F180/0x47C620 挂链 mode 参数**：沿用 LIVE-L1 未证状态；本卡只读全局 mode=5，未下断点（授权禁止 Hook）。

## 处置
以上均不触及主判据有效性：主判据只依赖「落格对象 + 落格格链 RTTI」，为纯内存只读；A 闸 4/6 达标即证其可用。

# S09-K1 UNKNOWNS — 未决项（本卡未能字节级坐实，不臆造）

1. **S09 UI 主类的实例尺寸（GetSize）未证**：SidebarClass/DisplayClass/MouseClass/TabClass/ScrollClass/RadarClass/PowerClass/SelectClass/SBGadgetClass/GadgetClass/CommandClass/WWMouseClass 的 slot12 均非 `B8 imm C3`（IGameMap COM 层次；共享复杂函数 0x4F4410/0x4E14C0/0x536000/0x7BA350）。按纪律 9「对不上报冲突 + [未证]，不要选一个看起来对的凑」，本卡不给这些类臆造尺寸。后续若需尺寸，应走「构造器分配点 push imm + call operator new」逐类取证（本卡已对 Tactical 示范），并查多级继承的 size 累加。
2. **DisplayClass 字段语义多为 [静态推断]**：+0x11CF/+0x11D0/+0x11B3 的写值（0/1/al）与读点已坐实，但"DraggingRectangle"等语义名来自 clue doc（sidebar_selection_ui.md）+ S09-F1，本卡未在字节层独立证明该布尔与框选行为的因果（须真机或更长的控制流追踪，静态卡不做）。+0x11A8 读写点足（W=9/R≥3）但语义未坐实 → [未证]。
3. **61 个 .rdata 之外的 vtable→COL 映射**：全节扫描得 1275 个 vtable→COL，其中 .rdata 1214（主表），余 61 落在 .data/.text（次级/接口 vtable，this 调整）。本卡槽数统计只覆盖 1214 主表（对账审计基线）；这 61 个次级表未逐一取证。
4. **ShapeButtonClass vtable 0x45CC44（在 .text，slots=None）**：其 COL 存在但 vtable 落在 `.text` 段，本卡的 `.rdata` 定界器不适用 → 槽数未定。不影响 1214/14,044 基线（该表不在 .rdata 主表集）。
5. **CommandClass 父类**：CHD 的 BaseClassArray 仅 1 项（自身），未读出父类名；本卡记为根，不断言其上是否有未捕获接口。
6. **B8 imm C3 基线口径差异**：本卡严格口径 638（要求 `mov eax,imm32` 5 字节 + 紧接 `C3`），审计 §969 记 837；差异来自过滤宽严，方向一致（均证明判据不特异）。本卡不引用 837 作为自己的分母。
7. **未跑真机**：本卡为静态卡；S09 的运行时点击/事件行为仍以 S09-F1 与真机线为准，本卡只做字节布局地基。

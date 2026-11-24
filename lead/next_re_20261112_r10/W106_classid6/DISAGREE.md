# W106 · 与既有记录的分歧

1. **对 R09 底座 §629-2"镜像无 RTTI"**：`[已证·部分推翻]`。gamemd.exe 的 .data 段存在成片 MSVC RTTI TypeDescriptor（`0x818C20=".?AVBombClass@@"`、`0x818C38=".?AVNeuronClass@@"`、`0x818C58=".?AVBrainClass@@"`、`0x818D68=".?AVBuildingClass@@"`、`0x825508=".?AVInfantryClass@@"` 等），且主要实例类虚表带完整 COL/CHD/BCA 链（本卡走通 BuildingClass 与 InfantryClass 两条）。"无 RTTI"的说法应改为"**RTTI 存在但 Westwood 另有一套 COM 风格 IRTTITypeInfo 体系**；二者并存"。产出：`EVIDENCE\rtti_names.txt`、`EVIDENCE\col_tda_proof.txt`。
2. **对台账 §623-ERR-3**：R09 L2-3 曾指出"`0x51BF90 = InfantryClass::IsCellOccupied 由 RTTI 定"与"无 RTTI"必有一错。本卡证明：**前者反而是对的**——虚表 `0x7EB058` 的 COL 指向 `".?AVInfantryClass@@"`，故槽 107 `0x51BF90` 归属 InfantryClass 现在有 RTTI 链背书；错的只是"镜像无 RTTI"那句。
3. **对 R09 L5 的方法论教训**：补充正例——"字节流搜常量"在 **.rdata 数据结构**（非指令）上依然可靠且高效（本卡 COL/BCD 链全部由原始字节解出并交叉验证）；L5 的告诫只适用于"在 .text 指令流里搜 imm32"的场景。
4. **对 Lead 卡面提示"RA2 镜像无 RTTI ⇒ 类名需反推"**：结论方向不变（类 6 确实解出来了），但后续卡可直接用 `vt[-1] → COL → TD+8 → .?AV名` 这条捷径，成本 ≈ 字节级 5 分钟，无需 Ghidra 全量分析。

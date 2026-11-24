# SURVEY-D39 UNKNOWNS / 方法边界

1. **C1 的 120 行 = direct-call 77 行 + exact-virtual-dispatch 43 行，二者无重叠。** 按卡面 C1 判据（环④形态）分类；对占位名行（如 `Class::slotN`）不再二次裁定 ③ 是否已具名，因为 D-39 问题只要求量化环④形态。若用户裁决要求 C1 也必须有具名语义，则 C1 会显著缩小，需重跑，不能从本表直接外推。
2. **C2 的 99 行**均满足：RTTI 链 FROM `vt-4=COL → COL+0xC=TD → TD+8 内联名串` 可解、有活 vptr 安装或 vt imm32 引用、direct call=0、exact dispatch=0，且 ③ 由强字节合同支撑（vector 族 slot1–6 或 scalar deleting dtor）。
3. **Vtable 基址识别**：扫描非 `.text` 节 4 字节对齐 dword；命中地址若不是表基址，向前最多回溯 256 个槽找到带 RTTI 的 COL 边界。超过该回溯范围的表会被判 C3（本卡未见需要人工扩范围的证据）。
4. **Exact dispatch 判据**：只识别 `mov reg,[global]` + `mov ecx,global` + `call [reg+slot]` 且 global 有 `mov [global],vt` 安装、`vt[slot]==entry`。稀有等价形态未枚举，故 exact 命中是保守下界；遗漏会落到 C2/C3，不会虚增 C1。
5. **体内合同判据**按 R14_COMMON §8.4 的 vector 族 slot→method 映射并加强字节形态：Clear/FindItemIndex/GetItemIndex/GetItem/operator==/SetCapacity。非 vector 族的 `slotN`/`vslotN` 仍按占位名归入 C4，未凭槽号猜名（守 ⑳/㉑）。
6. **C2 基线 15/100=15%** 表明「有活安装 + direct call=0」单独并不强；本卡 C2 不是仅凭该基线判定，还叠加 RTTI 与体内合同。数字只给一个 seed 一次抽样，按要求不给多 seed 富集表。
7. **K8/K10 61 地址**已按两份审计的 18+43 逐 address 收集；C2 抽样避开它们，计数本身未排除（否则会改变问题的全量规模）。
8. 未改目标文件、coverage、grade、subsystem；未生成 `coverage_delta.tsv`。

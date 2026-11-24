# W164 DISAGREE（与既有结论 / Lead 预期不符之处）

格式："我预期 X，实测 Y，因此 X 错"。

## D1 · Locomotion 每帧更新槽：预期 `+0x5C`，实测 `+0x40`
- **派发提示词 Q1 预设**："移动到 `LocomotionClass` 的哪个槽"，并提到"把 `Drive/Walk/...` 的 `[vtbl+0x5C]`（或对应的每帧更新槽）解析出来，说明哪些是真正的每帧驱动"。
- **实测**：Locomotion offset=4 子表 `+0x5C` = `0x55A910`（多数类），反汇编 `mov eax,[esp+4]; ...; ret 4` = stdcall 1 栈参的状态位设置器，**不是每帧驱动**；真正的每帧 Process wrapper 在**槽16 `+0x40`**（Drive→`0x4B0500`→大 Process `0x4B2630`→`0x4D3920`）。证据：`check_off4_process.py`、`rdata_bytescan.py`、capstone `0x55A910` 字节。
- **因此**：若把 Locomotion `+0x5C` 当每帧驱动，会得出错误结论。AI 层的 `[vptr+0x5C]`（ObjectClass::AI 槽）是对的，但 Locomotion 的更新槽号不同，不能混用。

## D2 · offset=4 子表槽数：台账 49，实测 50
- **预期**：R11_COMMON §3.1 "LocomotionClass offset=4 子表 49 槽"。
- **实测**：用 COL 指针（`vftable[-4]==col`）判定边界，off=4 子表从 vt 到下一张表的 COL 指针共 50 个 dword，最后一项（`vt+0xC4`）仍是 `.text` 合法函数指针。12 个 Locomotion 类全部 50 槽。证据：`loco_vtable_bounds.txt`。
- **因此**：台账"49 槽"口径偏 1（可能用了不同的终止规则）。不影响本卡结论（更新槽 +0x40 与 +0x5C 都在 50 槽内）。

## D3 · `MaxUnitCount=10` 不是运行期单位上限
- **预期**：看到 Rules 有 `MaxUnitCount` 可能以为是对象数硬上限。
- **实测**：`RULESMD_expandmd01.INI:2997` 注释 "maximum number of starting units. (def=20)"，`:3024 MaxUnitCount=10`；台账 §189 真机 "引擎无上限实锤"（units0 达 961/1212）。
- **因此**：不能用 `MaxUnitCount` 论证 1500 MTNK 进不了 `AbstractClass::Array`。

## D4 · 数量级判别：预期上界能排除其一，实测不能
- **预期**（Lead 派发的隐含预期）："用单对象每帧移动代价静态上界去判哪个数量级才可能"。
- **实测**：单对象上界（1 次满 SearchCore = 544×65527 ≈ 3.56×10⁷ 指令 = 11.9–71 ms）**同时包容 67 µs（N=1500）与 1.47 ms（N=69）**。上界不能排除任何一个数量级。
- **因此**：这一问的诚实答案是"**静态不可判**"，不能强行给出一个 N。必须由真机采 N（§14.3）才能分离。

## D5 · 与派发提示词背景的一致性说明（非真 DISAGREE，但需 Lead 知悉）
- 提示词背景称 `0x55B610` 循环"无 +0x98 门"，与 R12_FACTS §6.1 "`+0x98`=在册标志，AI 派发用 `[obj+0x98]==0 then skip`" 表面矛盾。实测 §10.2（更晚、更权威）明确 `0x55B608` 循环**无 +0x98 门**；`+0x98` 门在别处（入册/注销 0x55BAA0/0x55BAE0）。本卡采 §10.2。FootClass::AI 内另有一个 `[obj+0x90]` 总门（本卡新发现），与 +0x98 不同。

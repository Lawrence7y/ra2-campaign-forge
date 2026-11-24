# W160 DISAGREE（与 Lead 前提 / 既有结论不符）

1. **Lead 中途更正前提（任务进行中）**：开局提示词把"没找到每 tick ObjectClass AI 派发"当事实要我证伪；随后 Lead 发消息自我推翻（LogicClass 向量循环在 `0x55AFB0` 内）。本卡已按新前提重做；报告如实记录。[已证] 新前提成立。
2. **原 §891-4/§891-5/§896 的"遍历对象数组并调 AI 的可达代码尚未找到"是错的**：`0x55AFB0` 第 4 个槽-0x5C 循环遍历 `this=0x87F778` 的 `VectorClass<ObjectClass*>` 并逐元素调槽 0x5C。[已证] 依据：栈帧算术 + Ghidra 反编译 `param_1+0x10/+4` + 构造器 vptr `0x7E18FC→0x7E192C`。
3. **Lead 表中 `[edi+4]/[edi+0x10]` 标成"DynamicVectorClass 参数"错**：它就是 `this` 的成员 `LogicClass` 继承的 `VectorClass<ObjectClass*>`。[已证]
4. **原清单里"原始 `FF 5x 5C` 命中 164、边界假阳性 2、有效 162"**：我独立字节普查得到 **原始 166**（含 2 个 SIB `FF 54 24 5C`），**全节线性边界全部 166 成立**；后与 Lead 对账确认口径：162=普通寄存器子集、164=有效总数（162+2 SIB）、166=原始操作数命中（含 2 个位于 atlas 函数空洞的普通寄存器站点，`0x617641/0x61CC5C`，从 12 个已知函数入口线性反汇编也精确落边界）。**这不是数值分歧，是口径/覆盖差异**；我在报告中用 166/164/162 三口径并标注。
5. **`0x617641/0x61CC5C` 不是"假阳性"**：原始字节 `ff 52 5c`；从 `0x60CF00` 等 12 个 atlas 入口线性反汇编都在该地址精确解码为 `call [edx+0x5C]`。它们只是落在 `function_atlas.tsv` 的 entry+size 之外（Ghidra `getFunctionContaining=NONE`）。§6.2 的"函数空洞"陷阱在这里再次命中。[已证]

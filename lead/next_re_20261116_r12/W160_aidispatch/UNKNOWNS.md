# W160 UNKNOWNS / 未证清单

- `[未证]` `0x87F778` (`LogicClass` 的 `VectorClass<ObjectClass*>`) 在**运行期**是否真的包含全部 ObjectClass 子类（含 Bullet/Anim）。静态可证：构造器把 vptr 设为 `LogicClass`→析构改为 `VectorClass<ObjectClass*>`；`0x55BAA0`/`0x55BAE0` 是注册/注销入口并有 7+ 处调用者；21 处代码以 `0x87F778` 为 `this` 遍历/查询。缺的是在 `[0xA8ED84]` 推进期间把该向量的 Items 按 vtable 逐一点名并与 `AbstractClass::Array` 对账（R12 真机卡范围，本卡禁止真机）。
- `[未证]` `0x55B8F0` 11 路阶梯的"旧版/被取代"定性。静态已证零引用/零入口点字面量；W159 真机 0 命中（只能读台账 §896，不能本卡重做）。无法排除运行期计算出的入口地址（例如 `imm + delta`）到达；要定案需一次性断点或插桩。
- `[未证]` 若 AI 内部向 `0x87F778` 的向量增删对象，`0x55B610` 每次重读 Count 会吞掉增删而可能漏调或重复调用；静态没有证明任何 `AI` 实现会这么做。要证需对 5 个 `AI` 入口逐一检查是否调用 `0x55BAA0`/`0x55BAE0` 或 vector 写。
- `[未证]` `0x887324` 的精确单例身份。已证 `0x55B667` 对 `*[0x887324]` 单对象调槽 0x5C；`0x55D841`/`0x55E269`/`0x6485CD` 也把 `*[0x887324]` 当 ObjectClass 用。constructor 未在本次有限窗口内定位（461 处引用多为读取）。不能凭名字猜"某 Manager"。
- `[未证]` Ghidra 通道报 141 个 `call [reg+0x5C]` / 92 函数，与字节通道 166 / 101 不一致。原因可证：`getFunctionContaining` 对 `0x617641/0x61CC5C/0x55B8F0` 等无人引用区返回 NONE；Ghidra `getInstructions(executeSet)` 也没有覆盖全部真实指令。Ghidra 只作旁证/反编译，穷举数字以全节字节通道为准。

# W157 DISAGREE（与既有结论 / Lead 预期不符之处）

格式："我预期 X，实测 Y，因此 X 错"。

1. **与 §882-5 / §873 / R11_COMMON §3.4 的核心定性不符（本卡主判决）**
   - 我预期（台账）：`0x67D300` 是"依次驱动 House/Unit/Infantry/Building/Aircraft/Anim/Trigger 七个子系统单例的每帧协调器"，是每帧主要候选。
   - 实测：Ghidra 反编译为 `IStream::Write` + `QueryInterface(IID_IPersistStream)` + `OleSaveToStream` + `Release`；IAT `0x7E15F4=OleSaveToStream`；父函数 `0x67CEF0` 用 `StgCreateDocfile`/`CreateStream("CONTENTS")`；字符串 `SAVING GAME [%s] - Complete.`；唯一调用点在 `[0xA8B238]==0` + `[0xABCE08]` 一次性标志门控的存档分支内。
   - 因此：**"每帧协调器"定性错**，`0x67D300` 是存档序列化器，正常游戏不每帧执行。§881-4 对开头字节的"驱动单例"语义解读也是误读（那些 call 是写存档头）。

2. **与 W151 `fn_67cef0_bulletloop.log` 的函数归属不符**
   - 我预期（W151 EVIDENCE 标注）：`0x67CC30..0x67CCB0` 的"遍历 House/Bullet 调 `[edx+0x34]`"循环属于 `0x67CEF0`（用于支撑"槽 13 = 0x5F6250"）。
   - 实测：Ghidra `getFunctionContaining(0x67CC30) = NULL`（落在函数间隙）；`0x67CEF0` 精确范围 `0x67CEF0..0x67D2FF`（size=1040，BACKEDGE=0），其反汇编无该循环。
   - 因此：**W151 该 EVIDENCE 的函数标注错**（那段循环属于别的函数）。本卡据此把"槽 13"具体编号降为 [未证]，但"0x5F6250 是逐字段序列化器"仍由 `0x5F6250` 自身反汇编 + 8 个 vtable 引用独立证实。

3. **与 W151 措辞的轻微不一致（非方向性）**
   - 我预期（W151 §889-6 转引）：`0x5F6250` 是"槽 13 逐字段序列化器"，由 `0x67CEF0` 调用。
   - 实测：`0x5F6250` 确实是逐字段序列化器（方向正确），但本卡在 `0x67CEF0` 的 24 个 callee 中**未见**对 `0x5F6250` 的直接调用（`0x67CEF0` 的调用是经 `0x681040`/`0x6811c0` 等序列化框架函数间接发生；`0x5F6250` 的 6 处直接 CALL 来自 `0x5B3979/0x425419/0x436F49/0x63010A/0x71CF59/0x74AA39`，均不在 0x67CEF0）。
   - 因此："在 0x67CEF0 调槽 13 = 0x5F6250"这一具体调用路径描述**不成立**；W151 的核心定性（COM 序列化链）成立。

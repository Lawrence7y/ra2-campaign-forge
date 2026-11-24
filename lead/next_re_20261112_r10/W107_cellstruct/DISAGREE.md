# W107 DISAGREE

1. 台账 §629-2「镜像无 RTTI」—— Lead 本轮已亲证为错（.data 有 962 个类型描述符）。本轮报告按"有 RTTI"口径写，并用了 vt2name。`lead\GOAL_THREE_TARGETS_20261018.md` 未改（append-only 归 Lead）。
2. Lead 起点表称 `+0x140` 为「标志位（test ah,1）」—— 复核成立，且补充了写侧证据 `47DA88: OR dword ptr [ESI+0x140],0x20000`，支持"位域"而非单 bool。
3. Lead 起点表 `+0x11B` 标「未定」—— 本轮升级为 [已证]：FUN_0047d2b0 内 20+ 处 MOVSX（有符号语义），另 FUN_0047ec90 亦读；仍不知语义。
4. 方法差异：Lead 建议"对参数用在 +0xE4 的函数群做 Ghidra Reference/Data 流枚举"；实际用反编译文本溯源（等价但更快，且能区分 cell/对象侧），首次运行因参数种子取自 getParameters() 失败导致空表，改从签名行解析后修复——过程记录在 headless_run1.log / run2.log。

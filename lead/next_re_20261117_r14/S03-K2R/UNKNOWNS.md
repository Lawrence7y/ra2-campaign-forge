# S03-K2R · UNKNOWNS.md

| # | 未定项 | 现状 | 下一步 |
|---|---|---|---|
| U1 | BufferIOFileClass 是否存在未被当前三形式规则捕获的独立分配点 | 全镜像 `push imm8/imm32 -> call 0x7C8E17`、`mov reg,imm -> call new`、ctor-as-argument 上下各一层均 0；按纪律写 **未找到**，不得写「不存在」 | 若有新等价形式（间接 new 指针/构造工厂），须双通道重扫 |
| U2 | CDFileClass 是否参与 GetSize 5 类口径 | 上轮 5 类集合含 CC/Mix/3 内嵌基类；CD 两个 ctor 候选均 **未找到**独立分配点，本卡不擅自并入分母 | 请 Lead 明确 5 类名单；当前按 VERDICT 3/5 |
| U3 | RawFile +0x20 读点语义（byte vs bool） | 4W/3R 字节级复现；名字/语义未超出字段偏移证据 | 追 0x65CA3D/0x65D3DD 的下游分支 |
| U4 | 加密 MIX 分组层逐字节 dump | 与上轮一致：常量/字符串已证，Blowfish 分组流程未逐条 dump | 只读追 0x633050 PKStraw |

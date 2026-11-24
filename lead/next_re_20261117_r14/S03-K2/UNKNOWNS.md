# S03-K2 · UNKNOWNS.md

| # | 未定项 | 现状 | 下一步 |
|---|---|---|---|
| U1 | 加密 MIX 的分组层逐字节 dump | flags.bit1 密钥入口 `0x5B3D0E`/PKStraw `0x633110`/`0x6330C0`/RSA e=`0x10001`@`0x52A6AF`/`blowfish.dll`@`0x840A78` 已实证，**但 Blowfish 分组解读流程未逐条 dump** ⇒ 加密档 body 的解密链只 `[静态推断]` | 找 `0x633050` PKStraw 完整函数，逐指令追 Blowfish 调用参数；只读档内校验 |
| U2 | LZO 压缩的具体条目级算法 | RTTI `LZOPipe@@`/`LZOStraw@@`@`0x82A00C` + 字符串已证 LZO 存在；哪个 MIX/哪类资源用 LZO、窗口参数、解压例程入口未定 | 从 `LZOStraw` vtable 槽找解压函数，对照一个 `.SHP/.TXT` 压缩条目 |
| U3 | 3 个内嵌基类（BufferIO/RawFile/CDFile）的独立对象大小 | 无独立 `push size; call new` 堆分配点（均内嵌于 CCFile 等）；无 `B8 imm32 C3` GetSize 槽 ⇒ GetSize 不闭合（闭合 2/5） | 若需独立 size，做完整 ctor 写点 disp+width 上界 + 派生类 0x6C 约束，但仍属弱对账 |
| U4 | MIX 链表注册顺序的实际首元素 | 链表头 `[0xABEFE0]`、`ebp=[ebp+4]` FIFO 已证；但「哪个 MIX 先注册」（Bootstrap `0x5301A0` 写链细节）本卡未逐条 dump ⇒ 只报「先注册先查」结构，不报具体档名顺序 | dump `0x5301A0` 全函数，追 `mov [0xABEFE0]`/`mov [reg+4]` 写点 |
| U5 | 派卡基线 proved=11（5.67%）与盘面/PANEL=18（9.28%）不符 | 卡面 §2 写 11/5.67%，但 `PANEL.md` 与 `TARGETS.tsv` 实算均为 18/9.28% ⇒ 卡面系旧截面（纪律 9 停机项，未凑数） | 见 DISAGREE D1；以盘上现值 18 为准 |
| U6 | 无 `expendmd98.mix` 等第三方档的官方 hash 基准 | K1 曾用第三方 zlib 档误判「标准 CRC32」，本卡以官方 `langmd.mix` 8/8 纠正；第三方档 id 由 zlib 生成，引擎算得不同值（游戏找不到） | 无（已定性：第三方产物，不可作基准） |

D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R16-SLOT73-SEM

## Q1 · 0x6F4A70 身份核验
- 结论：是函数入口；thiscall（带 1 个栈参数）；不是构造器/未见装 vtable。
- 入口锚点：0x6F4A62 为 5E、0x6F4A63 为 C3（前一函数 pop esi; ret），随后 0x6F4A64..0x6F4A6F 为 12 个 90，函数从 0x6F4A70 起步。字节见 byte_checks.tsv 的 anchor_6F4A60_6F4A6F。
- 入口字节：8B 44 24 04 56 8B F1 50 E8 D3 0D F0 FF ...；0x6F4A75 8B F1 为 mov esi,ecx，以 ecx 为 this；0x6F4A70 8B 44 24 04 读第 1 个栈参数。
- 收尾：两条 C2 04 00（0x6F4A9A、0x6F4AA0），即 ret 4，与 1 个栈参数一致；0x6F4AA3 起为 90 填充。
- 装表检查：函数体 0x6F4A70..0x6F4AA2 内没有写 [this]/[esi] 为 vtable 的指令；只有 0x6F4A8B 8B 16 为 mov edx,[esi] 读取 vptr。因此按字节不是构造器。

## Q2 · vtable 出现次数
- TechnoClass 主 vtable 0x7F4960（309 槽）：0x6F4A70 出现 1 次，槽号 73，槽地址 0x7F4A84，value=0x6F4A70。
- BuildingClass 主 vtable 0x7E3EBC（322 槽）：0x6F4A70 出现 0 次；其 #73 槽 0x7E3FE0 = 0x43F180。
- 明细见 vtable_hits.tsv。

## Q3 · 覆写关系与调用形式
- 字节链（锚点对齐后）：0x43F5D5 C2 04 00 后，0x43F5D8 53 为 push ebx（对应 ret 4 的栈参数），0x43F5D9 8B CF 为 mov ecx,edi，0x43F5DB E8 90 54 2B 00 为直接 call 0x6F4A70（rel32 计算目标 0x6F4A70）。这是直接 call，不是 call [reg+..] 虚派发。
- edi 来源：0x43F191 8B F9 为 mov edi,ecx（函数入口 this）；0x43F193 55、0x43F194 89 7C 24 34 后 0x43F198 E8 D3 58 2B 00 也直接 call 0x6F4A70，此时 ecx 仍为入口 this。这支持 edi 承载本对象。
- 同一对象判定：强推断，未取得全区间字节证实。允许的锚定窗口证明了入口 ecx 到 edi 与调用点 edi 到 ecx，但按有界约束未反汇编 0x43F198..0x43F5D8 全段，不能字节级排除中间对 edi 的改写。
- 整体判定：BuildingClass 槽 73 覆写为 0x43F180，并在其体内显式调用 TechnoClass 槽 73 实现 0x6F4A70 —— 推断（非字节证实）。其中两张表槽位不同与 E8 直接调用是字节事实；同一 this 贯穿与基类语义关系依赖前提和强推断，不升级为字节证实。

## Q4 · 身份与语义边界
- 身份（字节）：0x6F4A70 是 TechnoClass 主 vtable #73 指向的函数入口，thiscall，非装表构造器。
- 可字节证实的函数体事实：
  - 读栈参数 [esp+4]，读入 eax；ecx 到 esi。
  - 0x6F4A78 直接调用 0x5F5850，测试 al。
  - 若 al 为真：0x6F4A81 读 byte [esi+0x418]；若该字节非零，0x6F4A8B 读 edx=[esi]（vptr），0x6F4A8D push 0x0D，0x6F4A8F mov ecx,esi，0x6F4A91 call dword ptr [edx+0x274]（虚调用）。
  - 返回 al（1/0），ret 4。
  - 函数体 0x6F4A70..0x6F4AA2 未见字符串地址引用或压栈。
- 功能语义：未取得。不把读 +0x418 标志、直接调用 0x5F5850、以 0xD 触发 vptr+0x274 升级为命名行为。
- 若必须标注推断强度：弱推断（仅形态），像一个带标志门控的布尔判定或通知路径；不命名、不断言。

## 产物与边界
- REPORT.md、vtable_hits.tsv、byte_checks.tsv、work.py、DIS_*.txt 均只写本目录。
- 反汇编仅取锚定后的 0x6F4A70 函数体、0x43F5D8 拒绝块邻域（前一指令 ret 4 之后起步）与必要 vtable 槽；未建进程、未调试、未启动 gamemd。

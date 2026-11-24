# S18-K2 · UNKNOWNS.md —— 未闭环项（如实登记，不凑数）

| # | 未知项 | 现状 | 卡面要求对应 | 建议下一步 |
|---|---|---|---|---|
| U1 | 卡面 atlas **660** vs 盘上 **659** | 盘上 `coverage∩atlas` 实算 659；PANEL.md L50 亦 659。卡面 660/75.15%/8.03% 系用错分母（496/660=75.15%、53/660=8.03%）。本卡用 659，未凑。 | T1 统计 / 纪律 9 | Lead 更正派卡数字；审计复核 659 |
| U2 | 「46 项逐项落地」口径 | F1 入账 46=EventType 跳表项；卡面措辞「在 CRC 串里的偏移」疑似想要 46 个 CRC 字段，但帧 CRC 每对象仅 ~4–6 字段，无 46 字段结构。本卡两义均落地（CRC.md §3.1/§3.2/§3.3）。 | T3 CRC 46 项 | Lead 澄清「46 项」确切所指 |
| U3 | 网络 EventClass 无独立 RTTI TD | 988 TD 中无 `.?AVEventClass@@`，仅指针容器 TD；「111B≡EventClass」为 `[静态推断]`。 | T2 RTTI 定名 | 若要彻底定名须类名 RTTI 直接证据（本镜像无）→ 保持 fail-closed |
| U4 | helper `0x4C93D0` 字段物理语义 | 读 `obj+0x388/+0x3A0` 结构（word@0/4, dword@8/0x10, word@0x14 + CurrentFrame 插值），位级读点已证，但字段是速度/朝向/血量档未定（`docs/re/net_sync_checksum.md §7.1` 同）。 | T2 字段语义 | 对照 TechnoClass/LocomotionClass 布局定点复核 |
| U5 | 帧 CRC term 精确拼装位序 | `÷10`(imul 0x66666667) 与 `<<0x10`、`>>7;inc;>>1;and0xFF` 均已证；但 Infantry 与 Unit 两处寄存器分配不同，+0xA4/helper 谁进高/低 16 位为 `[静态推断]`。 | T3 CRC 算法 | 逐寄存器数据流 IronPython 追踪两处 term 组装 |
| U6 | CalculateChecksum 331 处 Add 调用未逐类穷举 | 本卡验 `0x4A1C10` 核心+表 256/256；各 `*::v[13]` 的 331 处 `0x4A1CA0` 直呼未逐类展开（doc §3.1 线索）。 | T3 存档校验 46 项 | 另立卡逐类落地 v[13] Add 序列 |
| U7 | 每帧 RNG 数字 `0xAFA26C` 消费者 | `0x650A90` 关 ExtraSyncInfo 时 `0xAFA26C=Random()`；该值的下游用途未展开。 | T4 联机 | `[未证]`，不展开协议 |
| U8 | 「等待所有玩家」类函数 | 字符串 `0x82CBB8 "Waiting for 'GO' response."`(xref `0x5BB031`)、`0x82C67C "Timeout! %d ticks since last incoming message"`(xref `0x5B6608`/`0x5BA528`)、`Frame sync stalls: %d`(xref `0x48E215`/`0x64E18F`/`0x6519EA`) 已定位调用点；协议细节按卡面要求不展开。 | T4 同步/联机 | 只标 `[已证]` 调用点，协议 `[未证]` |
| U9 | 5 个 no-op EventType 全空验证 | `0x4C8109` 入口到 ret 逐条打完（F1 VERDICT §6）；本卡跳表前驱核 46/46 全在边界。5 个 no-op 列于 CRC.md §3.1。 | T3 执行 | 已闭环（本卡+前序卡） |

## 纪律自检（本卡落实）
1. **基线**：卡面 660/75.15%/8.03% 未作分母——先实测盘上 659 并记 U1/DISAGREE（纪律 9 派卡口径警告）。
2. **RTTI fail-closed**：无 `.?AVEventClass@@` 即停，不编名；容器类型经 `COL+0xC→TD+8` 实测（纪律 5 / 坑 ⑧）。
3. **双通道不同源**：本卡唯一通道 = 自写 pefile+capstone（不依赖 atlas）；RTTI 自建全镜像扫描（988 TD）与 CRC 表 256/256 逐项复算为**独立字节自证**，不冒称"第二解码器通道"。
4. **字段偏移≠语义**：所有字段给写者+读者双点（CRC.md §2/LAYOUT.md §2），未仅凭偏移断言语义（纪律 4/19）。
5. **槽号不假定**：EventClass 无虚表，GetSize 用三腿（分配 imm/拷贝体长/容器步长），不假定槽 12（§981）。
6. **站点归属用区间包含**：call 站点（0x64731C 等）明确标为"调用点"非函数入口，未混入 delta。
7. **调用点数≠调用者函数数**：帧 CRC 2 调用点、分派 2 调用点分别标注。
8. **写值逐字符核对**：CRC `rol1=shr1f+lea[eax+edx*2]+add` 逐条核对（未误抄为 xor）。
9. **不联网/不真机/不改游戏文件/不写台账/git commit**：全程遵守。

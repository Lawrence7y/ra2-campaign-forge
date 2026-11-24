# 11 处 bit0=0 直接写点逐个分类（D1 关键收口）
> 集合 = t3_u3_bit0_counts.py 的 "imm with bit0=0" 11 处；证据 EVIDENCE/t3_u3_bit0_counts.txt、p2_classify11.txt、p3_focused.txt、p4_rtti.txt、p5_vtables.txt、p6_verify.txt。
> 停机核验：卡面「直接写 0 共 11 处」是 bit0=0 集合的简称；逐字节核对，**只有 5 处 imm 恰为 0，另 6 处为 2 / 0x42 / 0x62 / 0x48 / 0x70 / 0x64（bit0=0 但非零）**。不凑数，已写入 UNKNOWNS.md。
> 站点归属用「函数区间包含」（prologue..ret 括住），不用 entry_at_or_before。

| # | 站点 | 所在函数（区间包含） | reg 指向对象族（this 来源 + RTTI / fail-closed） | 语义候选 | 能否命中「已放置、待判步兵」 |
|---|------|--------------------|------------------------------------------------|----------|------------------------------|
| 1 | 0x4CCA64 | 0x4CCA20 [0x4CCA20,0x4CCA6E) | ebx=`arg1`（push ebx; mov ebx,[esp+8]），非 this；该函数占 vtable slot 0x7E8A00，cluster COL 0x800658→TD 0x8223E8→`.?AVFlyLocomotionClass@@`。被查询对象 edi=arg2 有 type==2 与 [edi+0x6C4] (InfantryClass 字段)。RTTI 只定函数所属类，ebx 精确类 fail-closed | 查询结果布尔回写：`[out]+0x14 = (arg2 是 type2 且 [arg2+0x6C4]+0xE0D 置位)`；写目标是 **out 参数**，非被查询步兵 | **不能**：write 目标 ebx 是 out-holder，步兵是 edi；函数内从未对 edi+0x14 写入 |
| 2 | 0x5C0247 | 0x5C0240 [0x5C0240,0x5C026F) | esi=ecx(this)；紧接着 `mov [esi],0x7EE0F4` 设 vtable → COL 0x805FA0→TD 0x82DA40→`.?AVVQMovieHandle@@` | **构造器默认初始化**（新对象 +0x14=0） | **不能**：写入即设 vtable 的新建对象，VQMovieHandle 非 InfantryClass |
| 3 | 0x5C0920 | 0x5C07D0 [0x5C07D0,0x5C0960) | esi=operator new(0x18)@0x7C8E17 返回值；同样 `mov [esi],0x7EE0F4` → `.?AVVQMovieHandle@@` | **构造器默认初始化**，由 0x5BF189 等传入源数据复制 | **不能**：刚分配的新对象；vtable 0x7EE0F4 ≠ InfantryClass vtables (0x7EB058/03C/034/02C) |
| 4 | 0x76AB55 | 0x76AAF0 [0x76AAF0,0x76AB81) | eax=ecx(this)；调用者 0x76AAC4 前 `push 0x40; call 0x7C8E17` → **0x40 字节新对象**。RTTI fail-closed | 字面值 **2**（非 0）；小对象批量字段初始化 | **不能**：0x40 字节 ≪ InfantryClass 0x6F0（工厂 0x6C38BC `push 0x6f0`）；新分配，非在册步兵 |
| 5 | 0x77A74D | 0x77A700 [0x77A700,0x77A75E) | ecx=this（thiscall ret 8）；5 个直接调用者传 ecx = `lea [esp+0x10]`/`[esp+0x24]`/全局 0xB75E4C 等**小状态对象**；对象仅 +8/+0x10/+0x14/+0x18 四字段。RTTI fail-closed（无 vtable slot） | 状态机字段回零：仅当 arg2==3 时 `[ecx+0x14]=0`，伴 `[ecx+0x10]=arg1, [ecx+0x18]=arg2, [ecx+8]=1` = **临时标志重置** | **不能**：对象是栈上/全局小状态块（~0x1C 字节），非 0x6F0 字节 InfantryClass；且写入条件 arg2==3 是状态机终态 |
| 6 | 0x7B23F4 | 0x7B23B0 [0x7B23B0,0x7B24D0) | ebp=eax=调用 0x7B20E0 的**新分配对象**（0x2A0 大小，call 0x7C8E17）；函数占 slot 0x7F7958 / 0x7F79C8 → COL 0x80EA60 / 0x80EAF8 → `.?AVIPXInterfaceClass@@` / `.?AVWinsockInterfaceClass@@` | 拷贝构造初始化（`movsd/movsb` 复制源后写默认 0） | **不能**：新分配网络接口对象；类 RTTI 明确非 InfantryClass |
| 7 | 0x7CD0C0 | 0x7CCFFC [0x7CCFFC,~0x7CD2C0) | **ebp=frame pointer**（`push ebp; mov ebp,esp; push ecx; push ebx`）；[ebp+0x14]=**栈参数槽 #4（out 参）**，非对象字段 | 字面值 **0x42 'B'**；字符串格式化指令写出 | **不能**：栈槽，根本不是对象内存 |
| 8 | 0x7CD0C9 | 同上 | 同上 | **0x62 'b'** 格式化写出 | **不能**：同上 |
| 9 | 0x7CD0F7 | 同上 | 同上 | **0x48 'H'** 格式化写出 | **不能**：同上 |
| 10 | 0x7CD12D | 同上 | 同上 | **0x70 'p'** 格式化写出 | **不能**：同上 |
| 11 | 0x7CD1B8 | 同上 | 同上 | **0x64 'd'** 格式化写出 | **不能**：同上 |

## 收口判定（D1）
- 11/11 均**不可能**作用于「已放在格上、正在被放置闸检查的步兵」：5 处是格式化栈槽（#7–#11，ebp 帧指针，已证字节级），2 处是 VQMovieHandle 构造器（#2/#3，vtable RTTI 已证），1 处 0x40 字节小对象（#4，分配大小已证），1 处 IPX/Winsock 接口拷贝构造（#6，RTTI 已证），1 处小状态机 out 块（#5，调用者 ecx 来源已证），1 处 out-holder 布尔回写（#1，write 目标与查询对象分离已证）。
- 结合 0x6F2B40 的 `or al,1; mov [esi+0x14],al`（无绕过分支）⇒ **构造路径 bit0 恒 1 + 11 处均不可达在册步兵** ⇒ 闸对步兵恒命中。
- 但「全域闭环」仍受 26 处 register-derived bit0 写点未逐一追值限制（见 UNKNOWNS.md），故本卡总判断按 [静态推断] 收口，不抬 [已证]。

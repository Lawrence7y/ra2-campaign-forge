# S18-K2 · LAYOUT.md —— EventClass 类布局 + 事件队列容器字节级取证

> 目标/工具/分级同 CRC.md。绝对只读。
> RTTI 链按 R14_COMMON §8.1 #8 正确式：`vtable[-1] → COL`；**`COL + 0xC → TD`**；**TD+8 为内联名串**（`char name[]`，非指针）。本卡自写 `work/peutil.py` 全镜像扫得 **988 个 TD**（u32[0]=0x7F9594, u32[4]=0, name@+8 以 `.?A` 开头）。

## 1. RTTI 实测定名（纪律 5 / 坑 ⑧：fail-closed 不猜名）

| 查项 | 结果 | 分级 |
|---|---|---|
| `.?AVEventClass@@` 直接 TD | **不存在**（988 TD 中 0 个）；仅 `.?AV?$VectorClass@PAVEventClass@@@@`@`0x836890`、`.?AV?$DynamicVectorClass@PAVEventClass@@@@`@`0x8368C0` 两个**指针容器** TD | `[已证]` |
| `.?AVTEventClass@@` | 存在 @`0x8446F8`（name `.?AVTEventClass@@`），4 个 COL（subobj 0/4/8/C）→ 触发器事件类，**与网络 111B 结构无关** | `[已证]` |
| 网络事件是否多态 | **否**：无自身 TD/vptr；容器装的是 `EventClass*`，非 EventClass 实例 ⇒ 111B 是 POD 值类型 | `[已证]` |
| "EventClass" 名字来源 | RTTI 容器 TD 的模板实参 `PAVEventClass@@` 是引擎类型系统内的真实类名（RTTI 级支撑），但 111B 结构体的 `sizeof/布局` 由分配点+拷贝+容器步长三腿独立支撑 | `[已证]`(名字)/`[静态推断]`(111B≡该名) |

> **fail-closed 声明**：网络 EventClass 无独立 RTTI TD，无法像 TEventClass 那样从 `COL+0xC→TD+8` 直接定名；本卡不编造任何「EventClass::xxx」成员名，只给字节支撑的偏移/宽度/语义。

## 2. 事件记录布局（111B POD，`#pragma pack(1)`）

| 偏移 | 宽度 | 类型 | 写者（本卡验） | 读者（本卡验） | 语义 | 分级 |
|---|---|---|---|---|---|---|
| +0x00 | 1 | u8 Kind | FillEvent_Place `0x4C6B22 mov [esi],bl`；Animation `0x4C6823` 常量0x14 | 分派 `0x4C6CC8 mov al,[esi]; dec; cmp 0x2d; ja` | 事件类型 1..0x2E | `[已证]` |
| +0x01 | 1 | u8 | Fill 体写载荷（doc §9） | gate `0x64C56B test [event+1],1`；写 `0x64CAC7 or ...,1` | **执行标志**（F1 已订正：非「Unused」） | `[已证]` |
| +0x02 | 1 | i8 HouseIndex | `0x4C6B14 mov [esi+2],al`；错误支 `0x4C6B49 =0xFF` | `0x4C6CC4 movsx ebx,[esi+2]`→House 数组；`0x64C541 movsx` | 玩家槽位 | `[已证]` |
| +0x03 | 4 | u32 Timestamp | `0x4C6B3F mov [esi+3],CurrentFrame`（末写，成功/错误支皆有） | `0x64C563 cmp CurrentFrame,Ts`；`0x64C6D3 mov esi,[...+3]` | 逻辑帧号/排序键 | `[已证]` |
| +0x07 | 4 | u32 Checksum/载荷 | FrameInfo 由 `0x649CA0` 写帧 CRC | `0x64C6E9 mov esi,[event+7]` 比对 | 帧 CRC（0x1C）或 NetID 载荷 | `[已证]` |
| +0x0B | 2 | u16 CommandCount | `0x4C6B1B mov [esi+0xb],eax` | 各 handler | 命令计数 | `[已证]` |
| +0x0D | 1 | u8 Delay | Fill 载荷/doc §9 | `0x64C6CC mov dl,[event+0xD]`（desync 索引） | FrameInfo CRC 帧偏移 | `[已证]` |
| +0x0E..0x6E | 0x61 | u8[] ExtraData | Place `+0xF/+0x13/+0x15`、SellCell `+9`、Animation `+0xF/+0x13` 等 | 各 handler 解引用 | 载荷（NetID/坐标/类型索引） | `[已证]`(存在)/`[静态推断]`(逐子字段) |

> 字段写序（本卡字节全验 `fillevent_place.txt`）：HouseIndex(+2) → Kind(+0) → 载荷(+7,+0xB,+0xF,+0x13,+0x15) → **Timestamp(+3) 末写**；错误支 HouseIndex=0xFF/Kind=0/Timestamp=CurrentFrame。写序契约防半成品被「Kind 非0即有效」旁路读取。

## 3. 事件队列容器（T2 主攻）

### 3.1 容器是不是 DynamicVectorClass？——**否**（[已证]）

三个"队列"都是**静态定长环形/向量缓冲区**，不是 `DynamicVectorClass` 实例：

| 队列 | 基址 | 结构 | 容量 | 索引/游标 | 证据 |
|---|---|---|---|---|---|
| **本地待发 QueuedEvents** | `0xA802D4` | 128×**111B** 定长记录（裸字节数组，非对象容器） | 128 | Count `0xA802C8`(<0x80)、写游标 `0xA802D0`(&0x7F)、Timings `0xA83A54` | `EVIDENCE/enqueue_idiom.txt`：`0x48CA62 lea edi,[ecx*3+...+0xA802D4]`(=idx×111) |
| **网络命令环 Queue** | `0x8B4204` | 0x4000×111B 裸记录 | 0x4000 | Count `0x8B41F8`、读游标 `0x8B41FC`(&0x3FFF) | `0x64C6B8..C9`：idx&0x3FFF×111 |
| **MegaMission 暂存** | `0xA83EDC` | 111B，上限 0x100 | 0x100 | Count `0xA83ED0`、游标 `0xA83ED8` | `0x64C739 cmp [0xA83ED0],0x100` |

- **判定依据**（纪律 19 / 坑「偏移不能定语义」）：这些是 `.data` 内的**裸记录数组**，索引乘法 `idx×111`（`lea edx,[ecx+ecx*8]; lea ecx,[ecx+edx*4]; lea edi,[ecx+ecx*2+base]` = ecx×37×3 = ×111）直接算字节偏移；**没有 vtable/Items/Count 容器头**。真正的 `DynamicVectorClass<EventClass*>`（TD `0x8368C0`）另装在全局 `0xAC4B48`（F1），是**指针容器**，与 111B 记录数组不是一回事。
- **`LayerClass` 参照但不假定同布局**：`0x8A0360` 的 `[5]LayerClass`（+4=Items/+0xC,+0xD=byte/+0x10=Count/+0x14=10）是**另一个**容器（绘制层，S06/S07），布局仅作对照；本卡未把它套到事件队列上。

### 3.2 入队链（谁 Add / 分配 / 溢出）

- **分配**：FillEvent 先在栈上填 111B（`0x48CA3F call 0x4C66C0` 返回 `eax`=栈记录指针），再 `new(0x6F)` 深拷贝（`0x637C85`/`0x63862C`）。
- **谁"Add"**：**无单一 Add 函数**（F1 结论，本卡复核）——入队是内联惯用式，遍布 UI 泵 `0x48C8B0`、逻辑各 handler。典型 `0x48CA48..9C`。
- **溢出行为**：`0x48CA48 cmp [0xA802C8],0x80 / jge 0x48CAA1` ⇒ **Count≥128 直接丢弃事件**（静默跳过拷贝与游标推进，仅置 `0x822cfc=0`+`call 0x6471a0`）。不阻塞、不报错、不覆盖最旧项。**[已证]**

### 3.3 出队/执行链

- 消费 `0x64C380`（S18 [未证]→本卡字节支撑升级请求）：`0x64C6B8` 取读游标→idx&0x3FFF→记录指针；三道执行门 `0x64C541`(HouseIndex==本家)/`0x64C563`(Ts≤CurrentFrame)/`0x64C56B`(+1&1==0)；通过则 `0x64C911`/`0x64CC0A call 0x4C6CB0` 分派；执行后 `0x64CAC7 or [event+1],1`。
- 分派 `0x4C6CB0`（thiscall ecx=event）：`dec Kind; cmp 0x2D; ja 0x4C8109; jmp [eax*4+0x4C8114]`，46 项跳表全在指令边界（前驱 C3/00/D9）。

## 4. GetSize 双向核对（§981 槽契约）

卡面要求 GetSize 双点闭合；**但网络 EventClass 无 vtable ⇒ 不存在虚槽 GetSize**。改用等价三腿独立定尺寸（均不依赖 atlas）：
1. **分配点imm**：`push 0x6F`（6A imm8，17 处；68 imm32 0 处）→ `operator new@0x7C8E17`。
2. **拷贝体长**：`ecx=0x1b`(27 dword) + `movsw` + `movsb` = 27×4+2+1 = 111。
3. **容器步长**：队列索引乘 111（`lea ×9 → ×4 → ×3`）；128/0x4000/0x100 三容量延伸均按 111B 步长。
⇒ **size=111 三腿闭合，不假定槽 12**（无虚表可假定）。`v[11]/v[12]` 同形风险对本 POD 不适用。

## 5. 未闭环
- 网络 EventClass 无独立 RTTI TD，「111B 结构 ≡ EventClass 名」最终归属为 `[静态推断]`（名字本身有容器 TD 模板实参级支撑）。
- `0x4C93D0` 字段语义、term 拼装位序见 CRC.md §5。
- 每帧 RNG 数字 `0xAFA26C` 的消费者（侧信道语义）未展开 → `[未证]`。

# S18-K2 · CRC.md —— 事件入队/执行/校验和 三链字节级取证

> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（全串实测一致），4,825,360 B / ImageBase `0x400000`。
> 工具：capstone 5.0.7 `skipdata=True` + pefile 2024.8.26，自写 `work/peutil.py`（**不依赖 function_atlas.tsv**）。
> 分级：`[已证]`=本卡字节级独立复算（反汇编/RTTI/CRC 表逐项）；`[静态推断]`=单通道逻辑闭合；`[未证]`=需真机或未穷举。

## 0. 停机核验（纪律 9）—— 三条入账前提逐条复算

| 前提 | 本卡复算 | 结论 |
|---|---|---|
| **111 B** | ① `6A 6F push`→`call 0x7C8E17`(operator new) @`0x637C85`/`0x63862C`；② 拷贝 `ecx=0x1b`(27 dword)`+movsw+movsb`=27×4+2+1=**111**；③ 全镜像 `6A 6F` **17 处**、`68 6F000000` **0 处**（§972 6A 陷阱） | ✅ **111 B 成立** |
| **46 项** | 跳表 `0x4C8114+4*i` i=0..45 全 46 目标，前驱 ∈{C3 ret,00 nop,D9 leave}；引擎名表 `0x82091C` 47 名（含 name[0]=EMPTY） | ✅ **46 项成立** |
| **CRC 第 4 集合 = House** | 本卡自扫 RTTI：`0xA8022C` Items / `0xA80238` Count 容器的 vt → COL(vt-4) → TD(COL+0xC) → name(TD+8 inline) = `.?AV?$DynamicVectorClass@PAVHouseClass@@@@` | ✅ **House（非 Aircraft）成立** |

> **口径分歧（已记 DISAGREE.md）**：卡面写「atlas 660 / named 496(75.15%) / proved 53(8.03%)」，盘上 `coverage.tsv`∩`function_atlas.tsv` 实算 **atlas_n=659 / named_L=S=496(75.27%) / proved=53(8.04%)**（PANEL.md L50 同值）。以盘上 659 为准，未凑 660。50% 门槛 330，差 **277** 项 proved。

---

## 1. 两套 CRC，勿混（本卡核心结论）

引擎内存在**两套完全不同的校验和**，卡面「CRC 算法本体」须分述：

| # | 名称 | 入口 | 算法 | 表 | 用途 | 调用时机 | 失败行为 | 判定 |
|---|---|---|---|---|---|---|---|---|
| A | **帧 CRC**（轻量 desync 探针） | `0x64DAB0` | 自定义加法哈希 `acc = rol1(acc) + term`，初值 0，**无多项式、无查表** | 无 | 联机锁步防不同步 | **每逻辑帧** ×2（`0x64731C`/`0x647684`） | 不等→`0x64CC61` 写 SYNC*.TXT + 弹 `TXT_OUT_OF_SYNC`/`TXT_STOP` | **同步校验（防不同步）** |
| B | **对象 CRC / Checksummer**（全字段） | `0x4A1C10` 簇 + 各 `*::v[13]` | **标准 CRC-32**（反射，poly `0xEDB88320`，首尾取反） | **`0x81F7B4`**（256/256 项实测匹配） | 存档一致性 + desync 后诊断归因 | `*::CalculateChecksum` v[13]（仅 SYNC*.TXT 诊断档调用） | 无运行时失败动作（只进报告） | **存档/诊断校验（防篡改/归因）** |

> **回答卡面问题**：卡面问「是否标准 CRC32？表地址？」——**帧 CRC（A）不是**；**对象 Checksummer（B）是**，表在 `0x81F7B4`。二者服务不同目的，卡面「判同步 vs 存档」需分述：A=同步校验，B=存档/诊断校验。

---

## 2. 帧 CRC 算法本体（`0x64DAB0`，[已证]）

### 2.1 混合式（逐项）
`0x64DB3B..0x64DB43`（第一次出现，其余集合同构）：
```
0064DB33  mov edx,[0xAC51FC]      ; acc
0064DB39  mov eax,edx
0064DB3B  shr eax,0x1f            ; msb(acc)  (= 符号位)
0064DB3E  lea eax,[eax+edx*2]     ; acc*2 + msb(acc)  == rol1(acc)
0064DB41  add eax,ecx             ; + term
0064DB4A  mov [0xAC51FC],eax      ; 写回
```
⇒ **初值 0**（`0x64DAC3 mov [0xAC51FC],0`），**混合 = rol1(acc)+term**（`+` 而非 XOR；这是关键差异，**不是标准 CRC**）。

### 2.2 term 的量化（[已证]，字段语义 [静态推断]）
- `imul 0x66666667; sar edx,2; +sign` = **÷10**（有符号）；用于坐标低 32 位。
- 取值 helper `0x4C93D0(obj+0x388 / obj+0x3A0)`：读 `word[+0]`/`word[+4]`/`dword[+8]`/`dword[+0x10]`/`word[+0x14]` + `CurrentFrame[0xA8ED84]`，插值返回 dword；CRC 取 `shr 7;inc;shr 1;and 0xFF` ≈ `(v>>8)&0xFF`（**1 字节**）。该 helper 的字段物理含义未逐字段命名（同 `docs/re/net_sync_checksum.md` §7.1），标 `[未证]`。
- term 拼装 ≈ `((fieldA0/10)<<16) | q8 | (field9C/10)`（32 位，[静态推断] 拼装顺序）。

### 2.3 六集合 + 一 RNG（[已证]，容器元素类型经本卡 RTTI 链自证）
| 序 | 循环头 | Items/Count | 容器 RTTI（本卡 COL+0xC→TD+8） | 元素类型 | 每对象读字段 |
|---|---|---|---|---|---|
| 1 | `0x64DACE` | `0xA83DEC/0xA83DF8` | `VectorClass<InfantryClass*>` | Infantry | +0x9C/+0xA0/+0xA4 dword, helper(+0x388)→byte |
| 2 | `0x64DB67` | `0x8B410C/0x8B4118` | `DynamicVectorClass<UnitClass*>` | Unit | 同上 + helper(+0x3A0)→byte |
| 3 | `0x64DC29` | `0xA8EB44/0xA8EB50` | `DynamicVectorClass<BuildingClass*>` | Building | 同 Infantry |
| **4** | `0x64DCC3` | `0xA8022C/0xA80238` | **`DynamicVectorClass<HouseClass*>`** | **House** | **`byte [obj+0x241]`**（1 字节） |
| 5 | `0x64DCFA`(内)/`0x64DCE9`(外) | `0x8A0370` 起 step 0x18 至 `0x8A03E8`（5×LayerClass，Items=层基-0xC） | ctor `0x4A8630` 装 `Vec<ObjectClass*>` | 5×Layer | WhatAmI(vcall+0x2C)==4 时跳过；读 +0x9C/+A0/+A4 + vcall+0x2C |
| 6 | `0x64DDA7` | `0x87F77C/0x87F788` | `LogicClass` | Logic | 同 Layer |
| 7 | `0x64DE33` | — | `Random@0x65C780`（局内 RNG `*(0xA8B230)+0x218`） | RNG | 1 次 `Random()` |

- **采集序**：Infantry→Unit→Building→**House**→5×Layer→Logic→RNG（七回边逐一跟到）。
- Count−Items 恒 `0xC`（vtable+0 / Items+4 / Count+0x10，同一容器布局）——六者自证。

### 2.4 存储与比对（[已证]）
- 结果存 `LatestFramesCRC[CurrentFrame&0xFF]@0xB04474`（`0x647334` / `0x6476A5` 两处写）。
- 比对 `0x64C6CC mov dl,[event+0xD=Delay]` → `0x64C6D3 mov esi,[event+3=Ts]` → `sub; and 0xFF` → `0x64C6E2 mov edx,[esi*4+0xB04474]` vs `0x64C6E9 mov esi,[event+7=Checksum]` → `jne 0x64CC61`（**边界对齐解码点 `0x64C6AC`**，非审计曾误标的 `0x64C6AA`）。

### 2.5 每帧 1 次 RNG 同步消费（[已证]）
`0x64DE3F call 0x65C780`（帧 CRC 尾）+ `0x650A90`（`ExtraSyncInfo@0xB04880` 开关：关→`0xAFA26C=Random()`；开→同步快照）——`Random@0x65C780` 为滞后 Fibonacci 双游标（`0xFA=250` 表，`Next2` 初值 `0x67`），**改消费次数即分叉**。

---

## 3. 「46 项逐项落地」——两套含义均落地

> **诚实声明**：卡面「把 46 项逐项落地：每项 = 哪个对象/哪个字段、读宽度、在 CRC 串里的偏移」存在**口径混淆**。
> F1 入账的「46 项」=**EventType 跳表 46 项**（Kind 1..0x2E），与「111 B」（事件记录大小）并列，均属**网络事件**而非 CRC 字段。卡面把「在 CRC 串里的偏移」套到这 46 项上，但帧 CRC 每对象只读 ~4–6 个字段，不存在 46 个 CRC 字段。
> **处置**：(§3.1) 按 F1 权威口径落地 **46 个 EventType**（每项给 handler/事件字段/读宽度/偏移）；(§3.2) 另给**帧 CRC 全部字段贡献表**（"CRC 串"的真实构成）；(§3.3) 给 **Checksummer 标准 CRC32 本体**。三者分列，不凑数。

### 3.1 46 个 EventType 逐项落地（[已证]：跳表+名表+handler 前驱；字段来自 FillEvent 写点，节选自 `docs/re/net_sync_checksum.md §9` 并由本卡 `EVIDENCE/fillevent_*.txt` 字节复核代表项）

「事件串」= `NetworkEvent` 111B `#pragma pack(1)` 记录；偏移即记录内偏移。字段：+0 Kind(u8)/+1 执行标志(u8)/+2 HouseIndex(i8)/+3 Timestamp(u32)/+7 Checksum/载荷(u32)/+0xB CommandCount(u16)/+0xD Delay(u8)/+0xE.. ExtraData(0x61B)。

| Kind | 名 | handler | 事件字段写/读（偏移:宽度） | noop | 语义 |
|---|---|---|---|---|---|
| 0x01 | POWERON | 0x4C6CF0 | +7:dword(建筑 NetID) | | 建筑上电 |
| 0x02 | POWEROFF | 0x4C6D4D | +7:dword | | 建筑断电 |
| 0x03 | ALLY | 0x4C6DEE | +7/+…(FillEvent_PlayerBased) | | 结盟 |
| 0x04 | MEGAMISSION | 0x4C71CA | 路径载荷(+7.., FillEvent_Waypoints) | | 编队任务 |
| 0x05 | MEGAMISSION_F | 0x4C71CA | 同上 | | 编队任务(F) |
| 0x06 | IDLE | 0x4C74CB | +7:dword(NetID) | | 待机 |
| 0x07 | SCATTER | 0x4C7859 | +7:dword | | 散开 |
| 0x08 | DESTRUCT | 0x4C7BDF | +7:dword | | 摧毁 |
| 0x09 | DEPLOY | 0x4C76BC | +7:dword | | 部署 |
| 0x0A | DETONATE | 0x4C7823 | +7:dword | | 引爆 |
| 0x0B | PLACE | 0x4C70E1 | +2:b/+0:b/+7:d/+0xB:d/+0xF:d/+0x13:w/+0x15:w/+3:d | | 放置（本卡字节全验 `fillevent_place.txt`） |
| 0x0C | OPTIONS | 0x4C7929 | +7:dword | | 选项 |
| 0x0D | GAMESPEED | 0x4C794B | +7:dword | | 游戏速度 |
| 0x0E | PRODUCE | 0x4C711B | +7:d/+0xB:d/+0xF:d | | 生产 |
| 0x0F | SUSPEND | 0x4C7140 | 同上 | | 暂停生产 |
| 0x10 | ABANDON | 0x4C7163 | 同上 | | 放弃生产 |
| 0x11 | PRIMARY | 0x4C718C | +7:dword | | 主建筑 |
| 0x12 | SPECIAL_PLACE | 0x4C78D6 | +7:d/+0xB:w/+0xD:w(体A) | | 超武放置 |
| 0x13 | EXIT | 0x4C7903 | +2:b(+0x64C7B6 二次处理) | | 退出/踢人 |
| 0x14 | ANIMATION | 0x4C6FDE | +0:b(常量0x14)/+7:d/+0xB:d/+0xF:d/+0x13:d | | 动画（本卡字节验 `fillevent_animation.txt`） |
| 0x15 | REPAIR | 0x4C6ED2 | +7:dword | | 修理 |
| 0x16 | SELL | 0x4C6F12 | +7:dword | | 出售 |
| 0x17 | SELLCELL | 0x4C6FB3 | +7:w/+9:w(Cell X/Y) | | 出售格（本卡字节验 `fillevent_sellcell.txt`） |
| 0x18 | SPECIAL | 0x4C6E48 | +7:dword | | 超武 |
| 0x19 | FRAMESYNC | 0x4C8109 | — | ✅ | 传输层心跳（no-op） |
| 0x1A | MESSAGE | 0x4C8109 | — | ✅ | 聊天（no-op） |
| 0x1B | RESPONSE_TIME | 0x4C79FF | — | | 计时 |
| 0x1C | FRAMEINFO | 0x4C8109 | +7=Checksum/+0xD=Delay/+3=Ts（在 0x64C380 比对） | ✅ | 帧 CRC 载体（dispatch 层 no-op） |
| 0x1D | SAVEGAME | 0x4C7A14 | →0x67CEF0 读档 | | 存档命令 |
| 0x1E | ARCHIVE | 0x4C6DAA | NetID→Techno | | 归档 |
| 0x1F | ADDPLAYER | 0x4C7B4D | +7:dword | | 加玩家 |
| 0x20 | TIMING | 0x4C800C | — | | 计时 |
| 0x21 | PROCESS_TIME | 0x4C80B1 | — | | 处理时间 |
| 0x22 | PAGEUSER | 0x4C80F6 | — | | 传呼 |
| 0x23 | REMOVEPLAYER | 0x4C7B73 | +7:dword | | 移除玩家 |
| 0x24 | LATENCYFUDGE | 0x4C7F35 | — | | 延迟微调（0x4C7F35） |
| 0x25 | MEGAFRAMEINFO | 0x4C8109 | — | ✅ | no-op |
| 0x26 | PACKETTIMING | 0x4C8109 | — | ✅ | no-op |
| 0x27 | ABOUTTOEXIT | 0x4C7CF5 | — | | 即将退出 |
| 0x28 | FALLBACKHOST | 0x4C7BF1 | — | | 主机回退 |
| 0x29 | ADDRESSCHANGE | 0x4C7C12 | — | | 地址变更 |
| 0x2A | PLANCONNECT | 0x4C6CDE | — | | 计划模式连接 |
| 0x2B | PLANCOMMIT | 0x4C6CDE | — | | 计划模式提交 |
| 0x2C | PLANNODEDELETE | 0x4C6CDE | — | | 计划节点删除 |
| 0x2D | ALLCHEER | 0x4C6E2E | — | | 全体欢呼 |
| 0x2E | ABANDON_ALL | 0x4C7188 | — | | 全部放弃 |

（5 个 no-op 目标全 `0x4C8109`，入口→ret 逐条打完确认真空；4/5 个 PLAN*→0x4C6CDE 共用体。）

### 3.2 帧 CRC 字段贡献表（"CRC 串"的真实构成，[已证] 读点，语义 [静态推断]）

| 对象 | 字段 | 宽度 | 量化/用途 | term 内位置 |
|---|---|---|---|---|
| Infantry/Unit/Building/Layer/Logic | +0x9C | dword | ÷10 | 低 16 位 |
| 同上 | +0xA0 | dword | ÷10 | 高 16 位（`<<0x10`） |
| 同上 | +0xA4 | dword | 读出存栈（参与量化，拼装顺序 [静态推断]） | 中 |
| 同上 | helper(0x388)→返回 dword | 1 字节(`>>8&0xFF`) | 0x4C93D0 插值量化 | q8 |
| Unit 额外 | helper(0x3A0)→dword | 1 字节 | 同上 | q8b |
| Layer/Logic | WhatAmI `vcall[+0x2C]` | dword | ==4 跳过；值进 term | 直加 |
| House | +0x241 | **byte** | 直加 | 直加 |
| RNG | Random() | dword | 直加 | 直加 |

> **注意**：`0xA4`/`0x388` helper 的精确拼装位序为 `[静态推断]`（`0x66666667` 乘除与 `shl 0x10` 已证，谁进高/低 16 位在 Infantry 与 Unit 两处因编译器寄存器分配不同而形式有别）；不做过度断言。

### 3.3 Checksummer 标准 CRC32 本体（[已证]）

`0x4A1C10`（bulk Add）核心（`EVIDENCE/checksummer_probe.txt`）：
```
004A1C54  mov eax,[ecx]          ; crc state
004A1C5B  not eax               ; ~init
004A1C62  loop(4 bytes):
   bl = input byte
   edx = (eax & 0xff) ^ bl
   eax >>= 8
   edx = [edx*4 + 0x81F7B4]      ; CRC table
   eax ^= edx
004A1C80  not eax
004A1C83  mov [ecx],eax
ret 4
```
- **表**：`0x81F7B4`，256 项标准反射 CRC-32 表，**本卡逐项复算 256/256 匹配**（`[0]=0x00000000`/`[1]=0x77073096`/`[8]=0x0EDB8832`）；poly = **0xEDB88320**（反射形式，即 0x04C11DB7）。
- **初值/末值**：`not` 首尾取反（标准 CRC-32 的 init/final xor 0xFFFFFFFF）。
- **Add 簇**：`0x4A1C10`(bulk) / `0x4A1CA0`,`0x4A1D50`,`0x4A1D70`,`0x4A1D90`(标量重载) / `0x4A1DE0`(Process 循环) / `0x4A1FB0`(GetValue/Commit)。
- **进档口**：`AbstractClass::CalculateChecksum(v[13])`；各类 v[13] 内大量 `0x4A1CA0` 直呼（doc 记 331 处）；`SYNC*.TXT` 按类打印全量 CRC（`0x837FAA–0x83883A` 类目串）。
- **判定**：这是**存档/诊断校验**（防篡改 + desync 归因），**不用于每帧联机比对**（太重）。

---

## 4. 三链汇总（[已证] 地址级）

| 链 | 关键地址 | 证据 |
|---|---|---|
| **入队** | `0x48CA48`(溢出闸 `cmp [0xA802C8],0x80 / jge` 丢事件)、`0x48CA54..72`(dest=0xA802D4+idx×111，拷 27d+w+b)、`0x48CA7F`(Timings)、`0x48CA91`(`idx=(idx+1)&0x7F`)、`0x48CA9C`(Count++) | `EVIDENCE/enqueue_idiom.txt` |
| **分配** | `0x637C85`/`0x63862C` `push 0x6f`→`call 0x7C8E17`(operator new) | `EVIDENCE/alloc_and_desync.txt` |
| **执行** | `0x4C6CB0`(thiscall ecx=event；`dec eax;cmp 0x2d;ja; jmp [eax*4+0x4C8114]`), 跳表 46 项；gate `0x64C563`(Ts≤CF)/`0x64C56B`(+1&1==0)/`0x64C541`(HouseIndex match)；后置 `0x64CAC7 or [event+1],1` | `EVIDENCE/dispatch_entry.txt`/`execute_gate.txt`/`eventtype_full_table.txt` |
| **校验和** | 帧 CRC `0x64DAB0`→`0xAC51FC`→`LatestFramesCRC@0xB04474`；比对 `0x64C6CC..F2`→`0x64CC61`；对象 CRC `0x4A1C10`+表 `0x81F7B4` | §2 / §3.3 + EVIDENCE |

## 5. 未闭环
- helper `0x4C93D0` 的 +0x388/+0x3A0 字段物理语义（同 doc §7.1，需对照 TechnoClass 布局）→ `[未证]`。
- 帧 CRC term 的精确拼装位序（§3.2）→ `[静态推断]`。
- 46 个 EventType 中未逐一字节展开全部 FillEvent 写点（本卡验 Place/SellCell/Animation 三代表 + Noopt），其余按 doc §9 → `[静态推断]`。
- CalculateChecksum 331 处 Add 调用未逐类穷举 → `[未证]`。

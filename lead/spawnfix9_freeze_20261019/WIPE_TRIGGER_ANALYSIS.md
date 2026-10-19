# 开场清洗（Opening Wipe）引擎触发条件定谳 —— 只读反汇编机制分析

- 分析员：ZCode（ra2-re-analyst 深水区任务）
- 日期：2026-10-19
- 参照件（只读）：`lead\qc161_u0400_trip\_src_variant_800x600_csf\gamemd.exe`
  - sha256 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（起跑实测命中）
  - 大小 `0x49A110`；ImageBase `0x400000`；`.text VA=0x00401000 VS=0x003DF38D RAW=0x00001000` → `file_off = VA − 0x400000` 平坦映射成立
- 工具：Python 3.12.10 + capstone 5.0.7；全部反汇编经 bash heredoc stdin 内联执行（零写入纪律，唯一写入=本报告）
- 证据基线：`qc151_fields.json`（QC213 178 条 latch）、`FROZEN_DUMP_PARSE_T55H.md`、`SPAWNFIX9_FREEZE_ANALYSIS.md`、`measure_w0.json`

---

## §0 结论（条件表达式一句话）

**「开场清洗」不是 Purge、不是 skirmish 特有踢出、也不是 ShortGame 逻辑；它是 `HouseClass::AI`（`0x004F7870`）在 `ShortGame==no` 分支上执行的常规败北自检（`0x004F8E86`）——当某屋 `CurBuildables(+0x2F0)==0` 且其「本屋单位链表计数」四项全零（`+0x5564/+0x5578/+0x558C` 三链 Count + `+0x5550` 链按 `RulesClass+0x8E8[1]` 的当前指数计数）时，调 `0x004FC6D0`（解散本屋 TeamType 悬空成员）+ `0x004FC0B0`（置 `Defeated(+0x1F5)=1`、发 EVA、进入终局统计）；先决条件是 `SessionClass::GameType(0x00A8B238)!=0`（即已开战、非菜单态）、`frame(0x00A8ED84)>0`、本屋尚未 `Defeated`、且 `HouseType(+0x1A6)` 非「仅观察者」。**

对 T55h 的 h1 而言：四屋 `CurBuildings` 全程为 0（AI 未起建筑），h1 在 f270→f300 之间车辆链（`+0x5574`=list@0x5564 的 Count）被战斗打到 0，触发该分支；`0x004FC0B0` 内 `0x004FC179-0x004FC1AE` 的清洗循环随即把残余步兵链表（`+0x5588`=list@0x5578 的 Count，f300 时仍有 22）清零——**这就是「242 车瞬间清零且 def1F5 置位、f373 残余 22 步兵也清零」的完整机理**，与先验报告「四链表计数全零」的表面矛盾由该清洗循环解释（清洗在判定之后执行，故判据只需车辆侧三链为零）。

---

## §1 反汇编证据链

### 1.1 宿主函数与调用路径

`0x004F8F21` 所属函数为 `HouseClass::AI` 全体，实丈边界 `0x004F7870`（`sub esp,0x3C; mov ebp,ecx` = this=HouseClass）…`0x004F8361`（`ret 0xC`，两个栈参 + this）。`0x004F8F21` 之前的 `0x004F8931` 是函数中段（IDA 式伪边界，非真函数头；已用 int3 填充实测确认真头为 `0x004F7870`）。

调用者（E8 直调，全 .text 扫描）：

| 调用者 VA | 语境 |
|---|---|
| `0x004FEDB7` | `0x004FEBF9` 内：`0x00A8EC88`（TeamType 总数）遍历 + `0x00A83CF0`（HouseClass 数）外层循环 → **每帧 AI/败北自检主入口** |
| `0x00414C06` | `0x00414BE0` 附近：`frame % 24 == 0` 门（`idiv 0x18`）后的旁路调用 |
| `0x00445xxx` 等 5 处 | 脚本/事件路径 |

`0x004FC0B0`（败北处理）**唯一** E8 调用者 = `0x004F8F82`（本函数的 `ShortGame==no` 分支尾部）。这排除了「另有路径进 0x4FC0B0」的假说。

`0x004FC6D0`（解散 TeamType）调用者三处：`0x004F87FA`（另一条 AI 脚本路径）、`0x004F8F7B`（本路径）、`0x006E31C8`。

### 1.2 败北自检门（`0x004F8E86` → `0x004F8F21`）逐指令

```
0x004F8E86  cmp dword ptr [0xa8b238], ebp   ; ebp=0（函数内 0x4F8448 xor ebp,ebp）
0x004F8E8C  je 0x4f8f87                     ; GameType==0 → 跳过（菜单/未开战）
0x004F8E92  mov al, byte ptr [esi+0x1f5]    ; Defeated
0x004F8E9A  jne 0x4f8f87                    ; 已败北 → 跳过
0x004F8EA0  cmp dword ptr [0xa8ed84], ebp   ; frame counter
0x004F8EA6  jle 0x4f8f87                    ; frame<=0 → 跳过（开场前）
0x004F8EAC  mov eax, dword ptr [esi+0x34]   ; → HouseType
0x004F8EAF  mov cl, byte ptr [eax+0x1a6]    ; HouseType+0x1A6
0x004F8EB7  jne 0x4f8f87                    ; !=0 → 跳过（观察者/非参战屋）
0x004F8EBD  mov al, byte ptr [0xa8b262]     ; ★ ShortGame 位
0x004F8EC2  test al,al
0x004F8EC4  je 0x4f8f21                     ; ★ ShortGame==no → 走 0x4F8F21（常规败北判定）
```

**ShortGame 位实锤**：`0x00A8B262` 由 `0x0052D1F5`（`mov byte ptr [0xa8b262], cl`）从 `SessionClass+0x14B6` 拷入；而 `SessionClass+0x14B6` 由 `0x00672190`（`call 0x5295F0` = INI 布尔读取器，键名压栈 `0x0083CFA8` = `"ShortGame"`，节为 `[Skirmish]`）写入。INI 布尔读取器 `0x0052979A`：首字符 `'0'` → 返回 0，`'1'` → 返回 1。**故 `[Skirmish] ShortGame=no` → `0x00A8B262==0` → 走 `0x004F8F21` 常规判定**（与「好局坏局同配置」实测自洽：ShortGame 只切换判定分支，两分支判据同构，见 1.4）。

### 1.3 常规败北判定（`0x004F8F21` → `0x004F8F79`）

```
0x004F8F21  mov edi, dword ptr [esi+0x2f0]      ; edi = CurBuildables（建筑可建造计数）
0x004F8F27  lea ecx, [esi+0x5564]               ; 链 A
0x004F8F2D  call 0x49fb60                       ; → mov eax,[ecx+0x10] = Count
0x004F8F32  lea ecx, [esi+0x5578]               ; 链 B
0x004F8F38  add edi, eax
0x004F8F3A  call 0x49fb60
0x004F8F3F  lea ecx, [esi+0x558c]               ; 链 C
0x004F4F45  add edi, eax
0x004F8F47  call 0x49fb60
0x004F8F4C  mov edx, dword ptr [0x8871e0]       ; RulesClass
0x004F8F54  mov eax, dword ptr [edx+0x8e8]      ; → 数组基
0x004F8F5A  mov eax, dword ptr [eax+8]          ; → 元素[1]（HouseType* 数组第 2 项）
0x004F8F5D  cmp eax, ebp                        ; ==0?
0x004F8F5F  je 0x4f8f75                         ;   null → 不加
0x004F8F61  mov ecx, dword ptr [eax+0xdf8]      ; → 该 HouseType 的索引/ID
0x004F8F68  lea ecx, [esi+0x5550]               ; 链 D
0x004F8F6E  call 0x49fae0                       ; → Count(D[ID])
0x004F8F73  add edi, eax
0x004F8F75  cmp edi, ebp                        ; edi == 0 ?
0x004F8F77  jne 0x4f8f87                        ; !=0 → 存活，跳过
0x004F8F79  mov ecx, esi
0x004F8F7B  call 0x4fc6d0                       ; 解散本屋 TeamType 悬空成员
0x004F8F80  mov ecx, esi
0x004F8F82  call 0x4fc0b0                       ; ★ 败北处理
```

**完整条件表达式（精确到字段偏移）**：

```
判负(house H) ⟺ GameType(0x00A8B238) != 0
              ∧ frame(0x00A8ED84) > 0
              ∧ H.Defeated(H+0x1F5) == 0
              ∧ HouseType(H+0x34).IsObserver(HouseType+0x1A6) == 0
              ∧ ShortGame(0x00A8B262) == 0            ← T55h 本局取此支
              ∧ H.CurBuildables(H+0x2F0) == 0
              ∧ Count(list@H+0x5564) == 0
              ∧ Count(list@H+0x5578) == 0
              ∧ Count(list@H+0x558C) == 0
              ∧ ( Rules.Arr8E8[1] == NULL ∨ Count(list@H+0x5550[ Rules.Arr8E8[1]->+0xDF8 ]) == 0 )
```

`ShortGame==yes` 分支（`0x004F8EC6`→`0x004F8F11`）判据同构：`CurBuildables==0` ∧ 三个来自 `RulesClass+0xB24` 数组前三元素的指数在 `list@H+0x5514` 上的计数和 == 0。两分支都只数「单位/建筑类链表」，与 `CurBuildables` 互补。

### 1.4 链表族语义（`0x005514` 起的 0x14 字节步长族）

HouseClass 从 `+0x5514` 起以 0x14 字节为步长排布 12 个「按类型索引的计数向量」：`0x5514, 0x5528, 0x553C, 0x5550, 0x5564, 0x5578, 0x558C, 0x55A0, 0x55B4, 0x55C8, 0x55DC, 0x55F0`。

辅助函数（反汇编写点）：
- `0x0049FB60`：`mov eax,[ecx+0x10]; ret` —— **取 Count**（list 对象 +0x10）。
- `0x0049FAE0(list, typeIdx)`：若 `typeIdx < list.Count(+0x8)` 则取 `list.Array(+0x4)[typeIdx]`；否则**先扩容并清零尾部再取**（`0x49FB0E` `mov [edx+eax*4-4],0`）——即「该类型当前是否有一个活着」的指示器（非总数）。
- QC213 探针 `c5560/c5574/c5588/c559C` 的 source 自证：`list@0x5550 Count=list+0x10`、`c5574` 同模式——故 **`c5574` = list@0x5564 的 Count**（注意探针读的是 `HouseClass+0x5574` = list@0x5564 对象的 +0x10，不是 0x5578 那个 list）。

各 slot 语义（由调用点上下文定谳，非穷尽）：

| slot | 证据 | 语义 |
|---|---|---|
| `+0x5550` | 11 处调用，含 `0x004F78CE`（AI 起手检查）、`0x005097CA`（`RulesClass+0x910` 数组遍历）、`0x004820AB`（crate 生成） | ** Infantry（步兵）** |
| `+0x5564` | `0x004F7DBA`（AI：`Rules+0x400` 单类型检查） | ** Vehicles（车辆）** |
| `+0x5578` | `0x004F7DC0` 同族 | ** Aircraft（飞机）** |
| `+0x558C` | `0x004F7D6C` 同族（`Rules+0x3E8` 数组） | ** Buildings（建筑）** 或 Aircraft 族另一槽 |
| `+0x5514` | `0x004F800A`（mission 6 分支） | 另一单位族 |

T55h 实测（QC213 latch）与该判据精确对齐：

| frame | c5574(=list@0x5564) | c5588(=list@0x5578) | x2F0 | def1F5 |
|---|---|---|---|---|
| 270 | 242 | 92 | 0 | 0 |
| 300 | **0** | 22 | 0 | **1** |
| 373 | 0 | **0** | 0 | 1 |

即 f270→f300 之间车辆链归零（判据 3/4/5 项中车辆项先达成）→ 判负 → `0x4FC0B0` 的 `0x4FC179-0x4FC1AE` 循环把 h1 的 TeamType 成员逐个 `vtable+0xF8`（=Destroy/Release）→ f300 时 c5588 从 22 掉到 0（f373 锁存 0）。

### 1.5 `0x004FC0B0`（败北处理）关键指令

```
0x004FC0B0  sub esp,0xB0; push ebx/ebp/esi/edi; mov esi,ecx        ; esi=this
0x004FC0BC  mov eax,[esi+0x24c]                                    ; 本屋 slot id
0x004FC0C2  mov byte ptr [esi+0x1f5], 1                            ; ★ Defeated=1
0x004FC0C9  mov ecx,[0x8871e0]                                     ; RulesClass
0x004FC0CF  cmp eax,[ecx+0x1434]                                   ; 与 PlayerSlot 比
0x004FC0D5  jne 0x4fc112                                           ; 非本地玩家槽 → 跳过 EVA
0x004FC0D7  mov edx,[0xa8b238]                                     ; GameType
0x004FC0DD  mov al,[esi+0x1ec]                                     ; isHuman
...          0x4FC0E7..0x4FC0FB：inlined IsDefeatedOrPurged 等价逻辑
0x004FC0FF  mov al,[ecx+0x17e0]                                    ; 某会话旗
0x004FC105  test al,al; je 0x4fc112
0x004FC109  test edx,edx; je 0x4fc112
0x004FC10D  call 0x501640                                          ; 触发 "YouHaveLost" 音/EVA
0x004FC112  mov ecx,[0xa8b230]                                     ; SessionClass
0x004FC118  test byte ptr [ecx],0x10                               ; MP 标志位
0x004FC11B  je 0x4fc163                                            ; 非 MP → 跳过踢出
0x004FC11D  mov eax,[esi+0x53dc]                                   ; 本屋连接/玩家对象
...          0x4FC14E: 调 0x5657A0（发送败北消息）
0x004FC15E  call 0x4fbe40                                          ; MP 踢出路径
0x004FC163  mov eax,[0xa8b238]; test eax,eax; je 0x4fc1b0
0x004FC16C  mov edx,[0xa8b230]; mov eax,[edx]; test ah,8           ; 另一会话位
0x004FC177  je 0x4fc1b0
0x004FC179  mov eax,[0x8b4118]                                     ; 全局对象表 Count
0x004FC184  … loop: [ecx+0x21c]==esi ∧ [ecx+0x90]!=0 → call [edx+0xf8]   ; ★ 清洗本屋 TeamType 成员
0x004FC1B0  mov eax,[0xa83d4c]                                     ; PlayerPtr
0x004FC1B5  cmp eax,esi; jne 0x4fc30c                              ; 非本地玩家 → 走 0x4FC30C
              （本地玩家分支：置 MapIsClear、EVA_YouHaveLost、终局 UI）
0x004FC30C  … mov byte [ecx+0x241],1 ; printf "MPlayer_Defeated: frame %d, house id %d, MapIsClear set to true"
```

**关键甄别结论**：
- `0x004FC179-0x004FC1AE` 的清洗循环前置条件 = `GameType!=0` ∧ `SessionClass[0] 的 ah 位 8`（即 `byte[1]&0x08`）。**这是 `+0x1EC/+0x1ED` 之外的、真正把「在场 22 步兵」清零的指令位置**。
- 字符串锚：`0x00824BC8` = `"MPlayer_Defeated() - Player %s has been defeated (OBIWAN MODE)\n"`；`0x00824B84` = `"MPlayer_Defeated: frame %d, house id %d, MapIsClear set to true\n"`；`0x00824B3C` = `"MPlayer_Defeated() - Opponent %s has been defeated\n"`；`0x00824B0C` = `"MPlayer_Defeated() - Alive = %d, Humans = %d\n"`。函数名自证 = **`HouseClass::MPlayer_Defeated`**。
- `0x004FC3DE-0x004FC44F`：`Alive/Humans` 统计循环，逐屋查 `+0x1F5`（已败北跳过）、`HouseType+0x1A6`（观察者跳过），并按 `IsDefeatedOrPurged` 语义（`GameType!=0` 时直接取 `+0x1EC`；否则 `+0x1EC ∨ +0x1ED`）判人类存留。

### 1.6 `0x0050B730`（IsDefeatedOrPurged）反汇编写点

```
0x0050B730  mov eax,[0xa8b238]      ; GameType
0x0050B735  test eax,eax
0x0050B737  mov al,[ecx+0x1ec]      ; isHuman
0x0050B73D  jne 0x50b752            ; GameType!=0 → 直接返回 isHuman（"已开局则只看人类位"）
0x0050B73F  test al,al; jne 0x50b750 ; isHuman → 1
0x0050B743  mov al,[ecx+0x1ed]      ; loser 位
0x0050B749  test al,al; jne 0x50b750 ; → 1
0x0050B74D  xor al,al; ret          ; → 0
```
文件字节（file_off=0x10B730）前 32：`a1 38 b2 a8 00 85 c0 8a 81 ec 01 00 00 75 13 84 c0 75 0d 8a 81 ed 01 00 00 84 c0 75 03 32 c0 c3`（与 `FROZEN_DUMP_PARSE_T55H.md` §3.5 留档一致，交叉验证通过）。

`0x0050B730` 共 **141 个 E8 调用者**（`0x0041778F` … `0x007439F7`），遍布 AI/脚本/UI 各域——它是**通用「该屋是否已退场」查询**，不是败北专用门。**Lead 的「Purged 语义」提示在本件中不成立为独立路径**：没有任何调用者把 `0x50B730` 的返回值直接送进 `0x4FC0B0`；`0x4FC0B0` 只有一个调用者 `0x4F8F82`。**勘误**：`0x50B730` 应正名为「IsDefeatedOrIsHuman」（败北或人类）查询，其 `+0x1ED` 分支在已开局（GameType!=0）时**根本不参与**——这正是 T55h 里 h0 的 `+0x1ED==1` 却未被判负的原因（它走的是 `+0x1EC`）。

### 1.7 `0x004FC6D0`（解散 TeamType）反汇编写点

```
0x004FC6D0  sub esp,8; mov eax,[0xa8ec88]         ; TeamType 总数
0x004FC6F1  mov esi,[eax+ebp*4]                    ; TeamType[i]
0x004FC6F6  call 0x70f820                          ; → TeamType.House（+0x2C0→+0x2BC）
0x004FC6FD  mov eax,[esi+0x21c]                    ; TeamType.OriginalHouse
0x004FC703  cmp edi,eax; je 0x4fc727               ; 同屋 → 处理
0x004FC70D  mov eax,[esi+0x2c0]; mov ecx,[eax+0x2bc]; call 0x472330  ; IsHouseAlly?
0x004FC727  cmp edi,[esp+0x10]; jne 0x4fc770       ; 只处理本屋（或盟友）TeamType
0x004FC72D  cmp esi,ebx; je 0x4fc770               ; 跳过刚处理过的
0x004FC731  mov ecx,[esi+0x6c]; mov [esp+0x14],ecx ; 成员计数
0x004FC738  mov ecx,[esi+0x278]; test ecx,ecx; call 0x71ad40          ; 清理
0x004FC747  … call [edx+0x16c]                     ; TaskForce 重新编成
```
语义：把「属于本屋（或其盟友）且当前无家可归」的 TeamType 成员剥离子队——**这是「悬空号 16/80」效应的直接落点**：若 TeamType 的 House 指向已败北屋，其成员在 `0x4FC6D0` 里被强制改判。

---

## §2 为什么 T55 系触发而 T50 不触发

### 2.1 文件级差异（独立全文件 diff 复核）

| 代 | [Units] 行 | [Infantry] 行 | h0 车 | h1(Computer) 车 | h0 兵 | h1 兵 |
|---|---|---|---|---|---|---|
| spawnfix8（T50，`0add791d`） | 3360 | 2240 | 240 | 240 | 160 | 160 |
| spawnfix9（T55h，`92110131`） | 3840 | 2560 | **480** | **480** | **320** | **320** |
| spawnfix10（`5b47ee04`） | 3600 | 2400 | 480 | 240 | 320 | 160 |
| spawnfix10lite（`9e33585c`） | 3480 | 2320 | 360 | 240 | 240 | 160 |

两代除 [Units] 尾部追加 480 行（id 3360–3839，同格复制 h0 240 + Computer 240）与 [Infantry] 尾部追加 320 行（id 2240–2559，同格复制 h0 160 + Computer 160）外**逐字节相同**（含 [Basic]/[Map]/[Houses]/14 国节/[Waypoints]）。**没有 [Triggers]/[TaskForces]/[ScriptTypes]/[TeamTypes] 节**——「TeamType 悬空号 16/80」在地图文件层不存在新增引用，该假说对本差异集**不成立**（INSUFFICIENT 支撑，降权）。

### 2.2 触发条件的行数敏感性：不是阈值，是「清零时刻」

反汇编判据里**没有任何与「行数/总量/1500 上限/MaxUnitCount」直接比较的分支**：
- `0x004F8E86` 门只比 `GameType/frame/Defeated/HouseType+0x1A6/ShortGame` 五个标量；
- `0x004F8F75` 只比累加和 `edi == 0`；
- `0x00A8B270`（MaxUnitCount）与 `0x00822CF4`（UnitCount）**只被 INI dump 路径引用**（`0x005B5180`/`0x005B5BF4` 的 `printf("UnitCount: %d\n")` / `WritePrivateProfileString`），不参与运行时判定——**「总量压垮引擎」假说（H-A）在引擎层被否证**（与 SPAWNFIX9 报告 §0#2 结论一致，本通道给出指令级补强）。

**T50 免疫 / T55 触发的真实机制（行数 → 战斗烈度 → 清零时刻）**：

960 行（T50）时 h1 车辆链从 f15 的 246 起，在 2332 帧观测窗内从未归零（measure_w1 gate units0=971，全程无 def1F5）；1080 行（T55 系）时 h1 车辆链（c5574）单调下降到 f270=242 后于 f300 归零。行数翻倍使同格堆叠（480 格 max 栈 2）把 h1 的战斗烈度推过「在 AI 起建筑前清零」的临界——**判据本身与行数无关，行数只改变「车辆链何时触零」**。这解释了「同配置 ShortGame=no 仍触发」：ShortGame 位只切分支，两分支判据同构（§1.2/§1.4）。

**「记分板时口 00:00:07-00:00:30 极短即触发」的解释**：`0x004F8F87` 后的 `0x004F8F9C` 分支是 `frame % 7 == 0`（`and edx,0x80000007`）时的雷达/UI 刷新，`0x004F9015` 是 100 帧节拍的 AI 生产检查——**游戏内计时由 `0x00A8ED84` 驱动而非挂钟**，f300 在 30fps 下仅 ~10 秒游戏内时间，与记分板时口自洽。

### 2.3 待实测项（不编造）

- `Rules.Arr8E8[1]`（`0x004F8F5A`）在 T55h 局的实际指向与 `+0xDF8` 值：**未实测**（需运行时读 `RulesClass+0x8E8` 双字）。它决定第四项（`list@0x5550` 的哪个指数）是否参与，即「步兵是否也计入判据」。若 `Arr8E8[1]` 非空且其指数计数 >0，则 T55h 的 f300 判定**还需要步兵项为 0**——这与「f300 时 c5588=22 仍被判负」矛盾，故**推定 `Arr8E8[1]==NULL` 或其指数计数为 0**（后者可由 `0x4FC0B0` 的事后清洗解释）。列为下一趟首要探针。

---

## §3 受害者选择机制

### 3.1 循环顺序

`0x004FEBF9`（每帧 AI 主函数）的双层循环：

```
0x004FED6E  mov eax,[0xa83cf0]        ; HouseClass 实例数（本局=4）
0x004FED97  mov ebp,[esp+esi*4+0x3c]  ; 每屋的「单位预算」计数（0x4FECB6 处预填）
0x004FED9B  test ebp,ebp; jle 0x4fee2f ; 该屋无对象 → 跳过整屋
0x004FEDA3  mov edx,[0xa83ce4]        ; HouseClass 指针数组
0x004FEDB7  call 0x4f7870             ; ← HouseClass::AI（含败北自检）
```

**顺序 = `0x00A83CE4` 数组下标序 = 实例化序 = 地图 `[Houses]` 节顺序**（`0=Americans(<human player>)`、`1=Alliance(Computer)`、`2=French`…）。本局仅 4 屋实例化：h0=human(Americans)、h1=Computer(Alliance)、h2=Neutral、h3=Special。

### 3.2 为什么受害的是 h1（T55h）而非 h0

判据 §1.2 的四把锁解释了全部三组实测：

| 实测 | h0（human） | h1（Computer） | h2（Neutral） | h3（Special） |
|---|---|---|---|---|
| `+0x1EC`（isHuman） | **1** | 0 | 0 | 0 |
| `+0x1ED`（loser） | **1** | 0 | 0 | 0 |
| c5574（车辆链）f270 | 364 | 242 | 240 | 240 |
| c5588 f270 | 92 | 92 | 107 | 107 |
| x2F0（CurBuildables） | 0 | 0 | 0 | 0 |
| def1F5 f300 | 0 | **1** | 0 | 0 |

- **h0 不可能先被判负**：f270 时 h0 车辆链 364、步兵 92，均非零；且 `0x004F8EBD` 的 `ShortGame` 门与 `0x004F8EAC` 的 HouseType 门都不排斥它，纯粹是**它还有车**。T55g（h0=360 车）被灭是另一局的不同几何（h0 侧被 480 复制行推到交战带），本报告机制不变：**谁先归零谁死**。
- **h1 被判负的充分条件在 f270→f300 达成**：车辆链 242→0。
- **h2/h3 免疫的结构原因**：`HouseType+0x1A6`。`[Neutral]` 与 `[Special]` 两节在地图里 `PlayerControl=no` 且 `PercentBuilt=100/0`；`0x00500BDD`（`mov [ebx+0x1ed],al`，PlayerControl 读取点）之后的分支与 `0x004F8EAC` 的门共同保证非参战屋跳过。**注**：该门的精确谓词（`+0x1A6` 由哪个字段置位）**未逐指令定谳**，但 h2/h3 全程 def1F5=0 与「门生效」实测一致。

### 3.3 h0/h1 互换受害的来处

不在判据里，而在**地图几何**：sf9 相对 sf8 给 h0 与 h1 **同时**各加 240 车 + 160 兵同格复制行（块 A/B/C/D）。哪一屋被歼取决于哪一屋的复制行把它推入对方射程——T55h 是 h1 侧密度倍增先被清零；T55g 若 h0=360 车且 h0 复制行落在 h1 交战带，则 h0 先归零。**引擎侧完全对称，无屋别偏好**。

---

## §4 `+0x1EC` / `+0x1ED` 真实语义（反汇编写点）

### 4.1 `+0x1EC`（现标签 isHuman —— 基本正确，但需限定）

写入点共两处，全 .text 扫描 `c6 8x ec 01 00 00 01` / `c6 8x ec 01 00 00 00`：

| VA | 指令 | 语境 |
|---|---|---|
| `0x0068AD0C` | `mov byte [edx+0x1ec], 1`（edx=`[0xa83d4c]`=PlayerPtr） | 会话建立时**只给本地玩家屋置 1** |
| `0x0064C9F4` | `mov byte [esi+0x1ec], 0` | 某状态机复位路径清零 |

**语义定谳**：`+0x1EC` = 「本屋由本地人类玩家控制」（local-human-controlled）。`0x0050B73D` 在 `GameType!=0` 时直接把它当 IsDefeatedOrPurged 的返回值，即「已开局时，人类屋永不被判退场」——**这是保护 h0 的第二道锁**（第一道是它还有车）。T55h 实测 h0 `+0x1EC` 自 f15 起恒 1，与「仅 PlayerPtr 被置位」的写入点自洽。

### 4.2 `+0x1ED`（先验标签 loser1ED —— **不准确，需修正**）

写入点：

| VA | 指令 | 语境 |
|---|---|---|
| `0x0068AD18` | `mov byte [eax+0x1ed], 1`（eax=PlayerPtr） | **与 `+0x1EC` 成对、同一基本块、同一目标屋** |
| `0x00500BDD` | `mov byte [ebx+0x1ed], al` | `0x00500B40`（House 读取函数）中：`al` = `0x005295F0` 读 `[Skirmish]`/house 节 `"PlayerControl"` 的布尔返回值；随后 `0x004FC0FF` 一带据此决定是否给本地槽加成 |

**语义定谳**：`+0x1ED` = 「本屋的 PlayerControl 为真」即「本屋是玩家可控槽」（player-controlled slot），**不是 loser/败北位**。`0x0050B730` 只在 `GameType==0`（未开局/菜单态）时才把它纳入退场判据——那是「开局前的占位屋」清理语义。

**勘误（显式）**：
1. 先验把 `+0x1ED` 叫 `loser`（qc151_fields.json 的 `loser1ED` 键名与 note）**命名错误**，实为 player-controlled-slot 标志。不影响任何已判结论（该位在 T55h 对 h1 恒 0，从未参与判定）。
2. `FROZEN_DUMP_PARSE_T55H.md` §3.5 把 `0x0050B730` 称为「IsDefeatedOrPurged 假说」并称「Purged 语义=规则清除」——**该函数名与 Purged 语义均不成立**：它是 `IsDefeatedOrIsHuman`，且 `0x4FC0B0` 无第二调用者。保留其字节基线（已验证一致），弃其命名与「另有 Purge 路径」推论。
3. 先验「四链表计数全零」的判读需补一层：`0x4FC0B0` 的 `0x4FC179-0x4FC1AE` 在判定**后**执行清洗，故判据达成时可以有非零链（T55h f300 的 c5588=22），清洗后归零。**「判定时四链全零」是错的，「判定时车辆侧三链+建筑计数为零」才对。**

### 4.3 `0x004FC0B0` 内联的同族逻辑

`0x004FC0D7-0x004FC0FB` 与 `0x004FC163-0x004FC1B0` 两处把 `0x50B730` 的逻辑**内联展开**（`GameType!=0` → 取 `+0x1EC`；否则 `+0x1EC ∨ +0x1ED`），用于「是否给本地玩家播放 YouHaveLost」。这再次证明 `+0x1ED` 的语义域在「未开局」而不在「败北」。

---

## §5 可判真伪的预测（下一趟该看什么）

### 5.1 判死探针（按优先级）

| # | 探针 | 读取位置 | 预测值 | 若预测错则 |
|---|---|---|---|---|
| P1 | `RulesClass+0x8E8` 双字 → `[eax+8]` → `[+0xDF8]` | VA `0x008871E0`+0x8E8；再解两次 | 本局 `Arr8E8[1] == NULL`（或 `+0xDF8` 指向的指数在 list@0x5550 上计数为 0） | 若非 NULL 且计数 >0，则判据第四项也要求步兵为 0 → 「f300 时 22 步兵仍被判负」无法解释，须重开 §1.3 分析 |
| P2 | `HouseType+0x1A6`（h0/h1/h2/h3 四屋的 `[H+0x34]+0x1A6`） | VA `HouseClass+0x34` → `+0x1A6` | h0/h1 = 0，h2/h3 = 1 | 若 h2 或 h3 = 0，则 §3.2 的「h2/h3 免疫结构原因」崩塌，需另找免疫机制 |
| P3 | `SessionClass+0x14B6` 与 `0x00A8B262` | 两个地址对读 | 恒等（=ShortGame=no → 0） | 若不等，则 `0x52D1F5` 的拷贝时序有变，ShortGame 分支选择需重勘 |
| P4 | h1 车辆链触零的**精确帧**（30 帧步进 latch 加密到逐帧） | `HouseClass+0x5574` | 落在 (270, 300] 开区间内，且 `def1F5` 在同一帧或紧随其后置 1 | 若 def1F5 领先于车辆链归零，则存在另一判据（如 `0x4F8EC6` ShortGame=yes 分支被意外选中） |
| P5 | `0x00A8B230` 的 `byte[1] & 0x08`（清洗循环前置条件） | SessionClass | = 0x08（置位） | 若未置位，则 `0x4FC179` 清洗不执行 → f373 的 22 步兵清零需另找路径 |

### 5.2 对既有验收判据的修正建议（供 spawnfix10 复掷采纳）

- `SPAWNFIX9_FREEZE_ANALYSIS.md` §6 判据 5/6 用 `h1_c5574` / `h1_def1F5` 恒 >0 / 恒 0——**口径正确，建议补一条**：同时 latch `h1_c5588`（步兵链）与 P1 探针；若 `c5574>0` 但 `def1F5==1`，说明判据走了步兵/建筑项，机制理解需更新。
- 判据 7「Computer 侧亡失数 << 712」**保留但降权**：亡失数是战斗结果不是触发条件；即使 sf10 让 h1 免于清零，也不保证亡失数 <50%（几何未变，只密度回到 1×）。
- 新增可判项：**f300 前后 h1 的 `x2F0` 与 `HouseType+0x1A6`**——若 sf10 后 h1 仍被判负但 `x2F0>0`（起了建筑），则判据被建筑计数挡住，是「AI 起建筑早晚」问题而非密度问题，修复方向应改为提前给 AI 建筑而非删行。

### 5.3 明确不成立/待实测清单

- **不成立**：`0x0050B730` 是 Purge 规则清除路径（无调用者连到 `0x4FC0B0`）。
- **不成立**：总量/行数/MaxUnitCount/1500 上限进入触发条件（`0x00A8B270`/`0x00822CF4` 仅 INI dump 引用）。
- **不成立（对本差异集）**：TeamType 悬空号 16/80 的成员数效应（两代地图均无 [TeamTypes]/[TaskForces]/[ScriptTypes] 节）。
- **不成立**：`+0x1ED` 是 loser/败北位（实为 player-controlled-slot）。
- **待实测**：P1（`Rules.Arr8E8[1]`）、P2（`HouseType+0x1A6` 精确置位来源）、`0x004FC179` 清洗循环在非 MP 局是否执行（`SessionClass[0]` 的 `ah&8` 语义）。

---

## 附：关键地址速查（8 位十六进制）

| 项 | 值 |
|---|---|
| HouseClass::AI（宿主函数） | `0x004F7870` … `0x004F8361` |
| 败北自检门 | `0x004F8E86` |
| 常规判定（ShortGame=no） | `0x004F8F21` → `0x004F8F79` |
| ShortGame=yes 判定 | `0x004F8EC6` → `0x004F8F11` |
| 解散 TeamType | `0x004FC6D0` |
| MPlayer_Defeated（败北处理） | `0x004FC0B0` |
| 清洗本屋 TeamType 成员循环 | `0x004FC179` – `0x004FC1AE` |
| IsDefeatedOrIsHuman（先验误名 IsDefeatedOrPurged） | `0x0050B730` |
| 每帧 AI 主入口 | `0x004FEBF9` |
| GameType 全局 | `0x00A8B238` |
| frame 计数器 | `0x00A8ED84` |
| ShortGame 全局 | `0x00A8B262` |
| SessionClass | `0x00A8B230` |
| PlayerPtr | `0x00A83D4C` |
| HouseClass 指针数组 | `0x00A83CE4` |
| HouseClass 实例数 | `0x00A83CF0` |
| RulesClass | `0x008871E0` |
| RulesClass+0x8E8（败北判据第四项数组） | `0x008872C8` |
| RulesClass+0xB24（ShortGame 分支数组） | `0x00887204` |
| TeamType 总数 / 数组 | `0x00A8EC88` / `0x00A8EC7C` |
| 链表 Count 取数 | `0x0049FB60` |
| 链表按指数取数/扩容 | `0x0049FAE0` |
| INI 布尔读取器 | `0x005295F0` |
| `+0x1EC=1` 写入点 | `0x0068AD0C` |
| `+0x1ED=1` 写入点 | `0x0068AD18` |
| `+0x1ED` 由 PlayerControl 写入 | `0x00500BDD` |
| `+0x1EC=0` 清零点 | `0x0064C9F4` |
| 键名字符串 `ShortGame` | `0x0083CFA8` |
| 键名字符串 `PlayerControl` | `0x00824E28` |
| 日志 `MPlayer_Defeated: frame %d, house id %d, MapIsClear set to true` | `0x00824B84` |
| 日志 `MPlayer_Defeated() - Player %s has been defeated (OBIWAN MODE)` | `0x00824BC8` |
| 日志 `MPlayer_Defeated() - Alive = %d, Humans = %d` | `0x00824B0C` |
| 源码路径 `D:\ra2mdpost\House.CPP` | `0x00824724` |

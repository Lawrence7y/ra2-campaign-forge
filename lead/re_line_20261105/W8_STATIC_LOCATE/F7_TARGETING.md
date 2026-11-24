# W8 · F7 回件 · 索敌执行计数 / 限频计时器

```
被核对象 = gamemd.exe（+ TASK.md §1 所列五份前置件：D17_STATIC_FIELDS / D20_B_VISIBILITY_GAP /
           Q1_C2_RENDER / Q1_C3C4_PHYS_TARGET / card_00A8EC34；另只读参考
           docs/re/targeting_spatial.md、docs/re/house_team_ai_update.md、ra2tool.py）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（本人实算，
           探针 hashlib 全文件计算，且与 ra2tool.EXPECT_SHA 断言一致）
字节数 = 4,825,360（本人实算 len(eng.raw)）
Engine 自证 = COVERAGE 99.99837567729335%（1,394,120 条指令 / 重同步 66 次 / .text 4,063,232 字节）
           / IMAGEBASE 0x400000
回件时刻 = 2026-11-06 01:22（探针 01:03:07 启动，104.4 s 跑完，退出码 0）
```

探针：`_w8_f7.py`（本目录），复现命令
`python -I -X utf8 _w8_f7.py > _w8_f7_out.txt 2>&1`（在 W8_STATIC_LOCATE 目录内执行），
输出 `_w8_f7_out.txt`（1,626 行，EXIT=0）。探针零写盘（stdout 由 shell 重定向）、零真机、零注入、
只读 `ra2youli/gamemd.exe` 磁盘镜像。文中标「补跑」的反汇编为会话内以同法
（`python -I -X utf8` + `ra2tool.Engine`）补做的小片段，均给出 `地址 + 原始字节` 可独立复跑。

## 0. 一句话总判

**0x6FB010 = 弹药装填推进器（UpdateReload 语义）——独立复核成立**（INI 键链字节定谳）；
**0x6F8DF0（Greatest_Threat）的直接调用者恰 2 个**（`0x445F68`、`0x4D9942`），两个包装函数体内**无任何帧限频**；
14 个 v[241] 虚派发点中**恰 1 个带真帧取模门**（`frame % 14`，计数器 = 全局 `CurrentFrame 0xA8ED84`，
周期 = RulesClass 构造器常量 0.016×900，非 INI 键）+ 1 个状态门（`[this+0x2B4]==0`）；
**「索敌执行计数」（完成扫描口径）无现成全局累加器 → 未定位**——全路径唯一全局累加器是
`0x00A8EC34`，但它是 D-19 已定谳的「**入口**调用累计代理」（含早退，早退在写回之后），
按 TASK §1.5 属「另一个字段」，不充当 F7 答案。

**判定：UNLOCATED**（限频「计时器字段」与执行「计数器字段」在 vanilla 镜像中均不存在可读 VA；
本回件给出的是字节级排除 + 相邻机制的完整定谳，见 §5）。

---

## 1. 问一 · 独立复核「0x6FB010 是 UpdateReload 不是索敌」

**结论：成立，且证据链比 C3C4 报告更完整（INI 键绑定全部亲验）。**

### 1.1 函数体字节（探针输出 `_w8_f7_out.txt:948-996`，E 段 disasm 0x6FB010）

```asm
006FB014  8B 06                 mov eax, [esi]            ; vtable
006FB016  FF 90 84 00 00 00     call [eax+0x84]           ; GetType() → TechnoTypeClass*
006FB01C  8B 80 84 06 00 00     mov eax, [eax+0x684]      ; ★ type->Ammo（§1.2 证）
006FB022  83 F8 FF              cmp eax, -1
006FB025  74 47                 je 0x6FB06E               ; ★ Ammo==-1 → 直接跳函数尾
006FB027  8B BE FC 02 00 00     mov edi, [esi+0x2FC]      ; 当前弹药
006FB02D  3B F8                 cmp edi, eax
006FB02F  7D 3D                 jge 0x6FB06E              ; 已满 → 退出
006FB031  8B 96 FC 01 00 00     mov edx, [esi+0x1FC]      ; ReloadTimer.Start
006FB037  8B 86 04 02 00 00     mov eax, [esi+0x204]      ; ReloadTimer.Duration
006FB042  8B 0D 84 ED A8 00     mov ecx, [0xA8ED84]       ; CurrentFrame
006FB04A  3B C8                 cmp ecx, eax              ; (帧差) >= Duration ?
006FB04C  7D 06                 jge 0x6FB054
006FB050  85 C0                 test eax, eax
006FB052  75 1A                 jne 0x6FB06E              ; 未到期 → 退出
006FB056  47                    inc edi                   ; 弹药 +1
006FB05B  89 BE FC 02 00 00     mov [esi+0x2FC], edi      ; 写回
006FB061  FF 92 24 01 00 00     call [edx+0x124]          ; v[73](2)
006FB069  E8 12 00 00 00        call 0x6FB080             ; 重算装填周期
006FB06E  5F 5E C3              pop edi / pop esi / ret   ; 早退目标 = 函数尾
```

- `je 0x6FB06E` 的目标 0x6FB06E 实为 `5F 5E C3` 序言，**Ammo==-1 的单位每次进入 8 条指令内退出**
  （C3C4 报告称「第 5 条指令」，按指令计数实为第 8 条——计数口径小误，字节结论不变）。
- 函数体 [0x6FB010, 0x6FB070] 内的全部调用只有：GetType、v[73]、0x6FB080——**零扫格、零威胁评估、
  零 `call 0x6F8DF0`**。它不是索敌函数。
- v[73] 落点亲验：`u32(0x7F5D94)=0x4D3780`（Unit）、`u32(0x7EB17C)=0x4D3780`（Infantry）、
  `u32(0x7E8DB8)=0x4D3780`（Foot）——0x4D3780 头部 `83 FF 02 cmp edi,2` → `B0 01 mov al,1; ret 4`
  （探针输出 1092-1110 行）：**实参为 2 时不做任何事直接返回 1**。与 C3C4 §2.1(3) 一致
  （TechnoClass 自身 v[73]=0x6F4A70 不同、Building/Aircraft v[73] 未验，见 §7）。

### 1.2 INI 键绑定（决定性证据，全部亲验字节）

探针 C5 段（`_w8_f7_out.txt:859-864`）+ G 段（:1619-1624）+ E 段 LoadFromINI 窗口（:1504-1605）+ 补跑：

| TechnoTypeClass 偏移 | INI 键字符串 VA | 字符串实字节 | 绑定点（LoadFromINI 内） |
|---|---|---|---|
| **+0x684** | 0x81BBE0 | `b'Ammo'` | `0x71476D 68 E0 BB 81 00 push 0x81BBE0` → `0x71477A 89 85 84 06 00 00 mov [ebp+0x684],eax` |
| +0x698 | 0x843A5C | `b'Reload'` | `0x714871 push 0x843A5C` → `0x71487E mov [ebp+0x698],eax` |
| +0x69C | 0x843A50 | `b'EmptyReload'` | `0x71488B push 0x843A50` → `0x714898 mov [ebp+0x69C],eax` |
| +0x6A0 | 0x843A40 | `b'ReloadIncrement'` | `0x7148A5 push 0x843A40` → `0x7148B2 mov [ebp+0x6A0],eax` |
| +0x3E4 | 0x843DB8 | `b'PipWrap'` | `0x714180 push 0x843DB8` → `0x714198 mov [ebp+0x3E4],eax`（补跑） |

五个键的 imm 引用**全镜像各恰 1 处**，全部落在 TechnoTypeClass::LoadFromINI 区间，绑定偏移与
0x6FB010/0x6FB080 的读取偏移一一对应。⇒ **type+0x684 = Ammo（弹容上限），this+0x2FC = 当前弹药，
this+0x1FC/+0x204 = 装填计时器**。

### 1.3 0x6FB080 = 装填周期公式（探针输出 1034-1091 行）

- `[this+0x2FC]==0` 且 `type+0x69C != -1` → 用 **EmptyReload**（0x6FB0B0 `83 B8 9C 06 00 00 FF`）；
- 否则 `Duration = Reload(+0x698) + ReloadIncrement(+0x6A0) × (Ammo(+0x2FC) ÷ PipWrap(+0x3E4))²`
  ——0x6FB116 `F7 B9 E4 03 00 00 idiv [ecx+0x3E4]`、0x6FB130/0x6FB135 两条 `0F AF FB imul edi,ebx`
  即平方项。这正是 YR 规则里「按消耗弹药数平方放大的装填时间」机制。

### 1.4 0x6FB010 的调用拓扑（探针 B/C1/C2 段）

- 直接 E8 调用者恰 **1**：`0x736D3E`（`e8 cd 42 fc ff`）——位于 UnitClass v[265] 包装函数
  0x736CA0..0x736D48（`u32(0x7F6094)=0x736CA0`）尾部。
- 虚派发点恰 **1**：`0x736689`（`ff 90 24 04 00 00` = `call [eax+0x424]`，v[265] 槽；
  `u32(0x7F4D84)=0x6FB010`）。派发宿主 0x736664..（补跑）仅在派发前查
  `type+0xE18 / type+0xE19` 两个字节（键名未验），**无条件**每轮派发——即装填推进按帧轮询，
  弹容无限的单位在 0x6FB025 早退。

### 1.5 ★ 对 `docs/re/targeting_spatial.md` 误标的独立裁定

该文件称 0x6FB010 为「**限频调度器**」（:16、:111 起），把 `+0x2FC` 读作「扫描计数器」、
`+0x1FC` 读作「扫描定时器 StartTime」（:318-323）。**与字节不符**：
`+0x2FC` 是当前弹药（§1.2 键链 + 0x6FB056 的 `inc` 语义）、`+0x1FC/+0x204` 是装填计时器
（§1.3 的 Reload/EmptyReload/ReloadIncrement/PipWrap 公式）。0x6FB010 **不是索敌入口、
也不含任何引擎侧 8 帧哈希节流**——`targeting_spatial.md:145` 所述「L2 的 8 帧哈希节流作用在调度器上」
是 `ra2render.dll` Hook 层行为（`blitter_hooks.cpp:1362-1364`，card_00A8EC34 §6.2 已引），
磁盘镜像内不存在对应字节。**台账 §566 的误标判断：独立复核后维持。**

---

## 2. 问二 · 0x6F8DF0（Greatest_Threat）的全部直接调用者

**双通道普查（探针 B 段裸字节上界扫 + C1 段重同步解码流），两法结果一致：**

| # | 调用点 VA | 字节 | 所在函数（边界亲验） | 身份 |
|---|---|---|---|---|
| 1 | **`0x445F68`** | `E8 83 2E 2B 00` | 0x445F00..0x445F6F（头前 `90 90 90 90`，尾 `C2 0C 00 ret 0xC`） | BuildingClass v[241] 包装（`u32(0x7E4280)=0x445F00`） |
| 2 | **`0x4D9942`** | `E8 A9 F4 21 00` | 0x4D9920..0x4D995C（头前 `90 90 90 90`，尾 `C2 0C 00`） | FootClass v[241] 包装（`u32(0x7E9058)=0x4D9920`） |

- **E9 jmp 直跳：0 处**（裸扫 + 解码流双 0）。无第三个直接调用者。
- 虚派发（`call [reg+0x3C4]`，v[241] 槽）：**恰 14 处**（探针 C2，:60-74）：
  `0x414B24, 0x414B64, 0x417481, 0x4D4314, 0x4D4686, 0x4D49A3, 0x4D4E3E, 0x4DE056, 0x50D1D2,
  0x51F382, 0x6ECE06, 0x6ED15E, 0x6F0253, 0x709932`——与 card_00A8EC34 §4 记载的 14 独立一致。
- 虚表槽亲验（探针 F 段，:1607-1613）：Techno v[241]=`0x6F8DF0` 本体；Foot=`0x4D9920`、
  Infantry=`0x51E140`、Building=`0x445F00`、Unit=`0x743190` 四个包装。
- 包装级联（全部 E8 亲验）：Unit v[241] `0x743190` —`0x74325C`→ FOOT 包装；
  Infantry v[241] `0x51E140` —`0x51E39F`→ FOOT 包装（Owner+0x54E0 共享目标快路径失败后的回落，
  快路径结构见探针 1399-1415 行）。
- C3C4 报告的链 `UnitClass::v[151] @0x740B10 → 0x4D4280 → 0x4D9920 → 0x6F8DF0` **独立复核成立**，
  并补两处精确化：`u32(0x7F5ECC)=0x740B10`（UnitClass vtable+0x25C=v[151]，补跑）；
  0x4D4280 进入 GT 走的是 `call [edx+0x3C4]`（0x4D4314，`6A 02 push 2` 实参），非直调。

---

## 3. 问三 · 这些调用者里是否存在帧限频

### 3.1 两个直接调用者：**无门**（字节级）

- **Building 包装 0x445F00..0x445F6F**（探针 1113-1155 行）：直线代码——4 次 `call [v+0x3F8]`
  （v[254]，TargetFlags 查询）+ 2 次 `call 0x772A90` + `or edi,…` 合并标志，然后
  无条件 `call 0x6F8DF0`。**0 个 `test/and ×7`、0 次 CurrentFrame 读、0 个计时器。**
- **Foot 包装 0x4D9920..0x4D995C**（探针 1156-1180 行）：读 `+0x688` 标志字节、按其改写实参
  `and al,0xFD / or al,1`，无条件 `call 0x6F8DF0`，返回后按结果清 `+0x688`。**无门。**
- 探针 D 段对两个包装的整函数窗口扫描（:898-899）：`test-and-imm7=0 absdwordWR=0 CurrentFrame-read=0`。

### 3.2 14 个虚派发窗口普查（探针 D 段，:879-896）

启发式函数起点（最近 `ret/int3` 边界）+ 全窗扫描：**12 个窗口三类特征全零**；
仅两个窗口含 CurrentFrame 读（下两小节逐一裁决）。

### 3.3 真帧门 #1 · 派发点 `0x6ECE06` 宿主（~0x6ECCE0 起）的 `CurrentFrame % 14` 门

（会话补跑，字节逐条给出；「PAD before 0x6ECCE0 = `5d c2 08 00`」证上一函数 ret 8 止于 0x6ECCDF）

```asm
006ECD40  8B 15 E0 71 88 00     mov edx, [0x8871E0]       ; Rules 单例
006ECD46  DD 82 50 11 00 00     fld qword [edx+0x1150]    ; Rules+0x1150（double）
006ECD4C  DC 0D F8 27 7E 00     fmul qword [0x7E27F8]     ; × 900.0（该常量实测=900.0）
006ECD52  E8 A9 91 0D 00        call 0x7C5F00             ; double→int ⇒ N
006ECD59  A1 84 ED A8 00        mov eax, [0xA8ED84]       ; ★ 计数器 = CurrentFrame 全局
006ECD5E  99                    cdq
006ECD5F  F7 F9                 idiv ecx                  ; frame ÷ N，余数→edx
006ECD61  85 D2                 test edx, edx
006ECD63  0F 85 BE 00 00 00     jne 0x6ECE27              ; ★ 非整除 → 整块跳过（不派发）
```

- 通过门后：沿 `[edi+0x54]` 链表（节点步进 `+0x5D8`）按 `type+0x5FC` 取最大者，
  **只挑 1 个对象**派发 v[241]（0x6ECE02 `push 1` → 0x6ECE06）。
- **周期 N 的来源**：`Rules+0x1150` 是 double，全镜像 `[reg+0x1150]` 写点恰 1 处 =
  RulesClass **构造器** `0x666E09 C7 86 50 11 00 00 FC A9 F1 D2`（低 dword）+
  `0x666E1A C7 86 54 11 00 00 4D 62 90 3F`（高 dword）⇒ 默认值 = **0.016**；
  `N = int(0.016 × 900.0) = 14`。**它不是 INI 键**（无 LoadFromINI 写点），周期是编译期常量。
- 宿主函数唯一直接调用者：`0x6E962A`（`e8 b1 36 00 00`，补跑）——一个 switch 型分发的 case 尾块
  （0x6E961E..0x6E9636；同族 case 还转发 0x6EC9A0/0x6ECE60），switch 宿主函数身份未深究（§7）。
- **口径**：这是 **House 级宏观调度门**（每 14 帧给 1 个对象派一次 Greatest_Threat），
  不是「微观索敌节流」；门的对象是「挑谁去索敌」，不是「索敌做多少活」。

### 3.4 派发点 `0x709932` 宿主 = **v[231] 共享函数 0x709820**：帧戳 + 状态门

（裸 dword 全文件扫：0x709820 出现于 Techno/Unit/Foot/Infantry/Building 五张虚表
`+0x39C = vslot 231`，另 1 处 0x7E2640 未归属）

- 函数头第一条指令即 `0x709820 A1 84 ED A8 00 mov eax,[0xA8ED84]`，随后
  `0x70982E 89 86 FC 04 00 00 mov [esi+0x4FC],eax`、`0x70986C/0x7098A2 mov [esi+0x180],edx`
  ——这是把当前帧**戳**进实例字段（本帧已处理标记类用法），**不是比较门**。
- 真正的派发门是状态比较：`0x709918 8B 86 B4 02 00 00 mov eax,[esi+0x2B4]` →
  `0x70991E 85 C0 test eax,eax` → `0x709920 0F 85 92 00 00 00 jne 0x7099B8` →
  **仅当 `[this+0x2B4]==0` 才在 0x709932 `call [eax+0x3C4]`**（实参 `6A 00 push 0`）。
  `[+0x2B4]` 的字段名未验（§7）；它是实例指针/计数的判空门，**不是帧限频**。
- `0x7098B3 83 E7 03 and edi,3` 作用在**入参**上（选实参槽位），与帧无关。

### 3.5 House 级节奏门（对照 C3C4「8 帧/100 帧在 HouseClass::Update」说法的独立复核）

- **`% 8` 门：存在，实址 0x4F8F8D..0x4F8F9C**（会话补跑，探针 D 段 imm∈{7,-8} 扫描为何没报它——
  因为编译器用的是**带符号取模惯用法**，立即数是 0x80000007）：

  ```asm
  004F8F87  8B 15 84 ED A8 00   mov edx, [0xA8ED84]      ; ★ 计数器 = CurrentFrame
  004F8F8D  81 E2 07 00 00 80   and edx, 0x80000007      ; signed % 8 惯用法
  004F8F93  79 05               jns 0x4F8F9A
  004F8F95  4A                  dec edx
  004F8F96  83 CA F8            or edx, 0xFFFFFFF8
  004F8F99  42                  inc edx
  004F8F9A  75 22               jne 0x4F8FBE             ; frame % 8 != 0 → 跳过
  004F8F9C  8B 7E 48            mov edi, [esi+0x48]      ; ==0 → 逐项 call 0x6E53A0（建筑回调）
  ```

  即 **`frame & 7` 型节奏门确实存在，计数器 = 全局 `0x00A8ED84`（CurrentFrame）本身**——
  但它门的是建筑回调（0x6E53A0）及后续 AI 招募，**不直接门 Greatest_Threat**。
  C3C4 称「0x004F8F9C: test cl,7」——地址对、语义对，助记形式不对（实为
  `and edx,0x80000007` 惯用法，`test cl,7` 字节 `F6 C1 07` 在该址不存在）。
- **「%100 门」：字节上不成立。** 0x4F8DD3..0x4F8E21 实为一个 **per-house CDTimer**：
  `HouseClass+0x57A4`（Start）/`+0x57A8`/`+0x57AC`（Duration），
  到期重装 `0x4F8E0A B8 5A 00 00 00 mov eax,0x5A` → `0x4F8E1B mov [esi+0x57AC],eax`
  ——**Duration = 0x5A = 90 帧**，不是 `CurrentFrame % 100`。
  且 C3C4 所引「0x004F8E24: test eax,eax」在该址**根本不能解码**（0x4F8E24 落在指令
  `0x4F8E21 C7 86 46 02 00 00 00 mov byte [esi+0x246],0` 内部）——该报告此处是错位反汇编产物。
  机制修正：House 级第二层限频是「90 帧时长计时器」，非帧取模。（此修正属 C3C4 报告勘误，
  不改 F7 主判。）

### 3.6 索敌路径上的邻近计时器：**都在维护节拍，都不设门**

1. **Unit v[265] 包装 0x736CA0**（0x6FB010 的唯一宿主，探针 1182-1242 行）：
   `type+0x6AE` 字节为 0 时进入「装填延期」块——读 `+0x1FC/+0x204` 对 CurrentFrame，
   未到期则重装 `Duration = 剩余+1`（0x736D27 `8D 41 01 lea eax,[ecx+1]`）并把实参存 `+0x200`；
   **两条路径都落到 `call 0x6FB010`**——它推迟装填到点，不拦截调用。
2. **UnitClass v[151] `0x740B10`**（探针 1377-1398 行 + 补跑）：`lea edi,[esi+0x350]` →
   `call 0x4A51D0`（查 `+0x350` 对象内 `+0x18/+0x19` 两标志，全 0 才返 1）→ 未清则
   `call 0x4A5240`（把 **CurrentFrame 戳进 `+0x350` 对象 `+0x8`**、存入
   `type+0x3C8`/`type+0x3CC` 两参）→ **无条件 `call 0x4D4280`**（→v[241]→Greatest_Threat）。
   `TechnoClass+0x350` 是帧戳式计时器对象（C3C4 诚实账猜的「索敌冷却计时器」——
   字节上它存在、随 v[151] 刷新，但**在此调用链上不构成门**；其门控效果（若有）在其他读者，
   本轮未追踪，见 §7）。
3. `0x4D4280`（v[241] 派发宿主之一）：`[esi+0xBC]` 状态机 switch + `[esi+0x430]=1` +
   `[esi+0x5A4]` 判空——状态分发，无帧门（探针 1280-1311 行 + D 段窗口 :900）。

**问三小结**：直接调用者（2 个包装）**零帧限频**；14 个派发点中 1 个有 `CurrentFrame % 14`
宏观门（计数器 = `0xA8ED84`，周期 = 构造器常量 14，非 INI）、1 个有 `[this+0x2B4]==0`
状态门、其余 12 个无门。**Greatest_Threat 的进入路径在 vanilla 镜像里没有针对索敌本身的
帧限频计时器字段**——C3C4「微观索敌函数本身零 8 帧/100 帧限频」的结论在调用者侧同样成立。

---

## 4. 问四 · 「索敌执行计数」的现成全局累加器

**结论：未定位（不存在「完成扫描口径」的现成计数 VA）。**

### 4.1 全路径唯一的全局累加器 = `0x00A8EC34`，但它是「入口累计」，不是 F7 答案

本人独立复现（探针 C3/C6 段，:79-81、:866-875）：

- `disp=0xA8EC34` 的绝对访存**恰 2 条**：
  `0x6F8DF3 8B 15 34 EC A8 00`（R，读旧值）→ `0x6F8E04 42 inc edx` →
  `0x6F8E09 89 15 34 EC A8 00`（W，写回）——与 card_00A8EC34 §3 一致。
- **Greatest_Threat 体内 [0x6F8DF0,0x6F9DB0) 的绝对地址 dword 写恰 1 条**（就是上面的写回）；
  disp∈[A8EC30,A8EC38) 的全 .text 写恰 1 条；两个直接包装函数全局写 = 0。
- 入口→写回之间无 `jcc/cmp/test/call`（0x6F8DF0..0x6F8E09 逐条见探针 998-1028 行），
  早退 `0x6F8E41 C2 0C 00 ret 0xC` 在写回**之后**（`type+0xD20` 标志 + `0x50B730(Owner)` 双查，
  `0x50B730` 为 Gamemode×House 旗标谓词，补跑）。
- 全镜像无第三条访存 ⇒ 无业务读点、无递减、无比较——「重入计数」标签（targeting_spatial.md:167、
  :387）再次证伪；语义 = **「进入 Greatest_Threat 的次数」累计**（D-19 定谳措辞「索敌入口调用
  累计代理」）。按 TASK §1.5，此字段与 F7 **不许混淆**：它把「house 已出局早退」也计为 1 次，
  且对 `ra2render.dll` 节流帧会被整次跳过（card §6.2）。

### 4.2 排除清单（查了什么、为什么排除「执行计数」累加器的存在）

| # | 排除的路径 | 证据 |
|---|---|---|
| 1 | Greatest_Threat 体内（0xFC0 字节）第二个 `inc/add [全局]` | C6 段：体内绝对 dword 写恰 1（0xA8EC34 写回） |
| 2 | 两个直接包装函数内的全局写 | C6 段：0x445F00..70 与 0x4D9920..5C 各 0 条 |
| 3 | 14 个 v[241] 派发窗口内的全局写 | D 段：每窗 `absdwordWR=0` |
| 4 | v[231] 共享宿主 0x709820（最大派发宿主） | 其头两条写是 `this+0x4FC`/`this+0x180` **实例字段帧戳**（§3.4），非全局 |
| 5 | `0xA8EC34` 的第二个写者 / 邻域别名 | C6 段：disp∈[A8EC30,A8EC38) 写恰 1 条（同点） |
| 6 | 0x6FB010（装填器，若误标为索敌入口时它自己的计数器） | 它的自增在 `this+0x2FC` 实例字段（0x6FB056），非全局 |

**未穷尽（不冒充穷尽）**：绝对 disp 普查不覆盖①经寄存器中转的 `mov [reg],reg` 型全局写、
②`rep movsd`/`memset` 整块拷贝、③GT 体内经 call 下沉的子例程内全局写（如 0x412B40 空间桶
查询内部——那是查询结果向量 Count，语义不是执行计数）、④加载期/读档恢复。与 card_00A8EC34 §3.3
同边界，标「未验」。

**判定**：F7 意义上的「索敌执行计数」（完成扫描数 / 成功锁定数 / 扫格工作量口径）**无现成累加器
→ 未定位**；能给的最近似量只有 §4.1 的入口累计代理（另一个字段）与 §5 的遍历推导规格级线索
（`0x709932` 宿主的帧戳 `this+0x4FC` 是「该单位本轮是否已派发过索敌」的实例级候选读量，语义未验）。

---

## 5. 判定档（TASK §4 三选一）

**UNLOCATED。**

- 「索敌执行计数」：**未定位**（§4.2 排除清单）。
- 「限频计时器」：**未定位为字段**——vanilla 镜像中不存在「索敌限频计时器」这个可读 VA；
  存在的是①House 级 `frame % 8` 门（0x4F8F8D，计数器 `0xA8ED84`，门建筑回调/AI）、
  ②House 级 90 帧时长计时器（`HouseClass+0x57A4..57AC`）、③宏观派发门
  `frame % 14`（0x6ECD40..63，计数器同为 `0xA8ED84`，每次只派 1 个对象）、
  ④状态门 `[this+0x2B4]==0`（0x709918..20）。四者**没有一个以「索敌执行」为计数对象的字段**。
- 本判定**不是**「没找到」：四条问题全部给出了字节级答案（§1–§4），
  且对 C3C4 / targeting_spatial / card 三份前置件的相应论断做了独立复核
  （两处维持、两处修正，见 §6）。

---

## 6. 对既有结论的增量

1. **D-17 F7 保持「未定位」**：本轮把它的搜索空间从「SelectAutoTarget/Greatest_Threat 函数体内」
   扩到「全部 2 直调 + 14 虚派发宿主 + House 级门」，答案仍是无现成 VA；
   D-17 观测卡若要索敌口径，只能用 0xA8EC34（入口累计，含早退）或遍历推导。
2. **C3C4 报告两处字节修正**（结论方向不变）：
   a. 「0x004F8F9C test cl,7」实为 `and edx,0x80000007` 带符号取模惯用法（%8 语义成立）；
   b. 「0x004F8E24 每帧 %100 衰减」不成立——实为 `HouseClass+0x57A4..57AC` 的
      **Duration=90 帧** CDTimer，且 0x4F8E24 落在其所引指令内部（错位反汇编）。
3. **C3C4 报告两处补强**：0x6FB010 的 INI 键链（Ammo/Reload/EmptyReload/ReloadIncrement/PipWrap
   → +0x684/+0x698/+0x69C/+0x6A0/+0x3E4）本轮全部亲验落位；「v[151]→0x4D4280→…→0x6F8DF0」
   链补齐了 `u32(0x7F5ECC)=0x740B10` 与 0x4D4280 经 `call [v+0x3C4]` 派发的细节。
4. **targeting_spatial.md 误标维持误标**（§1.5）：0x6FB010 是装填推进器；
   其「+0x2FC 扫描计数器 / +0x1FC 扫描定时器 / 8 帧调度器」三分支读法与字节不符。
5. **新定位（对 C4 成本模型有用的两个入口侧事实）**：
   a. 虚派发宿主 v[231]（0x709820，五类共享）每帧给每个单位打帧戳 `this+0x4FC`，
      且仅当 `[this+0x2B4]==0` 才派 Greatest_Threat——**C4 雪崩假设的入口约束比 C3C4
      假设的「全量并发」更紧**；
   b. 存在一个 `frame % 14` 的 House 级单对象派发门（0x6ECD40..0x6ECE06），
      构成一股与 C4 竞争的、有界的索敌调用源。

---

## 7. 诚实账

**已验（本会话实跑，命令 = 探针 `_w8_f7.py` / 会话补跑片段）**：
SHA256、字节数、覆盖率自证；0x6FB010 全函数字节与全部 5 个 INI 键绑定；0x6FB080 公式；
v[73]/v[241]/v[265] 槽位 u32；0x6F8DF0 直调者=2（裸扫+解码流双通道）、E9=0；
两包装整函数无门；14 派发点窗口三类特征普查；0x6ECE06 宿主 %14 门全字节（含 Rules 常量
0.016×900=14 的构造器双写点）；0x709932 宿主 v[231] 归属（五虚表 +0x39C）与状态门字节；
0x4F8F8D %8 门、0x4F8DD3..21 的 90 帧计时器；0xA8EC34 恰 2 条访存 + GT 体内唯一全局写 +
四个包装零全局写；0x740BED `and ecx,7` 归属排除（不同函数、表索引非帧门）；
0x52DA08/0x68466B 为 CurrentFrame 清零形态写点（场景重置类例程，esi/ebx 经 xor/清块）。

**未验（如实列出，不补造）**：
1. `[this+0x2B4]`（0x709932 门的判空对象）的字段语义与 INI 键名；
2. `type+0x6AE / type+0xE18 / type+0xE19 / type+0x3C8 / type+0x3CC / type+0xD20 / type+0x5FC /
   type+0xE12 / type+0xEC3` 各字节/双字的 INI 键名（本轮只验了 Ammo 系五键）；
3. `TechnoClass+0x350` 计时器对象在其他读者处的门控效果（本轮只证它不门 v[151]→GT 链）；
4. Building/Aircraft 的 v[73] 槽位落点（0x6FB061 对建筑/航空器的实际行为）；
5. 0x6E962A 所在 switch 宿主函数（0x6E9xxx）的身份与它被调的频率；
6. 0x7E2640 处 0x709820 出现的归属（可能为第六张虚表，未解）；
7. 14 个派发窗口的函数起点为启发式（最近 ret/int3 边界），未逐一做 CFG 级确认；
8. 间接别名写 / `rep movsd` / 经寄存器中转的全局写（§4.2 边界，与 card 同）；
9. CurrentFrame 的另外 8 处写形态站点（0x5B7329、0x5BB20C、0x5E550F、0x5E747C、0x68466B、
   0x686765、0x795234、0x79758C）与 D-17 F4「唯一 RMW 链」的关系（F4 范畴，本轮仅抽查 2 处，
   皆清零形态，未逐一裁决）；
10. 12 个无特征派发窗口的宿主函数语义名（本轮只裁「有无门」，未命名函数）。

**纪律**：零真机、零采样代码、零注入、未读活进程；只读 `ra2youli/`、`docs/re/`、`lead/` 既有件；
唯一写入 = 本目录 `_w8_f7.py`、`_w8_f7_out.txt`、`F7_TARGETING.md`；未 commit、未 push。

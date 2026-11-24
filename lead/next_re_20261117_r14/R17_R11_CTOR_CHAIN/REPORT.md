# R17-R11-CTOR-CHAIN · 三个 host 的基类构造链（Q1–Q3）

只读 gamemd.exe（ra2youli，ImageBase 0x400000，.text VA/raw 均为 0x1000 起、1:1 平铺；.rdata 0x3E1000）。
反汇编用 capstone，**锚点对齐**：0x6F2B40 前 8 字节 `90` 填充、前函数 0x6F2B34 `c3`；host1 前函数 0x43B67E `c3`；
host2 第一段 0x43B740 由直接 `call` 命中入口、其后段由 `c2` 后接 `6a 01` 锚定；host3 前 `c3`+填充。
**全文不声称任何类名**（三个 host 及 0x6F2B40 的类名均未取得）。

---

## Q0 · 关键前提更正（必须先说）

卡面给的「0x6F322F 是 vtable 写点」**不是一个 vtable store**。字节如下：

```
0x6F3228  8a 46 14            mov  al, byte ptr [esi+0x14]
0x6F322B  8b 54 24 14         mov  edx, [esp+0x14]
0x6F322F  0c 01               or   al, 1          <-- 「写点」实为此指令
0x6F3231  8d be 04 03 00 00   lea  edi, [esi+0x304]
0x6F3237  88 46 14            mov  byte ptr [esi+0x14], al
0x6F323A  b9 08 00 00 00      mov  ecx, 8
0x6F323F  33 c0               xor  eax, eax
0x6F3241  89 96 4c 01 00 00   mov  [esi+0x14c], edx
0x6F3247  f3 ab               rep stosd
```
- 0x6F322F 的字节是 `0c 01`（`or al,1`），它不是立即数 vtable 安装点；它会改 `[esi+0x14]` 的 bit0。
- `0c 01 8d be 04 03` 这一字节序列在 .text 全段**只出现 1 次**（唯一性成立，但唯一性属于这条 or 指令本体）。
- 0x6F2B40 体内的 vtable 安装点是另一组，且**全部不含 2-b 卡面 vtable**：
  `0x6F306A [esi+0x440]=0x7E4E78`、`0x6F3130 [esi]=0x7F4960`、`0x6F3136 [esi+4]=0x7F4944`、`0x6F313D [esi+8]=0x7F493C`、`0x6F314A [esi+0xC]=0x7F4934`。
- 0x6F322F..0x6F3267 属同一函数（0x6F2B40–0x6F3266，尾 `mov eax,esi / ret 4`）；但 0x6F3172 处 `call 0x405BE0` **被 0x6F316C 的 `lea ecx,[esi+0x4dc]` 以 ecx 传入**，故 0x6F3172 不是独立函数入口，不能把 0x6F322F 划给别的函数。

结论：Q1 的「区间是否覆盖 0x6F322F」按**函数区间**判定（0x6F2B40 区间 = [0x6F2B40,0x6F3267)）成立；但 0x6F322F 的「写」是 `or al,1`，**不是 vtable 写**。

---

## Q1 · 三个 host 序言段的全部直接 call

### host1 0x43B680（前 40 条：0x43B680–0x43B73D，共 34 条）
直接 call 仅 1 个：
```
0x43B680  8b 44 24 04      mov  eax,[esp+4]
0x43B684  56               push esi
0x43B685  8b f1            mov  esi,ecx
0x43B687  50               push eax
0x43B688  e8 73 8c 2b 00   call 0x6F4300
...        （全是 mov 立即数初始化，至 0x43B71F）
0x43B71F  c7 06 bc 3e 7e 00   mov dword [esi],0x7E3EBC
0x43B725  c7 46 04 a0 3e 7e 00  mov dword [esi+4],0x7E3EA0
0x43B72C  c7 46 08 98 3e 7e 00  mov dword [esi+8],0x7E3E98
0x43B733  c7 46 0c 90 3e 7e 00  mov dword [esi+0xC],0x7E3E90
0x43B73A  8b c6            mov  eax,esi
0x43B73D  c2 04 00         ret  4
```
判定 `0x6F4300`：**构造器形态 ✓**（入口 `push ebx/ebp;mov ebp,[esp+0xC];push esi/edi;mov esi,ecx`；基类 call 0x65A7E0 @0x6F430B；vt 写 `0x6F4323 [esi+0x1A8]=0x7E180C`、`0x6F4413 [esi]=0x7F4960 / 0x6F4419 [esi+4]=0x7F4944 / 0x6F4420 [esi+8]=0x7F493C / 0x6F4427 [esi+0xC]=0x7F4934`；尾 `0x6F44E9 mov eax,esi / ret 4`）。
区间 [0x6F4300,0x6F44F0) **不覆盖 0x6F322F**。

### host2 0x43B740（前 40 条：0x43B740–0x43B7F5，共 38 条）
直接 call 仅 1 个：
```
0x43B740  8b 44 24 08      mov  eax,[esp+8]
0x43B744  53 55 56 57      push ebx/ebp/esi/edi
0x43B748  8b f1            mov  esi,ecx
0x43B74A  50               push eax
0x43B74B  e8 f0 73 2b 00   call 0x6F2B40      <-- 目标 = 0x400000 + 0x2B73F0
0x43B750 ...              （此后全为 mov 立即数初始化）
```
判定 `0x6F2B40`：**构造器形态 ✓**
- 入口：0x6F2B38–0x6F2B3F 为 8 个 `90`，前一函数 0x6F2B34 `c3` ⇒ 0x6F2B40 是函数入口（不是中段）。
- 基类调用：`0x6F2B46 e8 05 7c f6 ff → 0x65A750`。
- vt 写：见 Q0，含 0x7F4960/44/3C/34 一组（与 host1 基类 0x6F4300 同组）。
- 收尾：`0x6F3260 8b c6 (mov eax,esi) / 0x6F3266 c2 04 00 (ret 4)`。
- 区间 [0x6F2B40,0x6F3267) **覆盖 0x6F322F** ✓（0x6F322F 在其中，字节 `0c 01`）。

⇒ **host2 → 0x6F2B40 这一环，字节证实**（call 目标正中函数入口，且入口前是填充）。

### host3 0x43BCF0（前 45 条：0x43BCF0–0x43BD8A）
直接 call（含间接）共 8 处，**无一具构造器形态**：
```
0x43BCF0  51 53 55 56 8b f1 57     push ecx;push ebx;push ebp; mov esi,ecx; push edi
0x43BCF7  8d be b4 06 00 00        lea  edi,[esi+0x6b4]
0x43BCFD  c7 06 bc 3e 7e 00        mov  [esi],0x7E3EBC
0x43BD05  c7 46 04 a0 3e 7e 00     mov  [esi+4],0x7E3EA0
0x43BD0C  c7 46 08 98 3e 7e 00     mov  [esi+8],0x7E3E98
0x43BD13  c7 46 0c 90 3e 7e 00     mov  [esi+0xC],0x7E3E90
0x43BD1A  e8 41 a3 fc ff           call 0x406060
0x43BD27  e8 34 a3 fc ff           call 0x406060
0x43BD2E  e8 cd 9e fc ff           call 0x405C00
0x43BD35  e8 c6 9e fc ff           call 0x405C00
0x43BD47  e8 34 8d 11 00           call 0x554A80
0x43BD5A  ff 50 20                 call [eax+0x20]
0x43BD67  e8 64 9b 2e 00           call 0x7258D0
0x43BD6E  e8 0d 9b 00 00           call 0x445880
0x43BD87  ff 52 10                 call [edx+0x10]
```
- 0x406060（×2）、0x405C00（×2）、0x554A80、0x7258D0、0x445880：**均非构造器形态**（无 vt 安装写可见、后随 `mov ecx,[esi+0x614]`/`push &[esp+0x10]` 等使用形态），且为**子对象/成员的重初始化**（edi=esi+0x6B4、ebx=esi+0x6A0）。
- 与卡面已判一致：host3 装表 4 写在**最前**（0x43BCFD 起），随后才是成员重初始化；收尾无 `mov eax,esi`。
- 这三个目标（0x406060/0x405C00/0x554A80/0x7258D0/0x445880）是否覆盖 0x6F322F：**未取得（未做区间端点定界）**。

---

### Q0 补 · 0x6F2B40 的收尾形态（纠正一处旧描述）
```
0x6F3247  f3 ab            rep stosd                  ; [esi+0x304..+0x324) 清零（ecx=8, eax=0）
0x6F3249  a1 30 b2 a8 00   mov  eax,[0xa8b230]
0x6F324E  8d 88 18 02 00 00 lea ecx,[eax+0x218]
0x6F3254  e8 27 95 f6 ff   call 0x65C780
0x6F3259  66 89 86 c8 03 00 00  mov word [esi+0x3C8], ax
0x6F3260  8b c6            mov  eax, esi
0x6F3262  5f 5e 5d 5b      pop edi/esi/ebp/ebx
0x6F3266  c2 04 00         ret  4
```
⇒ 0x6F2B40 **确实在 0x6F3260 返回 this（esi）并以 `ret 4` 结束**，与「真构造器」一致。
（前一轮自动扫描把它记成 returns_this=False，是只看 3 条尾部指令所致；此处以字节为准更正。）
## Q2 · 基类构造链

```
host2 0x43B740 --call@0x43B74B--> 0x6F2B40  --call@0x6F2B46--> 0x65A750 --call@0x65A753--> 0x5B2DA0 --ret(链止)
host1 0x43B680 --call@0x43B688--> 0x6F4300  --call@0x6F430B--> 0x65A7E0 --call@0x65A7E8--> 0x5F3B50 --ret(链止)
host3 0x43BCF0 --(首个 call 0x406060 非 ctor)--> 链在此断开
```
每环强度（全部 **字节证实**，依据 = 可见 `e8` 位移精确落到目标入口）：
| 边 | call site | 目标 | 目标形态证据 |
|---|---|---|---|
| host2→0x6F2B40 | 0x43B74B | 0x6F2B40 | 入口前 8×`90`；尾部 `mov eax,esi/ret 4` |
| 0x6F2B40→0x65A750 | 0x6F2B46 | 0x65A750 | 基类 call 0x5B2DA0 @0x65A753；vt 0x65A798 起 `0x7F0508/04EC/04E4/04DC`；尾 `0x65A7D0 mov eax,esi/ret` |
| 0x65A750→0x5B2DA0 | 0x65A753 | 0x5B2DA0 | vt `0x5B2DE9` 起 `0x7EDCC0/DCA4/DC9C/DC94`；`0x5B2E07 ret` 后无 call ⇒ 链止 |
| host1→0x6F4300 | 0x43B688 | 0x6F4300 | 同上（自家 vt 组 0x7F4960/44/3C/34 + 子对象 0x7E180C） |
| 0x6F4300→0x65A7E0 | 0x6F430B | 0x65A7E0 | vt 0x65A7F7 起 `0x7F0508`…；尾 `0x65A812 mov eax,esi / ret 4` |
| 0x65A7E0→0x5F3B50 | 0x65A7E8 | 0x5F3B50 | vt `0x5F3B5D` 起 `0x7EF060/044/03C/034`；`0x5F3B7B ret` ⇒ 链止 |

层数：**可证实的 ctor 边为 3 层**（host → 0x6Fxxxx → 0x65Axxx → 0x5xxxxx），**未连到 TechnoClass 层级**。

第 3 层端点（本轮补证，纠正「无基类 call」这句）：
```
0x5B2DA0  56            push esi
0x5B2DA1  8b f1         mov  esi, ecx
0x5B2DA3  e8 58 0b 04 00 call 0x5F3900        <-- 第 3 层仍有 1 个基类 call（未继续追）
0x5B2DE9  c7 06 c0 dc 7e 00  mov [esi],0x7EDCC0
0x5B2DE9 起 [esi]/[+4]/[+8]/[+0xC] = 0x7EDCC0 / 0x7EDCA4 / 0x7EDC9C / 0x7EDC94
0x5B2E04  8b c6         mov eax, esi
0x5B2E07  c3            ret

0x5F3B50  8b 44 24 04   mov eax,[esp+4]
0x5F3B55  8b f1         mov esi, ecx
0x5F3B58  e8 63 c6 e1 ff call 0x4101C0        <-- 第 3 层仍有 1 个基类 call（未继续追）
0x5F3B5D  c7 06 60 f0 7e 00  mov [esi],0x7EF060
0x5F3B7A  5e            pop esi
0x5F3B7B  c3            ret                   <-- 前置 0x5F3B41..0x5F3B4F 全 90，入口锚点成立
```
⇒ 第 3 层**并非叶子**；只要继续追 0x5F3900 / 0x4101C0 就能再下一层。**本卡按铁律 2 不再展开**，故「连到 TechnoClass 层级」这一问 = **未取得（未连上）**，不是「链已终止」。

**与 TechnoClass 的关系**：0x6F2B40 与 0x6F4300 是两条**互不调用**的平行链（各自 call 表里都没有对方），且两条链在第 3 层分别落到 0x5B2DA0 / 0x5F3B50 两个不同函数 ⇒ 从 host2/host1 出发**看不到指向「TechnoClass 构造器」的独立证据**。若 0x6F2B40 本身即 TechnoClass 构造器（R14_COMMON §2.6 的说法），则 host2 的基类就是它——这一点成立；但**「再往上的 TechnoClass 层级」在字节上并不存在第二条独立边**，因为 0x6F2B40 自己就是被调方。
旁支（同 0x6F2B40 的其他 caller）：`0x4D31EA call 0x6F2B40`、`0x4D3548 call 0x6F4300`（各仅 1 处；连同 host2/host1，0x6F2B40 与 0x6F4300 全镜像各 **2 个** 直接 caller）。

**未取得的链环**：host3 的基类 ctor 未取得；0x5F3900 / 0x4101C0 之下的层未追（超出本卡范围）；「是否连到 TechnoClass 层级」= 未取得。

---

## Q3 · 0x6F322F 与「322 槽段起点 0x7E3EBC」是否同源

**不重合。** 分层给字节：

### 3.1 0x7E3EBC 的写点（全镜像计数 = 3，均落在三 host 序列里）
```
vtable imm32 安装站点计数：0x7E3EBC = 3；0x7E3EA0 = 3；0x7E3E98 = 3；0x7E3E90 = 3
   host1: 0x43B721 [esi]=0x7E3EBC / 0x43B728 [esi+4]=0x7E3EA0 / 0x43B72F [esi+8]=0x7E3E98 / 0x43B736 [esi+0xC]=0x7E3E90
   host2: 0x43B9FC [esi]=0x7E3EBC / 0x43BA03 [ebp] =0x7E3EA0 / 0x43BA0A [esi+8]=0x7E3E98 / 0x43BA11 [esi+0xC]=0x7E3E90
   host3: 0x43BCFF [esi]=0x7E3EBC / 0x43BD08 [esi+4]=0x7E3EA0 / 0x43BD0F [esi+8]=0x7E3E98 / 0x43BD16 [esi+0xC]=0x7E3E90
其余候选（0x7E3EC0 / 0x7E3EC4 / 0x7E3E9C / 0x7E3EA4 / 0x7E3EA8 / 0x7E3EDC / 0x7E3F18）安装站点计数 = 0
```
host2 侧关键几条（**卡面写的「site 0x43B9FF 一带」实际指令起点是 0x43B9FC**，差 3 字节）：
```
0x43B9E8  89 9e 04 07 00 00        mov [esi+0x704], ebx
0x43B9EE  89 9e 14 07 00 00        mov [esi+0x714], ebx
0x43B9F4  89 9e 18 07 00 00        mov [esi+0x718], ebx
0x43B9FA  c7 06 bc 3e 7e 00        mov [esi], 0x7E3EBC      <-- 322 槽段起点写点（host2）
0x43BA00  c7 45 00 a0 3e 7e 00     mov [?],  0x7E3EA0      <-- ModRM=0x45，基址字段非 esi
0x43BA07  c7 46 08 98 3e 7e 00     mov [esi+8], 0x7E3E98
0x43BA0E  c7 46 0c 90 3e 7e 00     mov [esi+0xC], 0x7E3E90
0x43BA15  e8 16 48 fd ff           call 0x410230
```
（0x43BA00 的 ModRM 0x45 若按 `[esi+disp8]`=0x6EA 或按 `[ebp]` 都能读通；本卡不下断言，只记字节。）

### 3.2 0x6F2B40 体内不写 0x7E3EBC
区间 [0x6F2B40,0x6F3267) 内 vtable imm32 安装点**只有 5 个，无一属 0x7E3EBC 族**：
```
0x6F306A  c7 86 40 04 00 00 78 4e 7e 00   mov [esi+0x440], 0x7E4E78
0x6F3130  c7 06 60 49 7f 00               mov [esi],       0x7F4960
0x6F3136  c7 46 04 44 49 7f 00            mov [esi+4],     0x7F4944
0x6F313D  c7 46 08 3c 49 7f 00            mov [esi+8],     0x7F493C
0x6F314A  c7 46 0c 34 49 7f 00            mov [esi+0xC],   0x7F4934
```

### 3.3 判据结论
- 同一 host（host2 0x43B740）既装 0x7E3EBC 段（0x43B9FC），又经 0x43B74B 调进含 0x6F322F 的 0x6F2B40 ⇒ **对象同一**成立。
- 但两处 site **地址不重合、写入目标不同**：`0x43B9FC → [esi]` 装 vtable 段；`0x6F322F → 0c 01` 是 `or al,1`，改 `[esi+0x14]` 标志位。
- 直接回答 Q3：**不重合** —— 不是同一写点、不是同一指令、不是同一子对象。

### 3.4 补充：0x7E3EBC 处不是带 typeinfo 的 vtable 头
`0x7E3EB8=0x7FC360`（前槽，非 .rdata 指针）、`0x7E3EBC=0x410260`。安装写法 `[obj+0]/[+4]/[+8]/[+0xC]` 四段组与之吻合。

---

## 字节行汇总（可直接复核）
```
0x43B688  e8 73 8c 2b 00            call 0x6F4300   (host1)
0x43B74B  e8 f0 73 2b 00            call 0x6F2B40   (host2)
0x43BD1A  e8 41 a3 fc ff            call 0x406060   (host3, 非 ctor)
0x6F2B38  90 90 90 90 90 90 90 90   (0x6F2B40 入口前填充)
0x6F2B40  53 55 56 57 8b f1 e8 05 7c f6 ff   call 0x65A750
0x6F322F  0c 01 8d be 04 03 00 00 88 46 14   or al,1; lea edi,[esi+0x304]; mov [esi+0x14],al
0x6F3260  8b c6 5f 5e 5d 5b c2 04 00         mov eax,esi; ...; ret 4
0x43B9FC  c7 06 bc 3e 7e 00         mov [esi],0x7E3EBC   (host2 内 322 槽段写点)
```

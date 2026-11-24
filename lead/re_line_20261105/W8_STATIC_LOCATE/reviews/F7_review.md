# W8 · F7 回件独立复核（reviews/F7_review.md）

> 复核员：独立复核员·F7（会话实跑，非转抄）。
> 被复核件：`F7_TARGETING.md` + `_w8_f7.py` + `_w8_f7_out.txt`（1,626 行，EXIT=0）。
> 复核探针（本目录，全部只读）：`_f7rev_probe.py`→`_f7rev_out.txt`（570 行）、
> `_f7rev_probe2.py`→`_f7rev2_out.txt`、`_f7rev_probe3.py`→`_f7rev3_out.txt`、
> `_f7rev_probe4.py`→`_f7rev4_out.txt`、`_f7rev_probe5.py`→`_f7rev5_out.txt`、
> `_f7rev_probe6.py`→`_f7rev6_out.txt`（中途崩于我自己的跳转表误读，字节已在崩前打出并据此改正）、
> `_f7rev_probe7.py`→`_f7rev7_out.txt`。复现命令一律
> `python -I -X utf8 _f7rev_probeN.py > _f7revN_out.txt 2>&1`（reviews/ 内执行）。

## 0. 复核总判

**PARTIAL —— F7 的主判「UNLOCATED」维持成立，四问主体全部复核通过；但 §3.3 的
「%14 门周期为编译期常量、非 INI 键」被字节证伪（实为 rules.ini `[AI]`→`PatrolScan` 键），
§1.4 的「v[265] 派发无条件每轮派发」被字节证伪（三条件门控的函数中途汇合点）。两处必须改。**

| # | F7 主张 | 复核结果 |
|---|---|---|
| 1 | 0x6FB010 = UpdateReload（装填推进器，非索敌） | ✅ 成立（§2） |
| 2 | GT 0x6F8DF0 直调者恰 2（0x445F68/0x4D9942）、E9=0、包装零限频 | ✅ 成立（§3） |
| 3 | 14 个 v[241] 派发点、1 个 %14 门 + 1 个状态门、其余无门 | ✅ 站数与字节成立；但 %14 门**周期来源**说法错误（§4-E1） |
| 4 | 「索敌执行计数」无现成全局累加器 → UNLOCATED | ✅ 成立（§5，反例狩猎全部未命中） |
| 5 | SHA256 头部 | ✅ 存在且独立实算一致（§1） |

## 1. SHA256 绑定核验（必查项 ①）

- 头部存在：`F7_TARGETING.md:7-12` 含 SHA256、字节数、COVERAGE、IMAGEBASE、回件时刻——**格式合规**。
- 独立实算（不经 ra2tool）：`_f7rev_probe.py` 用本会话独立 `open()+hashlib.sha256` 对
  `ra2youli/gamemd.exe` 全文件计算 →
  `SHA256(indep hashlib) = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`、
  `FILE_BYTES = 4825360`、`IMAGE_BASE = 0x400000`（`_f7rev_out.txt:2-4`）。
  与 F7 头部及 TASK.md §0 逐字符一致。**通过。**

## 2. 问一复核：0x6FB010 = UpdateReload —— 成立

本会话重跑（`_f7rev_out.txt` F 段 disasm 0x6FB010，0x28 字节）：
`0x6FB014 mov eax,[esi]` → `0x6FB016 call [eax+0x84]`（GetType）→ `0x6FB01C mov eax,[eax+0x684]`
→ `0x6FB022 cmp eax,-1` → `0x6FB025 je 0x6FB06E`（74 47，**Ammo==-1 早退**）→
`0x6FB027 mov edi,[esi+0x2FC]` → `0x6FB02D cmp edi,eax`（对弹容上限）——与 F7 §1.1 逐字节一致。
INI 键链（`_w8_f7_out.txt:1504-1605` 与 G 段 :1619-1624，本会话另验 PipWrap）：
`0x71476D push 0x81BBE0(b'Ammo')` → `0x71477A mov [ebp+0x684],eax`；
`0x714180 push 0x843DB8(b'PipWrap')` → `0x714198 mov [ebp+0x3E4],eax`（`_f7rev_out.txt` F 段）；
Reload/EmptyReload/ReloadIncrement 同构。五键 imm 引用全镜像各恰 1（`_w8_f7_out.txt:859-864`）。
⇒ **+0x684=Ammo、+0x2FC=当前弹药、+0x1FC/+0x204=装填计时器**；targeting_spatial.md 的
「+0x2FC 扫描计数器」误标维持误标，F7 §1.5 裁定正确。
（小疵：F7 §1.1 引文静默略去 0x6FB03D `cmp edx,-1`/0x6FB040 `je`/0x6FB048 `sub ecx,edx` 三条——
探针输出里都在，引文地址本身无误，见 §6-M1。）

调用拓扑复核：`RAW_E8 → 0x6FB010 = {0x736d3e}`、`RAW_E9 = {}`（`_f7rev_out.txt` C 段）；
`call [reg+0x424]` 恰 1 处 = 0x736689（E3 段）；u32(0x7F4D84)=0x6FB010、u32(0x7F6094)=0x736CA0
（G 段）。0x736CA0 包装内「装填延期块」（0x736CDF..0x736D3A）与早路在 0x736D3C 汇合、
同落 0x736D3E 的唯一 `call 0x6FB010`（`_w8_f7_out.txt:1182-1245`）——F7 §3.6.1
「两路径都落到 call、不拦截」成立。

## 3. 问二复核：GT 直调者恰 2、无旁路通道 —— 成立

- 裸扫（.text，含错位）：`RAW_E8 → 0x6F8DF0 = ['0x445f68','0x4d9942']`、`RAW_E9 = {}`；
  解码流双通道同结果（`_f7rev_out.txt` C/E2 段）。**恰 2 个直调者，0 个 E9。**
- **旁路通道狩猎（F7 未做，我补）**：全文件 LE-dword 扫描
  `0x006F8DF0` 全镜像**恰 1 处**（.rdata 0x7F4D24 = Techno 虚表 v[241] 槽，`_f7rev_out.txt` B 段）
  ——不存在第二个表项、不存在 `push 0x6F8DF0`/`mov reg,0x6F8DF0` 型 imm32 物化（E1 段：
  imm32==0x6F8DF0 仅两条 E8 指令自身）。四个包装虚表落点同法各恰 1（Foot 0x7E9058、
  Infantry 0x7EB41C、Building 0x7E4280、Unit 0x7F6034）。
- 两包装全函数反汇编无门：BLDG 0x445F00..0x445F6F 4×`call [v+0x3F8]`+2×`call 0x772A90` 后
  无条件 `call 0x6F8DF0`；FOOT 0x4D9920..0x4D995C 仅 +0x688 标志改写后无条件 call
  （`_w8_f7_out.txt:1113-1180`）。F7 §3.1 成立。
- 14 个 `call [reg+0x3C4]` 站点逐地址与我方普查完全一致（`_f7rev_out.txt` E3 段 vs
  `_w8_f7_out.txt:60-74`）。包装级联 0x74325C/0x51E39F → FOOT 包装（C 段 RAW_E8）成立。
- C3C4 链补强项成立：u32(0x7F5ECC)=0x740B10（G 段）；0x4D4280 经 0x4D4314
  `call [edx+0x3C4]`（`6A 02 push 2`）派发、非直调（`_w8_f7_out.txt:1280-1311`）。

## 4. 问三复核：门与限频 —— 站数成立，**两处说法被证伪**

### 4.1 复核通过的枝节

- **%14 门字节**：0x6ECD40 `mov edx,[0x8871E0]` → 0x6ECD46 `fld [edx+0x1150]` → 0x6ECD4C
  `fmul [0x7E27F8]` → 0x6ECD52 `call 0x7C5F00` → **0x6ECD57 `mov ecx,eax`**（F7 引文略去此条，
  字节存在）→ 0x6ECD59 `mov eax,[0xA8ED84]` → cdq/idiv/test edx/jne（`_f7rev_out.txt` F 段）。
  常量：raw@0x7E27F8=`0000000000208c40`=**900.0**；raw@0x666E09=`c78650110000fca9f1d2`、
  raw@0x666E1A=`c786541100004d62903f` → double=**0.016**；int(0.016×900)=**14**。
  0x6ECE02 `push 1` → 0x6ECE06 `call [edx+0x3C4]`（单点派发）。宿主唯一直调者恰
  0x6E962A（`RAW_E8 → 0x6ECCE0 = {0x6e962a}`）。
- **%8 门**：raw 0x4F8F87..=`8b1584eda800 81e207000080 7905 4a 83caf8 42 7522`
  =`and edx,0x80000007` 带符号 %8 惯用法（`_f7rev_out.txt` H 段）——F7 对 C3C4
  「test cl,7」的勘误成立。
- **90 帧 CDTimer**：0x4F8DD3..0x4F8E21 为 HouseClass+0x57A4/57AC 计时器，
  0x4F8E0A `mov eax,0x5A` → 0x4F8E1B `mov [esi+0x57AC],eax`；0x4F8E21 指令
  `c6864602000000` 覆盖 0x4F8E21..27，**0x4F8E24 落在 disp32 内部**，C3C4 所引
  「0x4F8E24 test eax,eax」字节上不存在（`_f7rev_out.txt` H 段）——F7 勘误成立。
- **0x740BED 归属排除**：0x740B10 函数止于 0x740B50 `ret`（`_f7rev_out.txt` F 段），
  0x740BED 在其后另一函数内，上下文为
  `0x740BE8 mov dx,[eax]` → `0x740BED and ecx,7` → `0x740BF0 add dx, word [ecx*4+0x89F688]`
  ——**表索引，非帧门**（probe4 J 段）。F7 该排除成立（其声称的函数起点 0x740B51
  落在 nop 填充内，实际下一起点 ≈0x740B60——精度小误，见 §6-M4）。
- **0x50B730 谓词**：头 0x30 字节 = 读 0xA8B238（Gamemode）+ House+0x1EC/+0x1ED
  （probe1 F 段）。GT 早退链 `0x6F8E19 → 0x6F8E1F type+0xD20 → 0x6F8E2F call 0x50B730 →
  0x6F8E41 ret 0xC` 且写回 0x6F8E09 在早退之前（`_f7rev_out.txt` F 段）——「早退也计数」成立。

### 4.2 ★ 必须改 E1：%14 门周期是 INI 键，不是「编译期常量」

F7 §3.3/§6.2/§7 称：「全镜像 [reg+0x1150] 写点恰 1 处 = 构造器 0x666E09/0x666E1A……
**它不是 INI 键（无 LoadFromINI 写点），周期是编译期常量**」。

**证伪**（probe2 I 段 `disp_hits_field(0x1150)` + probe4 S 段 + probe5 W 段）：

```
(6712841=0x666E09, 'W', mov dword [esi+0x1150], 0xd2f1a9fc)   ; 构造器低 dword（0.016）
(6764991=0x6739BF, 'R', fstp qword [esi+0x1150])              ; ← 被标 'R' 的真写点！
STR 0083d344 = b'PatrolScan'      u32(0x7F0CD4)=0x839DA4 → b'AI'
0067399e  mov eax,[esi+0x1154]        ; 当前值高 dword 作默认实参
006739a4  mov ecx,[esi+0x1150]        ; 当前值低 dword
006739b2  push 0x83d344               ; key = "PatrolScan"
006739b7  push edx                    ; section = "AI"（[0x7F0CD4]）
006739ba  call 0x5283d0               ; INI Get-Double（节/键/默认值）
006739bf  fstp qword [esi+0x1150]     ; ★ Rules+0x1150 的 LoadFromINI 写点
```

同函数邻键：`AttackInterval`→+0x10A0、`AttackDelay`→+0x10A8、`CreditReserve`→+0x1758、
`PathDelay`→下一字段——全是 rules.ini `[AI]` 节键。**即 Rules+0x1150 = `[AI]→PatrolScan`（double），
构造器默认 0.016，0x6739BF 是 read-with-default 的 INI 加载点。**

- 根因：capstone 对 `fstp` 存储不置 write 访问位 → F7 的「写点恰 1」普查把真写点当读点漏掉
  （我方 probe1 的 E7 同样先踩坑：nesting bug + access 位，probe2 用 disp_hits_field 才暴露）。
- 影响：N = int(PatrolScan × 900)——**默认 14，但可被 INI 改**。F7 门字节本身无误，
  「周期来源」结论必须改；C4 若把该门当死常量建模会错。
- 残余口径（如实注记）：0x6739BF 的 `esi` 与 `[0x8871E0]` 同一对象这一环，
  由「构造器默认 → INI read-with-default → 门读 [Rules]+0x1150」三角与 [AI] 键族推定，
  未做 CFG 级终证（F7 对构造器归属同样只到字段三角）。

### 4.3 ★ 必须改 E2：「0x736664 宿主无条件每轮派发」不成立

F7 §1.4：「派发宿主 0x736664.. 仅在派发前查 type+0xE18/E19，**无条件每轮派发**」。

**证伪**（probe3 O 段流清单 + probe7 AB2 段）：0x736663 有 `ret`、0x736664 无任何 E8/E9/EB
入边（probe2 M 段：RAW_E8/E9→0x736664 全空、全文件 dword 0 次）——它**不是函数起点，
是函数中途汇合标号**；入边是三条**条件**短跳：

```
007365f7  cmp eax, 5          ; v[65](this)（[edx+0x184]）
007365fa  jne 0x736664        ; 75 68
00736629  test al, al         ; call 0x568350（Map 查询，ecx=0x87F7E8）
0073662b  jne 0x736664        ; 75 37
00736633  test al, al         ; [esi+0x3D5]
00736635  je 0x736664         ; 74 2d
…（三条件全不满足则走 0x736637..0x736663 收尾 ret，**跳过派发**）
00736664: type+0xE18/E19 查 → （条件）call 0x737180 → 00736689 call [eax+0x424]
```

即 **v[265]（→0x6FB010）派发受「v[65]()!=5 ∨ Map查询非0 ∨ [this+0x3D5]==0」门控**；
仅当三条件同时落空才跳过。这不是帧门（F7 反对帧限频的结论保住），但「无条件每轮」
按字节不成立，且「宿主=函数起点」的框架错误。同类毛病：§6.5a「v[231] 宿主每帧给每个单位
打帧戳」——v[231]（0x709820）自身的调用方 F7 未追，频次说法无字节支撑（§6-M3）。

## 5. 问四复核：无现成全局累加器 → UNLOCATED 维持（反例狩猎未命中）

F7 的 11 条排除清单**逐条对得上实跑输出**（B/C1/C2/C3/C5/C6/D/E 各段均在
`_w8_f7_out.txt` 中有对应行，非「我没找到」式空口）。我在其边界之外加做四路反例狩猎，全部未命中：

1. **邻域全写普查**（超出 F7 的 [A8EC30,A8EC38) 窗）：全流绝对 disp 写 ∈[A8EC00,A8ED00)
   共 111 条，**disp==0xA8EC34 的写恰 1 条（0x6F8E09）**；0xA8EC38 的两条写（0x4E67FD/0x4E6828）
   是**相邻单件对象**的 vtable 装载（0x7E9CE4/0x7E9D04），不触 0xA8EC34
   （`_f7rev_out.txt` E5 段）。
2. **inc/add [abs] 全景**：全流 RMW 型绝对写站点全集（E6 段）中，A8ECxx/A8EDxx 区**零条**
   （0xA8EC34 的累加是 GT 用 load/inc/store 合成的，不属 inc/add 型）；最接近的
   `inc [0xA8E7AC]`@0x52E0BE 上下文为 inc/dec 配对的场景类例程（probe2 L 段），与索敌无关。
3. **GT 深度-1 被调者普查**（F7 §4.2 边界③只承认未查）：GT 体外直 call/jmp 目标恰 13 个
   （`_f7rev3_out.txt` N 段）；各目标 0x600 窗内全局绝对写仅 0xABDC74（三个查询类被调者，
   非计数器）；0x6F8960/0x6F8C10 窗内出现的 0x6F8E09 是窗口与 GT 体**重叠的假阳性**。
   ⇒ 深度-1 内无第二累加器。
4. **间接写通道收口**（F7 §4.2 边界①）：唯一物化 0xA8EC30 的三站点（0x65AAAB/0x65ACC3/0x65AD05）
   都把该指针作为第 2 实参传给虚方法 v[159]；七个虚表（Techno/Unit/Foot/Infantry/Building/
   0x7E22A4 系/0x7F0508 系）的 +0x27C 槽全部指向共享实现 0x65A970（probe7 AC 段），
   其实现把 arg2 原样转发给 0x40DD70，而 0x40DD70 全体仅读 `this`（WhatAmI 字节表@0x40DDA4，
   两出口 0x40DD91 返回 this / 0x40DD95 返回 NULL），**不读栈实参、不写穿指针**
   （probe5 X 段 + probe6 崩前字节）。⇒ 该通道对 0xA8EC34 无写。
5. GT 函数尾边界：[0x6F8DF0,0x6F9DB0) 精确——0x6F9DAC `ret 0xC`、0x6F9DAF nop、
   0x6F9DB0 起为下一函数（`_f7rev_out.txt` F 段）。F7 的普查窗没有漏字节。
6. GT 体内非 mov 型写（inc/add 经 disp）= 0（E6/E5 交叉）；F7 的 C6「体内绝对 dword 写恰 1」成立。

**判定：F7 的 UNLOCATED（「索敌执行计数」无现成全局累加器）维持。**
其 §4.2 自报的未穷尽边界（rep movsd、更深调用闭包、加载期恢复）如实、不冒充。

## 6. 次要意见（不阻塞）

- **M1** §1.1 引文略去 0x6FB03D/0x6FB040/0x6FB048 三条指令（探针输出里都有）；引文地址无误。
- **M2** F7 诚实账第 6 条「0x7E2640 未归属」现可结案：0x7E2640 = 第六张虚表 @0x7E22A4 的
  +0x39C（v[231]），同表 +0x3C4（u32(0x7E2668)）= **0x4D9920（FOOT 包装）**——Foot 派生类
  （疑 AircraftClass，类名未终证）。v[231] 共享实现 0x65A970 共被 7 张虚表引用（新增
  0x7E2520、0x7F0784）。不影响任何计数。
- **M3** §3.4/§6.5a 的「每帧/每轮」频次措辞普遍超前于字节（调用方未追）；建议统一改为
  「进入即打戳/派发」式事件描述。
- **M4** 「fn 0x740B51..0x740DED」起点落在 nop 填充内（实际 ≈0x740B60）；「0x736664 宿主」
  实为函数中途标号（§4-E2）。
- **M5** 「House 级」标签（%14 门宿主、90 帧计时器）与 switch 宿主身份：F7 已自报未深究，
  字节上无矛盾，维持存疑登记即可。

## 7. 复核员诚实账

- 本会话实跑：7 个只读探针（reviews/ 内，命令见文首）；SHA256 独立实算；0x6FB010/GT/两包装/
  %14 门/%8 门/90 帧块/0x740BED/0x50B730/INI 六键绑定/虚表 u32 全部重跑；四路反例狩猎。
- **未跑**：12 个无特征派发窗口的逐窗宿主命名（沿用 F7 的 D 段普查结果，未重扫每窗 CFG）；
  CurrentFrame 另 8 个写点裁决（F4 范畴）；Rules+0x1150 的 CFG 级「esi==Rules 实例」终证
  （§4.2 残余口径）；GT 深度≥2 被调者、`rep movsd`/块写、加载期恢复（与 F7 同边界）。
- 零真机、零注入、未读活进程；唯一写域 = `W8_STATIC_LOCATE/reviews/`
  （本文件 + `_f7rev_probe*.py` + `_f7rev*_out.txt`）。未 commit、未 push。

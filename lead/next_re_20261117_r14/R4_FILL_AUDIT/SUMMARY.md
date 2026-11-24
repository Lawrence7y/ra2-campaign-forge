# R4_FILL_AUDIT — SUMMARY

审计对象：`R4_FILL_91_R2\fill_delta.tsv` 的 91 行中抽出的 **12 行**（给已 `[已证]` 行补写成文 ④ 的产物）。
审计员：异族独立审计员（非执行器）。所有结论只来自我自己从 `ra2youli\gamemd.exe` 反汇编的字节，
未引用 `R4_FILL_91_R2\evidence\ROW_*.txt`，未复用 `fill.py` 代码，未改任何输入文件。

二进制：`ra2youli\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（4 825 360 字节）。

---

## 1 · 结果

| 项 | 数 |
|---|---:|
| 抽样行 | **12** |
| PASS | **12** |
| FAIL | **0** |
| 五项全成立的 check 计数 | 12/12 × 5 = 60/60 |
| 类名 ≠ 行名类（专项一） | **6 / 12** |
| 其中「表述不恰当」 | **6 / 6**（不影响 PASS，判的是措辞） |
| 装表点宿主是 initterm 回调（专项二） | 4 行（不在抽样内，已单独独立复核，**4/4 成立**） |

`verdict` 只允许 PASS/FAIL；`grade` 未动（仍 `[已证]`），本审计只判 ④ 是否名副其实。

---

## 2 · FAIL 逐条原因

**无 FAIL。** 12 行 × 五项，证据链逐条可复核（地址 + 字节见 `VERDICT.md` 每行 ①–⑤ 小节）：

- **① vt / 槽号**：12/12 `u32(vt+slot*4) == entry`，且 `vt` 都是表起点（`u32(vt-4)` 为合规 COL）；
  我独立全扫 `.rdata/.data` 得到的见证集合里，④ 的 `(vt, slot)` 都在其中。
- **② COL**：12/12 `u32(vt-4)` 等于 ④ 的 COL，`COL.sig == 0`，`offset` 与 ④ 写的 `0` 一致。
- **③ TD 与类名**：12/12 `u32(COL+0xC)`（**绝对 VA**）等于 ④ 的 RTTI，`TD+8` 按**内联串**读以 `.?A` 开头，
  去修饰后与 ④ 的类名**完全一致**。
- **④ 装表点与宿主**：12/12 装表点处是一条写内存、立即数 `== vt` 的指令（全是 `mov [reg], imm32`），
  且该地址在「不跟 call」的 CFG 遍历下从给出的宿主 entry 可达；宿主另有两条独立锚点互证
  （前有 `CC/90` 填充，且被 `call rel32` 指向）。
- **⑤ ㉓**：12/12 用的装表点都不在 atexit 注册**保守超集**内、也不是删除析构器/基类析构器形态。

需要明确说清的是：**四项「不成立也没判 FAIL」的例外都已核实为不适用**——`COL.pSelf` 在本镜像恒为 0
（不能用它判表起点，我改用 `sig==0` + `pTD` 合规装饰名）；`COL.offset` 抽样 12 行全为 0；无一行是 self-install；
`lea` 中介的写点在本镜像实测 0 处，枚举没有漏形式。

---

## 3 · 两项专项

### 专项一 · 40/91「④ 类名 ≠ 行名类」：抽样中 6 行，措辞该怎么写

事实（字节实测，抽样 6 行）：

| entry | 行名类 | ④ 表属类 | 同一 entry 的全部表（slot, 表属类）| 行名类自己的表是否持有它 |
|---|---|---|---|---|
| `0055A950` | LocomotionClass | FlyLocomotionClass | Fly/Hover/**Locomotion**/Mech/Rocket/Tunnel 的 slot1 | **是**（`007EAEC0` slot1 同址）|
| `005C0FE0` | MPGameModeClass | MultiplayerBattle | 仅 MultiplayerBattle slot0 | 否（`MPGameModeClass` 在本镜像无 RTTI，连字符串都不存在）|
| `005CA6D0` | MPGameModeClass | MultiplayerSiege | 仅 MultiplayerSiege slot5 | 否（同上）|
| `005CB440` | MPGameModeClass | UnholyAlliance | 仅 UnholyAlliance slot50 | 否（同上）|
| `005D6540` | MPGameModeClass | MultiplayerBattle | Battle/ManBattle/Megawealth/Siege/UnholyAlliance/**MultiplayerGameMode** 的 slot20 | 否（无 RTTI 表；但 `MultiplayerGameMode` slot20 同址）|
| `005D74A0` | MPGameModeClass | MultiplayerBattle | 同上系列 + FreeForAll 的 slot34（含 `MultiplayerGameMode` slot34）| 否（同上）|

**结论：④ 里必须写「表属类」（＝RTTI 实测去修饰名），但只写它仍会误导，必须再补一个关系的从句。**

- 写**行名类**是错的：`005C0FE0/005CA6D0/005CB440` 的行名类 `MPGameModeClass` 在本镜像**没有任何 RTTI/表**
  （`blob.find(b'.?AVMPGameModeClass@@')` = −1，连 `MPGameModeClass` 这个字符串都没有），写它等于给一个无法复核的类名，
  且与同一句里的 `vt/COL/RTTI` 三个字段自相矛盾。
- 只写**表属类**也不够：`0055A950` 的同一实现同时也在行名类 `LocomotionClass` 自己的 `vt=007EAEC0` slot1 里
  （同址，无须任何别名假设）；`005D6540`/`005D74A0` 的同一实现也在 RTTI 名 `MultiplayerGameMode` 的 slot20/slot34
  （同址；该 RTTI 名是否等于行名 `MPGameModeClass`，本审计不判，但「同一实现在另一张表里」是实测）。
  只写派生表会被读成「这是派生类的成员」——与实测方向相反（实测是**同一实现被多张派生表共用**）。
- 不误导的写法：`<表属类>::slotN` + 「该槽亦见于 <行名类基表> 的 slotN（同址 `<vt>`）」/「行名类 `MPGameModeClass`
  在本镜像无 RTTI 表」，两句合起来才闭合。
- 另有一处更会误导的事实：`005C0FE0` 是编译器生成的**标量删除析构器**
  （`push esi; mov esi,ecx; mov [esi],0x7EE184; call 0x5D5D20; test byte[esp+8],1; je; push esi; call 0x7C8B3D; ret 4`），
  占的正是 MSVC 虚表的**删除析构器槽 slot 0**。④ 只写 `MultiplayerBattle::slot0` 不会让人知道这一点，
  这类行应点明「该槽为删除析构器槽」。

抽样 6 行的措辞判定全部为「不恰当」（`verdict.tsv` 的 `wording_ok=no`），理由逐条写在表里；
**这不是 FAIL**：④ 的六字段本身都实测成立，缺的是类名归属与「编译器生成函数」的限定语。

### 专项二 · 4 行装表点宿主是 `initterm` 静态初始化函数

先把 `_initterm` 从字节里认出来（不靠名字）：`0x7CBED3` 是
`push esi; mov esi,[esp+8]; cmp esi,[esp+0xc]; jae …; mov eax,[esi]; test eax,eax; je …; call eax; add esi,4; jmp …`；
其调用点 `0x7CBDC6`–`0x7CBDD3` 是 `push 0x815DA4; push 0x812000; call 0x7CBED3`，即初始化表区间
**[0x812000, 0x815DA4)**（3 945 项）。

| entry | 装表点 | 宿主 | 宿主在初始化表内的位置 | 存储目标 | 目标所在节 | 全局对象？|
|---|---|---|---|---|---|---|
| `005519B0` | `004A8660` | `004A8630` | `00812D20`（第 840 项）| `008A0360`（`[eax-8]`，eax←`008A0368`）| `.data` | **是**（5 件一组，步长 0x18）|
| `0055B880` | `0040CBAC` | `0040CB80` | `00812130`（第 76 项）| `0087F778`（绝对地址）| `.data` | **是** |
| `0055BAA0` | `0040CBAC` | `0040CB80` | `00812130`（第 76 项）| `0087F778`（绝对地址）| `.data` | **是** |
| `006CF240` | `006CF0C8` | `006CF070` | `00814E10`（第 2948 项）| `00B0C110`（绝对地址）| `.data` | **是** |

- 装表点确实在 initterm 回调函数体内：从宿主做 CFG 遍历可达装表点，宿主地址本身作为 dword 出现在初始化表里，
  且区间由上述 `push/push/call` 定界。**4/4 成立。**
- `vt` 确实被装到全局对象上：三行是绝对地址写，一行是 `mov eax,0x8A0368` 预置后写 `[eax-8]`；目标全在 `.data`，
  不是 `this`。
- 与 Lead 裁定的关系：接受「由 initterm 写虚表」这个物理事实没问题。**但**这 4 行的宿主不是类构造器，
  而 ④ 句仍只写「位于 `<宿主>` 体内」、未标明它是静态初始化回调——措辞同样应补一句（与专项一同类问题）。
- 补一条独立观察，支持「这 4 行确实是全局对象」：它们的宿主在字节里还顺手把销毁函数登记给 atexit
  （如 `0040CB80` 体内 `push 0x40CBC0; …; call 0x7C978A`），即「静态构造 + 全局析构」成对出现；
  而 ④ 用的是构造那一次写，不是析构那一次。

---

## 4 · 一句话回答

**「这 91 行的 ④ 是否真的已成文（六字段实测、可复核），还是只是形式补齐？」**

**是真成文、可复核，不是形式补齐**——抽样的 12 行六字段全部与我从原始字节反汇编的结果逐一吻合
（`vt`/槽号/`COL`/`TD`/装表点/宿主，0 处不符、0 处编造，且 ④ 引的装表点都不是 atexit 或删除析构器写点，
而它们确实存在、只是没被拿来充数）；**但成文的「措辞」只完成了六字段那一半**：类名归属
（6/12 行 ④ 类名≠行名类、其中 3 行还隐去了基类表同址的事实、1 行隐去了「该槽是删除析构器槽」）
与宿主身份（4 行是 initterm 静态初始化而非构造器）都还没在句子里交代，需各补一个从句才算真正「写成文」。

# NAMED_PUSH_AUDIT20 — VERDICT（4 行逐行审计）

- 来源：`NAMED_PUSH_S07S11_B2\delta.tsv`（该文件 4 个数据行全取，无筛选）
- 执行器：Hy4（S07/S11）。本报告为异族独立反汇编，**未引用** `NAMED_PUSH_S07S11_B2\EVIDENCE\ROW_*.txt`
- 二进制：`ra2youli\gamemd.exe`，SHA-256 `73201CC0…FCF67476`（与卡片期望一致）；ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`
- 工具：capstone 5.0.7（`skipdata=True, detail=True`）+ pefile 2024.8.26，Python 3.12.10
- 计数：**PASS 4 / FAIL 0**

---

## 1. `006DBE00` — S07 Tactical::slot6 → **PASS**（③b② = 流写出）

### ② 类身份（独立成立）
- 主虚表 `007F4348`：COL 指针在 `007F4344`，读出 `0080B9A8`。
  COL 字节 `00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 38 2a 84 00 | 98 b9 80 00`
  → `offset(+4)=0`、`pTD(+0xC)=00842A38`（**绝对 VA**）、`pCHD(+0x10)=0080B998`（绝对 VA）。
- `pTD+8` 内联串原始字节 `2e 3f 41 56 54 61 63 74 69 63 61 6c 40 40 00` = `.?AVTactical@@`
  （`TD+8` 首 dword = `0x56413F2E`，是内联字符串而非指针 → 符合技术条）。
- 槽位：`007F4348 + 6*4 = 007F4360`，字节 `00 be 6d 00` = `006DBE00` ⇒ **slot 6**。
  同表 slot 值（前 8 项）：`00410260, 00410300, 00410310, 006DBCE0, 00410450, 006DBD20, 006DBE00, 004103E0`。
- 副表排除：ctor 同时写 `[esi+4]=007F432C`、`[esi+8]=007F4324`、`[esi+0xC]=007F431C`，三者 COL `offset` 分别为 4/8/0xC，是同一 `.?AVTactical@@` 的次对象表；**主表只有 `007F4348`（offset 0）**。
- 附带独立佐证（不参与判分）：该表与 IPersistStream 槽序一致 —— 0 QI(00410260)/1 AddRef(00410300,`mov eax,1;ret 4`)/2 Release(00410310)/3 GetClassID(006DBCE0，把 `007E9950` 处 GUID 写进 out 参数)/4 IsDirty(00410450，`mov dl,[ecx+0x20]; sete al`)/5 Load(006DBD20)/6 **本行**/7 GetSizeMax(004103E0，`call [eax+0x30]` 后 `add eax,4`)。

### ③b② 具体形态（形态 = 3b2）
行体 7 条指令（`006DBE00`–`006DBE1A`，共 `0x1C` 字节）：
```
006DBE00  8b 44 24 0c   mov eax,[esp+0xc]
006DBE04  8b 4c 24 08   mov ecx,[esp+8]
006DBE08  8b 54 24 04   mov edx,[esp+4]
006DBE0C  50            push eax
006DBE0D  51            push ecx
006DBE0E  52            push edx
006DBE0F  e8 0c 45 d3 ff  call 00410320        ; → 0x006DBE14 - 0x2CD1F4
006DBE14  85 c0         test eax,eax
006DBE16  7c 02         jl 006DBE1A
006DBE18  33 c0         xor eax,eax
006DBE1A  c2 0c 00      ret 0xc
```
- **失败返回**：`eax` 原样上抛的负 HRESULT（taken 路 `006DBE1A` 直接 `ret 0xc`，不碰 eax）。被调 `00410320` 的可伪证码表：`0041032B b8 03 40 00 80` = **`0x80004003` E_POINTER**（`00410325 85 f6 test esi,esi` 判流对象为空）；另有两处 `jl 00410372`（`0041034D`、`00410363`）把 `IStream::Write` 的失败负码原样带回。
- **成功返回**：`006DBE18 33 c0` → **0**（被调成功路同样返 0）。
- **拿它分支的指令**：`006DBE14 85 c0 test eax,eax` + `006DBE16 7c 02 jl`（两路一为"透传负码"，一为"归零"）。多值状态码，不是 `{0,1}` 布尔。
- 方向核对（本项目最高频错误，逐字节核）：被调 `00410320` 内 `00410348 ff 50 10` = **槽 `+0x10`（slot 4）**，`eax=[esi]` 而 `esi` 是被 null 检查过的流对象（`00410325 85 f6`）。方向为**内存 → 流（写出）**：`00410344 89 7c 24 20` 把 `edi`(=arg1 对象) 填进即将送出的栈缓冲，`00410358 call [edx+0x30]` 取对象长度后 `0041035E ff 53 10` 再次写出对象体；写成功后 `0041036E c6 47 20 00` 清对象 `+0x20` 脏位。
  对照同族读辅助 `00410380`：`0041039E ff 50 0c` = 槽 `+0xC`（slot 3，Read），`004103CD ff 55 0c` 亦为读 → **槽 0xC=Read / 槽 0x10=Write 分工明确**。
  再加成对佐证：`slot5` 的 Load（`006DBD2E e8 4d 46 d3 ff call 00410380` 读）与本行 `slot6`（`call 00410320` 写）成对 ⇒ 第 4 列"写出"**方向正确，未写反**。

### ④ 使用见证（独立、非 direct-only）
- 活表写入点 `006D1D54 c7 06 48 43 7f 00  mov [esi],007F4348`，所在函数 `006D1C20` 是**真构造器**：`006D1C23 8b f1 mov esi,ecx`（thiscall）+ `006D1C25 call 00410170`（基类 ctor，`00410198 c7 00 50 1f 7e 00` 装基表）+ 末尾 `mov eax,esi; pop; ret`。
- 5 个调用方全部是"堆实例化"：`0052C681/00599D6D/006853A1/00687604/006BF841` 处 `push 0xe18` + `call 0x7C8E17`（operator new：`007C8E17 6a 01; push [esp+8]; call 0x7C9442`），随后 `mov ecx,eax; call 006D1C20`；`006DC460 b8 18 0e 00 00 mov eax,0xe18; ret` 印证 `sizeof=0xE18`。
- 实例落入全局：`0052C69B a3 24 73 88 00 mov [0x887324],eax`（ClassFactory 风格），`[0x887324]` 在 `.text` 内被读取 **447** 次 ⇒ 该表是活表。
- 无静态 slot 6 派发点可解析（`006DBE00` 无任何 `e8` 直接调用者、无 `push imm` 引用；经 `[0x887324]` 追踪的间接调用窗口内无 `call [reg+0x18]`）。间接派发目标由实参寄存器决定，静态不可判 —— 此点如实披露；④ 依"行外真构造器装活表 + operator new 堆实例 + 全局登记后被 447 处引用"成立，与上一批同标准。

### ④ 与 ② 不同源
② 锚在表内容 `007F4360`；④ 锚在构造器写点 `006D1D54`。不同地址、不同角色 ⇒ `same_source = no`。

### ㉓ 全枚举（表 `007F4348` 全部写点，4 处）
| 写点 | 所在函数 | 分类 | 处置 |
|---|---|---|---|
| `006D1D54 c7 06 48 43 7f 00` | `006D1C20` | 真构造器（基类 ctor `00410170`，无 free） | **④ 锚**（非析构器） |
| `006D1E58 c7 06 48 43 7f 00` | `006D1E30` | 带参 CopyFrom/赋值形态（`ret 4`，先 `call 004101C0` 装基表）；唯一调用者 `006DBD46` 位于 Load `006DBD20` 内 | 非析构器，不参与 ④ |
| `006D1E80 c7 01 48 43 7f 00` | `006D1E80` | **非删除析构器**（装 4 表 + 清 `[0x887324]` + `e9 … jmp 004101F0` 基类 dtor；无 caller、无 push） | 按 ㉓ 排除 |
| `006DC475 c7 06 48 43 7f 00` | `006DC470` | **删除析构器**（`006DC49D f6 44 24 08 01 test byte[esp+8],1` + `006DC4A5 call 0x7C8B3D` + `ret 4`） | 按 ㉓ 排除 |
- **atexit 注册的全局析构器：0**（`006D1C20 / 006D1E30 / 006D1E80 / 006DC470` 的 `push imm32` 站点均为空；`0x7C978A` 为 atexit 入口：`ff 74 24 04; call 0x7C970C`）。

### 语义与实测一致性
第 4 列"③b② 流写出 / 失败原样上抛负 HRESULT(0x80004003 E_POINTER) / 成功返 0 / ② vt 007F4348 slot6 COL.offset=0 主表 RTTI .?AVTactical@@ / ④ 行外 ctor 006D1C20@006D1D54 + push 0xE18 new" **逐项与实测一致**。

### 边际披露（不改变 PASS，供 lead 复核）
- 本行是 `0x1C` 字节的 HRESULT 归一化包装：真实流写在被调 `00410320` 体内。**没有**把它当作"循环内非栈写"使用（那是 ③b④ 的禁令），本行按 ③b② 的"多值状态码 + 判分指令"成立。
- 在被调的实际值域 `{0} ∪ {负码}` 上，本行的映射是恒等（只有假设性的正码会被归零），因此形态上接近"纯转发"，但与 ③a 的判据（`jmp`/`call+ret` 不改返回值）不同：本行确实含 `test/jl` 两路且两路返回值语义不同（失败=负码，成功=0），失败/成功对调用方可区分。**据此判 3b② 而非 3a**；此边界如实标注。

---

## 2. `0069EE30` — S11 ShipLocomotionClass::slot0 → **PASS**（③b② = QueryInterface）

### ② 类身份（独立成立）
- 主虚表 `007F2E58`，COL `00809408`，字节 `00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 80 f8 83 00 | f8 93 80 00`
  → `offset=0`、`pTD=0083F880`（绝对 VA）、`pCHD=008093F8`。
- `pTD+8` 内联串 `2e 3f 41 56 53 68 69 70 4c 6f 63 6f 6d 6f 74 69 6f 6e 43 6c 61 73 73 40` = `.?AVShipLocomotionClass@@`。
- 槽位：`007F2E58` 首 dword `30 ee 69 00` = `0069EE30` ⇒ **slot 0**；本 entry 在同一表内仅出现于 slot 0。
- **小成员表排查**：`007F2E58` 是 ctor 写进 `[esi+0]` 的主表（`0069ECD2 c7 06 58 2e 7f 00`）；另外两处是次对象表 `[esi+4]=007F2D8C`（COL `008093A0` offset **4**）、`[esi+0x18]=007F2D68`（COL `00809388` offset **0x18**），二者 slot0 是**调整 thunk**：
  `006A4300 83 6c 24 04 04 sub [esp+4],4; e9 … jmp 0069EE30`；
  `006A4330 83 6c 24 04 18 sub [esp+4],0x18; e9 … jmp 0069EE30`。
  ⇒ "副表 slot0 thunk 已排除"属实；主表判定正确（非小成员表）。

### ③b② 具体形态（形态 = 3b2）
```
0069EE30 53              push ebx
0069EE31 8b 5c 24 08     mov ebx,[esp+8]        ; ebx = arg1 = this
0069EE35 55              push ebp
0069EE36 8b 6c 24 14     mov ebp,[esp+0x14]     ; ebp = arg3 = ppv
0069EE3A 56              push esi
0069EE3B 8b 74 24 14     mov esi,[esp+0x14]     ; esi = arg2 = riid
0069EE3F/40/41 55 56 53  push ebp/esi/ebx
0069EE42 e8 69 bb eb ff  call 0055A9B0         ; 基类 QI
0069EE47 3d 02 40 00 80  cmp eax,0x80004002   ; E_NOINTERFACE
0069EE4C 75 39           jne 0069EE87
0069EE4E 57              push edi
0069EE4F b9 04 00 00 00  mov ecx,4             ; 4 dwords = 16B IID
0069EE54 bf 10 9b 7e 00  mov edi,007E9B10       ; 常量 IID
0069EE59 33 c0           xor eax,eax
0069EE5B f3 a7           repe cmpsd [esi],[edi]
0069EE5D 5f              pop edi
0069EE5E 75 0e           jne 0069EE6E
0069EE60 85 db           test ebx,ebx
0069EE62 74 05           je 0069EE69
0069EE64 8d 43 18        lea eax,[ebx+0x18]     ; this+0x18 次对象
0069EE67 eb 02           jmp 0069EE6B
0069EE69 33 c0           xor eax,eax
0069EE6B 89 45 00        mov [ebp],eax          ; *ppv = this+0x18
0069EE6E 83 7d 00 00     cmp dword [ebp],0
0069EE72 75 0b           jne 0069EE7F
0069EE74 5e 5d           pop esi/ebp
0069EE76 b8 02 40 00 80  mov eax,0x80004002     ; E_NOINTERFACE
0069EE7B 5b              pop ebx
0069EE7C c2 0c 00        ret 0xc
0069EE7F 8b 0b           mov ecx,[ebx]
0069EE81 53              push ebx
0069EE82 ff 51 04        call [ecx+4]           ; AddRef
0069EE85 33 c0           xor eax,eax            ; S_OK
0069EE87 5e 5d 5b        pop esi/ebp/ebx
0069EE8A c2 0c 00        ret 0xc
```
- **被调多值码表（自测）**：`0055A9B0` 是 LocomotionClass 基类 QI（`(this,riid,ppv)`：`0055A9C1 mov ebx,[esp+0xc]` = riid 参与 `repe cmpsd` 与 `007F7C90/007F7C80/007ED358/007F7C70` 比较；`0055A9E7 lea ecx,[edx+4]` 返回 `this+4`）。
  失败/成功码：`0055A9B8 b8 03 40 00 80` = **`0x80004003`**、`0055AA41 b8 02 40 00 80` = **`0x80004002`**、`0055AA4F 33 c0` = **`0`（S_OK；`0055AA51 c2 0c 00`）**。
- **本行返回**：成功 `0`（`0069EE85`）；未命中 IID 或 `*ppv==0` → `0x80004002`（`0069EE76`）；基类已处理/已失败 → `eax` 原样上抛（`0069EE87`，taken 路不碰 eax）。
- **调用方拿它分支的指令（外部真实调用方，非本行内部）**：`006C4F6C 8b f8 mov edi,eax` → `006C4F6E 85 ff test edi,edi` → `006C4F70 7d 09 jge 006C4F7B`；负码路 `006C4F72 8b 16`/`006C4F74 6a 01`/`006C4F76 8b ce`/`006C4F78 ff 52 20 call [edx+0x20]`（Release）后把负码作为 `CreateInstance` 返回值 `ret 0x10` 抛出。
- 非 `{0,1}` 布尔（`0` / `0x80004002` / 透传 `0x80004003` 三类可区分）；非纯转发（本行自带 IID 比较与返回值裁决）。

### ④ 使用见证（活虚表派发点，非 direct-only）
`006C4F61 8b 4c 24 14 mov ecx,[esp+0x14]`（riid）→ `006C4F65 8b 06 mov eax,[esi]`（刚构造对象的主 vptr = `007F2E58`）→ `006C4F67/68/69 57 51 56 push edi/ecx/esi`（ppv, riid, this）→ **`006C4F6A ff 10 call dword ptr [eax]`** = 派发 **slot 0 = 0069EE30**。
该函数是 COM 类工厂创建路径：`006C4F3C 6a 70 push 0x70` + `006C4F3E e8 d4 3e 10 00 call 0x7C8E17`（operator new）+ `006C4F4A 8b c8 mov ecx,eax` + `006C4F4C e8 ff 9c fd ff call 0069EC50`（ctor），失败退 `0x8007000E`/`0x80040110`，`ret 0x10` — 即 `IClassFactory::CreateInstance`。

### ④ 与 ② 不同源
② 锚在表内容 `007F2E58+0`（RTTI 链）；④ 锚在**派发指令** `006C4F6A` 与**构造器写点** `0069ECD2`。不同地址、不同角色 ⇒ `same_source = no`。

### ㉓ 全枚举（表 `007F2E58` 全部写点，4 处）
| 写点 | 所在函数 | 分类 | 处置 |
|---|---|---|---|
| `0069ECD2 c7 06 58 2e 7f 00` | `0069EC50` | 真构造器（`0069EC53 call 0055A6C0` 基类 ctor：`0055A6D5 c7 00 c0 ae 7e 00`；`mov eax,esi; ret`，无 free） | **④ 锚** |
| `0069ECF3 c7 06 58 2e 7f 00` | `0069ECF0` | **非删除析构器**（装 3 表 + 释放成员 `[esi+0x68]` 经 `call [ecx+8]` + `0069ED16 call 0055A6F0` 基类 dtor + `ret`；无 caller/push） | 排除 |
| `0069EEB3 c7 06 58 2e 7f 00` | `0069EE90` | 虚方法 = 本表 **slot 5（Load）**：先 `0069EE9D call 0055AAC0`（基类），再 `0069EED3 ff 50 0c`（IStream **Read** 槽）读入 | 非析构器 |
| `006A42B3 c7 06 58 2e 7f 00` | `006A42B0` | **删除析构器**（`006A42DB f6 44 24 08 01 test byte[esp+8],1` + `006A42E3 call 0x7C8B3D` + `ret 4`） | 排除 |
- **atexit 注册：0**（上述 4 函数 `push imm32` 站点全空）。
- 结论：④ 锚非析构器、非 atexit 注册体 ⇒ 不触 ㉓ 陷阱。

### 语义与实测一致性
"QueryInterface 实现 / 基类 QI 先行 / E_NOINTERFACE 与 S_OK / 返回 this+0x18 / AddRef / ② 主表 slot0 / ④ ctor 0069EC50@0069ECD2 + push 0x70 new" **逐项一致**（`0x70` 见 `006C4F3C`）。执行器给出的 `0069EE42/47/4C/87`、`0055A9B8/0055AA41/0055AA4F`、`0069EE5B` 全部核对无误。

---

## 3. `00719E30` — S11 TeleportLocomotionClass::slot0 → **PASS**（③b② = QueryInterface）

### ②
- 主虚表 `007F50CC`，COL `0080C1E0`，字节 `00…00 | 38 45 84 00 | d0 c1 80 00` → `offset=0`、`pTD=00844538`（绝对 VA）、`pCHD=0080C1D0`。
- `pTD+8` = `.?AVTeleportLocomotionClass@@`（字节 `2e 3f 41 56 54 65 6c 65 70 6f 72 74 4c 6f 63 …`）。
- 槽位：`007F50CC` 首 dword `30 9e 71 00` = `00719E30` ⇒ slot 0，且表内唯一。
- 次对象表排除：`[esi+4]=007F5000`（COL `0080C178` offset **4**，slot0 `0071A160 83 6c 24 04 04 sub [esp+4],4; e9 … jmp 00719E30`）、`[esi+0x18]=007F4FDC`（COL `0080C160` offset **0x18**，slot0 `0071A190 sub [esp+4],0x18; jmp 00719E30`）⇒ 主表判定正确。

### ③b②（3b2）
行体与第 2 行同构（逐字节核对）：
`00719E42 e8 69 0b e4 ff call 0055A9B0` → `00719E47 3d 02 40 00 80 cmp eax,0x80004002` → `00719E4C 75 39 jne 00719E87` →
`00719E54 bf 10 9b 7e 00 mov edi,007E9B10` / `00719E5B f3 a7 repe cmpsd` →
命中 `00719E64 8d 43 18 lea eax,[ebx+0x18]` / `00719E6B 89 45 00 mov [ebp],eax` /
`00719E7F 8b 0b mov ecx,[ebx]` + `00719E82 ff 51 04 call [ecx+4]`(AddRef) + `00719E85 33 c0`(S_OK)；
未命中 `00719E76 b8 02 40 00 80 mov eax,0x80004002`；taken 路 `00719E87` 起 `pop/pop/pop/ret 0xc`（eax 不碰）。
- 外部调用方分支：`006C4C6C 8b f8 mov edi,eax` / `006C4C6E 85 ff test edi,edi` / `006C4C70 7d 09 jge 006C4C7B`，负码路 `006C4C78 ff 52 20`（Release）后原样返回。

### ④
`006C4C65 8b 06 mov eax,[esi]` → **`006C4C6A ff 10 call dword ptr [eax]`** = 派发 slot 0；同函数 `006C4C3C 6a 4c push 0x4c` + `006C4C3E call 0x7C8E17`(new) + `006C4C4A mov ecx,eax` + `006C4C4C call 00718000`(ctor)。
构造器写点 `0071805E c7 06 cc 50 7f 00 mov [esi],007F50CC`（`00718003 call 0055A6C0` 基类 ctor，末尾 `mov eax,esi; ret`）。

### ④ ≠ ②
② = 表内容 `007F50CC+0`；④ = 派发 `006C4C6A` / 构造器写点 `0071805E` ⇒ `no`。

### ㉓ 全枚举（`007F50CC`，2 处）
| 写点 | 所在函数 | 分类 |
|---|---|---|
| `0071805E c7 06 cc 50 7f 00` | `00718000` | 真构造器 | **④ 锚** |
| `00719CDF c7 06 cc 50 7f 00` | `00719CA0` | 虚方法 = 本表 **slot 5（Load）**：`00719CAD call 0055AAC0` 基类 → 装基表 `007EAEC0/007EADF4` → 装本类 3 表 → `00719CFF ff 51 0c`（IStream **Read** 槽）读入 |

- atexit 注册：**0**（两函数 `push imm32` 均空）。无析构器写点（该类 dtor 未在本表留写点）。
- 说明：本表写点仅 2 处，无删除析构器/非删除析构器重装点 —— 不触 ㉓ 陷阱。

### 一致性
"③b② QI / 0055A9B0 基类 / E_POINTER·E_NOINTERFACE·S_OK / taken 00719E87 / fall 00719E5B / ② 007F50CC slot0 offset0 / ④ ctor 00718000@0071805E + push 0x4C new" 全部命中（`0x4C` 见 `006C4C3C`）。

---

## 4. `0075C7F0` — S11 WalkLocomotionClass::slot0 → **PASS**（③b② = QueryInterface）

### ②
- 主虚表 `007F6AC4`，COL `0080D2A8`，字节 `00…00 | f0 7b 84 00 | 98 d2 80 00` → `offset=0`、`pTD=00847BF0`（绝对 VA）、`pCHD=0080D298`。
- `pTD+8` = `.?AVWalkLocomotionClass@@`（字节 `2e 3f 41 56 57 61 6c 6b 4c 6f 63 6f 6d …`）。
- 槽位：`007F6AC4` 首 dword `f0 c7 75 00` = `0075C7F0` ⇒ slot 0，表内唯一。
- 次对象表排除：`[esi+4]=007F69F8`（COL `0080D240` offset **4**，slot0 `0075CC30 sub [esp+4],4; jmp 0075C7F0`）、`[esi+0x18]=007F69D4`（COL `0080D228` offset **0x18**，slot0 `0075CC60 sub [esp+4],0x18; jmp 0075C7F0`）。

### ③b②（3b2）
`0075C802 e8 a9 e1 df ff call 0055A9B0` → `0075C807 3d 02 40 00 80 cmp eax,0x80004002` → `0075C80C 75 39 jne 0075C847` →
`0075C814 bf 10 9b 7e 00 mov edi,007E9B10` / `0075C81B f3 a7 repe cmpsd` / `0075C81E 75 0e jne` →
命中 `0075C824 8d 43 18 lea eax,[ebx+0x18]` / `0075C82B 89 45 00 mov [ebp],eax` /
`0075C83F 8b 0b` + `0075C842 ff 51 04 call [ecx+4]`(AddRef) + `0075C845 33 c0`(S_OK)；
未命中 `0075C836 b8 02 40 00 80 mov eax,0x80004002`；taken 路 `0075C847` `pop/pop/pop/ret 0xc`。
- 外部调用方分支：`006C47EC 8b f8` / `006C47EE 85 ff test edi,edi` / `006C47F0 7d 09 jge 006C47FB`，负码路 `006C47F8 ff 52 20`（Release）。

### ④
`006C47E5 8b 06 mov eax,[esi]` → **`006C47EA ff 10 call dword ptr [eax]`** = 派发 slot 0；同函数 `006C47BC 6a 3c push 0x3c` + `006C47BE call 0x7C8E17`(new) + `006C47CA mov ecx,eax` + `006C47CC call 0075AA90`(ctor)。
构造器写点 `0075AADF c7 06 c4 6a 7f 00 mov [esi],007F6AC4`（`0075AA93 call 0055A6C0` 基类 ctor，末尾 `mov eax,esi; ret`）。

### ④ ≠ ②
② = 表内容 `007F6AC4+0`；④ = 派发 `006C47EA` / 构造器写点 `0075AADF` ⇒ `no`。

### ㉓ 全枚举（`007F6AC4`，4 处）
| 写点 | 所在函数 | 分类 | 处置 |
|---|---|---|---|
| `0075AADF c7 06 c4 6a 7f 00` | `0075AA90` | 真构造器 | **④ 锚** |
| `0075AB03 c7 06 c4 6a 7f 00` | `0075AB00` | **非删除析构器**（释放成员 `[esi+0x38]` + `0075AB26 call 0055A6F0` 基类 dtor + `ret`；无 caller/push） | 排除 |
| `0075C6A3 c7 06 c4 6a 7f 00` | `0075C680` | 虚方法 = 本表 **slot 5（Load）**：`0075C68D call 0055AAC0` 基类 → 装 3 表 → `0075C6C3 ff 50 0c`（IStream **Read**） | 非析构器 |
| `0075CBE3 c7 06 c4 6a 7f 00` | `0075CBE0` | **删除析构器**（`0075CC0B f6 44 24 08 01 test byte[esp+8],1` + `0075CC13 call 0x7C8B3D` + `ret 4`） | 排除 |
- atexit 注册：**0**（4 函数 `push imm32` 全空）。

### 一致性
"③b② QI / 0055A9B0 / E_POINTER·E_NOINTERFACE·S_OK / taken 0075C847 / fall 0075C81B / ② 007F6AC4 slot0 offset0 / ④ ctor 0075AA90@0075AADF + push 0x3C new" 全部命中（`0x3C` 见 `006C47BC`）。

---

## 附：4 行共性（三个 QI 行）
- 三行行体除 `rel32` 外**逐字节同构**（各 `0x5B` 字节），比对的常量 IID 同为 `007E9B10`（ILocomotion 族），说明是同类 LocomotionClass 的 QI 覆写，`lea eax,[ebx+0x18]` 返回的 +0x18 次对象与 ctor 装的第三张表 `007F2D68/007F4FDC/007F69D4`（COL offset 均为 0x18）严格对应 —— 语义自洽，非"凑数"。
- 三行 ④ 均为**真实活虚表派发**（`ff 10` on `eax=[esi]`，`esi` 来自 ctor 返回值），并在同一处以 `test/jge` 消费返回值 ⇒ ③b② 与 ④ 同时落地，且 ④ 不是 direct-only、不是析构器锚点。
- 三行 ②④ 均不同源：② 用表内容 + RTTI，④ 用派发指令 + 构造器写点。

## 陷阱自查
| 陷阱 | 结果 |
|---|---|
| 读写方向写反 | `006DBE00` 方向 = **写出**（`ff 50 10` 槽 4 = Write，内存→流），并与 slot5 Load 用 `ff 50 0c`（槽 3 = Read）成对复核；**未写反**。3 QI 行不涉及读写方向。 |
| ④ 锚点落在析构器（㉓） | 4 行 ④ 锚点全部是真构造器（`006D1C20 / 0069EC50 / 00718000 / 0075AA90`），已排除删除析构器（`006DC470 / 006A42B0 / 0075CBE0`）与非删除析构器（`006D1E80 / 0069ECF0 / 0075AB00`），且 atexit 注册数为 0。 |
| 小成员表当主虚表 | 4 行主表 COL `offset` 全为 0，且构造器把该表写在 `[obj+0]`；`[esi+4]`/`[esi+0x18]` 次对象表（offset 4/0x18）已识别为 thunk 表并排除。 |
| RTTI 绝对 VA | pTD/pCHD 全 ≥ `0x400000`（`00842A38/0083F880/00844538/00847BF0`），未见 RVA 误读。 |
| TD+8 内联串 | 4 处 `TD+8` 首 dword 均 `0x56413F2E`（`.?AV`），为内联字符串非指针。 |
| ③ 可伪证性 | 4 行均为多值状态码（`0` / `0x80004002` / `0x80004003` 及 IStream 失败负码），非 `{0,1}` 布尔；均非纯转发（各含自有裁决）；`006DBE00` 的"包装性"已在边际披露中说明。 |

# NAMED_PUSH_AUDIT14 — 异族独立审计 VERDICT

## 取行法（本轮范围）
来源 `NAMED_PUSH_S11_B1/delta.tsv`（6 列：`entry subsystem name one_line_semantics grade evidence_path`）。第 2 行起取全部 4 个 entry：`004AF720`、`004B62C0`、`004B6470`、`0054DC60`（表头 `entry` 不计）。base_rate.tsv 自报本批 18 行 / ring2_ok 4 / ring3b_ok 4 / ring4_ok 18 / all_four 4 / rate 0.2222。

## 工具与镜像
- 镜像 `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，本地 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡片期望一致）。
- ImageBase `0x400000`，`.text=[0x401000,0x7E038D)`；capstone 5.0.7（skipdata=True）+ pefile 2024.8.26 + Python 3.12.10。
- 所有地址/字节来自本审计员对上述字节的独立反汇编（`work/auditlib.py` + `work/probe_*.py`）。delta.tsv / REPORT.md / EVIDENCE/ROW_*.txt 仅作地址线索，不作证据。

---

## ROW 004AF720 — DriveLocomotionClass::slot0 — **PASS**

**①/② 类身份独立成立**
- 主虚表 `0x7E7F7C`，slot0 内容 `20 F7 4A 00` = `0x004AF720`（= 本 entry）✓
- `vt[-4]` @`0x7E7F78` = COL 指针 `0x007FFEB0`。COL 原始字节 `00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 48 02 82 00 | a0 fe 7f 00`：`sig=0, offset=0, cd=0, pTD=0x820248`。
- TD @`0x00820248`，名串 `2E 3F 41 56 44 72 69 76 65 4C 6F 63 6F 6D 6F 74 69 6F 6E 43 6C 61 73 73 40 40` = `.?AVDriveLocomotionClass@@` ✓
- **主表判定**：`COL.offset=0` ✓；构造器 `0x4AF540` 在 `0x4AF5C2` 以 `C7 06 7C 7F 7E 00` (`mov [esi],0x7E7F7C`) 装到 `[this+0]` ✓；slot0 首字节 `53 8b 5c 24 08 55`（真函数 prologue），非 `83 6C 24 xx;jmp` 型 this 调整 thunk ✓。副表 `0x7E7EB0`(offset=4)、`0x7E7E8C`(offset=0x18) 才装 thunk（`0x4B4D90: sub [esp+4],4; jmp 0x4AF720`）；本行未取副表。

**②（③b②）具体形态**
- 本体 @`0x4AF732` `E8 79 B2 0A 00` = `call 0x55A9B0`；@`0x4AF737` `3D 02 40 00 80` = `cmp eax,0x80004002` (E_NOINTERFACE)；@`0x4AF73C` `75 39` = `jne 0x4AF777`。cmp→jne 相邻，之间无 eax 覆写。
- 被调 `0x55A9B0` 返回约定（多值、可伪证）：@`0x55A9B8` `B8 03 40 00 80` `mov eax,0x80004003`(E_POINTER)+@`0x55A9BD` `C2 0C 00` ret 0xc；@`0x55AA41` `B8 02 40 00 80` `mov eax,0x80004002`(E_NOINTERFACE)+@`0x55AA46` ret 0xc；@`0x55AA4F` `33 C0` xor eax,eax → @`0x55AA51` ret 0xc (S_OK)。非 {0,1} 布尔。
- 调用方拿分支的指令：`0x4AF73C jne`。taken → `0x4AF777: pop esi; pop ebp; pop ebx; ret 0xc`（eax 不碰，基类 HRESULT 原样上抛，不做 IID 比较）；fallthrough → `0x4AF73E` `push edi; mov ecx,4; mov edi,0x7E9B10; xor eax,eax; repe cmpsd` 比 16B IID，命中 @`0x4AF754` `lea eax,[ebx+0x18]` → @`0x4AF75B` `mov [ebp],eax` → @`0x4AF772` `call [ecx+4]`(AddRef) → @`0x4AF775` `xor eax,eax`(S_OK)；未命中 @`0x4AF766` `mov eax,0x80004002`。两路动作真不同。非 ③a，无「被调用者内部写充当循环内非栈写」。

**③ ④ 使用见证独立成立**
- 活虚表派发：ctor `0x4AF540` 先 @`0x4AF543` `E8 78 B1 0A 00` `call 0x55A6C0`（基类 ctor），再 @`0x4AF5C2` 装 `0x7E7F7C` 于 `[this+0]`，另装副表 `[esi+4]=0x7E7EB0`、`[esi+0x18]=0x7E7E8C`，尾 `mov eax,esi; pop esi; ret` 返 this。
- 实例化链：@`0x6C403C` `6A 70` push 0x70 → @`0x6C403E` `E8 D4 4D 10 00` `call 0x7C8E17`(operator new) → @`0x6C404C` `E8 EF B4 DE FF` `call 0x4AF540`。堆上活对象。
- 直接 `call` 到 entry = 0（全镜像扫描仅见 2 处 `jmp` thunk @`0x4B4D95/@0x4B4DC5`，属副表 this 调整跳板，非调用点）。非 direct-only。

**④ 与 ② 不同源**：② 用 `0x7E7F7C` 槽值+COL/TD；④ 用 ctor 安装点 `0x4AF5C2` + new 链 `0x6C403E`。地址不同 ⇒ `same_source=no`。

**㉓ 删除式析构器排除**：同类 deleting dtor `0x4B4D00`（@`0x4B4D26` `call 0x55A6F0` 基类 dtor、@`0x4B4D2B` `test byte [esp+8],1`、@`0x4B4D33` `call 0x7C8B3D` operator delete）。该 dtor 确在 @`0x4B4D03` 重装 `0x7E7F7C`，但本行 ④ 锚点在 ctor `0x4AF5C2`，**未在析构器内**。排除成立。

**⑤ 语义**：name `DriveLocomotionClass::slot0`、one_line 称 QueryInterface 实现 —— 实测为 IID 比较/AddRef/S_OK-E_NOINTERFACE 的 QI 实现，方向、子型均相符。

---

## ROW 004B62C0 — DropPodLocomotionClass::slot6 — **PASS**

**①/② 类身份独立成立**
- 主虚表 `0x7E8344`，slot6 = `0x7E8344 + 0x18 = 0x7E835C`，内容 `C0 62 4B 00` = `0x004B62C0`（= 本 entry）✓（整表 dump：slot0=0x4B6470, slot1=0x4B66A0, …, slot6=0x4B62C0, slot8=0x4B66F0）。
- `vt[-4]` @`0x7E8340` = COL 指针 `0x008000A8`。COL 字节 `00 00 00 00 | 00 00 00 00 | 00 00 00 00 | f8 02 82 00 | 98 00 80 00`：`sig=0, offset=0, cd=0, pTD=0x8202F8`。
- TD @`0x008202F8` 名串 = `.?AVDropPodLocomotionClass@@` ✓
- **主表判定**：`COL.offset=0` ✓；ctor `0x4B5AB0` @`0x4B5ADD` `C7 06 44 83 7E 00` (`mov [esi],0x7E8344`) 装 `[this+0]` ✓；slot0 (`0x4B6470`) 首字节 `53 8b 5c 24 08 55` 真函数 ✓。副表 `0x7E8278`(offset=4,thunk `0x4B6740`)、`0x7E8254`(offset=0x18,thunk `0x4B6770`) 未取用。

**②（③b②）具体形态**
- 本体 @`0x4B62D1` `E8 8A 47 0A 00` = `call 0x55AA60`；@`0x4B62D6` `85 C0` = `test eax,eax`；@`0x4B62D8` `0F 8C 9E 00 00 00` = `jl 0x4B637C`（按符号判负 HRESULT）。test→jl 相邻，之间无 eax 覆写。
- 被调 `0x55AA60` 返回约定（多值）：参数空 → @`0x55AA6B` `mov eax,0x80004003`(E_POINTER)+@`0x55AA71` ret 0xc；内层流 `call [eax+0x10]` 后 @`0x55AA8D` `jl 0x55AAB2` 透传；再 @`0x55AAA4` `jl 0x55AAB2` 透传；@`0x55AAB4` `C2 0C 00` ret 0xc 不碰 eax（成功侧 0 由调用链传入）。非布尔。
- 调用方拿分支的指令：`0x4B62D8 jl`。taken → `0x4B637C: pop edi; pop esi; ret 0xc`（eax 不碰，负错误码原样上抛，整段读入跳过）；fallthrough → @`0x4B62DE` `mov eax,[edi+0x2c]`、@`0x4B62FA` `call [ecx+0x10]`、@`0x4B6319` `call [ecx]`(QI)、@`0x4B6325` `call 0x4B4D60`、@`0x4B6364` `FF 15 F4 15 7E 00` `call [0x7E15F4]`（u32(0x7E15F4)=0x410868），尾 @`0x4B637A` `mov eax,esi`。两路动作真不同。非 ③a。

**③ ④ 使用见证独立成立**
- ctor `0x4B5AB0` 先 @`0x4B5AB3` `call 0x55A6C0`，再 @`0x4B5ADD` 装 `0x7E8344` 于 `[this+0]`，另装 `[esi+4]=0x7E8278`、`[esi+0x18]=0x7E8254`。
- 实例化链：@`0x6C493C` `6A 30` push 0x30 → @`0x6C493E` `call 0x7C8E17`(new) → @`0x6C494C` `call 0x4B5AB0`。
- 直接 `call` 到 `0x4B62C0` = 0（全镜像无 call/jmp 命中）。非 direct-only。

**④ 与 ② 不同源**：② 用槽 `0x7E835C`+COL/TD；④ 用 ctor 安装 `0x4B5ADD`+new 链 `0x6C493E`。② 槽、③ 站点 `0x4B62D1` 各自独立 ⇒ `same_source=no`。
- 注：本行与 004B6470 同属 `0x7E8344` 主表、共用 ctor 安装点 `0x4B5ADD`；但同一 ctor 安装整张表（含全部槽），各行的 ② 槽与 ③ 站点互不相同，不构成「同一虚表槽既证身份又证使用」。

**㉓ 删除式析构器排除**：deleting dtor `0x4B66F0`（@`0x4B6716` `call 0x55A6F0`、@`0x4B671B` `test [esp+8],1`、@`0x4B6723` `call 0x7C8B3D`）。其 @`0x4B66F3` 重装 `0x7E8344`，但本行 ④ 锚点在 ctor `0x4B5ADD`，**未在析构器内**。排除成立。

**⑤ 语义**：name `DropPodLocomotionClass::slot6`、one_line 称「流读入/序列化入口」—— 实测先调流读助手 `0x55AA60` 后做实质读入（`call [ecx+0x10]`/`call [ecx]`/`call 0x4B4D60`/`call [0x7E15F4]`），为读入方向，方向、子型相符。

---

## ROW 004B6470 — DropPodLocomotionClass::slot0 — **PASS**

**①/② 类身份独立成立**
- 主虚表 `0x7E8344`，slot0 内容 `70 64 4B 00` = `0x004B6470`（= 本 entry）✓
- COL @`0x8000A8`：`sig=0, offset=0, pTD=0x8202F8` → TD 名串 `.?AVDropPodLocomotionClass@@` ✓（与上行同主表同类）。
- **主表判定**：`COL.offset=0` ✓、装 `[this+0]` @`0x4B5ADD` ✓、slot0 首字节 `53 8b 5c 24 08 55` 真函数 ✓（非 thunk）。

**②（③b②）具体形态**
- @`0x4B6482` `E8 29 45 0A 00` `call 0x55A9B0`；@`0x4B6487` `3D 02 40 00 80` `cmp eax,0x80004002`；@`0x4B648C` `75 39` `jne 0x4B64C7`。相邻、无 eax 覆写。
- 被调 `0x55A9B0` 多值返回（同 004AF720：`0x80004003` / `0x80004002` / `0`）。
- 调用方拿分支的指令：`0x4B648C jne`。taken → `0x4B64C7: pop; pop; pop; ret 0xc`（eax 不碰）；fallthrough → @`0x4B648E` IID `repe cmpsd`，命中 @`0x4B64A4` `lea eax,[ebx+0x18]` → @`0x4B64AB` `mov [ebp],eax` → @`0x4B64C2` `call [ecx+4]` → @`0x4B64C5` `xor eax,eax`；未命中 @`0x4B64B6` `mov eax,0x80004002`。两路真不同，非 ③a。

**③ ④ 使用见证独立成立**
- ctor `0x4B5AB0` @`0x4B5AB3` `call 0x55A6C0`，@`0x4B5ADD` 装 `0x7E8344` 于 `[this+0]`；实例化 @`0x6C493C` push 0x30 → @`0x6C493E` `call 0x7C8E17` → @`0x6C494C` `call 0x4B5AB0`。
- 直接 `call` 到 `0x4B6470` = 0（仅见 2 处副表 `jmp` thunk `0x4B6745/@0x4B6775`）。非 direct-only。

**④ 与 ② 不同源**：② 槽 `0x7E8344`+COL/TD；④ ctor 安装 `0x4B5ADD`+new 链 `0x6C493E` ⇒ `same_source=no`。

**㉓ 删除式析构器排除**：dtor `0x4B66F0` 的 @`0x4B66F3` 重装 `0x7E8344`，本行 ④ 锚点在 ctor `0x4B5ADD`，**未在析构器内**。排除成立。

**⑤ 语义**：name `DropPodLocomotionClass::slot0`、QueryInterface 实现 —— 实测 QI，方向、子型相符。

---

## ROW 0054DC60 — JumpjetLocomotionClass::slot0 — **PASS**

**①/② 类身份独立成立**
- 主虚表 `0x7ECE34`，slot0 内容 `60 DC 54 00` = `0x0054DC60`（= 本 entry）✓
- `vt[-4]` @`0x7ECE30` = COL `0x00804CF0`。COL 字节 `00 00 00 00 | 00 00 00 00 | 00 00 00 00 | 48 96 82 00 | e0 4c 80 00`：`sig=0, offset=0, pTD=0x829648`。
- TD @`0x00829648` 名串 = `.?AVJumpjetLocomotionClass@@` ✓
- **主表判定**：`COL.offset=0` ✓；ctor `0x54AC40` @`0x54ACC3` `C7 06 34 CE 7E 00` (`mov [esi],0x7ECE34`) 装 `[this+0]` ✓；slot0 首字节 `53 8b 5c 24 08 55` 真函数 ✓。副表 `0x7ECD68`(offset=4,thunk `0x54DFF0`)、`0x7ECD44`(offset=0x18,thunk `0x54E020`) 未取用。

**②（③b②）具体形态**
- @`0x54DC72` `E8 39 CD 00 00` `call 0x55A9B0`；@`0x54DC77` `3D 02 40 00 80` `cmp eax,0x80004002`；@`0x54DC7C` `75 39` `jne 0x54DCB7`。相邻、无 eax 覆写。
- 被调 `0x55A9B0` 多值返回（同上）。
- 调用方拿分支的指令：`0x54DC7C jne`。taken → `0x54DCB7: pop; pop; pop; ret 0xc`（eax 不碰）；fallthrough → @`0x54DC7E` IID `repe cmpsd`，命中 @`0x54DC94` `lea eax,[ebx+0x18]` → @`0x54DC9B` `mov [ebp],eax` → @`0x54DCB2` `call [ecx+4]` → @`0x54DCB5` `xor eax,eax`；未命中 @`0x54DCA6` `mov eax,0x80004002`。两路真不同，非 ③a。

**③ ④ 使用见证独立成立**
- ctor `0x54AC40` @`0x54AC46` `call 0x55A6C0`，@`0x54ACC3` 装 `0x7ECE34` 于 `[this+0]`，另装 `[esi+4]=0x7ECD68`、`[esi+0x18]=0x7ECD44`。
- 实例化链：@`0x6C41BC` `68 98 00 00 00` push 0x98 → @`0x6C41C1` `call 0x7C8E17`(new) → @`0x6C41CF` `call 0x54AC40`。
- 直接 `call` 到 `0x54DC60` = 0（仅见副表 `jmp` thunk `0x54DFF5/@0x54E025`）。非 direct-only。

**④ 与 ② 不同源**：② 槽 `0x7ECE34`+COL/TD；④ ctor 安装 `0x54ACC3`+new 链 `0x6C41C1` ⇒ `same_source=no`。

**㉓ 删除式析构器排除**：deleting dtor `0x54DFA0`（@`0x54DFC9` `call 0x55A6F0`、@`0x54DFCE` `test [esp+8],1`、@`0x54DFD6` `call 0x7C8B3D`）；其 @`0x54DFA3` 重装 `0x7ECE34`，本行 ④ 锚点在 ctor `0x54ACC3`，**未在析构器内**。排除成立。

**⑤ 语义**：name `JumpjetLocomotionClass::slot0`、QueryInterface 实现 —— 实测 QI，方向、子型相符。

---

## 逐行判定汇总
| entry | ② | ③b | ④ | ④≠② | ㉓ | ⑤ | verdict |
|---|---|---|---|---|---|---|---|
| 004AF720 | ✓ | 3b2 ✓ | ✓ | no ✓ | ✓ | ✓ | **PASS** |
| 004B62C0 | ✓ | 3b2 ✓ | ✓ | no ✓ | ✓ | ✓ | **PASS** |
| 004B6470 | ✓ | 3b2 ✓ | ✓ | no ✓ | ✓ | ✓ | **PASS** |
| 0054DC60 | ✓ | 3b2 ✓ | ✓ | no ✓ | ✓ | ✓ | **PASS** |

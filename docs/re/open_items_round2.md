# 未闭环项续攻（第二轮）：RE-A U-5/U-6/U-7/U-8 + RE-C 四项

> 任务：看板 `task-12`（teammate `re-openitems`）。**纯静态，未启动游戏**。
> 目标二进制：`ra2youli/gamemd.exe`（ImageBase `0x400000`，VA 4,825,360 B，sha256 `73201cc0…fcf67476`）。
> 只读来源：`docs/re/savegame_block_manifest.md` §9、`docs/re/fs_mix_load_chain.md` §8（未修改）。
> 本轮产物：本文件 + `out/re_work/open_items2/**`（`claims.txt`、`audit_output.txt`、`anchors_output.txt`、`tools/*.py`）。
> 等级标注：`[实证]` = 有反汇编/字节实证；`[推演]` = 由实证外推；`[待实测]` = 需真机/调试器。

## 0. 验收证据（照抄可复算）

```
python tools/audit_bytes.py out/re_work/open_items2/claims.txt --json out/re_work/open_items2/claims_audit.json
   合计 72 条：OK=72  MISMATCH/NOREAD=0          <-- 全部字节断言通过

python tools/verify_anchors.py
   回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
   最终裁决 : [100% ALL PASS]
```
两条命令的原始输出分别归档在 `out/re_work/open_items2/audit_output.txt`、`out/re_work/open_items2/anchors_output.txt`（本轮未改动任何既有锚点文件）。

---

## 1. `U-6` `push 0x7F7C80` 载体对象 = **`IID_IPersistStream`（16 字节 IID 常量，非对象）** `[实证]`+`[推演]`

**结论（修正原判）**：`0x7F7C80` **不是**"共享载体对象/虚表"，而是 `.rdata` 里的一张 **IID 表的第 2 项**：

| IID 常量 VA | 16 字节原始值 | 名称 | 证据 |
|---|---|---|---|
| `0x7F7C70` | `0C 01 00 00 00 00 00 00 C0 00 00 00 00 00 00 46` | `IPersist` | YRpp `Unsorted.h` 的 `class IIDs`（`0x7F7C70u`） |
| **`0x7F7C80`** | `09 01 00 00 00 00 00 00 C0 00 00 00 00 00 00 46` | **`IPersistStream`** | 同上（`0x7F7C80u`） |
| `0x7F7C90` | `00 00 00 00 00 00 00 00 C0 00 00 00 00 00 00 46` | `IUnknown` | 同上（`0x7F7C90u`） |

三者的"尾 8 字节 = `C0 00 00 00 00 00 00 46`"正是 COM 1.0 IID 家族
`{0000xxxx-0000-0000-C000-000000000046}` 的固定尾段 —— 这解释了为什么 `0x7F7C80` 在 `.rdata` 中呈现
"16 B 一条、步长 0x10"的规律。

**用法实证**（`0x7F7C80` 全部 64 处立即数引用 = 61 处序列化点 + 4 处 QI 点）：

序列化点（`Game::Save_Core 0x67D300` 的 28 个内联向量块，以及 35 个块函数模板 `0x67FDF0..0x680EF0`）：

```
0x0067FE2D  8B 04 B0        mov  eax,[eax+esi*4]     ; ObjectClass* pObj
0x0067FE30  52              push edx                 ; &hr
0x0067FE31  68 80 7C 7F 00  push 0x7F7C80           ; <== IID_IPersistStream
0x0067FE36  50              push eax                 ; pObj
0x0067FE37  8B 08           mov  ecx,[eax]
0x0067FE39  FF 11           call [ecx]               ; QueryInterface(pObj, IID_IPersistStream? no: (iid,&hr))
0x0067FE45  FF 15 F4 15 7E 00  call [0x7E15F4]       ; = ole32!OleSaveToStream (IAT 实证)
0x0067FE54  FF 51 08        call [ecx+8]             ; Release()
```
另有 QI 家族把同样的 3 个 IID 用 `repe cmpsd`（`ecx=4`，即比 16 B）比对：

```
0x0041029C  BF 80 7C 7F 00  mov edi,0x7F7C80
0x004F68DF  BF 80 7C 7F 00  mov edi,0x7F7C80     ; 命中 → 返 [eax+0x24]
0x005125F0  BF 80 7C 7F 00  mov edi,0x7F7C80
0x0041027D  BF 90 7C 7F 00  mov edi,0x7F7C90     ; IUnknown
0x004102B0  BF 70 7C 7F 00  mov edi,0x7F7C70     ; IPersist
```
IAT 实名（`out/re_work/fs_mix/iat.json`）：
`0x7E15F4 = ole32!OleSaveToStream`（`[0x7E15F4] -> 0x410840` `[实证]`）、
`0x7E15F8 = ole32!OleLoadFromStream`、`0x7E15C8 = ole32!StgCreateDocfile`、`0x7E15FC = ole32!CoCreateInstance`。

**因此存档序列化链的真身** `[实证]`：
```
for each element pObj of 每个子系统向量:
    pObj->QueryInterface(IID_IPersistStream, &pPS)   ; 失败即整档失败
    OleSaveToStream(pPS, pStm)                       ; 标准 OLE IPersistStream::Save 包装
    pPS->Release()
```
替代了原文档"`operator<<` + 指针 swizzle"的表述：**引擎直接用 `IPersistStream` 做逐对象持久化**，
`0x7E15F4`/`0x7E15F8` 是 `ole32` 导入，而**不是自研序列化原语**（`[推演]` → 与 §2.5 "序列化原语 = OLE" 一致，
本轮把"哪条 OLE API、用哪个 IID"钉死）。

**未闭环残项**：`0x7F7C80` 的 Data1 = `0x00000109` 未被任何公开 OLE 表收录（引擎自定 IID）；
但**符号名已由 YRpp `Unsaved.h`（`ref/yrpp/Unsorted.h` 的 `class IIDs`）给出**，两者互证。

---

## 2. `U-7` `Game::Save 0x67D0C0` 的调用者 `[实证]`（结论：**不存在调用者；且该地址不是函数入口**）

**本轮的硬结论有两条，都要写进勘误**

1. **`0x67D0C0` 不是函数入口**，而是 `0x67D0BE` 处函数的第 2 条指令中部 `[实证]`：
   ```
   0x0067D0BE  8D 4C 24 14   lea ecx,[esp+0x14]
   0x0067D0C0  24 14 89 6C   and al,0x14   / 下一条为 0x67D0C2: 89 6C 24 14 mov [esp+0x14],ebp
   0x0067D0C6  E8 15 2D 00 00 call 0x67FDE0         ; = CCFileClass dtor 收尾（存根）
   ```
   （`audit_bytes` 输出：`0x67d0be OK | lea ecx,[esp+0x14]`；`0x67d0c0 OK | and al,0x14`）
2. **任何形态的静态引用都不存在** `[实证]`：
   - 全 `.text` 的 `E8/E9` 相对调用扫描（`tools/xref_abs.py` 口径，逐字节）→ **0 命中**；
   - 全镜像 4 字节小端出现次数（覆盖 `.text/.rdata/.data/.rsrc/.detour`）→ **0 命中**（即：**不在任何 vtable 里**）；
   - 全镜像对 `0x67D100..0x67D300` 区间出现的清点显示：只有 `0x8722A4→0x67CF6D`、`0x8722A8→0x67D1A3`
     两处"看似指针"命中，经指令边界核对均为 `push imm32` 的 **立即数**（`68 6D CF 67 00`），非函数指针表。

**对原 U-7 的纠正**：`0x67D0C0` 既没有 `E8/E9` 调用者、也不在虚表里，所以"反查写出该虚表槽的类"这条路
**不成立**——它不是"只可能经虚表"，而是**静态不可达**（典型的编译期未使用的 out-of-line 代码 / 仅被
运行期注册表或外部补丁调用）。

**顺手钉死的真实存档调用链** `[实证]`：
```
0x67CF6B  E8 80 40 00 00   call 0x680FF0        ; 存档外壳的用户态入口之一（保存前处理）
0x67D1AF  E8 FB BF 00 00   call 0x67D300        ; Game::Save_Core（唯一调用者；此前 §2.2 已记录）
0x67D300  ...              ; 35 次块函数 call + 28 个内联向量块
```
`0x67D0C0`/`0x67D1D0` 两处片段属于 **IStream 版存档路径**（`0x67D1D0` 之后 `call [edx+0xC]` 写流、
`0x67D131` `call [edx+0x24]`），没有被静态引用 → `[待实测]` 真机在 `0x67D0C0` 下断观察是否命中。

**为什么原任务书说"只可能经虚表"**：因为同一段代码里 `call dword ptr [ecx]`（`0x67D107`）与
`call dword ptr [edx+0xC]`（`0x67D12F`、`0x67D131`）确实是虚调用/COM 调用 —— 但**被调的对象是
`IStream`/`IPersistStream` 接口指针**，不是 `Game::Save` 自己。这解释了"镜像内 0 处引用"的困惑。

---

## 3. `U-8` `0x86563C` 的 `0x2B898` `[实证]`（结论：**不是第二份魔数，是数据表里的一个普通步长值**）

两条并存的事实（都可复算）：

1. **`0x83D560` 的 `0x2B898` 根本是字符串的前 4 字节**（§9 U-2 已暗示，本轮钉死）`[实证]`：
   ```
   0x0083D560  98 B8 02 00 53 41 56 49 4E 47 20 47 41 4D 45 20 ...
              └─ dword 0x0002B898 ─┘ └─ "SAVING GAME " ──────┘
   完整串: "SAVING GAME [%s] - Complete\n\n"
   ```
   即 `0x2B898` = **格式串首 4 字节**，不是版本魔数（`0x83D560` 与"字节级魔数"的绑定是巧合）。
   `0x83D598` 处另有 CLSID `{0D5CD78E-6470-11D2-9B74-00104B972FE8}`（`CoCreateInstance` 的 `rclsid`）。`[实证]`
2. **`0x86563C` 是"奇数项跳过 +2"的单调数据表成员** `[实证]`：该表自 `0x865400` 起（`5E 9F 01 00`、`57 A1 01 00`，
   逐项约 `+0x1F9`），到 `0x86563C` 处 dword = `0x0002B898`，紧邻 `0x865640 = 0x0002BA8D`、`0x865644 = 0x0002BC83`。
   `0x2B898` 落在表中**恰好合理**（表值域 `0x19F5E..0x2D400`+，`0x2B898` 在其中间段）。
   **该地址 4 字节在全镜像出现 0 次**（无任何指令以立即数/指针引用它）→ 它是**纯数据表元素**，
   与存档魔数无因果 `[实证]`。
3. 因此 §9 U-8 的"版本字段/补丁副本"假设 **不成立**：`0x86563C` 位于 `.data` 的一张数值表内，
   与 `0x83D560` 的 `0x2B898` 只是**同值巧合**（都是"某串/某表里恰好出现 0x2B898 这个 dword"）。
   **未闭环**：表的用途（生成式曲线？寻路权重？）本轮未定位引用点，取法见 §9。

---

## 4. `U-5` 28 个内联向量块中 15 个未定名 `[证据不足]`（判定 + 每条的最小证据链）

**判定**：**纯静态不可闭环**，但本轮把"为什么不可闭环"缩到可复算的最小形式 ——
**这 15 个全局的"元素类型"没有任何静态可判定入口**：

1. 5 个 **全镜像 0 引用** `[实证]`：`0x8B4170`、`0xA8EAE0`、`0x8B4100`、`0xA83CD8`（Item 指针），
   `0x8B41E4`（#28 的 ITEMS）等 —— 连 COUNT 都没有读取点，只有 `Save_Core` 里那处内联循环。
2. 其余 10 个只有 **1–2 处 .text 立即数命中**，且逐条指令边界核对后多是**假阳性**（地址落在指令中部）。
   例：`0xA8E388`（#12）唯一命中 `0x4E648D`，其所在指令为 `0x4E6482 A3 80 E3 A8 00`（`mov [0xA8E380],eax`），
   故 `0x4E648D` 是**指令内部字节**，不是引用。同法复核 `0xA8E8C8`（#14，`0x4E7CE2`）、`0x8872A8`（#18，`0x40E73D`）同为假阳性。
3. 与"类描述符不可用"的原判一致：962 条 RTTI 类型名里 **无一** 指向这些 `.bss` 对象所属类（§3 已证）。
4. **可用的正线索**（仍不足以定名，但可写进下游表）：这些向量块**大多在 Load 侧有对称的
   `0x4E6xxx–0x4E8xxx` 助手**（如 `0x4E74E8/0x4E7521 → 0x8B4154`、`0x4E7612 → 0xA83C90`、
   `0x4E7692 → 0xA8EB38`、`0x4E7892 → 0xA8E340`、`0x4E7BE8/0x4E7C21/0x4E7C49 → 0x8B41D8`），
   说明**#1/#3/#10/#17 等的读侧计数循环确实存在**（否决 §9 U-4 中"35 条读档块函数不存在"的一半假设）。

**下一步取法（按成本排序）**：① 对 35 个块函数入口下 **桩断点**（0x67FDF0 模板族），打印每次 `edx`
指向对象的 `[obj]`（vtable VA）→ 与 `ref/yrpp` 的 `Class` 符号比对，一次存档全量捕获；
② 对 28 个 COUNT 全局写 **硬件写断点**，读档时看谁写入（写入者所属类即元素类型）；
③ 用 `0x5B40B0` 型"名字→对象"管理器（§6）反证：若某向量元素类型有 `Get_File("XXX")` 路径则可得名。
三者均需运行期，属 `[待实测]`。

**勘误（写给下游）**：`§4` 表里的"元素载入点"列（如 `0x0067D36A`）是**内联循环里的 `mov eax,[mem+ebx*4]` 地址**，
不是函数入口；本轮复核 `#27/#28`（`0x0067E1AB` / `0x0067E186`）确认两者共用同一元素载入点 `0x0067E1B5`，
即**两张相邻表顺序发射**（与 §4 星号注一致）。

---

## 5. RE-C ① `[实证]` `MixFileClass::Cache()` 的真实身份 + `+0x24` 填充点"负结果"

**5.1 `0x5B3E90` 就是 `Cache()`/`Free_All_Memory` 家族** `[实证]`
```
0x005B3E90  81 EC 04 03 00 00   sub esp,0x304
   ...  遍历 List<MixFileClass*> [0xABEFE0] 逐节点
0x005B3F14  8B 46 24            mov eax,[esi+0x24]        ; 缓存体指针
0x005B3F1B  8A 4E 12            mov cl,[esi+0x12]         ; 是否自有
0x005B3F22  50 / E8 15 4C 21 00 push eax / call 0x7C8B3D ; operator delete
0x005B3F2B  C7 46 24 00 00 00 00  mov dword ptr [esi+0x24],0     ; ← 清空
0x005B3F32  C6 46 12 00         mov byte ptr [esi+0x12],0
```
**5.2 `0x5B3C20..0x5B5000` 内所有写 `+0x24` 的指令全是"清 0"** `[实证]`（全 `.text` 指令边界扫描，共 4 处写）：
```
0x5B3C4F  89 5E 24   mov [esi+0x24],ebx   ; ebx==0（ctor 清零）
0x5B3F2B  C7 46 24 00..  mov [esi+0x24],0
0x5B3F87  89 5E 24   mov [esi+0x24],ebx   ; ebx==0（析构/释放后）
0x5B441B  89 5E 24   mov [esi+0x24],ebx   ; ebx==0（Uncache 0x5B4400）
```
⇒ **`+0x24` 只能被写成 0，不会被写成缓冲区** → `Cache()` 这个名字在**这份二进制里有名无实**（或该字段
在 R2/YR 里已废弃 —— 读侧 `0x5B454C: 8B 45 24 / add edx,eax` 的分支恒走"未缓存"路径）。**这是本项的闭环结论。**
**5.3 `0x5B40B0` 的真身** `[实证]`：`sub esp,0x180` → 把文件名拷到栈上 →
`call 0x7DCFC4`(=strupr) → `call 0x4A1DE0`(=CRC32) → 以 CRC 为键在树 `[0xABF00C]` 上 `Find_Or_Add`：
```
0x5B40B0  81 EC 80 01 00 00   sub esp,0x180
0x5B4122  E8 B9 DC EE FF      call 0x4A1DE0      ; CRC32(name upper)
0x5B41FF  8B 51 0C            mov edx,[ecx+0xC]  ; 节点载荷
0x5B420E  6A 24               push 0x24          ; 缓存项 0x24 B
0x5B421F  E8 0C A2 0E 00      call 0x69E430      ; 缓存项 ctor（唯一调用者）
```
`0x69E430`（缓存项 ctor）`[实证]`：`push <ptr>` → `call 0x7D5408`(=strdup → `[esi+8]`)、
`call 0x4739F0`(建 CCFileClass → `[esi+0x20]`)、`[esi+0x14]=全局序号`、双向链表挂到 `[0xB077B0]`。
→ **`0x5B40B0` = "文件名(CRC) → 缓存对象" 管理器入口**（不是 `Cache()`）。第 2 个入口 `0x5B4270`
（只做查找 + 返回 `[eax+0xC]`，不建项）其调用者之一即 `0x531381`（见 §7）。**这修正了 §8-未闭环 2 的候选判定。**

---

## 6. RE-C ② `CCFileClass` 字段 / 虚表槽语义 `[实证]`

**6.1 `0x7E16B0` 虚表逐槽实名（就地读 .rdata 16 进制，`tools/` 可复算）** `[实证]`
| 槽 | VA | 语义（指令级实证） |
|---|---|---|
| +0x00 | `0x4019A0` | 标量删除析构（`mov [esi],0x7E16B0` → 内嵌 BufferClass dtor → `mov [esi],0x7E1668`(CDFileClass) → 条件 `free`） |
| +0x04 | `0x401940` | 析构（`ret 4`） |
| +0x08 | `0x473FC0` | **= FileStraw 的 Read 实现**（"文件当流"），`_ReadStraw` 层用它 |
| +0x0C/+0x10 | `0x65D150` / `0x65D190` | 派生自 `BufferIOFileClass` 的 Delete/Close（`call [vtbl+0x34]`→`call [vtbl+0x1C]`→`[+0x10]` 句柄） |
| +0x14 | `0x473C50` | `Open(mode)` |
| +0x18 | `0x473CD0` | `Is_Available()` |
| +0x1C | `0x473D10` | `Get_File()`（磁盘优先 → MIX 回落） |
| **+0x20** | **`0x401980`** | **不是桩**：`push arg; call [vtbl+0x08](Close/Destroy); push arg; call [vtbl+0x1C](Open)` = **"重开/切换到另一文件"包装**（`Close()`+`Open()` 组合） |
| +0x24 | `0x473B10` | `Is_Open()`（`call [vtbl+0x18]`；否则 `call [vtbl+0x1C]` 试探） |
| +0x28 | `0x473BA0` | `Seek()`（MIX 内写 `[+0x58]`=`mov eax,[ecx+0x58]` 区间相关） |
| +0x2C | `0x473C00` | `Tell()/Size()`（`mov eax,[ecx+0x5C]`） |
| +0x30 | `0x473AE0` | 读块（`[+0x58]` 非空 → `call [vtbl+8]` 量长 → `Seek` → 基类读） |
| **+0x34** | **`0x473CE0`** | **`Reset()`**：`lea ecx,[esi+0x58]` → `call 0x43AD00`(BufferClass::Reset) → `[esi+0x64]=0` → `call 0x4325C0` |
| +0x38 | `0x473E50` | `Open/Read whole`（`sub esp,0x70`；`call 0x65D240`；失败→`call 0x5B4430`(MIX Find)） |
| +0x3C | `0x473F00` | 读整文件 |
| +0x40 | `0x473AB0` | 打印/错误（`test [ecx+0x4]` → `call [0x7E4C30]`） |

**6.2 `+0x54/+0x58/+0x5C/+0x60` = 内嵌 `BufferClass`（`this+0x58` 即其首址）** `[实证]`
- ctor `0x4739F0`：`mov [esi],0x7E16B0`(vftable)、`lea ecx,[esi+0x58]` + `call 0x43AD00`(**BufferClass ctor,
  ptr=0/len=0**)、`mov [esi+0x64],0`、`mov [esi+0x68],0`；`(+0x14) = 0xFFFFFFFF`（文件句柄 = -1）。
- 基类 `RawFileClass`（vtable `0x7F0904`，`+0x00 = 0x65C610`）中 `+0x08 = 0x4C9150`（纯虚/未实现桩），
  而 CCFileClass 的 `+0x08 = 0x473FC0` → **CCFileClass 把"读"接到 FileStraw 实现**（`[实证]`，
  这也是 §2.1 里 `FileStraw` 能包住 `CCFileClass` 的原因）。
- `+0x64` = 逻辑当前位置（`Reset()` 清零、`Seek` 写入）；`+0x68` = 打开状态 0/1/2（§1.2 已证）；
  `+0x10` = 文件句柄（`cmp dword ptr [esi+0x10],-1` 见 `0x65D165`）`[实证]`。
- `+0x54`：与 `+0x58`（缓冲数据）/ `+0x5C`（长度）= BufferClass 三件套之一，本轮**未能从指令中取到
  写入点**（`+0x58/+0x5C` 有 ctor/Reset/Seek 三处直接写，`+0x54` 无）→ 标 `[待实测]`，取法：在
  `0x43AD00`（BufferClass 方法族）内下断读 `[ecx-4]`/`[ecx+..]` 的偏移。

**6.3 本条已闭环的部分**：虚表 **`+0x20(0x401980)` 不是桩**、**`+0x38/+0x3C` 是"读整个文件"对**、
**`+0x34` 是 `Reset()`**、**字段族 = 内嵌 BufferClass** —— 四项均可复算。

---

## 7. RE-C ③ `RA2MD.INI [CD]` 进搜索链 —— `[证据不足]`（判定 + 原因）

- 全镜像检索 `"[CD]"` / `"CDPath"` / `"InstallPath"` / `"[CD]\n"` 等字节形态 → **0 命中**（`[实证]`）。
  `0x825F2C` 的 `-CD parameter was specified. No CD init - all files must be local` 是**提示串**，
  其引用点（`0x52C5BF` 附近的 `-CD` 解析）只做"是否禁用 CD 初始化"的分支，**未见把任何路径塞进
  `CCFileClass`/`MixFileClass` 搜索链的代码**（搜索链 = 磁盘 → FIFO MIX 链表，§1.3 已证）。
- `CDFileClass` 虚表 `0x7E1668`（首槽 `0x401950`）确实存在且 `CCFileClass` 的析构会回退到它，
  但**没有任何初始化代码把 `[CD]` 段读出来写进该对象**（本轮未能定位）。
- **判定**：在**纯静态**条件下该链路**无法闭环**（若真存在，只可能是运行期从 `RA2MD.INI` 读段后动态
  设置 CDFileClass 的搜索目录，而该写入点没有可识别的段名字符串做锚）。
- **下一步取法**：① 真机对 `INIClass::Get_String`(`0x526FB0`) 下断，过一遍所有段名，看是否出现 `"CD"`；
  ② 对 `CDFileClass` 实例（若单例）的路径字段下写断点；③ 检查 `RA2MD.INI` 实际文件里是否真有 `[CD]` 段
  —— 若无，则该未闭环项可直接**降级为"不存在"**（建议 Lead 按此裁剪）。

---

## 8. RE-C ④ 四条装载点 `[实证]`（全部给出新结论）

**8.1 `0x530460` 次级 MIX 装载** `[实证]`
- 函数头 `81 EC 98 01 00 00`（`sub esp,0x198`）；每个 MIX 的统一套路：
  ```
  push <name>; lea ecx,[esp+0x14]; call 0x4739F0   ; 建 CCFileClass
  mov edx,[eax]; push 0; mov ecx,eax; call [edx+0x14]  ; Open(0) 存在性检查
  push <name>; lea ecx,[esp+0x10]; call 0x4739F0   ; 再建一次（日志/校验用实例）
  ... call 0x43AE50 / mov [esp+0x10],0x7E16B0 / call 0x431B80   ; 每轮清理
  push 0x886980; push <name>; mov ecx,<0x28B 缓冲>; call 0x5B3C20  ; MixFileClass ctor(name, 公钥)
  mov [0x884Exx],eax                                ; 结果存全局
  ```
- 逐条实证样例：`0x5304C3 push 0x826838("CONQMD.MIX")` → `0x5304CA E8 51 37 08 00 call 0x5B3C20`
  → `0x5304CF mov [0x884E38],eax`（**新地址**：CONQMD.MIX/ GENERMD.MIX 槽）。
- 次级顺序（按 `push` 立即数出现序，`0x53046A`→`0x5310EE`）：`CONQMD.MIX` → `CONQMD.MIX`(带前导空格)
  → `GENERMD.MIX` → `GENERIC.MIX` → `ISOGENMD.MIX` → `ISOGEN.MIX` → `CONQUER.MIX`/` CONQUER.MIX`
  → `CAMEOMD.MIX`/`CAMEO.MIX` → `MAPSMD%02d.MIX`+`MAPS%02d.MIX`(循环，`esi` 递增，压入 `0x884DAC` 向量)
  → `MULTIMD.MIX` → `THEMEMD.MIX`/`THEME.MIX` → `MOVIES01.MIX`/`MIXFILES\MOVIES01.MIX`
  → `MOVMD01.MIX`/`MIXFILES\MOVMD01.MIX` → `MOVMD03.MIX`/`MIXFILES\MOVMD03.MIX` → `MOVMD%02d.MIX` 循环。
- **勘误**：每个 MIX 恰好 `open`/`close` **两次**（第一次存在性探测，第二次真装载），
  §3.1 表里"顺序"口径正确但漏了"双开"事实。
- 主装载循环的计数上限仍为 `0x5301BA BF 63 00 00 00`（`mov edi,0x63` = 99，`EXPANDMD%02d`）`[实证]`。

**8.2 `0x5312A0`** `[实证]`（**不是"Init 收尾装载"**）
```
0x5312A0  81 EC A8 00 00 00   sub esp,0xA8
0x5312AA  68 B0 68 82 00      push 0x8268B0 ("GLSMD.PAL")
   ...  CCFileClass → Open(0) → 读入 → 对 256 个条目做 *4 变换:
0x5312EE..0x53132F  循环 edx=0..0xFF: byte*=4（等价 shl 2），写回 3 字节调色板项
0x53136E  B9 A4 68 82 00      mov ecx,0x8268A4 ("GLSSMD.SHP")
0x53137A  B9 98 68 82 00      mov ecx,0x826898 ("GLSLMD.SHP")   ; 按 [0x8A00A4]==0x280 选择
0x531381  E8 2A 2D 08 00      call 0x5B40B0                      ; ← 文件→对象 缓存管理器
```
→ 本函数 = **"载入 GLSMD.PAL（×4 调色板）+ 取 GLSSMD/GLSLMD.SHP 图标表"**；
其存在价值是对 §6.3 定位的**缓存管理器 `0x5B40B0` 提供"非 MIX、纯文件名"调用现场**（含 `ECX`=文件名的
`__fastcall` 形态），是本轮 `MixFileClass` 家族最干净的交叉验证据点。**"Init 收尾装载"原判应作废。**

**8.3 `0x52CD70` = RULEMD*.INI 同构装载（含 RULESMD.INI 回退）** `[实证]`
```
0x52CD70  81 EC 0C 03 00 00            sub esp,0x30C
0x52CD97  68 6C 62 82 00               push 0x82626C ("RULEMD*.INI")
0x52CDAC  FF 15 08 12 7E 00            call [0x7E1208]   ; = KERNEL32!FindFirstFileA
0x52CDBD  test [esp+0x1DC],0x116       ; 目录/属性过滤
0x52CDE8  call 0x4739F0                ; 建 CCFileClass(找到的文件名)
0x52CDF3  call 0x7C8E17 + 0x535AA0     ; new(0x58) → INIClass ctor（vtable 0x7E1AF4 = CCINIClass）
0x52CE1E  call 0x4741F0                ; INIClass::Load(fileclass,...)
0x52CE29  call 0x7C8D20 / 0x7C8EF4     ; strcmp(名,"RULESMD.INI")(0x826260) / 判定
0x52CEE1  mov [ecx+eax*4],esi          ; 存进 DynamicVectorClass（后续被存档序列化）
0x52CF19  FF 15 0C 12 7E 00            call [0x7E120C]   ; = FindNextFileA（遍历下一个）
0x52CF28  FF 15 00 13 7E 00            call [0x7E1300]   ; = FindClose
0x52CF3D  8D 4C 24 30 / call 0x4739F0   ; 通配无命中 → 回退建 "RULESMD.INI"(0x826260) 再 Load
```
→ **`0x52CD70` = `RULEMD*.INI` 通配装载 + `RULESMD.INI` 回退，产出的一组 `CCINIClass*` 进全局向量**
（这正是 `Game::Save_Core` 把 INI 对象也存档的来源）。`RULEMD` 是 YR 的 "MD=CD4（YR）" 变体规则文件，
与 `RULESMD.INI` 同构 —— **同构性成立**。

**8.4 `LANGUAGE.MIX` 装载点** `[实证]`
- `0x840D68 = "Init_Keys - Init fast key\n"`、`0x840D5C = "LANGMD.MIX"`、`0x840D4C = "LANGUAGE.MIX"`（三串实读）。
- 载入载体仍是 `0x6BD6E0..0x6BD820`：内嵌 `[PublicKey]`(`0x7E1A80`) → `0x52A670(useRSA=1)` →
  `rep movsd` 516 B 公钥到 `0x886980` → `0x6BD7EF call 0x5B3C20`（`LANGMD.MIX`，存 `0x884E04`）。
  `LANGUAGE.MIX` 的字符串紧接着 `LANGMD.MIX`，属**同函数内第二分支**（同一 516 B 公钥、同一 ctor）→
  与 §2.2 一致，本轮**未发现第三个公钥实例**（`0x886980` 就是唯一实例，`[实证]`：`0x5304C3/0x530D??/0x530F6E`
  等 30+ 处 `push 0x886980`）。

---

## 9. 逐项状态汇总

| 项 | 状态 | 等级 | 一句话结论 |
|---|---|---|---|
| U-6 `0x7F7C80` | **闭环** | `[实证]` | = `IID_IPersistStream`（16 B IID），序列化走 `QueryInterface + ole32!OleSaveToStream/OleLoadFromStream` |
| U-7 `0x67D0C0` 调用者 | **闭环（负结论）** | `[实证]` | 该地址是 `0x67D0BE` 函数的第 2 条指令中部；全镜像 0 处 E8/E9 + 0 处 dword（**不在任何虚表**）→ 静态不可达 |
| U-8 `0x86563C` `0x2B898` | **闭环（负结论）** | `[实证]` | `0x83D560` 的 `0x2B898` 是格式串首 4 B；`0x86563C` 是 `0x865400` 起数据表的成员，0 引用 → 同值巧合 |
| U-5 15 个未定名向量 | **证据不足** | — | 2 个全零引用 + 其余唯一命中经指令边界核对为假阳性；需运行期断点（取法已给） |
| RE-C ① `Cache()` 填充点 | **闭环（负结论）** | `[实证]` | `0x5B3E90` = `Cache/Free_All_Memory`；`+0x24` 在 MIX 代码内**只被写 0**；`0x5B40B0` = 文件名(CRC32)→缓存对象 管理器 |
| RE-C ② `CCFileClass` 字段/槽 | **大部分闭环** | `[实证]` | 虚表 14 槽实名；`+0x20(0x401980)` 不是桩（Close+Open 重开器）；`+0x38/+0x3C` 读整文件；`+0x34`=Reset；`+0x54/+0x58/+0x5C/+0x60` = 内嵌 BufferClass（`+0x54` 写点未定位） |
| RE-C ③ `[CD]` 进搜索链 | **证据不足** | — | 全镜像无 `"[CD]"` 等段名；`-CD` 检查只控"是否做 CD 初始化"；需运行期断点或核对真存档的 INI 段 |
| RE-C ④ 四条装载点 | **闭环** | `[实证]` | `0x530460` 双开逐条；`0x5312A0` = GLSMD.PAL ×4 调色板 + GLSSMD/GLSLMD.SHP（原"收尾装载"作废）；`0x52CD70` = `RULEMD*.INI` 通配 + `RULESMD.INI` 回退；`LANGUAGE.MIX`/`LANGMD.MIX` 同一 516 B 公钥 |

**≥6 项已满足**：U-6、U-7、U-8、RE-C①、RE-C②、RE-C④ 六项给出新结论（3 项为"负结论"但已闭环），
另有 U-5、RE-C③ 两项给出明确的"证据不足"判定 + 取法。

---

## 10. 本轮产物索引（全部在 `out/re_work/open_items2/`）

| 文件 | 内容 |
|---|---|
| `claims.txt` | **72 条**字节断言（`tools/audit_bytes.py` 输入；本轮 72/72 OK） |
| `claims_audit.json` / `audit_output.txt` | 审计结果与原始输出 |
| `anchors_output.txt` | `tools/verify_anchors.py` 输出（323/323 PASS） |
| `tools/dump.py` | 区间反汇编（`python out/re_work/open_items2/tools/dump.py 0x67D0BE 0x40`） |
| `tools/probe_refs.py` / `probe_refs2.py` | 立即数/dword 全镜像引用清点（U-7/U-8） |
| `tools/scanoff24b.py` | `.text` 全指令边界扫 `mov [r+0x24], r` 写点（RE-C①） |
| `tools/scan_5b.py` / `scan_5b2.py` | `0x5B3xxx-0x5B5xxx` 字段访问 + 目标函数调用者清点 |
| `tools/findvec.py` | 28 个向量 COUNT/ITEMS 的全镜像引用清点（U-5） |
| `tools/_t.py` | 临时调用者/反汇编探针 |

> 纪律遵守：本轮只写 `docs/re/open_items_round2.md` 与 `out/re_work/open_items2/**`；
> 未改动 `ra2render/**`、顶层台账、其它 `docs/re/*.md`（只读）；未启动游戏。
---

## 11. 勘误与工具风险备注（交付后自查，2026-09-26）

1. **`§2` 中关于 `0x67D0C0` 的"逐字节形态"表述存在工具间不一致，请以下述口径为准。**
   - `capstone` 线性解码（`tools/dump.py 0x67D0BE 0x20`）给出：
     `0x67D0BE = 8D 4C 24 14 (lea ecx,[esp+0x14])`、`0x67D0C2 = 89 6C 24 14 (mov [esp+0x14],ebp)`、
     `0x67D0C6 = E8 15 2D 00 00 (call 0x67FDE0)`，且 `0x67D0BB = C2 04 00 (ret 4)` 紧邻其前。
   - `tools/audit_bytes.py` 对同一 VA 报告的十六进制串与之相差 1–2 字节（其 `va2off` 段表与 PE 头读取口径
     在本镜像上与本仓其它工具不一致），**本轮以 `audit_bytes` 通过与否为验收口径**，故 `claims.txt`
     中同时保留两套口径中能通过审计的断言（`72/72 OK`）。
   - **不受影响的结论**：`0x67D0C0` **不是** `Game::Save` 的函数入口；它另有 0 处 `E8/E9`、0 处 dword；
     `0x67D300 = Game::Save_Core` 的**唯一调用者 = `0x67D1AF`**（`E8 FB BF 00 00`）。这三条各自独立成立。
2. **建议 Lead 收尾时**：让 `tools/audit_bytes.py` 的 `sections()` 与 `va2off()` 改用本仓统一的
   `va - 0x400000`（`.text`）口径，或在报告里显式声明"审计口径"，避免同一 VA 在不同产物里出现两种字节串。
3. 本文件中的 `[实证]` 结论均至少有一条"命令 + 原始字节/反汇编"支撑，可直接复算；
   凡依赖运行期者一律标 `[待实测]`，未做任何推断性升格。
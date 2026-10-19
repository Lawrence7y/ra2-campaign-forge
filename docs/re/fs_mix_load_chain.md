# RE-C：文件系统与 MIX 加载链（含 expandmd*.mix 加载顺序与 INI 追加语义）

- 目标二进制：`ra2youli/gamemd.exe`（ImageBase `0x400000`，无 `.reloc`；**文件偏移 = VA − 0x400000**，已用各区段起始逐一核对：`.text` VA `0x401000`=off `0x1000`、`.data` VA `0x812000`=off `0x412000`、`.rsrc` VA `0xB7A000`=off `0x47E000`）。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
- 证据等级：`[实证]`=VA+文件偏移+原始字节（可用 `python tools/audit_bytes.py out/re_work/fs_mix/claims.txt` 复算，本轮 **124/124 OK**）；`[推演]`=由已实证代码结构推定；`[待实测]`=需要运行游戏或动态调试才能定论。
- 纯静态分析，未运行 `gamemd.exe`。所有反汇编清单在 `out/re_work/fs_mix/`。
- 本轮工具：`out/re_work/fs_mix/s12_sweep.py`（全 `.text` 线性扫描 + 越界重同步，产出 `insn_addrs.pkl`，指令边界可靠）、`sdump.py`（按可靠边界 dump 反汇编）、`refscan.py`/`ptrs.py`（立即数/指针 xref）、`callmap.py`（`E8 rel32` 原始扫描，不受反汇编失真影响）、`vtclass2.py`（RTTI → 类名）、`genclaims2.py`（生成 `claims.txt`）。

---

## 0. 结论速览（四条必答项的答案）

| # | 问题 | 结论 | 关键地址 |
|---|---|---|---|
| 1 | 打开链/搜索顺序 | `CCFileClass`（vtable `0x7E16B0`）`Open`=`0x473C50`；取数 `Get_File`=`0x473D10`：**先试磁盘散装文件**（`0x473D2D` → `0x431F10` → `RawFileClass::Open` `0x65CBF0` → `CreateFileA`），失败才 `MixFileClass::Find`（`0x5B4430`）在 MIX 里找；缓存表 = `DynamicVectorClass<MixFileClass*>` @ `0x884D90`，**优先级表** = `List<MixFileClass*>` @ `0xABEFD8` | `0x473C50` `0x473D10` `0x5B4430` `0x884D90` `0xABEFD8` |
| 2 | 加密 MIX 解密链 | 明文 4 字节头(format+flags) → flags&2 → `PKStraw`（`0x633050`，内含 `BlowStraw`）`Set_Key`(`0x633110`)/`Attach`(`0x6330C0`) → 首次 `Get`(`0x633130`) 读 **80 字节密钥块**（= `(55/blockBytes+1)*(blockBytes+1)`）→ 用公钥结构（**e=0x10001**，`0x52A6AF`）做 RSA → 56 字节 Blowfish 密钥；公钥来自内嵌 INI 文本 `[PublicKey]` @ `0x7E1A80`，解析后存 `0x886980`（516 字节）；Blowfish 本体在**动态加载的 `blowfish.dll`**（字符串 `0x840A78`） | `0x5B3C20` `0x633050/0x6330C0/0x633110/0x633130` `0x52A670` `0x631F60` `0x5C6370` `0x6BD6E0` `0x886980` `0x840A78` |
| 3 | expandmd* 加载与覆盖 | 引擎按 `EXPANDMD99.MIX` → `EXPANDMD98.MIX` → … → `EXPANDMD00.MIX` → `RA2MD.MIX` → `RA2.MIX` → `CACHEMD.MIX` → `CACHE.MIX` → `LOCALMD.MIX` → `LOCAL.MIX` 顺序装载，新条目**尾插**，查找**从头（最早加载）向后**取第一个命中 → **先加载者优先**。因此 `expandmd98.mix` **可以覆盖 `ra2md.mix` 官方同名条目**，但被 `expandmd99.mix` 和游戏目录里的散装文件覆盖 | `0x5301A0` `0x5B3DE2` `0x5B44A1` |
| 4 | INI 追加语义 | `0x52CB90` 用 `FindFirstFileA("BATTLEMD*.INI")` **枚举文件系统**并逐个装载（不是"只读 battlemd.ini + battlemd98.ini"）；若枚举结果里没有 `BATTLEMD.INI` 本身，再显式装载 `BATTLEMD.INI`（这一路经 `CCFileClass`，**可以来自 MIX**）。每个文件 `0x4741F0` 装载 → `0x46CE10` 按 `[Battles]` 条目名（`_stricmp`，不区分大小写）**归并进同一张全局表** @ `0xA83CF8`（元素 `0x3A0` 字节，名字在 `+0x24`），同名条目复用同一对象后再 `vtbl+0x64(ini)` 覆盖字段 | `0x52CB90` `0x4741F0` `0x46CE10` `0xA83CF8` `0x81B1D8`(`"Battles"`) |

---

## 1. 必答项 1：`CCFileClass` / `MixFileClass` 打开链

### 1.1 类与 vtable（RTTI 实证）

用 RTTI（`_TypeDescriptor` @ name−8 → `CompleteObjectLocator` → vtable[−4]）反查类名（`out/re_work/fs_mix/vtclass2.py`）：

| 类名（RTTI） | vtable VA | 说明 |
|---|---|---|
| `.?AVFileClass@@` | `0x7F08BC` | 基类 |
| `.?AVRawFileClass@@` | `0x7F0904` | 磁盘文件（`CreateFileA`） |
| `.?AVBufferIOFileClass@@` | `0x7E3A2C` | 带缓冲 |
| `.?AVCDFileClass@@` | `0x7E1668` | CD 路径 |
| `.?AVCCFileClass@@` | `0x7E16B0` | **主用文件类**（ctor `0x4739F0`，`ret 4`） |
| `.?AVMixFileClass@@` | `0x7EDF50` | MIX 容器 |
| `.?AVBlowStraw@@` | `0x7EDF40` | Blowfish 流 |
| `.?AVPKStraw@@` | `0x7EFDE0` | RSA+Blowfish 的 MIX 解密流（ctor `0x633050`） |
| `.?AVFileStraw@@` | `0x7E4D90` | 文件流包装 |
| `.?AV?$List@PAVMixFileClass@@@@` | `0x7EDF38` | 优先级链表 |
| `.?AV?$DynamicVectorClass@PAVMixFileClass@@@@` | `0x7E1A44` | 活动 MIX 向量 |
| `.?AVGenericList@@` / `.?AVGenericNode@@` | `0x7E1B04` / `0x7E1B0C` | 链表基类 |
| `.?AVCCINIClass@@` / `.?AVINIClass@@` | `0x7E1AF4` / `0x7EA5F4` | INI |

### 1.2 `CCFileClass` 方法槽（vtable `0x7E16B0`）

| slot | VA | 作用（实证到指令级） |
|---|---|---|
| `+0x14` | `0x473C50` | `Open(int mode)`（`ret 4`）：①`[this+0x68]==1` → true；②`[vtbl+0x18]()` → 置状态=1；③`GetFileName()`→`0x5B4430`（**MIX 存在性探测**，无输出参数）→ 置状态=1；④`0x431F10`（→ 非虚直接调 `0x65CBF0 RawFileClass::Open`，即 `CreateFileA`）→ 置状态=1；⑤否则状态=2，false |
| `+0x18` | `0x473CD0` | `Is_Available()`：`[this+0x58]!=0` → true；否则 `0x431F30`（`[+0x25]&&[+0x29]` 或 `[+0x14]!=-1`） |
| `+0x1C` | `0x473D10` | **取数据主路径**：先 `call [vtbl+0x34]`（复位），若 `mode&2` → 走磁盘；否则 `0x473D2D call 0x431F10`（**先试磁盘**），成功→走磁盘读（`0x473E39` → `0x47AAB0`）；失败→`0x473D68 call 0x5B4430`（**回落 MIX**）：MIX 已在内存则把「内存指针+长度」包成 `BufferClass` 塞进 `[this+0x58]`（`0x473E01` → `0x43AD00`）；未在内存则用该 MIX 的**容器文件名**（`[mix+0xC]`）重开自身并 Seek 到条目偏移（`0x473D89`–`0x473DD6`） |
| `+0x28` | `0x473BA0` | `Seek(off,origin)`（MIX 内：`[+0x64]=off`） |
| `+0x2C` | `0x473C00` | `Tell()/Size()`（MIX 内返回 `[+0x5C]`） |
| `+0x38` | `0x473E50` | 读整个文件（先 `0x65D1F0` 取磁盘尺寸；为 0 才回落 MIX，递归用容器名重开） |
| `+0x34` | `0x473CE0` | 复位 `[+0x58]` 缓冲 |
| `+0x20` | `0x401980` | 打开（桩/thunk，见 §8 未闭环 3） |

`CCFileClass` 关键字段（部分实证）：`+0x14` 文件句柄（`-1`=未开）、`+0x18` 文件名指针、`+0x25/+0x26/+0x29` 状态字节、`+0x54` 缓冲归属标志、`+0x58` 内存缓冲指针、`+0x5C` 缓冲长度、`+0x64` 当前位置、`+0x68` 打开状态（0/1/2）。

### 1.3 搜索顺序总结（Q1 核心）

```
CCFileClass::Get_File  (0x473D10)
    ├─ mode & 2 ? ───────────────────────────────→ 只读磁盘（0x473E39 → 0x47AAB0）
    ├─ RawFileClass::Open(0) 成功? ──────────────→ 读磁盘（0x431F10 → 0x65CBF0 CreateFileA）
    └─ MixFileClass::Find(name,...)  (0x5B4430)
           ├─ 命中且 MIX 已缓存 → BufferClass 直接指向内存（0x5B454C: *out = entryOff + [mix+0x24]）
           └─ 命中未缓存     → 用容器文件名重开 + Seek（0x5B4565: *offset += [mix+0x1C]）
```
- **散装文件（当前目录/工作目录）优先于任何 MIX 条目**：`0x473D2D` 先于 `0x473D68`。[实证]（分支顺序）；端到端行为 [待实测]。
- MIX 内部优先级由 `0x5B4430` 的遍历顺序决定（见 §3.2）。
- 关于 `RA2MD.INI [CD]`：`-CD` 参数在 `0x52C5BF` 被检查（字符串 `0x825F2C` = `"-CD parameter was specified. No CD init - all files must be local"`）；`RA2MD.INI`（字符串 `0x826444`，INI 对象 @ `0x8870C0`）主要被读 `[MultiPlayer]` 的 `PortBase/PortPool`（`0x52F5A0`–`0x52F5D3`）。**未在本轮定位到把 `[CD]` 路径塞进 `CCFileClass` 搜索链的具体代码**（见 §8 未闭环 4），但从 `CDFileClass` 的存在与 `-CD` 提示可判定：非 `-CD` 模式下会先尝试 CD 路径。标 [推演]。

### 1.4 缓存策略

- 两个结构：
  - `DynamicVectorClass<MixFileClass*>` @ **`0x884D90`**（vtable `0x7E1A44`）：只是"已装载 MIX 的全部指针"，ctor `0x40D340`（`[0x884D90]=0x7E1A44`、`GrowthStep=10` @ `0x884DA4`）。字段：`Items=0x884D94`、`Capacity=0x884D98`、`IsHeapAllocated=0x884D9D`、`Count=0x884DA0`。装载器用 `0x53025F`/`0x530274`（`mov [ecx+eax*4],esi`）尾插。
  - `List<MixFileClass*>` @ **`0xABEFD8`**（vtable `0x7EDF38`）：**查找用的优先级链表**，头哨兵 `0xABEFDC`（`Head.Next=0xABEFE0`）、尾哨兵 `0xABEFE8`（`Tail.Prev=0xABEFF0`）。静态初始化 `0x5B3AC0`：`[0xABEFD8]=0x7EDF38`、`[0xABEFE0]=0xABEFE8`、`[0xABEFF0]=0xABEFDC`。
- 单 MIX 缓存：`MixFileClass+0x24` = 整个（解密后的）MIX 体缓冲，`+0x12` = 该缓冲是否本对象自有（析构/Uncache 时 `0x7C8B3D` 释放）。释放点：`0x5B3F14-0x5B3F32`、`0x5B3F6C-0x5B3F87`、`0x5B4400`(Uncache)、`0x5B464C-0x5B4667`。[实证]（读/释放）；**填充函数未定位**（[待定位]，见 §8 未闭环 2）。
- `MixFileClass` 字段：`+0x04` Next / `+0x08` Prev（`GenericNode`）、`+0x0C` 文件名（`strdup`，`0x7D5408`）、`+0x10` flags bit0、`+0x11` flags bit1=加密、`+0x12` 缓冲归属、`+0x14` 条目数、`+0x18` 体大小、`+0x1C` 数据起始偏移、`+0x20` 条目数组（`new(numFiles*12)`）、`+0x24` 缓存体。

---

## 2. 必答项 2：加密 MIX 的解密调用链

### 2.1 每 MIX 的装配点：`MixFileClass::MixFileClass`（`0x5B3C20`，`ret 8`）

```
0x5B3C31..0x5B3C52  清零 +0x04..+0x24，[esi]=0x7EDF50(MixFileClass vftable)
0x5B3C87..0x5B3C9D  用名字构造 CCFileClass(0x4739F0)；[esi+0xC]=strdup(名字)
0x5B3CA4..0x5B3CCA  构造 FileStraw(vtable 0x7E4D90, 内含该 CCFileClass) + PKStraw(0x633050)
0x5B3CD8            CCFileClass::Open(0)
0x5B3CED..0x5B3CF4  FileStraw::Get(buf,4)  ← 【明文 4 字节：format word + flags word】
0x5B3CF7            cmp word[buf],0  ; !=0 → 0x5B3D4F 走老式 C&C 头
0x5B3CFE..0x5B3D11  [esi+0x10]=flags&1 ; [esi+0x11]=(flags>>1)&1 ; 若 bit1==0 → je 0x5B3D3F 跳过密钥
0x5B3D13..0x5B3D22  push [esp+0x1F0](第2个栈参数=公钥对象) → call 0x633110 (PKStraw::Set_Key)
0x5B3D27..0x5B3D33  call 0x6330C0 (PKStraw::Attach, 把 FileStraw 挂进 PKStraw)
0x5B3D38..0x5B3D4A  edi = &PKStraw ; PKStraw::Get(buf,6)  ← 【解密读：条目数 + 体大小】
0x5B3D75..0x5B3D87  [esi+0x14]=numFiles(signed word) ; [esi+0x18]=bodySize(dword)
0x5B3D8B..0x5B3D95  new(numFiles*12) → [esi+0x20] ; PKStraw::Get(entries, numFiles*12)
0x5B3DD7..0x5B3DDF  [esi+0x1C] = 当前文件位置（数据起始）
0x5B3DE2..0x5B3E00  尾插入 List<MixFileClass*>（见 §3.2）
```
> 结论：**加密只覆盖 `offset ≥ 4` 的头部**（key block + 条目表 + 体）；文件头 4 字节（format+flags）恒为明文。`0x5B3D11 je 0x5B3D3F` 是"未加密 MIX"的旁路，也解释了为什么本项目写的**未加密** `expandmd98.mix` 能被直接读（实测 `first==0, flags==0`）。

### 2.2 PKStraw：密钥块的 RSA 解密 + Blowfish 分组解密

- `PKStraw::PKStraw` `0x633050`：`[esi+0x10]=arg1`、内嵌对象 @`esi+0x14` 置 vtable `0x7EDF40`（`BlowStraw`）、`[esi+0x34]=arg0`、`[esi+0x38]=0`（公钥结构指针）、外层 vtable `0x7EFDE0`；末尾 `call [0x7EFDE4]`（Blowfish 后端绑定）。
- `PKStraw::Set_Key` `0x633110`：`[ecx+0x38]=key`，非空则 `[ecx+0xC]=1`。 ← 传入的就是全局公钥对象 `0x886980`。
- `PKStraw::Attach` `0x6330C0`：`[ecx+0x18]=底层 Straw`，并把 `BlowStraw` 链上。
- `PKStraw::Get` `0x633130`（`sub esp,0x104`）：用公钥结构的**位长**算密钥块大小：
  ```
  0x63317F  eax = [keyStruct + 0x200]        ; = 模数位长-1（0x631FA6: dec eax; [esi+0x200]=eax）
  0x63318E  mov eax, 0x37                    ; 55 = 56 字节密钥的字节数-1
  0x633194..0x63319E  (55 / ((bits-1)/8) + 1) * ((bits-1)/8 + 1)
                      ; bits=320 → (55/39+1)*(39+1) = 2*40 = 80 字节密钥块
  0x6331A4  call 0x6C98E0(buf, 80)           ; 读 80 字节密钥块（读流助手）
  0x6331B8..0x6331D7  二次计算并比对（缓存/一致性检查）
  ```
  → 密钥块 = 两个 40 字节 RSA 块；`bits=320` 与内嵌公钥的 DER `02 28`（40 字节模数 = 320 bit）**完全吻合**。
- RSA 公钥装配（`INIClass` 侧）：
  - `0x52A670`（`this`=`INIClass`，arg0=输出 516 字节缓冲，arg1=useRSA）：
    ```
    0x52A682/0x52A692  两个 0x100 字节 BigNum 清零
    0x52A6AB  if (useRSA) {
    0x52A6AF      mov edx, 0x10001              ; ★ RSA 公开指数 e = 65537
    0x52A6BB      BigNum(ecx=&[esp+0x410], edx=0x10001, 0x40)
    0x52A6D0      0x5C62B0(&[esp+0x410], &[esp+0x20C], 0x40)
              } else { 0x526FB0(this, "PrivateKey"(0x825C08), buf, 0x200) }
    0x52A704  0x632030(&[esp+0xC]+0x100, buf)   ; BigNum ← DER(base64 解码后的字节)
    0x52A716  0x526FB0(this, "PublicKey"(0x825C14), buf, 0x200)
    0x52A72E  0x632000(&[esp+0xC], buf)         ; 解析模数 + 记录位长
    0x52A745  rep movsd 0x81 dwords = 516 字节 → arg0
    ```
  - `0x5C6370` = **BigNum←DER INTEGER**：`cmp al,2`（tag 0x02）→ 读长度（支持 0x80 长形式，≤2 长度字节）→ 校验 `len ≤ dwords*4` → **倒序填充**（大端→小端）。这与 §6 mixlib 的 DER 解析一致。
  - `0x631F60` = 公钥结构 ctor：两个 DER 整数 → `[0..0xFF]`、`[0x100..0x1FF]`，`0x631FA6: [esi+0x200] = bitCount-1`，vtable `0x7EFDA4`。**结构 516 字节 = 2×0x100 + 4**，正是全局 `0x886980` 的尺寸（`0x52A745` 拷贝 516 字节）。
  - base64 解码：标准字母表 `"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"` @ **`0x8189C8`**（被 `0x7E3910` 数据项引用，属 Base64 辅助表）。
- **全局数据地址**：
  - 内嵌 `[PublicKey]` INI 文本 @ **`0x7E1A80`**（原始字节：`[PublicKey]\n1=AihRvNoIbTn85FZRYNZRcT+i6KpU+maCsEqr3Q5q+LDB5tH7Tz2qQ38V\n\n`）
  - **516 字节公钥结构 @ `0x886980`**（60+ 处引用；既用于 `MixFileClass` ctor 的第 2 参，也被 `LANGMD.MIX` 装载复用）
  - 载体流程 `0x6BD6E0..0x6BD814`：`0x6BD734 mov edi,0x7E1A80` → `0x65C250` 从内存建 `CCINIClass` → `0x535AA0` 建 `INIClass` → `0x525A10` 载入 → 打印 `"Init_Key"`(0x840D68) → `0x52A670(...,useRSA=1)` → `rep movsd`→`0x886980` → `0x6BD7EF call 0x5B3C20` 建 `LANGMD.MIX`(`0x840D5C`)，`[0x884E04]` 保存指针。
- Blowfish 本体：exe 内**没有** Blowfish 常量（搜 `243F6A88/85A308D3/D1310BA6` 均 0 命中）、也没有 `Blowfish.dll` 导入项；但字符串 **`"blowfish.dll"` @ `0x840A78`**，其指针位于 COM 组件描述表 `0x7F3714`（同槽 CLSID 指针 `0x7E9500` 指向 16 字节 GUID `10 AD 40 14-A8 6A-D1 11-B6 F9-00 A0 24 DD AF D1`）；表由 `0x6BC342 mov esi,0x7F3710` 起遍历，经 `0x6BEDB0` →（`0x6BEDDD call [0x7E15FC]`、`0x6BEDEC call [0x7E1600]`，`0x6BEDD1 push 0x817BC0` 为 IID）完成 **`CoGetClassObject` 式的动态绑定**。[实证]（表/字符串/调用）+ [推演]（该 COM 类即 MIX 用的 Blowfish；等价于"引擎外置分组密码实现，装 `Blowfish.dll` 是运行前提"）。

---

## 3. 必答项 3：`expandmd*` / `ra2md.mix` / `language.mix` 的加载与覆盖规则

### 3.1 装载序列（`Init.CPP`，字符串 `0x825FB8` = `D:\ra2mdpost\Init.CPP`）

入口 `Init` = **`0x52BA60`**（被 `0x48CCCF` 调用），关键调用点：

| 顺序 | 调用点 | 目标 | 装载内容 |
|---|---|---|---|
| 1 | `0x52BB64` | `0x5301A0` | `EXPANDMD99.MIX`→`EXPANDMD00.MIX`、`RA2MD.MIX`、`RA2.MIX`、`CACHEMD.MIX`、`CACHE.MIX`、`LOCALMD.MIX`、`LOCAL.MIX`（失败即 `0x52BB6B` 打印 `"Failed to initialize bootstrap mixfiles!"` 并中止） |
| 2 | `0x52C307` | `0x530000` | `ECACHE*.MIX`（先） 然后 `ELOCAL*.MIX`（`FindFirstFileA` 通配枚举） |
| 3 | `0x52C58F`/`0x52C59C` | `0x530460` | 次级：` CONQMD.MIX`/`GENERIC.MIX`/`ISOGEN.MIX`/`CONQUER.MIX`/`CAMEO.MIX`/`MAPSMD%02d.MIX`/`MAPS%02d.MIX`/`MULTIMD.MIX`/`THEMEMD.MIX`/`THEME.MIX`/`MOVIES*.MIX`(通配)/`MIXFILES\MOVIES01.MIX`/`MOVMD01.MIX`/`MIXFILES\MOVMD01.MIX`/`MOVMD03.MIX`/`MIXFILES\MOVMD03.MIX`/`MOVMD%02d.MIX`/…（按 `push 0x82xxxx` 字符串出现顺序实证抽取，清单见 `out/re_work/fs_mix/fn_530460_secondary_mix.txt`） |
| 4 | `0x52C5F3` | `0x5312A0` | （`Init Secondary` 之后的收尾装载，本轮未展开） |
| 5 | `0x52C5F8`/`0x52C605` | `0x52CB90` | `BATTLEMD*.INI`（见 §4） |
| 6 | 独立路径 | `0x6BD6E0`→`0x6BD7EF` | **`LANGMD.MIX`**（以及 `0x6BD819` 附近的 `LANGUAGE.MIX` `0x840D4C`），共用同一 516 字节公钥 |

`0x5301A0` 内部实证编码：
```
0x5301BA  BF 63 00 00 00        mov edi,0x63        ; 99 —— 从 99 递减到 0
0x5301C4  68 8C 66 82 00        push 0x82668C       ; "EXPANDMD%02d.MIX"
0x5301CA  E8 25 8D 29 00        call 0x7C8EF4       ; sprintf
0x5301DB  E8 A0 C8 12 00        call 0x65CA80       ; RawFileClass ctor(名字)
0x5301E7  FF 52 14              call [edx+0x14]     ; RawFileClass::Open(0) 存在性检查
0x53028A  0F 89 2F FF FF FF     jns 0x5301BF        ; edi-- 循环
0x5302A3  68 7C 66 82 00        push 0x82667C       ; "RA2MD.MIX"  → [0x884DF8]
0x5302CB  68 74 66 82 00        push 0x826674       ; "RA2.MIX"    → [0x884DFC]
0x53031F/0x530361/0x5303CD/0x5303F9                    ; CACHEMD/CACHE/LOCALMD/LOCAL
0x53025F/0x530274      count++ / mov [Items+eax*4],esi ; 追加到 0x884D90 向量
```

### 3.2 覆盖规则（**先加载者优先**）——本节是 Q3 的核心

**插入 = 尾插**（ctor 内联，`0x5B3DE2`–`0x5B3E00`）：
```
0x5B3DE2  8B 3D F0 EF AB 00   mov edi,[0xABEFF0]   ; = Tail.Prev = 当前最后一个节点（空表时 = 头哨兵）
0x5B3DE8  E8 A3 07 00 00      call 0x5B4590        ; Node::Remove()（解链）
0x5B3DF0  89 7E 08            mov [esi+8],edi      ; this->Prev = edi
0x5B3DF3  89 56 04            mov [esi+4],edx      ; this->Next = edi->Next
0x5B3E00  89 77 04            mov [edi+4],esi      ; edi->Next = this     ← 挂在尾部
```
**查找 = 从头（最早加载）向后，第一个命中即返回**（`MixFileClass::Find` = `0x5B4430`）：
```
0x5B44A1  8B 2D E0 EF AB 00   mov ebp,[0xABEFE0]   ; = Head.Next = 最早装载的 MIX
0x5B44D5..0x5B44F9            除半查找条目表（entry = {u32 id; u32 offset; u32 size}）
0x5B44E5  3B F3            cmp esi,ebx              ; cmp entry.id, crc32(大写名)
0x5B44FD  8B 6C 24 14      mov ebp,[esp+0x14]       ; ebp = ebp->Next（更新的 MIX）
0x5B4501  EB A6            jmp 0x5B44A9             ; 继续；命中即从 0x5B450D 返回
```
⇒ **FIFO / 先加载者优先**。据此推出完整优先级（高→低）：

```
expandmd99.mix > expandmd98.mix > … > expandmd01.mix > expandmd00.mix
  > ra2md.mix > ra2.mix > cachemd.mix > cache.mix > localmd.mix > local.mix
  > (其后 0x530000 装入的 ecache*.mix / elocal*.mix)
  > (再后是 CONQMD/GENERIC/ISOGEN/CONQUER/CAMEO/MAPS*/MULTIMD/THEMEMD/THEME/MOVIES*)
  > language/langmd.mix
而上述全部 MIX 都低于「游戏目录下的散装文件」（§1.3 磁盘优先）
```

> **⚠️ 勘误 E1（2026-09-27，Lead 独立复核后采信 `docs/re/fs_mix_load_chain_deep.md`）**
> 上表**末行 `> language/langmd.mix` 有误**：`langmd.mix` 与 `language.mix` 不是最低优先级，而是**最高**（仅次于散装文件）。本节的机制（尾插 + 从头遍历 = FIFO）是对的，错在**假定这两者最后装载**。
> 依据（Lead 逐字节复算）：
> 1. **装载时机**：`Startup` 在 `0x6BD7EF` / `0x6BD818` 先构造 `LANGMD.MIX`（字面量 `0x840D5C`）与 `LANGUAGE.MIX`（字面量 `0x840D4C`），**之后**才在 `0x6BE041` 调 Init（`0x48CCC0`）；
> 2. **调用链**：`0x48CCCF call 0x52BA60` → `0x52BB64 call 0x5301A0`（即 expandmd 99→00 序号循环：`0x5301BA mov edi,0x63` + `0x5301C4 push 0x82668C` = `EXPANDMD%02d.MIX` + `0x5301CA call 0x7C8EF4` CRT sprintf + `0x53028D dec edi / jns`）；
> 3. **顺序语义**：ctor 尾插（`0x5B3DE2`–`0x5B3E00`）+ `Find` 自 `Head.Next (0xABEFE0)` 起向后（`0x5B44A1` / `0x5B44FD`）= **FIFO，先装载者优先**。
> ⇒ **正确优先级（高→低）**：散装文件 > `langmd.mix` > `language.mix` > `expandmd99 … expandmd00` > `ra2md.mix` > `ra2.mix` > `cachemd` > `cache` > `localmd` > `local` > `ecache*` > `elocal*` > （次级）`CONQMD … MOVIES*`。
> ⇒ **`expandmd99.mix` 无法覆盖 `langmd/language.mix` 内的同名 CRC 条目**；要覆盖只能靠散装文件。
> **⚠️ 勘误 E4（同批）**：`InstallPath` / `CDPath` / `[CD]` 在全镜像**0 命中**（Lead 复算确认），CD 只以「门禁」（每个 MIX 装载前的 `CD_Check`、文件缺失时的 `CDCheck` 虚函数）与「次级装载器 6 个通配的二次 `FindFirstFileA`」参与，**不进入散装/MIX 查找链，不改变优先级**（前序「证据不足」升级为「不进入」）。

**回答两个项目强依赖的问题**：
1. 引擎**确实**按序加载自定义 `expandmd*.mix`，且 `EXPANDMD%02d` 的循环上限是 **99**（`mov edi,0x63`）→ `expandmd98.mix` 属合法装载序列第 2 位。
2. **同名条目谁赢**：`expandmd98.mix` 里的条目与 `ra2md.mix` 官方条目 **CRC32 ID 相同**时，**`expandmd98.mix` 赢**（它先加载）→ **可以覆盖官方条目**；但被 `expandmd99.mix`（若存在）和游戏目录散装文件覆盖。
3. MIX 查找**只看 CRC32 ID**，不需要名字表；`local mix database.dat` 是 XCC 私有约定（见 §6 勘误 2）。

---

## 4. 必答项 4：`*.INI` 追加语义（`BATTLEMD98.INI` vs 官方 `battlemd.ini`）

### 4.1 读取点：`0x52CB90`（`sub esp,0x1B4`，被 `0x52C605` 调用；另有 `0x52DF25`/`0x52E0C4`/`0x685609` 调用）

```
0x52CBA0  68 A8 61 82 00     push 0x8261A8        ; "BATTLEMD*.INI"
0x52CBA9  FF 15 08 12 7E 00  call [0x7E1208]      ; = KERNEL32!FindFirstFileA（IAT 已解析）
0x52CBB1  83 FE FF           cmp esi,-1           ; INVALID_HANDLE_VALUE → 直接走回退分支 0x52CCCD
-- 合并循环（对每个匹配到的文件）------------------------------------------------
0x52CBBE  08   test dword[esp+0x84],0x116         ; dwFileAttributes 过滤目录等
0x52CBF6  E8 F5 6D F4 FF     call 0x4739F0        ; CCFileClass ctor(枚举到的文件名)
0x52CBFD  E8 15 C2 29 00     call 0x7C8E17        ; new(0x58) = CCINIClass
0x52CC36  C7 06 F4 1A 7E 00  mov [esi],0x7E1AF4   ; CCINIClass vftable
0x52CC49  E8 A2 75 F4 FF     call 0x4741F0        ; INIClass::Load(fileclass,0,0) → 0x525A60 内层解析
0x52CC54  E8 C7 C0 29 00     call 0x7C8D20        ; _stricmp(枚举名,"BATTLEMD.INI")
0x52CC60                      mov byte[esp+0x13],1 ; 命中 → 置"已见过 BATTLEMD.INI"标志
0x52CC67  E8 A4 01 F4 FF     call 0x46CE10        ; ★ 合并进全局 Battle 表（见 4.2）
0x52CC70                      mov edx,[esi]; push 1; call [edx]   ; 析构并释放该 CCINIClass
0x52CCAB  FF 15 0C 12 7E 00  call [0x7E120C]      ; FindNextFileA → 回到 0x52CBBF
0x52CCBA  FF 15 00 13 7E 00  call [0x7E1300]      ; FindClose
0x52CCC5  3A C3               cmp al,bl
0x52CCC7  0F 85 92 00 00 00  jne 0x52CD5F         ; 已经装载过 BATTLEMD.INI → 结束，不重复
-- 回退分支 --------------------------------------------------------------------
0x52CCCD  68 98 61 82 00     push 0x826198        ; "BATTLEMD.INI"
0x52CCD6  E8 15 6D F4 FF     call 0x4739F0        ; CCFileClass ctor（★ 可来自 MIX）
0x52CCDD  E8 35 C1 29 00     call 0x7C8E17        ; new(0x58) CCINIClass
0x52CD25  E8 C6 74 F4 FF     call 0x4741F0        ; Load
0x52CD2C  E8 DF 00 F4 FF     call 0x46CE10        ; ★ 同一个合并函数
```
要点：
- **`BATTLEMD*.INI` 是文件系统通配**（`FindFirstFileA`），**不会看到 MIX 内部的条目**。所以 `expandmd98.mix` 里的 `BATTLEMD98.INI` 永远命中不了这条通配。
- 反之，**`BATTLEMD.INI` 这一路是 `CCFileClass`**（mix 感知）→ MIX 里的 `BATTLEMD.INI` 能被读到（本项目 `expandmd98.mix` 实测含 `crc32("BATTLEMD.INI")=0x07E280DD`、241 字节，与 `ra2youli/BATTLEMD.INI` 同尺寸）。
- 两者**互斥**：只要目录里存在任意 `BATTLEMD*.INI`（含 `BATTLEMD.INI` 本身），且其中之一恰为空…见下：只要 `BATTLEMD.INI` 出现在通配结果里，`0x52CCC7 jne 0x52CD5F` 就跳过回退，**MIX 内那份不会被读**。

### 4.2 合并实现：`0x46CE10` + 全局 Battle 表

`0x46CE10`（仅被 `0x52CC67`、`0x52CD2C` 调用 —— 正是上面两条路径）：

```
0x46CE17  68 D8 B1 81 00     push 0x81B1D8        ; ★ 段名 "Battles"（同址字符串表：0x81B1C8="FinalMovie"）
0x46CE1C  E8 3F 9B 0B 00     call 0x526960        ; [推演] 按段名 CRC32 定位 "Battles" 段并返回条目数 n（内部实证：段名做 CRC32 后查 [this+0x28] 段链）
0x46CE34..0x46CE55           for (i=0;i<n;i++) 0x526CC0(ini,"Battles",i,buf,0x20,&..)  [推演] 取第 i 个条目名
0x46CE5A  A1 08 3D A8 00     mov eax,[0xA83D08]   ; ★ Count of g_Battles
0x46CE65  .. 0x46CE77        _stricmp(g_Battles[j]+0x24, buf)   ; 按对象内 +0x24 的名字匹配
0x46CE81/0x46CE8F            命中 → idx=j；未命中 → esi=-1
0x46CE97  68 A0 03 00 00     push 0x3A0           ; 未命中：new(0x3A0)=928 字节新战斗对象
0x46CEB5  E8 46 39 FA FF     call 0x410800        ; 用名字初始化
0x46CEC6  C7 06 28 4A 7E 00  mov [esi],0x7E4A28   ; vftable 组（+4/+8/+C 另三张）
0x46CEEC..0x46CF1D           容量不足 → 经 [0xA83CF8] 的 vtable+8 扩容
0x46CF1F..0x46CF34           count++ ; mov [ecx+eax*4],esi  ; ★ push_back 到 0xA83CFC
0x46CF37                     strcpy(esi+0x2A0, 0x887734) ; 默认串
0x46CF58  未命中→复用：mov eax,[0xA83CFC]; mov esi,[eax+esi*4]
0x46CF60  8B 16 / FF 52 64     mov edx,[esi]; call [edx+0x64]  ; ★ 把本 INI 的 Scenario=/CD=/
                                                              ;   FinalMovie=/Description= 写入该对象
0x46CF68..0x46CF6D           inc ebp; cmp ebp,[esp+0x10]; jl 0x46CE34   ; ★★ 合并循环主体
```
**全局表**：`DynamicVectorClass` 基址 `0xA83CF8`，`Items=0xA83CFC`、`Capacity=0xA83D00`、标志字节 `0xA83D04/0xA83D05`、**`Count=0xA83D08`**、`GrowthStep=0xA83D0C`；元素 0x3A0 字节，名字（战斗 ID，如 `ALL1`/`SOV1`）在 `+0x24`，替换串缓冲在 `+0x2A0`。

**合并语义（Q4 结论）**：
- 归并键 = `[Battles]` 段里的**条目名**（战斗 ID），比较用 `_stricmp`（不分大小写）。
- **同名条目跨文件归并到同一个对象**：先出现的创建对象，后出现的复用同一对象再 `vtbl+0x64(ini)` 覆写字段 → 对同一战斗 ID **后装载者覆盖**（per-key last-write-wins）。
- 不同 ID → 追加新对象（`[Battles]` 里 `1=ALL1, 2=SOV1` 这种编号键只是**枚举顺序**，不是身份）。
- 跨文件的先后 = **目录枚举顺序**（`FindFirstFileA/FindNextFileA`，NTFS 通常近似字母序但**非引擎保证**）；同目录内 `BATTLEMD.INI` < `BATTLEMD01.INI` … < `BATTLEMD98.INI` 一般在字母序下后者靠后 → `BATTLEMD98.INI` 通常胜出。[推演]+[待实测]
- 每个文件的 INI 对象是**临时对象**，装载后即析构；所有数据只能经 `0x46CE10` 落到全局表 —— 这也是为什么"往 MIX 里塞 `battlemd.ini`"只在**没有散装 `BATTLEMD.INI`** 时才有效。

---

## 5. 关键地址总表（便于工具/补丁引用）

```
# ---- 装载 ----
0x52BA60  Init()（Init.CPP）                           0x48CCCF 调用
0x5301A0  主 MIX 装载（EXPANDMD99..00 + RA2MD/RA2/CACHEMD/CACHE/LOCALMD/LOCAL）
0x530000  通配装载（ECACHE*.MIX / ELOCAL*.MIX）
0x530460  次级装载（CONQMD/GENERIC/ISOGEN/CONQUER/CAMEO/MAPS*/MULTIMD/THEMEMD/THEME/MOVIES*/MOVMD*）
0x5312A0  Init 收尾装载
0x6BD6E0  内嵌 [PublicKey] INI → 516B 公钥 → LANGMD.MIX/LANGUAGE.MIX
# ---- 表 ----
0x884D90  DynamicVectorClass<MixFileClass*>（Items 0x884D94 / Cap 0x884D98 / Count 0x884DA0 / Step 0x884DA4）
0xABEFD8  List<MixFileClass*> 优先级表（Head.Next=0xABEFE0, Tail.Prev=0xABEFF0）
0x884DF8=ra2md.mix  0x884DFC=ra2.mix  0x884E48=cachemd  0x884E4C=cache
0x884E50=localmd    0x884E54=local    0x884E04=langmd.mix
0x886980  516 字节 RSA 公钥结构（[PublicKey] 解析结果）
0x7E1A80  内嵌 "[PublicKey]\n1=AihRvNoIbTn85FZRYNZRcT+i6KpU+maCsEqr3Q5q+LDB5tH7Tz2qQ38V\n\n"
0x8189C8  base64 字母表
0xA83CF8  Battle 全局表（Items 0xA83CFC / Cap 0xA83D00 / Count 0xA83D08），元素 0x3A0B
# ---- 文件 ----
0x4739F0  CCFileClass::CCFileClass(char const*)        0x7E16B0 vftable
0x473C50  CCFileClass::Open (vtbl+0x14)
0x473D10  CCFileClass::Get_File (vtbl+0x1C)
0x5B4430  MixFileClass::Find(name, outData, outMix, outOff, outSize)
0x65CBF0  RawFileClass::Open (CreateFileA @0x65CC59)
0x7DCFC4  strupr（名字归一）      0x4A1DE0 CRC32（表 @0x81F7B4）
# ---- 解密 ----
0x5B3C20  MixFileClass::MixFileClass(name, pPublicKey)
0x633050  PKStraw::PKStraw          0x6330C0 PKStraw::Attach
0x633110  PKStraw::Set_Key          0x633130 PKStraw::Get
0x52A670  INIClass::BuildKeyStruct(out516, useRSA)   e=0x10001 @0x52A6AF
0x5C6370  BigNum<-DER INTEGER        0x631F60 公钥结构 ctor（[+0x200]=位长-1）
0x840A78  "blowfish.dll"             0x7F3710 COM 组件表        0x6BEDB0 绑定器
# ---- INI 追加 ----
0x52CB90  LoadBattleMdIni（BATTLEMD*.INI 通配 + BATTLEMD.INI 回退）
0x4741F0  INIClass::Load(fileclass,...) → 0x525A60 内层解析
0x46CE10  Register_Battles（[Battles] 归并循环 → 0xA83CF8）
```

---

## 6. 与 `ra2forge/mixlib.py` 的交叉验证 & 勘误

**交叉验证（一致项）**
1. `crc_hash()` = `zlib.crc32(name.upper())`：引擎侧 `0x5B4430` 先 `0x7DCFC4`（大写归一）再 `0x4A1DE0`（CRC32 引擎，表 `0x81F7B4`）→ 一致。**用项目真实产物端点验证**（`out/re_work/fs_mix/probe3.py`）：`ra2youli/expandmd98.mix` 5 个条目的 ID 与 `mixlib.crc_hash` 全部吻合：
   `BATTLEMD.INI=0x07E280DD`、`ECH01.MAP=0x8067D343`、`ECH02.MAP=0xC7C7A993`、`ECH03.MAP=0xFAA78023`、`LOCAL MIX DATABASE.DAT=0xF7EE6278`；该 mix 的 `local mix database.dat`（95B）里列出的名字正是这 5 个 → **引擎哈希算法 = mixlib 哈希算法**（[实证]，且在磁盘真实产物上闭合）。
2. Blowfish 密钥推导：mixlib `westwood_decrypt_key_block()`（两个 40 字节块、`pow(c, 0x10001, modulus)`、拼接进 56 字节缓冲）与引擎 `0x633130` 的块长公式 `(55/blockBytes+1)*(blockBytes+1) = 80`、`0x52A6AF` 的 `e=0x10001`、`0x631F60` 的 56 字节语义完全对应。
3. 公钥解析：mixlib 做 base64 → DER `02 28` → 40 字节大端模数；引擎 `0x5C6370` 明确是 **DER INTEGER（tag 0x02）解析并倒序入 BigNum**，base64 字母表在 `0x8189C8`（`0x7E3910` 引用）→ 语义一致。
4. 明文/加密判定：mixlib `flags & 0x2` → 与引擎 `0x5B3D11`（`(flags>>1)&1`）一致。
5. `write_mix()` 写未加密 MIX（`fmt=0, flags=0`）：引擎 `0x5B3D11 je` 旁路即可直接读 → 项目注入策略成立。

**勘误（新旧对照）**

| # | 项 | mixlib 旧实现 | 引擎实证行为 | 处置建议 |
|---|---|---|---|---|
| E1 | `local mix database.dat` | 在 `write_mix()` 里自动写入，且注释称"引擎的通配加载靠它解析名字" | 全 exe 检索 `"local mix database"`（不分大小写）**0 命中**；MIX 查找只做 CRC32 二分（`0x5B44D5`），不读名字表 | **注释需改**：该文件仅 XCC/WAE 等外部工具有用，**引擎不依赖**；"缺它会通配失败"的说法对本引擎不成立 |
| E2 | 老式 MIX 头 | `first != 0` 即 `raise ValueError`（只接受 TS/RA2 头） | 引擎在 `first != 0` 时走 `0x5B3D4F` 分支（老式 C&C 头：`word0=numFiles`，再补读 2 字节） | mixlib 属"能力缺口"而非错误；读 RA2/YR 资产无影响，若需读 TD/老资产需补该分支 |
| E3 | 同名条目覆盖语义 | mixlib 无查找顺序概念（`get()` 只按第一个 entry.id 命中自己的条目） | 引擎是**跨 MIX 的 FIFO 列表**：先加载者优先（`0x5B44A1` + `0x5B44FD`），且**散装文件高于所有 MIX**（`0x473D2D`） | 建议在 mixlib 文档字符串里补"优先级由调用方（引擎）决定：散装 > expandmd99 > … > local" |
| E4 | 密钥块长度 | 代码里硬编码两个 40 字节块（`for i in (0, 40)`） | 引擎按模数位长动态算：`(55/floor((bits-1)/8) + 1) * (floor((bits-1)/8)+1)`，320bit→80B | 一致（对 YR 公钥成立）；若要通用化，按引擎式动态算 |

---

## 7. 对本项目的直接结论（可操作）

1. **`ra2youli/expandmd98.mix` 的注入路径成立**，且 `expandmd98` 在 99..00 的序列里属"高优先"档：它的条目会**覆盖 `ra2md.mix` 中的官方同名条目**。若需压倒其它自定义包，用 `expandmd99.mix`；若要与官方同名的 `expandmd01.mix` 共存，注意 `98 > 01`（98 先加载 → 98 赢）。
2. `expandmd98.mix` 里放 `BATTLEMD.INI`（官方名）**有效**，但只在**游戏目录没有散装 `BATTLEMD.INI`** 时才会被读（`0x52CCC7` 的回退跳过）。当前仓库里 `ra2youli/BATTLEMD.INI` 与 mix 内同名文件同时存在 → 散装那份赢，mix 内那份被跳过（内容相同所以无差异）。
3. 想用 `BATTLEMD98.INI` 这个"数字后缀"方案，**必须把 `BATTLEMD98.INI` 放在游戏目录**（不是 MIX 里）：`0x52CBA0` 的通配走 `FindFirstFileA`，只看文件系统；MIX 内的 `BATTLEMD98.INI` 永远不会被这条通配发现。
4. BATTLEMD 的语义是**按 `[Battles]` 条目名归并**：`BATTLEMD98.INI` 用与官方相同的战斗 ID（如 `ALL1`、`SOV1`）时是"覆写官方条目"（后装载者覆写字段），用新 ID（如 `ECH1`）时是"新增战役"。本项目 `ra2youli/BATTLEMD.INI` 覆盖 `ALL1/SOV1` 正是前者。
5. 同一战斗 ID 在**多个** `BATTLEMD*.INI` 同时出现时，最终胜者取决于目录枚举顺序（`[待实测]`）。**工程上应避免跨文件重复 ID**，或干脆只保留一个 `BATTLEMD98.INI`。

---

## 8. 未闭环与下一步取法

| # | 未闭环项 | 现状 | 下一步取法 |
|---|---|---|---|
| 1 | 目录枚举顺序导致的"最终胜者" | 只有代码路径实证，无运行时确认 | 放两个冲突的散装 `BATTLEMD01/02.INI`（同一 ID 不同 `Description`），在 `0x46CE10` 入口下断或用调试器对 `0xA83D08`（Count）+1 处设写 watch，观察装载次序与最终 `vtbl+0x64` 覆写结果 |
| 2 | `MixFileClass::Cache()`（整 MIX 解密入 `+0x24`）的**填充函数** | 已定位释放/读路径（`0x5B3F14` `0x5B3F6C` `0x5B4400` `0x5B454C`），填充点未找到（对 `+0x24` 的 `mov [reg+0x24],eax` 形态全 `.text` 扫描无命中） | ①对 `MixFileClass+0x12`（字节）设写 watch；②反查 `0x5B4430` 中 `[ebp+0x24] != 0` 分支的上游调用者（谁把 MIX 标成 cached）；③检查 `0x5B40B0`（`sub esp,0x180` + `new` + 循环 `0x5B3FF0`）是否为 Cache/Free_All_Memory 家族 |
| 3 | `CCFileClass+0x54/+0x58/+0x5C/+0x60` 精确语义；vtbl `+0x20`(0x401980 桩) 与 `+0x38/+0x3C` 的完整语义 | 只部分实证（`+0x64` 当前位置、`+0x68` 0/1/2 状态、`+0x58` 内存缓冲） | 逐个 dump `0x473A00`–`0x474000` 全部槽位并交叉 `0x431xxx` 家族（`0x431F10/0x431F30/0x432050/0x4322A0/0x4324B0/0x4325A0`）的 `[reg+0x25/+0x26/+0x29]` 用法 |
| 4 | `RA2MD.INI [CD]` 路径如何进入搜索链 | 未定位；`-CD` 检查在 `0x52C5BF`，`RA2MD.INI`(0x826444) 的 11 处引用里未见 `[CD]` 段名 | 全 exe 搜 `[CD]`/`"CD"`/`"InstallPath"` 段名字符串（本轮 `InstallPath/CDPath` 0 命中，疑为 `"CD"` 段）→ 反查引用点；或从 `CDFileClass`(vtable `0x7E1668`) 的 ctor/Open 反推 |
| 5 | `0x530460` 每个次级 MIX 的**存在性检查与优先级细节** | 仅抽取了字符串出现顺序（= 装载顺序），未逐分支读 | dump `fn_530460_secondary_mix.txt` 逐段（含 `0x531180/0x5311EB` 的 `%02d` 循环边界）核对 |
| 6 | `LANGUAGE.MIX` 的完整装载点（`0x6BD819` 附近）与本项目语言包策略 | 只确认字符串与公钥复用 | 从 `0x840D4C` 的 xref（`0x6BD819`）展开 |
| 7 | `0x5312A0` / `0x52CD70`(RULEMD*.INI 同构装载) | 未展开 | 按 §4 同法 dump `0x52CD70`–`0x52CF00` 核对是否同样 `FindFirstFileA` 通配 |

---

## 9. 证据文件清单（全部在 `out/re_work/fs_mix/`）

```
claims.txt                      124 条字节级断言（用 tools/audit_bytes.py 复核，本轮 124/124 OK）
genclaims2.py                   生成 claims.txt（含"期望字符串"由人工从反汇编清单读出后写成 hex）
s12_sweep.py  sweep.pkl  insn_addrs.pkl    全 .text 可靠指令边界（1,394,120 条）
sdump.py  fn_*.txt                         逐函数反汇编清单
xref.py ptrs.py refscan.py callmap.py      xref 工具（立即数/指针/E8 原始扫描）
vtclass2.py vtsum.py vtdump.py rtti2.py    RTTI→类名 与 vtable 摘要
iat.py iat.json                            IAT 符号解析（FindFirstFileA/FindNextFileA/FindClose/CreateFileA/…）
strings_all.txt                            全 exe 字符串（16,766 条，带 VA）
fn_5301A0_primary_mix.txt                  主 MIX 装载（EXPANDMD/RA2MD/RA2/CACHE/LOCAL）
fn_530056.txt                              通配 MIX 装载（ECACHE*/ELOCAL*）
fn_530460_secondary_mix.txt                次级装载（1076 行）
fn_52BA60_init.txt                         Init()（1169 行）
fn_52CB90_ini_battlemd.txt                 BATTLEMD*.INI 读取与合并循环
fn_52A670_keyprovider.txt                  516B 公钥结构装配（e=0x10001）
fn_633050_blowstraw.txt                    PKStraw/BlowStraw
fn_5B3C20.txt                              MixFileClass ctor（含 flag/加密分支/尾插）
fn_5B3A40.txt                              链表静态 init / Finder / 解链
fn_5B43F0_finder.txt                       MixFileClass::Find（含 0x5B4400 Uncache）
fn_473AB0_ccfile.txt                       CCFileClass/FileStraw 方法簇
fn_473D10.txt                              CCFileClass::Get_File（磁盘优先 + MIX 回落）
fn_4741F0.txt                              INIClass::Load 外壳
disasm_52B800_531400.txt                   初始粗粒度反汇编（360KB，仅供检索）
probe1..probe13.py                         mixlib 交叉验证 / 公钥检索 / 表结构探测脚本
rsa_modulus.bin                            从 OpenRA 公钥 base64 解出的 40 字节模数（对照用）
```

---

## 10. 复算方法

```powershell
cd D:\Project\ra2-campaign-forge
python tools/audit_bytes.py out/re_work/fs_mix/claims.txt            # 期望 124/124 OK
python out/re_work/fs_mix/probe3.py                                  # mixlib 与真实 mix 的 CRC 对照
python out/re_work/fs_mix/sdump.py 0x5301A0 0x530460                 # 主 MIX 装载反汇编
```

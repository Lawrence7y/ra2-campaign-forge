# S03-K1 · CCFileClass / MixFileClass 布局与 MIX 查找链

> 卡号 S03-K1｜证据全部本卡自取（capstone skipdata=True + pefile；Ghidra SLEIGH 独立通道 E08）。
> 分级：`[已证]`=写点+读点双重支撑且双通道一致；`[静态推断]`=字节实证但语义靠上下文；`[未证]`=仅单点/无读点。
> **字段数口径**：下表每个具名行计 1 字段；多字节数组/内嵌对象整体计 1 行。继承字段标注来源基类。

## 0. 双通道定位（纪律 1：至少一条不依赖 function_atlas）

| 类 | RTTI TypeDescriptor | 主 vftable | 通道 A（capstone RTTI→COL→vft + 字节扫描） | 通道 B（Ghidra SLEIGH 独立反汇编，-noanalysis） |
|---|---|---|---|---|
| `CCFileClass` | `0x815E58` `.?AVCCFileClass@@` | `0x7E16B0` (COL `0x7FA590`, off 0, 17 slots) | ctor `0x4739F0`(ret 4)；vft 写点 `0x473A12` | E08 与 capstone 逐字节一致 |
| `MixFileClass` | `0x82C318` `.?AVMixFileClass@@` | `0x7EDF50` (COL `0x805DE0`, off 0) | ctor `0x5B3C20`(ret 8)；vft 写点 `0x5B3C52` | E08 一致 |

- 继承链（RTTI + ctor 调用）：`FileClass(0x7F08BC)` → `RawFileClass(0x7F0904)` → `BufferIOFileClass(0x7E3A2C)` → `CDFileClass(0x7E1668)` → `CCFileClass(0x7E16B0)`。CCFileClass ctor `0x4739F3 call 0x47AA30`=CDFileClass 基类 ctor（置 `+0`=0x7E1668），随后 `0x473A12` 改回自身 vft `0x7E16B0`。
- 纪律 17 落实：类名只认 RTTI TypeDescriptor。台账 §27610 记载 `0x65CA80` 曾被按文件名误标 CCFileClass（实为 RawFileClass）；本卡以 RTTI 实测为准——CCFileClass ctor 是 `0x4739F0`，`0x65CA80` 不在本卡任何结论中。

## 1. CCFileClass 字段表（**12 字段**，对象大小 `0x6C`）

| # | 偏移 | 宽 | 类型 | 写者站点 | 读者站点 | 语义 | 级 |
|---|---|---|---|---|---|---|---|
| 1 | +0x00 | 4 | vptr | `473A12` ctor=0x7E16B0；`473A4F`/`473A9B` 重载 | 间接虚调用 | 主 vtable `0x7E16B0` | 已证 |
| 2 | +0x14 | 4 | HANDLE | `65CC62` RawFile::Open←CreateFileA | `65CC2D`→CloseHandle | 文件句柄（继承 RawFileClass；-1=未开） | 已证 |
| 3 | +0x18 | 4 | char* | `47AE10` Set_Name(strdup 名字参数) | `65CBF4`/`65CC3B`/`65CC58`→CreateFileA | 文件名**指针**（strdup，非内联） | 已证 |
| 4 | +0x19 | 1 | byte | 基类 ctor 链 | `431F30` Is_Available 判定 | 状态字节（继承，语义靠上下文） | 静态推断 |
| 5 | +0x25 | 1 | byte | 基类 ctor 链 | `431F10`/`431F30` | 已开/就绪标志 | 静态推断 |
| 6 | +0x29 | 1 | byte | `431F10 mov al,[ecx+0x29]` 读前 | `431F10` 判定 | Open 内部状态字节 | 静态推断 |
| 7 | +0x54 | 1 | byte | `47AA38` 基类 ctor=0；`473DB1`=1；`473DBD`=0 | `47AE26` CD 门禁读 | SkipCDCheck / 缓冲归属标志 | 已证 |
| 8 | +0x58 | 4 | void* | `4739FF`→`43AD0D` Buffer 构造；`43AD25` 分配 | `473AE3`/`473C04`/`473CD2`/`473B32` | 内存 Buffer 数据指针（内嵌 BufferClass @+0x58） | 已证 |
| 9 | +0x5C | 4 | int | `43AD0F` Buffer 构造(length) | `473C0B` Size 返回；`473BB5` Seek EOF | 缓冲长度 | 已证 |
| 10 | +0x60 | 1 | byte | `43AD12`=0；`43AD27`=1 | Buffer 内部 | Buffer.IsHeapAllocated（缓冲是否自有） | 已证 |
| 11 | +0x64 | 4 | int | `473A0B`/`473A48`/`473A94`/`473CF5`=0；`473BB3`/`473BB8`/`473BD6`/`473BDB` | `473B36`/`473BC8` | 当前读/定位位置（MIX 内为条目相对偏移） | 已证 |
| 12 | +0x68 | 4 | int | `473A18`=0；`473C70`/`473C94`/`473CAB`=1；`473CB5`=2 | `473C59` cmp 1 | 打开状态 0=未开/1=就绪/2=失败 | 已证 |

- **所属 MIX 指针**：CCFileClass **无**持久化 MIX 指针字段。`0x5B4430 MixFileClass::Find` 把命中 MIX 作为**输出参数**返回（`0x5B4518 mov [eax],ebp`）；`0x473D10 Get_File` 仅在该次调用栈内用它取容器名（`0x473D89 mov eax,[eax+0xc]`）或缓存体（`0x5B4553`），不写回 `this`。[已证]
- 最大偏移+宽度 = `0x68+4 = 0x6C` = 对象大小（`push 0x6C` @`0x407BF3`/`0x433999` + new `0x7C8E17` + ctor `0x4739F0`）。

## 2. MixFileClass 字段表（**12 字段**，对象大小 `0x28`）

| # | 偏移 | 宽 | 类型 | 写者站点 | 读者站点 | 语义 | 级 |
|---|---|---|---|---|---|---|---|
| 1 | +0x00 | 4 | vptr | `5B3C52` ctor=0x7EDF50 | `5B45C7` 改 0x7EDF40 | 主 vtable `0x7EDF50` | 已证 |
| 2 | +0x04 | 4 | node* | `5B3C31`=0；`5B3DF3`=尾节点Next | `5B4594`/`5B3DED` | 优先级链表 Next（GenericNode） | 已证 |
| 3 | +0x08 | 4 | node* | `5B3C34`=0；`5B3DF0`=尾 | `5B459B`/`5B45AB` | 优先级链表 Prev | 已证 |
| 4 | +0x0C | 4 | char* | `5B3C37`=0；`5B3C9D`=strdup(name) | `5B45C4` 析构 free | MIX 文件名（strdup） | 已证 |
| 5 | +0x10 | 1 | byte | `5B3C3A`=0；`5B3D0B`=flags&1 | 逻辑分支 | flags bit0 | 已证 |
| 6 | +0x11 | 1 | byte | `5B3C3D`=0；`5B3D0E`=(flags>>1)&1 | `5B3D11` je 加密分支 | flags bit1=**加密标志** | 已证 |
| 7 | +0x12 | 1 | byte | `5B3C40`=0 | `5B3F14` 等 free 路径 | 缓冲归属（cached body 是否自有） | 静态推断 |
| 8 | +0x14 | 4 | int | `5B3C43`=0；`5B3D7E`=movsx word[numFiles] | `5B44CB` Find 上界；`5B3DB9` | 条目数（头里是 signed word） | 已证 |
| 9 | +0x18 | 4 | int | `5B3C46`=0；`5B3D84`=bodySize dword | 逻辑 | MIX body 大小 | 已证 |
| 10 | +0x1C | 4 | int | `5B3C49`=0；`5B3DDF`=Seek返回+长度 | `5B4565` Find 输出偏移 | 数据起始偏移（条目区之后） | 已证 |
| 11 | +0x20 | 4 | Entry* | `5B3C4C`=0；`5B3D95`=new(numFiles*12) | `5B44CE` Find 基址 | 索引表指针（**每项 12B**） | 已证 |
| 12 | +0x24 | 4 | byte* | `5B3C4F`=0 | `5B454C`/`5B455A` Find | 整包缓存体（解密后）或 NULL | 已证 |

- 最大偏移+宽度 = `0x24+4 = 0x28` = 对象大小（60 个 ctor 调用点中 59 个 `push 0x28`+new `0x7C8E17`，1 个栈对象）。

## 3. MIX 头与索引结构（经典 Westwood MIX）

- **明文 4 字节头**：`0x5B3CF4 call [straw+8]` 读 4 字节 → `[esp+0x28]` word0=format（0=新头）、`[esp+0x2A]` word1=flags。`0x5B3CF7 cmp word[..],0` 非零走老式 C&C 头分支 `0x5B3D4F`。
- **flags**：`0x5B3D02 shr eax,1; and cl,1` → `+0x10=flags&1`；`and al,1` → `+0x11=(flags>>1)&1`。`0x5B3D11 je 0x5B3D3F`：bit1=0 跳过密钥块 ⇒ **未加密 MIX** 直接读。
- **加密头（flags bit1=1）**：PKStraw `0x633050`（内含 BlowStraw `0x7EDF40`）；`0x633110` Set_Key（公钥结构 @`0x886980`，516B）；`0x6330C0` Attach；`0x633130 Get` 读 RSA 密钥块（`e=0x10001` @`0x52A6AF`），Blowfish 后端经 `blowfish.dll`(字符串 `0x840A78`) COM 动态加载。**RSA 用于密钥块、Blowfish 用于体数据**。[静态推断：加解密调用链未逐条 dump 到分组层，但入口/常量经字节实证]
- **条目头 6 字节**：`0x5B3D4A call [straw+8]` 读 6 字节 → `movsx word [esp+0xc]`=numFiles（`+0x14`）、`dword [esp+0xe]`=bodySize（`+0x18`）。
- **索引表**：`0x5B3D81 lea edx,[eax+eax*2]; 0x5B3D87 shl edx,2` = `numFiles*3*4 = numFiles*12` → `call 0x7C8E17` new → `+0x20`。**每项 12 字节 = {u32 id(CRC32); u32 offset; u32 size}**（`0x5B44DF mov esi,[edi+edx*4]` 取 id、`0x5B4543 mov eax,[edx+4]` 取 offset、`0x5B4525 mov ecx,[edx+8]` 取 size）。无独立哈希表/名字表——查找只对 id 做二分（分布式哈希表即索引本身，按 id 排序）。

## 4. 哈希算法（MIX 查找链核心）

| 项 | 值 | 证据 |
|---|---|---|
| 哈希函数 | **`0x4A1DE0`**（CRC32 引擎，thiscall，输入=大写名+长度） | `0x5B4499 call 0x4A1DE0`；E05/E08 |
| 名字归一 | **`0x7DCFC4` strupr**（大写） | `0x5B4470 call 0x7DCFC4` |
| 初始值 | **`0xFFFFFFFF`**（`not eax` @`0x4A1E79`） | E05/E08 |
| 多项式 | **反射 `0xEDB88320`**（表 `0x81F7B4`，`u32[1]=0x77073096`） | E05；表首 8 项=`00000000 77073096 EE0E612C 990951BA…` |
| 查表/移位 | `shr eax,8`(`4A1E8E`)；`mov edx,[edx*4+0x81F7B4]`(`4A1E91`)；`xor eax,edx`(`4A1E98`) | E05/E08 |
| 最终异或 | **`0xFFFFFFFF`**（`not eax` @`0x4A1E9E`） | E05/E08 |
| 交叉验证 | `crc_hash = zlib.crc32(name.upper())`；真实 `expandmd98.mix` 5 条目 ID 全部吻合（线索文档，本卡未独立验证产物） | 线索 only |

## 5. MIX 查找链（每跳给调用点地址）

```
资源请求(按文件名)  CCFileClass::Open 0x473C50 / Size 0x473C00 / Get_File 0x473D10
   ├─ 0x473C3A / 0x473C8B : call 0x5B4430  (Open/Size 的 MIX 存在性探测)
   └─ Get_File 0x473D10:
        ├─ 0x473D2D : call 0x431F10 → RawFileClass::Open 0x65CBF0 → CreateFileA   [磁盘优先]
        └─ 0x473D68 : call 0x5B4430  MixFileClass::Find                            [MIX 回落]
MixFileClass::Find 0x5B4430:
   ├─ 0x5B4470 : call 0x7DCFC4  strupr(name)             [大写归一]
   ├─ 0x5B4499 : call 0x4A1DE0  CRC32(name)              [哈希]
   ├─ 0x5B44A1 : mov ebp,[0xABEFE0]  链表头=最早装载 MIX   [FIFO，先装载者优先]
   ├─ 0x5B44D5..0x5B44F9 : 除半查找（12B 步长，cmp id@5B44E5）[索引定位]
   └─ 命中输出：0x5B4518 outMix；0x5B4543 offset；0x5B4525 size；0x5B4553/0x5B4565 缓存体/数据起点
```

- 散装优先：`0x473D2D`（磁盘）早于 `0x473D68`（MIX），无排序调用；MIX 内按链表 `Head.Next` 顺序（先装载者优先，FIFO）。

## 6. GetSize 一致性 + 越界写（纪律：两处独立对账）

> **事实修正**：这两个类**不是 AbstractClass 派生**，vtable 无 S16-K1 式 `v[12] = B8 <imm32> C3` 的 GetSize 方法（`CCFileClass v[12]=0x473AE0` 实为带 2 参数的 `Read`-family 方法 `ret 8`；MixFileClass vft 仅 1 槽）。因此采用 K 类等价核对：**构造器 `new(size)` 分配点** ↔ **字段 `max(disp+width)`**（两处独立来源）。

| 类 | new(size) 分配点（通道 A 字节扫描） | 字段 max(disp+width) | 字段写点数 | 越界写数 |
|---|---|---|---|---|
| CCFileClass | `0x6C`（`push 0x6C`@`407BF3`/`433999`；164 ctor 点中独立 new 均 0x6C） | `0x68+4=0x6C` | 10 | **0** |
| MixFileClass | `0x28`（59/60 个 `push 0x28`@`406C8F`/`47939E`…；另 1 栈对象） | `0x24+4=0x28` | 21 | **0** |

- 越界判据：对每个 this=[esi] 的 `[reg+disp]` 写（capstone 解析宽度），`disp+width ≤ size` 全部成立；E06 完整列出 31 个写点，0 处 OOB。

## 7. 与 DLC 通配的关系（散装 vs MIX 内 → 同一 INI 解析器）

- `0x52CB90`(BATTLE) / `0x52CD70`(RULE) 先用 `FindFirstFileA`(`0x7E1208`) 枚举**磁盘散装** `BATTLEMD*.INI`/`RULEMD*.INI`，对每命中：
  `call 0x4739F0`(CCFileClass ctor, `52CBF6`/`52CDEC`) → `call 0x4741F0`(INIClass::Load, `52CC49`/`52CE1E`)。
- 通配 0 命中时的回退用字面量官方名 `BATTLEMD.INI`/`RULESMD.INI` 再走 `call 0x4739F0`(`52CCD6`/`52CF41`) → `call 0x4741F0`(`52CD25`/`52CF73`)；这一路 CCFileClass 是 MIX 感知的（磁盘缺失时 `0x473D68` 回落 MIX）。
- **两条路径汇合点 = `INIClass::Load 0x4741F0`**：其内部 `0x47422B call 0x525A60`（内层 INI 解析器，参数含 FileStraw vft `0x7E4D90`）。差别只在文件名来源（枚举结果 vs 字面量），数据来自磁盘还是 MIX 由 `0x473D10 Get_File` 内部决定，**解析器完全相同**。RULE 额外在 `0x52D0DF`/`0x52D49D` 经 IAT 调 DialogBox 让玩家选一个，并把 `RULESMD.INI` 插到数组第 0 位（已入账 §3，本卡证据 E07 显示 RULE 有额外多次 ctor/Load 与对话框 IAT 调用）。

## 8. 一致性结论

两类字段表 `max(disp+width)` 均恰好等于各自 `new(size)`（CCFileClass `0x6C`、MixFileClass `0x28`），31 个 ctor 写点 0 越界；MIX 索引项 12 字节在分配点与二分查找两处独立印证；哈希算法地址/初值/多项式/表基址全部字节实证并经 Ghidra 独立通道复核。

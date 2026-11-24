# S03-K2 · MIX.md（T2：MIX 头结构 + hash 算法 + 查找链 + 叠加顺序）

> 目标 `ra2youli\gamemd.exe` SHA256 `73201CC0…F67476`，ImageBase 0x400000；全部只读。
> 字节证据：`EVIDENCE\E_T2_hash_mix.txt`、`E_T2_lookup_chain.txt`、`E_T2_findorder_header.txt`、`E_T2_bootstrap_sha1.txt`；复跑 `work\t2_hash_verify.py` 等。

## 1. MIX 头结构（**定出**，`[已证]`）

两种头，靠首 u16 判别：

| 式 | 布局 | 长度 | 实例 |
|---|---|---|---|
| **旧式** | `u16 numFiles` + `u32 bodySize` | 6 B | `theme.mix` num=16 body=76862464，`thememd.mix` num=10 body=46858976 — 两者 `filesize-(6+12n)-body=0` 精确闭合 |
| **新式** | `u16 0` + `u16 flags` + `u16 numFiles` + `u32 bodySize` | 10 B | `langmd.mix` v0=0 flags=1 num=10 body=84643056；`expandmd98.mix` v0=0 flags=0 num=3 body=43315 |

- **索引表**紧随头后，`numFiles × 12 B`，**每项 `{u32 id; u32 offset; u32 size}`**（`0x5B3D81 lea edx,[eax+eax*2]` + `0x5B3D87 shl edx,2` = num*12；`0x5B44DF mov esi,[edi+edx*4]` / `[edx+4]` / `[edx+8]`）。`offset` 相对 datastart，实际读取时加 `[MixFile+0x24]`（`0x5B4553 mov edx,[edx+4]; add edx,[ebp+0x24]`）。
- **无文件名表**（4 证）：loader 只读 6/10 B 头 + 12n 索引；Find 只按 id 二分、从不比字符串；`datastart+bodySize==filesize`（旧式余 0）；真实名由 hash 反推而档内无名字字节。
- **flags.bit0** = 末尾 20 B SHA1 校验：`langmd.mix` flags=1，`sha1(body)=aed02db4…db71` 与尾 20 B **逐字节相等**（`E_T2_bootstrap_sha1.txt`）。
- **flags.bit1** = 加密（见 §4）。索引 id 按**有符号**升序（`0x5B44E5 cmp esi,ebx / jle` 有符号）。
- 二分步长 12 B：`0x5B44DC lea edx,[eax+eax*2]`、`0x5B44EF lea edi,[edx+0xC]`。

## 2. 文件名 → id 的 hash 算法（**定出**，`[已证]`）

函数 `0x4A1DE0`，thiscall(ecx=&state, char* name, int len) `ret 8`。**反射 CRC-32 内核 + len%4 尾部填充**（非 `zlib.crc32(name)`）：

- 表 `0x81F7B4`（256×u32），`u32[1]=0x77073096` ⇒ 反射多项式 **0xEDB88320**；逐字节 `edx=(eax&0xff)^byte; eax>>=8; eax^=table[edx]`（`0x4A1E80–0x4A1E9C`）。
- 状态以补码存放：每个 dword 前后 `not eax`（`0x4A1E79`/`0x4A1E9E`）⇒ 等效 init=`0xFFFFFFFF`、final xor=`0xFFFFFFFF`。
- **关键漏项（K1 审计纠正）**：`len%4=r≠0` 时尾部补成整 dword——`buf[r]=r`，其后 `buf[r+1..3]=buf[0]`（buf 此时持有末 r 字节，`0x4A1F40–0x4A1F63`）。真被哈希的是改写过尾部的字节串。
- 调用前 `strupr 0x7DCFC4`（`0x5B4470`）转大写；调用点清零 state 3 dword（`0x5B4490/94/98`）。

**验证（决定性，本卡独立复算）**：对 `langmd.mix` 官方 10 条目，8 个已知文件名 8/8 命中索引 id，`zlib.crc32` 0/8。表：

| 文件名 | 期望 id | 本模型 | zlib |
|---|---|---|---|
| KEYBOARDMD.INI | 930BE675 | **930BE675** | 1198ABAE |
| RA2MD.CSF | BD835079 | **BD835079** | 42CBEDCB |
| GLSMD.PAL | 366CBDFB | **366CBDFB** | 94193C91 |
| CREDITSMD.TXT | 373A7BC1 | **373A7BC1** | 75D42DA2 |
| AUDIOMD.MIX | FE9DF3BE | **FE9DF3BE** | 4682B8BD |
| CAMEOMD.MIX | 16A802B6 | **16A802B6** | CBA783FA |
| GLSLMD.SHP | B11D7C29 | **B11D7C29** | 9C2154B2 |
| MISSIONSMD.PKT | 480B82E4 | **480B82E4** | B798871B |

> K1 曾称「＝标准 CRC-32」，被其审计 VERDICT §2 推翻（唯一验证用的是第三方 zlib 产物 `expandmd98.mix`）；本卡以官方档 8/8 + 0/8 反证独立确认修正结论。

## 3. 查找链（**每跳地址**，`[已证]`）

```
CCFileClass::Get_File 0x473D10 (slot7)
  ├─ 0x473D1A call [vptr+0x34]          取磁盘状态
  ├─ 0x473D2D call 0x431F10             试开磁盘散装文件 (RawFileClass::Open)
  │     al!=0 → 0x473E39 直接用磁盘文件（散装优先，跳过 MIX）
  └─ 0x473D68 call 0x5B4430             MixFileClass::Find(upper name, out params)
        0x5B4470 call 0x7DCFC4          strupr(大写化)
        0x5B449C call 0x4A1DE0          hash → id (ebx)
        0x5B44A1 mov ebp,[0xABEFE0]     MIX 链表头（全 .text 唯一 xref）
        0x5B44A9..0x5B450B 链表遍历：ebp = [ebp+4]（+4 为 next）
        0x5B44D5..0x5B44FB 对每个 MIX 索引二分（12B 步长，有符号 cmp）
        命中 0x5B4503 → 0x5B450D..0x5B4558 填返回 offset/size/base
        ret 0xC，al=1 命中 / al=0 未命中 (0x5B4580)
```

字段：`[Mix+4]`=next、`[Mix+0x14]`=count、`[Mix+0x20]`=index 指针、`[Mix+0x24]`=datastart base、`[Mix+0x1C]`=备用 base。

## 4. 多 MIX 叠加顺序 / 散装覆盖（`[已证]`）

- **散装文件优先**：`Get_File 0x473D10` 先 `call 0x431F10` 试开磁盘（`0x473D2D`），成功即返回（`0x473E39`），失败才进 `Find`。⇒ **散装文件覆盖 MIX 内容**，与 §3 的 `BATTLEMD*.INI` 走文件系统、不查 MIX 机制一致。
- **MIX 之间**：链表头 `[0xABEFE0]`，`ebp=[ebp+4]` 从头向尾遍历（**FIFO，先注册先查**），第一个命中即返回。17 个 MIX 在本目录只读可见。

## 5. 压缩 / 加密（T4）

- **加密**：新式 flags.bit1 控密钥块。`0x5B3D0E mov [esi+0x11],al` 存 flag；bit1=0 时 `0x5B3D11 je 0x5B3D3F` 明文旁路；命中则 `call 0x633110`/`0x6330C0`（PKStraw 密钥 setup）。RSA 指数 `mov edx,0x10001` @`0x52A6AF`（字节 `BA 01 00 01 00`）；对称加密 `blowfish.dll` 串 @`0x840A78`（动态加载）。级 `[静态推断]`（入口/常量实证，分组逐条未 dump）。
- **压缩**：RTTI `LZOPipe@@`/`LZOStraw@@` @`0x82A00C`，`PKStraw@@` @`0x836874`；串 `"compression buffers"` @`0x82C7FC`、`"Compressed preview image is %d bytes"` @`0x82CC5C`。⇒ **LZO 压缩存在**，`[已证]`（RTTI 名 + 字符串），具体算法条目级 `[未证]`。

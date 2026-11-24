D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R35-V5657A0-TABLE · 0x5657A0 / #73 8 sites

> 纯静态只读；实际镜像与 SHA-256 见首行，期望前缀 `73201CC0` 校验通过。入口锚点 `0x5657A0` / `0x43F180`，线性解码，**未以 C3/C2 字节扫描定入口**。扫读字节：目标函数 56 B；`#73` atlas `0x43F180..0x43FB0B` 共 2443 B；`.text` 原始区 0x3E0000 B 仅作 E8 rel32 目标精确计数（1439），不作入口判定。8 个 site 均由 `0x43F180` 锚点解码验证。

## Q1 · 56 字节函数体

- `ret 4` ⇒ 1 个 4B 栈参；`mov edx,[esp+4]` @0x5657A0 取该参。参为坐标结构指针：`movsx eax,[edx+2]`（Y，int16）、`movsx esi,[edx]`（X，int16）。`ecx` 为调用者传入的 this（见 8 处 `mov ecx,0x87F7E8`）。
- 索引算术：`shl eax,9`（Y*512）+ `add eax,esi`（+X）；`js` 拒负，`cmp eax,0x40000; jge` 拒 >=0x40000。即 512x512、X 低 9 位。
- 表基址：`mov ecx,[ecx+0x13C]` @0x5657BB，随后 `mov eax,[ecx+eax*4]` @0x5657C1。调用者常量 this=`0x87F7E8` ⇒ 表指针槽 = `0x87F7E8+0x13C = 0x87F924`（该槽在 `.data` virtual-only 尾部，RVA `0x47F924`；`.data` raw 仅到 RVA `0x47E000`）。**静态文件没有该运行期指针值，绝对表基址未取得**；表达式为 `T = dword[0x87F924]`。
- 返回内容是表项内容，不是表项地址：字节 `8B 04 81` = `mov eax,[ecx+eax*4]` 已把 4B 值装入 eax；`test eax,eax; jne ret` 表示非 0 直接返回该 dword；0 时走 `mov eax,0xABDC50` 哨兵并写 `[0xABDC74]`。`ret 4` @0x5657D5。

## Q2 · 表本身（只报字节可证）

- 表指针槽：`0x87F924`（`.data` virtual-only/BSS 尾部）；表数组本身不在静态镜像，无法由镜像字节断言其所在节（`.rdata`/`.data` 未取得）。
- 规模：`cmp eax,0x40000` + `eax*4` ⇒ `0x40000 = 262144` 个 4B 项，`0x100000 = 1 MiB`；相对起止 `[T, T+0x100000)`。按“连续读 4B 项遇到非 image 指针/越界即止”的绝对扫描**未执行**：运行时表基址未取得。
- 表项内容：非零 4B 值被作为对象指针使用（8 处 site 中 3 处作 `this` 调函数、3 处读字段、1 处写字段、1 处作栈参）；0 项触发 `0xABDC50` 哨兵。可证实“对象指针样式/哨兵”，**不能由字节证明堆/`new` 分配**。

## Q3 · #73 的 8 处调用

完整逐 site 邻域见 `sites8.tsv`（每处 ±6/8 条，均 <=20）。8 处全部位于 case 1/3 的 A 正常主路径（0x43F1E9 起）；B 短路（0x43F5EF 等）与其它分支命中 0 处。

| site | 路径 | 紧邻前 | 紧邻后 | 返回值去向 |
|---|---|---|---|---|
| 0x0043F210 | A正常/mode1|3入口预检(0x43F1E9->0x43F210) | `push ecx; mov ecx,0x87F7E8` | `push eax; mov ecx,edi; call [esi+0x1AC]` | 栈参给 vslot+0x1AC，非 this |
| 0x0043F2A7 | A正常/mode1|3双层格循环 | `push eax; mov ecx,0x87F7E8` | `mov ecx,eax; call 0x47C620` | this -> 0x47C620 |
| 0x0043F2C5 | A正常/mode1|3双层格循环 | `push ecx; mov ecx,0x87F7E8` | `mov edx,[edi+0x520]; ...; mov edx,[eax+0x38]; cmp ...` | 读 +0x38 比较 |
| 0x0043F2EF | A正常/mode1|3双层格循环 | `push eax; mov ecx,0x87F7E8` | `cmp dword ptr [eax+0xec],1` | 读 +0xEC 比较 |
| 0x0043F30B | A正常/mode1|3双层格循环 | `push ecx; mov ecx,0x87F7E8` | `mov ecx,[eax+0x48]; cmp ecx,-1` | 读 +0x48 比较 |
| 0x0043F39C | A正常/mode1|3双层格循环(overlay/invalidate内) | `lea eax,[esp+0x58]; mov ecx,0x87F7E8` | `mov dword ptr [eax+0x48],-1` | 写 +0x48 = -1 |
| 0x0043F3BF | A正常/mode1|3双层格循环(overlay/invalidate内) | `push eax; mov ecx,0x87F7E8` | `mov ecx,eax; call 0x4852D0` | this -> 0x4852D0 |
| 0x0043F587 | A正常/mode1|3边界补扫(0x43F526后) | `push edx; mov ecx,0x87F7E8` | `mov ecx,eax; call 0x486E70` | this -> 0x486E70 |

**是否都像 #107（`mov ecx,eax; call ...`）？否。** 分类：`this` 3 处（0x43F2A7/0x43F3BF/0x43F587）；栈参 1 处（0x43F210）；字段读/比较 3 处（0x43F2C5/0x43F2EF/0x43F30B）；字段写 1 处（0x43F39C）。

## Q4 · 对 0x43F180 语义的帮助（候选，均非事实）

1. `[静态推断｜强度:中]` 候选：`0x5657A0` 可解释为 `0x43F180` mode1/3 主循环的“坐标->CellClass 样式对象”取指针工具；8 个 site 全在 A 主路径、且输入均为 `CellStruct*` 形态的 2xint16。它可能把放置判定 switch 与 512x512 格坐标遍历连接起来。依据：index 算术 + 8 site 路径分布；局限：未证明 `0x43F180` 的全部语义。
2. `[静态推断｜强度:中]` 候选：`0x43F2A7` 把返回的格对象作为 `this` 送入 `0x47C620`，可能说明 `0x5657A0` 是到达已定位的类型无关占用闸的“取格”前级。依据：`mov ecx,eax; call 0x47C620` 字节；局限：不证明该闸在真机具体格上触发，不改变可达性未知。

**收口不变：** 以上候选不改变 ②-b 的 `[静态推断]` 收口（§2.9 + §2.10 的 (a′)）；不得升级为 `[已证]`。

## 复跑

```bash
python lead/next_re_20261117_r14/R17_R35_V5657A0_TABLE/work.py
```

依赖：pefile / capstone。产物均为 LF，无 CR。

## 附：目标函数 56B 逐指令
```
005657A0  8b 54 24 04              mov edx, dword ptr [esp + 4]
005657A4  56                       push esi
005657A5  0f bf 42 02              movsx eax, word ptr [edx + 2]
005657A9  0f bf 32                 movsx esi, word ptr [edx]
005657AC  c1 e0 09                 shl eax, 9
005657AF  03 c6                    add eax, esi
005657B1  5e                       pop esi
005657B2  78 14                    js 0x5657c8
005657B4  3d 00 00 04 00           cmp eax, 0x40000
005657B9  7d 0d                    jge 0x5657c8
005657BB  8b 89 3c 01 00 00        mov ecx, dword ptr [ecx + 0x13c]
005657C1  8b 04 81                 mov eax, dword ptr [ecx + eax*4]
005657C4  85 c0                    test eax, eax
005657C6  75 0d                    jne 0x5657d5
005657C8  8b 12                    mov edx, dword ptr [edx]
005657CA  b8 50 dc ab 00           mov eax, 0xabdc50
005657CF  89 15 74 dc ab 00        mov dword ptr [0xabdc74], edx
005657D5  c2 04 00                 ret 4
```
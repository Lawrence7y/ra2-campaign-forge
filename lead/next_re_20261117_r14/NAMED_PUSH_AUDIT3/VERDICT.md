# NAMED_PUSH 第三批（单行）异族审计 — VERDICT

审计员：异族独立审计员（非 Hy4、非 DeepSeek）。本文件全部结论由我本人反汇编 `gamemd.exe` 得出；
执行器 `NAMED_PUSH_S05_B3\*`（`delta.tsv` / `REPORT.md` / `EVIDENCE\ROW_00748190.txt` / `work\*`）**只当线索**，未作任何证据引用。

- 目标：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` = 卡面期望 ✔
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)` ✔；capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26 + Python 3.12.10
- 我的工具：`work\core.py`（PE 映射 / 反汇编器 / 字节扫描）、`work\d1..db.py`（各行取证脚本，可复算）

---

## 行 1 · `00748190` — UnitTypeClass::slot8 — **PASS**

### ① 入口与边界（自证）

函数头前是填充 `90`（`0074818F 90`），`00748190` 是函数起点；末条 `0074821A C2 04 00`（`ret 4`）落于 `.text` 内，
函数体 `[0x748190, 0x74821D)` = **141 字节 / 42 条指令**，`skipdata` 命中 0 次。与执行器报的 141B/42 条一致。

```
00748190  51                 push    ecx
00748191  56                 push    esi
00748192  8BF1               mov     esi, ecx
00748194  B201               mov     dl, 1
00748196  C70618627F00       mov     dword ptr [esi], 0x7f6218      ; 本类主表
0074819C  C74604FC617F00     mov     dword ptr [esi+4], 0x7f61fc
007481A3  C74608F4617F00     mov     dword ptr [esi+8], 0x7f61f4
007481AA  C7460CEC617F00     mov     dword ptr [esi+0xc], 0x7f61ec
007481B1  E81AD7FDFF         call    0x7258d0                       ; 解除全局单例引用
007481B6  8B15E03CA800       mov     edx, dword ptr [0xa83ce0]      ; 全局 DynamicVectorClass<UnitTypeClass*>.vft
007481BC  8D442404           lea     eax, [esp+4]
007481C0  50                 push    eax
007481C1  B9E03CA800         mov     ecx, 0xa83ce0
007481C6  89742408           mov     dword ptr [esp+8], esi         ; 参数 = this
007481CA  FF5210             call    dword ptr [edx+0x10]           ; ← Find(this)
007481CD  83F8FF             cmp     eax, -1                        ; ← 伪证点
007481D0  742D               je      0x7481ff                       ; 未找到 → 跳过摘链
007481D2  8B0DF03CA800       mov     ecx, dword ptr [0xa83cf0]      ; Count
007481D8  3BC1               cmp     eax, ecx
007481DA  7D23               jge     0x7481ff
007481DC  49                 dec     ecx
007481DD  3BC1               cmp     eax, ecx
007481DF  890DF03CA800       mov     dword ptr [0xa83cf0], ecx      ; 非栈写(全局 Count)
007481E5  7D18               jge     0x7481ff
007481E7  8B0DE43CA800       mov     ecx, dword ptr [0xa83ce4]      ; 数组基址
007481ED  40                 inc     eax
007481EE  8B1481             mov     edx, dword ptr [ecx+eax*4]
007481F1  895481FC           mov     dword ptr [ecx+eax*4-4], edx   ; 非栈写(数组前移)
007481F5  8B0DF03CA800       mov     ecx, dword ptr [0xa83cf0]
007481FB  3BC1               cmp     eax, ecx
007481FD  7CE8               jl      0x7481e7                       ; 回边
007481FF  8BCE               mov     ecx, esi
00748201  E8DA98FCFF         call    0x711ae0                       ; 基类析构
00748206  F644240C01         test    byte ptr [esp+0xc], 1          ; delete 标志
0074820B  7409               je      0x748216
0074820D  56                 push    esi
0074820E  E82A090800         call    0x7c8b3d                       ; operator delete
00748213  83C404             add     esp, 4
00748216  8BC6               mov     eax, esi
00748218  5E                 pop     esi
00748219  59                 pop     ecx
0074821A  C20400             ret     4
```

补证（我实测，非执行器材料）：`0x711AE0` 是真基类析构（`00711AED C706D84E7F00` 装基类 4 张表、`00711B17 call 0x7C8B3D` 释放子缓冲），
`0x7C8B3D` = `operator delete`（`007C8B3D FF742404 / E8A2080000 call 0x7C93E8 / 59 C3`），
`0x7258D0` 体内 `007258DB FF 50 2C` 后按 `[0x88098C]==this` 清全局单例指针 ⇒ 本函数是**标量删除析构**（scalar deleting destructor）。

---

### ② 类身份独立成立 — **PASS**

`slotN` 里的 `UnitTypeClass` 只当线索，我用 RTTI 数据链独立钉死（`work\d4.py`）：

| 环节 | 地址 | 实测字节 / 值 |
|---|---|---|
| 虚表 | `007F6218` | 构造器 `007471BF C70618627F00` 写入 `[esi]`（主表） |
| vt 前 4 字节 = COL | `007F6214` → `0080CD28` | `.rdata` |
| COL 签名 | `0080CD28` | `00 00 00 00`（sig=0，是 RTTI Complete Object Locator） |
| COL→TD（+0xC） | `0080CD28+0xC` → `00845980` | `80 59 84 00` |
| TD 名串（内联于 TD+8） | `00845988` | `2E 3F 41 56 55 6E 69 74 54 79 70 65 43 6C 61 73 73 40 40 00` = **`.?AVUnitTypeClass@@`** |
| 槽 8（vt+0x20） | `007F6238` | = **`00748190`** |

- 槽偏移 `0x20/4 = 8`，与名字线索 `slot8` 自洽；类名与 `UnitTypeClass::slot8` 逐字一致。
- 全 `.rdata`/`.data` 扫描 `90 81 74 00`：**唯一一处**在 `007F6238` ⇒ 入口只驻留这一个虚表槽，不存在同名多表歧义。

### ③b 具体形态 — **③b②（可伪证返回约定）成立**

- 被调方：容器活虚表 `007EA2A4`（`[0xA83CE0]`）的 `+0x10` 槽 = **`004EDF50` = Find**：

```
004EDF50  8B5110             mov     edx, dword ptr [ecx+0x10]      ; Count
004EDF53  33C0               xor     eax, eax
004EDF55  56                 push    esi
004EDF56  85D2               test    edx, edx
004EDF58  7E15               jle     0x4edf6f
004EDF5A  8B742408           mov     esi, dword ptr [esp+8]          ; &this
004EDF5E  8B4904             mov     ecx, dword ptr [ecx+4]          ; 数组
004EDF61  8B36               mov     esi, dword ptr [esi]
004EDF63  3931               cmp     dword ptr [ecx], esi
004EDF65  740B               je      0x4edf72
004EDF67  40                 inc     eax
004EDF68  83C104             add     ecx, 4
004EDF6B  3BC2               cmp     eax, edx
004EDF6D  7CF4               jl      0x4edf63
004EDF6F  83C8FF             or      eax, -1                        ; ← 未命中哨兵 -1
004EDF72  5E                 pop     esi
004EDF73  C20400             ret     4
```

- **失败返回**：`eax = -1`（`004EDF6F 83 C8 FF`）；**成功返回**：元素下标（`004EDF72` 前 `eax` 保持为命中下标）。
- **调用方哪条指令拿它分支**：`007481CA FF 52 10` 调用 → 紧接 `007481CD 83 F8 FF`（`cmp eax,-1`）→ `007481D0 74 2D`（`je 0x7481FF`），**零间隔、无 eax 覆写**。
- **两路真不同**：命中路做全局 `Count` 写（`007481DF`）+ 数组前移循环（`007481F1 89 54 81 FC`，回边 `007481FD jl`）；未命中路直接落到 `007481FF` 只做基类析构 + 条件释放。
- 循环内非栈写 `007481F1` **在本函数体内**（不是"被调用者内部的写"）✔；非 ③a 直线/纯转发/空判断形态 ✔。
- 容器自身的 ㉓ 成对陷阱已排除：活表 `007EA2A4` 由**构造器** `004E7460` 于 `004E747D` 写入；死表 `007EA2C4` 由它 `004E7496` 注册（`push 0x4E74A0` + `call 0x7C978A`）的 atexit 析构 `004E74A0` 于 `004E74A8` 写入。本行取的是**活表**，未踩。

### ④ 使用见证独立成立 — **PASS（我自己取的证，比执行器的锚更硬）**

执行器给的 3 个锚中 `00748196` **在本行体内**（即析构器自装表），`0074803D` 在本类**槽 5 方法** `00748010` 内 —— 都不干净（详见"需账"）。
我不依赖它们，改以自己的实派发点立证：

```
; IClassFactory::CreateInstance 形态（ret 0x10，三类 HRESULT 分支）
006C2810  56                 push    esi
006C2811  57                 push    edi
006C2812  8B7C2418           mov     edi, dword ptr [esp+0x18]      ; ppvOut
006C2816  85FF               test    edi, edi
006C2818  750A               jne     0x6c2824
006C281A  ...                mov     eax, 0x80070057                ; E_INVALIDARG
006C2830  740A               je      0x6c283c                       ; pUnkOuter!=0 → 0x80040110
006C283C  68780E0000         push    0xe78                          ; sizeof(UnitTypeClass)
006C2841  E8D1651000         call    0x7c8e17                       ; operator new
006C284B  740F               je      0x6c285c                       ; → 0x8007000E (OOM)
006C284D  6A00               push    0
006C284F  8BC8               mov     ecx, eax                       ; this = 新对象
006C2851  E87A480800         call    0x7470d0                       ; ← 真构造器(装表点在宿主内 007471BF)
006C2856  8BF0               mov     esi, eax
006C286A  8B06               mov     eax, dword ptr [esi]           ; 取活虚表(应=007F6218)
006C286F  FF10               call    dword ptr [eax]                ; 槽 0
006C2871  8BF8               mov     edi, eax
006C2873  85FF               test    edi, edi
006C2875  7D09               jge     0x6c2880
006C2877  8B16               mov     edx, dword ptr [esi]           ; 再取活虚表
006C2879  6A01               push    1                              ; delete 标志 = 1
006C287B  8BCE               mov     ecx, esi
006C287D  FF5220             call    dword ptr [edx+0x20]           ; ← 槽 8 活派发 = 本 entry
006C2880  8BC7               mov     eax, edi
006C2884  C21000             ret     0x10
```

- 构造器宿主 `007470D0`：`007470DE E80D9AFCFF call 0x710AF0`（基类构造，`0x710AFB` 再 `call 0x5F7090`）→ 逐字段初始化 → `007471BF C70618627F00` 装 `007F6218` → `0074721C FF5208` 调容器 `+8` 扩容 → `0074722B/00747235` 把 `this` **追加进全局容器** `[0xA83CE0]`。无 free、无 delete 标志、非 atexit ⇒ **真构造器**。
- `006C287D FF 52 20` 是**活虚表派发点**，且 `006C286A` 刚读过同一对象的 `[esi]` 虚表；`push 1` 与入口 `ret 4` + `test byte [esp+0xC],1` 的契约逐字吻合（caller 传 delete 标志=1 ⇒ 走 `0074820B` 分支释放）。
- 另有工厂侧 `0074813A E891EFFFFF call 0x7470D0`（同一构造器，分配 `push 0xE78` 后），并在 `00748149 8B04B2 mov eax,[0xA83CE4+esi*4]` 直接读本类容器数组。
- 可达性实测（`work\dc.py`）：全 `.text` 内 `E8`（call rel32）、`E9`（jmp rel32）、`0F 84`（jz rel32）目标为本 entry 各 **0 处**；
  `90 81 74 00` 在 `.text` 内也 **0 处** ⇒ 本 entry **无任何直接调用者**，只能经唯一虚表槽 `007F6238` 到达。
  故 ④ 不可能靠 direct call 立证，必须落到活派发点 `006C287D`——本条已满足（非 direct-only）。
- 旁证（不单独当证据）：容器活表 RTTI = `.?AV?$DynamicVectorClass@PAVUnitTypeClass@@@@`（`007EA2A4-4` → COL `00801D30` → TD `00823A10`），容器元素类型就是 `UnitTypeClass*`。

### ④ 与 ② 不同源 — **不同源（no）**

- ② 链：`.rdata` 只读数据（`007F6214` → `0080CD28` → `00845980` → 名串）＋ `.rdata` 槽 `007F6238` 的驻留值。
- ④ 链：`.text` 代码路径（`006C283C..006C2851` 分配+构造 → `006C287D FF 52 20` 活派发）。
- 二者不共用"同一虚表槽既证身份又证使用"：身份来自 RTTI 描述符（数据），使用来自工厂函数的运行期派发（代码），锚点地址互不相交。

### ⑤ 语义与实测相符 — **相符**

逐项对 `delta.tsv` 第 4 列：

| 第 4 列说法 | 实测 | 结论 |
|---|---|---|
| `call [edx+0x10]` 返回 this 在全局对象列表中的索引 | `007481CA FF 52 10`，被调 `004EDF50` 逐元素比较返回下标 | ✔ |
| `-1`（未找到哨兵）则 `je` 路跳过摘链仅收尾释放 | `004EDF6F 83 C8 FF` → `007481CD 83 F8 FF` → `007481D0 74 2D je 0x7481FF` | ✔ |
| 否则边界检查 | `007481D8 3BC1 / 007481DA 7D23 / 007481DC 49 / 007481DD 3BC1 / 007481E5 7D18` | ✔ |
| `mov [0xA83CF0],ecx` 非栈写 | `007481DF 890DF03CA800` | ✔ |
| 数组前移循环 `mov [ecx+eax*4-4],edx` 非栈写 | `007481F1 895481FC`，回边 `007481FD 7CE8 jl` | ✔ |
| 两路真不同、无 eax 覆写 | 命中/未命中动作不同；`007481CA`→`007481CD` 之间无指令 | ✔ |
| 读写方向 | 写向（摘链/计数/数组前移），与语义"移除"方向一致，**未反向** | ✔ |

---

### 裁定

**PASS**（②③b④⑤ 全部独立成立，④ 与 ② 不同源）

### 需账（不单独构成 FAIL，但必须进台账备注）

| # | 问题 | 实测 |
|---|---|---|
| 1 | 执行器 ④ 锚 `00748196` **在本行体内** | 它就是本函数 `00748196 C70618627F00` 的"析构自装 4 表"，不是构造点；把它当 ④ 证据属"写点在行外"违规 + ㉓ 析构锚。本行 ④ 不依赖它（我已另立 `006C287D`）。 |
| 2 | 执行器 ④ 锚 `0074803D` 不在构造器里 | 宿主 `00748010` 是本类**槽 5 方法**（`00748024 call 0x7162F0`、`00748038 call 0x711840` 基类构造后装表、`007480A7 C20800 ret 8`），是"读入/装载时重建对象"的路径；可算安装点，但不是构造器。 |
| 3 | 执行器漏了干净的构造点 | `007472C0`（`007472C8 call 0x711840` 基类构造 → `007472CD C70618627F00` 装表 → `007472EB C20400 ret 4`），但该函数**0 个直接调用者**（与 `007472F0` 死副本同理），故不作为主证。 |
| 4 | 第 4 列漏写 `007481B1 call 0x7258D0` | 体内 `007258DB FF 50 2C` 后按 `[0x88098C]==this` 清全局单例指针 ⇒ "解除全局单例引用"未写；与上一批 `00691EE0`/`00691FA0`/`006E87F0` 同一类漏项。 |
| 5 | 第 4 列未标注该行是**标量删除析构** | 体内有 4 表复位 + `test byte[esp+0xC],1` + `call 0x7C8B3D` + `ret 4`；语义只写"收尾释放"，未点明形态。 |
| 6 | 报告"358 处 `[reg+0x20]` 派发"是泛型计数 | 我复算 `FF 5x 20` 确为 358 处，但全二进制通用、不绑定本类；真正绑定的 ④ 派发点是 `006C287D`（对象由本类构造器 `007470D0` 产出）。 |

### 天花板（供 Lead 判读，不改结论）

本行 ③b② 的判别内容是"从全局 `DynamicVectorClass<UnitTypeClass*>` 自摘链"，与上一批 4 个 S14 析构行同型：
**它是模板级、低信息量的 ③b②**，不得据此单独扩域。若 Lead 要把 ③b② 收紧成"只认本函数自身返回约定"，
本行应按上一批已写明的口径改标 **③b④**（体内压缩循环 `007481F1` 非栈写 + `007481D8` 边界 + `007481FD` 回边），结论仍是 `[已证]` 可达，只是形态标签要换——**该收紧须先成文并同步处理既有同型 `[已证]` 行**。

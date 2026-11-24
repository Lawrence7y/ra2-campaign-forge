# W105 WRITE_SITES —— `CellClass+0xE4/0xE8` 链头读写点清单（修正 W99）

编制：W105 ｜ 2026-11-14 ｜ 产出命令（本文所有数字的唯一来源，可复现）：

```
C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe census.py
# -> EVIDENCE\census.txt (UTF-8, 全量 A/B/C 明细 + 上下文 + 补充 +0x30 扫描)
```

---

## 0 · 结论速览

| 问题 | 答案 | 分级 |
|---|---|---|
| A 类（写 `[base+0xE4/0xE8]`，base 非 esp/ebp） | **114 条**（SIB=2 / modrm-disp32=112），全部边界 HIGH | `[已证]` |
| 其中被"装虚表"判据剔除（他类构造） | **19 条**（A-excluded） | `[已证]` |
| **真候选（可能为 cell 链头写）** | **95 条** | `[已证]` |
| 条件摘链（仅当 `链头==this` 才改写） | **≥4 条**形态确认（0x436A2D / 0x62FEFE / 0x678874 / 0x6F105D），另有完整摘链函数 `0x47EA90` | `[已证]` |
| 条件置空（cmp 同字段守卫的置零） | **0 条**（8 条置零全部指令级无条件） | `[已证]` |
| **有没有"无条件把链头整体替换成 next"** | **没有**。唯一形似的 `0x47EAC4/0x47EACF`（`head←[this+0x30]`）在 `0x47EAB9: cmp eax,esi; jne` 守卫之后 —— 只在 `head==this` 时执行 | `[已证]` |
| UAF 假设（摧毁后未摘链） | **无法判定（静态）**：既不能支持（完整摘链机制存在，见 §3.1），也不能推翻（无法证明每条摧毁路径都走到它） | `[已证·负结果]` |

---

## 1 · 方法（对 W99 两个缺陷的修正）

1. **按指令边界解码，不在字节流里搜模式**：线性扫描 `.text`（0x401000 起，4,063,232 B），
   capstone 逐条解码；无效编码逐字节跳过并记 gap（不静默）。共解码 **1,394,120** 条指令，
   gap **64 段 / 66 字节**（全部 ≤2 B 的孤立点，无一落在任何命中邻域）。
   产出：census.txt `== 扫描统计 ==`。
2. **SIB 与 modrm-disp32 两种编码全覆盖**：在解码后的操作数上匹配 `disp∈{0xE4,0xE8}`，
   并手工解 modrm 位标注形式（SIB=2 条 / 非 SIB=112 条，A 类）。
   `disp8` 形式（0xE4→-0x1C，负偏移）语义上不是 +0xE4，天然不入册。
3. **esp/ebp 基址显式排除并计数（W99 假阳性主体）**：C 类 = **写 76 + 读 153 = 229 条**，
   另 base 空（绝对地址）0 条。例：`0x46780B` 类 `[esp+0xE4]` 全部落此。
4. **函数边界**：ret/retf + 0x90/0xCC 填充切段，共 **31,077** 锚。
   命中向上取最近锚；若 `[锚, 命中)` 内有 gap 则标"边界未定"。
   **A 类 114 条全部 HIGH（无边界未定）**。产出：census.txt `== 汇总 ==`。
   注：锚取 nop 游程首字节，故锚点可比真入口早几字节
   （如 `0x47C520→func 0x47C519`、`0x47C4D0→func 0x47C4CA`、`0x47EA90→func 0x47EA89`）。
5. **Lead 补丁判据**：① ±20 条内出现 `mov dword [同base+0], imm32∈[0x7E1000,0x812000]`
   （Lead L2 的 .rdata 游程范围）⇒ 该写点判 **A-excluded（他类构造/初始化）**；
   ② 前 2 条内 `cmp [同base+同disp]` ⇒ 条件写；③ 前 3 条内 `mov <src>,[x+0x30]` ⇒ 链头←next 形态。
6. **自检 3/3 PASS**（census.txt `== 自检 ==`）：
   `0x47C52A: mov esi,[ecx+0xE4]`（8b b1 e4 00 00 00）、`0x47C4E3: mov esi,[ecx+0xE8]`、
   `0x47C538: call [eax+0x2C]`（ff 50 2c）均按预期解码并落入 B 类清单（census.txt:753,755）。

**汇总**（census.txt `== 汇总 ==`）：解码 1,394,120 ｜ A=114（SIB 2 / 非 SIB 112）｜
B=442（SIB 1 / 非 SIB 441）｜ C：写 76 / 读 153 / 绝对地址 0 ｜ 函数锚 31,077 ｜ gap 64/66B。

---

## 2 · A 类判读分布（114 条 = 95 真候选 + 19 A-excluded）

| 判读 | 条数 | 说明 |
|---|---:|---|
| link候选（寄存器写入，未见 cmp 同字段守卫） | 64 | 多数语境是构造/赋值/状态字段，见 §5 撞车警告 |
| **A-excluded（他类构造，装虚表判据）** | **19** | 全清单 census.txt `== A-excluded 节 ==` |
| 其它（立即数/浮点/查表/RMW/内存拷贝） | 17 | 含 `0x62F1E9: mov [ebx+0xE4],0x40000000`（位标志）、`0x721A44` 族写 12（小整数，非指针） |
| **置空（指令级无条件）** | **8** | 见 §3.2 |
| **条件写（cmp[同字段]守卫）** | **4** | 见 §3.3 —— Lead 假设的核心形态 |
| unlink-head候选（`head←[this+0x30]`） | 2 | 见 §3.1 —— **人工复核后修正：有守卫** |

---

## 3 · 关键写点逐条（真候选中直接关系链语义的）

### 3.1 完整摘链函数 `0x47EA90`（真入口；census.txt 锚记 0x47EA89）—— 本卡最重要发现

直接反汇编核验（命令：§6 复核命令 ②）：

```
0x47EA94  mov esi,[esp+0x14]      ; 参数: 被摘对象 this
0x47EA99  mov edi, ecx            ; ecx = cell
0x47EAAB  mov eax,[edi+0xE8]      ; 链B 头（cl 参数选链）
0x47EAB3  mov eax,[edi+0xE4]      ; 链A 头
0x47EAB9  cmp  eax, esi           ; *** head == this ? ***
0x47EABB  jne  0x47EAD7           ; 不是头 → 走链中遍历
0x47EAC1  mov  eax,[esi+0x30]     ; next = this->next
0x47EAC4  mov  [edi+0xE8],eax     ; 链B: head = next      (A 类命中)
0x47EACC  mov  ecx,[esi+0x30]
0x47EACF  mov  [edi+0xE4],ecx     ; 链A: head = next      (A 类命中)
0x47EAD7  test eax,eax; je 0x47EAF7
0x47EADB  mov  ecx,[eax+0x30]     ; 遍历: cur->next
0x47EADE  cmp  ecx, esi           ; cur->next == this ?
0x47EAE0  je   0x47EAEA
0x47EAE2  mov  eax,ecx; test eax,eax; jne 0x47EADB
0x47EAEA  mov  edx,[esi+0x30]
0x47EAED  mov  [eax+0x30],edx     ; prev->next = this->next   (+0x30 写)
0x47EAF0  mov  [esi+0x30],0       ; this->next = 0            (+0x30 写)
0x47EAF7  mov  eax,[esi]; call [eax+0x2C]   ; WhatAmI()
0x47EAFE  cmp  eax,0xF; je 0x47EB8F         ; 类ID 0xF=15 特判（与 Lead L2 的 ID15 呼应）
```

判读 `[已证]`：**头摘（head==this 才执行）+ 链中摘（遍历找 prev）双路齐全，摘完清 `this->next`**。
⇒ "引擎从不摘链"这一极端形态被静态证据**否定**；UAF 只可能来自"摧毁路径没有调用它"（§5）。

### 3.2 置空 8 条（全部指令级无条件；条件置空 = 0 条）

| 地址 | 指令 | func | 语境判读 |
|---|---|---|---|
| `0x468AE5` | `mov [ebx+0xE8],0` | 0x468668 | 前 `test ah,0x40; je`（分支保护），`[ebx+0xEC]`同支写 float 3.5 ⇒ 疑非 cell 对象 `[静态推断]` |
| `0x48EE2A` | `mov [esi+0xE4],eax`(xor置零) | 0x48EBE1 | 后随 `push 8; call` ⇒ 疑构造/重置 `[静态推断]` |
| `0x48EE51` | `mov [esi+0xE8],eax`(xor置零) | 0x48EBE1 | 同上 |
| `0x48FC00` | `mov [esi+0xE4],eax`(xor置零) | 0x48F054 | 同上 |
| `0x48FC27` | `mov [esi+0xE8],eax`(xor置零) | 0x48F054 | 同上 |
| `0x619F22` | `mov [ecx+0xE8],edx`(xor置零) | 0x619230 | 连续清 +0xE8/+0xEC/+0xF0 ⇒ 批量清场 `[静态推断]` |
| `0x61ABB0` | `mov [esi+0xE8],ebp`(xor置零) | 0x61AB69 | 大函数（栈帧 0x2D48）内，语境未定 |
| `0x62CE1C` | `mov [esi+0xE4],0` | 0x62CE1C | 独立小函数首指令，随后 `[esi+0x131]=1`（bool 标志）⇒ 对象身份 `[未证]` |

### 3.3 条件写 4 条（`cmp [同字段],X; jne; store` —— "仅当字段==X 才改"）

| 地址 | 指令 | 守卫 | 判读 |
|---|---|---|---|
| `0x436A2D` | `mov [esi+0xE4],eax` | `0x436A25: cmp [esi+0xE4],edi; jne` | 若字段!=edi 则跳过 —— "头==this 才摘"的**单字段缩水版** `[已证]` |
| `0x62FEFE` | `mov [edi+0xE4],eax` | `0x62FEF6: cmp ebx,[edi+0xE4]; jne` | 同形态，紧接对 +0xE0 同样处理 |
| `0x678874` | `mov [esi+0xE8],eax` | `0x67886C: cmp edi,[esi+0xE8]; jne` | 同形态 |
| `0x6F105D` | `mov [ecx+0xE4],edx` | `0x6F1055: cmp [ecx+0xE4],eax; jne` | 同形态 |

这 4 条**与 Lead 的 UAF 失败模式一致**：若"被删对象==字段"比较用的是不同值/不同支路，
该字段就不会被清。但它们是否挂在摧毁路径上，静态单点普查**判定不了**（§5）。

### 3.4 链族邻域（func∈[0x47B000,0x480000)）真候选 7 条 —— 与 Lead L1 的链遍历器同域

| 地址 | 指令 | func | 判读 |
|---|---|---|---|
| `0x47BBA7` | `mov [esi+0xE4],ebx` | 0x47BB5B | 批量清场（0xFC/0xE4 连写同值），疑 unlink/清 cell `[静态推断]` |
| `0x47BC82` | `mov [esi+0xE4],ebx` | 0x47BBE9 | 同上（0xDC..0xEC 连写） |
| `0x47BC88` | `mov [esi+0xE8],ebx` | 0x47BBE9 | 同上；func 内还有 `0x47BC0B: mov [esi+0x30],ebx` |
| `0x47E90B` | `mov [ebx+0xE8],ebp` | 0x47E892 | 前一条 `0x47E908: mov [ebp+0x30],esi` ⇒ **头插形态（link）** `[静态推断]` |
| `0x47E91F` | `mov [ebx+0xE4],ebp` | 0x47E892 | 同上（链A 支） |
| `0x47EAC4` | `mov [edi+0xE8],eax` | 0x47EA90 | **条件摘头**（§3.1，head==this 才执行）`[已证]` |
| `0x47EACF` | `mov [edi+0xE4],ecx` | 0x47EA90 | 同上 |

### 3.5 0x41F86F 特别标注（Lead 要求）

`0x41F86F: mov byte ptr [edi+ebp+0xE4], al` —— **`ebp` 是变址（[edi+ebp*1+0xE4]），
base=edi**；byte 宽度；同 func 0x41F575 内 B 类有 `mov dl,[esi+edi+0xE4]`（byte 数组读）。
该条**按口径入 A 但可能根本不是对象字段而是字节数组元素**，勿当链头写。

---

## 4 · B 类（读，442 条）与 C 类（W99 假阳性，229 条）

- **B=442**（全量 census.txt `== B 类明细 ==`）。函数聚类（≥6 条）：0x4361C9×6、
  0x468668×7、0x62CB10×7、0x62ED3D×7。**语义混入警告**：其中 `call [reg+0xE4/0xE8]`
  （0x415DE8、0x41BD40、0x54CD44×2、0x5F578D 等 ≥5 条）是 **vtable 槽调用**（槽偏移撞车），
  不是 cell 字段读；`lea`（≥7 条）是取址非读。按字段读口径引用 B 时需先滤这两类。
- **C=229（写 76 + 读 153）**：全部 `[esp/ebp+0xE4/0xE8]` 栈访问 —— **这就是 W99 清单的主体
  假阳性形态**。census.txt `== C 类 ==` 给前 20 条示例。
- 补充（服务 UAF 判定）：写 `[base+0x30]`（dword，base 非 esp/ebp）全 `.text` **286 条**；
  链族邻域 4 条：`0x47BC0B`、`0x47E8EB`、`0x47EAED`、`0x47EAF0`（后两条即 §3.1 的摘链对）。

---

## 5 · 核心问答（Lead 指定必答）

**Q：A 类里有没有"无条件把该格链头整体替换成 next"（不比较 this，直接 `head←[this+0x30]`）？**

**A：没有。** 全 A 类只有两条指令在形态上等于 `head←[this+0x30]`（`0x47EAC4`/`0x47EACF`），
但二者都在 `0x47EAB9: cmp eax,esi; jne 0x47EAD7` 之后 —— **只有 `链头==this` 才执行**；
链中间位置由 `0x47EADB..0x47EAF0` 的遍历摘除处理（`prev->next=this->next; this->next=0`）。
"链头←next"形态不带 head==this 守卫的写法在本镜像 A 类中**零条** `[已证]`。

**Q：UAF 假设（摧毁后未摘链）静态能否支持/推翻？**

**A：无法判定（静态）。** 三条理由：
1. **不能支持**：完整摘链机制存在（§3.1），置空 8 条 + 条件写 4 条也在；静态单点普查
   无法证明"某次摧毁不走其中任何一条"——那是调用图/数据流问题，超出本卡口径。
2. **不能推翻**：条件写形态（§3.3）恰恰是"比较值不匹配就漏清"的载体；
   且 95 条真候选里**没有一条能静态证明 base 是 CellClass**（+0xE4 在别的类上是普通字段，
   A-excluded 19 条即为实证；0x74CE4C 写 0xFFFFFFFF、0x721A44 写 12、0x62F1E9 写
   0x40000000、0x60Dxxx 写规则全局指针，均为同偏移异语义撞车）。
3. **可检验判据（交给 W100 真机观测器）**：若捕获"链头（或链中 prev）指向 vptr 已坏的节点"
   且该节点 `next` 仍非 0 ⇒ 支持"漏摘"；若每次摧毁后链头与全链均无悬空指针 ⇒ 推翻。

---

## 6 · 复核命令

① 全量清单：`python census.py`（本卡目录内执行，写 EVIDENCE\census.txt）。
② §3.1 函数反汇编（独立于 census.py，本轮实测通过）：
```python
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
pe = pefile.PE(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", fast_load=True)
sec = [s for s in pe.sections if s.Name.rstrip(b"\0") == b".text"][0]
data, va0 = sec.get_data(), 0x400000 + sec.VirtualAddress
lo, hi = 0x47EA89, 0x47EB10
for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(data[lo-va0:lo-va0+(hi-lo)], lo):
    print("0x%08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
```
③ 自检三条：census.txt `== 自检 ==`（0x47C52A / 0x47C4E3 / 0x47C538 全 PASS）。

## 7 · 局限（详见 UNKNOWNS.md）

装虚表判据窗口 ±20 条，窗口外的构造性语境（如 0x48EE2A 所在大函数）可能漏剔；
`xchg` 未计写方向；`movs/stos` 隐式内存不在操作数文本中，天然不入册；
函数锚可比真入口早一个 nop 游程（§1.4）；A 类 base 的"是否 CellClass"静态不可证。

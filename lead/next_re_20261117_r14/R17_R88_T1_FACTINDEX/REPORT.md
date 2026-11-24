# R88-T1 独立复算报告（executor / hy4）

目标目录：lead/next_re_20261117_r14/R17_R88_T1_FACTINDEX/
所有数字由本次自写脚本在 t628 本机实跑得到，未 import 调度方的任何脚本。
脚本放在 /tmp/r88t1_check_ab.py、/tmp/r88t1_check_c.py、/tmp/r88t1_check_d.py（产物目录之外，未复制 live 树）。

---

## 命题 A（可核验率）：成立

数据：FACT_INDEX.tsv 表头 `fact_id  statement  grade  evidence_paths  limitations`，数据行 54。
拆分规则：evidence_paths 按 `;` 切；锚点从**第一个 `(`** 起截断（路径本身不含 `(`；锚点可嵌套，如 `R14_COMMON.md(§2.10 / 一 / (a′))`）；`\` 转 `/`；用 os.path.isfile 判断（相对项目根）。

| 项 | 我算出的值 | 卡面预期 | 结论 |
|---|---|---|---|
| 引用总数 | 171 | 171 | 一致 |
| 存在 | 128 | 128 | 一致 |
| 缺失 | 43 | 43 | 一致 |
| 存在 + 缺失 | 171（=128+43） | 应等于 171 | 一致 |
| 缺失路径去重 | 16 | 16 | 一致 |
| 涉及 fact 去重（至少 1 条缺失） | 34 | 34 | 一致 |

一条重要实现细节：若用常见正则 `\([^)]*\)$` 去锚点，遇到嵌套括号 `(a′)` 会在内层 `)` 处截断，留下 `R14_COMMON.md(§2.10 / 一 / (a′)` 这样的伪路径，导致结果变成 126 存在 / 45 缺失 / 17 去重缺失（F06、F07 各 1 条受影响）。改用「从第一个 `(` 截断」后得到上表的正确值。这是构造反例的入口，见「反例」节。

---

## 命题 B（零可核验证据的 fact）：成立

- 零可核验证据的 fact：**F23、F35**（与预期一致）。
  - F23：2 条引用全缺失 —— `lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md`、`lead/next_re_20261117_r14/COVERAGE/PANEL.md`
  - F35：1 条引用缺失 —— `lead/next_re_20261117_r14/COVERAGE/PANEL.md`
- evidence_paths 为空或只含空格的 fact：**无**（54 行全部非空）。

---

## 命题 C（F24 语料清单闭合）：成立（带一个口径说明）

先打印表头再取列，五份文件的 bytes 列均为第 2 列（名 `bytes`）；表头分别为：
- `R17_R88_T1_SEMDEF/tier_final.tsv` → `rel  bytes  why_content  oldC  in_A`（5 列，与其余 4 列不同，已按列名定位 bytes）
- 其余四份 → `rel  bytes  source  why_content`

对照 F24 正文中声明的件数/字节数：

| 清单 | 我算数据行数 | 我算 bytes 求和 | F24 声明 | 是否对上 |
|---|---|---|---|---|
| R17_R88_T1_SEMDEF/tier_final.tsv | 4518 | 724479859 | 4518 / 724479859（主文「4,518 / 724,479,859 B」） | 对上 |
| R17_R96_TIER_FINAL_4413/tier_final_4413.tsv | 4413 | 744172839 | 4413 / 744172839 | 对上 |
| R17_R97_TIER_FINAL_4413B/tier_final_4413b.tsv | 4413 | 727461721 | 4413 / 727461721 | 对上 |
| R17_R99_TIER_FINAL_4416/tier_final_4416.tsv | 4416 | 736151921 | 4416 / 736151921 | 对上 |
| R17_R101_TIER_FINAL_4417/tier_final_4417.tsv | 4417 | 737517286 | 4417 / 737517286（当前主引值） | 对上 |

口径说明：`R17_R88_T1_SEMDEF/tier_final.tsv` 物理上共 4520 行（含表头），末尾第 4520 行是无 TAB 的审计附记：
`DISC_RECHECK discipline=28 round=R55 at=2026-11-22T17:39:19+08:00 anchors=sha256:e394ea5dbbb4dbbc88d1d386402fc938a32ec52b5bb9c9a2e23d28325a16c28c conclusion=PASS`
它不是清单数据行（无 rel/bytes 结构）。把它排除后是 4518 行 / 724479859 B，与声明完全一致；若机械计为数据行会得到 4519 且 bytes 列有 1 行不可解析（int 抛 ValueError）。

---

## 命题 D（F29 字节断言）：部分成立

### D0 节表核对（pefile 实读，不照抄卡面）

ImageBase = 0x400000，SectionAlignment = FileAlignment = 0x1000，NumberOfSections = 5。
pefile 输出（Name, VirtualAddress, VirtualSize, PointerToRawData, SizeOfRawData）：

```
.text   0x1000    0x3df38d  0x1000    0x3e0000
.rdata  0x3e1000  0x30074   0x3e1000  0x31000
.data   0x412000  0x367be4  0x412000  0x6c000
.rsrc   0x77a000  0x18128   0x47e000  0x19000
.detour 0x793000  0x2718    0x497000  0x3000
```

卡面给的 4 个节 `.text / .rdata / .data / .detour` 的 VA、raw size、raw offset 全部与 PE 头一致；但卡面节表**漏了 `.rsrc`（VA 0x77a000，raw 0x19000 @ 0x47e000）**。本次涉及的 4 个 VA（0x7E11C8、0x6C2AC0、0x7F3D98、0x40F990）都不落在 .rsrc 内（0x7E11C8/0x7F3D98 在 .rdata，0x6C2AC0/0x40F990 在 .text），故节表遗漏不影响下述读数。

### D1  VA 0x7E11C8，16 字节（RVA 0x3e11C8，.rdata，file_off 4067784 = 0x3E11C8）

```
raw: 90 f9 40 00 78 f9 40 00 62 f9 40 00 48 f9 40 00
dwords (LE):
  [0] 0x40f990
  [1] 0x40f978
  [2] 0x40f962
  [3] 0x40f948
```

### D2  VA 0x6C2AC0，16 字节（RVA 0x2c2ac0，.text，file_off 2894528 = 0x2C2AC0）

```
raw: 8b 44 24 04 83 c0 04 50 ff 15 c8 11 7e 00 c2 04
```

### D3  VA 0x7F3D98，16 字节（RVA 0x3f3d98，.rdata，file_off 4144536 = 0x3F3D98）

```
raw: 50 51 6c 00 c0 51 6c 00 e0 51 6c 00 10 52 6c 00
dwords (LE):
  [0] 0x6c5150
  [1] 0x6c51c0
  [2] 0x6c51e0
  [3] 0x6c5210
```

### D4  以 D1 第 1 个 dword = 0x40F990 为地址，读 8 字节

0x40F990 → RVA 0xf990，.text，file_off 63888 = 0x0F990：

```
raw: dd 05 18 17 7e 00 dc 35
```

（另：D1 四个 dword 指向的 8 字节分别：
0x40f990 → `dd 05 18 17 7e 00 dc 35`；
0x40f978 → `c0 1e 7e 00 dd 1d 88 75`；
0x40f962 → `88 00 83 c4 08 c3 90 90`；
0x40f948 → `08 17 7e 00 e8 5f 96 3b`。可见这些槽内的值多为地址型数据，不是直接可执行码。）

### D5  VA 0x6C2AC0 是否为 `call [0x7E11C8]` 形态：**否（严格字节口径）**

期望形态 `FF 15 C8 11 7E 00`，而 D2 起始 6 字节为 `8B 44 24 04 83 C0`，不相等（MATCH: False）。

objdump 反汇编窗口（起始 0x6C2AB0）确认指令边界：

```
006c2ac0:  8b 44 24 04           mov    0x4(%esp),%eax
006c2ac4:  83 c0 04              add    $0x4,%eax
006c2ac7:  50                    push   %eax
006c2ac8:  ff 15 c8 11 7e 00     call   *0x7e11c8
006c2ace:  c2 04 00              ret    $0x4
```

真正的 `call [0x7E11C8]` 在 **0x6C2AC8（= 0x6C2AC0 + 8）**；0x6C2AC0 是函数入口。若把「0x6C2AC0 处」理解为「以 0x6C2AC0 为入口的这段函数里」，则函数内确有该 call（+8 处），F29 正文的语义不断言错；但卡面 D5 的严格字面命题（入口 6 字节等于 FF 15 + 地址）**不成立**。

### 附加核对：0x7E11C8 的导入表解析

pefile 解析导入目录：IAT 槽 0x7E11C8 = KERNEL32.dll 的 `InterlockedIncrement`，hint=432（按名导入，非序数）。这与 F29 正文「0x7E11C8 已经导入表证实为 KERNEL32.dll 的 InterlockedIncrement（Hint=432）」一致。

---

## 反例

找到了针对**命题 D5 字面表述**的反例（也是对 F29 正文一处措辞的反例）：
卡面 D5 与 F29 正文都写「0x6C2AC0 是 call [0x7E11C8] 的真 AddRef」。按原始字节，0x6C2AC0 处的 6 字节是 `8B 44 24 04 83 C0`（mov eax,[esp+4]; add eax,4），并非 `FF 15 C8 11 7E 00`；call 实际位于 0x6C2AC8。objdump 已确认指令边界，不存在「从 0x6C2AC0 误对齐到 0x6C2AC8」的合法反汇编解释（0x6C2AC0 是函数入口，前有 0x90 填充、后有 ret 4 收尾）。因此若有人按「VA == 0x6C2AC0 处就是那条 call 的地址」逐字节核验，会判 F29 该句为错；正确写法应是「0x6C2AC0 入口函数内 +8 处（0x6C2AC8）为 call [0x7E11C8]」。

另记录 A 的实现级反例（不是对 A 结论的推翻，而是对「如何拆锚点」的推翻）：同一份 TSV，用 `\([^)]*\)$` 剥离锚点会得到 126/45/17，与卡面 128/43/16 不符；只有按「第一个 `(` 截断」才复现 128/43/16。由于 F06/F07 的锚点 `§2.10 / 一 / (a′)` 含嵌套括号，任何假定括号不嵌套的解析器都会翻车。这解释了为何「独立复算必须自写脚本、不能照抄正则」在本题是实质要求。

---

## 无法判定的项

1. 卡面 D5 的「处」是否按字面（入口字节）还是按函数归属理解，卡面未定义；我两种口径都给了：字面不成立，函数归属成立。若调度方要求单一结论，需其明确口径。
2. F29「该 AddRef 对 [this+4] 自增」的语义：D2 的 `mov eax,[esp+4]; add eax,4; push eax; call InterlockedIncrement; ret 4` 与「对 this+4 处的 LONG 自增」一致，但本次只读了 8+ 字节，未追 `this` 的调用约定与 [this+4] 的写回语义；严格说该句在本报告里只能算「与字节形态相容」，不算我独立证明。
3. 命题 A 的 16 条缺失路径是否「本精简库外的 live 路径存在」，只能判定在本盘 os.path.isfile 为假；盘外是否存在无法从本库确定。

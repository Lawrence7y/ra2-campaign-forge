# R-058 · 容器宿主拿到名字：RTTI 链把 `+0x2C` 容器钉到 `CCINIClass`（并定谳 INISection、闭合 L-25）

> 对象：`gamemd.exe` sha256 `73201cc0…f67476`（只读）。
> 门禁 `tools/r058_container_class_rtti.py` **28/28 PASS**；变异
> `tools/mutate_r058_gate.py` **27/27 精确集合击杀**（每条断言都有可杀变异，
> 逐一清点过 killer 覆盖）。全部常量由 `out/_probe_r058_*.py` 机器转储先行（G-65）。
> 领 R-057 §6 悬项 (1)（容器归属）与 §6 悬项 3（L-25）。

## 0. 结论表

| # | 结论 | 强度 |
|:--|:--|:--|
| ① | `new(0x58)` 工厂（`0x52CBFB`，加载 `"BATTLEMD*.INI"`）构造的对象**类名 = `CCINIClass`** | RTTI 实证 |
| ② | `CCINIClass` **派生自 `INIClass`**（基类表条目 TD=`INIClass`，mdisp=0） | RTTI 实证 |
| ③ | 容器四字段 `{+0 数组基址,+4 个数,+0xC 排序标志,+0x10 命中缓存}` 嵌在该对象 **+0x2C**；构造器对它显式四槽清零 | 构造现场实证 |
| ④ | 对象 +0x0C 处内嵌 `List<INISection*>`（facet vptr `0x7E1AFC` 的 TD 名）；其基类 `GenericList`/`GenericNode` 同表族 | RTTI 实证 |
| ⑤ | R-056 §C 的「dtor 形宿主」(vptr `0x7EB73C`) 的类名 = **`INISection`**（INIClass 的嵌套 struct，`U` 前缀） | RTTI 实证 |
| ⑥ | **L-25 闭合**：`CCINIClass` 尺寸 0x58 双路实证 —— 堆上 `push 0x58; call new` @`0x52CBFB`，以及 6 个 `.data` 全局由**全局构造器**直接盖 vptr（从不 new） | 实证 |
| ⑦ | 孪生不对称：twin A（`0x52B4F0`）22 个调用者里 **13 个**在 call 前 0x40 内有 `add esi,0x2c`（重基址协议）；twin B（`0x52B620`）20 个调用者里 **0 个**（远端才有） | 普查实证 |
| ⑧ | 六个被盖 vptr 的全局：`0x887180 / 0x887208 / 0x887128 / 0x887058 / 0x8870C0`（`0x40DFE0` 簇）+ `0x89F518`（`0x49B405`，独立小簇） | 实证 |

**一句话**：R-057 卡在「结构是真的、类不知道」；本轮 RTTI 三段链
`vtable → COL → TypeDescriptor（x86 名内联在 TD+8）` 把类名直接钉死，
并顺手把 R-056 留下的「匿名 dtor 宿主」也钉成 `INISection`。

## 1. RTTI 链怎么钉的（布局是验出来的，不是背出来的）

x86 MSVC：`COL = {sig=0, offset, cdOffset, TD, CD}`（在 vtable[-1]）；
**TD 名在 TD+8 内联**（不是 TD+0x10 指针——那是 x64 布局，探针按指针解引用直接崩，
用崩溃反证了布局，A1..A3 门禁把这条钉死）。CD = `{sig, attr, numBase, baseArray}`，
基类条目首 dword 是 TD。

```
[0x7E1AF0] = 0x7FAC88   ; 工厂在 [esi]=0x7E1AF4 的 vtable[-1]
COL  0x7FAC88 = {0,0,0, TD=0x8174C8, CD=0x7FAC78}
TD   0x8174C8 名 = '.?AVCCINIClass@@'          <- A2
CD   0x7FAC78 numBase=2 array=0x7FAC68 -> {0x7FAC50, 0x7FAC38}
条目 0x7FAC38 首 dword TD=0x8174B0 名 = '.?AVINIClass@@'   <- A4/A5
```

**防篡改结构证**（A6）：六个 TD（INIClass/CCINIClass/List/INISection/GenericList/
GenericNode）vfptr 全部共享 `0x7F9594`（slot0=`0x7C8AB7`）——同一个编译器生成的
TypeDescriptor 表，排除「手工摆出来的假 vtable」。

facet 链：`[0x7E1AF8]=0x7FAC20` COL → TD `0x817480` = `'.?AV?$List@PAUINISection@INIClass@@@@'`
（A7）；`0x7E1B04`→`GenericList`、`0x7E1B0C`→`GenericNode`（A8）。
dtor 宿主：`[0x7EB738]=0x803708` COL → TD `0x825B40` = `'.?AUINISection@INIClass@@'`（A9/A10）。

## 2. 工厂 = `CCINIClass` 的构造现场（B 组）

```
0x52CBA0  68 a8 61 82 00    push 0x8261A8        ; "BATTLEMD*.INI"（字符串实测，B1）
0x52CBFB  6a 58             push 0x58            ; 尺寸
0x52CBFD  e8 15 c2 29 00    call 0x7C8E17        ; rel32 算术解码 = CRT new（B2/B3，G-11）
0x52CC0B  8d 7e 0c          lea edi,[esi+0xC]    ; facet 就位
0x52CC16  e8 c5 e0 ff ff    call 0x52ACE0        ; List 子构造器：先盖基类 Generic* vptr
0x52CC1B  c7 07 fc 1a 7e 00 mov [edi],0x7E1AFC   ; 再用派生 List vptr 覆盖 —— 教科书基/派序列（B6）
0x52CC21  ...895e2c 895e30 885e38 895e3c...      ; 容器四槽显式清零（B5）
0x52CC36  c7 06 f4 1a 7e 00 mov [esi],0x7E1AF4   ; 主 vptr = CCINIClass（B4）
```

**③ 的含义**：容器不是「恰好和 CCINIClass 字段表重合」，而是**被构造器当字段初始化**
（清零 + 尺寸容纳于 0x58）。R-057 表里四行宿主偏移现在收窄为两行定谳、两行另议：
`this+0`（孪生自身）与 `+0x2C`（两个活见证 + 0x52A4D0 同偏移）都有「CCINIClass 宿主」
这一硬底座；而 `0x528A10` 路径 B 的 `+0x28` **不是** CCINIClass 的容器槽（构造器把
`+0x28` 当独立 dword 清零、容器在 `+0x2C`）⇒ 要么 `0x528A10` 的 `this` **不是**
CCINIClass，要么它读的是与容器形状巧合的另一成员。**本轮不断言哪种**——
`0x528A10` 宿主类仍未定（诚实账 ① 的具体化）。

## 3. L-25 闭合（D 组）：全局 CCINIClass 从不 new

`0x40DFE0` 簇（一个全局构造器函数）对 **5 个 `.data` 全局**逐一：盖 List 族 vptr、
盖主 vptr `0x7E1AF4`、清零镜像字段、`push 0x88719c` → `call 0x40E340`（注册 worker，
参数结构 `{+4 链, +8 …}`）→ `push 0x40E050`。thunk `0x40E050 = mov ecx,0x887180;
jmp → 0x5256F0`（push ebx/esi、xor ebx 的析构形函数）——**atexit 式注册析构**，
与 §391 RC-4 的 atexit 重盖 vptr 是同一机制家族（D4 只登记形状，不外推）。
worker 的节点初始化子程序 `0x40E320` 尾字节 `c7 00 0c 1b 7e 00` =
`mov [eax],0x7E1B0C`（GenericNode vptr，A8）⇒ **注册表本身也是 Generic* 链表族**（D4）。

第 6 个全局 `0x89F518` 由独立位置 `0x49B405` 盖 vptr、thunk `0x49B420` 指 dtor；
它**属于哪个 `.ini` 未证**（coopsave.ini push 在 `0x49BE64..`，是后面的别的函数体，
门禁明细里明写「不断言」——诚实账 ③）。

`0x887058` 等全局的**本体字节不可读**（`.data` raw 覆盖 0x412000..0x47e000，
全局 VA 越过 raw 尾 = 零填充段）⇒「全局 ctor 必须在启动时盖 vptr」自洽（D1）。

## 4. 孪生不对称（F 组）——修正 R-056 的「可互换重复」印象

| 量 | twin A `0x52B4F0` | twin B `0x52B620` |
|:--|--:|--:|
| E8 调用者 | 22 | 20 |
| call 前 0x40 内 `add esi,0x2c` | **13** | **0** |
| call 前 0x200 内 | 22 | 15 |

字节等价（R-056 A4）**不等于调用协议等价**。A 是「宿主对象 +0x2C 容器查找」（两个
活见证 `0x527750`/`0x52A7DE` 都在 13 人近端集合内，F3 用**集合成员**不用计数）；
B 的 20 个调用者没有近端重基址——它们的容器在别的偏移/别的寄存器形态上。
「同一函数编译两遍」的定性不变，但**「可互换」的印象作废**（诚实账 ② 升级）。

`0x52A4D0` 依旧三通道零引用（E8/E9/imm32，阳性对照 = 同趟 twin A 的 22，F2），
**仍不下死代码定谳**。

## 5. 与两条异族盲验路线的关系（本轮反采纳）

- GLM 路线给的 `0x52A7BD` 第二活见证：**采纳**（字节复核 E2 成立，
  且它补出「调用方在 call 前先查 `[esi+0x10]` 缓存、未命中才 call、命中回填」的
  完整协议——比我原来的 witness1 更富）。
- qwen 路线给的「`0x52CC21` 清零集按 +0x2C 粒度、vptr 槽写非零 ⇒ 可判别」：
  **采纳并升级为 B5**；R-057 初稿说「构造器判别不了」只在**存在性**口径成立，
  **取值+宽度口径判别成立**——已记 G-78 附例。
- 两条路线都未做的（本轮新做）：RTTI 链、工厂字符串、全局构造器簇、近端重基址普查。

## 6. 诚实账 / 未证项

1. **见证函数的 `this` 还没逐个回溯到具体实例**（全局 or 工厂堆对象）：
   `mov ecx,0x887180` 等「全局作 this」站点存在（clean census：
   `0x887180` 3 处 / `0x887128` 3 处 / `0x89F518` 28 处…），但与 13 个近端见证站点的
   **一一对应未证**（需函数边界图）。下一轮首要。
2. `0x52A4D0` 静态隐身依旧无解释（非 .text 到达路径没找到）。
3. 第 6 全局 `0x89F518` 的 .ini 归属未证（见 §3）。
4. 「`BATTLEMD*.INI` 通配」语义（多文件合并进一个实例？）未证。
5. `INIClass` 主 vtable `0x7E1AF4` 槽表本身未展开（槽数/语义）。
6. atexit 注册队列与 CRT 的关系只登记形状（`call 0x40E340` 参数结构、
   worker 链字段），不宣称机制定谳。
7. 不宣称任何可改写点。

## 7. 判例入账

- **G-79（新）**：变异套件全绿 ≠ 每条断言可杀。首轮 24 案 21 OK，按断言清点
  killer 覆盖后发现 **A7/A8/D1 三人零 killer**（补 M31..M33 才闭合）。
  「N/N 击杀」的 N 分母是**用例**，不是**断言**——套件收口必须做
  断言→killer 的双向清单。是 R-033「装饰断言」同类在套件层的复发。
- **G-75 附例**：M02 预期多列 A1——A1 只读 COL 20 字节窗口，名在 TD+8 窗口外；
  击杀集必须按**读取足迹**推，不能按语义联想。
- **G-71 判据一三连**：M06（A9 钉链、A10 钉内容——两个窗口各管各的）、
  M24（F2 把 22-对照嵌进断言里，所以丢一个调用者也打红）——全部改预期，不动判据。

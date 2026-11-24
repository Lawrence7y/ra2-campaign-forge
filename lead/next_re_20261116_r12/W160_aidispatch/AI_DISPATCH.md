# W160 · ObjectClass AI 派发（每 tick）结论

## 摘要（5 行）

1. **[已证]** Lead 中途更正的前提成立：真正的每帧全对象 AI 派发在 `0x55AFB0` 的 `0x55B610`，遍历 `this=0x87F778`（LogicClass 的 `VectorClass<ObjectClass*>`），逐元素 `call [vptr+0x5C]`，无 mode 门。
2. **[已证]** `[esp+0x10] = this`：函数栈帧 `sub esp,0x28` + 4×push(0x10) ⇒ 栈参数从 `[esp+0x3C]` 起（保守阈值 `0x38`）；实测 `[esp+N]` 最大 `0x34`，`mov [esp],ecx` 保存 this（push 后即 `[esp+0x10]`）；Ghidra 反编译独立得到 `param_1+0x10/+4` 循环。
3. **[已证]** 该循环**不检查 `+0x98`**、**每次迭代重读 Count**（`0x55B613`）；注册 `0x55BAA0` 置 `+0x98=1`，注销 `0x55BAE0` 清 0 并摘链 ⇒ 语义是"对在册对象逐帧调 AI"，孤儿阶梯才是带 `+0x98` 门的版本。
4. **[已证]** 全镜像 `call [mem+0x5C]` 原始 **166** 处（164 边界成立 + 2 处 SIB 栈调用），有效 **164**，普通寄存器子集 **162**；没有发现 `call [reg+index*4+0x5C]` 派发表或 `add reg,0x5C; call [reg]` 形态。
5. **[已证]** `0x55B8F0` 孤儿阶梯全镜像零引用、全文件零地址字面量、零 `push`；结合 W159 真机 0 命中，最像**旧版/被取代的实现**（静态不能 100% 排除运行期计算入口）。

> 纪律说明：Lead 在任务进行中更正了前提（见 `DISAGREE.md`），本报告按新前提重做。
> 双通道：通道 A = 全 `.text` 逐字节 + capstone `skipdata=True`（不依赖 atlas entry+size）；通道 B = Ghidra `-noanalysis` 引用模型/反编译。Ghidra 对空洞区不建函数，因此穷举数字以通道 A 为准。

---

## Q1：162 处普查能否被推翻 / 漏掉的调用形态

### 1.1 独立重做口径

通道 A（`work/q1_byte_census.py`，`EVIDENCE/W160_Q1_channelA.json`）：

```bash
python lead\next_re_20261116_r12\W160_aidispatch\work\q1_byte_census.py
```

- `.text` 原始字节逐字节搜 `FF /2`（`mod=01/10`，rm=reg 或 SIB），disp 为 `0x5C`：原始 **166** 命中（`FF 5x 5C` 164 + `FF 54 24 5C` 2）。全节线性反汇编 `skipdata=True` 共 1,394,186 条指令，**166 个命中全部落在指令边界**。
- 按形态：REG 基址 **164**，SIB `[esp+0x5C]` **2**（`0x785132`、`0x7852CF`，均在 `fn 0x783C80` 内，是栈槽而不是虚表）。
- 与 Lead 对账后的三口径：原始操作数命中 **166**；边界成立/有效 **164**（= 普通寄存器 162 + SIB 2）；"普通寄存器子口径" **162**。Lead 初始的"原始 164、假阳性 2、有效 162"是把 SIB 整类漏掉并按子口径记数。
- 关于 `0x617641/0x61CC5C`（Lead 原称假阳性）：`work/boundary_proof.py` 从 `0x60CF00` 等 12 个 atlas 函数入口线性反汇编，它们**精确落指令边界**并解码为 `call [edx+0x5C]`；只是落在 atlas 的所有 entry+size 之外。它们应计入 164。Ghidra 因 `getFunctionContaining=NONE` 没有把它们归入函数（见下文 1.3）。

### 1.2 特别检查的三种"漏掉形态"

1. **SIB 编码**：`modrm=0x54/0x94` 的 `FF 54 5C xx`/`FF 94 5C imm32` 扫描后，`disp==0x5C` 的只有 2 个 `FF 54 24 5C`（`[esp+0x5C]`，栈槽）；`FF 94 5C imm32` 形式 0 命中。不存在被漏掉的 SIB 虚表调用。[已证，`work/alt_forms.py`]
2. **派发表 `call [reg + index*4 + disp]`**：全节线性扫描这种形态只有 3 处（`0x7CC172/0x7CC21B/0x7CC257`），disp 为 `+8/+4/+8`，**没有** `+0x5C`。[已证]
3. **`add reg,0x5C; call [reg]`**：全节扫描 `add reg,0x5C` 共 64 条（多数是 `add esp,0x5C` 栈清理），后续 8 条指令内跟 `call [同一 reg]` 的 **0 处**。[已证]

⇒ Q1 的"漏形态"假设全部被否证；普查数字修订为 166/164/162 三口径。

### 1.3 通道 B（Ghidra）与通道 A 的对账

一次 `-noanalysis` 运行（`work/W160Gather.java`，日志 `EVIDENCE/W160_Ghidra_gather.log`）：

- `XREF_TO_SUM 0055B8F0 n=0`，`FUNC_AT 0055B8F0 = NONE`（孤儿区不建函数）。
- `XREF_TO_SUM 0087F778 n=20`（含 `0x55DC99 mov ecx,...` 与多处注册/遍历）。
- `XREF_TO_SUM 0040CB80 n=1` / `0040CBC0 n=1`（静态构造器/atexit 析构器）。
- 全指令扫描 `CALL_5C_TOTAL 141`，`CALL_5C_FUNCS 92`，其中 12 个 `fn=NONE`。**这个数不能当穷举真值**：Ghidra 对 `0x617641/0x61CC5C` 等代码空洞不建函数/不完整建模；全节字节通道才是穷举通道。两条通道在"8 个 `0x55AFB0` 站点、11 个孤儿阶梯站点、`0x55B8F0` 零引用"等具体事实上一致。

---

## A：独立复核 Lead 的 1–4 条

### A1 `[esp+0x10]` 是 `this` 还是栈参数

独立算法（`work/analyze_55afb0.py`，输出 `EVIDENCE/W160_analyze_55afb0.stdout.txt`）：

```python
# capstone detail，枚举 0x55AFB0 (size=1901 十进制) 全部 esp 基址访存
offs = {op.mem.disp & 0xffffffff for ins in ... for op in ins.operands
        if op.type==X86_OP_MEM and op.mem.base==X86_REG_ESP}
# 实测 = [0,4,0xc,0x10,0x14,0x18,0x1d,0x20,0x24,0x28,0x2d,0x30,0x34]
```

- 序言 `0x55AFB0 sub esp,0x28` ⇒ 局部区 `[esp+0x00..0x27]`（此时 esp 记为 S0）。
- 随后 `0x55AFC3..0x55AFCC push ebx/ebp/esi/edi` 4×4=0x10 字节 ⇒ 最终 esp = S0-0x38。
- 调用约定：进入函数时 `[S0+0]=返回地址`，第一个栈参数在 `[S0+4]`；最终 esp 下它是 `[esp+0x3C]`。即便用不计返回地址槽的保守阈值也是 `0x38`。实测最大 `0x34` 小于两者 ⇒ **没有栈参数**。
  - 直接别名证明：`mov [esp],ecx`（在 `sub` 之后、push 之前）写入 `[S0]`，4×push 后该 dword 位于 `[esp+0x10]`。二者是同一个内存 dword。
- `0x55B5FB mov edi,[esp+0x10]` 位于这段里，Ghidra 反编译给出等价形式：`if (0 < *(int *)(param_1 + 0x10)) { do { (**(code **)(**(int **)(*(int *)(param_1 + 4) + iVar6*4)+0x5c))(); ... } while (iVar6 < *(int *)(param_1 + 0x10)); }` —— `param_1` 即 `ecx`（this），**不是栈参数**。

⇒ **[已证] `edi = this`。** 调用点 `0x55DC99 mov ecx,0x87F778` / `0x55DC9E call 0x55AFB0` 字节 `b9 78 f7 87 00 e8 0d d3 ff ff`（`EVIDENCE/W160_verify_stack.stdout.txt`）⇒ `edi=0x87F778`。

### A2 `0x87F778` 的身份

`work/bss_writer_scan.py` 与 `work/ctor_disasm.py` 从原始字节定位静态构造器 `0x40CB80`：

```
0040CB80 xor eax,eax
0040CB82 push 0x40cbc0              ; atexit 析构
0040CB87 mov [0x87f77c],eax         ; Items=0
0040CB8C mov [0x87f780],eax         ; Cap=0
0040CB91 mov byte [0x87f784],1      ; IsInitialized
0040CB98 mov byte [0x87f785],al     ; IsAllocated=0
0040CB9D mov [0x87f78c],0xa         ; Increment
0040CBA7 mov [0x87f788],eax         ; Count=0
0040CBAC mov [0x87f778],0x7e18fc
0040CBB6 call 0x7c978a              ; atexit
```

`vtables_canonical.json`：`0x7E18FC = .?AVLogicClass@@`；析构器 `0x40CBC0` 把 vptr 改为 `0x7E192C = .?AV?$VectorClass@PAVObjectClass@@@@` 并释放 Items。

⇒ **[已证]** `0x87F778` 是 LogicClass 单例，内存布局是 `VectorClass<ObjectClass*>`：`+4 Items / +0x10 Count`（注意是 `VectorClass`，不是 `DynamicVectorClass`；Capacity 等字段语义不同，但本循环只用 Items/Count）。

### A3 `0x55B608` 循环边界

`EVIDENCE/W160_whole_text_disasm.tsv` 与 `W160_analyze_55afb0.stdout.txt`：

```
0055B5FB mov edi,[esp+0x10]      ; edi = LogicClass
0055B5FF xor esi,esi
0055B601 mov eax,[edi+0x10]      ; Count
0055B604 test eax,eax
0055B606 jle 0x55b61b
0055B608 mov eax,[edi+4]         ; Items
0055B60B mov ecx,[eax+esi*4]
0055B60E mov edx,[ecx]
0055B610 call [edx+0x5c]         ; AI
0055B613 mov eax,[edi+0x10]      ; 每次重读
0055B616 inc esi
0055B617 cmp esi,eax
0055B619 jl 0x55b608
```

回边核对（`work/analyze_55afb0.py` 打印 9 个回边）：**没有**任何回边指向 `0x55B5FB`；`0x55B5FB` 仅由 `0x55B5F6 call 0x4c54a0` 之后的直落到达。`[esp+0x10]` 在 `0x55B6EF/0x55B6FC` 的后续覆写发生在循环之后，不影响此读。

⇒ **[已证]** Lead 的 1–4 全部成立。

---

## B：语义边界 / `+0x98` / Count 重读

### B1 运行期装的是什么

静态能判定到"这个容器**类型**是 `VectorClass<ObjectClass*>`"（vptr `0x7E18FC/0x7E192C` 双阶段 + COL），并且注册/注销入口是 `0x55BAA0`/`0x55BAE0`（前者 `call 0x5519B0` 过滤后置 `[obj+0x98]=1`，后者经 `call [vptr+0x10]` 查找索引、左移覆盖、Count--、`[obj+0x98]=0`；`EVIDENCE/W160_reg98.stdout.txt`）。全镜像有 21 处把 `0x87F778` 当 `ecx` 调用成员函数/遍历（如 `0x435AFC`, `0x4F9C7F`, `0x64DD98`, `0x68558B`, `0x7259CA`），其中多处以 `[0x87F77C]` Items + `[0x87F788]` Count 做遍历（例如 `0x482C18`, `0x4F9C7F`），说明它是引擎的"活动对象列表"。

**[静态推断]** 该向量装的是引擎的活动 ObjectClass（很可能含 Bullet/Anim、House/Team/Factory 等非 Foot 对象），不是"只含需要 AI 的对象"——因为没有任何类型过滤器在 `0x55B610` 前，且调用点直接传 `this=LogicClass`。**[未证]** 精确成员集合（vtable 逐一点名 + 与 `AbstractClass::Array` 对账）需要真机读该容器，本卡禁止。

### B2 `+0x98` 门差异的含义

孤儿阶梯（`0x55B8F0`）每块都有 `mov al,[obj+0x98]; test; je skip`；每帧循环 `0x55B610` **没有**。结合 `+0x98` 的设置/清除点：

- `0x55BAA0`: 注册时若 `[obj+0x98]!=0` 直接返回（幂等），否则 `call 0x5519B0` 过滤后 `mov [obj+0x98],1`。
- `0x55BAE0`: 注销时先按 vptr 查索引并从向量中删除，再 `mov [obj+0x98],0`。

⇒ **[静态推断]** `+0x98` 表示"已在册"。孤儿阶梯是"注册对象但跳过未激活者"的保守版本；每帧版依赖"向量里只存在在册对象"这一不变量，不需要再查标志。这也解释了为什么 `0x55AFB0` 的其它 7 个循环都没有 `+0x98` 门：它们也直接遍历各自的 `DynamicVectorClass`。

### B3 重读 Count 的增删/重入行为

`0x55B613` 每次迭代 `mov eax,[edi+0x10]` 重读 Count，`cmp esi,eax; jl` 继续；Items 指针 `0x55B608` 也每次重载。

- 若某次 AI 在向量**尾部追加**：Count 增大，循环会继续处理新增对象（可能同一帧内被 AI 两次，若加入位置 ≤ 当前 esi 则会跳过）。
- 若 AI 删除**当前或之前**的元素：左移覆盖会让后面元素被跳过或重复；`esi` 单调增而 Count 减小 ⇒ 可能提前结束、漏调。
- 若 AI 删除当前元素本身：下一次迭代读的是原下一个元素（已被移到当前位置），本轮当前位被跳过一次。
- 若 AI 注销自己（调用 `0x55BAE0`）导致 Items 被 `free`/重分配：`0x55B608` 每次重载 Items 指针，不会持有野指针，但索引语义仍可能跳/重。

**[静态推断]** 这个写法对重入不健壮；引擎可能依赖"AI 不修改全局对象向量"的约定。要证实/否证需对 5 个 AI 入口做全 callee BFS 查是否调用 `0x55BAA0/0x55BAE0` 或直接写 `[0x87F778]`（本卡未做 exhaustive BFS，列 `[未证]`）。

### B4 每帧推进由谁做

`0x55D360 →(0x55DC9E)→ 0x55AFB0` 在每帧路径（§894 已证 `0x55DC9E` 在写档门控汇合点之后，所有 mode 执行）。`0x55D360` 的 44 个直接 callee 中，只有 `0x55AFB0` 含槽-0x5C 数组循环；`0x4F4320`/`0x55E160` 各只有一个单对象虚调用（都不是遍历 Unit/Infantry/Building/Aircraft/Bullet 类型数组）。因此**每帧对象状态推进机制**是：

1. `0x55AFB0` 的 8 个虚调用循环，按容器批量调 `AI`（主通道是 LogicClass 的全部对象向量）。
2. 各对象 `AI`（如 `BulletClass::AI 0x4666E0`）内部自行推进位置/碰撞/状态。
3. 原生类型数组（Unit/Infantry/Building/Aircraft/Bullet）的每帧行为**通过 LogicClass 全局向量**驱动，而不是各自 `Array`；这解释了为什么此前在 162 个站点里找不到"遍历各类型 Array 调 AI"的代码。

---

## C：`0x55AFB0` 8 个槽-0x5C 站点逐个重新定性

全部证据来自 `instance_arrays.tsv`、静态构造器 vptr、`vtables_canonical.json` 的 COL 名、Ghidra 反编译。列"上界"= 每次比较还是快照。

| # | call 地址 | 数组/对象身份（独立反查） | 证据 | 上界来源 | 门控条件 |
|---|---|---|---|---|---|
| 1 | `0x55B595` | 调用前由 `0x55BB40`（`VectorClass<TagClass*>` vptr `0x7E9F84`）初始化的**临时向量**（栈 `[esp+0x24]`/`[esp+0x30]`），内容是 `TagClass::Array`(`0x8B40CC/0x8B40D8`) 经 `call [vtable+8]` 过滤后的子集 | `0x4E7FB0` 构造器 `0x8B40C8=0x7EA5A4` `DynamicVectorClass<TagClass*>`；`0x55B50E` 写 `0x7E9F84`=`VectorClass<TagClass*>`；`0x55B4FD call 0x55BB40` | 每次迭代重读 `[esp+0x30]`（`0x55B598`） | 前置过滤：`[0xA8B230+0x34AB]` 标志 + `call [vtable+8]` 条件；无 mode 门 |
| 2 | `0x55B5B8` | `DiskLaserClass*`：Items `0x8A020C`, Count `0x8A0218` | `instance_arrays.tsv` 唯一匹配，vptr `0x7E5EDC`=`DVC<DiskLaserClass*>` | **快照**（`mov eax,[Count]; lea esi,[eax-1]`，向下数） | 无 mode 门 |
| 3 | `0x55B5E4` | `RadSiteClass*`：Items `0xB04BD4`, Count `0xB04BE0` | `instance_arrays.tsv`，vptr `0x7F07A4`=`DVC<RadSiteClass*>` | **快照** | 无 mode 门 |
| 4 | **`0x55B610`** | **`LogicClass` 内的 `VectorClass<ObjectClass*>`**：Items=`[this+4]`= `[0x87F77C]`, Count=`[this+0x10]`=`[0x87F788]` | `0x40CB80` 构造器 vptr `0x7E18FC`，`0x40CBC0` 析构改 `0x7E192C`；两者 COL 名分别 LogicClass/`VectorClass<ObjectClass*>`；Ghidra 反编译 `param_1+4/+0x10` | 每次重读 Count（`0x55B613`） | **无任何门，每帧所有 mode 执行** |
| 5 | `0x55B63E` | `AnimClass*`：Items `0xA83E04`, Count `0xA83E10` | `0x4E7C60` 静态构造器写 `[0xA83E00]=0x7E9F24` = `DVC<AnimClass*>`（COL 名已核）；`instance_arrays.tsv` 无此行（TSV 漏项） | 每次重读 Count（`0x55B641`） | **mode 门**：`mode==0` 或 `mode==5` 时跳过（`0x55B61B test; je 0x55B64B` / `cmp 5; je`）；Ghidra: `if ((mode!=0)&&(mode!=5)&&...)` |
| 6 | `0x55B667` | 单对象：单例指针 `[0x887324]`，`mov ecx,[0x887324]; mov eax,[ecx]; call [eax+0x5C]` | 该地址在 `0x55D841/0x55E269/0x6485CD` 也被当 ObjectClass 用；精确类名 `[未证]` | 无循环 | 无 mode 门（紧跟 Anim 循环之后） |
| 7 | `0x55B680` | `FactoryClass*`：Items `0xA83E34`, Count `0xA83E40` | `instance_arrays.tsv`，vptr `0x7E9FA4`=`DVC<FactoryClass*>`；`0x4E6E60` 构造器确认 | 每次重读 Count（`0x55B683`） | 无 mode 门 |
| 8 | `0x55B6A6` | `HouseClass*`：Items `0xA8022C`, Count `0xA80238`；元素有 null 检查 `test ecx,ecx; je skip` | `instance_arrays.tsv`，vptr `0x7E9EE4`=`DVC<HouseClass*>` | 每次重读 Count（`0x55B6A9`） | 元素非空检查；无 mode 门 |

**关于 Lead 特别点名的身份**：`TeamClass`/`DiskLaserClass`/`RadSiteClass` 三项**有 TSV+构造器双证据**，不是猜测。其中 Team 出现在站点 1 的**来源数组**（`0x8B40CC/D8` 实为 `TagClass*` 而非 Team；真正的 TeamClass 数组是 `0x8B40E8/0x8B40EC/0x8B40F8`，在 `0x55B502/0x55B52A` 被读取用于构造过滤列表）。Lead 原表把 #1 标为"参数向量"、#4 标为"DVC 参数"均需按上表更正。

### E（mode 门控）汇总

只有站点 5 (`0x55B63E`, `AnimClass*`) 有 mode 门：`mode ∈ {1,2,3,4}` 才跑；`mode==0/5` 跳过。其余 7 个站点（含核心的 LogicClass 全对象 AI）均无 mode 门。因此局内（`mode=5`）跑的是 #1/#2/#3/#4/#6/#7/#8，**跳过 Anim**。这与 §9.1 真机"局内 0 弹基线 32 ms/帧"和"AI 驱动全部对象"一致。

---

## D：`0x55B8F0` 孤儿阶梯定性

| 假设 | 证据等级 | 依据 |
|---|---|---|
| (a) 链接进来的死代码 / 旧版被取代实现 | **[静态推断] 偏好** | Ghidra `getReferencesTo=0`（`W160_Ghidra_gather.log`）；全文件 4 字节 `F0 B8 55 00` 0 命中、`push 0x55B8F0` 0 命中（`W160_taskBD.stdout.txt`）；从 0x55B8F0 开头是完整 `push esi…pop esi;ret` 函数；W159 真机 818 万次采样 0 命中（台账 §896-1，本卡只读引用）；而每帧版 `0x55AFB0` 的相同语义（带更强的不变量）已在同一函数体内存在 ⇒ 阶梯像被取代的旧实现 |
| (b) 运行期构造的表可达 | **[未证]** | "地址字面量"通道全 0（无 `push imm32`、无 dword 表项）；但运行期可计算出 `base+delta` 再写入函数指针变量，静态无法穷尽。找到任何"把 0x55B8F0 写进表"或 `push 0x55B8F0` 会是重大发现，本次**没有** |
| (c) 被内联后的残留副本 | **[静态推断] 弱** | 它是 430 B 完整函数（有栈平衡 ret），不像典型内联残片；且与 `0x55AFB0` 语义不完全相同（有 `+0x98` 门、11 个类型数组 vs 8 个混合容器），更像独立旧版实现而非拷贝 |

---

## 机制结论

每 tick 的对象状态推进不依赖"逐类型 Array 循环"。链路：

```
0x48CCC0 (主循环)
  → 0x55D360 (每帧更新)
    → 0x55DC9E: mov ecx,0x87F778; call 0x55AFB0
      → 0x55B5FB: edi = this = 0x87F778 (LogicClass / VectorClass<ObjectClass*>)
        → 0x55B608..0x55B619: for i in 0..Count-1: AI(obj[i])   [vptr+0x5C, 无 +0x98 门, 无 mode 门]
      → 另 7 个槽-0x5C 循环 (Tag 临时向量 / DiskLaser / RadSite / Anim(mode∉{0,5}) / 单例 / Factory / House)
```

各对象的 `AI` 例：`BulletClass::AI 0x4666E0`、`UnitClass::AI 0x7360C0`、`InfantryClass::AI 0x51BAB0`、`BuildingClass::AI 0x43FB20`、`AircraftClass::AI 0x414BB0`（虚表校准，见 `R12_FACTS §6.1`）。它们没有静态直接调用者，因为都经此统一虚槽派发。这补齐了 ① 解释链上"每帧对象派发点"的硬缺口。

---

## LEAD_AUDIT（可独立复算）

1. **[已证] 每帧 AI 派发指令与地址链**：`0x55DC99 b9 78 f7 87 00`（`mov ecx,0x87F778`）+ `0x55DC9E e8 0d d3 ff ff`（`call 0x55AFB0`）；核心循环 `0x55B608 mov eax,[edi+4]` / `0x55B60B mov ecx,[eax+esi*4]` / `0x55B610 ff 52 5c`。复跑：`work\verify_stack.py`，输出 `EVIDENCE\W160_verify_stack.stdout.txt`；或 `grep -F '0055B610' EVIDENCE\W160_whole_text_disasm.tsv`。
2. **[已证] 栈算术**：`0x55AFB0` 内全部 esp 偏移集合 = `{0,4,12,16,20,24,29,32,36,40,45,48,52}`，max `0x34`；序言 `83 ec 28` + 4×push；`0x55AFB9 89 4c 24 00` (`mov [esp],ecx`) + `0x55B5FB 8b 7c 24 10` ⇒ `[esp+0x10]=this`。复跑：`python work\analyze_55afb0.py`；独立 Ghidra 反编译在 `EVIDENCE\W160_ghidra_extract.stdout.txt` 显示 `param_1+0x10 / +4`。
3. **[已证] `0x87F778` 身份双字节证据**：`0x40CBAC c7 05 78 f7 87 00 fc 18 7e 00`（写 `0x7E18FC`），`0x40CBC8 c7 05 78 f7 87 00 2c 19 7e 00`（写 `0x7E192C`）；COL 查 `vtables_canonical.json` 得 `.?AVLogicClass@@` 与 `.?AV?$VectorClass@PAVObjectClass@@@@`。复跑：`python work\ctor_disasm.py` + `python work\vtbl_lookup3.py`。
4. **[已证] 站点普查**：全 `.text` 原始 166 = REG 164 + SIB 2；`0x55AFB0` 内 8 站点 `0x55B595/5B8/5E4/610/63E/667/680/6A6`；孤儿阶梯 11 站点 `0x55B912..0x55BA98`。复跑：`python work\q1_byte_census.py` → `EVIDENCE\W160_Q1_channelA.json`，`python work\q1_sitelist.py` → `EVIDENCE\W160_Q1_sitelist.txt`。

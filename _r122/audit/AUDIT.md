# R122 跨家族审计 · hy4 · AUDIT.md

审计对象：主会话 r122a/r122b 脚本及 r122a_objs35.json、r122b_allvec.json。
所有"实测"数字来自我自己的独立复算脚本 `_r122/audit/audit_recalc.py`（只读取盘、只写自己的 out/audit .md），未引用主会话 json 的计数。
复算命令：`cd /home/t628/projects/ra2-campaign-forge/_r122/audit && python3 audit_recalc.py > audit_recalc.out`。
原 exe SHA256 实测 = `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，与主会话一致。

PE 节表实测：ImageBase=0x400000，SizeOfImage=0x796000（VA 末 0xb96000）。
- `.text`  VA 0x401000..0x7e038d（raw 0x3e0000）
- `.rdata` VA 0x7e1000..0x811074（raw 0x31000）
- `.data`  VA 0x812000..0xb79be4（raw 0x6c000），故 BSS 区 = [0x87e000, 0xb79be4)，长 3,128,292 字节
- `.rsrc`  VA 0xb7a000..0xb92128
- `.detour` VA 0xb93000..0xb95718

---

## A1 断言逐条审计

### r122a_objs35.py

| 检查 | cond 实参 | 实际验证了什么 | 与名字是否一致 |
|---|---|---|---|
| S2a (L97) | `len(calls)==36` | 重扫 call rel32 落在 [0x67fdf0,0x680f80) 得到 36 个不同入口。 | 一致。但"入口数"与"35 个孪生"不是一回事，它同时包含了控制入口 0x680f70；数值 36 本身不构成对"孪生"的断言。 |
| S2b (L102) | `total_sites==37` | 这些入口被 call 的总站点数=37。 | 一致。 |
| S2c (L111) | `set(R121_TWINS)<=set(CK_SITES)` | R121 硬编码的 35 站全在本次重扫的 37 站里。 | 一致。注意 R121_TWINS 是硬编码常量，不是从字节解出的；此断言只验证"R121 的名单没写错"，不验证名单本身的语义。 |
| S2d (L113) | `sorted(extras)==[0x67d193,0x67e62b]` | 多出的两站恰是这两个地址。 | 一致。 |
| S2e (L126) | `len(cands)==35 and not bad_shape` | 35 站前 7 字节形如 `ba <edx> 8b ce`。 | 一致。这是强字节锚点，是 R122 最有价值的断言之一。 |
| S2f (L130) | `len(set(EDX))==35` | 35 个 edx 互不相同。 | 一致。 |
| S1a/S1b/S1c (L134/137/141) | region 判断 / `BSS_LO<=a<BSS_HI` | 35 个 edx 在 `.data` 且落在 raw 尾 0x87e000 到虚拟尾 0xb79be4 之间。 | 一致。**但命名"BSS 区"是按 `va+SizeOfRawData .. va+VirtualSize` 算的虚拟区，不等于 Windows loader 实际零初始化的 BSS（loader 按 VirtualSize 提交，raw 到 VirtualSize 的部分零填充；此处 raw 0x6c000 < VirtualSize 0x367be4，故这段确为未落盘区，命名合理）。** |
| **S1d (L143)** | `rd(EDX[0],4) is None` | 只验证了脚本自己的 `rd()` helper 在读到 BSS 时**主动返回 None**（L68：`if va-x['va']+n > x['rs']: return None`）。 | **不是真反控。** 它验证的是 Python 函数行为，不是二进制事实。把任意 BSS 地址传进去都会 None，与 edx 取值无关；对 P1 没有任何增量证据。若要把 S1d 当"这些地址无文件字节"的证据，应当断言 `EDX[0] >= ds.va+ds.SizeOfRawData` 且读文件偏移不在 SizeOfRawData 内——这件事 S1c 已经做了，S1d 是冗余的自证。 |
| S2g (L155) | `len(writes)>1000` | c7 05 写 BSS 的不同目标数 >1000。 | 一致，用作"不是 35 个特例"的旁证，弱断言。 |
| S2h (L157) | `all(a in writes for a in EDX)` | 35 个 edx 每个至少被一条 c7 05 写入。 | 一致。 |
| S2i (L161) | `list(per.items())==[(2,35)]` | 35 个目标每个恰好被写 2 次。 | 一致，强断言。 |
| **S2j (L162)** | **`True`** | **什么都不验证。** cond 是字面常量 True；详情字符串里打印全库 sites-per-target 直方图，但直方图本身不是断言。 | **不一致，是占位断言。** 它声称"2 次写入对照全库不是多数派"，却没写 `Counter(len(v)...)[2] < len(writes)` 或类似条件。实测直方（我的复算第 9 行）：1 次=847 个目标、2 次=241、3 次=22……所以"2 次不是多数派"确实是事实，但**这个事实没有被 S2j 的 cond 验证**；cond 永远 PASS。任何返回 False 的实际情况都不会让它失败。 |
| S3a (L200) | `all(w['name'] for ...)` | 70 次写入全部经 name_of_vtable 解出 `.?AV...` 名。 | 一致。 |
| S3b (L203) | `len({...})==70` | 70 个名字互不相同。 | 一致。 |
| S3c (L219) | 两次名字含 `VectorClass@` | 两个名字都是 VectorClass 族（注意 `DynamicVectorClass` 也含子串 `VectorClass@`，name_of_vtable 的 split 对两者都切出元素类型）。 | 一致但弱：它实际上只断String包含，不断"一个是 Dynamic 一个是非 Dynamic"；那由 S3d 的 order_ok 单独做。 |
| S3d (L223) | `order_ok==35` | 每对象 w[0] 是 Dynamic、w[1] 是非 Dynamic 的 VectorClass。 | 一致。**但 order_ok 的判定只看了 w[0] 含 `DynamicVectorClass@` 且 w[1] 不含 Dynamic 而含 `VectorClass@`；它没验证"写序在时间上先 Dynamic 后 Vector"——w[0]/w[1] 是 `sorted(writes[e])` 按站点 VA 排序（L190），不是按执行流排序。所以该断言的名字"构造链基类->派生类"是解释性语言，字节层面只确证"低地址站点写的是 Dynamic vptr、高地址站点写的是 Vector vptr"。** |
| S3e (L233) | `same_elem==35` | split 出的元素类型字符串相同。 | 一致。 |
| S3f/S3g (L236/238) | 元素类型全 PAV、distinct==35 | 35 个元素类型互不相同且都是 PAV 指针。 | 一致。 |
| **S5a (L243)** | `all(x[0] is None for x in c1)`，c1 = `[name_of_vtable(u32(a+1) or 0) for a in EDX[:10]]` | 反控 1 取的是 **edx+1 处存放的 dword 当 vtable**，而 edx 是 BSS 地址、`u32()` 对 BSS 返回 None，所以传入的是 0；name_of_vtable(0) 读 u32(0xFFFFFFFF) 必然 None。 | **假反控。** 它验证的是"从 BSS 读不到字节"，不是"错位的 vtable 解析不出类名"。真正的对照应取一个**在 .rdata 里的 vtable 地址 +1** 再 name_of_vtable；所给 cond 对任何 EDX 都 PASS。 |
| **S5b (L247)** | `all(x[0] is None for x in c2)`，c2 = `name_of_vtable(vptr+4)` | 对前 10 个对象，把真实 vptr+4 当 vtable 起点。 | 这是**真反控**（vptr 在 .rdata，vptr+4 也在节内，读到的是 vtable 第二个槽，其 -4 处不是合法 COL，因此失败）。但只取前 10 个对象，不是 70 个。 |
| S5c (L251) | 真实 vptr 解得出 | 正控，前 10 个（每对象只取 w[1] 的 vptr）。 | 一致。 |

### r122b_allvec.py

| 检查 | cond | 实际验证 | 与名字是否一致 |
|---|---|---|---|
| **B0 (L94)** | `len(OBJ35)==35` | 把重扫的 37 站排除 0x67d193/0x67e62b 后，对每站 `rd(site-7,7)` 并 `struct.unpack_from('<I',b,1)` 取 edx；用 dict 去重得 35。 | **是弱反控/半重算。** 它确实从字节重新取了 edx（不是复制 r122a json），但**没有重新验证 `b[0]==0xba` 和 `b[5:7]==b'\x8b\xce'`**（r122a 的 S2e 有验），也没有断言 37-2=35 这个筛选前提是否仍成立。若某站前 7 字节形态变了，B0 会静默解出垃圾地址但仍可能凑出 35。与"重算得 35 个对象"的名字部分一致。 |
| A1 (L113) | `len(VEC_TD)>300` | 扫全节 `.?AV?$` 字串，正则 `^\.\?AV\?\$(Dynamic)?VectorClass@` 命中 396。 | 一致，弱断言（>300）。 |
| A2 (L115) | `len(VEC_TD)<len(TD_NAMES)` | 396 < 634。 | 与名字"比例"不符：cond 只断言子集关系（真子集），不计算也不约束比例。 |
| B1 (L168) | `sum(len(v) ...)>1000` | c7 05 写 BSS 站点数 >1000（实测 1777）。 | 一致，弱断言。 |
| B2 (L174) | `len(ALL_VEC_OBJS)>=35` | 至少 35 个目标曾被写入 VectorClass 族 vptr。 | **不一致/方向写反。** 名字是"全库 = 142 个"，cond 只验 ≥35。一个只找到 35 个的实现也会 PASS。这个断言无法支持 P4 的精确数字 142。 |
| B3 (L176) | `set(OBJ35)<=set(ALL_VEC_OBJS)` | 35 是全集子集。 | 一致。 |
| B4 (L179) | `len(EXTRA)>0` | 35 之外还有别的 VectorClass 目标。 | 一致，弱断言（>0 不能推出 107）。 |
| B5 (L198) | `all(v is not None ...)` | 35 个各恰有一个非 Dynamic VectorClass vptr。 | 一致。 |
| **B6 (L215)** | **`True`** | **什么都不验证。** 详情字符串打印 `n=103` 和 sample，但 cond 是字面常量。 | **不一致，是占位断言。** 它声称"决定 35 是否=全体该形态"，却对 n 没有任何约束：即使 n=0 也 PASS。103 这个数只在 JSON 的 `detail` 字符串里，不在 PASS/FAIL 里。 |
| **B7 (L218)** | `len(extra_dual)>0` | 至少有 1 个 35 之外的同形态对象。 | **与名字部分一致但结论过强。** 从">0"不能逻辑推出"特异性不在形态而在调用点"；只能推出"形态不是 35 独有的必要条件"。要支持"形态不能区分 35 与其余"，至少应断言 `len(extra_dual) > 100` 或给出比例；实测 103/107 的同形态率确实很高（见 A2），但这是我在复算里测的，B7 自己没测。 |

**A1 小结**：S2j 与 B6 的 cond 都是硬编码 `True`，是占位断言；S1d 是假反控；S5a 是假反控；B2/B4/B7 是方向或强度不足的断言，无法支撑它们名字所宣称的精确结论。真正强的断言是 S2e/S2f/S1b/S1c/S2i/S3a-e/S3g 和 S5b。

---

## A2 数字复算

全部来自 `audit_recalc.out`（独立脚本），不引用主会话 json。

| 主张 | 主会话数字 | 我的实测 | 一致性 |
|---|---|---|---|
| .data BSS 起止 | 0x87e000..0xb79be4 | 0x87e000 (= 0x812000+0x6c000) .. 0xb79be4 (= 0x812000+0x367be4)，size 3,128,292 | 一致。注意 upper bound 用了 `VirtualSize` 而非 `SizeOfRawData`，且 .data 的 VirtualSize > RawSize，所以这片确是未落盘区。 |
| 35 个 edx 全落在其中 | 35/35 | 35/35；regions = {('BSS','.data'):35}；min edx=0x887388，max=0xb72608 | 一致。 |
| 35 个 edx 互不相同 | 35 | 35 | 一致。 |
| 70 个类名互不相同 | 70 | 70 个全部 `.?AV` 解析成功，distinct=70；元素类型 distinct=35，全以 PAV 开头 | 一致。 |
| 全库 VectorClass 族全局静态对象 = 142 | 142 | 142（用写入侧路径独立重建：遍历全部 1777 个 c7 05 写 BSS 站点，把 imm32 当 vtable 经 COL→TD 反解，正则 `^\.\?AV\?\$(Dynamic)?VectorClass@` 命中，按写入目标去重） | 一致，可复算。 |
| 35 之外 107 个 | 107 | 142−35=107 | 一致。 |
| 103 个形态相同 | 103 | 独立复算：在 142 个全集里对**每个**目标按站点 VA 排序取所有可解析名，恰有 1 个 `VectorClass` 名 + 1 个 `DynamicVectorClass` 名且两者 split 出的元素类型相同者 = 138 个；其中 35 个是 EDX35，其余 **103** 个。复算输出 `EXTRA dual-form same-elem=103`，样例 0x87f5d8/PAVBombClass、0x87f5f0/PAVTechnoClass、0x87f658/PBVCommandClass 等。 | 一致，可复算。补充：主会话把"142"叫"全库 VectorClass 族全局静态对象"，但这个数只覆盖"被 c7 05 直接写 vptr 的 BSS 目标"；通过其他指令（如 `mov [addr], reg`、ctor 内联 `mov dword ptr [addr+off],imm` 或运行时才初始化）创建的 VectorClass 全局对象不在此列。P4 的措辞"全库"过宽，应改为"全库中**可由本扫描路径（c7 05 写 BSS vptr）观测到的**"。 |

复算命令：`cd /home/t628/projects/ra2-campaign-forge/_r122/audit && python3 audit_recalc.py`；原始输出在 `audit_recalc.out`。

---

## A3 过度推论审计：字节层面能确证到哪一步

### 能确证的（强字节锚点）

1. 35 个调用点前 7 字节实测形态如 `0x67df0f: ba 30 3e a8 00 8b ce e8 ...`（`mov edx, 0xa83e30; mov ecx, esi; call rel32`）——edx 立即数是硬编码在 .text 里的，35 个互不相同。
2. 每个 edx 地址在 BSS 虚拟区内；全 .text 扫描 `c7 05 <addr>, imm32` 恰好命中每个 edx 两次，例如 0xa83e30 在 `0x4e6e7d: c7 05 30 3e a8 00 a4 9f 7e 00` 与 `0x4e6ea8: c7 05 30 3e a8 00 c4 9f 7e 00`，Capstone 实测反汇编就是 `mov dword ptr [0xa83e30], 0x7e9fa4` / `..., 0x7e9fc4`。
3. 两个 imm32 (0x7e9fa4, 0x7e9fc4) 均在 `.rdata`，按 `[vt-4]=COL → COL+12=TD → TD+8=name` 解出 `.?AV?$DynamicVectorClass@PAVFactoryClass@@@@` 与 `.?AV?$VectorClass@PAVFactoryClass@@@@`。70 个全部成功，35 个元素类型互异。

### 能区分"写 vptr"与"恰好写了一个等于该地址的常量"吗

两个场景字节上**可以区分**，判据是 imm32 与写入目标的角色：

- 场景 X（主会话）：`c7 05 <edx>, <vtable>`——目标操作数 = edx 地址，imm32 = .rdata 里的 vtable。检查 imm32 能否走 RTTI 链解出 `.?AV...`。
- 场景 Y（替代）：某处 `c7 05 <某 BSS>, <edx>`——即 edx 值作为 imm32 被写到别处。检查的是 imm32 是否等于某个 edx。

主会话实际验证了 X（imm32 走 RTTI 成功），**没有直接排除 Y**。我额外做了一个扫描：全 .text 找所有 `c7 05` 写 BSS 站点，检查 imm32 是否等于 35 个 edx 中的任一个——**命中 0 个**。所以在这份二进制里 Y 路径不存在，35 个 edx 不是作为常量被写到别处。这是主会话没明确写、但事实支持的补强。

### 不能确证的（过度推论）

- **"这些对象是保存器模板的实参"** —— 这超出了字节层面。字节能确证的是：35 个不同的 BSS 地址被 35 个不同调用点以 `edx=imm32` 传入，且这 35 个地址各自被写入一对同元素的 Dynamic/Vector vtable。从"edx 指向全局 VectorClass 容器"到"它们是保存器模板的实参"还需要额外证据：例如被调函数体内 `mov eax,[edx]` 后的 vtable 虚调用模式、或调用点所在函数的符号/命名。**脚本里没有这一步**（S2/S3 都只看了调用点前置字节和 BSS 写入，没有反汇编 35 个字节全同的孪生函数体去验证它如何使用 edx）。R121 的"35 个字节全同孪生"是前提，但 R122 没有从孪生函数体侧建立"edx 被当容器用"的证据。
- **"先 Dynamic 后 Vector 的构造链"** —— 字节只证明低地址站点写 Dynamic、高地址站点写 Vector（按站点 VA 排序），不等于执行序。S3d 的"构造链基类->派生类"是合理猜测，未被静态证据直接确证。
- **"静态存储，非栈"** —— 对 BSS 地址这成立（BSS 不在栈上），但"全局"的语义（extern/static/类内 static 成员）在 stripped exe 里无法区分；B0/B2 的"全局静态对象"应降级为"BSS 中的对象"。

---

## A4 漏掉的解释

主会话的推导链是：35 个不同 edx → 每个被写 2 次 vptr → 两个 vptr 同元素 → 全局 VectorClass 容器。能同时满足这三个字节事实的**替代解释**至少有以下几类，脚本未排除：

1. **同一对象的两个不同子对象/基线**——一个 BSS 地址同时是 DynamicVectorClass 实例的 this 和内嵌 VectorClass 子对象的 this（MSVC 单继承下首地址相同，两个 vptr 写同一地址是构造/析构链的正常现象）。这与"一个对象有两个 vptr 槽"在字节上无法区分，两者都是"全局容器对象"的变体，不影响 P1 的核心，但影响"每对象恰好 2 次写入"的语义解读。

2. **静态数组/结构体中相邻的 VectorClass 成员被同一地址重用**——35 个 edx 互不相同只说明 35 个地址不同；它们可能是一个大数组里的元素步长（例如每 0x14 一个 VectorClass），而不是 35 个独立全局符号。实测 EDX min=0x887388、max=0xb72608，跨度约 3 MB，稀疏分布，看起来更像独立对象；但脚本没有分析地址间间隔分布或相邻 BSS 对象的布局，无法从字节排除"结构体成员数组"解释。

3. **编译器生成的 vtable 初始化桩共用同一写入模板**——"每个地址被写 2 次"可由两个独立的初始化函数（各写一次）造成，而不必是"同一对象的构造链 Domino"。S3d 的"构造链"解读依赖"两个站点 VA 相邻且分别写 Dynamic/Vector"（实测如 0x4e6e7d 与 0x4e6ea8 仅相隔 0x2b 字节），这是强旁证但不是证明：两个独立初始化函数也可能被编译器放在相邻位置。

4. **35 个对象不是"保存器模板的实参"而是"保存器模板的返回值缓冲/输出参数"**——edx 作为 `this` 传入与被调函数把结果写回 edx 指向的对象，在 x86 调用约定里字节形态相同（都是 `mov edx, addr; call`）。要区分必须看被调函数体对 `[edx]` 的读写方向，r122a/r122b 都没做。

主会话为何没排除：S2/S3 只分析调用点的前置字节与 BSS 写入站点，没有反汇编 35 个孪生函数体、没有检查 edx 在函数内是否被写、没有检查 35 个地址之间的内存布局。这些解释中 (1)(3) 不改变 P1-P3 的核心计数，(4) 直接冲击"保存器模板实参"的推论——这是必须降级的部分。

---

## A5 1436/1777 归因审计

**主张 P5 的因果归因错了，数字本身部分对。**

### 实测分类（1777 个 c7 05 写 BSS 站点的 imm32）

独立复算，完整分类（我的复算第 14 行 + 后续专门分类脚本）：

| 类别 | 数量 | 说明 |
|---|---|---|
| `no-COL`（`u32(vt-4)` 取不到） | 1399 | imm32 落在无文件字节处，无法读 `COL` 指针 |
| `no-COL-body`（COL 地址可解析但 COL 内容不可读） | 33 | imm32 在 `.text`/`.data RAW`，例如 0x4093c0、0x822bc4 |
| `bad-COL`（sig≠0 或 td=0） | 4 | imm32=0x808080 / 0x807a68，在 `.rdata` 内，只是指向非 RTTI 数据 |
| 解析成功 `.?AV...` | 341 | 其中 288 命中 VectorClass 族、53 是其他 RTTI 类（LogicClass/MouseClass/GenericList 等） |
| 合计 | 1777 | |

主会话把"反解不出类名"记为 1436 = 1399 + 33 + 4， Arithmetic 对；但**把它整体归因为"imm32 落在节外（NOWHERE，1379 个）"是错的**。实测：

- 在 1399 个 `no-COL` 中，只有 **1379** 个 imm32 确实不落在任何节（NOWHERE）；另 **20** 个落在 `.data BSS`（如 0x87e2c0、0x87e4e0），只是 BSS 无文件字节所以取不到 COL。
- 33 个 `no-COL-body` 全部落在**节内**（`.text RAW` 22 个、`.data RAW` 11 个），不是节外。
- 4 个 `bad-COL` 全部落在 `.rdata` 内，也不是节外。

### 1436 个失败 imm32 的 VA 区间直方（其中 NOWHERE 占 1379；实测）

| 区间 | 个数 | 说明 |
|---|---|---|
| [0x00000000, 0x00400000) < ImageBase | **1236** | 全是小整数常量：0 出现 740 次、10 出现 155 次、1 出现 103 次、2 出现 40 次……典型 `mov [addr], 0` 清零/计数赋值，不是 vptr |
| [0x00400000, 0x007e1000) `.text` 及前导间隙 | 22 | 属于 `no-COL-body` 类，不是 NOWHERE；此处列出仅为区间全貌 |
| [0x007e1000, 0x00811074) `.rdata` | 4 | 属于 `bad-COL` 类 |
| [0x00812000, 0x0087e000) `.data RAW` | 11 | 属于 `no-COL-body` 类 |
| [0x0087e000, 0x00b79be4) `.data BSS` | 20 | 落在 BSS，读不到 COL |
| [0x00b79be4, 0x00b7a000) | 0 | 间隙 |
| [0x00b7a000, 0x00b92128) `.rsrc` | 0 | — |
| [0x00b92128, 0x00b93000) | 0 | 间隙 |
| [0x00b93000, 0x00b95718) `.detour` | 0 | — |
| [0x00b95718, 0x00b96000) 节尾到 ImageEnd | 0 | — |
| **[0x00b96000, 0xffffffff] > ImageEnd(=VA 0xb96000)** | **143** | 0xffffffff 出现 52 次、0x99999999 出现 24 次、0x3fcccccc 及 0x3fd66666 各 12 次等；也全是常量填充值 |

精确归属（1436 个失败 imm32）：1379 个不在任何节内——1236 个 **低于 ImageBase**（小整数），143 个 **高于 ImageEnd**（0xffffffff/0x99999999 等哨兵），0 个落在 "ImageBase..ImageEnd 但不属于任何节" 的间隙；另 57 个在节内（20 `.data BSS` + 22 `.text RAW` + 11 `.data RAW` + 4 `.rdata`）。

所以 P5 的"节外"表述需要拆开：这 1379 个确实不在任何节内，但其中 1236 个是"低于镜像基址的小整数常量"，143 个是"高于镜像末尾的哨兵值/常量"，并非主会话暗示的"随机节外地址"。而 1436 个反解失败里还有 57 个**在节内**（20 BSS + 22 .text + 11 .data RAW + 4 .rdata），根本不是"节外"。

### 具体反例

- 001: `target=0x0087e848, site=0x00409393, imm=0x004093c0` —— imm 在 `.text` 节内，反解失败（no-COL-body），不是节外。
- 002: `target=0x00ac4628, site=0x006005b0, imm=0x00808080` —— imm 在 `.rdata` 节内，失败原因是 bad-COL，不是节外。
- 003: `target=0x0087e73c, site=0x00406b2e, imm=0x0087e2c0` —— imm 在 `.data` BSS 内，失败原因是 BSS 无字节，不是"节外"。
- 004: `target=0x0087e278, site=0x00403eb5, imm=0x00000000` —— imm=0，NOWHERE，是清零常量。

结论：1436/1777 的"反解不出"**主要**是小整数/哨兵常量，归因"写非指针常量"方向正确；但"原因是这些 imm32 落在节外（NOWHERE，1379 个）"这句话把 1379 当成了 1436 的同义词，忽略了 57 个节内失败，也没有细分 1379 的组成。**应改写。**

---

## 主会话必须改的

1. **S2j（r122a L162）cond 从 `True` 改为实断言**，例如 `Counter(len(v) for v in writes.values())[2] < len(writes)`，并在 detail 里保留直方。当前 PASS 是假的。
2. **B6（r122b L215）cond 从 `True` 改为实断言**，例如 `len(extra_dual) >= 100`（或断言 `len(extra_dual)/len(EXTRA) > 0.9`）。当前 PASS 是假的，103 这个数没有通过断言验证。
3. **B7 的结论句降级**：从"因此 35 个的特异性不在形态而在调用点"改为"35 之外的 107 个中有 103 个同形态，故形态不足以单独区分 35 个；是否调用点特异需另证"。B7 的 cond 只验 `>0`，不支持原句强度。
4. **B2 的条件加强或改述**：`>=35` 不能支撑"全库=142"。要么改为 `==142`（把 142 变成可证伪断言），要么把主张中的"=142"改为"扫描路径观测到 142 个"，并说明该数只覆盖 c7 05 写 BSS 路径。
5. **P4 里"全库"改为"c7 05 写 BSS 路径可观测到的"**：这是 142 这个数的真实口径，D3(3) 的分析表明其他初始化路径未覆盖。
6. **P5 整句撤回重写**：原句"1436 个反解不出 RTTI 类名，原因是这些 imm32 落在节外（NOWHERE，1379 个）"——1436 中有 57 个 imm 在节内（20 BSS + 22 .text + 11 .data RAW + 4 .rdata），1379 个 NOWHERE 里 1236 个是 <0x400000 的小整数、143 个是 >0xb96000 的哨兵。改为："1436 个反解失败中 1379 个 imm 不在任何节内（1236 个为 <ImageBase 的小整数常量、143 个为 >ImageEnd 的哨兵值），另 57 个在节内但 COL 不可读或非 RTTI；整体符合'非 vptr 常量写入'，但'全部节外'不成立。"
7. **S1d 标记为自证冗余**：它验证 `rd()` 对 BSS 返回 None，不是二进制证据；建议删掉或改名为"rd helper BSS guard smoke test"，不要当反控引用。
8. **S5a 标记为假反控并重做**：当前 c1 取的是 BSS 里的 dword（None→0），与 vtable 错位无关。应改为对真实 vptr 列表做 `vt+1` 的 name_of_vtable 反控（与 S5b 的 vt+4 平行）。
9. **"保存器模板实参"这句话降级为工作假设**：字节层面目前只确证"35 个不同 edx 指向 BSS 中 35 个被写双 vptr 的容器对象"；"是模板实参"需要补一段对 35 个孪生函数体的反汇编（看 edx 是被读还是被写、虚调用偏移），否则应从结论里拿掉。
10. **"构造链基类->派生类"降级为推测**：S3d 按站点 VA 排序，非执行序；改为"低址站点写 Dynamic、高址站点写 Vector"。

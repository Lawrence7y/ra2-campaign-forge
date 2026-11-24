# R123 跨家族审计 · hy4 审计员报告

审计对象：`_r123/r123a_a4_verdict.py` + `r123a_a4_verdict.json`（30 条断言，`all_ok=true`）
审计纪律：只读、独立脚本复算、流式 disasm_lite、单次带 timeout。所有复算命令/输出列在文末。

---

## A1 逐条核对 30 个断言：名字 vs cond 是否一致

### 重点质疑项结论

| 编号 | 断言名 | 结论 | 依据 |
|---|---|---|---|
| T1d | 全库存在 this-offset != 0 的 vptr | **口径有严重噪声，但反控方向成立** | 主脚本扫 `.rdata` 每 4 字节，把任意 dword 当 COL 指针。复算得 632 个 `sig==0 && off!=0 && pTD!=0`，但样例含明显垃圾：`vt=0x7e1210, COL=0x40f834, off=2122956851, pTD=0x6e89c094`（0x40f834 在 .text，不是 COL）。加严口径（pTD 必须是合法 TypeDescriptor：sig=`0x7f9594`、名字以 `.?AV` 开头、CHD/nBase 合法）得 **1212 个合法 vtable，其中 260 个 mdisp!=0**（例 `vt=0x7e1f24, COL=0x7fafd8, off=12, td=.?AV...`）。T1b 的鉴别力确实存在，但 632 这个数不可引用。 |
| T2f | 同一单元两次写同一 BSS 地址 = 18 | **数字精确，但口径偏窄** | 独立复算得 `c705 targets=1142, sites=1748, same_unit_twice=18, our_hits=0`，与主脚本一致。但 cond 只统计 `len(ss)==2` 且仅 `c7 05` 指令；`len(ss)>2`（239 个目标）和 `c6 05`/`a3` 写法被忽略。作为「存在反例目标」够用，但不能称「全库恰好只有 18 个重复写目标」。 |
| T2g | 相邻间隔取 31 种不同值 | **31 是精确值，脚本判据却是弱下界** | 独立复算 `distinct=31`（min=24, max=1884280），31 是精确统计值。但断言 cond 写的是 `len(gap_kinds) >= 20`，即脚本只验了下界；名字说「31 种」，cond 只保证「≥20 种」。应把 cond 改成 `==31` 或在 detail 里注明精确值来源。 |
| T3a2 | 不归一化 OWNDTOR 时分成 35 份 | **可被更强归一化绕过，鉴别力有限** | 实测 35 个对象全部 `du == cu + 0x40`。主脚本的 `norm_body` 只在 `v == own_dtor` 时打 `OWNDTOR`，关掉后该立即数变 `CODE:du`，自然 35 个不同值 → 35 份。若归一化规则改成「距单元起点 +0x40 内的 .text 地址一律打 `NEARDTOR+0x40`」，复算 `distinct ctor = 1`（`/tmp/norm_probe.py`）。故 T3a2 只证明「采用了一套能抹平差异的归一化」，不是「不归一化时天然 35 份」的稳健反控。 |
| T3e | 每项要么 0 要么 .text 指针 | **无第三分支被吞，正确** | 精确复算表 `[0x812000,0x815da4)` 共 3945 项：0 值 1 个，`.text` 指针 3944 个，其他 0 个。classification 无 rdata/data/other。 |
| T3m | 全库存在一个单元写 >=2 个 BSS 目标 = 337 | **与 T3k 不矛盾** | 独立复算 `multi_units=337`，hist `{1:780, 2:225, 3:54, ...}`。T3m 统计全库所有单元写任意 BSS 目标；T3k 只统计 35 个 ctor 单元写「这 35 个目标地址」。独立复算 T3k `hist={1:35}`。两者口径不同，337 恰恰证明 T3k 的判据不是恒真。 |

### 其余断言

- A0a 线性扫描覆盖：独立复算 `insns=1394186, last_end=0x7e1000=TE`，一致。
- A0b 单元切分自检：`unit(0x40ee5d)=0x40ee40, unit(0x40ee88)=0x40ee80`，合理。
- A1a 输入 35 对象、A1b 两处 vptr 可解 COL/类名：独立复算 35/35，一致（但见下方 A2 对 T1a 实现的重大更正）。
- T1b 两处 mdisp=0：**35/35 正确**（按 x86 COL 布局 `sig,+4 off,+8 cd,+12 pTD,+16 pCHD,+20 pSelf` 解析，COL @0x801610/0x801640 原始字节实证）。
- T1c 元素类型相同：复算 35/35 正确（`.?AV?$DynamicVectorClass@PAVX@@@@` → `.?AV?$VectorClass@PAVX@@@@`）。
- T2a 字段集 `(0,4,8,12,16,20)`：复算 35/35 完全一致。
- T2b 尺寸 24：见 A2 第 3 点，应降级为「≥24」。
- T2c 最小间隔 24 ≥ 24：正确。
- T2d/T2e 35 个独立 ctor/dtor 单元、无交集：与复算一致。
- T2h 相邻 +24 同类型对 = 0：复算 3 对相邻（0xa83d68/80/98、0xa8e318/330），确实元素类型不同，cond 方向正确。
- T3a 归一化 ctor 骨架唯一 = 1：独立复算确认（`/tmp/norm_probe.py` 用同规则得 1）。
- T3b 短形态 dtor 64 字节 33 个归一化唯一：与 json 一致。
- T3c 长形态 96 字节 2 个差异是守卫字节：实证 `0x4c5250: mov cl,[0x8a3818]`、`0x4d0790: mov cl,[0x8b3cd5]`，两地址在 .data BSS（无文件映射），在对象窗口外，正确。
- T3d CRT 表区间：实证 `0x7cbdcf: push 0x812000`、`0x7cbdd2: push 0x815da4`、`call 0x7cbed4`，由立即数直接给出。遍历函数真实形态是 `for(esi=begin; esi<end; esi+=4) if(*esi) call [*esi]`（`0x7cbed4` 实测反汇编），与主脚本注释的 `mov [ebp+8]` 栈变量形态不同但功能等价。
- T3f 非零项互不相同：3944/3944，正确。
- T3g 35 ctor 全在表内：独立复算 `all 35 in table, idx 177..3586`，正确。
- T3h 下标序单调：正确。
- T3i atexit 注册 35/35、总 308：独立复算 `regs=308, registered=35`，一致。
- T3j 截断反控 34：与 json 一致。
- T3k 每 ctor 写恰好 1 个目标：独立复算 `hist={1:35}`，一致。

---

## A2 数字复算（独立脚本，不引用主会话 json 作为数据源）

### 1. 35 个对象两处 vptr 的 RTTI 基类关系（逐个表）

**主脚本实现有重大 bug**：`class_bases()`（r123a_a4_verdict.py:167）把 BaseClassArray 里的 `pBaseClassDescriptor` 直接当 `pTypeDescriptor` 传给 `td_name()`。实测首个对象 `0xa83e30`：CHD @0x801600, nBase=2, pbase=0x8015f0, raw = `[0x8015d8, 0x8015c0]`；正确路径是 `pTD = u32(pBaseDescriptor)`：`u32(0x8015c0)=0x8234b0` → `.?AV?$VectorClass@PAVFactoryClass@@@@`。主脚本却对 `0x8015c0+8` 取字符串，得到空串 `''`。因此主脚本 T1a 的 `n2 in b1` 是 **假阳性**（两侧都是空串匹配）。

我用正确解析独立复算（`_r123/audit/rtti_recheck.txt`，35 行逐个表），结果：

```
obj=0xa83e30: .?AV?$DynamicVectorClass@PAVFactoryClass@@@@ -> .?AV?$VectorClass@PAVFactoryClass@@@@
  base names = ['.?AV?$DynamicVectorClass@PAVFactoryClass@@@@', '.?AV?$VectorClass@PAVFactoryClass@@@@']
  mdisp = 0,0 ; elem_norm_equal = True
... （35 行全部同形态）
TOTAL correct: base=35 off=35 elem=35 of 35
```

**结论**：结论碰巧正确（35/35 基类关系成立），但主脚本的证据链是坏的。必须修 `class_bases()` 并重跑。

### 2. x86 COL 布局核对

主张的布局 `sig,+4 this-offset,+8 cdOffset,+12 pTD,+16 pCHD,+20 pSelf` **正确**。实证 COL @0x801610 原始 24 字节：

```
00 00 00 00 | 00 00 00 00 | 00 00 00 00 | e0 34 82 00 | 00 16 80 00 | c0 15 80 00
sig=0, off=0, cd=0, pTD=0x8234e0, pCHD=0x801600, pSelf=0x8015c0
```

CHD @0x801600: `sig=0, attr=0, nBase=2, pBaseArray=0x8015f0`。BaseClassDescriptor @0x8015c0 原始 24 字节：`b0 34 82 00 00 ...` → `pTD=0x8234b0` → VectorClass。这是标准 MSVC x86 RTTI，没有拿 x64 三段 int32 来否 x86 结论。

### 3. 对象尺寸 24 的推导链是否唯一

独立复算 T2a：35 个 ctor 写的字段偏移集全部 `(0,4,8,12,16,20)`，max=20 → `size >= 24`。但这是**下界**：字段集只覆盖被写字段，对象可能有未写的尾部填充/字段（例如 vftable 后还有 4 字节未初始化成员）。主会话句子「对象尺寸由构造函数体实际写的字段偏移上界推出为 24 字节」应降级为「至少 24 字节；结合 min_gap=24 与 CRT 表逐项注册，实际占用不小于 24」。推导链不唯一。

### 4. CRT 初始化表区间是否由立即数给出 / 遍历函数形态

实证（`0x7cbdb0` 附近反汇编）：

```
007cbdbb push 0x815dbc
007cbdc0 push 0x815da8
007cbdc5 call 0x7cbed4      ; 第二段
007cbdd2 push 0x815da4
007cbdd4 push 0x812000
007cbdd9 call 0x7cbed4      ; 目标段 [0x812000, 0x815da4)
```

`0x7cbed4` 实测反汇编：`mov esi,[esp+8]; cmp esi,[esp+0xc]; jae done; mov eax,[esi]; test eax,eax; je next; call eax; next: add esi,4; jmp loop`。是 `for(p=begin;p<end;p+=4) if(*p) (*p)();` 形态，**区间确由 push imm32 给出**。主脚本注释写的栈变量 `[ebp+8]` 形态与二进制不符，但 T3d 检出的区间和调用点正确。

### 5. 35 个 ctor 是否真在表里各占一项

独立复算：35/35 全部在表内，下标 177..3586，按 ctor 地址序单调。成立。

---

## A3 过度推论审查

| 原句 | 能否推出 | 处理 |
|---|---|---|
| 「35 份骨架相同 ⇒ 同一模板展开」 | **只能推出**「归一化后指令骨架同构」。C++ 模板展开、手写复制粘贴、宏展开、编译器 COMDAT 合并都能产生同构骨架。骨架同构是必要条件不是充分条件。 | 降级为「与同一模板展开一致」，不得写成「证明确实是同一模板展开」。 |
| 「35 个独立 CRT 表项 ⇒ 35 个独立对象」 | 表项证明的是 **35 个独立初始化函数单元**，不是 35 个独立对象。一个对象可以有多个初始化单元；35 个对象也可以共用一个初始化单元（数组）。结合 T3k（每单元只写 1 个目标）和 T2d（35 个不同 cu）才使「35 个独立对象」成立。 | 降级：表项本身只证「独立初始化单元」。 |
| 「独立翻译单元产物」 | 字节里没有源文件/translation unit 信息。CRT 表项通常对应 COMDAT/obj 文件，但不能从指针表反推源码 TU 数量。 | **必须撤回**「独立翻译单元」这个说法，改为「独立 CRT 初始化表项」。 |
| 「对象尺寸 = 24」 | 仅由字段上界得 ≥24。 | 降级为「≥24，且与 min_gap=24 一致」。 |
| T1a 的「第二个类在第一个基类表里」 | 结论正确但实现假阳性（见 A2-1）。 | 必须修实现并重跑，否则证据无效。 |

---

## A4 漏掉的解释（第四类）

能同时满足「35 互异地址 / 每地址写 2 次 vptr / 两类成基类关系 / 35 独立 ctor 单元 / 35 独立 CRT 表项」的第四类解释：

1. **同一模板的 35 次显式实例化（explicit instantiation）/ 手动复制的 35 份全局对象**——这其实与「35 个独立对象」不冲突，只是说明来源可以是同一模板或手工复制。主会话把它当作 ③「共用模板」已定性（部分成立），没有排除它是对的；但没写清「模板展开 ≠ 非独立对象」。

2. **CDTOR 冷/热拆分或 COMDAT 折叠后保留两份表项**——若同一对象的 ctor 被拆成两个单元，会满足独立表项但地址只有一个，与「35 互异地址」矛盾，排除。

3. **类数组 + 每元素独立 ctor thunk**——MSVC x86 对全局类数组生成一个循环 ctor + 一个 CRT 表项，不会产生 35 个表项。当前字节形态（35 个表项、每单元写 1 个绝对地址）不支持这个解释。主会话 T2d/T3g 实质排除了它，但没有明说。

**主会话为何没排除 1**：因为它把「同一模板展开」和「独立对象」错误对立起来（A3）。共用模板在 C++ 里完全能产生 35 个独立全局对象，各占 CRT 表项。正确的表述应是「模板展开成立，且每次展开是独立对象」。

---

## A5 自错登记诚实性

| 编号 | 登记内容 | 脚本痕迹 | 复算确认 |
|---|---|---|---|
| S-102 | 归一化没做完就得 35 份不同却当事实 | r123a_a4_verdict.py:308-316 注释；`norm_body` 显式命名 OWNDTOR/ATEXIT/VPTR/REL | 复算 `hc=1`（修正后），`h_no_own=35`（反控），可复算。 |
| S-103 | vptr 在 .rdata 被标 IMM 没抹掉 | :359 注释；`blank_vptr` 匹配 `('IMM:','CODE:')` 两种标签 | 复算 ctor 骨架唯一=1，可复算。 |
| S-104/S-105 | 守护地址解析进制错 | :404-409 注释；`guard_addrs` 对 `base_ in (10,16)` 两种都试 | 复算 `guards=[0x8a3818],[0x8b3cd5]`，两者确在 BSS 且在对象窗口外，可复算。 |
| S-106 | 判据方向错（用 a+24 是否被写判成员数组） | :447-450 注释；新增 T2h 查同类型相邻对 | 复算 `adjacent_pairs=3, same_type=0`，cond 方向正确。 |

**结论**：5 条都在脚本里留下了可复算痕迹，不是嘴上认错。但新增的 bug（T1a 的 `class_bases` 解错指针、T1d 的噪声扫描）**没有被登记**，属于新的自错，必须补登 S-107/S-108。

---

## 主会话必须改的

1. **撤回/修复 T1a 的证据链**：`r123a_a4_verdict.py:167` 的 `class_bases()` 把 `pBaseClassDescriptor` 当 `pTypeDescriptor`，得空串假阳性。必须改成 `pTD = u32(pBaseDescriptor)` 后重跑；结论（35/35）预计不变，但当前证据无效。补登 S-107。
2. **T1d 的 632 必须降级/替换**：该数含大量垃圾命中（如 `off=2122956851, pTD=0x6e89c094`），不能作为反控数字。改用严格口径：合法 TD sig=`0x7f9594`、名字 `.?AV`、CHD 合法 → 1212 个合法 vtable 中 260 个 mdisp!=0。补登 S-108。
3. **T2g 的断言 cond 与名字对齐**：名字说「31 种」，cond 写 `>=20`。改成 `==31` 或把名字改成「至少 20 种」。
4. **T2f 的数字加口径限定**：「18」只统计 `len(ss)==2` 的 `c7 05` 写。句子应加「按 c7 05 且恰好两次、同一单元的口径」。
5. **T3a2 降级**：`du-cu==0x40` 使更强归一化可把 35 份塌成 1，该反控不是稳健的「非恒真」证明。改述为「在当前归一化规则下，OWNDTOR 项确实是唯一使骨架分叉的参数」。
6. **对象尺寸 24 → ≥24**：字段上界只给下界。
7. **撤回「独立翻译单元」**：改为「独立 CRT 初始化表项」；「35 份骨架相同 ⇒ 同一模板展开」改为「与同一模板展开一致」。
8. **CRT 遍历函数注释纠错**：主脚本注释写的栈变量形态与 `0x7cbed4` 实测不符，改成 `esi` 指针递增形态。
9. **补登 A4 第四类解释**：显式实例化/手工复制的 35 份全局对象——共用模板与独立对象并不互斥，主会话的对立表述须修正。

---

## 复算命令与产物

- `python3 /tmp/mdisp_scan.py`（精确复现 T1d 632）
- `python3 /tmp/mdisp_strict2.py`（严格口径 260 / 1212）
- `timeout 480 python3 -u /tmp/insn_recheck.py 2>&1 | tee _r123/audit/insn_recheck.txt`（INS/单元/gaps/T2f/T3m）
- `python3 - <<...>>`（RTTI 正确解析，输出 `_r123/audit/rtti_recheck.txt`）
- `timeout 240 python3 -u /tmp/writecheck.py`（T3k 复算）
- `timeout 120 python3 -u /tmp/norm_probe.py`（T3a2 更强归一化）
- `timeout 60 python3 -u /tmp/table_check.py`（CRT 表项/单调）
- `timeout 240 python3 -u /tmp/atexit_check.py`（atexit 308/35）
- `python3 - <<...>>`（CRT 遍历函数 + 守卫字节 + COL 原始字节 dump）

所有复算均为只读；`_r123/audit/` 下仅新增本报告与两份 `.txt` 输出，未修改任何既有文件。收口时 `ps` 确认无孤儿复算进程残留（两个 timeout 进程均正常退出）。

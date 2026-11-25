# R132 审计报告（deepseek 侧 / 独立复算）

对象：`/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe`
PE32，ImageBase 0x400000，`.text`：VA 0x401000，raw 0x1000，可在内存映射长度 0x3df38d（`min(Misc_VirtualSize, SizeOfRawData)`）。
本报告全部数字由本目录脚本自行产出；脚本与原始输出：`a_cfg.py` / `a_cfg.json` / `a_cfg.out`、`a5_else.py` / `a5_else.json`、`b_diff.py` / `b_diff.json`、`c_census.py` / `c_census.json`、`d_xcheck.py`、`e_supp.py` / `e_supp.out`、`run.log`。
跨引擎佐证：`i686-w64-mingw32-objdump -d -z`。

---

## 任务 A：函数真实边界

### A1/A2/A3 命令与输出

```
$ python3 a_cfg.py
```

```
A {'entry': '0x6bedb0', 'cfg_len': 136, 'cfg_max_end': '0x6bee38', 'visited_insn_count': 56,
   'first_ret_len': 106, 'first_ret_end_va': '0x6bee1a', 'else_cfg_len': 30,
   'else_cfg_max_end': '0x6bee38', 'else_visited': 12}
B {'entry': '0x41c250', 'cfg_len': 136, 'cfg_max_end': '0x41c2d8', 'visited_insn_count': 56,
   'first_ret_len': 106, 'first_ret_end_va': '0x41c2ba', 'else_cfg_len': 30,
   'else_cfg_max_end': '0x41c2d8', 'else_visited': 12}
```

遍历规则：从入口入栈，`ret`/`ret imm` 不再产生后继；条件跳转（je/jl 等）压入「目标 + 顺序下一条」；`jmp` 只压入目标；其余（含 `call`、`loop` 之外普通指令）压入顺序下一条。第二套独立实现（`d_xcheck.py`，改用 `md.disasm_lite`、后继处理代码另写）复算结果相同：

```
$ python3 d_xcheck.py
xcheck CFG A: cfg_len=136 first_ret_len=106 visited=56 max_end=0x6bee38
xcheck CFG B: cfg_len=136 first_ret_len=106 visited=56 max_end=0x41c2d8
```

| 项 | 0x6bedb0 (A) | 0x41c250 (B) |
|---|---|---|
| CFG 最大结束地址 | 0x6bee38 | 0x41c2d8 |
| CFG 真实长度 L | **136** (0x88) | **136** (0x88) |
| 访问到的指令条数 | 56 | 56 |
| CFG 内 ret 指令 | 0x6bee17 `ret 0xc`、0x6bee35 `ret 0xc` | 0x41c2b7 `ret 0xc`、0x41c2d5 `ret 0xc` |
| 跳出 [entry, hi) 范围的分支数 | 0 | 0 |
| 「到第一条 ret 为止」长度 | 106 | 106 |

### A4 第一条 ret 之后的跳转

```
$ python3 a_cfg.py | grep -A8 jumps_at_or_beyond_first_ret
```

A（第一条 ret 结束于 0x6bee1a）：

| 跳转指令地址 | 助记符/操作数 | 目标 | 目标处指令助记符 |
|---|---|---|---|
| 0x6bedc6 | `je 0x6bee1a` | 0x6bee1a | `mov ecx, dword ptr [esp + 0xc]` |
| 0x6bede5 | `jl 0x6bee33` | 0x6bee33 | `pop edi` |

B（第一条 ret 结束于 0x41c2ba）：

| 跳转指令地址 | 助记符/操作数 | 目标 | 目标处指令助记符 |
|---|---|---|---|
| 0x41c266 | `je 0x41c2ba` | 0x41c2ba | `mov ecx, dword ptr [esp + 0xc]` |
| 0x41c285 | `jl 0x41c2d3` | 0x41c2d3 | `pop edi` |

即两条向前跳（`je` 到 else 块入口、`jl` 直接跳到第二条 ret 前）都落在第一条 ret 之后。106 vs 136 的差是 30 字节，与 else 块长度相等。

objdump 对齐复核（原始输出片段）：

```
  6bedc0:	8b 44 24 14          	mov    0x14(%esp),%eax
  6bedc4:	a8 14                	test   $0x14,%al
  6bedc6:	74 52                	je     0x6bee1a
  ...
  6bedd1:	68 c0 7b 81 00       	push   $0x817bc0
  ...
  6bede5:	7c 4c                	jl     0x6bee33
  ...
  6bee13:	8b c6                	mov    %esi,%eax
  6bee15:	5f                   	pop    %edi
  6bee16:	5e                   	pop    %esi
  6bee17:	c2 0c 00             	ret    $0xc
  6bee1a:	8b 4c 24 0c          	mov    0xc(%esp),%ecx
  ...
  6bee33:	5f                   	pop    %edi
  6bee34:	5e                   	pop    %esi
  6bee35:	c2 0c 00             	ret    $0xc
  6bee38:	90                   	nop
```

### A5 反控：else 块单独遍历

```
$ python3 a5_else.py
A {'cfg_len': 136, 'first_ret_len': 106, 'boundary': '0x6bee1a', 'else_len': 30,
   'else_lo': '0x6bee1a', 'else_hi': '0x6bee38', 'else_insn_count': 12,
   'else_escape_jumps': [], 'cfg_insn_count': 56, 'total_gap': 30}
B {'cfg_len': 136, 'first_ret_len': 106, 'boundary': '0x41c2ba', 'else_len': 30,
   'else_lo': '0x41c2ba', 'else_hi': '0x41c2d8', 'else_insn_count': 12,
   'else_escape_jumps': [], 'cfg_insn_count': 56, 'total_gap': 30}
```

else 块 CFG：A 长度 30（0x6bee1a–0x6bee38，12 条指令，无向外跳转），B 长度 30（0x41c2ba–0x41c2d8，12 条指令，无向外跳转）。
106 + 30 = 136：两段互不重叠、拼接正好等于 CFG 真实长度。「到第一条 ret 为止」= 前半分支；真实长度 = 前半分支 + else 分支。

补充实测（不参与上表推导，仅记录）：两个 CFG 结束地址之后都紧跟 8 个 0x90 填充字节，填充之后即为下一条函数的入口：

```
after 0x6bee38: 8 continued 0x90 bytes, next bytes 8b c1 c7 40 04 00 00 00   (即 0x6bee40: mov %ecx,%eax)
after 0x41c2d8: 8 continued 0x90 bytes, next bytes 83 ec 08 56 8b f1 83 ec
```

结论性数字（不含推测）：入口到第一条 ret = 106 字节，CFG 真实长度 = 136 字节，差 30 字节，差值完全由 A4 表里的两条向前跳产生。

---

## 任务 B：字节差异

### B1/B2/B3 命令与输出

```
$ python3 b_diff.py
L = 136
diff count L=136: 2
  off=78   vaA=0x6bedfe vaB=0x41c29e A=c0 B=b0
  off=112  vaA=0x6bee20 vaB=0x41c2c0 A=c0 B=b0
diff count first 106: 1
  off=78   vaA=0x6bedfe vaB=0x41c29e A=c0 B=b0
```

| 比较范围 | 差异个数 | 差异偏移（两侧值） |
|---|---|---|
| L = 136 | **2** | off 78: A=c0 / B=b0；off 112: A=c0 / B=b0 |
| 前 106 字节 | **1** | off 78: A=c0 / B=b0 |

体 A 原始字节（136 B，md5 ca001e3da43132fec0a97472d507d8c1）：

```
56 57 8b f9 8b 07 85 c0 74 06 8b 08 50 ff 51 08 8b 44 24 14 a8 14 74 52
8b 4c 24 0c 8d 54 24 10 52 68 c0 7b 81 00 50 8b 44 24 1c 50 51 ff 15 fc
15 7e 00 85 c0 7c 4c 8b 54 24 10 52 ff 15 00 16 7e 00 8b f0 85 f6 7c 11
8b 44 24 10 57 68 c0 7b 81 00 50 8b 08 ff 11 8b f0 8b 44 24 10 50 8b 10
ff 52 08 8b c6 5f 5e c2 0c 00 8b 4c 24 0c 57 68 c0 7b 81 00 50 8b 44 24
1c 50 51 ff 15 fc 15 7e 00 8b f0 5f 5e c2 0c 00
```

体 B 原始字节（136 B）：

```
56 57 8b f9 8b 07 85 c0 74 06 8b 08 50 ff 51 08 8b 44 24 14 a8 14 74 52
8b 4c 24 0c 8d 54 24 10 52 68 c0 7b 81 00 50 8b 44 24 1c 50 51 ff 15 fc
15 7e 00 85 c0 7c 4c 8b 54 24 10 52 ff 15 00 16 7e 00 8b f0 85 f6 7c 11
8b 44 24 10 57 68 b0 7b 81 00 50 8b 08 ff 11 8b f0 8b 44 24 10 50 8b 10
ff 52 08 8b c6 5f 5e c2 0c 00 8b 4c 24 0c 57 68 b0 7b 81 00 50 8b 44 24
1c 50 51 ff 15 fc 15 7e 00 8b f0 5f 5e c2 0c 00
```

### B4 两次结果不同的原因

差异偏移 112 位于 0x6bee20（A）/ 0x41c2c0（B），它落在第一条 ret（0x6bee17 `ret 0xc`，结束于 0x6bee1a）之后的 else 块内，距入口偏移 ≥ 106。前 106 字节比较覆盖的是 [0,106)，不含偏移 112，因此少报 1 处；136 字节版本才把它纳入。

两处差异都是 `push` 立即数的最低字节：偏移 78 与 112 分别是第 2、第 3 条 `push` 立即数的首字节（`68 c0 7b 81 00` vs `68 b0 7b 81 00`，即 0x817bc0 vs 0x817bb0）。这两处偏移与任务 C1 得出的掩码偏移 78、112 完全重合（C1 中三处立即数在体 A 全为 0x817bc0，体 B 第 2、3 处为 0x817bb0）。

---

## 任务 C：模板实例化普查

### C1 体 A 内 push 立即数 > 0x400000

```
$ python3 c_census.py
C1 push imm >0x400000 count = 3
   {'insn_va': '0x6bedd1', 'off': 33, 'op': '0x817bc0', 'imm': '0x817bc0', 'imm_off': 34, 'imm_bytes': 'c0 7b 81 00'}
   {'insn_va': '0x6bedfd', 'off': 77, 'op': '0x817bc0', 'imm': '0x817bc0', 'imm_off': 78, 'imm_bytes': 'c0 7b 81 00'}
   {'insn_va': '0x6bee1f', 'off': 111, 'op': '0x817bc0', 'imm': '0x817bc0', 'imm_off': 112, 'imm_bytes': 'c0 7b 81 00'}
```

| 指令偏移（相对 0x6bedb0） | 指令 VA | 立即数 |
|---|---|---|
| 33 | 0x6bedd1 | 0x817bc0 |
| 77 | 0x6bedfd | 0x817bc0 |
| 111 | 0x6bee1f | 0x817bc0 |

掩码字节偏移（体 A 内）：34,35,36,37 / 78,79,80,81 / 112,113,114,115（共 12 字节可不同，其余 124 字节须完全相同）。

### C2 掩码搜索（.text 全段）

```
C2 masked scan [body A mask]: hits=2 ['0x41c250', '0x6bedb0']
```

整文件（所有节，非只 `.text`）掩码扫描同结果，未发现额外命中：

```
$ python3 e_supp.py
whole-file masked hits (file offsets): ['0x1c250', '0x2bedb0']
   off=0x1c250 section=.text VA=0x41c250
   off=0x2bedb0 section=.text VA=0x6bedb0
```

第二套实现（纯字节比较，不走正则）复算：

```
xcheck masked hits (byte-compare impl): ['0x41c250', '0x6bedb0']
```

### C3 每个命中的立即数读回

```
C3 immediates per hit:
  0x41c250 -> ['0x817bc0', '0x817bb0', '0x817bb0']  bytes=c0 7b 81 00 | b0 7b 81 00 | b0 7b 81 00
  0x6bedb0 -> ['0x817bc0', '0x817bc0', '0x817bc0']  bytes=c0 7b 81 00 | c0 7b 81 00 | c0 7b 81 00
```

| 命中地址 | push@+33 | push@+77 | push@+111 |
|---|---|---|---|
| 0x6bedb0 | 0x817bc0 | 0x817bc0 | 0x817bc0 |
| 0x41c250 | 0x817bc0 | 0x817bb0 | 0x817bb0 |

### C4 直接 E8 call 调用点（原始字节法，rel32 = target − (site + 5)）

```
C4 E8 call sites:
  0x41c250 <- ['0x416bc2', '0x44e02c', '0x4db8cc', '0x4df85c', '0x51b064', '0x521fc2', '0x5230dc',
               '0x65f092', '0x6cc999', '0x710213', '0x7354f2', '0x742699', '0x742a94'] (n=13)
  0x6bedb0 <- ['0x6bc364', '0x6bc3aa'] (n=2)
```

| 目标 | 调用点个数 | 调用点地址 |
|---|---|---|
| 0x6bedb0 | **2** | 0x6bc364, 0x6bc3aa |
| 0x41c250 | **13** | 0x416bc2, 0x44e02c, 0x4db8cc, 0x4df85c, 0x51b064, 0x521fc2, 0x5230dc, 0x65f092, 0x6cc999, 0x710213, 0x7354f2, 0x742699, 0x742a94 |

合计 15 处。rel32 原值与扫到的 0xE8 总数：

```
total 0xE8 bytes in .text: 81715
   0x6bc364 -> 0x6bedb0  rel=0x2a47 (10823)
   0x6bc3aa -> 0x6bedb0  rel=0x2a01 (10753)
   0x416bc2 -> 0x41c250  rel=0x5689 (22153)
   0x44e02c -> 0x41c250  rel=0xfffce21f (-204257)
   ... （其余 11 处均为 0x41c250，rel32 见 e_supp.out）
hits inside either function body: []
```

objdump 独立复核（`i686-w64-mingw32-objdump -d -z` 线性全段，grep `call 0x41c250|0x6bedb0`）：15 条，地址与上表逐一相同。

> 解析器修正记录（卡片「得 0 先怀疑解析器」）：用 capstone `md.disasm(CODE, TEXT_VA)` 做全段线性反汇编再统计 call 目标时，`0x6bedb0` 得 **0**、`0x41c250` 得 **2**：
> ```
> xcheck capstone call-rel32 -> 0x6bedb0: n=0 []
> xcheck capstone call-rel32 -> 0x41c250: n=2 ['0x416bc2', '0x44e02c']
> ```
> 原因不是没调用，而是 capstone 的迭代器在 0x46f5a0 处遇到无法解码的字节即停止：
> ```
> capstone linear sweep: insns=155215 last=0x46f59d end=0x46f5a0 text_end=0x7e038d
> disasm attempt at desync: []
> ```
> 只覆盖到 0x46f5a0，其后的调用点（0x4db8cc 起）全部漏掉。改用原始字节法（逐字节找 0xE8，校验 rel32）后得 15 处，与 objdump 一致。两项对照均只覆盖标准 `E8 rel32`；`FF /2`、`FF 15` 等间接调用不在本步统计范围。

### C5 三条反控

```
C5 controls:
C2 masked scan [off5=0xff]: hits=0 []
C2 masked scan [first mask byte flipped (off=34)]: hits=2 ['0x41c250', '0x6bedb0']
plain scan [unmasked body A]: hits=1 ['0x6bedb0']
```

| 反控 | 命中数 | 要求 | 是否满足 |
|---|---|---|---|
| 体 A 偏移 5 置 0xff，同掩码搜索 | **0** | 必须为 0 | 满足 |
| 掩码内第一个字节（偏移 34）取反，同掩码搜索 | **2**（0x41c250, 0x6bedb0） | 必须 ≥2 | 满足 |
| 不做掩码，直接搜体 A 完整 136 字节 | **1**（0x6bedb0） | 必须为 1 | 满足 |

第二条纯字节比较实现（`d_xcheck.py`）复算：

```
xcheck ctrl off5=0xff: 0
xcheck ctrl first-mask-flip: ['0x41c250', '0x6bedb0']
xcheck plain: ['0x6bedb0']
```

---

## 解析器说明（立即数双形态）

```
$ python3 e_supp.py
parse_imm dual-form: [('0x817bc0', 8485824), ('8485824', 8485824),
                      ('0x10', 16), ('16', 16), ('0x14', 20), ('20', 20)]
```

判定规则：以 `0x`/`-0x` 前缀走 `int(s,16)`，否则走 `int(s,10)`；两种形态都接受，C1 因此未出现 0 命中。

## 产物清单（本目录，只读仓库其余部分）

- `a_cfg.py` / `a_cfg.json` / `a_cfg.out`：CFG 可达性遍历、首 ret 边界、越界跳转定位
- `a5_else.py` / `a5_else.json`：else 块独立 CFG 反控
- `b_diff.py` / `b_diff.json`：136 B 与 106 B 两版逐字节比较
- `c_census.py` / `c_census.json`：push 立即数、掩码搜索、立即数读回、E8 调用点、三条反控
- `d_xcheck.py`：CFG/掩码/调用点的第二套独立实现
- `e_supp.py` / `e_supp.out`：整文件掩码扫描、立即数双形态解析、capstone 线性 sweep 截断定位、E8 原始表
- `run.log`：上述脚本的合并原始输出

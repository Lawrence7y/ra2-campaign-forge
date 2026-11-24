# R119 跨家族审计 · C16 门禁与 GUID 判据复核

## 5 【成立】三处都满足「COM 形态 GUID」；其中只有两处 +0x10 是 type_info vftable

从 `ra2bench/gamemd.exe` 独立解析（PE 头 `e_lfanew=0x3c`，machine=0x14c，ImageBase=0x400000，5 节；`.data` VA=0x812000 / raw=0x412000 / size=0x6c000），直接读 raw 偏移 `0x412000+(VA-0x812000)`：

| VA | 16 字节 hex | 4 个小端 dword | +0x10 dword |
|---|---|---|---|
| 0x818858 | `0c 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46` | `0x10c, 0x0, 0xc0, 0x46000000` | `0x7f9594` |
| 0x820270 | `09 01 00 00 00 00 00 00 c0 00 00 00 00 00 00 46` | `0x109, 0x0, 0xc0, 0x46000000` | `0x7f9594` |
| 0x817bc0 | `00 00 00 00 00 00 00 00 c0 00 00 00 00 00 00 46` | `0x0, 0x0, 0xc0, 0x46000000` | `0x59524753` |

三处第 2 dword == 0、第 3 dword == 0xC0、第 4 dword == 0x46000000，**COM 形态 3/3 成立**。
但 +0x10 处：`0x818858` 与 `0x820270` 都是 `0x7f9594`（vftable，后接 `2e 3f 41 56 3f 24 ...` = `.?AV?...` 装饰名），`0x817bc0` 是 `0x59524753`，其后字节为 `53 47 52 59 53 4d 4b 31 00` = ASCII `SGRYSMK1`，不是 vftable、也不是装饰类名。
机械复算：在 `.data` 里 `0x818868` 处为 `94 95 7f 00 00 00 00 00 2e 3f 41 56 3f 24 56 65 63 74 6f 72 43 6c 61 73 73 40 47 40 40`（`.?AV?$VectorClass@G@@`），`0x818888` 处为 `94 95 7f 00 ... 2e 3f 41 56 3f 24 44 79 6e 61 6d 69 63...`（`.?AV?$DynamicVectorClass@G@@`），两个 type_info 确实相邻；`0x818858` 到前者 gap=0x10、到后者 gap=0x30。配对歧义成立；同时 `0x817bc0` 的 +0x10 根本不是 type_info，说明原「GUID+type_info」判据在该地址上本就返回否定，不能用作「真记录」的正证据。

## 6 【成立】独立核验得到同样的 8/1 分布

自写 PE 解析 + Capstone 线性扫描（`CS_ARCH_X86/CS_MODE_32`，`detail=False`，从 `.text` raw=0x1000 起逐条 decode），按 `68 c0 7b 81 00` 定位 `push 0x817bc0`，得 9 个站点：

```
0x413dd8 0x41c271 0x437f58 0x517b6b 0x67d0d0 0x67e5b4 0x6bedd1 0x6bedfd 0x6bee1f
```

逐站取 push 之后第一条 `call`：

| push 站点 | 第一条 call 地址与目标 |
|---|---|
| 0x413dd8 | 0x413de2 `call dword ptr [0x7e15fc]` |
| 0x41c271 | 0x41c27d `call dword ptr [0x7e15fc]` |
| 0x437f58 | 0x437f6e `call dword ptr [0x7e15fc]` |
| 0x517b6b | 0x517b74 `call dword ptr [0x7e15fc]` |
| 0x67d0d0 | 0x67d0dd `call dword ptr [0x7e15fc]` |
| 0x67e5b4 | 0x67e5c1 `call dword ptr [0x7e15fc]` |
| 0x6bedd1 | 0x6beddd `call dword ptr [0x7e15fc]` |
| 0x6bedfd | 0x6bee05 `call dword ptr [ecx]` |
| 0x6bee1f | 0x6bee2b `call dword ptr [0x7e15fc]` |

共 8 个 `[0x7e15fc]` + 1 个 `[ecx]`。IAT 名称解析必须按导入描述符的 **FirstThunk（fa）** 计槽位、按 **OriginalFirstThunk（ft）** 读名字：ole32 描述符 `ft=0xb935ec`、`fa=0x7e15c8`，名字序列第 14 项为 `CoCreateInstance`，落在 `fa+4*13=0x7e15fc`。自写解析结果：`IAT[0x7e15fc] = ('ole32.dll', 'CoCreateInstance')`；对照 `IAT[0x7e1600] = ('ole32.dll', 'OleRun')`。若误用 ft 当 IAT 地址会得到 None（我第一次即如此），这不是「8 个不是 CoCreateInstance」的证据。故「8 个走 CoCreateInstance」独立复核成立。

## 7 【成立】存在至少两种具体失败模式，但对本样本 8 这个数字无影响

模式一 —— **参数在 push IID 之后继续 push，中间可夹入别的 call**：CoCreateInstance 的 stdcall 实参顺序是 `(pClsid, pUnkOuter, dwClsContext, riid, ppv)`，riid 先入栈。实测 `0x413dd8` 字节为 `68 c0 7b 81 00 | 6a 07 | 6a 00 | 53 | ff 15 fc 15 7e 00`，即 IID 是第 1 个 push，消费它的 call 是第 4 条指令。若编译器/优化在中间插入 `call`（例如栈检查、字符串转换 helper），「第一条 call」就不是消费 IID 的那条，而会指向 helper。对本样本 8 个站点：两条 `call [0x7e15fc]` 之前只有 `push`/`mov`/`lea`，无中间 call，故不影响。

模式二 —— **第一条 call 是间接虚调用但确实消费 IID**：`0x6bedfd` 站点字节 `68 c0 7b 81 00 | 50 | 8b 08 | ff 11 ...`，第一条 call 是 `call [ecx]`（QueryInterface 形态），IID 在此正作为 riid 传入；从「第一条 call 不是导入函数」推出「该 IID 无代码用途」会丢掉这一真阳性。本会话把它排除出「CoCreateInstance」计数是正确的，但排除的是「调用目标类型」，不是「IID 未使用」。

模式三 —— **跨基本块/尾跳转**：若 push 之后是 `jmp` 到共享 call 序列，线性扫描的「下一条 call」取决于解码起点，可能把不相邻块的 call 算进来；本样本 9 个站点均为顺序流，未出现跳转。

三种模式的机械检查路径：对 9 个站点从 push 起 32 字节逐字节查看是否出现 `e8/e9/eb/ff /4` 或 `ff /2`，实测只有 `0x6bedfd` 出现 `ff 11`，其余 8 个首个 `ff 15` 都指向 `0x7e15fc`。故失败模式成立，但不改变第 6 点的 8/1 计数；它们只限制该判据向其他 IID/其他二进制推广。

## 1 【成立】50% 下界会误伤合法的「删长重写」

`_r119/c16_floors.json` 的 `sizes` 共 116 节；按 `floor = size/2` 复算，**64 节原始大小落在 [3072, 6144) 字节**（id：8, 9, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23, 25, 27–71, 80, 94, 95, 98, 99, 100）。对这类节，纯删 3 KB 且重写量不足时必然跌破 floor：例如 2.8 原 3749 B、floor=1874，删掉 3 KB 重复段后仅剩 677 B，即使重写 1 KB 也只回到 1749 B < 1874 ⇒ FAIL。另 2.11 原 1540 B、floor=770，删 3 KB 已不可能（节内不足 3 KB），说明该下界对小节的敏感度过高。
反向证据：`_r119/r119e_gate.json` 的 E4 正控只做了「2.80 删末尾 10% 行 ⇒ exit 0」，删 10% 远小于 50%，不能证明对「3 KB 删长重写」不误伤。结论：会误判，误判面约 64/116 节（有 3 KB 可删且净减少时）。

## 2 【成立】表外新节确实永久免检，但现脚本已把「无限张票」压到 2 张

现脚本 `lead/next_re_20261117_r14/check_disc.py` 除 `C16_NEW_MIN = 0` 外，还有 `C16_UNPINNED_MAX = 2` 及相应检查（`check_disc.py:512-518`）：`_unp16 = sorted(_c16_seen - set(C16_FLOORS))`，仅当 `len(_unp16) > 2` 才 FAIL。因此下一轮新增 2.123 时：`_unp16 = [123]`，长度 1 ≤ 2 ⇒ 不 FAIL，该节**永久无字节下限**（只要不追加第 3 个新节）。这构成「永远通过」子项：一个空壳新节（甚至只有标题行）不会被 C16 看见；C15 的四条判据只看总量和末节号，也看不见。C16b 只是把免检票上限从无限改为 2，并未给票加内容约束，也没有票的时效。

## 3 【成立】同改表与常量可无声通过，且弱于 C14 的 sha 钉

`C16_FLOORS`（`check_disc.py:460-477`）是脚本内的 Python 整数常量，与 116 节字节数之间没有密码学绑定。把某节正文清空并把对应 floor 改小（或把该节 id 从表中删除、同时把 `C16_UNPINNED_MAX` 调大）后，`_c16_bad` 为空、`_miss16` 为空、`_unp16` 不超限，脚本 exit 0。脚本注释 `check_disc.py:457-458` 已自认此边界。

与 C14 比较：`C14_TEXT_SHA256 = 'a740bcc9...'` 和 `C14_ROW_SHA` 在 `check_disc.py:401-417` 对 31 行自由文本做整表 sha256 + 逐行 sha256；篡改必须同步替换一个 64 位摘要（或对应行的摘要），且注释同样自认「同时改表与本常量者仍可过」。C16 的篡改只需把一个十进制整数改小（例如 `50: 2771` → `50: 100`），diff 中 indistinguishable from 正常重钉；C14 至少要改一个 64 hex 常量。两者都可被同改绕过，但 C16 无摘要、多常量、逐项分散，审计可见性更低 ⇒ **更弱**。此外 C16_FLOORS 未登记 `GATE_VER`，`C10` 自检只核对 `GATE_VER` 与 DISC_RECHECK 第 20 行，不覆盖 C16 表本身。

## 4 【不成立】差异不是 CRLF 造成的，而是 preamble 与边界 LF 的归属

独立统计 `lead/next_re_20261117_r14/R14_COMMON.md`：`len(rc)=1008448`，`CR=1081`，`LF=11034`，`rc.split('\n')` 得 11035 行。复刻 C16 切段（`check_disc.py:483-495`）得 116 节（7..122，无重复），逐节字节和 **778085**，与 `_r119/c16_floors.json` 的 `sizes` 逐个相等（0 处差异），与文件字节差 **1008448-778085 = 230363**。

账面拆解：
- 第一节标题 `## 2.7` 位于第 1577 行，`preamble = '\n'.join(lines[:1577])` 为 **230247 B**；
- `preamble + 116 节 = 230247 + 778085 = 1008332`，距文件差 **116 B**；
- 116 恰好 = 1（preamble 与第一节标题之间的 1 个 LF）+ 115（116 节之间的 115 个节间 LF）：C16 的 `'\n'.join(_buf16)` 只计节内行间 LF，每个节少计其前面那个 LF；116 节共少 115 个节间 LF，再加 preamble 与 2.7 标题之间的 1 个 LF，合计 116 B。
- CR 分布：1081 个 CR **全部在 preamble 内**，116 节内部 CR 数为 **0**（节内 LF=11034-1577=9457，与逐节和一致）。

因此 CRLF 对「节字节数」的影响为 **0**：节内没有 CR，`split('\n')` 与按 `splitlines()` 计数在这些节上等价；各节之和不等于整文件大小是因为门禁只统计 2.x 正文（230247 B 前言不属于任何节），再加 116 个边界 LF 归属，不是 CRLF 切错。若论自洽性：节和与 `c16_floors.json.sizes` **完全自洽**（116/116），与整文件不自洽但差额可逐字节解释。

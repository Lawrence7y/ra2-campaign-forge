# §388　★★★ 异族复核推翻 §387：门禁 63 条里 35 条不构成取值证明，`_esp_bfs.py` 是打印机不是门禁

**性质**：离线，零真机。异族 = `general-purpose`（会话默认族，非 DeepSeek 本线）。
**结论**：§387 的**数值结论仍成立**（`[esp+0x18]` = msg），但 §387 声称的
「63/63 PASS 已证明」被推翻 —— 那是**计数虚高**。已全部修好，现 **75/75 + 14/14**。

---

## 一、异族的独立复算：与我的数值一致

异族完全不看我的文档，自己写代码从 PE 字节推导，结论：

| 项 | 异族独立结论 |
|:--|:--|
| 分支 A（跳过 GetMenu）到 0x777687 | esp = **−0x10** ⇒ `[esp+0x18]` = **E+0x08 = msg** |
| 分支 B（走 GetMenu）到 0x777687 | esp = **−0x10** ⇒ 同上 |
| `0x7E1404` 解析 | `USER32.dll!GetMenu`，**1 个参数**，净 esp = +4 |
| 虚调用 `call [eax+0x38]` | ret=4 时唯一值 {−16}；ret=0 时 {−16, −20} 两个值 |

它还给了**一条我没想到的语义论证**：合并点 `0x777627` 处
`mov edi,[esp+0x14]` / `lea ecx,[esp+0x20]` / `lea edx,[esp+0x1c]` / `lea eax,[esp+0x1c]`
之后 4 次 push 再 `call 0x6930A0`（ret 0x10，4 参）。
**只有 esp=−0x10 时这 4 个实参才恰好是 (hwnd, msg, wParam, lParam)**；
若为 −0x14，第一个实参变成返回地址 —— 畸形调用。这反向锁定了虚调用 ret=4。

⇒ **数值层面双方一致，`[esp+0x18]` = msg 成立。**

---

## 二、但异族推翻了门禁的**证明力**

### 2.1 分类结果

| 类别 | 条数 | 说明 |
|:--|--:|:--|
| 真断言 | 27 | 被测值（从二进制读 / 实算）出现在断言表达式里 |
| **恒真式** | **19** | 断言两侧都是脚本自己刚赋的常量 |
| 弱断言 | 16 | 只验证「存在」不验证「取值」 |

**35/63（56%）不构成取值证明。**

### 2.2 最严重的一条：10 条 WNDCLASSA 槽位断言完全不读二进制

```python
for addr, esp_off, want_wc, name in slots:
    got_wc = esp_off - WC_SLOT
    check("0x%08X 写 wc+0x%02X (%s)" % (addr, want_wc, name),
          got_wc == want_wc, "算得 wc+0x%02X" % got_wc)
```

`esp_off` / `WC_SLOT` / `want_wc` 全是本文件字面量，`addr` **只进了标题字符串**。

**我实测复现**：把 10 个 `addr` 全改成 `0xDEADBEEF` → 仍 **63/63 PASS、exit 0**。

### 2.3 `_esp_bfs.py` 是打印机，不是门禁

它的 6 条断言只有「可达」「唯一」「间接调用存在」—— **没有一条断言取值**。

**我实测复现（P4）**：把二进制 `0x7775C0` 的 `push ecx`（`51`）改成 `nop`（`90`），
它打印：

```
目标 0x00777687 到达时的 esp 集合: [-12]
   esp= -12 => [esp+0x18] = 入口 E+12
0x00777687 的 esp 唯一（无分支分歧）   PASS  [-12]
0x00777687 esp=-12 => [esp+0x18] = wParam     ← 自己算出了 wParam
6/6 PASS                                       ← 仍全绿
```

**它自己打印出 `wParam` 了，还报 6/6 PASS。** 我把打印当成了验证。

### 2.4 门禁自报「结论不可靠」却仍 exit 0

`path2` 区间的分支分歧被检出（`0x77764C` 两侧 −4 vs 0），脚本打印
「该区间**不是单一路径** —— esp 结论不可靠」，随后
`RESULTS.append((..., True, ...))` 记 PASS 并 exit 0。

**这就是它没拦住我 §387 那个 bug 的原因**（GetMenu 净额算错 ⇒ 恰好产生这个分歧）。
我把告警降级成了 INFO。

### 2.5 其余

- 脚本**从未走到 `0x7775D4`**：`walk()` 解码范围是 `0x7775C0..0x77766C`，
  `0x7775D0–0x777626` 一条没碰。而脚本文档把「虚调用 ret 尺寸」说成根因修正
  —— 这条因果链**没有被代码验证**。
- `0x7779B9` 前驱清单不完整：脚本列 5 个，实际 **9 个**。
- 起点错位（B2）时 `_esp_bfs.py` 静默给出错值且全绿 —— 它没有边界自检。

---

## 三、修复

### 3.1 `_esp_bfs.py`：从打印机改成门禁（6/6 → 14/14）

新增**取值断言**：

```python
EXPECTED_ESP = -0x10
EXPECTED_ARG = 0x08
for t in TARGETS:
    s = reached[t]
    check("0x%08X 可达" % t, bool(s), ...)
    check("0x%08X 的 esp 唯一" % t, len(s) == 1, ...)
    got = sorted(s)[0] if len(s) == 1 else None
    check("0x%08X 的 esp 取值 = %+d（实算，非结构性）" % (t, EXPECTED_ESP),
          got == EXPECTED_ESP, "实算 %s" % got)
    check("⇒ 0x%08X 的 [esp+0x18] = E+0x%02X = msg" % (t, EXPECTED_ARG),
          got is not None and got + 0x18 == EXPECTED_ARG, ...)
```

新增**起点边界自检**（异族 B2）：

```python
bounds = {i.address for i in md.disasm(b[off_fn - 16:off_fn + 16], FN - 16)}
check("起点 0x%08X 是已知指令边界" % FN, FN in bounds, ...)
check("负控 0x7775C3（指令中段）不是边界", 0x7775C3 not in bounds, ...)
```

新增**目标指令本体自检**（异族 P2：本工具只按地址算 esp，从不读目标指令）：

```python
TARGET_DISP = {0x777687: (0x777687, 0x18), 0x7779B9: (0x7779B5, 0x18)}
for t, (ins_va, want_disp) in TARGET_DISP.items():
    ins = next(md.disasm(b[va2off(ins_va):][:8], ins_va))
    check("0x%08X 的目标指令读 [esp + 0x%x]（实读二进制）" % (ins_va, want_disp),
          ins.mnemonic == "mov" and "[esp + 0x%x]" % want_disp in ins.op_str, ...)
```

★ 注意 `0x7779B9` 处首条指令是 `mov edx,[esp+0x20]`，读 `[esp+0x18]` 的是前一条
`0x7779B5`。我第一版把断言写在 0x7779B9 上，被门禁自己抓出来了（14/14 → 13/14）。

### 3.2 WNDCLASSA 槽位：从自说自话改成真读指令

```python
for addr, want_wc, name in slots:
    o_a = va2off(addr)
    if o_a is None:                     # ★ 干净的 FAIL，不抛异常
        check("0x%08X (%s) 可映射到文件" % (addr, name), False, "VA 不在任何节内")
        continue
    ins = next(md.disasm(b[o_a:o_a + 16], addr))
    m_disp = re.search(r"\[esp \+ (0x[0-9a-f]+)\]", ins.op_str)
    got_wc = (int(m_disp.group(1), 16) - WC_SLOT) if m_disp else None
    check("0x%08X 写 wc+0x%02X (%s)" % (addr, want_wc, name), got_wc == want_wc,
          "%s %s ⇒ wc+0x%02X" % (ins.mnemonic, ins.op_str, ...))
```

现在 D1 负控得 **10 条干净 FAIL**（原版是崩溃，FAIL 计数失真）。

### 3.3 分支分歧：从 INFO 改成真 FAIL

```python
if mismatched:
    check("自检 %s 区间必须是单一路径（不得跨分支）" % label, False,
          "分歧点 %s" % mismatched[:2])
```

### 3.4 真正把 path2 拆成两条分支

原先 `path2 = (0x777627, 0x77766E)` 跨过 `0x77764C` 的两支，`walk()` 只按
「顺序落入」一条走。现在：

```python
path1  = (0x7775C0, 0x7775CE)    # 入口到 je
path2a = (0x777627, 0x777655)    # 分支 A：0x77764C je 成立 ⇒ 跳过 GetMenu
path2b = (0x77764E, 0x777655)    # 分支 B：je 不成立 ⇒ push+call GetMenu
path3  = (0x777655, 0x77766E)    # 汇合后到 0x77766C je

def esp_along(*segs):
    esp = 0
    for seg in segs: walk(*seg)
    return esp

esp_A = esp_along(path1, path2a, path3)
esp_B = esp_along(path1, path2b, path3)
```

**两条分支各自独立算到 −0x10** —— 这才是「与分支无关」的实证，
而不是 `hand_esp()` 那种字面量同义反复。

### 3.5 删除 `hand_esp()` 的 4 条恒真式

异族认定它是「纯字面量算术、不读二进制」。已被真实双分支 `walk` 取代。

---

## 四、灵敏度实证（全部负控变红）

### `_verify_stack_offset.py`（75/75）

| 负控 | 注入 | exit | FAIL |
|:--|:--|--:|--:|
| P0 | baseline | 0 | 0 |
| P1 | 二进制：nop `0x7775C0 push ecx` | 1 | 9 |
| P2 | 二进制：`0x777687` 改读 `[esp+0x1c]` | 1 | 1 |
| P5 | 二进制：`0x777C79` 槽位 `0x28→0x2c` | 1 | 1 |
| P6 | 二进制：`0x7779E1` `0x286→0x287` | 1 | 1 |
| P7 | 二进制：跳表 `0x77810C` 第 4 项 `1→0` | 1 | 2 |
| M2 | 源码：`GetMenu` argc `1→0` | 1 | 9 |
| M3 | 源码：`walk` 的 `call [mem]` 改回净 0 | 1 | 9 |
| **D1** | 源码：10 个 slot addr → `0xDEADBEEF` | 1 | **10** |

### `_esp_bfs.py`（14/14）

| 负控 | 注入 | exit | FAIL |
|:--|:--|--:|--:|
| P0 | baseline | 0 | 0 |
| P4 | 二进制：nop `push ecx` | 1 | 4 |
| P2 | 二进制：`0x777687` 改读 `[esp+0x1c]` | 1 | 1 |
| P2b | 二进制：`0x7779B5` 改读 `[esp+0x1c]` | 1 | 1 |
| B2 | 源码：起点改 `0x7775C3`（指令中段） | 1 | 5 |

**P4 与 D1 是 §387 那两个缺陷的直接回归测试** —— 它们现在都会变红。

---

## 五、修完 `ret_778030()` 后又发现：它**内容也是错的**

异族把 `ret_778030()` 列为恒真式（纯字面量、不读二进制）。我改从二进制读跳表后，
发现它不只是「不读二进制」，而是**事实错误**：

原版断言「`0x282..0x291` **全部**返回 1」。实际跳表：

```
0x7780D6  jmp dword ptr [ecx*4 + 0x778104]     ; 二级跳表
0x7780D0  mov cl, byte ptr [eax + 0x77810c]    ; 字节索引
```

实读结果（`0x77810C` 的 16 个字节 = `[0,1,1,0,1,1,1,1,1,1,1,1,1,1,0,0]`）：

| msg | 索引 | 落点 | 返回 |
|:--|--:|:--|--:|
| 0x282 | 0 | 0x7780DD | **1** |
| 0x283 | 1 | 0x7780FD | 0 |
| 0x284 | 1 | 0x7780FD | 0 |
| 0x285 | 0 | 0x7780DD | **1** |
| 0x286 | 1 | 0x7780FD | **0** ← 原版误判为 1 |
| 0x287..0x28F | 1 | 0x7780FD | 0 |
| 0x290 | 0 | 0x7780DD | **1** |
| 0x291 | 0 | 0x7780DD | **1** |

**只有 `{0x282, 0x285, 0x290, 0x291}` 返回 1。**

### 这条修正的实际意义

`0x286` = **WM_IME_CHAR**。原版认为它返回 1（⇒ 不跳 0x777687），
实际返回 0（⇒ **跳** 0x777687）。

这直接影响 §387 语义证据 5 的解释：`0x7779E1 cmp eax,0x286` 那个 IME 分支，
**在 0x777687 之后**（`0x777687 → ... → 0x7779B9 → 0x7779DD → 0x7779E1`），
与「0x778030 是否把它挡住」是两件事。两者不矛盾，但我原先没分清。

现在改为真读跳表：

```python
TAB_VA, IDX_VA = 0x778104, 0x77810C
TAB_N = 2
tab2 = struct.unpack_from("<%dI" % TAB_N, b, va2off(TAB_VA))
idx2 = list(b[va2off(IDX_VA):va2off(IDX_VA) + 16])
RET1_VA, RET0_VA = 0x7780DD, 0x7780FD

def ret_778030_real(msg):
    if msg > 0x281:
        k = msg - 0x282
        if not (0 <= k < 16): return 0
        return 1 if tab2[idx2[k]] == RET1_VA else 0
    if msg == 0x281: return 1
    if msg in (0x10D, 0x10E, 0x10F): return 1
    return 0
```

负控 P7（把 `0x77810C` 第 4 项 `1→0`）⇒ **exit 1 / FAIL 2**，灵敏度坐实。

---

## 六、`0x7779B9` 前驱清单补全

异族指出脚本列 5 个、实际 9 个。我扫函数体 `0x7775C0..0x777C30` 得 **11** 个：

```
0x7776A0 ja    0x7777D5 jne   0x7777E3 je    0x777846 jne
0x777865 jne   0x77787B jmp   0x777886 jmp   0x777891 jne
0x777958 jmp   0x777967 jne   0x77798B jne
```

已改为**从二进制全量扫描**，并断言「原列 5 个 ⊆ 全量结果」。

---

## 七、剩余风险（异族列出，我认可，如实登记）

1. ~~**虚调用路径仍未被脚本覆盖**~~ ⇒ **§389 已闭合**（符号解析得
   vtable=0x7F794C、slot14=0x7B1780、`mov eax,0x473; ret 4`，实测 ret=4）。
   且 §389 另证：`0x7775D0` 分支与 `0x777687` **互斥**（前者只在
   msg ∈ {0x473,0x475} 时进入），故即使 ret≠4 也不影响 0x777687 的结论。
2. ~~`0x7779B9` 前驱清单不完整~~ ⇒ **已修**（见第六节，全量 11 个）。
3. ~~`ret_778030()` 是字面量恒真式~~ ⇒ **已修**，且修的过程中发现它**内容也是错的**
   （见第五节）。现从二进制读跳表，负控 P7 可打红。

---

## 八、门禁状态（全绿）

| 门禁 | 结果 |
|:--|:--|
| `_verify_stack_offset.py` | **75/75 PASS** |
| `_esp_bfs.py` | **14/14 PASS** |
| `_verify_wmclose_chain.py` | 20/20 PASS |
| `_survey_6930a0.py` | 2/2 PASS |
| `_selftest_todo6_verdict.py` | 10/10 PASS |
| `_verify_a8_runtime.py` | 11/11 PASS |
| `_verify_probe_a4a7a8.py` | 21/21 PASS |
| `_todo7_creation_trigger.py` | 16/16 PASS |
| `_verify_wer_sig.py`（harness6） | 10/10 PASS |

---

## 九、教训（本轮最重要的一条）

**「N/N PASS」这个数字本身没有意义。** 必须问：这 N 条里，有多少条的断言
**真的把被测物放进了等式**？

§387 我报了 63/63，异族一查 35 条不构成取值证明，其中 10 条连一个字节都没读。
更糟的是 `_esp_bfs.py` —— 它自己打印出 `wParam`（错的），还报 6/6 PASS。
**我把「程序跑完了没报错」当成了「程序证明了结论」。**

三条具体对策（已落进代码）：

1. **每条断言都必须能问「哪个字节变了会让它红」**。答不出来的就是装饰。
2. **自检发现异常时不许降级成 INFO**。§387 的分支分歧告警正是缺陷信号。
3. **打印 ≠ 断言**。算出一个值之后，必须把那个值和期望值比较，
   而不是把它打印出来就完事。

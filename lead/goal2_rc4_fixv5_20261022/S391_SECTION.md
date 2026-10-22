# §391　★ 自纠 §389：「两路互斥」结论对，**理由错**

**性质**：离线，零真机。**自纠**。结论不变，但 §389 给的机制是错的。

---

## 一、§389 写的理由

> `0x7775E7` 段只在 `msg ∈ {0x473, 0x475}` 时执行，是 IME 专用路径。
> 而 `0x777687` 的主分派处理的是**非 IME 的普通消息**。**两条路互斥。**

隐含的推理是：「IME 消息走 IME 段，普通消息走 0x777687，所以互斥」。

**这个理由站不住。** 我查了实际控制流：

```asm
0x7775CE  je  0x777627        ; [0x887628]==0 ⇒ 直接跳到主线
0x7775D0  ...                 ; 对象非空才走
0x7775D4  call [eax+0x38]     ; slot14 → 返回 0x473
0x7775DB  cmp edx, eax        ; msg vs 0x473
0x7775DD  je  0x7775E7        ; msg == 0x473 ⇒ IME 段
0x7775DF  cmp edx, 0x475
0x7775E5  jne 0x777627        ; msg 非 IME ⇒ 跳到主线
0x7775E7  ...                 ; IME 段
```

`0x7775E5 jne 0x777627` 跳到的是 **0x777627**，而 0x777627 之后
（经 `0x77764C` 分支、`0x77766C je`）**继续流向 0x777687**。

⇒ **IME 消息和普通消息在 0x777627 汇合，之后一起流向 0x777687。**
按 §389 的写法，ret 尺寸**确实会影响** 0x777687 处的 esp —— 降级判断是错的。

---

## 二、但结论「互斥」仍然成立 —— 真正的机制是**IME 段自己返回**

继续往下查 IME 段（`0x7775E7`）的出口：

```asm
0x777602  test eax, eax
0x777604  je  0x777A5B        ; ─┐
0x77760A  ...                 ;  │
0x77761A  call [0x7e1394]     ;  │  DefWindowProcA
0x777620  pop edi             ;  │
0x777621  pop esi             ;  │
0x777622  pop ebx             ;  │
0x777623  pop ecx             ;  │
0x777624  ret 0x10            ; ─┤ 出口 1：函数返回
                              ;  │
0x777A5B  pop edi             ; ─┤ 出口 2（je 目标）
0x777A5C  pop esi             ;  │
0x777A5D  xor eax, eax        ;  │
0x777A5F  pop ebx             ;  │
0x777A60  pop ecx             ;  │
0x777A61  ret 0x10            ; ─┘ 也是函数返回
```

**IME 段的两条出口都是 `ret 0x10` —— 直接返回，不回落主线。**

所以互斥成立，但**机制是「IME 段终结了自己」**，不是「msg 值不同」。

---

## 三、为什么这个区别重要

| | §389 的说法 | 真实情况 |
|:--|:--|:--|
| 互斥成立？ | 是 | 是 |
| 机制 | msg 值不同 ⇒ 走不同路 | **IME 段自己 ret** |
| 若 ret≠4，影响 0x777687 吗 | 按此说法**不影响** | 不影响（但理由不同） |
| 若 IME 段被改成不返回 | 互斥仍成立（按错理由） | **互斥破裂** |

最后一行是关键：按 §389 的错误理由，无论代码怎么改，只要 msg 不同就"互斥"；
按真实机制，**只要 IME 段开始回落主线，互斥就没了**。两者对代码变化的敏感度完全不同。

---

## 四、修法：用控制流可达性取代地址比较

第一版我写的是：

```python
check("★ IME 段出口 0x777A5B 在 0x777687 之后（不同路径，非汇合）",
      0x777A5B > 0x777687, ...)      # ← 弱断言
```

**地址大小与路径关系无关**，这是弱断言。改成从出口沿控制流走：

```python
def reaches(start, target, limit=64):
    """从 start 沿控制流（不跨 ret）走，是否到达 target。"""
    seen, work = set(), [start]
    while work and n < limit:
        pc = work.pop()
        if pc == target: return True
        ins = decode(pc)
        if ins.mnemonic == "ret":  continue      # 返回 ⇒ 路径终止
        if ins.mnemonic == "jmp":  work.append(target_of_jmp)
        if jcc:                    work.append(taken); work.append(fallthrough)
        else:                      work.append(next_insn)
    return False
```

断言：

```python
check("★★ IME 段出口 0x777A5B 沿控制流**到不了** 0x777687", not reaches(0x777A5B, 0x777687))
check("★★ IME 段出口 0x777624 之后（ret）到不了 0x777687", not reaches(0x777624, 0x777687))
check("正控 主线 0x777627 **能**到 0x777687（reaches 有区分力）", reaches(0x777627, 0x777687))
```

★ **正控是必需的**：只断言「到不了」的话，一个恒返回 False 的 `reaches()`
会让所有断言都通过。正控证明它确实能区分。

---

## 五、灵敏度实证（`_vtable_slot14.py` 17 → 24 条）

| 负控 | 注入 | exit | FAIL |
|:--|:--|--:|--:|
| P0 | baseline | 0 | 0 |
| P15 | 二进制：`0x777A61` 的 `ret 0x10` → `ret 0` | 1 | 1 |
| **P16** | 二进制：`0x777604 je 0x777A5B` → **`jmp 0x777627`（伪造回落）** | 1 | 1 |
| P17 | 源码：反转 IME 不可达断言 | 1 | 1 |

**P16 是最关键的一条**：它把 IME 段强行改成回落到主线，
门禁立刻变红 —— 证明「互斥」是**被测出来的**，不是自说自话。

---

## 六、门禁状态（十套全绿）

| 门禁 | 结果 |
|:--|:--|
| `_vtable_slot14.py` | **24/24 PASS**（原 17） |
| `_verify_stack_offset.py` | 81/81 PASS |
| `_esp_bfs.py` | 14/14 PASS |
| `_verify_wmclose_chain.py` | 20/20 PASS |
| `_survey_6930a0.py` | 2/2 PASS |
| `_selftest_todo6_verdict.py` | 10/10 PASS |
| `_verify_a8_runtime.py` | 11/11 PASS |
| `_verify_probe_a4a7a8.py` | 21/21 PASS |
| `_todo7_creation_trigger.py` | 16/16 PASS |
| `_verify_wer_sig.py`（harness6） | 10/10 PASS |

---

## 七、对既有结论的影响

| 结论 | 状态 |
|:--|:--|
| `0x777687` 处 `[esp+0x18]` = msg | ✅ 不变 |
| slot14 ret = 4（实测） | ✅ 不变 |
| 唯一性（5 构造点 × 1 vtable） | ✅ 不变 |
| 「两路互斥」**结论** | ✅ 不变 |
| 「两路互斥」**理由** | ❌ **作废**（§389 写错，本节点明真实机制） |
| 风险降级 | ✅ 仍成立（机制更硬：IME 段自己 ret） |

---

## 八、教训

**结论对 ≠ 推理对。** §389 的「互斥」结论碰巧是对的，但理由经不起追问：
按它写的机制，我无法解释「为什么 0x7775E5 jne 0x777627 之后不再流向 0x777687」。

这与 §388 的「计数虚高」是同一族：**我满足于结论看起来对，没检查支撑它的推理链是否闭合。**

判据：一个结论给出后，问自己「如果按我写的机制，能否推出这个结论」。
本例中「msg 不同 ⇒ 走不同路」推不出「不流向 0x777687」，因为两条路在 0x777627 汇合。

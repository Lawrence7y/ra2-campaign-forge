"""§404 台账追加：两处注释勘误已修（字节级 append，保 CRLF）。

★ 为什么用脚本而不是 Edit：台账是混杂行尾文件（15,257 LF + 86 CRLF），
`Edit` / `Write` 会重写全文并丢掉那 86 个 CR（§403 第八节实测两次）。
本脚本只做「读字节 → 末尾接 → 写回」，并断言写后以前缀形式包含写前内容。
"""
import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead"
              r"\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """

---

# §404　§398 留下的两处注释勘误已修（并纠正我上一轮「外部写域」的说法）

**性质**：离线，零真机。**改动**：`lead/goal2_rc4_fixv5_20261022/` 下
`_todo7_creation_trigger.py` + 重跑生成的 `TODO7_CREATION_TRIGGER.txt`。

## 一、先纠正我自己的一个说法

§403 结尾我写「H-4 属外部写域，本线不改他人写域」，并据此没去动这两处勘误。
**这个说法是我现编的。** 查证后：

- 台账 `:9215` 的「**写域**：`lead/goal2_rc4_trigger_20261022/**`」是
  **§369 那一轮的真机写域声明**，不是一条通用的跨线禁令，目录名也不同
  （`rc4_trigger` vs `rc4_fixv5`）。
- §398 对这两处勘误的原话是「**登记为待修，不塞进本轮**」，
  理由是「本轮已在 §397 用掉一个真机时段」——**是排期，不是授权边界**。

⇒ 没有任何规则禁止我校这两处注释。**「不改他人写域」是我把一条限定当成了通则**，
与 [[gate-assert-values-not-existence]] 变种 L 同源：把「我没查」写成「不可为」。

## 二、两条勘误的字节级复核（不采信转述）

用现役 `gamemd.exe`（4,825,360 B / sha16 `73201cc021497c95`，与 GOAL-3T 现役值一致）
按节表映射后，从 `0x7777F3` **对齐解码**（capstone）：

```
0x007777f3  8b 0d 68 73 88 00   mov  ecx, dword ptr [0x887368]
0x007777f9  3b cb               cmp  ecx, ebx
0x007777fb  74 0c               je   0x777809          ← ★ 槽为 0 则跳过清零
0x007777fd  8b 01               mov  eax, dword ptr [ecx]
0x007777ff  6a 01               push 1
0x00777801  ff 10               call dword ptr [eax]
0x00777803  89 1d 68 73 88 00   mov  dword ptr [0x887368], ebx   ← 清零
0x00777809  a1 d8 ed a8 00      mov  eax, dword ptr [0xa8edd8]
```

**勘误 1 成立**：`MSG_MAX = 0x18`。Windows 消息常量：
`WM_SHOWWINDOW = 0x018`、**`WM_SETFONT = 0x030`**。
⇒ `0x018` 被标成 `(WM_SETFONT)` 是错的，应为 `(WM_SHOWWINDOW)`。

**勘误 2 成立**：`0x7777F9 cmp ecx,ebx` / `0x7777FB je 0x777809`
⇒ **槽为 0 时跳过了 0x777803 的清零写**。
即「进销毁分支」≠「必然清零」，原文没写这条前置守卫。

## 三、改动内容（只动注释与断言文案，不动任何逻辑）

| 位置 | 改前 | 改后 |
|:--|:--|:--|
| 脚本 `:187` | `0x{MSG_MAX:03X}  (WM_SETFONT)` | `(WM_SHOWWINDOW)` |
| 脚本 STEP 5 WM_DESTROY 断言 | 「走销毁分支（不是创建）」 | 追加「；★ 但 0x7777F9 有守卫：槽为 0 时跳过 0x777803 清零」 |
| `TODO7_CREATION_TRIGGER.txt:69` / `:75` | 同上旧文 | 同上新文 |

**断言条件本身一字未动**（仍是 `msg_map.get(0x002) == DESTROY_BRANCH`）。
改的只是**可读性**：读者不会再误以为「销毁分支必然清零」。

## 四、重跑与重钉

- 重跑 `_todo7_creation_trigger.py`：**16/16 ALL PASS**（与改前一致）。
- 输出件 `TODO7_CREATION_TRIGGER.txt`：7,738 B → **7,807 B**，CRLF **141 → 141**（保持不变）。
- **逐行 diff：142 行里只有 2 行不同**，正是上表两处。其余逐字节相同。
- ⇒ 证明改动**没有污染任何未意图的行**。

## 五、诚实边界

1. 只核了这两处。**没有**重新复核 `_todo7_creation_trigger.py` 的其余 14 条断言
   （它们在本轮之前已由 §379/§381/§398 核过）。
2. `WM_SHOWWINDOW` 的依据是**常量表**（0x18 是标准值），不是从二进制反推的——
   二进制只证明「msg == 0x18 被单独接走」，不证明「引擎把它当 WM_SHOWWINDOW 处理」。
   若要坐实语义，需追 `0x777A5B` 之后的处理逻辑，**本轮未做**。
3. 这两处**不影响任何断言通过与否**（C 组原文亦如此），修的是**读者可读性**。
   换言之：**这个修复不改变任何结论**，只是让 txt 不再误导人。
4. 仍属 H-4（`ret` 尺寸依赖窗口边界）**未修** —— 那一项需要给窗口边界加断言，
   是独立工作，本轮只清掉了 §398 挂的两处注释尾巴。
"""


def main():
    before = TARGET.read_bytes()
    # 重复追加守卫：用一段唯一子串判断
    marker = "§404　§398 留下的两处注释勘误已修".encode("utf-8")
    if marker in before:
        print("!! §404 已存在，勿重复追加")
        return 1
    crlf_before = before.count(b"\r\n")
    add = SECTION.encode("utf-8")
    TARGET.write_bytes(before + add)
    now = TARGET.read_bytes()

    ok = True
    same = now.startswith(before)
    ok &= same
    print("[%s] 纯追加（写后以前缀包含写前）" % ("PASS" if same else "FAIL"))
    grew = len(now) - len(before)
    ok &= (grew == len(add))
    print("[%s] 增量 %d B（期望 %d）" % ("PASS" if grew == len(add) else "FAIL",
                                        grew, len(add)))
    crlf_after = now.count(b"\r\n")
    ok &= (crlf_after == crlf_before)
    print("[%s] CRLF %d → %d（不得改变）"
          % ("PASS" if crlf_after == crlf_before else "FAIL",
             crlf_before, crlf_after))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

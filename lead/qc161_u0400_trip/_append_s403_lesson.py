"""把 §403 第八节（CRLF 污染教训）以字节级追加方式写入台账。

## 为什么单独做这一步

台账是**混杂行尾**文件（15,257 bare-LF + 86 CRLF）。
两种常规写法都会破坏它：
  - `Edit` / `Write` 工具：重写全文 ⇒ 86 处 CRLF 全部丢（本轮已实测两次）
  - `_fix_ledger_crlf.py --write`：从 `git show HEAD` 重建 ⇒ 会冲掉未提交的追加

故本脚本的做法是**纯追加**：读现有字节、只在末尾接新内容、写回。
并在写前断言「写后新内容 == 写前内容 + 追加段」。
"""
import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead"
              r"\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SECTION = """

---

## 八、★ 本轮自己造成并修复的一处污染：台账 CRLF 被误转 LF

**现象**：§403 提交后 `git show --stat` 显示台账 `+171 / −86`。纯追加不该有删除。

**根因**：该文件行尾**本来就是混杂的**（15,257 bare-LF + **86 CRLF**，
那 86 行是 §399 整节）。本轮对它做过的**任何整体重写**都会把这 86 个 CR 丢掉。
已实测两种触发路径：

| 触发 | 后果 |
|:--|:--|
| `Edit` 工具改一行 | **整文件重写** ⇒ CRLF 86 → **0**（本轮实测两次） |
| `_fix_ledger_crlf.py --write` | 从 `git show HEAD` 重建 ⇒ 覆盖掉未提交的追加 |

**实测证据**（提交后的 `git show <ref>:<file>` 字节统计）：
```
HEAD~2  CRLF=86
HEAD~1  CRLF=86
HEAD    CRLF=0     ← §403 这一轮
```

**修法**：`_fix_ledger_crlf.py` —— 不重写全文，只对 14948–15033（0-based）
这 86 行补回 `\\r`。五项自检全过：
① 前缀逐字节相同 ② 区间内 86 行全恢复 CR ③ 区间内容（忽略 CR）不变
④ 其后本轮追加内容逐字节相同 ⑤ 总 CRLF 回到 86。

**修复后复核**：`new.startswith(old)` = **True**（对 HEAD~1），纯追加，
CRLF 86 = 86。

**教训（新增，可复用）**：
1. **对混杂行尾文件，`Edit` 是危险工具**——它改一行也会重写全文。
   追加只能用**字节级 append**（本脚本的做法）。
2. **用 `git diff --stat` 的删除数当门禁**：「纯追加」必须显示 `−0`。
   出现删除先怀疑行尾，不要解释成「diff 对齐假象」
   （我第一反应正是这个，`startswith` 一测就否掉了）。
3. **修复脚本不要从 `git show HEAD` 重建**——那会吃掉未提交的新内容。
   要么先提交再修，要么改成「读工作区字节 + 只补 CR」。
4. **不要"顺手全局规范化"**：该文件 99.4% 是 LF，
   全局转 LF 会再改 86 行、全局转 CRLF 会改 15,257 行。只能按行号区间精准补。
5. 与 [[crlf-diff-roundtrip-traps]] 同源：那条讲**生成 diff 时**的坑，
   这条讲**编辑/追加时**的坑。

"""


def main():
    before = TARGET.read_bytes()
    if b"\xe5\x85\xab\xe3\x80\x81\xe2\x98\x85 \xe6\x9c\xac\xe8\xbd\xae" in before:
        print("!! 第八节已存在，勿重复追加")
        return 1
    crlf_before = before.count(b"\r\n")
    add = SECTION.encode("utf-8")
    after = before + add
    TARGET.write_bytes(after)

    # 自检
    now = TARGET.read_bytes()
    ok = True
    same_prefix = now.startswith(before)
    ok &= same_prefix
    print("[%s] 写后内容以写前内容为前缀（纯追加）" % ("PASS" if same_prefix else "FAIL"))
    grew = len(now) - len(before)
    ok &= (grew == len(add))
    print("[%s] 增量 = %d B（期望 %d）" % ("PASS" if grew == len(add) else "FAIL",
                                          grew, len(add)))
    crlf_after = now.count(b"\r\n")
    ok &= (crlf_after == crlf_before)
    print("[%s] CRLF %d → %d（不得改变）"
          % ("PASS" if crlf_after == crlf_before else "FAIL",
             crlf_before, crlf_after))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

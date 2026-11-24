#!/usr/bin/env python3
"""Fix the one outright error in §826-3 (FUN_006922e0 DOES have a direct caller)
and append §828: adversarial-verification record + new facts.

Anchored, exact-once replacements; aborts loudly otherwise.
"""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
src = io.open(LEDGER, encoding="utf-8").read()
orig_len = len(src)


def replace_once(s, old, new, tag):
    n = s.count(old)
    if n != 1:
        sys.exit("ABORT %s: anchor count=%d" % (tag, n))
    return s.replace(old, new)


# ---- 1. the factual error: 0x6922E0 has a direct caller @0x005BDF1F
old1 = """- **§826-3 [已证·"静态找不到调用者"不等于不可达：3 处是靠虚表派发的]**
  - `FUN_006922e0`（29 B）**没有任何直接代码调用者**，但其地址出现在 `.rdata` `0x007F10BC`，"""
new1 = """- **§826-3 [已证·"静态找不到调用者"不等于不可达：3 处是靠虚表派发的]**
  - ⚠️ **2026-11-15 更正**：原文写"`FUN_006922e0` 没有任何直接代码调用者"，**这是错的**。
    它确有 **1 个直接调用者 `@0x005BDF1F`**（Ghidra 与 capstone 双向一致）；
    同时它的地址也出现在 `.rdata` `0x007F10BC`（虚表槽）。**两条入口都存在。**
  - 其地址出现在 `.rdata` `0x007F10BC`，"""
src = replace_once(src, old1, new1, "826-3")

# ---- 2. strengthen the caveat in §826-4's dead-code claim
old2 = """  - ⇒ 站点 15、16、17 属死代码；**但"死"是就静态映像而言**（无任何静态引用），若后续发现计算地址派发需重判（§826-5 已给证伪路径）。"""
new2 = """  - ⇒ 站点 15、16、17 属**"静态零引用"**；**但"死"是就静态映像而言**，若后续发现计算地址派发需重判（§826-5 已给证伪路径）。
  - ⚠️ **措辞纪律（复核后收紧）**：`0x887368` 等 BSS 区在磁盘上**没有字节**，
    运行期写入的函数指针**静态不可判定**（本项目已因越界读 BSS 得出过"该处是字符串"的错误结论，见 §809）。
    因此这里只能主张 **"四类静态引用为零"**，**不能升格为"运行期不可达"**。"""
src = replace_once(src, old2, new2, "826-4")

extra = """

## §828 · **对抗性独立复核记录：C1 成立、C2 部分、C3 部分（并纠正 §826-3 的实错）、C4 被推翻**（2026-11-15 10:20）

- **§828-1 [已证·复核方式]** 另派独立子代理，**不给它我的脚本**，只给结论 + 二进制，
  要求它自己从字节出发判定 CONFIRMED / REFUTED / PARTIALLY / INCONCLUSIVE。
  它产出的每一条我再用 `W127_reach\verify_ds_claims.py` / `verify_vtables.py` 独立复算（不采信它的断言）。

- **§828-2 [已证·处置结果]**
  | 编号 | 复核判定 | 我的复算 | 处置 |
  |---|---|---|---|
  | C1（69 处载入 / 20 处调用） | CONFIRMED，但指出"24 字节窗口"定义不自洽 | 一致 | **采纳**：改述为"ECX 保持判定"，真实数为 **28**（见 §825-2/§825-4） |
  | C2（`0x6D14F0/0x6D1570/0x6D15F0` 无静态引用） | 四类引用为零**成立**；但"不可达"升格不成立 | 一致 | **采纳**：§826-4 已收紧为"静态零引用" |
  | C3（`0x6922E0` 是 ScrollClass 槽 10、`0x6D0680` 唯一调用者） | 槽位与类名成立；"唯一调用者"**不成立** | **确证我错** | **已改**（§826-3）：`0x6922E0` 有直接调用者 `@0x005BDF1F`；`0x6D0680` 还直接占据 TabClass 槽 10 |
  | C4（`FUN_004FC0B0` 仅 1 个调用者 + 能连到消息泵） | **REFUTED**：向上链路在虚派发处断掉 | 部分采纳（见下） | **采纳其断链结论，但否掉其"2 个代码引用"** |

- **§828-3 [已证·复核方给出的新事实（我已逐条复算，全部成立）]**
  1. **`FUN_004FC0B0` 的调用者在 `HouseClass` 虚方法里**：
     `call 0x4FC0B0 @0x004F8F82` → 所属函数 **`0x004F8440`**（`0x4F842E ret` + nop 填充后 `sub esp,0x4c` 起，是干净入口）。
     `0x4F8440` **零直接调用者**，唯一静态引用是 **`.rdata:0x007EA8FC` = 虚表 `0x007EA8A0` 槽 23**，
     RTTI 反查（我逐字节读：`[vt-4]→COL 0x00802A28→TD 0x00824500`，名字内联在 `TD+0x08`）= **`.?AVHouseClass@@`**。
     ⇒ **静态可达链在"虚调用"处终止**：真实崩溃证明它确实在生产路径上被执行（`except.txt` 的栈），
     但**无法用静态调用图证明到达消息泵**。这是"经验已证、静态不可证"的典型两面。
  2. **`FUN_006d14f0` 的体在 `FUN_006d1660` 内部有一份近似副本**：
     `0x6D14F0` 起的 116 字节与 `+0x181`（`0x6D1671` 起）逐字节比对 **105/116 相同**；
     按指令对齐（`0x6D14F9` vs `0x6D167A`）**35 条中 32 条助记符同类**。
     ⚠️ 复核方报的是"32/32 逐指令一致"，**我复算后不成立**（并非逐字节一致），此处按 105/116 记录。
     ⇒ 证据指向**内联展开/编译器复制**，与"被取代的旧实现"一致，但**不足以单独定案**。
  3. **MSVC RTTI 的 TD 布局（可复用事实）**：名字是 `TD+0x08` 处的**内联字符数组**，不是指针；
     COL 布局 `{signature,+0x04,+0x08,pTypeDescriptor@+0x0C,pSelf@+0x10}`，本项目 `signature` 全为 0。
     （把 `TD+0x08` 当指针读会得到垃圾值 `0x56413F2E`。）
  4. **该 PE 没有 `.reloc` 目录** ⇒ 磁盘上的函数指针就是运行期值，不存在重定位导致的漏检
     （这条支持"四类静态引用为零"的强度）。

- **§828-4 [已证·我否掉复核方的一条主张]**
  - 复核方称 "`FUN_004FC0B0` 有 2 个静态代码引用：`call@0x4F8F82` 与 `jmp@0x4FC6A0`"。
  - 我用 capstone 扫全部 `call/jmp` 直接目标：**指向 `0x4FC0B0` 的只有 1 处 `call@0x4F8F82`**。
    它说的 `jmp@0x4FC6A0` 目标实为 **`0x4FC67B`**（该函数自身的清理跳板），不是 `0x4FC0B0`。
  - ⇒ **"仅 1 个静态调用者"成立**；但"能向上连到消息泵"**不成立**（同 §828-3.1）。

- **§828-5 [已证·虚表归属全表（用原始字节 + RTTI 复算，9/9 通过）]**
  | 虚表 | 槽 | 槽值 | 类名（RTTI） | 归属 |
  |---|---|---|---|---|
  | `0x007F0344` | 34 | `0x00654320` | `.?AVRadarClass@@` | 站点 1 |
  | `0x007EDFB4` | 34 | `0x006ABD30` | `.?AVTabClass@@` | 站点 2、3 |
  | `0x007F1094` | 34 | `0x006ABD30` | `.?AVScrollClass@@` | 站点 2、3 |
  | `0x007F3058` | 34 | `0x006ABD30` | `.?AVSidebarClass@@` | 站点 2、3 |
  | `0x007EDFB4` | 54 | `0x006D04F0` | `.?AVTabClass@@` | 站点 4、5、6 |
  | `0x007F1094` | 54 | `0x006D04F0` | `.?AVScrollClass@@` | 站点 4、5、6 |
  | `0x007EDFB4` | 10 | `0x006D0680` | `.?AVTabClass@@` | 站点 7、8、9 |
  | `0x007F1094` | 10 | `0x006922E0` | `.?AVScrollClass@@` | 站点 7–9 的包装层 |
  | `0x007EA8A0` | 23 | `0x004F8440` | `.?AVHouseClass@@` | 崩溃入口的调用者 |
  - ⇒ **同一套"清理 tooltip 容器"的方法被多个 UI 类各自实现**（Tab/Scroll/Sidebar/Radar 槽 34；Tab/Scroll 槽 54/10）。
  - ⇒ **这也是"②-a 一旦触发就会在多种界面状态下崩"的结构性原因**：不是在一条孤立路径上，而是散落在所有 UI 控件的清理钩子里。

- **§828-6 [未证]** 复核方提到 `0x007E1958` 也是一个候选"虚表"（`0x6ABD30` 的第 4 处数据指针）。
  我复算：`[0x007E1954]` 不是合法 COL（越界），**它更像普通函数指针表而非虚表**，未深究。
"""

if "## §828" in src:
    sys.exit("ABORT: §828 already present")
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)

back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (orig_len, len(back)))
for k in ("## §828", "§826-3", "只会得到垃圾值" if False else "这是错的",
          "105/116", "HouseClass"):
    print("  %-14s count=%d" % (k, back.count(k)))

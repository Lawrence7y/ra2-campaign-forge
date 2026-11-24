#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update SESSION_HANDOVER_R10.md with the §859..§868 round."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

# ---- 1. extend the overturned-conclusions table with this round ----
OLD_ROW = ('| `DAT_00a8eb44` 是"单位/对象主表" | **错**：它是 `BuildingClass::Array.Items`；单位表是 `0x8B4108` | **§859** |\n')
NEW_ROWS = OLD_ROW + (
    '| `0xB0F720` 是"全部对象的注册表" | **错**：`AbstractClass*` 有 **12 个**数组；`FootClass` 构造器只登记自己的表、对 `0xB0F720` **0 引用** | **§867 / §868** |\n'
    '| ②-a 修复面 = **50 处 / 6 例程** | **错**：`0x7241A0` 有 **14** 个调用点（我只算了 1 个）⇒ 合计 **54** | **§865** |\n'
    '| `.text` 覆盖 **79.5%** | **低估**：真实 **86.39%**（找回 5,875 个函数 / 281,623 B） | **§864** |\n'
    '| 引擎实例数组 **49 个** | **错**：全量枚举得 **142 个**（漏 93 个） | **§867** |\n'
    '| 那 370 个"不可枚举"条目未解释 | **已解**：是 `EXTERNAL` 空间的 PE 导入函数；**12,916 就是完整函数数** | **§860** |\n'
    '| `AbstractClass` 只有 1 个 vptr | **错**：**4 个**（`+0/+4/+8/+0xC`），4 基类多继承 | **§862** |\n'
)
if h.count(OLD_ROW) != 1:
    raise SystemExit("REFUSE: overturned-table anchor not unique")
h = h.replace(OLD_ROW, NEW_ROWS)
h = h.replace("### ⚠️ 后续接手必读：交付过程中被推翻的旧结论（8 条）",
              "### ⚠️ 后续接手必读：交付过程中被推翻的旧结论（14 条）")

# ---- 2. insert a new section before the anchor ----
SEC = """### 0'.5 **2026-11-15 第二轮（§859–§868）：对抗性复核推翻了我自己 4 条结论，也闭合了 2 条旧悬案**

> 用户令："多派 glm 模型子代理" → 发现 GLM 并发上限 3 → DeepSeek 补剩余通道。
> 本节只列**结论**，证据在台账对应节。

**已闭合（可以不再追）**
| 项 | 结论 | 节 |
|---|---|---|
| 370 个"计入总数但不可枚举" | = `EXTERNAL` 空间里的 PE **导入函数**。`getFunctionCount()` 统计全部空间，`getFunctions(true)` 只走 `ram`。**12,916 = 引擎完整函数数，无未解释余量** | §860 |
| `AbstractClass::Array` 是否完整注册表 | **已证否**（不是"未证"）。`FootClass` 构造器登记自己的表、对 `0xB0F720` **0 引用**；47 个 `0x4101F0` 调用者里只有 3 个内联 push | §868 |

**被推翻 / 修正的我方结论**

1. **②-a 修复面 50 → 54，且 `0x7241A0` 从 1 个调用点变成 14 个**（§865）。
   **这是唯一有安全后果的修正**：按旧清单打补丁会漏 6 条未守卫路径。
   14 个地址已列出（`0x48CE5D 0x4E1FA9 0x52DB04 0x55D0AB 0x55D173 0x55D202 0x5C4BE3`
   `0x683F61 0x684026 0x685D90 0x6863AF 0x68643E 0x686553 0x69BBA8`）。
   - **`W128_fix\\entries.json`/`stubs.json`/`sites.json` 是按旧清单生成的，必须重建。**
   - 务实建议：**在函数入口守卫**（`ecx==0` 直接返回），而不是逐调用点守卫——
     这样 14 个点全覆盖，也避免 §825 的"崩溃点平移"。
2. **`.text` 覆盖率 79.45% → 86.39%**（§864）。找回 5,875 个函数 / 281,623 B。
   我方**全量验证**过：0 个与图谱重叠、0 个自重叠、0 个无法解码、98.4% 以 `ret` 结尾。
   - ⚠️ 但"漏了函数"≠"漏了重要函数"：852 个只有 prologue 证据。**不能说"找到 5,875 个新功能"。**
3. **实例数组 49 → 142**（§867）。`AbstractClass*` 有 **12 个**、`ObjectClass*` 3 个、
   `TechnoClass*` 4 个、`BulletClass*` 2 个、`BuildingClass*` 2 个、`MixFileClass*` 4 个。
4. **`AbstractClass` 有 4 个 vptr**（§862），"vptr 在 +0"只对单继承类成立。
   `AbstractClass::AbstractClass` = `0x004101F0`，**28 字节 / 5 条指令 / `n_callees=0` / 不登记**。

**经受住对抗性复核而未被推翻的**（§868-6）
`49 数组表`的身份层面全部 CONFIRMED：布局 `+0/+4/+8/+0xC/+0xD/+0x10/+0x14`（increment=10）、
`BuildingClass@0xA8EB40`、`UnitClass@0x8B4108`（且**载具只有这一个向量**）、
`HouseClass@0xA80228`（飞机是 `0xA8E390`）、`FootClass@0x8B3DC0`、`AbstractClass` 4 vptr。

**两个必须记住的陷阱**
1. **`function_atlas.tsv` 的 `size` 列是十进制**，`entry` 是十六进制（§863）。按 hex 读 size 会让 **81.2%** 越界。
   已审计：仓库内**所有**解析点口径正确，故 79.5%/64.8% 等历史数字**无需重算**。
2. **`TypeDescriptor` 的名字内联在 `TD+0x08`**，不是 `char*`。
   这一点已让**两个独立实现各错一次**（我 §859-3、复核 §868-5）。
   **凡"扫描得到 0 个结果"，必须先怀疑扫描器。**

**新增未闭合**
1. 那 12 个 `AbstractClass*` 数组各自的用途**完全未知**。
2. `0x7241A0` 的 14 个调用点里几个未守卫：**我判 13:1，复核判 7:7，未定谳**（§866）。
3. `ClassDescriptor` 的 `+0x40` 自校验在本镜像**对所有类失败** ⇒ **继承关系无法从 RTTI 验证**。
4. 143 个数组**尚未合并进 `instance_arrays.tsv`**；合并会改变所有下游分母，需单独决定。

---

"""
ANCH = "## 0. 锚点（未变）"
if "0'.5 " in h and "§859–§868" in h:
    raise SystemExit("REFUSE: 0'.5 already present")
if h.count(ANCH) != 1:
    raise SystemExit("REFUSE: anchor not unique")
h = h.replace(ANCH, SEC + ANCH)

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover updated; size=%d bytes; control chars=%d" % (len(h.encode("utf-8")), len(bad)))

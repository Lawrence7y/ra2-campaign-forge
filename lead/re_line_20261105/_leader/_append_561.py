# -*- coding: utf-8 -*-
"""Append §561: my COUNT-vs-KIND parsing error corrected (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7561"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §561 · 我把 `[Actions]` 的 **COUNT 字段当成了动作 kind**：U0400 的 15 条动作**全是 99**，不是 `{2,4,9}`（2026-11-05）

> **本节的地位**：**公开自我订正**，订正 §556 第二节与 §559 第三节两处引用。
> 由 W1 的 `Q3B_MAPS.md`（`lead/re_line_20261105/W1_HOLD_SURFACE/sections/Q3B_MAPS.md`，39 KB）
> 指出，我逐字节复算确认。

### 一、错在哪

`[Actions]` 段的行格式（由本项目自身代码写死，`ra2forge/triggers.py:19-20` 与 `maplib.py:463-472`）：

```
ID = COUNT, (CODE, P1..P7) × COUNT        # 每组 8 个 token
```

即**行首第一个数字是「这条触发器有几个动作」（COUNT），不是动作号（CODE）**。

我此前对 `ra2youli/[2]0LoadBench_U0400.yrm` 解析时，取了 `v[0]` 当动作号，
得到「`{2,4,9}`」并写进了 §556 与 §559。**那是 COUNT = 9/4/2，不是 kind。**

### 二、正确结果（我逐字节复算，与 Q3b 完全一致）

`U0400` 的 `[Actions]` 真貌：

```
03F504FC=9,99,7,_Amb_BirdsTemperate1,0,0,0,0,AE,99,7,...（共 9 组）
03F50E1C=4,99,7,_Amb_UrbanMurmur1,0,0,0,0,AA,...（共 4 组）
03F51C4C=2,99,7,_Amb_WindPlains,0,0,0,0,AN,99,7,...（共 2 组）
```

⇒ **COUNT = 9 / 4 / 2（合计 15 条动作），每一条的 CODE 都是 `99`。**
`99` 在 265 张图的全量直方图里出现 **4,421 次**（占 83%），是环境音效类动作。

**全量复算（我实跑，独立于 Q3b，结果逐项一致）**：

```
files=265   with_[Actions]=154   records=1261   actions=5309
kinds 34 种，最高 {99:4421, 54:177, 53:145, 119:81, 14:62, ...}
has110: 0    has127: 0    has117: 0
```

⇒ **Q3b 的 265 / 154 / 1261 / 5309 / 34 / 110=0 / 127=0 全部复现**，Q3b 正确。

### 三、连带影响（两处，方向不同）

**(a) 结论方向不变，反而更强**
§556 与 §559 要证的是「测量图里没有 110/127/117」。真实结果显示 U0400 的 15 条动作
**全部是环境音效（kind 99）**，连「Lose/CreateTeam/FireSale」都没有。
⇒ **测量图比我说得更"干净"**：连胜负判定与建队动作都不存在。
**§559「265 张图零 110/127/117」的结论不受影响**（该结论来自 Q3b 的全量 kind 直方图，口径正确）。

**(b) 但 §556/§559 里那几个具体数字必须作废**
凡我写「U0400 = `{2,4,9}`」、「ECH 只有 `{(1,11)}`」的地方，**全部是 COUNT 误读**，
正确读法应为「U0400 的 COUNT 为 9/4/2，动作 CODE 全为 99」。
`ECH01/02/03` 那三个「`{(1,11)}`」同理：是 COUNT=(3 条记录的各 COUNT)，不是 kind，
**本轮我未重新解析 ECH 的 CODE**（标未验）。

### 四、这是同一条纪律的第四次触发，但形态有新意

前三次（§558/§559/§560）都是「把间接线索当直接证据」——读文件不读注释、看 call 不进函数体、
无段当无行为。**这一次是更基础的一类：我没有先确认字段口径就统计。**

而且这次错误**存活了 5 轮**（§556 12:4x → §561 15:1x），
期间 §559 还把它当作「我亲验的事实」二次引用。
**抓到我的是子代理**（Q3b 的 `Q3B_MAPS.md` 甚至在 §0 就直接点名「`U0400={2,4,9}` 不是 kind 直方图」）。

⇒ **纪律第四条**：**统计任何结构化文本前，先确定「第几个字段是什么」，
并从产出该文件的代码（本例 `ra2forge/maplib.py:463-472`）反向核对格式。**
已知格式定义在仓内，**没有理由靠猜**。

### 五、诚实账

1. **我亲验**：`U0400` 的 `[Actions]` 原始字节逐行解析（COUNT=9/4/2、15 条全 CODE=99）；
   全量 265 图的 kind 直方图（`{99:4421, ..., 131:5}`）、`has110/127/117 = 0`；
   与 Q3b 的 265/154/1261/5309/34 五数逐项吻合。
2. **我未验**：`ECH01/02/03` 的 CODE 直方图（只知我此前的 `{(1,11)}` 是 COUNT 误读，不知道正确值）。
3. **我未验**：`99` 这个 kind 的确切名称（我据参数形态 `7,_Amb_*,...` 判为环境音效类，
   与 `trigger_system_manifest.md` 的 kind 99 条目**未逐条对照**）。
4. **我未验**：W1 的 `Q3B_MAPS.md` 其余推论（它现在是未过复核的初稿）。
5. 本节**不改变任何已裁结论**；D-16/D-15/D-13 处置不变；E3 维持「暂停」。
6. 本轮**零真机**、**零母本改动**、**未 commit**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))

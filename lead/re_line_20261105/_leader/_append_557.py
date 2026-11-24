# -*- coding: utf-8 -*-
"""Append §557: hold-counter script entry surface corrected (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7557"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
# 两侧都按行归一化再比（HEAD 含 66 个 CR，工作树零 CR）——只比归一化形状，不比原始字节
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d (norm %d) wt=%d" % (len(head), len(head.replace(b"\r\n", b"\n")), len(wt)))

SECTION = u"""
## §557 · 挂起计数器的脚本入口**不止** 110/127：动作 117 与引擎影片流程都是入口（2026-11-05）

> **本节的地位**：**订正 §556 第二节的外推**。§556 写「第三个挂起入口不是脚本动作 ⇒ 引擎内部状态机，无脚本入口」，
> 并据此在 §556 第二节做了「测量语料内帧钟停摆不能用地图脚本解释」的阳性排除。
> **本轮 W1 回件（`dwfrun-3eee0767`，`magpie/work/cn:hy4free$high`）推翻了这个外推**，
> 我逐字节复核其关键断言后接受订正。**§556 的「U0400 无 110/127」这一事实不变，但外推作废。**
> 回件：`lead/re_line_20261105/W1_HOLD_SURFACE/sections/Q1_B45B68.md`、`Q2_6579E0.md`（**均属 phase-1 初稿，尚未过复核阶段**）。

### 一、订正的核心：`0xB45B68` 是**影片播放器向量的 Count**，不是「布尔沿对象」

W1 的 Q1 定谳（我已复核写点数量）：`0xB45B68` = 全局 `DynamicVectorClass<BinkMoviePlayer*>`
（基址 `0xB45B58`）的 **Count 字段**。`0x6579E0` 用 `setg bl` 把它折成布尔沿，
沿翻正 → `call 0x684060(0)`（挂起），沿翻回 → `call 0x684180()`（释放）。
⇒ §556 写的「布尔沿触发对象」是**派生量**，不是它本身。

### 二、★ 动作 117 是**第四条**脚本入口（字节自证，我亲验）

| 动作 | kind | 内联派发块 | 关键字节 | 语义 |
|---|---|---|---|---|
| **117 PlayIngameMovieAndPause** | `0x75` | `0x6DF90E..0x6DF920` | `0x6DF90E mov ecx,[esi+0x90]` → `0x6DF914 mov dl,1` → **`0x6DF916 call 0x5BF390`** | **pause=1 ⇒ 入队后下一绘制帧经 `0x6579E0` 触发 `0x684060`** |
| 100 PlayIngameMovie | `0x64` | `0x6DF546..0x6DF558` | `0x6DF54C xor dl,dl` → **`0x6DF54E call 0x5BF390`** | pause=0 ⇒ **不触发**挂起 |

`call 0x5BF390` 全镜像**恰 4 点**：`{0x6DF54E, 0x6DF916, 0x6E1728, 0x6E1748}`
（前两个是动作内联体，后两个是对应从属体）——与 W1 回件一致，我实跑复现。

⇒ **`[Scenario+0x62C]` 的脚本可达路径至少 4 条**：110 PauseGame、127 StartChronoScreenEffect、
**117 PlayIngameMovieAndPause**、以及经 117/100 的从属体（同一链）。
§556 只列了前两条。

### 三、★ 更关键：**没有脚本动作也能非 0**（引擎影片流程）

W1 给出并在我的复核中被确认：

- `0x53933E call 0x5BF260`，而 `0x53932F mov ecx,0x8263A8`，`0x8263A8` 处字节实读为 **`INTRO`**
  （我实跑 `Engine.rd(0x8263A8,16)` = `b'INTRO'`）。
- `call 0x5BF260` 全镜像 **12 点**（我复现），包含 `0x6DE755`（动作 10 PlayMovie）与
  `0x6E16F9`（其从属）。

⇒ **即使一张图的 `[Actions]` 段里一个 110/117/127 都没有（如 `U0400` 只有 `{2,4,9}`），
引擎自身的 INTRO / 简报 / 过场 / 结算影片流程仍可能让 `0xB45B68 > 0`，进而让 `+0x62C` 非 0。**

**这直接推翻 §556 第二节的阳性排除**：「测量图无 110/127 ⇒ 帧钟停摆不能用地图脚本解释」
只在「110/127」这一个子集上成立，**不能外推到「引擎挂起路径不可达」**。

### 四、`0xB45B68` 的引用口径订正（我上轮写错）

| 项 | §556 我写的 | 实测（`Engine.disp_hits(0xB45B68)`，我亲验） |
|---|---|---|
| 引用总数 | 23 | **23** ✓ |
| 写点 | **3**（`0x5BF341/0x5BF43B/0x5BF487`） | **5**：加 `0x657B67`（`mov [0xB45B68],ecx`，`0x657B64 dec ecx` ⇒ **RemoveItem 时 Count--**）、`0x7591B1`（`mov [0xB45B68],eax=0`，CRT 静态构造 `0x759180` 初始化） |
| 读点 | 未写 | **18** |

⇒ 正确口径：**23 处引用 / 5 写 / 18 读**；其中「局内非 CRT-init 写点」确为 3 个，
但**不能简写成「3 个写点」**。上一轮我的表述漏了 dec 与 init 两个。

### 五、`0x6579E0` 的子系统归属（W1 给出，我采信层次级）

=`SidebarClass::v[16] → PowerClass::v[16] → RadarClass::v[16] (0x653100) → 0x653446 → 0x6579E0`
的**雷达/侧边栏影片显示状态机**（每帧 HUD 绘制链内），带音频（EVA/Vox）辅助调用与场景挂起副作用。
三条调试串实读为 `"Radar: Movie done.\\n"` / `"Radar: Next movie.\\n"` / `"Radar: Movie full redrawn\\n"`。
**W1 明确否定「简报链」**（不读 `ScenarioClass::Brief/Briefing` 字段），
并把任务书原提示「动作 10 / 117 同族」收窄为「**117 直接同链，10 是并行全屏影片族**」。

### 六、目标①的连带影响

1. **§556 第三节的受控对照仍然成立**（同图 units0±10% 却帧时差 2–5.7 倍）——与本节无关。
2. **但「慢窗不是挂起/冻结」这一前提，不能再靠「图里没有 110/127」来支撑**。
   要排除挂起，须证明「窗内 `+0x62C` 恒为 0」，而这需要运行期读数——**现有语料没有该通道**。
3. **不改变任何已裁结论**：D-16 / D-15 / D-13 处置不变；E3 维持「暂停」。
   本节**不构成**任何真机/采样授权。

### 七、诚实账

1. **我亲验**：`disp_hits(0xB45B68)` 的 5 写/18 读/23 引用逐条；`0x6DF916`/`0x6DF54E` 两段反汇编；
   `call 0x5BF390` 4 点、`call 0x5BF2B0` **0 点**、`call 0x5BF260` 12 点；
   `0x53933E call 0x5BF260` 与 `0x8263A8` = `INTRO`；引擎 coverage/SHA。
2. **我未验**：W1 的两节**仍处 phase-1、未过其自身复核阶段**；我复核的是**其中的关键字节断言**，
   不是全部推论（例如动作 100/117 与从属体的父子关系、EVA/Vox 六个库函数的层次归类，我**未逐一重证**）。
3. **我未验**：`0x5BF2B0` 是否有间接调用者（W1 亦标「无法判定」）；`0x7591B1` 是否只有 CRT init 一处。
4. **我未验**：`l3_1101v4c` 的 w0→w1 变快是否与任何影片/挂起事件相关（本轮零真机，无该通道）。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. **公开自我订正**：§556 第二节那段阳性排除的外推**是我写的、也是我错的**；
   是 W1 的独立回件抓到的。这再次印证「执行者≠核验者」：我自己写的结论，我自己复核时没抓到。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))

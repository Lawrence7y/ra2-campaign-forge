#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §878: 0x8871E0 writer analysis — the extra crash site is a REAL latent defect."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

SEC = """
## §878 · **`[0x8871E0]` 的写入者分析：`0x6CD8CD` 是**真·潜在缺陷**（Init.CPP 创建失败或关闭后为 NULL），但它属超级武器路径，不是常规玩法崩溃**（2026-11-15 18:00）

> 承接 §875-3 / §876。纯静态，零真机。本条把 `0x6CD8CD` 从"形态成立"提升为**已证有真实 NULL 可达路径**。

- **§878-1 [已证·`[0x8871E0]` 只有 3 个写者]**
  全 `.text` 严格扫描（1,394,120 条指令，`skipdata=True`）：
  | 站点 | 指令 | 所在函数 | 语义 |
  |---|---|---|---|
  | `0x0052BAD8` | `mov [0x8871E0], eax` | `0x0052BA60`（**`Init.CPP` 引擎初始化**） | `call 0x665650` 成功后赋值 |
  | `0x0052BAFA` | `mov [0x8871E0], ebx` | 同上，**失败分支** | `ebx` 在 `0x0052BA82` 已被 `xor ebx,ebx` 清零 ⇒ **写 NULL** |
  | `0x006BEABD` | `mov [0x8871E0], ebx` | `0x006BE1C0`（关闭/清理） | `operator delete` 之后**置 NULL**（前有 `cmp esi,ebx / je` 的 NULL 检查，顺序安全） |
  - 关键片段（我亲自反汇编）：
    ```asm
    0052BA82  xor  ebx,ebx
    0052BAD1  call 0x665650            ; 创建对象
    0052BAD6  cmp  eax,ebx
    0052BAD8  mov  [0x8871E0],eax      ; 成功
    0052BADD  jne  0x52BB02
    0052BAFA  mov  [0x8871E0],ebx      ; <<< 失败 ⇒ NULL
    ```
    ```asm
    006BEAA3  mov  esi,[0x8871E0]
    006BEAA9  cmp  esi,ebx
    006BEAAB  je   0x6BEAC3            ; 已为 NULL 则跳过
    006BEAB5  call 0x7C8B3D            ; operator delete
    006BEABD  mov  [0x8871E0],ebx      ; <<< 销毁后 NULL
    ```
  - ⇒ **`[0x8871E0]` 存在两条真实的 NULL 可达路径**：初始化失败、关闭之后。

- **§878-2 [已证·`0x0052BA60` 确实是引擎初始化]** 该函数内的字符串：
  `Bootstrap.....`、`voxels.vpl`、`GRFXTXT.PAL`、`GRFXTXT.SHP`、
  `Init Secondary Mixfiles.....`、`SOUNDMD.INI`、`EVAMD.INI`、`THEMEMD.INI`、
  `BATTLEMD.INI`、`RULESMD.INI`、`ARTMD.INI`、`LANGRULE.INI`、`AIMD.INI`、`INTRO`，
  且大量引用 `D:\\ra2mdpost\\Init.CPP`。
  - ⇒ 这是**引擎启动资源加载**函数；`[0x8871E0]` 是**启动期创建的全局单例**。

- **§878-3 [已证·`0x6CD8CD` 在超级武器函数里]**
  该站点属于 `0x006CC390`（6,835 字节）。其字符串：
  `EVA_ChronosphereActivated/Ready`、`EVA_LightningStormCreated/Ready`、
  `EVA_PsychicDominatorActivated/Ready`、`EVA_IronCurtainActivated/Ready`、
  `EVA_ForceShieldReady`、`EVA_NuclearMissileLaunched/Ready`、
  `EVA_GeneticMutatorActivated/Ready`、`EVA_ReinforcementsReady`、`EVA_SpyPlaneReady`、
  `EVA_PsychicRevealReady`、`PDPLANE`、`NukePayload`、`PSIWARN`。
  - ⇒ **超级武器施放/就绪广播**函数。
  - 直接调用者只有 **3 个**：`0x006CBA41`、`0x006CBA6D`、`0x006CBB05`（都在 `0x6CBxxx` 邻域）。

- **§878-4 [已证·判定：真缺陷，但优先级低于已修补的 6 个]**
  | 项 | 判定 |
  |---|---|
  | 是否真缺陷 | **是**（`[0x8871E0]` 确有 NULL 路径，站点无守卫） |
  | 是否常规玩法可触发 | **否**（需初始化失败，或关闭后仍有超级武器施放调用） |
  | 与 6 个已修补例程的关系 | **无关**（不同全局、不同函数、无入口守卫覆盖） |
  | 建议 | **记为已知潜在缺陷**，**不**加入当前 ②-a 补丁批次；若日后要做"完整加固"，与 `0x4FD7A0`/`0x59A5B0` 一并处理 |

- **§878-5 [已证·★ 一个结构洞察：这两个全局是同一种生命周期]**
  | 全局 | 写者数 | 写者模式 |
  |---|---:|---|
  | **`0x887368`**（②-a 崩溃源） | **3** | 赋值 + 置空 + 置空，全部集中在 `0x007777B8 / 0x007777C3 / 0x00777803` |
  | **`0x8871E0`**（本节） | **3** | Init.CPP 赋值 + 失败置空 + 销毁置空 |
  - 两者地址仅差 **0x78**，**无守卫地被以 `+0x250` 偏移解引用**（`[eax+0x250]` / `[ebp+0x250]`）。
  - ⇒ **引擎有一族"全局单例指针 + 显式置空"的对象**，而 ②-a 的六个例程
    **无守卫地解引用它们的 `+0x250` 字段**。这解释了为什么同一形状的崩溃点会散落在多处。
  - ⇒ **`+0x250` 很可能是这类单例对象的共同字段偏移**（例如某个容器或子对象指针），
    但**该字段语义未证**（未反编译该类的成员）。

- **§878-6 [已证·一条对我自己扫描器的更正（本轮我第 9 次自我纠正）]**
  我第一次跑这个分析时用了 `md.skipdata=False`，解码在第一个非法字节处**静默停止**，
  只解出 **155,215** 条指令（实际 1,394,120），因此得出"**0 个写入者**"的结论 —— **完全错误**。
  - ⇒ 换成 `skipdata=True` + 跳过 `insn.id==0` 后才得到正确的 **3 个写入者 / 1,420 处读取**。
  - ⇒ 这**正是我在 §875-7 转述给别人的那条警告**（"字节扫 `E8` 有 13,462 个不是指令起点"），
    我自己转头就犯了它的镜像错误（**不够扫** 而不是 **扫多了**）。
  - ⇒ **教训**：**"没找到"必须附带"扫了多少条指令"**。只报结论不报扫描规模，等于没有证据。

- **§878-7 [未证·如实登记]**
  1. `[0x8871E0]` 的**对象类型未知**（未反编译 `call 0x665650` 的返回值类型 / 未查其 vtable）。
  2. `+0x250` 字段的**语义未知**。
  3. 1,420 处读取分布在 512 个函数里，**这 512 个函数我只统计了数量，未做任何分类**。
  4. `0x6CD8CD` 是否真的会在"关闭后"被调用：需知道 3 个调用者是否可能在引擎关闭阶段执行，**未追**。
  5. `0x4FD7A0` / `0x59A5B0` 的 `this` 来源与上游守卫**仍未追**（§875-3 遗留）。
"""

if "## §878 ·" in s:
    raise SystemExit("REFUSE: §878 already present")

# update the §876-4 action row now that we know 0x6CD8CD's reachability
OLD = "  | **新增评估 `0x006CD8CD`**（`this` 来自 `[0x8871E0]`，读 `[this+0x250]`，无守卫） | §875-3，真实缺口 |"
NEW = ("  | **`0x006CD8CD` 已评估完毕**：真缺陷但**非常规玩法可触发**（需 Init 失败/关闭后）⇒ "
       "**不加入本批补丁**，记为已知潜在缺陷 | **§878** |")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§876-4 action row updated")
else:
    print("WARN: §876-4 anchor found %d times, skipped" % s.count(OLD))

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §878; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))

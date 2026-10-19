# W3-ZC-S5 · 修复 `forced-off-mp` 守卫的**时序穿透漏洞**（`ra2render/**`，ZCode 独占写域）

> 独立会话包。**唯一的 `ra2render/**` 写者是你**，故本包不与任何包并行写该目录。

## 1. 缺陷（**Lead 已逐行读源码证实**，非推测）

`EnableGapProtection` 的联机保护**只拦住"加载时已在联机"这一种情形**：

| 证据 | 位置 |
|---|---|
| 守卫本体：`if (!g_enableGapProtection) return false;` → `if (MpActive()) { LogMessage("forced-off-mp …"); return false; }` | `blitter_hooks.cpp:3313-3324` |
| 默认值 `false`；两份 ini 均 `EnableGapProtection=0` | `blitter_hooks.cpp:38`；`ra2youli/ra2bench ra2render.ini:32` |
| **`InstallGapProtectionPatch()` 全项目仅被调用 1 次**（初始化路径） | `blitter_hooks.cpp:3736` |
| **不存在任何** `Uninstall/Restore/Rollback` 符号（Lead grep 全 `.cpp`+`.h`，0 命中） | — |
| `CheckMpGateTransition()` 在单机→联机迁移时**只重算配置镜像**（`effInterval`/`effKey`/`effMinimapFog`/`s_minimapFogGate`/`s_radarFogGuardMode`）**并打日志，从不撤销已写入 `.text` 的 3×6B NOP** | `blitter_hooks.cpp:314-341` |

**后果**：设 `EnableGapProtection=1` ⇒ 在主菜单/单机阶段加载 DLL（此时 `MpActive()==false`）⇒ 三点 NOP 写入 `.text` ⇒ 随后进入联机对局 ⇒ **`.text` 保持已打补丁**，`forced-off-mp` 完全没生效。
代码自己的日志就写着「R-1 混端 DESYNC 风险，须全端同构建同开关」——**该风险当前是敞开的**。

**严重性必须写准（不要夸大）**：因默认 `=0`，这是**选择加入型**缺陷——**不是默认配置不安全**，而是「这个守卫在它**本来要防的那个场景**里失效」。回报里必须这样表述。

## 2. 本包任务

### 2.1 先做设计裁决（**必须先给方案对比再动手**）
至少对比三条路线，逐条给**风险与副作用**：

| 路线 | 要点 | 你必须评估的风险 |
|---|---|---|
| **A. 运行期回滚** | 单机→联机迁移时，把三点 NOP **还原为原字节** | ⚠️ 触碰项目红线「**禁止热切换**」。若要选它，**必须证明**这 3 个站点在迁移时刻**不可能正被另一个线程执行**（给出调用相位/线程证据）；证明不了就**不得**选 A |
| **B. 延迟安装** | 不在 init 安装，改为**首次确认 `MpActive()` 稳定为 false 且已过主菜单**后再装 | 需要界定"确认稳定"的判据（帧数？相位？）；装晚了会不会漏掉该保护的窗口？ |
| **C. 安装决策收紧** | 安装前检查"本次进程是否可能进入联机"（如网络子系统的初始化状态） | 判据是否可靠；`MpActive()` 在迁移后才可用 ⇒ 可能无解 |

**必须给出你选了哪条、为什么、以及被否方案的具体否决理由。**

### 2.2 实现与证据
1. 改 `ra2render/**`（**唯一允许改的源码域**）。
2. **不得覆盖正在使用的已部署 DLL**：新版构建产物放到 `out/re_work/zcode_live/W3_20261001/gapfix/build/**`，并给出部署说明（由 Lead 排后续真机卡执行）。
3. 证据要求：
   - 三个站点（`0x00568273` / `0x00577EC5` / `0x00577B60`）的**原字节**与**补丁后字节**逐字节贴出（含 FileOffset；**按段映射算，勿用 `VA − 0x400000` 通式**——本镜像 `.rsrc`/`.detour` 为 `−0x6FC000`）
   - **负控制**：必须有一个用例证明「**先在非联机装、再进联机**」这一路径下，三点要么**从未被写**、要么**已被还原**（二选一，取决于你选的路线），并给出可重放的判定输出
   - 单机路径**行为不变**：同一 ini 配置下，单机时三点仍被正确安装（`installed=N` 日志 + 字节读回）
4. 日志口径：`forced-off-mp` 与新的判定必须能被日志区分（便于真机判读）。

## 3. 门禁（**原文粘贴**，缺一不可）
- `python tools\verify_anchors.py` → **323/323 PASS**
- `python tools\verify_hooks.py` → PASS
- `python tools\verify_evidence.py`
- 构建产物哈希 + 源码 diff 摘要（before/after 行号与内容）

## 4. 交付物（写域：`ra2render/**` + `out/re_work/zcode_live/W3_20261001/gapfix/**`）
- 修好的 `ra2render/**` 源码
- `out/re_work/zcode_live/W3_20261001/gapfix/{DESIGN_DECISION.md, EVIDENCE.md, claims.txt, build/**, runs/**, verify_gapfix.py(EXIT=0)}`
- 回报按 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 十节骨架；`[0]` 直接答：**你选了哪条路线 / 为什么 / 负控制是否通过 / 单机路径是否不变**

## 5. 纪律
- **禁写** `ra2youli/**`、`ra2bench/**`、`D:\Red2/**`、`docs/**`、`tools/**`、`out/re_work/qc/**`、`out/re_work/agy/**`
- **不得**覆盖/替换游戏目录中正在使用的 `ra2render.dll`；**不得**启动游戏（真机验证由 Lead 另排卡，交给真机会话）
- 若你在实现中发现**本卡对缺陷的描述有误**（例如 `MpActive()` 在切入点其实可用、或另有回滚路径），**以你的复算为准**并单列勘误——**不要迁就 Lead 的结论**
- 额度纪律：GLM-5.3-Flash 用尽即切 **step-5-preview**，并在 `[META]` 注明切换时点与已完成包

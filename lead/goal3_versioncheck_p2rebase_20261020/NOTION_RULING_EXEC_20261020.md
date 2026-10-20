# 裁决执行回执（2026-10-20 17:1x）

来源：Notion 会话「RA2 Campaign Forge 仓库分析」，对 §309 三问的裁决。

---

## 裁决1（①）：选 A —— E1/E2/E3 阶梯；B 降为 E1 内顺手对照

**Notion 原句要点**：
- 无干预实验已隔离地图和 INI（那 2 字节是运行期回写，不是启动前因素），B 单独换图对照价值不大，还会把 L1 从 sf8 档变掉。
- **E1 要固化成趟前门禁**，不只要跑一次：起趟前把其他前台大窗全部最小化/关闭，确认桌面无遮挡，再发射。
- E1 跑之前，先在同一次清屏条件下用两张图各裸起一次（10 分钟就能彻底锁死「地图无关」）——把 B 的信息量并进 E1，不另起趟。
- harness 要补一条独立缺陷修复（**另开项，不阻塞 E1**）：进程死亡后 fail-fast，不要再对死 PID 空转 148 秒、产出错误截图。退出码要记进字段（现在是 `alive_seconds` 的值）。
- E3 的 procdump 作为兜底。
- 这几趟都要用户在场，按 ① 基线方案 §7 的清单走。

**本轮执行状态**：⏸ **待用户在场**（E1 要求清屏，会关闭 ZCode 本身）。
已落地的准备：L1 根因取证件 + 4 个复现探针（`ra2forge-audittools/scratch_boot_probe/`）已可供 E1 使用。

---

## 裁决2（③）：B + C 合并 —— 现在只编译不部署，部署并入 P1+SBH 合批

**Notion 原句要点**：
- **不批准单独施用（否决 A）**。理由：① P1 自己从没编译过，而 SBH 这轮已证明 vcvarsall x86 下 bcrypt 可用，所以 P1 也要先过编译这关；② P1 和 SBH 都从 `656e6b4e` 分出、互不包含，将来必然要合并（`bcrypt.h` include 和 `g_enableSbhGuard` 声明会冲突），没必要先单独部署 P1 再拆一次。
- 现在离线编译 P1 验证通过即可，**不写 ra2youli、不碰真机**。
- 合批上真机前的硬前置：白名单哈希、13 个虚表槽位期望原值、9 个代码位点原字节，全部继承自 P1 原实现、本轮未重算——这些要**对着当前 P2 母本重新算一遍并经异族核验**。
- D1「任意 1 字节篡改⇒整体不装」已判 REFUTED，报告里要**如实写清版本门的实际覆盖面**（.text / 13 槽 / 9 位点 / PE 关键字段），不要写成全覆盖。
- P1 的目标是 ③（安全改动能力），不是 ①；它上真机不解 boot/L1 的卡死，**排在 L1 跑通之后**，不抢 ① 的档期。

**本轮执行状态**：✅ **离线编译已通过**

```
vcvarsall.bat x86
cl /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp \
   /Fe:ra2render_p1.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS \
   kernel32.lib user32.lib winmm.lib bcrypt.lib
CL_EXIT=0
```

- 产物：`scratch/p1_build/ra2render_p1.dll`
- 1 条警告（`fopen` 不安全建议，既有代码风格）
- **bcrypt.lib 在 vcvarsall x86 下可用**（与 SBH 同结论）
- 未写 `ra2youli/`、未碰真机

---

## 裁决3（②）：确认「先离线」；桌面单测是硬门，补三条

**Notion 原句要点**：
- 桌面单测**必须补齐 RECEIPT 偏差 4 列的全部项**：G0 四条路径 + 开关幂等 + 多线程计数器精确性。**这是真机前的硬门，不是可选。**
- G0.2（.text raw 段哈希）和 G0.5（段级哈希）是 SHOULD，可以不做，但要在报告里**显式登记「未实现」**，别让后面误以为全覆盖。
- PW-2 次守卫窗字节是 `[推演]`、未验证，**确认继续禁用，符合规格**。
- 真机 A/B 对拍（规格 §3.1.7，四臂各 ≥3 局）要满足之前 #4 的全部既有条件：先跑 1 趟批 4 安慰剂冒烟、G-0a~G-0d/G-0f 全过、只给发生器单独加杀软信任、spawnfix8 满足 ShortGame 门禁、用户在场。
- 之前裁 #4 批 3 单臂时的前提是「守卫未交付、RC-1 全链无实现」。现在 RC-1 的 SBH 守卫已实现并编译通过、cave 13/13 核验过了。**等它过了桌面单测**，#4 就有条件从「单臂裸奔」升级为「守卫关/开两臂对拍」，批 3 报告首行的单臂局限声明可以相应放宽。具体放宽程度等桌面单测结果出来再裁。

**本轮执行状态**：✅ **桌面单测已完成，两项全过**

### 测项 1：G0 四条路径 + 开关幂等（Python 真值表，16/16 PASS）

```
baseline sha256 matches whitelist          PASS  73201cc0...
baseline size matches                      PASS  4825360
baseline PW-1 6B window matches            PASS  8b 54 f9 04 8b 0a
baseline back-jump 3B matches              PASS  2b 4d f0
G0 path1 size-mismatch -> reject           PASS  hash-mismatch
G0 path2 unknown identity -> reject        PASS  identity-unknown
G0 path3 window-mismatch -> reject         PASS  window-mismatch
G0 path3b back-jump mismatch -> reject     PASS  window-mismatch
G0 path4 all-pass                          PASS  identity-ok/window-ok
switch off -> off                          PASS
switch off+mp -> off (switch first)        PASS
switch on+mp -> forced-off-mp              PASS
switch on+installed -> already (idempotent) PASS
switch on+identity fail -> rejected        PASS
switch on+window fail -> window-mismatch   PASS
switch on, all ok -> install(ok)           PASS
```

### 测项 2：多线程计数器精确性 + 熔断单向性（C 侧实跑，5/5 PASS）

```
TEST1 interlocked_counter: got=400000 expected=400000   PASS   （8 线程 × 50000）
TEST3 gate_oneway: after_first_exchange=0               PASS
TEST3b gate_stays_zero: after_second_exchange=0         PASS
TEST4 cmpxchg_1to0: prev=1 now=0                        PASS
TEST4b cmpxchg_repeat_noop: prev=0 now=0                PASS
RESULT: ALL_PASS (failures=0)
```

> 说明：`InterlockedIncrement` 是编译器内建（kernel32 不导出），Python ctypes 调不到，改用 C 编译实跑。
> 第一版测试 4b 写法有误（用 `CmpXchg(&g,1,0)` 试图证明「不能改回 1」，但那本来就该能改），已修正为规格真实写法
> `CmpXchg(&g,0,1)` 重复执行 ⇒ 第二次不匹配 ⇒ no-op。

### 显式登记的未实现项（按裁决要求）

| 项 | 级别 | 状态 |
|:--|:--|:--|
| G0.2 `.text` raw 段哈希 | SHOULD | **未实现** |
| G0.5 段级哈希门禁 | SHOULD | **未实现** |
| G2 严格模式（region 成员扫描） | 可选 P1 | **未实现** |
| PW-2 次守卫窗 | 可选 P1（字节 `[推演]`） | **禁用**（符合规格与裁决） |
| 真机 A/B 确定性对拍（§3.1.7） | 必须 | **未做**（需 #4 前置条件） |

---

## 裁决附加项：调度器

Notion：「nextRunAt 在未来、调度器状态正常，说明只是 09:41 之后那几拍没成功跑。等 16:46 这拍；如果它也没跑成，再重建并把失败原因一起报上来。」

**本轮核实**：现时刻 17:1x，`automation-07c8dfec` 的 `lastRunAt` 仍是 `2026-10-20 09:41:22`。16:46 那拍**未跑成**。按裁决要求，需重建并报告失败原因（候选：provider network_error —— 本轮 SBH 工作流 `dwfrun-3d9ad208` 正是连续 network_error 停滞 20 分钟）。

---

## 裁决附加项：合批基线

Notion：「合批时以哪一份为基、CRLF 怎么统一，要在 rebase 回执里写清，避免又出现上次那种 CRLF/LF 哈希对不上的情况。」

**本轮记录**：
- P1 成品 **以 `patch` 工具从母本副本生成**（非手工拼接），行尾与母本一致（CRLF 4,313 / LF 4,313，无孤立 CR/LF）
- 反向 `patch -R` 还原 sha = `656e6b4e…daada1`（与母本逐字节相同）
- 正向 `patch` 再打回 = 成品 sha
- 合批时**建议以本回执的 `.cpp` 为 P1 基**，SBH 作为其上的一次新插入（因为 SBH 的 5 处插入点在本件中均已存在且行号已重算）

---

## 并发写入者事件（必须记录）

16:35–16:55 期间，本目录存在**两个并发写入者**：

| 写入者 | 成品 | 判定 |
|:--|:--|:--|
| 主会话（我） | `blitter_hooks_p2rebase.txt` 261,843B sha `6e81569e` | **有缺陷，已废弃** |
| 子代理 actor#1 | `blitter_hooks_p2rebase.cpp` 261,746B sha `4431f4a4` | **正确，已采信** |

**缺陷实证**（我亲自核验，不是转述）：

| 检查项 | 我的版本 `6e81569e` | 子代理版本 `4431f4a4` |
|:--|:--|:--|
| `ForgeTelemetry g_telemetry` 出现次数 | **2**（重复定义，编译不过） | 1 |
| `int g_targetScanInterval = 8;` 出现次数 | **1**（旧值残留） | 0 |
| `int g_targetScanInterval = 1;` 出现次数 | 1 | 1 |

根因：我的 hunk1 用「前 3 行 context 锚 + replace_len=0 纯插入」定位时，把 include 段插入点选在了
`#include <cstdlib>` 之后，但 P2 在该位置插入了 17 行 G3-SPLIT 注释块，导致 P1 新增的两行与
旧的 `ForgeTelemetry`/`g_targetScanInterval = 8` 被一起复制了一份。

**我的 python 语法检查漏了这两项**（只查了 G3-SPLIT/VER-GATE 计数和 5 参形态），
子代理用「P1 新增 335 行完整性 + P2 新增 160 行完整性 + 删除行残留检查」抓到了。

**处置**：
- 采信子代理的 `4431f4a4` 作为 P1 交付件
- 我的版本移入 `_discarded_foreign_1638/`（目录名由子代理所取，保留不改）
- **已用 `4431f4a4` 重新编译，CL_EXIT=0**（见裁决2 执行状态）——编译通过反过来证明该版本无重复定义

**教训（写入台账）**：语法层检查必须包含「全局符号重复定义」与「关键常量取值唯一性」两项；
不能只查标记计数。而且这类缺陷**编译器一跑就现形**，所以「离线编译」应作为 rebase 的必备步骤，不是可选项。

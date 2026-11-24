# 卡 R17-R44-FACTINDEX-V32 · 修两类缺陷：路径基准不一致（10 条）+ 行号锚已腐烂（v3.1 → v3.2）

**产物目录必须写 `lead\next_re_20261117_r14\R17_R44_FACTINDEX_V32\`；产物不得含 CR。**
本卡是**文档修正**卡：不执行逆向、不启动 gamemd。

## 〇、依据（`R17_R43_INDEX_INTEGRITY` 实测）
对 v3.1 的 26 条做了 71 次路径检查，结果 **RESOLVED 16 / PARTIAL 0 / BROKEN 10**，BROKEN 恰为 `F17`–`F26`。根因是**两类**问题：

**缺陷 A · 路径基准不一致（机械性，10 条）**
- `F01`–`F16` 的 `evidence_paths` 以 **`lead\next_re_20261117_r14\...`** 开头 ⇒ 从仓库根可解析；
- `F17`–`F26` 用 **run 内相对写法**（`R17_DELIVERY\...` / `COVERAGE\...` / `R14_COMMON.md` / `LEAD_LOCK` / `R17_R8_RESIDUAL` …）⇒ 从仓库根全部解析不到。
- 🔴 **文件其实都存在**，是**同一份索引里混了两种基准**。这本身就是交付缺陷（读者按仓库根走会在 10 条上扑空）。

**缺陷 B · 行号锚已腐烂（真问题）**
- `F01` 引 `STATUS_BOARD.md(L210-213)`，实测该区间现在是 R17 第 13 轮 / R31 / R32 段，**与 F01 内容无关**；
- `F07` 引 `STATUS_BOARD.md(L261-265)`，而文件**只有 255 行** ⇒ **越界**；
- 根因：看板每几轮就要归档一次（H47/H48 各搬走一批），**行号整体位移** ⇒ **任何指向看板行号的锚都会周期性失效**。

## 一、要做的修改（逐条，全部 26 条都要过一遍）

**1. 路径基准统一（缺陷 A）**
 把所有 `evidence_paths` 统一为**仓库根相对路径**，即 `lead\next_re_20261117_r14\...` 前缀；
 `LEAD_LOCK` → `lead\LEAD_LOCK`；台账 → `lead\GOAL_THREE_TARGETS_20261018.md`。
 **逐条改完后必须自己重跑路径解析**，报「26 条全部 RESOLVED」。

**2. 行号锚一律去掉（缺陷 B）**
 🔴 **规则：`evidence_paths` 中不得出现 STATUS_BOARD / PANEL / 台账 / LEAD_LOCK 的裸行号**（如 `L210-213`）。
 - 改为**稳定标识**：看板用**段标题**（如 `STATUS_BOARD.md(R17 第 13 轮 段)`）；
   `PANEL` 用 **M 编号**（如 `PANEL.md(M58)`）；台账用 **`§号码`**；`LEAD_LOCK` 用**段号**（如 `LEAD_LOCK(AH 段)`)。
 - `R14_COMMON.md` 用 **`§x.y` 节号**（本来就是稳定的，保留）。
 - 例外：若某条必须指向**具体行**才能定位（例如某脚本第 78 行），**允许保留，但须在该路径后加「(行号仅供定位，文件变更后可能位移)」字样**。

**3. `F25` 的 `PANEL` 引用要改准**
 `R43` 实测 `PANEL.md` **L139 写「proved_strict 只是下界」**，而 **L140 写「上面 L134/L138 把 proved_strict 说成『下界』方向标反——它是上界」**。
 ⇒ `F25` 该引 **`PANEL.md(M58 界向更正)`**（不要再写 `L139–140` 这个区间，因为它**同时包含被更正的旧句**）。
 `F25` 的 statement 本身（界向 = 上界不是下界）**是对的，不要改**。

**4. 重跑路径解析并留证**
 改完必须**自己重跑** `R43` 那套解析（可从 `R17_R43_INDEX_INTEGRITY\work.py` 借鉴思路，但**自己实现**），
 报：26 条 RESOLVED / PARTIAL / BROKEN 各多少；BROKEN 必须为 **0**。

## 二、硬约束
1. 以 **v3.1**（`R17_R42_F23_FIX\FACT_INDEX.tsv`）为基底。**`statement` / `grade` 内容不得改动**（只改 `evidence_paths`，以及必要的 `limitations` 里同样的行号写法）。
2. `fact_id` 仍为 `F01`–`F26`，**不增不删不改号**。
3. 产物：`FACT_INDEX.tsv`（v3.2）、`README.md`（**新增一条**：`evidence_paths` 一律仓库根相对、不含裸行号；行号锚会因归档腐烂）、`REPORT.md`（改了多少条路径、多少处去行号、重跑结果）。
4. **不得修改** `R17_R42_F23_FIX` / `R17_R40_FACTINDEX_V3` / `R17_R38_FACTINDEX_FIX` / `R17_R34_FACT_INDEX` 下任何文件。
5. 产物不得含 CR（自校验）。
6. 严格 **9 分钟**。
# -*- coding: utf-8 -*-
"""向台账追加 §1030（R15 十项裁决），并做 append-only 前缀哈希复验。"""
import hashlib, sys
sys.stdout.reconfigure(encoding="utf-8")

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SECTION = r"""
## §1030 · R15 十项裁决一次关闭（D-35/36/37/38/39/41/43/44/45/46 + D-42 子项）——口径定为「D-38 维持 R14-R14 + D-44 严格读法双列」；对外声明 **严格达标 1/22（仅 S17）**、名义 3/22 并列；`proved_strict` 1,138（8.81%）**仅为下界**

**裁决人**：用户（2026-11-19，三问三答明示）。**裁决书**：`lead/next_re_20261117_r14/RULING_R15_20261119/RULING_R15.md`。
**复算件**：`RULING_R15_20261119/work/strict_panel.py`（`strict_panel.tsv` / `.json`）、`append_panel_strict.py`、`apply_pending_r15.py`。
**`coverage.tsv` 零改动**（sha256 `b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c`）；**未降级任何行**。

### 裁决与量
| 项 | 裁决 | 对本表的作用 |
|---|---|---|
| D-38 | **(A)** `slotN` 计入 `named`，DoD 用 `named_pct_S(R14)`；strict 列仅参考 | named 7,203（55.77%）；strict 口径 1,372（10.62%）、22 子系统全不达 —— 已登记不再重开 |
| D-44 | **严格读法 + 双列**，**不降级 273 行**（改用 `proved_strict` 列） | proved 1,455 → **proved_strict 1,138**；S15 101→**48**、S16 46→**20**（双双失守）、S17 54→**53**（仍过门槛 51）⇒ **严格 1/22** |
| D-37 | **(D)** 授权按 `class_to_sub` 做 S22 全表再归属普查，**只作数据卫生** | S13 分母保持 240（剔 92 行后 named 124/148=83.78% < 门槛 134 ⇒ 净收益 0） |
| D-39 | **(C)** ③④同源时以「审计逐条复算 + 检出力反证」替代环④，附三条件 | 预期 **+11**（K8 18 行过 ㉓ 只认 11）⇒ S13 89→**100/240=41.67%**，仍低于门槛 120，**不产生达标** |
| D-41 | **(B)** 允许身份替代（YRpp+字节双吻合 / 调用者契约） | **DoD 增量 = 0**（S02/S19 的 named 12.42%/11.27% 永远不达标） |
| D-42 子项 | **要标等级** | 实点 **8 行**（S03 3 / S09 5）、写法分裂 3 种；**细则#1 仍算 ③b ⇒ proved 不降级**（`S03 7→5 / S09 8→7` 须另裁「是否仍算 ③b①」才执行） |
| D-43 | **(A)** ④ 宽读（不要求真实派发点） | 两读法差 **18 行** ⇒ ④ 非瓶颈，条目关闭 |
| D-45 | **(A)** 仅结构证据的 FUNC 不入表 | 1,491 留 UNDECIDABLE，上界 ≤1,491（C ≤19,989） |
| D-46 | **(A)** ③b② 不认 bool 返回 | `0045A640` 不并入，S08 保持 9/22（差 2），留可重开旋钮 |
| D-35 | **(D)** 副本打补丁 + 有界冒烟 6–8 处；**放弃现有单测作部署依据** | `ra2youli\gamemd.exe` SHA-256 必须不变；禁止原地打 |
| D-36 | **维持 (A)**，且原 (B)/(C) **判为物理不自洽** | 硬件执行断点无处理器 ⇒ `#DB` 未处理 ⇒ **首次命中即终止进程**；改派只读分支判别卡 |

### 本轮复核（Lead 亲跑，非转述）
- 脚本复算的 `named_S(R14)` **7,203** / `named_S(strict)` **1,372** / `proved_n` **1,455** / `atlas_n` **12,916**
  与 `PANEL.md` 三列**逐格全等** ⇒ 新增 `proved_strict` 与前人列同源可加。
- 全表 `[已证]` 1,460（atlas 内 1,455）；语义栏含 `[未证]` **317** 行，其中非 S22 **274**（273 模板 + 1 坐标误入）。

### 三条事实更正（本轮发现）
1. **D-38 原文前提之一为假**：「`Class::sub_XXXXXXXX` 在 atlas 内 = 0 条」——实测 **7 行**（6 位短形态
   `AudioController::sub_4060F0` 等 6 行在 S19、1 行在 S05）。面板按 `::sub_` 前缀排除**恰好排掉**，故现有数字未受影响；
   但按字面 8 位匹配会虚高 +7。排除规则统一为 `::sub_[0-9A-Fa-f]+$`。
2. **Lead 自纠**：本轮先用「全表 `[已证]`」口径得 S16=47 并据此判面板陈旧；实际面板用 **atlas 内**口径 = **46**，**面板无误、我口径错**。
3. **`PANEL.md` 在我工作期间被并发写入**（22:11 读到 18,479/M50；22:15 已为 18,498 且带 M51/M52、A/B/C = 12,916/14,554/18,498）。
   **该同步非本轮所为**，`PANEL.md` 在本仓 **untracked**，只能靠 mtime + sha256 事后识别。
   ⇒ 撤销「面板陈旧」判断；本轮对 PANEL 的写入只有「增严格双列表」（+2,895 B，sha256 `3dff129d…`→`4d431d63…`）。
   **处置**：凡改 `PANEL.md`/`coverage.tsv` 必须读写前各记 mtime + sha256。

### 两条遗留缺口（本轮识别，未解）
- **`proved_strict` 只是下界中的下界**：只排「自陈 `[未证]`」。`004AB9B0`（S09，`[已证]`：slot 身份字节已证 + 语义引自
  `R8_ui_crt.md §21.1`）**从不自陈未证**，本列排不掉，③b 同样无字节证据 ⇒ **1,138 不得当作合规已证总量**，规模待只读卡统计（R15-C7）。
- **`004AB9B0` 被误列入「细则#1 三行」**：其语义栏无任何 ③b 主张，属 D-44 类问题，须按 D-44 处理。

### 产出与状态
- `PENDING_DECISIONS.md`：10 条整条删除 + 10 行已裁决记录（95,064 → 71,792 B 前，含 D-42 细则 4 增补后 ~73 KB）；`N10-C04` 仍未裁，保留。
- `COVERAGE/PANEL.md`：新增「严格口径双列表（22 行 + TOTAL）」+ 表头口径注改写 + `proved_strict` 下界警示。
- **待办卡**：`RULING_R15_20261119/CARDS_R15.md`（R15-C1…C7）。
- **未做**：未改任何 `[已证]` grade；未跑真机；未派子代理。
"""


def main():
    with open(LEDGER, "rb") as f:
        old = f.read()
    pre_sha = hashlib.sha256(old).hexdigest()
    pre_len = len(old)
    pre_lines = old.count(b"\n")

    with open(LEDGER, "ab") as f:          # 纯追加，单次写
        f.write(SECTION.encode("utf-8"))

    with open(LEDGER, "rb") as f:
        new = f.read()

    # append-only 复验：旧字节必须是新文件的前缀，且前缀哈希不变
    prefix_ok = new[:pre_len] == old
    prefix_sha_ok = hashlib.sha256(new[:pre_len]).hexdigest() == pre_sha
    print("prefix bytes identical      :", prefix_ok)
    print("prefix sha256 unchanged     :", prefix_sha_ok)
    print("sha256 %s -> %s" % (pre_sha[:16], hashlib.sha256(new).hexdigest()[:16]))
    print("bytes  %d -> %d (Δ%+d)" % (pre_len, len(new), len(new) - pre_len))
    print("lines  %d -> %d (Δ%+d)" % (pre_lines + 1, new.count(b"\n") + 1, new.count(b"\n") - pre_lines))
    if not (prefix_ok and prefix_sha_ok):
        sys.exit(3)
    print("APPEND_ONLY_PASS")


main()

# -*- coding: utf-8 -*-
"""按 PENDING_DECISIONS.md 自身规则执行 R15 裁决：已裁条目整条删除 + 记一行。

删除范围（均由锚点定位，不自造行号）：
  1) 待裁段：`- **D-35（` 起 到 `- **D-13 已裁决（` 前  （含 D-35/D-36/D-38/D-37 四块）
  2) `## D-39（` 起 到 `## D-40（` 前
  3) `## D-41（` 起 到 `## D-42（` 前
  4) `# ===== r14-s8` 起 到 文件末（banner + D-43/D-44/D-45/D-46）
保留：D-40、D-42（已裁/执行中的口径出处）、N10-C04（未裁）、D-13/D-14 状态块（未裁）。

自校验：删除后必须 ①无上述待裁锚点 ②D-40/D-42/N10-C04 仍在 ③行数与字节数下降符合预期。
"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")

P = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"

RECORD = """
- **D-38 已裁决（2026-11-19，用户）：(A) 维持 R14-R14 原文 —— `Class::slotN`/`vslotN` 计入 `named`。**
  **DoD 判定用 `named_pct_S(R14)`**，`named_pct_S(strict)` 只作参考列、不参与判定；第 ⑬ 类错源**仅用于 proved**。
  **执行**：`COVERAGE\\PANEL.md` 表头口径注改写（并修正「`Class::sub_XXXXXXXX` 在 atlas 内 = 0 条」这一前提——实测 7 行，含 6 位短形态）。
  参考列后果已登记：按 strict 口径全表 10.62%、**22 个子系统全不达标**，不再重开。
- **D-44 已裁决（2026-11-19，用户）：严格读法 + 双列并列；不批量改 grade。**
  **对外声明一律用严格列：严格达标 1/22（仅 S17）**；名义达标 3/22（S15/S16/S17）并列报告。
  严格值：S15 101→**48（30.38%）**、S16 46→**20（22.22%）**（双双失守）、S17 54→**53（51.96%）**（仍过门槛 51）。
  **不降级 273 行**：改用 `proved_strict` 列（atlas 内 `[已证]` 且语义栏不含 `[未证]`），机器可复算、`coverage.tsv` 零改动、可回滚。
  **执行**：`PANEL.md` 新增「严格口径双列表」（22 行 + TOTAL，数字绑定 `coverage.tsv` sha256 `b4c998c0…be94c`）；
  `M48` 的解封条件改为「该行语义栏不含 `[未证]`」。
- **D-37 已裁决（2026-11-19，用户）：(D) 授权按 `class_to_sub` 做 S22 全表再归属普查，但只作数据卫生、不作达标手段。**
  **S13 分母保持 240**（剔 92 行后 `named 124/148 = 83.78% < 门槛 134` 仍不达标，而 proved 75/148 会达标 ⇒ 净收益 0，且制造第二个双分母争议）。
  **执行**：派全表普查卡，产出改归前后对照表 + 「S22 4,851 行中多少类名可由 RTTI 定出」这一从未统计过的基础数；
  任何达标声明必须两种映射下同时出数。追加范围证据（`SpawnManagerClass` 被劈进两桶、`004E0E80` 容器模板）已移入裁决书附录 5。
- **D-39 已裁决（2026-11-19，用户）：(C) ③④物理同源时，以「审计逐条复算 + 检出力反证」替代环④。**
  **三个绑定条件**：①规则先成文写入 `R14_COMMON §8`；②5 条已接受先例（`004393F0` `0046B5C0` `0046C890` `0062AF70` `007730F0`）补同注；
  ③`S13_K8` 的 18 行须过 ㉓ 陷阱（基类死表+派生活表）后逐行复核，**实测只有 11 行可辩护**。
  **预期收益 +11（非 +18）⇒ S13 89→100/240 = 41.67%，仍低于门槛 120，不产生达标**。
- **D-41 已裁决（2026-11-19，用户）：(B) 允许身份替代（YRpp 绑定 + 字节逐项吻合 / 调用者契约）。**
  规则与 D-39 的 §8 增补同批成文。**必须同时记录：DoD 增量 = 0**（S02/S19 的 proved 上界够，但 named 12.42%/11.27% 永远不达标）。
  解禁的是「能否把事实记成已证」，不是「能否达标」。原支撑证据已移入裁决书附录 4。
- **D-42 子项已裁决（2026-11-19，用户）：要标等级。**
  `006C9890` `00631CC0` `004AB9B0` 三行须标明为「③b 细则#1 级」（多路守卫链），不得与 ③b①（跳表）混写。
  **连带后果照记：严格口径 S03 7→5、S09 8→7**（proved 各减 2 / 1）。
- **D-43 已裁决（2026-11-19，用户）：(A) 宽读法 —— ④「活 vtable 槽位」不要求真实派发点。**
  两读法实测差 **18 行**（宽 3,349 / 严 3,331）⇒ **④ 不是瓶颈**。执行：`PANEL`/台账并列报两读法数字，**不再单独立项**。
- **D-45 已裁决（2026-11-19，用户）：(A) 仅结构证据的 FUNC 不许入表。**
  1,491 行留 `UNDECIDABLE`，P0 收口按「**已枚举、非漏检**」认定，上界 ≤1,491（C 口径 ≤19,989）。
  理由：A_call / B 通道在 3,944 个真入口上富集 **0.00x** ⇒ 结构性不可见，不是判据不够好；用零区分力判据扩分母为 §8.1 ⑨⑪㉔ 所禁。
  执行：已并 P0-ADJ5 的 19 行（外部取址证据、S22/atlas 外/`[静态推断]`）保持不动；34 行仅结构证据不入表；`0042FF70` 剔除。
- **D-46 已裁决（2026-11-19，用户）：(A) 窄读 —— ③b② 不认 bool 返回。**
  `0045A640` 维持 `[静态推断]`；S08 保持 **9/22（门槛 11，差 2）**。
  反向基线照记（该形状占 300 个 atlas-free 样本 3.33%，不足以「一放就泛滥」否掉它）⇒ **留作可重开的政策旋钮**，本轮不重开。
- **D-35 已裁决（2026-11-19，用户）：(D) 允许在副本上打补丁 + 有界真机冒烟；放弃现有单测作部署依据。**
  ①**只碰副本**，`ra2youli\\gamemd.exe` SHA-256 `73201CC0…F67476` 必须不变，卡毕复验登记；②现有 `UNIT_TEST.txt` 31/31
  **明确不得作部署依据**（审计 ★A：同质对照下 90.6% PASS ⇒ 空判据）；③主证伪器改为**有界冒烟 6–8 处**最易复现的 NULL 路径，
  其余只报覆盖率、**不宣称全覆盖**；④**禁止原地打**（选项 C 未授权）。
- **D-36 已裁决（2026-11-19，用户）：维持 (A) 不设硬件断点、不写线程上下文；改派只读卡。**
  **原 (B)/(C) 判为物理不自洽**：硬件执行断点命中时 CPU 在执行前抛 `#DB`，无人处理 ⇒ 未处理异常 ⇒ **进程终止**
  （游戏自带顶层过滤则写 `except.txt` 后退出）⇒ (B) 不是最小只读扩展而是首次命中即终结游戏；(C) 在无处理器时不可实现。
  留住命中现场需要 `DebugActiveProcess` 当调试器（attach，远大于写 Dr）或注入处理器（禁区）。
  **执行**：派**只读**卡验证「条件输入 + 行为排除」能否唯一区分 `0x47C738`；若不能唯一区分，则把条目重写为
  「**是否授权 debugger attach**」再裁。
"""


def main():
    raw = open(P, "r", encoding="utf-8").read()
    before_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    lines = raw.split("\n")
    n0, b0 = len(lines), len(raw.encode("utf-8"))

    def idx(pred, what):
        for i, ln in enumerate(lines):
            if pred(ln):
                return i
        print("ANCHOR_NOT_FOUND: %s —— 中止，未写盘" % what)
        sys.exit(2)

    # 1) 待裁段 4 块
    i35 = idx(lambda l: l.startswith("- **D-35（"), "D-35 bullet")
    i13 = idx(lambda l: l.startswith("- **D-13 已裁决（"), "D-13 bullet")
    assert i35 < i13, "锚点顺序异常"
    del lines[i35:i13]

    # 2) D-39 段
    i39 = idx(lambda l: l.startswith("## D-39（"), "D-39 section")
    i40 = idx(lambda l: l.startswith("## D-40（"), "D-40 section")
    del lines[i39:i40]

    # 3) D-41 段
    i41 = idx(lambda l: l.startswith("## D-41（"), "D-41 section")
    i42 = idx(lambda l: l.startswith("## D-42（"), "D-42 section")
    del lines[i41:i42]

    # 4) r14-s8 banner + D-43..D-46
    i8 = idx(lambda l: l.startswith("# ===== r14-s8"), "r14-s8 banner")
    del lines[i8:]

    # 插入已裁决记录
    ih = idx(lambda l: l.strip() == "## 已裁决记录（最近在上）", "已裁决记录 header")
    block = RECORD.strip("\n").split("\n")
    lines[ih + 1:ih + 1] = [""] + block

    new = "\n".join(lines)
    open(P, "w", encoding="utf-8", newline="").write(new)

    # 自校验
    out = open(P, "r", encoding="utf-8").read()
    bad = []
    for pat in ("- **D-35（", "- **D-36（", "- **D-37（", "- **D-38（",
                "## D-39（", "## D-41（", "## D-43（", "## D-44（", "## D-45（", "## D-46（",
                "# ===== r14-s8"):
        if pat in out:
            bad.append(pat)
    keep = ["## D-40（", "## D-42（", "N10-C04", "D-38 已裁决", "D-44 已裁决", "D-36 已裁决"]
    missing = [k for k in keep if k not in out]
    after_sha = hashlib.sha256(out.encode("utf-8")).hexdigest()

    print("sha256 before=%s after=%s" % (before_sha[:16], after_sha[:16]))
    print("bytes  %d -> %d (Δ%+d)" % (b0, len(out.encode("utf-8")), len(out.encode("utf-8")) - b0))
    print("lines  %d -> %d (Δ%+d)" % (n0, out.count("\n") + 1, out.count("\n") + 1 - n0))
    print("残留待裁锚点:", bad if bad else "无")
    print("必备保留项缺失:", missing if missing else "无")
    if bad or missing:
        sys.exit(3)
    print("SELFCHECK_PASS")


main()

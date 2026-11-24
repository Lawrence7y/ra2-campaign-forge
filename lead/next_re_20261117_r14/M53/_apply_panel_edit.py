# -*- coding: utf-8 -*-
"""M53 Task B/C: guarded edit of PANEL.md. Guard baseline sha+mtime; backup to _hygiene.
Edits: (1) title M53段, (2) named exclusion rule in main caliber + strict section,
(3) new 'RULING-R15 生效声明' section after three-denominator table.
"""
import hashlib, json, os, shutil, sys
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PAN = os.path.join(ROOT, "COVERAGE", "PANEL.md")
BAK = os.path.join(ROOT, "_hygiene", "PANEL.M53.bak")
REPORT = os.path.join(ROOT, "M53", "_panel_edit_report.json")

BASE_SHA = "869e7daf4ea33936f3a8fc73566f069ee28c9370718408bbf831e796169f17a2"
BASE_MTIME = "2026-11-19 22:19:02.075"
BASE_BYTES = 102125
BASE_LF = 482

def sha(b):
    return hashlib.sha256(b).hexdigest()

def mtime_str(p):
    m = os.path.getmtime(p)
    return datetime.fromtimestamp(m).strftime("%Y-%m-%d %H:%M:%S.") + ("%03d" % (int(m*1000) % 1000))

M53_TITLE = (
    "M53 PANEL 全表同步（本卡接管 COVERAGE 独占写权；"
    "三行语义栏标「③b 细则#1 级」（006C9890/00631CC0 去 ③b① 混写、004AB9B0 补标）；"
    "named 排除规则明确为 `::sub_[0-9A-Fa-f]+$`（任意长度十六进制），不用字面 8 位量；"
    "按此重算 21 行+TOTAL 的 named_S 全部与现值一致、面板行值改动 0 行；"
    "coverage.tsv 行数 18,498 不变、仅第 4 列 3 行语义改动；"
    "新增「RULING-R15 生效声明」节；不改其它文件、不 git commit）；"
)

NEW_SECTION = """## RULING-R15 生效声明（M53 落记）

> 本节把 RULING_R15 十项裁决的生效口径并列落记；不改任何 `[已证]` 行 grade。

- **D-38 (A)**：`slotN` 计入 `named`，DoD 判定使用 `named_pct_S(R14)`；`named_pct_S(strict)` 列保留为**参考列**，不参与达标判定（strict 口径 22 个子系统全部不达标）。
- **D-44 严格读法 + 双列并列**：对外声明一律用严格列——严格达标 **1/22（仅 S17）**；名义达标 **3/22** 为 **S15 / S16 / S17** 并列报告。另设 `proved_strict` = atlas 内 `[已证]` 且语义栏不含 `[未证]`，不批量改 grade（273 行不降级）；引用严格列须带「仍含待 F3a 第二类复核的行」限定。
- **D-39 (C)**：③④物理同源时可用「审计逐条复算 + 检出力反证」替代环④；规则已成文写入 `R14_COMMON §8.8`。K8 的 18 行经 ㉓ 陷阱检查只有 **11 行可辩护**，故 S13 proved 由 **89 → 100/240 = 41.67%**，仍远低于门槛 **120**，本条不产生达标。
- **D-41 (B)**：允许身份替代（YRpp 绑定 + 字节逐项吻合 / 调用者契约）；**DoD 增量 = 0**——S02 与 S19 的 named 分别 12.42% / 11.27%，永远不达标。
- **D-42 子项**：006C9890 / 00631CC0 / 004AB9B0 三行语义栏统一标「③b 细则#1 级」（多路守卫链，非跳表），不与 ③b①（跳表）混写。严格口径（若否掉细则#1）S03 7→5、S09 8→7；**本轮不执行该降级**（细则#1 级仍算 ③b、proved 不降级，须另裁才降）。
- **D-37 (D)**：S13 分母不改（**240** 保留）；按 `class_to_sub` 的归属改正只作**数据卫生**，不得作为达标手段。
- **D-43 (A)**：宽读法，条目关闭不再单独立项；两读法差 18 行（宽 3,349 / 严 3,331），PANEL 与台账并列报两读法数字。
- **D-45 (A)**：不许入表；1,491 行留 `UNDECIDABLE`，上界 ≤1,491（C 口径 ≤19,989），已并 P0-ADJ5 的 19 行保持不动，34 行仅结构证据不入表，`0042FF70` 剔除。
- **D-46 (A)**：窄读，条目关闭；`0045A640` 维持 `[静态推断]`，③b② 只认错误码 / 返回约定；S08 保持 **9/22（40.91%，门槛 11，差 2）**。
- **D-35 (D)**：允许在副本上打补丁 + 有界真机冒烟，放弃现有单测作部署依据；只碰副本（`ra2youli\\gamemd.exe` SHA-256 必须不变），主证伪器改为 6–8 处最易复现 NULL 路径的有界真机冒烟，禁止原地打。
- **D-36 (A)**：维持不设硬件断点、不写线程上下文，改派只读卡；(B)/(C) 物理前提不成立（首次 `#DB` 命中即终结游戏），本轮不新增任何写权限。

"""

STRICT_RULE_LINE = (
    "> **named 排除规则（任务 B / 事实更正 1，M53 明确）**：`named_pct_S(R14)` 的 `Class::sub_` "
    "排除统一用 `::sub_[0-9A-Fa-f]+$`（任意长度十六进制），不用字面 8 位量；atlas 内 7 行短形态"
    "（S19 6 行 `AudioController::sub_4060F0` 等 + S05 1 行 `TechnoClass::sub_70DE00`）按此规则正确排除。"
    "按字面 8 位匹配会漏这 7 行，使 named_S 虚高 +7（S19 +6 / S05 +1 / TOTAL +7）。\n"
)

def rep_once(txt, old, new, tag):
    c = txt.count(old)
    if c != 1:
        print("ABORT %s: anchor count=%d" % (tag, c)); sys.exit(2)
    return txt.replace(old, new, 1)

def main():
    mt = mtime_str(PAN)
    raw = open(PAN, "rb").read()
    s0 = sha(raw)
    print("GUARD mtime:", mt, "expect:", BASE_MTIME)
    print("GUARD sha  :", s0, "expect:", BASE_SHA)
    print("GUARD bytes:", len(raw), "lf:", raw.count(b"\n"))
    if mt != BASE_MTIME or s0 != BASE_SHA or len(raw) != BASE_BYTES or raw.count(b"\n") != BASE_LF:
        print("ABORT: third-party write detected before PANEL edit")
        sys.exit(2)
    txt = raw.decode("utf-8")

    # 1) title: prepend M53段 after opening （M52...
    txt = rep_once(txt,
        "（M52 PANEL 全表同步（对齐 M51 后现态；",
        "（" + M53_TITLE + "M52 PANEL 全表同步（对齐 M51 后现态；",
        "title")

    # 2a) main caliber named rule
    txt = rep_once(txt,
        "本列按 `::sub_[0-9A-Fa-f]+$` **前缀**排除，",
        "本列排除规则明确为 `::sub_[0-9A-Fa-f]+$`（任意长度十六进制），不用字面 8 位量，按此**前缀**排除，",
        "main-caliber")

    # 2b) strict section named rule (insert after the self-证 note line)
    strict_anchor = "> （该脚本同时复现本文件上方 `named_S(R14)` / `named_S(strict)` / `proved_n` 三列，用于口径自证）\n"
    txt = rep_once(txt, strict_anchor, strict_anchor + STRICT_RULE_LINE, "strict-rule")

    # 3) new section after three-denominator table
    sec_anchor = "三分母 A/B/C 在 M8 不变。\n\n## 覆盖面板（A 分母，每子系统 S01–S22；named_pct_S 双口径并列）"
    txt = rep_once(txt, sec_anchor,
        "三分母 A/B/C 在 M8 不变。\n\n" + NEW_SECTION +
        "## 覆盖面板（A 分母，每子系统 S01–S22；named_pct_S 双口径并列）",
        "new-section")

    out = txt.encode("utf-8")
    shutil.copy2(PAN, BAK)
    print("BACKUP:", BAK, "sha:", sha(open(BAK, "rb").read()))
    with open(PAN, "wb") as f:
        f.write(out)
    s1 = sha(open(PAN, "rb").read())
    print("WROTE PANEL.md new sha:", s1)
    print("bytes before/after: %d / %d" % (len(raw), len(out)))
    print("LF before/after: %d / %d" % (raw.count(b"\n"), out.count(b"\n")))
    print("trailing newline:", out.endswith(b"\n"))

    report = dict(before_sha=BASE_SHA, after_sha=s1,
                  before_bytes=len(raw), after_bytes=len(out),
                  before_lf=raw.count(b"\n"), after_lf=out.count(b"\n"),
                  edits=["title M53段", "main-caliber named rule", "strict-section named rule",
                         "new RULING-R15 生效声明 section"])
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("REPORT:", REPORT)

main()

# -*- coding: utf-8 -*-
"""把 R15 严格口径双列表追加进 PANEL.md（单次读→单次写，避免与并发会话交错）。

同时打印 coverage.tsv 的 sha256 供裁决书绑定。
"""
import hashlib, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
WORK = os.path.join(ROOT, "RULING_R15_20261119", "work")

ANCHOR = "## M50 并表说明"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    cov_sha = sha256(COV)
    data = json.load(open(os.path.join(WORK, "strict_panel.json"), encoding="utf-8"))
    rows, tot = data["rows"], data["total"]

    lines = []
    lines.append("## 严格口径双列表（R15 裁决 D-38(A) / D-44(严格) 后新增）")
    lines.append("")
    lines.append("> 口径：**D-38 选 (A)** ⇒ `named` 用 R14-R14 原文（`slotN` 计入），本表不重复 named 列；")
    lines.append("> **D-44 取严格读法** ⇒ `proved_strict` = atlas 内 `[已证]` **且语义栏不含 `[未证]`**。")
    lines.append(">")
    lines.append("> **对外声明达标一律用本表「严格」列：严格达标 1/22（仅 S17）；名义达标 3/22（S15/S16/S17）并列。**")
    lines.append(">")
    lines.append("> 数字绑定 `coverage.tsv` sha256 = `%s`" % cov_sha)
    lines.append("> 复算命令：`python lead\\next_re_20261117_r14\\RULING_R15_20261119\\work\\strict_panel.py`")
    lines.append("> （该脚本同时复现本文件上方 `named_S(R14)` / `named_S(strict)` / `proved_n` 三列，用于口径自证）")
    lines.append("")
    lines.append("| S | atlas_n | proved_n | proved_pct | proved_strict_n | proved_strict_pct | 门槛(50%) | 名义 | 严格 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for r in rows:
        lines.append("| %s | %d | %d | %.2f | **%d** | **%.2f** | %d | %s | %s |" % (
            r["S"], r["atlas_n"], r["proved_n"], r["pct_proved"],
            r["proved_strict_n"], r["pct_proved_strict"], r["thu_proved"],
            "达标" if r["dod_nominal"] else "—",
            "**达标**" if r["dod_strict"] else "—"))
    lines.append("| **TOTAL** | **%d** | **%d** | **%.2f** | **%d** | **%.2f** | — | **3/22** | **1/22** |" % (
        tot["atlas_n"], tot["proved_n"], 100.0 * tot["proved_n"] / tot["atlas_n"],
        tot["proved_strict_n"], 100.0 * tot["proved_strict_n"] / tot["atlas_n"]))
    lines.append("")
    lines.append("> 读数：全表 `[已证]` 1,455（atlas 内）中 **317 行**语义栏自陈 `[未证]`")
    lines.append("> （非 S22 = 274，其中 273 行是同一条「名字已证、语义据名推断」模板，1 行是台账坐标误入）")
    lines.append("> ⇒ 严格口径下净存 **1,138 行（8.81%）**，相对名义**净减 317**。")
    lines.append("> S15 由 63.92% 掉到 30.38%、S16 由 51.11% 掉到 22.22%，**双双失守**；S17 仅由 52.94% 掉到 51.96%，仍过门槛 51。")
    lines.append("")
    block = "\n".join(lines)

    with open(PANEL, "r", encoding="utf-8") as f:
        text = f.read()
    before = hashlib.sha256(text.encode("utf-8")).hexdigest()

    if "## 严格口径双列表" in text:
        print("ALREADY_PRESENT（未重复写入）")
        print("coverage sha256 =", cov_sha)
        return
    idx = text.find(ANCHOR)
    if idx < 0:
        print("ANCHOR_NOT_FOUND —— 中止，未写盘")
        sys.exit(2)

    new = text[:idx] + block + "\n" + text[idx:]
    with open(PANEL, "w", encoding="utf-8", newline="") as f:
        f.write(new)

    after = hashlib.sha256(new.encode("utf-8")).hexdigest()
    print("coverage sha256 =", cov_sha)
    print("PANEL sha256  before=%s  after=%s" % (before[:16], after[:16]))
    print("PANEL bytes   before=%d  after=%d  delta=+%d" % (
        len(text.encode("utf-8")), len(new.encode("utf-8")),
        len(new.encode("utf-8")) - len(text.encode("utf-8"))))
    print("行数 before=%d after=%d" % (text.count("\n") + 1, new.count("\n") + 1))


main()

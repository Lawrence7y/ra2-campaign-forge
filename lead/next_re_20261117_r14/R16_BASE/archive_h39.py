# -*- coding: utf-8 -*-
"""R16 · H39 看板归档：把 board 第 105–106 轮、第 107–109 轮两段逐字搬进 BOARD_ARCHIVE.md，
board 侧各留一行指针。硬约束：搬走的每一行必须逐字出现在 archive 里（missing=0）。"""
import hashlib, io, os, sys

sys.stdout.reconfigure(encoding="utf-8")

D     = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
BOARD = os.path.join(D, "STATUS_BOARD.md")
ARCH  = os.path.join(D, "BOARD_ARCHIVE.md")
OUT   = os.path.join(D, "R16_BASE", "H39_ARCHIVE.txt")

# 1-based 行号区间（含两端）：第 105–106 轮段 + 第 107–109 轮段
RANGE = (233, 258)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    with open(BOARD, "rb") as f:
        raw = f.read()
    h_before = sha(raw)
    n_before = len(raw)

    lines = raw.decode("utf-8").split("\n")
    # 保留末尾换行语义：split 后最后一元素为空串
    trailing = lines.pop() if lines and lines[-1] == "" else None

    i0, i1 = RANGE[0] - 1, RANGE[1] - 1
    seg = lines[i0:i1 + 1]

    # 段标题行必须是这两段的 ## 行
    assert seg[0].startswith("## 🔴 第 105–106 轮"), seg[0][:60]
    assert any(l.startswith("## 🔴 第 107–109 轮") for l in seg), "未找到第 107–109 轮标题"

    # 去掉段尾多余空行，便于归档拼接
    while seg and seg[-1].strip() == "":
        seg.pop()
    while seg and seg[0].strip() == "":
        seg.pop(0)

    with open(ARCH, "rb") as f:
        arc_before = f.read()
    h_arc = sha(arc_before)

    hdr = [
        "",
        "---",
        "",
        "## 📦 H39 归档（2026-11-20，R16 Lead 执行）：看板第 105–106 轮 / 第 107–109 轮两段",
        "",
        f"> 来源：`STATUS_BOARD.md` 第 {RANGE[0]}–{RANGE[1]} 行（搬走前的位置）。以下**逐字搬入**，未改一字；"
        f"board 侧已改为指针行。归档前 board {n_before} B / sha256 `{h_before[:16]}…`，"
        f"archive {len(arc_before)} B / sha256 `{h_arc[:16]}…`。",
        "",
    ]

    arc_add = ("\n".join(hdr) + "\n" + "\n".join(seg) + "\n").encode("utf-8")
    with open(ARCH, "ab") as f:
        f.write(arc_add)

    # board 侧替换为两行指针
    pointers = [
        "> 📦 ## 🔴 第 105–106 轮（2026-11-20 21:1x）· 746 批判死；11 行「0 引用」实为名字错 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）",
        "> 📦 ## 🔴 第 107–109 轮（2026-11-20 21:3x）· **`[已证]` 证据可解析率 28.90% → 50.73%** 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）",
    ]
    new_lines = lines[:i0] + pointers + lines[i1 + 1:]
    new_text = "\n".join(new_lines)
    if trailing is not None:
        new_text += "\n"
    with open(BOARD, "wb") as f:
        f.write(new_text.encode("utf-8"))

    # ---------- 校验 ----------
    with open(ARCH, "rb") as f:
        arc_after = f.read()
    with open(BOARD, "rb") as f:
        board_after = f.read()

    assert arc_after.startswith(arc_before), "archive 前缀被改动"
    assert arc_after[len(arc_before):] == arc_add, "archive 追加段不一致"

    at = arc_after.decode("utf-8")
    miss = [l for l in seg if l.strip() and l not in at]
    # board 新内容 = 旧内容去掉该区间 + 指针
    expect = ("\n".join(lines[:i0] + pointers + lines[i1 + 1:]) + ("\n" if trailing is not None else "")).encode("utf-8")
    assert board_after == expect, "board 重建结果与预期不符"

    rep = []
    rep.append("=== H39 看板归档 ===")
    rep.append(f"board   : {n_before} B / sha256 {h_before}")
    rep.append(f"archive : {len(arc_before)} B / sha256 {h_arc}")
    rep.append(f"搬迁区间: 第 {RANGE[0]}–{RANGE[1]} 行（{i1-i0+1} 行原始行，去除首尾空行后 {len(seg)} 行）")
    rep.append("")
    rep.append(f"archive 追加 {len(arc_add)} B（含 7 行归档头）→ {len(arc_after)} B / sha256 {sha(arc_after)}")
    rep.append(f"board   {n_before} → {len(board_after)} B（{len(board_after.encode())-len(raw)} B）；行数 "
               f"{len(lines)+(1 if trailing is not None else 0)} → {len(new_lines)+(1 if trailing is not None else 0)}")
    rep.append("")
    rep.append(f"【missing 校验】搬走的 {len([l for l in seg if l.strip()])} 条非空行中，未在 archive 找到的：**{len(miss)}** 条")
    if miss:
        rep.append("  缺失样例：")
        for m in miss[:5]:
            rep.append("    " + m[:120])
    rep.append(f"【board 重建校验】新 board == 「旧 board 去掉该区间 + 2 行指针」：{'PASS' if board_after == expect else 'FAIL'}")
    rep.append(f"【archive 前缀校验】追加前内容逐位未动：{'PASS' if arc_after.startswith(arc_before) else 'FAIL'}")
    rep.append("")
    rep.append("段标题行（已搬走的两段第一行）：")
    for l in seg:
        if l.startswith("## "):
            rep.append("  " + l[:100])

    txt = "\n".join(rep) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()

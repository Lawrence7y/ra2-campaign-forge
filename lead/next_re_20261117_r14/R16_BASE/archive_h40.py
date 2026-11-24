# -*- coding: utf-8 -*-
"""R16 · H40 看板归档：搬第 110 轮 + 第 111 轮两段进 BOARD_ARCHIVE.md，board 侧留指针行。
校验：搬走的每条非空行必须逐字出现在 archive（missing=0）；board 重建 == 旧 - 区间 + 指针。"""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

D     = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
BOARD = os.path.join(D, "STATUS_BOARD.md")
ARCH  = os.path.join(D, "BOARD_ARCHIVE.md")
OUT   = os.path.join(D, "R16_BASE", "H40_ARCHIVE.txt")

RANGE = (235, 258)   # 1-based 含两端：第 110 轮 + 第 111 轮


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    with open(BOARD, "rb") as f:
        raw = f.read()
    h_before = sha(raw)
    n_before = len(raw)

    text = raw.decode("utf-8")
    trailing = text.endswith("\n")
    lines = text.split("\n")
    if trailing:
        lines = lines[:-1]

    i0, i1 = RANGE[0] - 1, RANGE[1] - 1
    assert lines[i0].startswith("## 🔴 第 110 轮"), lines[i0][:50]
    assert any(l.startswith("## 🔴 第 111 轮") for l in lines[i0:i1 + 1]), "未找到第 111 轮标题"
    # 确认区间之后紧接着是下一段（不能吃掉别的段）
    nxt = lines[i1 + 1] if i1 + 1 < len(lines) else ""
    assert nxt.startswith("## 🔴 R16 接手"), "区间右边界不对，下一行不是 R16 接手段: " + nxt[:50]

    seg = lines[i0:i1 + 1]
    while seg and seg[-1].strip() == "":
        seg.pop()

    with open(ARCH, "rb") as f:
        arc_before = f.read()
    h_arc = sha(arc_before)

    hdr = [
        "",
        "---",
        "",
        "## 📦 H40 归档（2026-11-21，R16 Lead 执行）：看板第 110 轮 / 第 111 轮两段",
        "",
        f"> 来源：`STATUS_BOARD.md` 第 {RANGE[0]}–{RANGE[1]} 行（搬走前位置）。以下**逐字搬入**，未改一字；"
        f"board 侧已改为指针行。归档前 board {n_before} B / sha256 `{h_before[:16]}…`，"
        f"archive {len(arc_before)} B / sha256 `{h_arc[:16]}…`。",
        "",
    ]
    arc_add = ("\n".join(hdr) + "\n" + "\n".join(seg) + "\n").encode("utf-8")
    with open(ARCH, "ab") as f:
        f.write(arc_add)

    pointers = [
        "> 📦 ## 🔴 第 110 轮（2026-11-20 21:5x）· 证据指针修复收尾：R_OK 843 / 1,654（50.97%） 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）",
        "> 📦 ## 🔴 第 111 轮（2026-11-20 22:0x）· 802 行 trace-only 探针：D-47 的第三个量化后果 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）",
    ]
    new_lines = lines[:i0] + pointers + lines[i1 + 1:]
    new_text = "\n".join(new_lines) + ("\n" if trailing else "")
    with open(BOARD, "wb") as f:
        f.write(new_text.encode("utf-8"))

    with open(ARCH, "rb") as f:
        arc_after = f.read()
    with open(BOARD, "rb") as f:
        board_after = f.read()

    assert arc_after.startswith(arc_before), "archive 前缀被改"
    assert arc_after[len(arc_before):] == arc_add, "archive 追加段不一致"
    at = arc_after.decode("utf-8")
    miss = [l for l in seg if l.strip() and l not in at]
    expect = ("\n".join(lines[:i0] + pointers + lines[i1 + 1:]) + ("\n" if trailing else "")).encode("utf-8")
    assert board_after == expect, "board 重建与预期不符"

    rep = [
        "=== H40 看板归档 ===",
        f"board   : {n_before} B / sha256 {h_before}",
        f"archive : {len(arc_before)} B / sha256 {h_arc}",
        f"搬迁区间: 第 {RANGE[0]}–{RANGE[1]} 行（原始 {i1-i0+1} 行，去尾空行后 {len(seg)} 行）",
        "",
        f"archive +{len(arc_add)} B → {len(arc_after)} B / sha256 {sha(arc_after)}",
        f"board   {n_before} → {len(board_after)} B ; 行数 {len(lines)} → {len(new_lines)}",
        "",
        f"【missing 校验】{len([l for l in seg if l.strip()])} 条非空行未在 archive 找到的：**{len(miss)}** 条",
        f"【board 重建校验】{'PASS' if board_after == expect else 'FAIL'}",
        f"【archive 前缀校验】{'PASS' if arc_after.startswith(arc_before) else 'FAIL'}",
        "",
        "搬迁段的 ## 标题：",
    ]
    for l in seg:
        if l.startswith("## "):
            rep.append("  " + l[:100])

    txt = "\n".join(rep) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()

# -*- coding: utf-8 -*-
"""Leader 自查（W7 收尾用）：只核 phase-1 八份回件里**新增的、会改变卡片文字**的断言。

不是重做八份复核——只挑「如果错了，汇总判定书就会写错」的几条，自己反汇编/实查一遍：
  S1  card_0087E8E0.md:54-55 「无 linker map / .map 均为 FinalAlert2 地图」是否真为假（A1 的 REFUTED 局部）
  S2  card_0087E8E0.md:47 的 0x67C8E0 → 0x6C8E0（A1 必改项 2）
  S3  card_0087E8E0.md:306 的 0x56721B → 0x56721A（A1 必改项 3）
  S4  0x6D3DF5 真实字节 756e=jne、test eax,eax 在 0x6D3DFF（A3 的订正）
  S5  Q3 跨度 0x28E5A8 = 2,680,232 B（B2 的算术）
  S6  Disp 口径：disp_hits(0x87E8E0)==[]、disp_hits_field(0x28) 计数（A1 §1.5）
零真机、零注入、只读。
"""
import io
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\goal3t_nightwatch_20261102\swarm_20261104"))
from ra2tool import Engine  # noqa: E402

OUT = []
def P(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)

P("=" * 74)
P("Leader 自查（W7 收尾）  run_at =", __import__("datetime").datetime.now().isoformat(timespec="seconds"))
P("=" * 74)

# ---------- S1: .map 文件普查 ----------
P("\n[S1] 仓内 *.map 普查（A1 称：1206 个 .map，其中 1 个是 ra2render.map linker map）")
total = 0
hits = []
by_ext_like = {}
for dp, dns, fns in os.walk(ROOT):
    # 跳过 .git / 临时树，避免把版本库对象算进来
    dns[:] = [d for d in dns if d not in (".git", "node_modules", "__pycache__", ".tmp")]
    for fn in fns:
        if fn.lower().endswith(".map"):
            p = os.path.join(dp, fn)
            total += 1
            try:
                head = open(p, "rb").read(2048)
            except OSError:
                continue
            # MSVC linker map 的典型头：含 "  Timestamp is" 或 "Preferred load address is"
            txt = head.decode("latin-1", "replace")
            is_linker = ("Preferred load address is" in txt) or ("Timestamp is" in txt) or ("Start" in txt and "Length" in txt and "Name" in txt and "Class" in txt)
            first = txt.splitlines()[0][:60] if txt.splitlines() else ""
            if "ra2render" in fn.lower() or is_linker:
                hits.append((p, is_linker, first, "ra2render" in fn.lower()))
P("  TOTAL .map =", total)
P("  疑似 linker map 或名字含 ra2render 的：", len(hits))
for p, is_linker, first, name_hit in hits[:10]:
    P("    -", p.replace(ROOT + "\\", ""), "| linker=%s name_hit=%s" % (is_linker, name_hit), "| first=", first)

# ---------- Engine ----------
e = Engine()
P("\n[Engine] SHA256 =", e.sha)
P("  IMAGEBASE = 0x%X" % e.IB)
P("  COVERAGE  =", e.coverage)

# ---------- S2/S3/S4: 逐址字节 ----------
P("\n[S2] card:47 的地址：0x67C8E0 vs 0x6C8E0")
for va in (0x67C8E0, 0x6C8E0):
    P("  0x%06X  raw = %s" % (va, e.raw(va, 8).hex()))
    for line in e.disasm(va, 12):
        P("      ", line)

P("\n[S3] card:306 的地址：0x56721B vs 0x56721A")
for va in (0x56721A, 0x56721B):
    P("  0x%06X  raw = %s" % (va, e.raw(va, 8).hex()))
    for line in e.disasm(va, 8):
        P("      ", line)

P("\n[S4] 0x6D3DF0..0x6D3E10 逐条（A3 订正：0x6D3DF5 是 jne、test 在 0x6D3DFF）")
for line in e.disasm(0x6D3DF0, 0x20):
    P("   ", line)
P("  原始字节 0x6D3DF5 =", e.raw(0x6D3DF5, 6).hex())
P("  原始字节 0x6D3DFF =", e.raw(0x6D3DFF, 4).hex())

# ---------- S5: 跨度算术 ----------
P("\n[S5] Q3 四地址跨度 0x28E5A8 算术")
span = 0x28E5A8
P("  0x28E5A8 =", span, "B =", round(span / 1024 / 1024, 6), "MiB")
P("  十进制约 2.7 MB ?", 2.6 <= span / 1e6 <= 2.8)

# ---------- S6: disp 口径 ----------
P("\n[S6] A1 §1.5 的 disp 口径复跑")
for va in (0x87E8E0, 0x87E8B8):
    P("  disp_hits(0x%X) = %r" % (va, e.disp_hits(va)))
P("  disp_hits_field(0x28) =", len(e.disp_hits_field(0x28)))

# ---------- 七个被核文件哈希（确认收尾时未被改动） ----------
P("\n[S7] 七份被核文件哈希（收尾时刻）")
import hashlib
d = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections")
FILES = ["card_0087E8E0.md", "card_00A8EC34.md", "card_00B0CE88.md", "card_00A8ED50.md",
         "Q2_ALPHA.md", "Q3_FRAME_EDGE_SPEC.md", "Q4_REDLINE.md"]
SHAS = []
for f in FILES:
    b = open(os.path.join(d, f), "rb").read()
    h = hashlib.sha256(b).hexdigest()
    SHAS.append(h)
    P("  %-24s %8d  %s" % (f, len(b), h))
P("  COMPOSITE(concat in table order) =", hashlib.sha256(b"".join(
    open(os.path.join(d, f), "rb").read() for f in FILES)).hexdigest())

P("\n=== END ===")
io.open(os.path.join(ROOT, r"lead\re_line_20261105\W7_W4_REVIEW\_leader_spotcheck_w7_out.txt"),
        "w", encoding="utf-8").write("\n".join(OUT) + "\n")

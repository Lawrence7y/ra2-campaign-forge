"""T1：从 .rdata 枚举 vtable 并按表间边界数槽；尝试复现审计基线 14,044 槽/1,214 表。"""
import struct
import re_lib as R

b = R.Bin()
rtti = R.RTTI(b)
colset = set(rtti.cols.keys())

# 只在 .rdata 扫 vtable-4 位置（dword == 合法 COL）
s = b.sec(".rdata")
buf = b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
base = s["va"]
vpos = []  # (position, col_va)
for i in range(0, len(buf) - 4, 4):
    v = struct.unpack_from("<I", buf, i)[0]
    if v in colset:
        vpos.append((base + i, v))
vpos.sort()

print("rdata vtable-4 positions:", len(vpos))
print("distinct COLs referenced in rdata:", len(set(v for _, v in vpos)))
print("total COLs:", len(colset))

# 相邻 vtable-4 位置间距分布
gaps = {}
for k in range(len(vpos) - 1):
    d = vpos[k + 1][0] - vpos[k][0]
    gaps[d] = gaps.get(d, 0) + 1
print("gap distribution (top 15):", sorted(gaps.items(), key=lambda x: -x[1])[:15])

# 数槽：vtable = pos+4；下一个 vtable-4 位置 = 上界；槽数 = (next_pos - pos)//4 - 1
# 但需排除"非 vtable-4 的 COL 引用"（如静态初始化器里的立即数）。先全部按边界算。
total_slots = 0
zero_slot_tables = 0
neg = 0
dist = {}
rows = []
for k, (pos, col) in enumerate(vpos):
    nxt = vpos[k + 1][0] if k + 1 < len(vpos) else base + len(buf)
    slots = (nxt - pos) // 4 - 1
    if slots < 0:
        neg += 1
        slots = 0
    if slots == 0:
        zero_slot_tables += 1
    dist[slots] = dist.get(slots, 0) + 1
    total_slots += slots
    rows.append((pos + 4, col, rtti.cols[col]["name"], slots, nxt))

print("total_slots (all-adjacent-boundary):", total_slots)
print("zero-slot tables:", zero_slot_tables, "neg:", neg)
print("slot-count distribution top20:", sorted(dist.items(), key=lambda x: -x[1])[:20])

# 保存全表
with open("rdata_vtables.tsv", "w", encoding="utf-8") as f:
    f.write("vtable\tcol\tname\tslots\tnext_pos\n")
    for vt, col, nm, slots, nxt in rows:
        f.write("%08X\t%08X\t%s\t%d\t%08X\n" % (vt, col, nm, slots, nxt))
print("wrote rdata_vtables.tsv rows=", len(rows))

# 抽验线索虚表的槽数
for vt_known in [0x7F3058, 0x7F2FCC, 0x7E6114, 0x7E1964, 0x7EBE3C, 0x7F7B2C]:
    for vt, col, nm, slots, nxt in rows:
        if vt == vt_known:
            print("CLUE vt=%08X %-55s slots=%d next=%08X" % (vt, nm, slots, nxt))
            break

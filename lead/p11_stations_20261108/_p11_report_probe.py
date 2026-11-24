# -*- coding: utf-8 -*-
# P11_STATION_NAMING.md 撰写员本会话只读探针：哈希绑定 + 0x6E9F74 跳表重算 + 崩点字节裁决
# 零真机 / 零采样 / 零进程 API / 零网络 / 零写盘（仅 stdout）
import struct, hashlib, os

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")

data = open(EXE, "rb").read()
print("EXE SHA256", hashlib.sha256(data).hexdigest())
print("EXE BYTES", len(data))

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
size_opt = struct.unpack_from("<H", data, e_lfanew + 20)[0]
opt_off = e_lfanew + 24
image_base = struct.unpack_from("<I", data, opt_off + 28)[0]
sec_off = opt_off + size_opt
sections = []
for i in range(nsec):
    o = sec_off + i * 40
    name = data[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    sections.append((name, vaddr, vsize, rawptr, rawsize))
    print("SEC", name, "VA", hex(vaddr), "VS", hex(vsize), "RAW", hex(rawptr), hex(rawsize))

def off(va):
    rva = va - image_base
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

def rd(va, n):
    o = off(va)
    return data[o:o + n]

print("--- 哈希绑定（本会话 hashlib 实算）---")
for rel in [
    r"lead\p11_stations_20261108\_p11_stations_naming.md",
    r"lead\spec_static_closure_20261108\STATIC_GAP_CLOSURE.md",
    r"lead\spec_static_closure_20261108\_sc_scan_out.txt",
    r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md",
    r"lead\re_line_20261105\W8_STATIC_LOCATE\W8_STATIC_LOCATE.md",
]:
    b = open(os.path.join(ROOT, rel), "rb").read()
    print(rel, hashlib.sha256(b).hexdigest(), len(b))

print("--- 跳表 0x6E9F74 重算（65 条目，0-based）---")
TBL = 0x6E9F74
ents = list(struct.unpack_from("<65I", data, off(TBL)))
for i in (0, 16, 49, 55, 56, 57, 58):
    print("entry[%d]=0x%X" % (i, ents[i]))

print("--- 派发器字节（索引基数裁决）---")
print("0x6E944B bytes:", rd(0x6E944B, 5).hex(" "), "(expect 83 f8 40 = cmp eax,0x40 -> 0-based, 上界64)")
print("0x6E945B bytes:", rd(0x6E945B, 7).hex(" "), "(expect ff 24 95 74 9f 6e 00 = jmp [eax*4+0x6E9F74])")

print("--- 崩点裁决：0x6E9DD3 的 call 归属 ---")
cb = rd(0x6E9DD3, 5)
rel = struct.unpack("<i", cb[1:5])[0]
tgt = 0x6E9DD3 + 5 + rel
print("0x6E9DD3 bytes:", cb.hex(" "), "-> call 0x%X" % tgt)
print("0x6E9DD3 in entry[57] block [0x6E9DC7,0x6E9DE0):", 0x6E9DC7 <= 0x6E9DD3 < 0x6E9DE0)
print("0x6E9DD3 in entry[56] block [0x6E9DAE,0x6E9DC7):", 0x6E9DAE <= 0x6E9DD3 < 0x6E9DC7)
print("entry[57] 块起点字节:", rd(0x6E9DC7, 8).hex(" "), "(expect 8b 44 24 10 = mov eax,[esp+0x10])")
print("0x6F0130 起点字节:", rd(0x6F0130, 9).hex(" "))

print("--- 旁证 ---")
cb2 = rd(0x6ED167, 5)
rel2 = struct.unpack("<i", cb2[1:5])[0]
print("0x6ED167 bytes:", cb2.hex(" "), "-> call 0x%X" % (0x6ED167 + 5 + rel2))
print("0x4166D0 bytes:", rd(0x4166D0, 5).hex(" "), "-> jmp 0x%X" % (0x4166D0 + 5 + struct.unpack("<i", rd(0x4166D1, 4))[0]))
print("DONE")

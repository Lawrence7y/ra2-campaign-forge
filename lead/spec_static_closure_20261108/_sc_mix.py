# -*- coding: utf-8 -*-
# _sc_mix.py — S4: 在 ra2youli/*.mix 磁盘镜像内做 b"PatrolScan" 原始字节扫描（零真机、纯文件只读）
# 同时解析 MIX 头/索引，尝试把命中归属到条目并判定该条目是否带压缩头。
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/spec_static_closure_20261108/_sc_mix.py"
import os, struct, hashlib, time

T0 = time.time()
D = r"D:\Project\ra2-campaign-forge\ra2youli"
OUT = []
NEEDLES = [b"PatrolScan", b"patrolscan"]

def chunked_find(path, needles, chunk=64 * 1024 * 1024, overlap=64):
    hits = []
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        base = 0
        tail = b""
        while True:
            blob = f.read(chunk)
            if not blob:
                break
            buf = tail + blob
            for nd in needles:
                s = 0
                while True:
                    i = buf.find(nd, s)
                    if i < 0:
                        break
                    hits.append((base - len(tail) + i, nd))
                    s = i + 1
            base += len(blob)
            tail = buf[-overlap:]
    return size, hits

def parse_index(path):
    """解析 MIX 头与索引。返回 (file_size, header_tuple, entries) 或 None。
    头: int16 w0 | int16 count | int32 body_size。entries=[(id, off, size)]（off 相对条目数据区）。"""
    with open(path, "rb") as f:
        hdr = f.read(10)
    if len(hdr) < 10:
        return None
    w0, count, body = struct.unpack_from("<HHI", hdr, 0)
    if w0 != 0:
        return (os.path.getsize(path), ("ENCRYPTED?", w0, count, body), [])
    idx_off = 6
    idx_sz = count * 12
    with open(path, "rb") as f:
        f.seek(idx_off)
        idx = f.read(idx_sz)
    if len(idx) < idx_sz:
        return None
    entries = []
    for k in range(count):
        fid, off, sz = struct.unpack_from("<III", idx, k * 12)
        entries.append((fid, off, sz))
    return (os.path.getsize(path), (w0, count, body), entries)

def entry_at(entries, data_start, file_off):
    """把文件内偏移映射到索引条目（需 data_start=索引区结束偏移）。"""
    rel = file_off - data_start
    if rel < 0:
        return None
    for fid, off, sz in entries:
        if off <= rel < off + sz:
            return (fid, off, sz, rel - off)
    return None

targets = []
for fn in sorted(os.listdir(D)):
    if fn.lower().endswith((".mix", ".mmx")):
        p = os.path.join(D, fn)
        targets.append((fn, os.path.getsize(p)))
print("== MIX 清单 ==")
for fn, sz in targets:
    print("MIXFILE %-24s %d" % (fn, sz))

SCAN_FIRST = ["ra2md.mix", "ra2.mix", "expandmd01.mix", "expandmd98.mix",
              "expandmd98.mix.ra2forge.bak", "expandmd98.mix.old-pre-migrate",
              "multi.mix", "multimd.mix", "wdt.mix", "theme.mix", "thememd.mix"]

for fn, sz in targets:
    p = os.path.join(D, fn)
    if fn not in SCAN_FIRST:
        # 其余（movies/maps/language 等）也做一遍，但放在主目标之后；这里先全扫，代价可接受
        pass
    size, hits = chunked_find(p, NEEDLES)
    if hits:
        print("\n== HIT %s size=%d hits=%d ==" % (fn, size, len(hits)))
        idx = parse_index(p)
        data_start = None
        if idx:
            fs, hdr, entries = idx
            print("  header=%r entries=%d" % (hdr, len(entries)))
            if entries:
                # 估计数据区起点 = 6 + 12*count（RA2 可能 +4 校验）；用 max(offset+size) 反推校验
                idx_end_plain = 6 + 12 * len(entries)
                mx = max(off + sz for _, off, sz in entries)
                print("  max(offset+size)=%d  plain_idx_end=%d  file_size=%d  => data_start_guess=%d" % (mx, idx_end_plain, fs, fs - mx))
                data_start = fs - mx
        with open(p, "rb") as f:
            for off, nd in hits[:40]:
                f.seek(max(0, off - 2048))
                ctx = f.read(4096 + 2048)
                print("  ---- hit@file_off=0x%X (%d) needle=%r ----" % (off, off, nd))
                print("  ctx:", ctx.decode("latin1", errors="replace").replace("\r", "\\r").replace("\n", "\n  "))
                if data_start is not None and data_start > 0:
                    ent = entry_at(entries, data_start, off)
                    if ent:
                        fid, eoff, esz, ein = ent
                        try:
                            f.seek(data_start + eoff)
                            head = f.read(8)
                            comp = (struct.unpack_from("<H", head, 0)[0] & 0x8000) != 0 if len(head) >= 2 else False
                            print("  entry id=0x%08X off=%d size=%d in_entry=%d entry_head=%s compressed_header=%s"
                                  % (fid, eoff, esz, ein, head.hex(), comp))
                        except OSError as e:
                            print("  entry id=0x%08X off=%d size=%d (seek失败 %s)" % (fid, eoff, esz, e))
                    else:
                        print("  entry: 未归属（data_start 猜测不符）")
                else:
                    print("  entry: 索引头异常，跳过归属（data_start=%r）" % (data_start,))
    else:
        print("NOHIT %-24s size=%d" % (fn, size))

print("\n== RUN TIME %.1fs ==" % (time.time() - T0))

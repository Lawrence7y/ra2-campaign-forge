"""精确定位热点函数所在的虚表与槽号（不再用范围重叠，取最近 vt 且偏移 4 对齐）。"""
import json
import struct

import audit_lib as A

VTJSON = (r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10"
          r"\W130_atlas\vtables_canonical.json")

HOT = [(0x494B60, "A 34.8%"), (0x491820, "B 22.3%"),
       (0x485020, "C 21.6%"), (0x6D7840, "D 6.1%"),
       (0x497FD0, "E 4.8%"), (0x5657A0, "F 3.2%")]


def main():
    b = A.Bin()
    rows, _ = A.load_func_atlas()
    rec = dict(rows)
    d = json.load(open(VTJSON, encoding="utf-8"))
    vts = [(v["vt"], v["class"], v["col_offset"]) for v in d["vtables"]]

    for fn, tag in HOT:
        pat = struct.pack("<I", fn)
        print("=" * 90)
        print("热点 %s  fn %08X  size=%s  is_fnptr=%s" %
              (tag, fn, rec.get(fn, {}).get("size", "?"),
               rec.get(fn, {}).get("is_fnptr", "?")))
        hits = []
        for s in b.sections:
            buf = b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
            i = 0
            while True:
                i = buf.find(pat, i)
                if i < 0:
                    break
                hits.append((s["name"], s["va"] + i))
                i += 1
        if not hits:
            print("   （无 dword 引用 ⇒ 只可能是直接 call 或不可达）")
        for secname, hit in hits:
            # 精确：取 vt <= hit 且 (hit-vt)%4==0 的**最大** vt
            cand = [(vt, cls, co) for vt, cls, co in vts
                    if vt <= hit and (hit - vt) % 4 == 0]
            if not cand:
                print("   %-7s %08X  (非虚表槽)" % (secname, hit))
                continue
            vt, cls, co = max(cand, key=lambda t: t[0])
            off = hit - vt
            print("   %-7s %08X -> vt=%08X col=%d %-44s slot %d (+0x%X)"
                  % (secname, hit, vt, co, cls, off // 4, off))
        print()


if __name__ == "__main__":
    main()

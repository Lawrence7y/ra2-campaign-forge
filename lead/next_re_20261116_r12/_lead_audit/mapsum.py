"""紧凑对比两个 MAP 的 [Units] 段：数量、拥有者、几何散布。只打印摘要。"""
import re
import statistics as st

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out"
PATHS = {
    "range1":  BASE + r"\_archive_range1\trip_range1_r1\installed_inputs\RA2F_M1.MAP",
    "c2_near": BASE + r"\_archive_c2\trip_c2_near_r1\installed_inputs\RA2F_M1.MAP",
}


def parse_units(path):
    raw = open(path, "rb").read().decode("latin-1", "replace")
    m = re.search(r"\[Units\](.*?)(?=\n\[|\Z)", raw, re.S)
    body = m.group(1) if m else ""
    out = []
    for line in body.split("\n"):
        line = line.strip()
        if "=" not in line:
            continue
        _, v = line.split("=", 1)
        f = [x.strip() for x in v.split(",")]
        if len(f) >= 6 and f[1] == "MTNK":
            try:
                out.append((f[0], int(f[3]), int(f[4]), f[5]))
            except Exception:
                pass
    return out


def main():
    for label, p in PATHS.items():
        u = parse_units(p)
        own = {}
        mis = {}
        for o, _, _, mi in u:
            own[o] = own.get(o, 0) + 1
            mis[mi] = mis.get(mi, 0) + 1
        xs = [x for _, x, _, _ in u]
        ys = [y for _, _, y, _ in u]
        print("=== %s : %d MTNK ===" % (label, len(u)))
        print("   owners  : %s" % own)
        print("   missions: %s" % mis)
        if xs:
            w = max(xs) - min(xs) + 1
            h = max(ys) - min(ys) + 1
            print("   col %d..%d (med %.1f)  row %d..%d (med %.1f)"
                  % (min(xs), max(xs), st.median(xs), min(ys), max(ys), st.median(ys)))
            print("   bbox %dx%d = %d cells ; density %.3f units/cell" % (w, h, w * h, len(u) / (w * h)))
        print()

    a = {(x, y) for _, x, y, _ in parse_units(PATHS["range1"])}
    b = {(x, y) for _, x, y, _ in parse_units(PATHS["c2_near"])}
    print("=== 几何差异 ===")
    print("  range1 占位 cell 数 = %d" % len(a))
    print("  c2_near 占位 cell 数 = %d" % len(b))
    print("  交集 = %d ; range1-only = %d ; c2_near-only = %d"
          % (len(a & b), len(a - b), len(b - a)))
    print("  Jaccard = %.4f" % (len(a & b) / len(a | b) if (a | b) else 0))


if __name__ == "__main__":
    main()

import json, os, datetime

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
GUARD = os.path.realpath(ROOT)

def ok(p):
    rp = os.path.realpath(p)
    if not (rp == GUARD or rp.startswith(GUARD + os.sep)):
        raise SystemExit("bad path: " + rp)
    return rp

def mt(p):
    s = os.stat(ok(p))
    return s.st_mtime, datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")

print("== measure json mtimes (for png-minus-json delta)")
for p in (ROOT + r"\archive_T42\measure_w1.json",
          ROOT + r"\archive_T42\measure_w2.json",
          ROOT + r"\archive_T33\measure_w2.json",
          ROOT + r"\archive_T45\measure_w2.json",
          ROOT + r"\l1_20261023e4\measure_w2.json",
          ROOT + r"\archive_T33\measure_w1.json",
          ROOT + r"\archive_T45\measure_w1.json"):
    m, s = mt(p)
    print("%-90s %.9f %s" % (p.rsplit("\\", 1)[-1] + " @ " + p.rsplit("\\", 2)[-2], m, s))

print()
print("== png-minus-json deltas")
pairs = [
    (ROOT + r"\archive_T42\measure_w1_end_x.png", ROOT + r"\archive_T42\measure_w1.json"),
    (ROOT + r"\archive_T42\measure_w2_end_x.png", ROOT + r"\archive_T42\measure_w2.json"),
    (ROOT + r"\archive_T33\measure_w2_end_x.png", ROOT + r"\archive_T33\measure_w2.json"),
    (ROOT + r"\archive_T45\measure_w2_end_x.png", ROOT + r"\archive_T45\measure_w2.json"),
    (ROOT + r"\l1_20261023e4\measure_w2_end_x.png", ROOT + r"\l1_20261023e4\measure_w2.json"),
]
for png, js in pairs:
    mp, _ = mt(png); mj, _ = mt(js)
    print("%-46s - %-22s = %+.1f ms" % (png.rsplit("\\", 2)[-2] + "\\" + png.rsplit("\\", 1)[-1], js.rsplit("\\", 1)[-1], (mp - mj) * 1000))

print()
print("== w1-png mtime vs same-trip w2 t_abs0")
for d in ("archive_T33", "archive_T42", "archive_T45"):
    pw = ok(GUARD + "\\" + d + "\\measure_w1_end_x.png")
    with open(ok(GUARD + "\\" + d + "\\measure_w2.json"), "r", encoding="utf-8") as fh:
        mj = json.load(fh)
    mp = os.stat(pw).st_mtime
    print("%s w1png mtime=%.7f  w2 t_abs0=%.7f  delta=%+.4f us" % (d, mp, mj["t_abs0"], (mp - mj["t_abs0"]) * 1e6))

print()
print("== forensics rows for T33/T34/T36/T38/T41/T45/l3r (measure_forensics_*)")
for d in ("archive_T33", "archive_T34", "archive_T36", "archive_T38", "archive_T41", "archive_T45", "l3_20261023r"):
    fp = ok(GUARD + "\\" + d + "\\qc151_fields.json")
    with open(fp, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    meta = [r for r in rows if r.get("group") == "META"][:1]
    if meta:
        print("--", d, "META first ts=", meta[0].get("ts"), " card=", meta[0].get("value"))
    for r in rows:
        k = str(r.get("key", ""))
        if "forensics" in k:
            v = r.get("value")
            if isinstance(v, dict):
                print("   %s ts=%s hwnd=%s fg=%s focus=%s cur=%s empty=%s png=%s ok=%s wh=%s" % (
                    k, r.get("ts"), v.get("game_hwnd"), v.get("fg_hwnd"), v.get("focus_ok"),
                    v.get("current_frame"), v.get("empty_window"), v.get("forensics_png"),
                    v.get("capture_ok"), v.get("capture_wh")))
            else:
                print("   %s ts=%s value=%r" % (k, r.get("ts"), v))

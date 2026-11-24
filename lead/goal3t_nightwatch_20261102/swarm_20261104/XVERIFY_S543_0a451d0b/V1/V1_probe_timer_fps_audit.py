import os
import glob
import json

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"

# Ground truth visual readings from our verified images
# Format: (relpath, visual_screen_type, visual_time_str)
READINGS = {
    r"archive_T33\measure_w1_end_x.png": ("计分屏", "00:00:24"),
    r"archive_T33\measure_w2_end_x.png": ("纯战斗无面板", None),
    r"archive_T34\measure_w1_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T34\measure_w2_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T36\measure_w1_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T36\measure_w2_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T38\measure_w1_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T38\measure_w2_end_x.png": ("计分屏", "00:00:32"),
    r"archive_T39\measure_w2_end_x.png": ("计分屏", "00:00:31"),
    r"archive_T40\measure_w1_end_x.png": ("计分屏", "00:00:30"),
    r"archive_T40\measure_w2_end_x.png": ("计分屏", "00:00:30"),
    r"archive_T41\measure_w1_end_x.png": ("计分屏", "00:00:28"),
    r"archive_T41\measure_w2_end_x.png": ("计分屏", "00:00:28"),
    r"archive_T42\measure_w1_end_x.png": ("纯战斗无面板", None),
    r"archive_T42\measure_w2_end_x.png": ("纯战斗无面板", None),
    r"archive_T43\measure_w1_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T43\measure_w2_end_x.png": ("计分屏", "00:00:10"),
    r"archive_T44\measure_w1_end_x.png": ("计分屏", "00:00:29"),
    r"archive_T44\measure_w2_end_x.png": ("计分屏", "00:00:29"),
    r"archive_T45\measure_w1_end_x.png": ("计分屏", "00:00:28"),
    r"archive_T45\measure_w2_end_x.png": ("纯战斗无面板", None),
    r"archive_T49_u0800\measure_w1_end_x.png": ("计分屏", "00:00:15"),
    r"archive_T49_u0800\measure_w2_end_x.png": ("计分屏", "00:00:15"),
    r"l1_20261023e4\measure_w2_end_x.png": ("Windows桌面/编辑器", None),
    r"l3_20261023r\measure_w2_end_x.png": ("计分屏", "00:02:56"),
}

def parse_time_s(t_str):
    if not t_str:
        return None
    parts = t_str.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

print(f"{'Path':40s} | {'Type':12s} | {'f0':5s} | {'f1':5s} | {'df':4s} | {'TimeStr':8s} | {'Sec':4s} | {'ImplicitFPS':11s} | {'Diff_31.2':9s}")
print("-" * 115)

# Per trip audit as well
trip_data = {}

for rel, (vtype, t_str) in sorted(READINGS.items()):
    p = os.path.join(BASE_DIR, rel)
    json_path = p.replace("_end_x.png", ".json")
    f0, f1, df = None, None, None
    if os.path.exists(json_path):
        j = json.load(open(json_path, encoding="utf-8"))
        ed = j.get("frame_edges", [])
        if ed:
            f0 = ed[0][0]
            f1 = ed[-1][0]
            df = f1 - f0
    
    sec = parse_time_s(t_str)
    if sec and f1 is not None and sec > 0:
        imp_fps = f1 / sec
        diff_312 = imp_fps - 31.2
        imp_fps_str = f"{imp_fps:6.2f}"
        diff_str = f"{diff_312:+6.2f}"
    else:
        imp_fps = None
        imp_fps_str = "N/A"
        diff_str = "N/A"
    
    print(f"{rel:40s} | {vtype:12s} | {str(f0):5s} | {str(f1):5s} | {str(df):4s} | {str(t_str):8s} | {str(sec):4s} | {imp_fps_str:11s} | {diff_str:9s}")
    
    trip = rel.split("\\")[0]
    trip_data.setdefault(trip, []).append({
        "rel": rel, "vtype": vtype, "t_str": t_str, "f0": f0, "f1": f1, "df": df, "sec": sec, "imp_fps": imp_fps
    })

print("\n" + "=" * 80)
print("=== PER TRIP SUMMARY & COMPARISON WITH S543 LEADER TABLE ===")
print("=" * 80)

# Leader's table from S543:
leader_table = {
    "archive_T33": {"f": 738, "t": "00:00:24", "fps": 30.75, "diff": -0.45},
    "archive_T34": {"f": 302, "t": "00:00:10", "fps": 30.20, "diff": -1.00},
    "archive_T36": {"f": 310, "t": "00:00:10", "fps": 31.00, "diff": -0.20},
    "archive_T38": {"f": 940, "t": "00:00:30", "fps": 31.33, "diff": +0.13}, # NOTE: Leader claims 00:00:30
    "archive_T39": {"f": 945, "t": "00:00:31", "fps": 30.48, "diff": -0.72},
    "archive_T40": {"f": 908, "t": "00:00:30", "fps": 30.27, "diff": -0.93},
    "archive_T41": {"f": 860, "t": "00:00:28", "fps": 30.71, "diff": -0.49},
    "archive_T43": {"f": 314, "t": "00:00:10", "fps": 31.40, "diff": +0.20},
    "archive_T44": {"f": 883, "t": "00:00:29", "fps": 30.45, "diff": -0.75},
    "archive_T45": {"f": 845, "t": "00:00:28", "fps": 30.18, "diff": -1.02},
    "archive_T49_u0800": {"f": 448, "t": "00:00:15", "fps": 29.87, "diff": -1.33},
    "l3_20261023r": {"f": 4367, "t": "00:02:56", "fps": 24.81, "diff": -6.39},
}

for trip, ldata in sorted(leader_table.items()):
    actual_items = trip_data.get(trip, [])
    print(f"\nTrip: {trip}")
    print(f"  Leader claimed: f={ldata['f']}, time={ldata['t']}, fps={ldata['fps']}, diff={ldata['diff']}")
    for item in actual_items:
        w_name = item['rel'].split("\\")[1]
        print(f"  Actual {w_name:22s}: f1={item['f1']}, time={item['t_str']}, actual_fps={item['imp_fps']}")

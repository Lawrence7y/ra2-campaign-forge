import os
import json
import hashlib
from PIL import Image
import numpy as np

base_qc161 = r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip'
v4e_dir = os.path.join(base_qc161, 'l3_1101v4e')
v4f_dir = os.path.join(base_qc161, 'l3_1101v4f')
v4g_dir = os.path.join(base_qc161, 'l3_1101v4g')
src_carrier = os.path.join(base_qc161, '_src_L3_sf10c_20261021')

def sha256_file(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("=== 1. CHECKING QC151_FIELDS.JSON ===")
for name, d in [('v4e', v4e_dir), ('v4f', v4f_dir), ('v4g', v4g_dir)]:
    p = os.path.join(d, 'qc151_fields.json')
    with open(p, 'r', encoding='utf-8') as f:
        raw_list = json.load(f)
    qf = {item['key']: item['value'] for item in raw_list if 'key' in item}
    print(f"--- {name} ---")
    print(f"h7_frame_wait: {qf.get('h7_frame_wait')}")
    print(f"h7_nav_to_measure: {qf.get('h7_nav_to_measure')}")
    print(f"gate.ok: {qf.get('gate:ok')}, gate.pre_fps15: {qf.get('gate:pre_fps15')}, gate.units0: {qf.get('gate:units0')}")
    print(f"verify_nav: menu={qf.get('verify_ok_nav_menu')}, setup={qf.get('verify_ok_nav_setup')}, start={qf.get('verify_ok_nav_start')}")
    print(f"clicked: menu={qf.get('clicked_nav_menu')}, setup={qf.get('clicked_nav_setup')}, start={qf.get('clicked_nav_start')}")
    print(f"signature_got: menu={qf.get('signature_got_nav_menu')}, setup={qf.get('signature_got_nav_setup')}, start={qf.get('signature_got_nav_start')}")
    print(f"stage_seconds: frame={qf.get('stage_seconds:frame')}, nav_start={qf.get('stage_seconds:nav_start')}")
    print(f"stage_begin: nav_start={qf.get('stage_begin:nav_start')}, frame={qf.get('stage_begin:frame')}, measure_w0={qf.get('stage_begin:measure_w0')}, T1={qf.get('stage_begin:T1')}")
    print(f"trip_seconds: {qf.get('trip_seconds')}")
    print(f"in_tactical_target: {qf.get('in_tactical_target')}, seconds_to_window: {qf.get('seconds_to_window')}, window_stabilize_seconds: {qf.get('window_stabilize_seconds')}")

print("\n=== 2. CHECKING EXCEPT FILES & DIFF ===")
src_except = os.path.join(src_carrier, 'except.txt')
if os.path.exists(src_except):
    print(f"src_carrier except.txt: size={os.path.getsize(src_except)}, sha256={sha256_file(src_except)}")
    with open(src_except, 'r', encoding='utf-8', errors='ignore') as f:
        src_lines = f.readlines()
    print(f"src lines count: {len(src_lines)}")
    has_007cfc9f = any('007CFC9F' in l for l in src_lines)
    print(f"src contains 007CFC9F: {has_007cfc9f}")

for name, d in [('v4e', v4e_dir), ('v4f', v4f_dir), ('v4g', v4g_dir)]:
    diff_p = os.path.join(d, 'except_set_diff.json')
    if os.path.exists(diff_p):
        with open(diff_p, 'r', encoding='utf-8') as f:
            diff_data = json.load(f)
        print(f"{name} diff: new_exception_count={diff_data.get('new_exception_count')}, no_new_exception={diff_data.get('no_new_exception')}, pre_line_count={diff_data.get('pre_line_count')}, post_line_count={diff_data.get('post_line_count')}")
    for fn in os.listdir(d):
        if fn.startswith('except_post_'):
            fp = os.path.join(d, fn)
            print(f"{name} {fn}: size={os.path.getsize(fp)}, sha256={sha256_file(fp)}")
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            print(f"  lines count: {len(lines)}, contains 007CFC9F: {any('007CFC9F' in l for l in lines)}")

print("\n=== 3. CHECKING MEASURE_W0.JSON ===")
for name, d in [('v4f', v4f_dir), ('v4g', v4g_dir), ('v4e', v4e_dir)]:
    mp = os.path.join(d, 'measure_w0.json')
    if os.path.exists(mp):
        with open(mp, 'r', encoding='utf-8') as f:
            mdata = json.load(f)
        counters = mdata.get('counters', [])
        samples = mdata.get('samples', {})
        f_samples = samples.get('f', [])
        distinct_f = set(f_samples)
        print(f"--- {name} measure_w0 ---")
        print(f"f_samples len: {len(f_samples)}, distinct f: {distinct_f if len(distinct_f) < 10 else f'len={len(distinct_f)} min={min(distinct_f)} max={max(distinct_f)}'}")
        print(f"counters count: {len(counters)}")
        for idx, c in enumerate(counters):
            print(f"  idx {idx}: t_rel={c.get('t_rel')}, units={c.get('units')}, infantry={c.get('infantry')}, g_items={c.get('g_items')}, g_valid={c.get('g_valid')}")
        print(f"gate in measure_w0: {mdata.get('gate')}")
        print(f"verdict in measure_w0: {mdata.get('verdict')}")
    else:
        print(f"--- {name} measure_w0: NOT FOUND ---")

print("\n=== 4. CHECKING PNGS ===")
for img_name in ['frame_target_01.png', 'fs_boot_probe.png']:
    print(f"Checking {img_name}:")
    hashes = {}
    imgs = {}
    for name, d in [('v4e', v4e_dir), ('v4f', v4f_dir), ('v4g', v4g_dir)]:
        p = os.path.join(d, img_name)
        h = sha256_file(p)
        hashes[name] = h
        if os.path.exists(p):
            imgs[name] = np.array(Image.open(p))
            print(f"  {name} {img_name}: sha256={h}, shape={imgs[name].shape}")
        else:
            print(f"  {name} {img_name}: NOT FOUND")
    if 'v4e' in imgs and 'v4f' in imgs:
        diff_ef = np.abs(imgs['v4e'].astype(int) - imgs['v4f'].astype(int))
        print(f"  v4e vs v4f max_diff={diff_ef.max()}, diff_pixels={np.count_nonzero(diff_ef)}")
    if 'v4e' in imgs and 'v4g' in imgs:
        diff_eg = np.abs(imgs['v4e'].astype(int) - imgs['v4g'].astype(int))
        print(f"  v4e vs v4g max_diff={diff_eg.max()}, diff_pixels={np.count_nonzero(diff_eg)}")
    if 'v4f' in imgs and 'v4g' in imgs:
        diff_fg = np.abs(imgs['v4f'].astype(int) - imgs['v4g'].astype(int))
        print(f"  v4f vs v4g max_diff={diff_fg.max()}, diff_pixels={np.count_nonzero(diff_fg)}")

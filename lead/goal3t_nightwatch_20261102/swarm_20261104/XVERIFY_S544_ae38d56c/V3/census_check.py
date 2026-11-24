import os
import json
import re

base_dir = r'D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip'

subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
print(f"Total subdirectories in qc161_u0400_trip: {len(subdirs)}")

# 1. Check except files
except_trips = []
trips_with_007cfc9f = []
other_except_trips = []

for d in subdirs:
    dp = os.path.join(base_dir, d)
    # look for except_post_*.txt or except.txt
    except_files = [f for f in os.listdir(dp) if f.startswith('except_post_') or f == 'except.txt']
    if except_files:
        except_trips.append((d, except_files))
        found_007 = False
        found_other = []
        for ef in except_files:
            ef_path = os.path.join(dp, ef)
            try:
                with open(ef_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if '007CFC9F' in content:
                    found_007 = True
                # look for exception addresses: "Exception occurred at: XXXXXXXX" or "Eip: XXXXXXXX"
                addrs = re.findall(r'Exception occurred at:\s*([0-9a-fA-F]+)', content)
                for a in addrs:
                    if a.upper() != '007CFC9F':
                        found_other.append(a.upper())
            except Exception as e:
                print(f"Error reading {ef_path}: {e}")
        if found_007:
            trips_with_007cfc9f.append(d)
        if found_other:
            other_except_trips.append((d, found_other))

print(f"Trips with except files: {len(except_trips)}")
print(f"Trips with 007CFC9F: {len(trips_with_007cfc9f)}")
print(f"Trips with other exception addresses: {len(other_except_trips)}")

# 2. Check measure_w0.json
measure_w0_trips = []
no_advance_units0_zero = []

for d in subdirs:
    dp = os.path.join(base_dir, d)
    mp = os.path.join(dp, 'measure_w0.json')
    if os.path.exists(mp):
        measure_w0_trips.append(d)
        try:
            with open(mp, 'r', encoding='utf-8') as f:
                mdata = json.load(f)
            gate = mdata.get('gate', {})
            units0 = gate.get('units0')
            pre_fps15 = gate.get('pre_fps15')
            verdict = mdata.get('verdict')
            if units0 == 0 and verdict == 'no_advance':
                no_advance_units0_zero.append((d, units0, pre_fps15, verdict))
        except Exception as e:
            print(f"Error reading {mp}: {e}")

print(f"Total measure_w0.json found: {len(measure_w0_trips)}")
print(f"Trips with units0 == 0 and verdict == 'no_advance' ({len(no_advance_units0_zero)}):")
for item in no_advance_units0_zero:
    print(" ", item)

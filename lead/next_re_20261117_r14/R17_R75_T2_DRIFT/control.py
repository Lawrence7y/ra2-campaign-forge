# R42-T2-DRIFT Q5 positive control - independent Python csv implementation
# Reads the two source TSVs directly (no intermediate files), computes the same metrics as analyze.ps1.
import csv

base = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
f_old = base + r'\R17_R70_T1_REPRO\files_scale_today.tsv'
f_new = base + r'\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv'

def load(path):
    d = {}
    with open(path, 'r', encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            d[row['rel']] = (int(row['bytes']), row.get('mtime_ns', ''), row.get('ext', ''), row.get('selfkind', ''))
    return d

old = load(f_old)
new = load(f_new)

only_a = [(rel, v[0]) for rel, v in new.items() if rel not in old]
only_old = [(rel, v[0]) for rel, v in old.items() if rel not in new]
changed = [(rel, old[rel][0], v[0]) for rel, v in new.items()
           if rel in old and old[rel][0] != v[0]]

print('METRIC\tVALUE\tSOURCE\tCOLUMN\tSCRIPT')
print(f'old_rows\t{len(old)}\tfiles_scale_today.tsv\trel\tcontrol.py')
print(f'new_rows\t{len(new)}\tfiles_tier_A_snap2.tsv\trel\tcontrol.py')
print(f'old_total_bytes\t{sum(v[0] for v in old.values())}\tfiles_scale_today.tsv\tbytes\tcontrol.py')
print(f'new_total_bytes\t{sum(v[0] for v in new.values())}\tfiles_tier_A_snap2.tsv\tbytes\tcontrol.py')
print(f'Q1_onlyA_count\t{len(only_a)}\tBOTH(rel join)\trel/bytes\tcontrol.py')
print(f'Q1_onlyA_bytes\t{sum(b for _, b in only_a)}\tfiles_tier_A_snap2.tsv\tbytes\tcontrol.py')
print(f'Q1_onlyOld_count\t{len(only_old)}\tBOTH(rel join)\trel/bytes\tcontrol.py')
print(f'Q1_onlyOld_bytes\t{sum(b for _, b in only_old)}\tfiles_scale_today.tsv\tbytes\tcontrol.py')
print(f'Q1_changed_count\t{len(changed)}\tBOTH(rel join)\tbytes\tcontrol.py')
print(f'Q1_changed_delta_bytes\t{sum(nb - ob for _, ob, nb in changed)}\tBOTH\tdelta=new-old\tcontrol.py')

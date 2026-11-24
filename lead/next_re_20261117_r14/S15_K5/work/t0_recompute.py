from pathlib import Path
import re, hashlib, math, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'D:\Project\ra2-campaign-forge')
R14 = ROOT / 'lead' / 'next_re_20261117_r14'
COV = R14 / 'COVERAGE' / 'coverage.tsv'
ATL = ROOT / 'lead' / 'next_re_20261112_r10' / 'W130_atlas' / 'function_atlas.tsv'
BIN = ROOT / 'ra2youli' / 'gamemd.exe'
DELTAS = [R14 / 'S15-K3' / 'coverage_delta.tsv', R14 / 'S15_K4' / 'coverage_delta.tsv']
OUT = Path(__file__).resolve().parents[1] / 'EVIDENCE' / 't0_baseline.txt'

def read_tsv(path):
    with path.open('r', encoding='utf-8-sig', errors='replace') as f:
        lines=[ln.rstrip('\r\n').split('\t') for ln in f]
    return [row for row in lines if row and re.fullmatch(r'[0-9a-fA-F]{8}', row[0].strip())]

def norm(e): return e.strip().upper().zfill(8)
def is_named(name):
    n=(name or '').strip()
    if not n or n.lower().startswith('sub_'): return False
    if re.match(r'^[^:]+::sub_[0-9a-fA-F]+$', n): return False
    return True
atlas = {norm(r[0]) for r in read_tsv(ATL)}
cov_rows=[r for r in read_tsv(COV) if len(r)>4 and r[1].strip()=='S15']
cov={norm(r[0]):r for r in cov_rows}
base=sorted(set(cov)&atlas)
base_named={e for e in base if is_named(cov[e][2])}
base_proved={e for e in base if cov[e][4].strip()=='[已证]'}
unnamed=[e for e in base if not is_named(cov[e][2])]
need=math.ceil(0.9*len(base))
merged_named=set(base_named); merged_proved=set(base_proved); delta_rows=[]
for p in DELTAS:
    for r in read_tsv(p):
        if len(r)<5: continue
        e=norm(r[0]); name=r[2].strip(); grade=r[4].strip()
        delta_rows.append((p.parent.name,e,name,grade,str(e in atlas),str(e in cov)))
        if is_named(name): merged_named.add(e)
        if grade=='[已证]': merged_proved.add(e)
        elif e in merged_proved: merged_proved.discard(e)
resid=[e for e in base if e not in merged_named]
lines=[]
lines.append('SHA256 '+hashlib.sha256(BIN.read_bytes()).hexdigest().upper()+' size '+str(BIN.stat().st_size))
lines.append('target expected 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476')
lines.append('coverage_S15_rows '+str(len(cov_rows))+' atlas_intersection '+str(len(base))+' outside_atlas '+','.join(sorted(set(cov)-atlas)))
lines.append('baseline_named_S '+str(len(base_named))+' named_pct '+format(100*len(base_named)/len(base),'.2f'))
lines.append('baseline_proved '+str(len(base_proved))+' proved_pct '+format(100*len(base_proved)/len(base),'.2f'))
lines.append('need '+str(need)+' baseline_shortfall '+str(need-len(base_named)))
lines.append('baseline_unnamed_count '+str(len(unnamed)))
lines.append('baseline_unnamed '+','.join(unnamed))
lines.append('delta_rows (card,entry,name,grade,in_atlas,in_coverage)')
lines += ['\t'.join(x) for x in delta_rows]
lines.append('merged_named_S '+str(len(merged_named))+' pct '+format(100*len(merged_named)/len(base),'.2f')+' shortfall '+str(need-len(merged_named)))
lines.append('merged_proved '+str(len(merged_proved))+' pct '+format(100*len(merged_proved)/len(base),'.2f'))
lines.append('residual_unnamed_after_K3K4_count '+str(len(resid)))
lines.append('residual_unnamed_after_K3K4 '+','.join(resid))
lines.append('target_check_141 '+str(len(merged_named)==141).lower())
OUT.write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('\n'.join(lines))

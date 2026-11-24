import io, os, csv
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
SEM = os.path.join(R14, r'R17_R88_T1_SEMDEF\tier_final.tsv')
REJ = os.path.join(R14, r'R17_R92_T1_REJUDGE\rejudge1242.tsv')
BASE = os.path.join(R14, r'R17_R78_T1_RECLASS\files_tier_Cprime.tsv')

def load(p, cols):
    rows = list(csv.reader(io.open(p, encoding='utf-8', errors='replace'), delimiter='\t'))
    h = rows[0]
    idx = {c: h.index(c) for c in cols if c in h}
    return h, rows[1:], idx

hS, dS, iS = load(SEM, ['rel', 'bytes', 'why_content'])
hR, dR, iR = load(REJ, ['rel', 'bytes', 'new_verdict', 'old_verdict'])
hC, dC, iC = load(BASE, ['rel', 'bytes'])

sem_rel = set(r[iS['rel']] for r in dS)
cprime_rel = set(r[iC['rel']] for r in dC)
rej_new = {r[iR['rel']]: r[iR['new_verdict']] for r in dR}
rej_old = {r[iR['rel']]: r[iR['old_verdict']] for r in dR}
rej_bytes = {r[iR['rel']]: int(r[iR['bytes']]) for r in dR}

print('tier_final = %d 件' % len(sem_rel))
print('Cprime     = %d 件' % len(cprime_rel))
print('rejudge    = %d 件' % len(rej_new))

# tier_final 里那两个来源的划分
p1a = set(r[iS['rel']] for r in dS if r[iS['why_content']].startswith('有内容证据=前8KiB'))
obj = set(r[iS['rel']] for r in dS if not r[iS['why_content']].startswith('有内容证据=前8KiB'))
print('\ntier_final 来源: P1a(前8KiB) = %d ; 逐件判为对象 = %d' % (len(p1a), len(obj)))

# 那 732 件与 rejudge 的 1242 交集
print('\n「逐件判为对象」732 与 rejudge 1242 的交集 = %d' % len(obj & set(rej_new)))
in_rej = obj & set(rej_new)
from collections import Counter
print('  这 732 件的旧 verdict 分布:', dict(Counter(rej_old[x] for x in in_rej)))
print('  这 732 件的新 verdict 分布:', dict(Counter(rej_new[x] for x in in_rej)))

# 新对象集
new_obj = set(r for r in rej_new if rej_new[r] == '对象抄本')
print('\n新对象集 = %d 件' % len(new_obj))
print('  其中原属 Cprime 的:', len(new_obj & cprime_rel))
print('  其中不属 Cprime 的:', len(new_obj - cprime_rel))
print('    不属且旧=无法判定:', len(set(x for x in new_obj - cprime_rel if rej_old[x] == '无法判定')))
print('    不属且旧=过程输出:', len(set(x for x in new_obj - cprime_rel if rej_old[x] == '过程输出')))

# 关键：tier_final 里那 732 是否都在 Cprime
print('\n「逐件判为对象」732 里, 属 Cprime 的:', len(obj & cprime_rel), '/', len(obj))

nb = sum(rej_bytes[x] for x in new_obj)
ob = sum(int(r[iS['bytes']]) for r in dS if r[iS['rel']] in obj)
print('\n旧「逐件对象」字节 = %d ; 新对象集字节 = %d' % (ob, nb))

import io, os, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P_SM = os.path.join(R14, r'S21_DIRECT\_audit\EVIDENCE\scan_mine.json')
P_E8 = os.path.join(R14, r'S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json')
P_SW = os.path.join(R14, r'S08_KPROVED2\_audit\EVIDENCE\sweep.json')
P_A2 = os.path.join(R14, r'D41_SUBST\_audit\EVIDENCE\a2_sites.json')

sm = json.load(io.open(P_SM, encoding='utf-8', errors='replace'))
e8 = json.load(io.open(P_E8, encoding='utf-8', errors='replace'))
sw = json.load(io.open(P_SW, encoding='utf-8', errors='replace'))
a2 = json.load(io.open(P_A2, encoding='utf-8', errors='replace'))

sm_calls = [tuple(x) for x in sm['calls']]
e8_pairs = [tuple(x) for x in e8]
sw_e8 = [tuple(x) for x in sw['e8']]
print('scan_mine.calls = %d 对' % len(sm_calls))
print('e8_sites_audit  = %d 对' % len(e8_pairs))
print('sweep.e8        = %d 对' % len(sw_e8))
print()
print('scan_mine.calls == e8_sites_audit ?', set(sm_calls) == set(e8_pairs))
print('scan_mine.calls == sweep.e8 ?', set(sm_calls) == set(sw_e8))
print('e8_sites_audit == sweep.e8 ?', set(e8_pairs) == set(sw_e8))

# 「两个 68,253」：a2_sites 的 calls 调用点集合 vs 这些的 site 集合
a2_sites = set()
for k, lst in a2['calls'].items():
    a2_sites.update(lst)
sm_sites = set(x[0] for x in sm_calls)
print()
print('a2_sites.calls 调用点(%d) ∩ scan_mine site(%d) = %d'
      % (len(a2_sites), len(sm_sites), len(a2_sites & sm_sites)))
print('  scan_mine 首元素 = %r' % (sm_calls[0],))
print('  a2_sites 某键首值示例 = %r' % (list(a2['calls'].items())[0],))

import io, os, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
a2 = json.load(io.open(os.path.join(R14, r'D41_SUBST\_audit\EVIDENCE\a2_sites.json'),
                       encoding='utf-8', errors='replace'))
sm = json.load(io.open(os.path.join(R14, r'S21_DIRECT\_audit\EVIDENCE\scan_mine.json'),
                       encoding='utf-8', errors='replace'))

# a2_sites: calls 是 {hex_str_target: [hex_str_site, ...]}
a2_pairs = set()
for tgt_hex, sites in a2['calls'].items():
    t = int(tgt_hex, 16)
    for s_hex in sites:
        a2_pairs.add((int(s_hex, 16), t))
sm_pairs = set(tuple(x) for x in sm['calls'])

print('a2_sites 转成 (site,target) 十进制对 = %d 个' % len(a2_pairs))
print('scan_mine.calls                        = %d 个' % len(sm_pairs))
print()
print('两者集合相等 ?', a2_pairs == sm_pairs)
print('交集大小 =', len(a2_pairs & sm_pairs))
print()
if a2_pairs:
    ex = sorted(a2_pairs)[0]
    print('a2_sites 最小对 (site,target) = %d, %d = %#x, %#x' % (ex[0], ex[1], ex[0], ex[1]))
exs = sorted(sm_pairs)[0]
print('scan_mine 最小对               = %d, %d = %#x, %#x' % (exs[0], exs[1], exs[0], exs[1]))
print()
print('⇒ 若相等，则「两个 68,253 交集为 0」是字符串/整数编码差异造成的假象')

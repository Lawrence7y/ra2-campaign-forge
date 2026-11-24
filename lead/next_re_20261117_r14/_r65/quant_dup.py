import io, os, json

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P = {
 'scan_mine': r'S21_DIRECT\_audit\EVIDENCE\scan_mine.json',
 'e8_sites':  r'S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json',
 'sweep':     r'S08_KPROVED2\_audit\EVIDENCE\sweep.json',
 'a2_sites':  r'D41_SUBST\_audit\EVIDENCE\a2_sites.json',
}
tot = {}
for k, rel in P.items():
    p = os.path.join(R14, rel)
    size = os.path.getsize(p)
    d = json.load(io.open(p, encoding='utf-8', errors='replace'))
    print('=== %s : %d B' % (k, size))
    if k == 'a2_sites':
        calls_obj = d['calls']
        n = sum(len(v) for v in calls_obj.values())
        # 序列化 calls 部分估算字节
        s = json.dumps(calls_obj, separators=(',', ':'))
        print('   calls: %d 键 / %d 调用点 ; 序列化 %d B (占 %.1f%%)' % (len(calls_obj), n, len(s), 100.0*len(s)/size))
        print('   bounds: %d 条' % len(d['bounds']))
        tot[k] = (size, len(s))
    elif k == 'e8_sites':
        s = json.dumps(d, separators=(',', ':'))
        print('   整个 list: %d 对 ; 序列化 %d B (100%%)' % (len(d), len(s)))
        tot[k] = (size, size)
    elif k == 'sweep':
        e8 = d['e8']
        s = json.dumps(e8, separators=(',', ':'))
        ins = d.get('installs', [])
        si = json.dumps(ins, separators=(',', ':'))
        print('   e8: %d 对 ; 序列化 %d B (占 %.1f%%)' % (len(e8), len(s), 100.0*len(s)/size))
        print('   installs: %d 条 ; 序列化 %d B (占 %.1f%%)' % (len(ins), len(si), 100.0*len(si)/size))
        print('   其余(instructions/e8_sites 计数): 少量')
        tot[k] = (size, len(s))
    elif k == 'scan_mine':
        c = d.get('calls', [])
        s = json.dumps(c, separators=(',', ':'))
        print('   calls: %d 对 ; 序列化 %d B (占 %.1f%%)' % (len(c), len(s), 100.0*len(s)/size))
        print('   其余 11 个键 = 元数据 + 计数（无对象内容）')
        tot[k] = (size, len(s))
    print()

print('=== 重复量估算 ===')
# scan_mine / e8_sites / sweep 三份的 calls 部分内容相同
tri = ['scan_mine', 'e8_sites', 'sweep']
sizes = [(k, tot[k][0], tot[k][1]) for k in tri]
print('%-11s %12s %12s' % ('file', 'total B', 'calls-part B'))
for k, s, c in sizes:
    print('%-11s %12d %12d' % (k, s, c))
dup = sum(c for _, _, c in sizes)
print()
print('三份 calls 部分序列化合计 = %d B（内容是同一批 68,253 对）' % dup)
print('若只计一次，重复部分 = %d B（另两份）' % (dup - min(c for _, _, c in sizes)))
print('但盘上字节 = %d B（三份文件总字节）' % sum(s for _, s, _ in sizes))

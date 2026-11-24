import io, os, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
A2 = None
for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
    if 'a2_sites.json' in fs:
        A2 = os.path.join(dp, 'a2_sites.json')
        break
assert A2, 'a2_sites.json not found'
print('file:', A2.replace(ROOT + '\\', ''))
print('bytes:', os.path.getsize(A2))

d = json.load(io.open(A2, encoding='utf-8', errors='replace'))
print('top keys:', list(d.keys()))
calls = d.get('calls', {})
bounds = d.get('bounds', [])
print('calls keys = %d ; bounds = %d' % (len(calls), len(bounds)))
print('bounds sample:', bounds[:5])

# bounds 的元素形态
types = collections.Counter(type(x).__name__ for x in bounds)
print('bounds 元素类型:', dict(types))
if bounds and isinstance(bounds[0], (str, int)):
    lens = collections.Counter(len(str(x)) for x in bounds)
    print('bounds 元素长度分布:', dict(lens))

# 核对 T1 声称的 1,392,592
print()
print('T1 声称: calls键 6,728 / 调用点 68,253 / bounds 1,392,592 / 合计 1,467,573')
n_call_sites = sum(len(v) for v in calls.values())
print('实测: calls键 %d / 调用点 %d / bounds %d / 合计 %d'
      % (len(calls), n_call_sites, len(bounds), len(calls) + n_call_sites + len(bounds)))

# bounds 段的字节占比
tot = os.path.getsize(A2)
# 粗算：每个 bounds 元素在 JSON 里约 "00123456", = 11 B（8 hex + 2 quote + 1 comma）
print()
print('bounds 记录数 %d ; T1 声称其字节 16,711,118 (94.82%%)' % len(bounds))
print('  16,711,118 / %d = %.3f B/条' % (len(bounds), 16711118 / len(bounds)))

import io, os, re

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
G = os.path.join(R14, 'check_disc.py')
V = os.path.join(R14, 'recheck_verify.py')

# ---- 修缺陷 1：rows= 应跳过 DISC_RECHECK 自述行（否则补凭证反而 +1 FAIL）----
t = io.open(G, encoding='utf-8').read()
OLD = """    m3 = re.fullmatch(r'rows=(\\d+)', head)
    if m3:
        n = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for _ in f: n += 1
        return ((n - 1) == int(m3.group(1))), 'rows=%d' % (n - 1)"""
NEW = """    m3 = re.fullmatch(r'rows=(\\d+)', head)
    if m3:
        # R55 修：跳过表头与 DISC_RECHECK 自述行，否则「补凭证」会把 rows 计数 +1 而误 FAIL
        n = 0
        hdr_seen = 0
        with io.open(ap, encoding='utf-8', errors='replace') as f:
            for ln in f:
                s = ln.strip()
                if s.startswith('DISC_RECHECK '):
                    continue
                if hdr_seen == 0:
                    hdr_seen = 1
                    continue
                n += 1
        return (n == int(m3.group(1))), 'rows=%d' % n"""
assert OLD in t, 'rows= block not found'
t = t.replace(OLD, NEW, 1)
t = t.replace("GATE_VER = 'R53'", "GATE_VER = 'R55'", 1)
io.open(G, 'w', encoding='utf-8').write(t)
print('defect1 fixed: rows= now skips DISC_RECHECK lines; GATE_VER -> R55')

# ---- 修缺陷 2：ROUND_WINDOWS 必须覆盖到当前轮（r54/r55），否则 R4 必然 FAIL ----
v = io.open(V, encoding='utf-8').read()
# 找 ROUND_WINDOWS 表里的最后一条
m = re.search(r"\(5[0-9], '[^']*', '[^']*', '[^']*', '[^']*'\)", v)
print('last window entry sample:', m.group(0) if m else 'NOT FOUND')

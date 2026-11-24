import io, os, re, hashlib, shutil

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
G = os.path.join(R14, 'check_disc.py')
F = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')

# 计算冻结档内容哈希（按字节，LF-only）
raw = io.open(F, 'rb').read()
h = hashlib.sha256(raw).hexdigest()
print('frozen registry sha256 =', h)
print('bytes =', len(raw))

t = io.open(G, encoding='utf-8').read()
shutil.copy2(G, G + '.bakR58c')

# 在 GATE_VER 后加常量
anchor = "GATE_VER = 'R58'"
assert anchor in t
if 'FREEZE_SHA256' not in t:
    t = t.replace(anchor, anchor + "\nFREEZE_SHA256 = '%s'   # DISC_UNVERIFIABLE.tsv 的 sha256（防静默篡改）" % h, 1)
    print('added FREEZE_SHA256 constant')

# 在载入冻结档后校验哈希
OLD = "    notes.append('C11 frozen-class registry loaded: %d ids %s' % (len(C11_FROZEN), sorted(C11_FROZEN)))"
NEW = """    _fh = hashlib.sha256(io.open(_FREEZE, 'rb').read()).hexdigest()
    if _fh != FREEZE_SHA256:
        fails.append('C11 frozen-class registry TAMPERED: sha256 %s != registered %s '
                     '(新增/删除不可验证类必须经 Lead 显式改 FREEZE_SHA256)' % (_fh[:16], FREEZE_SHA256[:16]))
    notes.append('C11 frozen-class registry loaded: %d ids %s ; sha256=%s %s'
                 % (len(C11_FROZEN), sorted(C11_FROZEN), _fh[:16],
                    'OK' if _fh == FREEZE_SHA256 else 'TAMPERED'))"""
assert OLD in t
t = t.replace(OLD, NEW, 1)

# 确保 import hashlib
if 'import hashlib' not in t:
    t = t.replace('import io, os, re, sys', 'import io, os, re, sys, hashlib', 1)
    print('added hashlib import')

io.open(G, 'w', encoding='utf-8').write(t)
print('wired freeze-hash check')

#!/usr/bin/env python3
"""R147 M：门禁回归 —— C16_FLOORS 加 152、表项 145→146、重钉 sha、GATE_VER R146→R147。

纪律：先备份 → 断言旧值恰好出现一次 → 替换 → 重算 sha → 回读。
重钉 sha 前必须先**用现表复现旧钉**（证明我的算法与门禁一致，否则重钉等于把 bug 钉进去）。
"""
import io, os, re, json, time, hashlib

HERE = '/home/t628/projects/ra2-campaign-forge'
GATE = HERE + '/lead/next_re_20261117_r14/check_disc.py'
BL = HERE + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

s0 = read(GATE)

# ---- 0 用现表复现旧钉（证明算法一致）----
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', s0, re.S)
tbl = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
ck('现表可解析且含 151', 151 in tbl, len(tbl))
norm = '\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl))
old_pin = hashlib.sha256(norm.encode()).hexdigest()
reg = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", s0).group(1)
ck('用现表复现已注册的旧钉（算法与门禁一致）', old_pin == reg, [old_pin[:16], reg[:16]])

# ---- 1 新 floor：从 r147k 的结果取实测字节 ----
w = json.load(open(HERE + '/_r147/r147k_write.json'))
size152 = w['size152']; floor152 = w['floor152']
ck('r147k 记录的 §2.152 字节数 > 1000', size152 > 1000, size152)
ck('floor = 实测 - 21', floor152 == size152 - 21, [size152, floor152])

# 独立复算 §2.152 字节（不复用 r147k 函数，防止同一个 bug 自证）
rc = read(HERE + '/lead/next_re_20261117_r14/R14_COMMON.md')
cur = None; acc = []
for l in rc.split('\n'):
    if re.match(r'^##\s+2\.152\b', l):
        cur = 152; acc = [l]; continue
    if cur == 152:
        if re.match(r'^##\s+', l):
            break
        acc.append(l)
indep = len('\n'.join(acc).encode('utf-8'))
ck('独立复算 §2.152 字节 == r147k 记录', indep == size152, [indep, size152])

# ---- 2 改表 ----
ck('前置 151: 10384 恰 1 次', s0.count('151: 10384') == 1, s0.count('151: 10384'))
ck('前置 152 尚未入表（幂等）', '152: ' + str(floor152) not in s0, True)
s1 = s0.replace('151: 10384,', '151: 10384, 152: ' + str(floor152) + ',', 1)
ck('表已加入 152（出现 1 次）', s1.count('152: ' + str(floor152)) == 1, s1.count('152: ' + str(floor152)))

# ---- 3 重钉 sha ----
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', s1, re.S)
tbl2 = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m2.group(1)))
ck('新表含 152 且 151 未变', 152 in tbl2 and tbl2[151] == 10384 and tbl2[152] == floor152,
   [tbl2.get(151), tbl2.get(152)])
norm2 = '\n'.join('%d:%d' % (k, tbl2[k]) for k in sorted(tbl2))
new_pin = hashlib.sha256(norm2.encode()).hexdigest()
ck('新钉 != 旧钉', new_pin != old_pin, [old_pin[:16], new_pin[:16]])
s2 = s1.replace(old_pin, new_pin, 1)
ck('sha 常量已替换恰 1 次', s2.count(new_pin) == 1, s2.count(new_pin))

# ---- 4 GATE_VER ----
ck('前置 GATE_VER = R146 恰 1 次', s2.count("GATE_VER = 'R146'") == 1, s2.count("GATE_VER = 'R146'"))
s3 = s2.replace("GATE_VER = 'R146'", "GATE_VER = 'R147'", 1)
ck('GATE_VER = R147 恰 1 次', s3.count("GATE_VER = 'R147'") == 1, s3.count("GATE_VER = 'R147'"))

# ---- 5 备份 + 写 ----
src = open(GATE, 'rb').read()
dst = os.path.join(BL, 'check_disc.py.before_r147_gate_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
with io.open(dst, 'xb') as f:
    f.write(src)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))
with io.open(GATE, 'w', encoding='utf-8', newline='') as f:
    f.write(s3)
s4 = read(GATE)
ck('回读 逐字节相同', s4 == s3)
ck('回读 表项数 146', len(tbl2) == 146, len(tbl2))
ck('回读 sha 自洽', hashlib.sha256(norm2.encode()).hexdigest()
   == re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", s4).group(1))

out = {'fails': FAILS, 'size152': size152, 'floor152': floor152, 'indep_size152': indep,
       'old_pin': old_pin, 'new_pin': new_pin, 'table_entries': len(tbl2)}
json.dump(out, open(HERE + '/_r147/r147m_gate.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))

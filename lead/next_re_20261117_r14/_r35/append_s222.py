# -*- coding: utf-8 -*-
"""把 §2.22 追加到 R14_COMMON.md。
写入纪律：wx 独占创建且文件名唯一 → 断言旧文件前缀 sha256 → 一次性写入 → 回读校验。
CR 不变量：R14_COMMON 的 CRLF 计数必须保持 1081（新增内容必须全 LF）。
"""
import io, os, shutil, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TGT  = os.path.join(R14, 'R14_COMMON.md')
SEC  = os.path.join(R14, '_r35', 's222.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')

def stat(p):
    t = io.open(p, encoding='utf-8', newline='').read()
    return t, t.count('\r\n'), t.count('\n'), os.path.getsize(p)

before, crlf0, lf0, bytes0 = stat(TGT)
sha0 = hashlib.sha256(io.open(TGT, 'rb').read()).hexdigest().upper()
print('BEFORE bytes=%d CRLF=%d LF=%d sha=%s' % (bytes0, crlf0, lf0, sha0))
assert crlf0 == 1081, crlf0

# 1) 备份：wx 独占 + 唯一文件名
ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'R14_COMMON.before_AZ12_%s.md' % ts)
with open(bk, 'xb') as f:              # x = 独占创建，已存在即抛错
    f.write(io.open(TGT, 'rb').read())
# 2) 断言备份与原文件 sha 一致
sha_bk = hashlib.sha256(io.open(bk, 'rb').read()).hexdigest().upper()
assert sha_bk == sha0, (sha_bk, sha0)
print('BACKUP ok', os.path.basename(bk), os.path.getsize(bk))

# 3) 拼装：原文件末尾若无换行先补一个；新增段必须全 LF
sec = io.open(SEC, encoding='utf-8', newline='').read()
assert '\r' not in sec, 'section has CR'
assert crlf0 == before.count('\r\n')
sep = '' if before.endswith('\n') else '\n'
new = before + sep + '\n' + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == crlf0, (new.count('\r\n'), crlf0)   # CR 不变量

# 4) 一次性写入（覆盖）
with open(TGT, 'wb') as f:
    f.write(new.encode('utf-8'))

# 5) 回读校验
back, crlf1, lf1, bytes1 = stat(TGT)
assert back == new, 'readback mismatch'
assert crlf1 == 1081, crlf1
assert back.startswith(before[:2000]), 'prefix changed'
sha1 = hashlib.sha256(io.open(TGT, 'rb').read()).hexdigest().upper()
print('AFTER  bytes=%d CRLF=%d LF=%d sha=%s' % (bytes1, crlf1, lf1, sha1))
print('delta bytes = +%d' % (bytes1 - bytes0))
print('prefix sha (before[0:2000]) preserved = True')

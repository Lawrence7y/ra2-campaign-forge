import io, os, shutil, datetime
LL = r'D:\Project\ra2-campaign-forge\lead\LEAD_LOCK'
BK = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEAD_BASELINE'
t = io.open(LL, encoding='utf-8', newline='').read()
old = '台账 4,600,xxx B / max §1106'
assert old in t, 'placeholder not found'
new = '台账 4,599,943 B / max §1106'
n = t.replace(old, new, 1)
assert n != t
assert n.count('\r\n') == 137
ts = datetime.datetime.now().strftime('%H%M%S')
open(os.path.join(BK, 'LEAD_LOCK.before_fix54_%s' % ts), 'xb').write(io.open(LL, 'rb').read())
io.open(LL, 'w', encoding='utf-8', newline='').write(n)
back = io.open(LL, encoding='utf-8', newline='').read()
assert back == n and back.count('\r\n') == 137
print('fixed: 4,600,xxx -> 4,599,943 ; CRLF=137 kept ; bytes=%d' % os.path.getsize(LL))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dedup_r116.py —— 自错 S-32：修复脚本重跑导致 LEAD_LOCK 的 ER9b 被插入**两次**。

起因：fix_r116_count.py 第一次跑成功写入四件套；我改完 W4 断言后又跑了一次，
而该脚本的替换锚 `ER10. **方法论...**` 在第一次插入后**仍然存在**（ER9b 是新加在它前面的），
于是第二次又插了一遍 ⇒ LEAD_LOCK 里 ER9b 出现 2 次。
这正是「替换脚本必须幂等或必须做前置检查」的教训：我改脚本时只关注了断言的正确性，
没检查「重跑会不会重复施加副作用」。

本脚本：只删掉重复的那一份（保留唯一一份），断言删前 count==2、删后 count==1、
ER10 仍为 1、CR 仍为 137、字节减少量 == 被删段长度。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
LCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


stamp = time.strftime('%Y%m%d_%H%M%S')
data = open(LCK, 'rb').read()
cr0 = data.count(b'\r')
ck('D1 LEAD_LOCK 旧 CR==137', cr0 == 137, cr0)

txt = data.decode('utf-8')
ck('D2 ER9b 确实重复（count==2）', txt.count('ER9b.') == 2, txt.count('ER9b.'))
ck('D3 ER10 只有 1 个', txt.count('ER10.') == 1, txt.count('ER10.'))

# 重复段落的两份内容完全相同（同一 new 串被插两次）⇒ 删掉前一份即可。
# 用「第一份 ER9b 起点 -> 第二份 ER9b 起点」的区间作为待删段。
i1 = txt.find('ER9b.')
i2 = txt.find('ER9b.', i1 + 1)
dup = txt[i1:i2]
ck('D4 待删段 = 第一份 ER9b（%d 字符），以两条 LF 结尾且下一段紧接第二份 ER9b'
   % len(dup), dup.endswith('\n\n') and txt[i2:i2 + 6] == 'ER9b.',
   {'len': len(dup), 'tail': repr(dup[-6:])})

bak = os.path.join(BASE, 'LEAD_LOCK.before_R116_dedup_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
with os.fdopen(fd, 'wb') as f:
    f.write(data)
ck('D5 备份独占创建且字节一致', hashlib.sha256(open(bak, 'rb').read()).hexdigest()
   == hashlib.sha256(data).hexdigest(), os.path.basename(bak))

new_txt = txt[:i1] + txt[i2:]
open(LCK, 'wb').write(new_txt.encode('utf-8'))
back = open(LCK, 'rb').read()
bt = back.decode('utf-8')
ck('D6 回读逐字节 == 删除结果', bt == new_txt, {'old': len(data), 'new': len(back)})
ck('D7 删除后 ER9b == 1', bt.count('ER9b.') == 1, bt.count('ER9b.'))
ck('D8 删除后 ER10 == 1', bt.count('ER10.') == 1, bt.count('ER10.'))
ck('D9 CR 仍为 137', back.count(b'\r') == 137, back.count(b'\r'))
ck('D10 字节减少量 == 待删段字节数（%d）' % len(dup.encode('utf-8')),
   len(data) - len(back) == len(dup.encode('utf-8')), len(data) - len(back))
ck('D11 正确计数 76 仍在 2 处以上（ER9b + 自错登记）',
   bt.count('76') >= 2, bt.count('76'))

json.dump({'checks': checks}, open(os.path.join(ROOT, '_r116/dedup_r116.json'), 'w'),
          indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- dedup_r116: %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)

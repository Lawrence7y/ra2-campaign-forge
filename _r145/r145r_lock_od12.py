#!/usr/bin/env python3
"""R145 R：给 LEAD_LOCK 的 OD 段补 OD12 —— 如实登记 S-321（看板超行）与一处**未查明**的观测矛盾。"""
import io, json, os, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
LK = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

ADD = """
OD12. 🔴 **自错 S-321（看板超行）与一处未查明的观测矛盾。** **S-321**：`r145p` 把第 145 轮段写成 99 行，看板从 **216 → 315 行**，超 300 上限（写前 216 < 260，归档规则**未触发**，所以正确处置不是归档而是压段落）。`r145q` 用 `r145p` 的 `.bak` 回滚、断言回滚后逐字节相同，再写**紧凑版 77 行** ⇒ 终态 **293 行**，并已把这个过错本身写进看板第九节（不留暗账）。**未查明的观测矛盾（不粉饰）**：`r145q` 的第一条断言 `Q0b`（「当前看板以备份为前缀且多出 99 行」）**FAIL 且实测差值为 0**，即 `r145q` 读到的看板是 **216 行**；但 `r145p` 自己的 JSON 记录 `lines_after = 315`，且 `r145p` 与 `r145q` 之间我只跑过一条 `analyze` 命令、没有任何写操作。**根因未查明**，我不做解释性归因（既不假设「写没落盘」也不假设「被别的进程回滚」）。**风险已用独立路径封住**：终态由 `r145q` 的 Q1（回滚后逐字节 == 备份）、Q4（CR 仍 0）、Q5（<= 300 行）、Q6（以回滚内容为前缀）、Q7（含第 145 轮段）五条分别断言，不依赖 Q0b；`r145t` 再从磁盘独立核一遍。**教训**：断言「状态 A 变成状态 B」之前，先在同一进程里把 A 读回来验证 —— 我只用 JSON 记忆代替了现场读回。
"""
b = ADD.encode('utf-8')
ck('追加段不含 CR', b'\r' not in b)
old = open(LK, 'rb').read()
ck('LK CR == 137', old.count(b'\r') == 137, old.count(b'\r'))
ck('LK 尾部是换行', old.endswith(b'\n'))
ck('LK 里尚无 OD12', b'OD12.' not in old)
ck('LK 末段是 OD', old.rstrip().split(b'\n')[-1][:2] == b'OD' or b'OD11.' in old[-4000:], 'ok')
dst = os.path.join(BL, 'LEAD_LOCK.before_r145_od12_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(old)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == old, os.path.basename(dst))
open(LK, 'wb').write(old + b)
new = open(LK, 'rb').read()
ck('LK 写后 CR 仍 137', new.count(b'\r') == 137, new.count(b'\r'))
ck('LK 写后以原文件为前缀', new[:len(old)] == old)
ck('LK 写后 OD12 在场', b'OD12.' in new)
json.dump({'fails': cc}, io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145r_lock_od12.json', 'w'), indent=1)
print('\n=== OD12：FAIL %d ===' % len(cc))

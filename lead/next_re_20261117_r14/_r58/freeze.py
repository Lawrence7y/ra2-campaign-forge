import io, os, csv, datetime, hashlib

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
T = os.path.join(R14, 'DISC_RECHECK.tsv')
FREEZE = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')

raw = [l for l in io.open(T, encoding='utf-8', newline='').read().split('\n') if l]
hdr, body = raw[0], [r.split('\t') for r in raw[1:]]

# 冻结时刻 = 现在
now = datetime.datetime.now().astimezone().isoformat(timespec='seconds')

# 结构性不可验证 = 声称「有」但没有合规自述行 的那 12 条
# 用 check_disc 的 C11 判定结果确定（此处按已知：有==17 行，可核 5 行 3/4/22/27/28）
LANDABLE = {3, 4, 22, 27, 28}
rows_out = []
for r in body:
    n = int(r[0])
    if not r[6].strip().startswith('有'):
        continue
    if n in LANDABLE:
        continue
    # 该类：产物形态结构上不可能自产出凭证
    prod = r[4].strip()
    expr = r[5].strip().split(' ')[0]
    rows_out.append([str(n), '§' + r[1].lstrip('§'), prod, expr,
                     'structurally_unverifiable',
                     '产物为叙述/他人报告/手编一次性/底座自指，无法自产出 DISC_RECHECK 行'])

HDR = ['纪律号', '节', '产物路径', '校验式', '不可验证类别', '理由', '冻结时刻', '冻结时是否已声称有']
out = []
for r in rows_out:
    out.append(r + [now, 'YES'])

assert not os.path.exists(FREEZE), 'freeze registry already exists — refusing to overwrite'
with open(FREEZE, 'x', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in out:
        w.writerow(r)

back = io.open(FREEZE, encoding='utf-8', newline='').read()
assert '\r' not in back
bl = [l for l in back.split('\n') if l]
assert len(bl) - 1 == len(out)
for l in bl:
    assert l.count('\t') == len(HDR) - 1, l.count('\t')

print('froze %d disciplines as structurally unverifiable at %s' % (len(out), now))
print('ids:', [r[0] for r in out])
print('wrote', FREEZE, os.path.getsize(FREEZE), 'B ; sha256 =',
      hashlib.sha256(back.encode()).hexdigest()[:16])

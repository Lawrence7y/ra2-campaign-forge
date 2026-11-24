# -*- coding: utf-8 -*-
# _s604_fp_check.py —— S604 交付件撰写员自跑指纹核验（只读；hashlib 实算）
# 用途：
#   (1) 绑定复算/复核两轮全部关键件 SHA256+字节数；
#   (2) 比对重跑 _r3_recompute_gapdiff.py 后的 _r3_recompute_out.txt 与登记件（备份件）是否逐字节一致（确定性检查）；
#   (3) 核对 15 份语料 measure_w*.json 的 SHA256/bytes 与复算输出 [A] 节登记值；
#   (4) 记录台账/被核对象 mtime（未改台账佐证）。
import hashlib, os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = 'D:/Project/ra2-campaign-forge'
R3 = BASE + '/lead/slowframe_r3_20261108'
N8DIR = BASE + '/lead/slowwindow_n8_20261108'
CORPUS = BASE + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

REGISTERED_OUT = 'f1f55791f14bb13669d2fde062a1d85ffaab3c05d7379c59573692c5cb88e54b'

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def line(p):
    b = os.path.getsize(p)
    import datetime
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')
    print(f'{p}\n  SHA256 = {sha256_file(p)}  bytes = {b}  mtime = {mt}')

print('== [1] 关键件指纹 ==')
for p in [
    BASE + '/lead/GOAL_THREE_TARGETS_20261018.md',
    N8DIR + '/SLOW_WINDOW_LIMITS.md',
    R3 + '/_r3_recompute_gapdiff.py',
    R3 + '/_r3_recompute_out.txt',
    R3 + '/_r3_GAPDIFF_RECHECK.md',
    R3 + '/_verify_r3_gapdiff.py',
    R3 + '/_verify_r3_out.txt',
]:
    line(p)

print('== [2] 重跑确定性比对 ==')
cur = sha256_file(R3 + '/_r3_recompute_out.txt')
bak = R3 + '/_s604_fp_backup_out.txt'
if os.path.exists(bak):
    b = sha256_file(bak)
    print('重跑后 out.txt SHA256 =', cur)
    print('重跑前备份   SHA256 =', bak, b)
    print('逐字节一致（重跑前后）:', cur == b)
    print('与复核登记值 f1f55791...e54b 一致:', cur == REGISTERED_OUT)
else:
    print('备份不存在（未做重跑比对）')
    print('与复核登记值一致:', cur == REGISTERED_OUT)

print('== [3] 15 份语料 measure_w*.json 指纹（对照 _r3_recompute_out.txt [A]）==')
TRIPS = ['l1c_20261021', 'l1d_20261021', 'l1e_20261021', 'l3_20261021', 't55k_20261020']
for t in TRIPS:
    for w in (0, 1, 2):
        p = f'{CORPUS}/{t}/measure_w{w}.json'
        if os.path.exists(p):
            print(f'{t}/w{w}  sha256={sha256_file(p)}  bytes={os.path.getsize(p)}')
        else:
            print(f'{t}/w{w}  MISSING: {p}')
print('== END ==')

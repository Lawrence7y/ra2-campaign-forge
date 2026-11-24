# -*- coding: utf-8 -*-
# _w2_seal_report.py —— 按 R3-1 两阶段算法回填本报告自绑定行，并做门禁视角独立校验。
# 运行： python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_template_20261108/_w2_seal_report.py
import hashlib, re, shutil, sys
from pathlib import Path

WD = Path('D:/Project/ra2-campaign-forge/lead/gate_template_20261108')
DOC = WD / 'GATE_FALSE_POSITIVES.md'
BAK = WD / '_w2_report_preseal.md'

RE_LINE = re.compile(r'本件扣行 SHA256 = ([0-9a-fA-F]{64})，本件字节数 = (\d+)')
RE_NUM = re.compile(r'(本件扣行 SHA256 = [0-9a-fA-F]{64}，本件字节数 = )(\d+)')
RE_HASH = re.compile(r'(本件扣行 SHA256 = )([0-9a-fA-F]{64})')

shutil.copyfile(BAK, DOC)   # 从封印前备份恢复，保证幂等
raw = DOC.read_bytes()
assert b'\r\n' not in raw, 'preseal file must be LF-only'
text = raw.decode('utf-8')
ms = RE_LINE.findall(text)
assert len(ms) == 1, f'self-binding line occurrences = {len(ms)}, expect 1'

def with_num(t: str, n_str: str) -> str:
    return RE_NUM.sub(lambda m: m.group(1) + n_str, t, count=1)

def with_hash(t: str, h: str) -> str:
    return RE_HASH.sub(lambda m: m.group(1) + h, t, count=1)

# 阶段一：字节不动点（哈希字段保持 64 个 '0' 占位）
zero64 = '0' * 64
assert ms[0][0] == zero64 and ms[0][1] == '0', 'placeholder expected (64 zeros / 0)'
n = len(with_num(text, '0').encode('utf-8'))
iters = 0
for i in range(12):
    iters = i + 1
    m = len(with_num(text, str(n)).encode('utf-8'))
    if m == n:
        break
    n = m
N = n
t_num = with_num(text, str(N))
assert len(t_num.encode('utf-8')) == N, 'fixed point check failed'

# 阶段二：扣零哈希（哈希字段为 64 个 '0' 时对全件计算）
H = hashlib.sha256(t_num.encode('utf-8')).hexdigest()
final_bytes = with_hash(t_num, H).encode('utf-8')
DOC.write_bytes(final_bytes)   # 二进制写，杜绝 \n→\r\n 翻译破坏不动点

# 门禁视角独立校验（从磁盘重读字节）
disk_b = DOC.read_bytes()
disk = disk_b.decode('utf-8')
m2 = RE_LINE.search(disk)
decl_h, decl_n = m2.group(1), m2.group(2)
zeroed = RE_HASH.sub(lambda m: m.group(1) + zero64, disk, count=1)
recomputed = hashlib.sha256(zeroed.encode('utf-8')).hexdigest()
ok_hash = recomputed == decl_h
ok_len = len(disk_b) == int(decl_n)
ok_single = disk.count(decl_h) == 1
print(f'stage_A_iters = {iters}')
print(f'declared_bytes = {decl_n}  actual_bytes = {len(disk_b)}  byte_match = {ok_len}')
print(f'declared_sha(扣行) = {decl_h}')
print(f'recomputed_sha(置零重算) = {recomputed}  hash_match = {ok_hash}')
print(f'hash_field_single_occurrence = {ok_single}')
print(f'SEAL_RESULT = {"PASS" if (ok_hash and ok_len and ok_single) else "FAIL"}')
sys.exit(0 if (ok_hash and ok_len and ok_single) else 2)

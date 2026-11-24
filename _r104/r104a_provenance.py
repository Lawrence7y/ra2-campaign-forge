#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r104a_provenance.py —— R104 第三套反汇编器的来源与可信度（先证工具，再证结论）

本轮引入 iced-x86 1.22.0 作为第三套反汇编器。纪律要求：**先钉工具**，否则
「两个数都对、被测对象不同」这类混淆会重演（R102 ED7 / R103 EE11 的教训）。

本脚本只做四件事，不做任何逆向结论：
  A. 钉 exe 与 R101 所用 objdump 文本的 sha256，并证明 dump 可由本机工具**逐字节重生成**
     （/tmp/r93_disasm.txt 是易失路径；若重生成 sha 不一致，则 R99..R103 所有 objdump 侧
      数字都失去可复现性——这是一条必须先关掉的前提）
  B. 钉 iced-x86 版本与 wheel 的 sha256（离线 vendored 于 _r104/vendor/，不依赖网络）
  C. iced 线性铺满 .text：+ 正控（sum(len)==VirtualSize 且无缝隙）+ 反控两条
  D. capstone 线性铺满：同样给正控与「拒解即 1 字节重同步」口径的实测

反控设计（每条都必须能 FAIL）：
  NC1 把 .text 尾字节切掉 1 ⇒ iced sum(len) 必须比 VirtualSize 少，正值控给恰等
  NC2 以 DecoderOptions.NO_INVALID_CHECK 解码 ⇒ invalid 计数必须变 0（证明 is_invalid 不是空判据）
  NC3 capstone 侧把 skipdata 打开 ⇒ 65 条拒解必须变成 1 字节 .byte，长度和变 65
"""
import array, hashlib, io, json, os, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r104/r104a_provenance.json'
DUMP = '/tmp/r93_disasm.txt'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
DUMP_SHA = '5935356b2914d90baeaeb0d8ea5198961976118526b37d341ab72f06d4046c70'
SHIM = 'i686-w64-mingw32-objdump'
VENDOR = '_r104/vendor'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)
R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:700]), flush=True)

# ---------------- A 来源与可复现性
raw = open(EXE, 'rb').read()
sha_exe = hashlib.sha256(raw).hexdigest()
ck('A1 exe sha256 == 登记值', sha_exe == EXE_SHA, sha_exe[:16])
sha_dump = hashlib.sha256(open(DUMP, 'rb').read()).hexdigest()
ck('A2 R101 所用的 objdump 文本 sha256 == 登记值', sha_dump == DUMP_SHA, sha_dump[:16])
put('A_sha', {'exe': sha_exe, 'dump': sha_dump})

# 用本机 shim 重生成，逐字节比对（R99..R103 全部 objdump 侧数字的可复现性前提）
gen = '/tmp/r104_regenerate.txt'
rc = subprocess.call([SHIM, '-d', '-M', 'intel', EXE], stdout=open(gen, 'wb'),
                     stderr=subprocess.DEVNULL, timeout=900)
sha_gen = hashlib.sha256(open(gen, 'rb').read()).hexdigest()
ck('A3 ABI：本机 objdump 重生成与 R101 使用的文本逐字节相同（可复现性前提）',
   rc == 0 and sha_gen == DUMP_SHA, '%s %s' % (rc, sha_gen[:16]))
put('A_regen', {'rc': rc, 'sha': sha_gen, 'bytes': os.path.getsize(gen),
                'lines': sum(1 for _ in io.open(gen, encoding='utf-8', errors='replace'))})
# 这是本轮第一条「被证成」的前提：不打 -M intel 会得到 AT&T 语法，sha 必然不同
rc2 = subprocess.call([SHIM, '-d', EXE], stdout=open('/tmp/r104_regen_att.txt', 'wb'),
                      stderr=subprocess.DEVNULL, timeout=900)
sha_att = hashlib.sha256(open('/tmp/r104_regen_att.txt', 'rb').read()).hexdigest()
ck('A4 反控：去掉 -M intel（AT&T 语法）后 sha 必须不同（证明 A3 不是恒真断言）',
   sha_att != DUMP_SHA, sha_att[:16])

# ---------------- B 第三套解码器
sys.path.insert(0, os.path.join(ROOT, VENDOR))
import iced_x86
wheel = os.path.join(VENDOR, '..', 'iced_x86-1.22.0.dist-info')
hit = []
for d in ('/tmp/r104venv/lib/python3.13/site-packages', os.path.join(ROOT, '_r104')):
    if not os.path.isdir(d):
        continue
    for e in os.listdir(d):
        if e.startswith('iced_x86-1.22.0.dist-info'):
            m = os.path.join(d, e, 'RECORD')
            if os.path.exists(m):
                hit.append((m, hashlib.sha256(open(m, 'rb').read()).hexdigest()))
put('B_iced', {'module_file': iced_x86.__file__, 'distinfo_record': hit[:1]})
ck('B1 iced 从 vendored 目录加载（不依赖 /tmp 或网络）',
   os.path.abspath(iced_x86.__file__).startswith(os.path.join(ROOT, '_r104', 'vendor')))
ck('B2 vendored 目录体积 < 8 MiB（不与 t628 内存/磁盘争抢）',
   int(subprocess.check_output(['du', '-sk', '_r104/vendor']).split()[0]) < 8192,
   subprocess.check_output(['du', '-sh', '_r104/vendor']).decode().split()[0])

# ---------------- C 段表
import struct
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
sh = opt + osz
SECS = []
for i in range(nsec):
    o = sh + 40 * i
    nm = raw[o:o + 8].rstrip(b'\0').decode('ascii', 'replace')
    vs, va, rsz, roff = struct.unpack_from('<IIII', raw, o + 8)
    SECS.append({'name': nm, 'va': IB + va, 'vsize': vs, 'vsz_raw': rsz, 'roff': roff})
put('C_sections', SECS)
T = [s for s in SECS if s['name'] == '.text'][0]
B, TVS = T['va'], T['vsize']
txt = raw[T['roff']:T['roff'] + TVS]
ck('C1 .text 段起点/长度与 R99..R103 一致', (B, TVS) == (0x401000, 4060045), '%x %d' % (B, TVS))

# ---------------- C iced 铺满（正控）
def iced_sweep(buf, base, opts=0, cap=None):
    dec = iced_x86.Decoder(32, buf, ip=base, options=opts)
    va = array.array('I'); bad = array.array('I'); lens = array.array('H')
    tot = 0; n = 0
    while dec.can_decode:
        i = dec.decode()
        n += 1
        if i.is_invalid:
            bad.append(i.ip)
        else:
            va.append(i.ip)
        lens.append(i.len); tot += i.len
        if cap and n >= cap:
            break
    return va, bad, lens, tot, n

va, bad, lens, tot, n = iced_sweep(txt, B)
ck('C2 正控：iced 线性铺满 .text（sum(len) == VirtualSize，无缝隙无重叠）',
   tot == TVS, '%d vs %d' % (tot, TVS))
ck('C3 iced 单元总数与 capstone 单元总数不同（两实现确实不同，不是同一份结果）',
   n != 1392527, 'iced=%d capstone=1392527' % n)
put('C_iced', {'units': n, 'valid_starts': len(va), 'invalid': len(bad),
               'sum_len': tot, 'vsize': TVS})
put('C_iced_invalid_len_hist', {int(k): int(v) for k, v in
    sorted(__import__('collections').Counter(lens[i] for i, ip in enumerate([]) ).items())})
# invalid 单元长度分布（单列，供后轮核对）
inv_lens = []
dec = iced_x86.Decoder(32, txt, ip=B)
while dec.can_decode:
    i = dec.decode()
    if i.is_invalid:
        inv_lens.append(i.len)
import collections
put('C_iced_invalid_len_hist', {int(k): int(v) for k, v in sorted(collections.Counter(inv_lens).items())})

# NC1：切掉尾字节 ⇒ sum(len) 必须少
va2, bad2, lens2, tot2, n2 = iced_sweep(txt[:-1], B)
ck('NC1 反控：.text 去尾 1 字节后 iced sum(len) 必须 != VirtualSize（正控因此不是恒真）',
   tot2 != TVS, '%d vs %d' % (tot2, TVS))
# NC2（修：原版断言「invalid 必须变 0」是错的 —— 我先前把 DecoderOptions 的语义想当然了）
# 实测：NO_INVALID_CHECK 只把 66 个 invalid 里的 13 个变成可解，仍剩 53 个
# （这些是 opcode 表里根本不存在的编码，绕过检查也没法给出合法指令）。
# 正确的反控是「invalid 集合必须**改变**，且是严格子集」，这才证明 is_invalid 不是恒真常量。
va3, bad3, lens3, tot3, n3 = iced_sweep(txt, B, opts=iced_x86.DecoderOptions.NO_INVALID_CHECK)
_s1, _s3 = set(bad), set(bad3)
ck('NC2 反控：NO_INVALID_CHECK 下 invalid 集合严格缩小（66 -> 53），且仍是子集'
   '（证明 is_invalid 会随解码选项变化，不是恒真）',
   len(bad3) < len(bad) and _s3 < _s1 and tot3 == TVS,
   'default=%d opt=%d subset=%s sum=%d' % (len(bad), len(bad3), _s3 < _s1, tot3))
put('NC2_detail', {'default_invalid': len(bad), 'no_invalid_check_invalid': len(bad3),
                   'became_valid': sorted(hex(x) for x in _s1 - _s3),
                   'note': '这 13 个是「仅因保留位/非法组合被拒」的编码，绕过检查后可解；'
                           '其余 53 个是 opcode 表里不存在的编码，绕过检查仍不可解。'})

va.tofile(open('_r104/iced_valid.bin', 'wb'))
bad.tofile(open('_r104/iced_invalid.bin', 'wb'))
json.dump({'base': B, 'vsize': TVS, 'iced_units': n, 'iced_valid': len(va), 'iced_invalid': len(bad)},
          open('_r104/start_sets_iced.json', 'w'))

# ---------------- D capstone 铺满（同口径）
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = False
mdskip = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); mdskip.detail = False
mdskip.skipdata = True
cv = array.array('I'); cb = array.array('I'); cl = array.array('H')
off = 0; cs_tot = 0
while off < TVS:
    ins = next(md.disasm(txt[off:off + 16], B + off), None)
    if ins is None:
        cb.append(B + off); cl.append(1); cs_tot += 1; off += 1
    else:
        cv.append(B + off); cl.append(ins.size); cs_tot += ins.size; off += ins.size
ck('D1 capstone「拒解即 1 字节重同步」口径下 sum(len) == VirtualSize',
   cs_tot == TVS, '%d vs %d' % (cs_tot, TVS))
ck('D2 capstone 拒解数 == 65（与 R99/R100 登记值一致）', len(cb) == 65, len(cb))
put('D_capstone', {'valid_starts': len(cv), 'bad': len(cb), 'units': len(cv) + len(cb), 'sum_len': cs_tot})
# NC3（修：原版断言写错了两处）
# 错处一：skipdata 打开后**整个 .text 仍然铺满**（sum(len)==TVS），不是「长度和 == 65」。
# 错处二：「拒解变成 1 字节 .byte」是对的，但要看的是**那 65 个地址处产出的单元数**，
#         不是全段长度和。修法：全段铺满 + 那 65 个位置各有恰好一条 .byte。
sk_tot = 0; sk_n = 0; dot = []
off = 0
while off < TVS:
    ins = next(mdskip.disasm(txt[off:off + 16], B + off), None)
    if ins is None:
        break
    if ins.mnemonic == '.byte' and ins.size == 1:
        dot.append(ins.address)
    sk_tot += ins.size; sk_n += 1; off += ins.size
ck('NC3 反控：skipdata 打开后全段仍铺满（sum==VirtualSize），且恰有 65 个 1 字节 .byte 单元',
   sk_tot == TVS and len(dot) == 65, 'sum=%d .byte=%d units=%d' % (sk_tot, len(dot), sk_n))
ck('NC3b 这 65 个 .byte 的地址集合 == capstone 的拒解地址集合（逐址相等，不是只数相等）',
   set(dot) == set(cb), len(set(dot) ^ set(cb)))
cv.tofile(open('_r104/capstone_valid.bin', 'wb'))
cb.tofile(open('_r104/capstone_bad.bin', 'wb'))

# E 两套起点集的整体关系（只报数，结论留给 r104b）
sv, sb, scv, scb = set(va), set(bad), set(cv), set(cb)
put('E_set_relation', {'iced_valid': len(sv), 'cap_valid': len(scv),
                       'both': len(sv & scv), 'iced_only': len(sv - scv), 'cap_only': len(scv - sv),
                       'iced_invalid_not_cap_bad': sorted(hex(x) for x in sb - scb),
                       'cap_bad_not_iced_invalid': sorted(hex(x) for x in scb - sb)})
ck('E1 两个「拒解集」不相等（必须分开数，R100 教训：65 与 65 不是同一集合）',
   sb != scb, 'iced_invalid=%d cap_bad=%d inters=%d' % (len(sb), len(scb), len(sb & scb)))

for c in checks:
    if not c['ok']:
        print('FAILED:', c['name'])
json.dump({'checks': checks, 'R': R}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n_fail = sum(1 for c in checks if not c['ok'])
print('SUMMARY: %d checks, %d FAIL -> %s' % (len(checks), n_fail, OUT))
sys.exit(1 if n_fail else 0)

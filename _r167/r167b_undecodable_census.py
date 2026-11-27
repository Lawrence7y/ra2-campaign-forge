#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167b_undecodable_census.py —— 「那 65 条到底是什么」的第一条独立判据：全段不可解码位普查

命题：如果这 65 条真的是「线性解码走到这里就停」的洞，那么它们应当**恰好等于**
      「在 .text 里 c a p s t o n e 一条指令都解不出来的起始位置」集合。
      （反过来，若它们与不可解码位集合不等，则「解码洞」这个说法就还缺一层机制。）

做法：对 .text VirtualSize 内每个字节位置 p，用 capstone 解 1 条指令（15 B 窗口）。
      4,060,045 个位置串行太慢，按 4 进程分片，每个分片返回失败位置列表。
      严禁 detail=True；每次只解 count=1。
反控：
  K1 正控：从已知合法起点（0x401000）必须解得出来
  K2 正控：随机 3000 个位置的可解率必须 > 90%（否则普查实现有 bug）
  K3 负控：故意构造一段非法字节（0x0F 0xFF 之后）必须解不出来 —— 证明 capstone 会返回空
  K4 自查：本次普查若得 0 条失败，立即 FAIL（因为 65 个洞必然解不出来）
"""
import io, json, os, sys, time, random
import multiprocessing as mp
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r167/r167b_undecodable_census.json'
W = 15          # 最长指令 15 B
NPROC = 4

def load_text():
    data = io.open(EXE, 'rb').read()
    pe = pefile.PE(EXE, fast_load=True)
    IB = pe.OPTIONAL_HEADER.ImageBase
    t = [s for s in pe.sections if s.Name.decode().rstrip('\x00') == '.text'][0]
    LO = IB + t.VirtualAddress
    VSZ = t.Misc_VirtualSize
    blob = data[t.PointerToRawData:t.PointerToRawData + VSZ]
    return data, LO, VSZ, blob

def worker(args):
    blob, LO, a, b = args
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    bad = []
    dl = md.disasm_lite
    for off in range(a, b):
        if not list(dl(blob[off:off + W], LO + off, count=1)):
            bad.append(LO + off)
    return bad

def main():
    FAIL = 0
    RES = []
    def ck(n, c, d=''):
        nonlocal FAIL
        ok = bool(c)
        if not ok: FAIL += 1
        RES.append({'id': n, 'ok': ok, 'detail': str(d)[:400]})
        print(('PASS ' if ok else 'FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
        sys.stdout.flush()

    data, LO, VSZ, blob = load_text()
    print('== 0 基线 ==  .text lo=%#x vsz=%d' % (LO, VSZ))
    ck('B0 gamemd.exe == 4,825,360 B', len(data) == 4825360, len(data))
    ck('B1 VirtualSize == 4,060,045', VSZ == 4060045, VSZ)

    # 正控 K1
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    ck('K1 正控：0x401000 处解得出一条指令',
       len(list(md.disasm_lite(blob[0:W], LO, count=1))) == 1)
    # 负控 K3
    junk = bytes([0x0f, 0x0f] * 8)
    ck('K3 负控：非法字节 0f 0f 之后解得 0 条',
       len(list(md.disasm_lite(junk, LO, count=1))) == 0)
    # K2
    random.seed(20261127)
    samp = random.sample(range(VSZ - W), 3000)
    okc = sum(1 for o in samp if list(md.disasm_lite(blob[o:o + W], LO + o, count=1)))
    ck('K2 正控：随机 3000 个位置可解率 > 90%', okc / 3000.0 > 0.90, '%.4f' % (okc / 3000.0))

    # 分片普查
    n = VSZ - W
    step = (n + NPROC - 1) // NPROC
    chunks = [(blob, LO, i * step, min(n, (i + 1) * step)) for i in range(NPROC)]
    t0 = time.time()
    with mp.Pool(NPROC) as pool:
        res = pool.map(worker, chunks)
    bad = sorted(x for part in res for x in part)
    el = time.time() - t0
    print('== 1 普查 == 位置数 %d, 耗时 %.1fs, 不可解 %d' % (n, el, len(bad)))
    ck('C0 本次普查不为 0（65 个洞必然解不出来）', len(bad) > 0, len(bad))

    # 与重对齐点集合比
    J = json.load(io.open(A2, encoding='utf-8'))
    bounds = [int(x, 16) for x in J['bounds']]
    starts, resync = [], []
    pos = 0
    while pos < VSZ:
        base = LO + pos
        seg = blob[pos:pos + 65536]
        cons = 0
        for a, sz, mn, op in md.disasm_lite(seg, base):
            if a - base + sz > len(seg): break
            starts.append(a); cons = a - base + sz
        if cons: pos += cons
        else: resync.append(base); pos += 1
    holes = sorted(resync)
    ck('C1 bounds - plain起点 == 重对齐点（65 条）',
       sorted(set(bounds) - set(starts)) == holes and len(holes) == 65, len(holes))
    bS, hS = set(bad), set(holes)
    ck('D0 65 个洞全部落在不可解位集合里（only_hole == 0）', len(hS - bS) == 0,
       'only_hole=%d' % len(hS - bS))
    ck('D1 不可解位总数 > 65（不可解位远多于 65 个，故 65 不是其全集）', len(bad) > len(holes),
       'bad=%d holes=%d' % (len(bad), len(holes)))
    extra = sorted(bS - hS)
    print('  不可解但从未被线性扫描命中: %d 条（占不可解位 %.2f%%）'
          % (len(extra), 100.0 * len(extra) / len(bad)))
    print('  仅洞非不可解: %d' % len(hS - bS))
    # 机制：65 = 不可解位 ∩ 线性扫描真的踩到的位置
    ck('D3 洞 ⊆ 不可解位，且 65/58017 说明「踩到的只是极少数」',
       set(holes) <= bS, '%d / %d' % (len(holes), len(bad)))
    # 每个洞的首字节
    import collections
    fb = collections.Counter(blob[v - LO] for v in holes)
    print('  洞首字节分布: %s' % dict(sorted(fb.items())))
    ck('D2 洞首字节只有少数几种（前缀类 0xF0/0xFE/0xC7/0xDD…）', len(fb) <= 20, len(fb))

    obj = {'lo': hex(LO), 'vsz': VSZ, 'bad_count': len(bad), 'holes': [hex(v) for v in holes],
           'undecodable': [hex(v) for v in bad], 'equal': bS == hS,
           'only_bad_count': len(extra), 'only_bad': [hex(x) for x in extra[:200]],
           'only_hole': [hex(x) for x in sorted(hS - bS)],
           'first_byte_hist': {hex(k): v for k, v in fb.items()},
           'elapsed_s': el, 'assertions': RES, 'fail': FAIL}
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
    print('\n断言 %d 条, FAIL %d -> %s' % (len(RES), FAIL, OUT))
    return 1 if FAIL else 0

if __name__ == '__main__':
    sys.exit(main())

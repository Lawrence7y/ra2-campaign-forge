"""三个只读事实块：
 A. PE 里有没有任何栈展开元数据（FPO/.pdata/异常目录/调试目录内容）；
 B. .text 里函数的帧指针（EBP 链）比例 —— StackWalk 在无 FPO 数据时的可用性上限；
 C. 单值偏移命中的那两个 disp，其站点落在哪些函数里（是否像真代码路径）。
"""
import sys, os, json, struct, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
import pefile, capstone
from capstone import x86 as X

img = plan.Image(plan.EXE)

# ---------------------------------------------------------------- A. 展开元数据
pe = img.pe
print('=== A. PE 展开/调试元数据 ===')
print('sections:', [(s['name'], hex(s['va']), hex(s['vsize'])) for s in img.secs])
for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
    if d.VirtualAddress:
        print('  DIR[%d] rva=%08X size=%d' % (i, d.VirtualAddress, d.Size))
off = pe.get_offset_from_rva(pe.OPTIONAL_HEADER.DATA_DIRECTORY[6].VirtualAddress)
chars, ts, maj, mnr, typ, sz, addr, ptr = struct.unpack('<IIHHIIII', img.pe.__data__[off:off + 28])
print('debug entry: type=%d size=%d ptr=%08X' % (typ, sz, ptr))
blob = pe.__data__[ptr:ptr + sz]
print('blob head bytes:', blob[:64].hex())
print('blob ascii:', ''.join(chr(c) if 32 <= c < 127 else '.' for c in blob[:272]))
print('has ".pdata"?', any(s['name'] == '.pdata' for s in img.secs))
print('exception dir (3) rva:', pe.OPTIONAL_HEADER.DATA_DIRECTORY[3].VirtualAddress)

# ---------------------------------------------------------------- B. 帧指针比例
atlas = plan.load_atlas()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
t = img.section('.text')
code = t['data']
lo = t['va']

def prologue(entry, size):
    n = min(size, 48) if size else 48
    o = entry - lo
    if o < 0 or o >= len(code):
        return 'oob', []
    ins = []
    for k, i in enumerate(md.disasm(code[o:o + n], entry)):
        ins.append(i)
        if k >= 6:
            break
    return ins, None

stat = collections.Counter()
fpo_examples = []
for entry, size in atlas.items():
    ins, _ = prologue(entry, size)
    if not isinstance(ins, list):
        stat['oob'] += 1
        continue
    mn = [(i.mnemonic, i.op_str) for i in ins]
    if len(mn) >= 2 and mn[0] == ('push', 'ebp') and mn[1] == ('mov', 'ebp, esp'):
        stat['push_ebp_mov'] += 1
    elif len(mn) >= 1 and mn[0] == ('push', 'ebp'):
        stat['push_ebp_only'] += 1
        if len(fpo_examples) < 6:
            fpo_examples.append((entry, size, mn[:4]))
    else:
        stat['no_ebp_frame'] += 1
        if len(fpo_examples) < 12:
            fpo_examples.append((entry, size, mn[:4]))
print('\n=== B. atlas %d 个函数的序言 ===' % len(atlas))
for k, v in stat.most_common():
    print('  %-16s %5d  %.2f%%' % (k, v, 100.0 * v / len(atlas)))
print('  examples of non-standard prologue:')
for e, s, mn in fpo_examples[:8]:
    print('    %08X size=%-4d %s' % (e, s, mn))

# 小函数占比（帧指针缺失在小函数里更常见）
szs = sorted(atlas.values())
for cut in (16, 32, 64, 128):
    print('  size<=%3d: %d (%.1f%%)' % (cut, sum(1 for x in szs if x <= cut),
                                        100.0 * sum(1 for x in szs if x <= cut) / len(szs)))

# ---------------------------------------------------------------- C. 命中 disp 的站点
text = plan.Text(img)
base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
starts = sorted(atlas)
asz = [atlas[s] for s in starts]
for d in (0x444, 0x41C, 0x55C):
    ss = [s for s in base_only if s['disp'] == d]
    print('\n=== C. disp=%08X 站点 %d 个 ===' % (d, len(ss)))
    fn = collections.Counter()
    for s in ss:
        f = plan.body_of(asz, starts, s['va'])
        fn[f] += 1
    for f, n in fn.most_common(10):
        print('   in func %s : %d sites   %s' % (
            ('%08X' % f) if f else '-', n, ss[0]['text']))

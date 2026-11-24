"""降级形态的两个候选行，逐条查：
 1. 站点所在函数是否有 EBP 帧（没有 ⇒ 采样永不观测到该站点）；
 2. 该行的 ② 是否来自同一张虚表（⇒ 与 §12.3 / D-47 的关系）；
 3. 该行现在的语义栏原文。
只读。
"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
import capstone
from capstone import x86 as X

img = plan.Image(plan.EXE)
text = plan.Text(img)
atlas = plan.load_atlas()
t = img.section('.text')
code = t['data']
LO = t['va']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
starts = sorted(atlas)
asz = [atlas[s] for s in starts]

def prologue(entry):
    size = atlas.get(entry, 64)
    o = entry - LO
    ins = []
    for k, i in enumerate(md.disasm(code[o:o + 48], entry)):
        ins.append((i.mnemonic, i.op_str))
        if k >= 7:
            break
    fp = any(ins[k] == ('push', 'ebp') and ins[k + 1][0] == 'mov' and ins[k + 1][1] == 'ebp, esp'
             for k in range(len(ins) - 1))
    return size, ins, fp

cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
proved = {int(r['entry'], 16) for r in cov if r['grade'] == '[' + plan.PROVED + ']'}

cases = [(0x444, 0x706640), (0x41C, 0x70B570), (0x55C, 0x73B140)]
base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
for d, e in cases:
    print('\n===== disp %08X -> entry %08X =====' % (d, e))
    r = cov_by_entry.get(e)
    if r:
        print(' row: %s %s %s' % (r['sub'], r['name'], r['grade']))
        print(' sem: %s' % r['sem'][:400])
        print(' ev : %s' % r['ev'][:200])
    else:
        print(' NOT in coverage')
    ss = [s for s in base_only if s['disp'] == d]
    fns = collections.Counter()
    for s in ss:
        f = plan.body_of(asz, starts, s['va'])
        fns[f] += 1
    print(' sites=%d  funcs=%s' % (len(ss), ['%08X(%d)' % (f, n) for f, n in fns.most_common()]))
    for f in fns:
        if f is None:
            continue
        size, ins, fp = prologue(f)
        print('  func %08X size=%-4d ebp_frame=%s  prologue=%s' % (f, size, fp, ins[:5]))

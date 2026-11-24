"""s7: evidence — mandatory controls table + per-row classification with witnesses."""
import sys, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM

C.build_jt()
EV = C.OUT/'EVIDENCE'; EV.mkdir(exist_ok=True)

# ---------------- mandatory controls ----------------
CTL = [
    ('0053AF40', 'POS', '③b①', 'R14_COMMON §8.6 条3 举例：6 路 stage 跳表'),
    ('0069DEB0', 'NEG', '③a',   '五模式汇入同一 call 4AED70'),
    ('00704350', 'NEG', '③a',   '三闸同型仅源寄存器不同'),
    ('004DDDE0', 'NEG', '③a',   '多闸汇入共享返回桩'),
]
with open(EV/'controls.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('entry\trole\texpect\tgot_strict\tgot_loose\tpass\tn_ins\tspan\tevidence\tnote\n')
    npass = 0
    for e, role, exp, note in CTL:
        r = b3.classify(int(e, 16))
        got = r['cats'][0] if r['cats'] else '③a'
        gotl = r['cats_alt'][0] if r['cats_alt'] else '③a'
        ok = (got == exp)
        npass += ok
        evid = ''
        if r['b1']: evid = 'b1=%s' % (r['b1'][:1],)
        elif r['b2']: evid = 'b2=%s' % (r['b2'][:1],)
        elif r['b4'].get('ok'): evid = 'b4=%s' % (r['b4'],)
        else: evid = 'no ③b channel fired'
        f.write('%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%s\t%s\n' % (
            e, role, exp, got, gotl, 'PASS' if ok else 'FAIL',
            r['n_ins'], r['hi']-r['lo'], str(evid).replace('\t', ' '), note))
        print('%-9s %s  expect=%s got=%s/%s  %s' % (role, e, exp, got, gotl, 'PASS' if ok else 'FAIL'))
print('controls pass %d/%d' % (npass, len(CTL)))

# ---------------- per-row classification ----------------
rows = json.loads((C.OUT/'work'/'rows3b.json').read_text(encoding='utf-8'))

def witness(r):
    """one-line human-auditable witness for the row's first ③b channel"""
    e = int(r['entry'], 16); fn = b3.Fn(e); out = []
    if r['b1']:
        h = r['b1'][0]
        out.append('①%s site=%08X targets=%s qual=%s distinct=%s' % (
            h[0], h[1], h[2], h[3], h[4]))
    if r['b2']:
        h = r['b2'][0]
        out.append('②%s call=%08X cmp=%08X imm=%#x' % (h[0], int(h[1]), int(h[2]), int(h[3])))
    if r['b3'].get('ok'):
        out.append('③ctor=%d vt=%d maxdisp=%#x size=%s' % (
            r['b3']['n_ctor'], r['b3']['n_vt'], r['b3']['max_disp'], r['b3']['size'][:2]))
    if r['b4'].get('ok'):
        b = r['b4']
        out.append('④loop %08X..%08X n=%d bound=%s' % (b['head'], b['back'], b['n'], b['bound']))
    return '; '.join(out)

with open(EV/'classification_all.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('entry\tsubsystem\tname\tverdict\tchannels\tatlas_size\tspan\tn_ins\twitness\n')
    for r in rows:
        f.write('%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\t%s\n' % (
            r['entry'], r['sub'], r['name'], r['verdict'], ','.join(r['cats']) or '-',
            r['atlas_size'], r['span'], r['n_ins'], ''))

with open(EV/'b3_rows_with_witness.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('entry\tsubsystem\tname\tchannels\twitness\n')
    n = 0
    for r in rows:
        if not r['cats']: continue
        f.write('%s\t%s\t%s\t%s\t%s\n' % (r['entry'], r['sub'], r['name'],
                                          ','.join(r['cats']), witness(r)))
        n += 1
print('wrote EVIDENCE: classification_all.tsv (%d rows), b3_rows_with_witness.tsv (%d rows)' % (len(rows), n))

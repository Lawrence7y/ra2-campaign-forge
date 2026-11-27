#!/usr/bin/env python3
"""R144 J：并集后残余 5 张虚表的最终定性（含「落在可写节 ⇒ 运行期构造」这一分层）。

r144h 把 F7（栈帧写虚表）纳入后残余从 45 降到 5。这 5 张必须逐张说清：
  0x7e6060 在 .rdata（只读），全镜像只有 1 次 4 字节出现（= vt-4 的 COL 回指）
  其余 4 张全在 .data（**可写**）⇒ 表体本身在运行期被填，静态不可见 ⇒ 动态项
本脚本用节属性（IMAGE_SCN_MEM_WRITE）判定可写性，并给出每张的 COL/TD/表体前 8 槽。
"""
import sys, json, struct, hashlib, collections
sys.path.insert(0, '_r143')
import pefile
import r143lib as L

B = L.Bin()
TDs, COL, VTS = B.vtset()
pe = pefile.PE(L.P, fast_load=True)
writable = {}
for s in pe.sections:
    nm = s.Name.decode().rstrip('\x00')
    writable[nm] = bool(s.Characteristics & 0x80000000)   # IMAGE_SCN_MEM_WRITE
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
coltd = {c: B.dw(c + 12) for c in COL}

resid = [int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']]
rows = []
for vt in resid:
    sec = B.sec_of(vt)
    slots = []
    for k in range(8):
        v = B.dw(vt + 4 * k)
        slots.append(hex(v) if v is not None else None)
    intxt = sum(1 for s in slots if s and B.sec_of(int(s, 16)) == '.text')
    rows.append({
        'vt': hex(vt), 'sec': sec, 'writable': writable.get(sec),
        'col': hex(COLof[vt]) if vt in COLof else None,
        'col_offset': coloff.get(COLof.get(vt)),
        'td': hex(coltd[COLof[vt]]) if vt in COLof else None,
        'raw_4byte_hits': B.data.count(struct.pack('<I', vt)),
        'first8_slots': slots, 'slots_into_text': intxt,
        'slots_nonzero': sum(1 for s in slots if s and int(s, 16) != 0),
    })

n_wr = sum(1 for r in rows if r['writable'])
n_allzero = sum(1 for r in rows if r['slots_nonzero'] == 0)
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'resid_n': len(resid), 'rows': rows,
 'writable_n': n_wr, 'all_slots_zero_n': n_allzero,
 'section_writable_map': writable,
}
POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('残余恰 5 张（与 r144h 一致）', len(resid) == 5, len(resid))
chk('残余里 >= 4 张落在可写节（.data）⇒ 运行期填表', n_wr >= 4, n_wr)
chk('残余里 >= 3 张前 8 槽全 0（表体尚未出现）', n_allzero >= 3, n_allzero)
chk('.rdata 与 .text 均不可写（节属性判定正确）', writable['.rdata'] is False and writable['.text'] is False, [writable.get('.rdata'), writable.get('.text')])
chk('.data 可写（同上）', writable['.data'] is True, writable.get('.data'))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r144/r144j_resid5.json', 'w'), indent=1)
print(json.dumps(res, indent=1, ensure_ascii=False)[:3400])
print('\n'.join('%-58s %s %s' % (p[0], p[1], p[2]) for p in POS))
print('POS %d/%d FAIL %d' % (res['pos_pass'], len(POS), res['pos_fail']))

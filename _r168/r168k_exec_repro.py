#!/usr/bin/env python3
"""R168 K：忠实复现执行员 #393 的 1,390,966，并定位口径差（审计员 #394 与我都得 1,392,527）。

执行员脚本 _r168_exec/recompute.py 的两处可疑点（纯阅读，先列表再用数值证实）：
  P1 行 68：md.disasm_lite(data[pos:buf_end], base + pos) —— base 是 VA（tva=0x401000），
     pos 是**文件偏移**（从 tptr=0x1000 起）⇒ 报出的地址整体 +0x1000，而后面用
     end_va = base + length 过滤，等价于只扫 pos < 0x3df38d，末尾 4,096 B 未扫。
  P2 行 69-71：off >= block_limit 时 break 且**不**把这条跨块指令计入，下一轮从 last_end 续解码
     ⇒ 这条会被重解一次，不丢，但块内最后一条跨块指令的位置被反复试探。
本脚本分别开关 P1 / P2 复算四个数。
"""
import sys, json
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
B = L.Bin(); data = B.data; IB = B.IB
text = [s for s in B.secs if s[0] == '.text'][0]
tva = IB + text[1]; tvsz = text[2]; tptr = text[3]; trsz = text[4]
HI = tva + tvsz
md = Cs(CS_ARCH_X86, CS_MODE_32)
CHUNK = 0x10000

def scan_linear(start_off, length, base, shift_bug=True, block_limit=True):
    end_off = start_off + length
    end_va = base + length
    starts = set(); resync = set()
    pos = start_off; steps = 0
    while pos < end_off:
        steps += 1
        if steps > 30000000: raise RuntimeError('explosion')
        if block_limit:
            bl = start_off + ((pos - start_off) // CHUNK + 1) * CHUNK
            buf_end = min(bl + 15, len(data))
        else:
            bl = end_off
            buf_end = min(pos + CHUNK + 15, len(data))
        last_end = pos
        hb = False
        va_base = (base + pos) if shift_bug else (base + (pos - start_off))
        for (addr, size, _, _) in md.disasm_lite(data[pos:buf_end], va_base):
            off = addr - va_base + pos   # 换算回文件偏移
            if off >= bl:
                hb = True; break
            starts.add(addr)
            last_end = off + size
        if last_end < bl and not hb:
            resync.add(va_base + (last_end - pos)); pos = last_end + 1
        else:
            if last_end > pos: pos = last_end
            else:
                resync.add(va_base + (pos - pos)); pos += 1
    return ({a for a in starts if a < (base + (length if not shift_bug else 0)) or a < HI and not shift_bug},
            {r for r in resync if not shift_bug and r < HI})

# 用执行员的原式（含 shift bug）与改正版各跑一次
def exec_literal():
    end_va = tva + tvsz
    starts = set(); resync = set()
    pos = tptr; start_off = tptr; end_off = tptr + tvsz
    steps = 0
    while pos < end_off:
        steps += 1
        bl = start_off + ((pos - start_off) // CHUNK + 1) * CHUNK
        buf_end = min(bl + 15, len(data))
        last_end = pos; hb = False
        for (addr, size, _, _) in md.disasm_lite(data[pos:buf_end], tva + pos):
            off = addr - (tva + pos) + pos
            if off >= bl:
                hb = True; break
            starts.add(addr)
            last_end = off + size
        if last_end < bl and not hb:
            resync.add(tva + last_end); pos = last_end + 1
        else:
            if last_end > pos: pos = last_end
            else:
                resync.add(tva + pos); pos += 1
    return ({a for a in starts if a < end_va}, {r for r in resync if r < end_va}, steps)

ex_starts, ex_resync, ex_steps = exec_literal()

def corrected():
    starts = set(); resync = set()
    pos = tptr; start_off = tptr; end_off = tptr + trsz
    steps = 0
    while pos < end_off:
        steps += 1
        bl = start_off + ((pos - start_off) // CHUNK + 1) * CHUNK
        buf_end = min(bl + 15, len(data))
        last_end = pos; hb = False
        va_base = tva + (pos - start_off)
        for (addr, size, _, _) in md.disasm_lite(data[pos:buf_end], va_base):
            off = addr - va_base + pos
            if off >= bl:
                hb = True; break
            if addr < HI: starts.add(addr)
            last_end = off + size
        if last_end < bl and not hb:
            if va_base + (last_end - pos) < HI: resync.add(va_base + (last_end - pos))
            pos = last_end + 1
        else:
            if last_end > pos: pos = last_end
            else:
                if va_base < HI: resync.add(va_base)
                pos += 1
    return {a for a in starts if a < HI}, {r for r in resync if r < HI}, steps

co_starts, co_resync, co_steps = corrected()

A = []
A.append({'id': 'K1 执行员原式复现 1,390,966', 'ok': len(ex_starts) == 1390966, 'detail': str(len(ex_starts))})
A.append({'id': 'K2 执行员原式复现 65 个重对齐点', 'ok': len(ex_resync) == 65, 'detail': str(len(ex_resync))})
A.append({'id': 'K3 改正 VA 基址（tva + (pos - tptr)）后起点 = 1,392,527', 'ok': len(co_starts) == 1392527,
          'detail': str(len(co_starts))})
A.append({'id': 'K4 改正后重对齐点 = 65', 'ok': len(co_resync) == 65, 'detail': str(len(co_resync))})
# 差值归因：执行员漏扫的后 4,096 B 内的起点数
tail_lo = tva + tvsz - 4096
tail_starts = sum(1 for a in co_starts if a >= tail_lo)
A.append({'id': 'K5 差 1,561 == 末 4,096 B 内起点数（执行员因 end_va 过滤而丢）',
          'ok': len(co_starts) - len(ex_starts) == tail_starts,
          'detail': 'diff=%d tail_starts=%d' % (len(co_starts) - len(ex_starts), tail_starts)})
# 与执行员的 65 个重对齐点逐条比对
A.append({'id': 'K6 执行员的重对齐点（去 +0x1000 平移）与正确集合逐条相同',
          'ok': set(r - 0x1000 for r in ex_resync) == co_resync,
          'detail': 'symdiff=%d' % len(set(r - 0x1000 for r in ex_resync) ^ co_resync)})
out = {'exec_starts': len(ex_starts), 'exec_resync': len(ex_resync), 'exec_steps': ex_steps,
       'corrected_starts': len(co_starts), 'corrected_resync': len(co_resync), 'corrected_steps': co_steps,
       'tail_4096_starts': tail_starts,
       'exec_resync_shifted': sorted(hex(r - 0x1000) for r in ex_resync)[:10],
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168k_exec_repro.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'assertions'}, ensure_ascii=False, indent=1))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:160])

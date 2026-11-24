"""S12: the Q2 time-budget tables (pure arithmetic over measured instruction counts).

All instruction counts come from the CFG channel of w171_lib (see S2/S10 evidence files)
and are cross-checked against function_atlas.tsv n_instr in S13.

time(us) = instructions * CPI / freq_Hz * 1e6
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w171_lib as L

OUT = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


# ---- measured instruction counts (CFG channel, this card) ----
I_WRAP = 485      # Drive Process wrapper 0x4B0500
I_PROC = 2600     # Drive::Process 0x4B2630
I_UPD = 669       # FootClass::UpdatePathfinding 0x4D3920
I_CFP = 58        # CallFindPath 0x4CBBA0
I_FP = 327        # PathFinder::FindPath 0x42C900
I_ASTOT = 812     # fn 0x429A90 whole
I_ROUND = 544     # outer A* loop body 0x429D6D..0x42A3D8
I_SUCC = 331      # inner successor loop 0x429DC2..0x42A1AD
I_ASTAILLOOP = [47, 12, 12, 39, 39]   # other back edges in 0x429A90
I_A_PREAMBLE = I_ASTOT - I_ROUND
I_CHAIN_NONASTAR = I_WRAP + I_PROC + I_UPD + I_CFP + I_FP + I_A_PREAMBLE

FREQS = [('1.0 GHz', 1.0e9), ('2.0 GHz', 2.0e9), ('3.0 GHz', 3.0e9)]
CPIS = [1, 2, 4]
ROUNDS = [30, 100, 300, 1000, 65527]

p('instruction counts used (CFG channel, w171):')
p('  0x4B0500 wrapper            %6d' % I_WRAP)
p('  0x4B2630 Drive::Process     %6d' % I_PROC)
p('  0x4D3920 UpdatePathfinding  %6d' % I_UPD)
p('  0x4CBBA0 CallFindPath       %6d' % I_CFP)
p('  0x42C900 FindPath           %6d' % I_FP)
p('  0x429A90 A* container       %6d  (of which outer loop body %d, preamble/exit %d)'
  % (I_ASTOT, I_ROUND, I_A_PREAMBLE))
p('  A* outer loop body per round %d ; inner successor loop %d ; other loops %s'
  % (I_ROUND, I_SUCC, I_ASTAILLOOP))
p('  non-A* fixed part (all of the chain above minus the round loop) = %d' % I_CHAIN_NONASTAR)
p()


def t_us(instr, cpi, f):
    return instr * cpi / f * 1e6


p('=== TABLE 1: A* search cost only, %d instructions per round ===' % I_ROUND)
hdr = '| rounds | ' + ' | '.join('%s CPI%d' % (fn, c) for fn, f in FREQS for c in CPIS) + ' |'
p(hdr)
p('|' + '---|' * (1 + len(FREQS) * len(CPIS)))
for R in ROUNDS + [10000]:
    row = ['| %d |' % R]
    for fn, f in FREQS:
        for c in CPIS:
            row.append(' %.3f |' % (t_us(R * I_ROUND, c, f) / 1000.0))
    p(''.join(row))
p('  (units: ms.  10000 row = the 0x2710 constant found at 0x42A3E2.)')
p()

p('=== TABLE 2: A* with the inner successor loop expanded 8x (544 + 7*331 = %d instr/round) ==='
  % (I_ROUND + 7 * I_SUCC))
for R in ROUNDS:
    row = ['| %d |' % R]
    for fn, f in FREQS:
        for c in CPIS:
            row.append(' %.3f |' % (t_us(R * (I_ROUND + 7 * I_SUCC), c, f) / 1000.0))
    p(''.join(row))
p()

p('=== TABLE 3: non-A* fixed cost of one chain pass (%d instructions) ===' % I_CHAIN_NONASTAR)
row = ['| fixed |']
for fn, f in FREQS:
    for c in CPIS:
        row.append(' %.3f |' % (t_us(I_CHAIN_NONASTAR, c, f) / 1000.0))
p(hdr)
p(''.join(row))
p()

p('=== TABLE 4: rounds needed to fill the 4.54 ms budget (544 instr/round) ===')
p('| freq | CPI1 | CPI2 | CPI4 |')
p('|---|---|---|---|')
for fn, f in FREQS:
    row = ['| %s |' % fn]
    for c in CPIS:
        per_round_us = I_ROUND * c / f * 1e6
        row.append(' %.0f |' % (4540.0 / per_round_us))
    p(''.join(row))
p()

p('=== TABLE 5: %% of the 4.54 ms budget consumed at R rounds (3.0 GHz / CPI1, the most favourable) ===')
for R in ROUNDS:
    p('  R=%-6d  %8.3f ms  = %5.1f%% of 4.54' % (R, t_us(R * I_ROUND, 1, 3e9) / 1000.0,
                                                 100.0 * t_us(R * I_ROUND, 1, 3e9) / 1000.0 / 4.54))
p()

p('=== TABLE 6: worst-case single invocation (65527 rounds, both tables, plus fixed part) ===')
for fn, f in FREQS:
    for c in CPIS:
        a = t_us(65527 * I_ROUND + I_CHAIN_NONASTAR, c, f) / 1000.0
        b = t_us(65527 * (I_ROUND + 7 * I_SUCC) + I_CHAIN_NONASTAR, c, f) / 1000.0
        p('  %s CPI%d : static-only %.2f ms ; successor-expanded %.2f ms' % (fn, c, a, b))
p()

p('=== TABLE 7: what 4.54 ms buys at 3.0 GHz / CPI 2 (the anchor R12 used: 0.3627 us/round) ===')
per = I_ROUND * 2 / 3e9 * 1e6
p('  per round = %.4f us ; 4540 us / per round = %.0f rounds' % (per, 4540.0 / per))
for R in (12600,):
    p('  upstream statement "4.54 ms ~ 12,600 rounds" reproduces at R=%d' % R)
p()
p('=== TABLE 8: what the measured 0.284 ms/moving-object/frame means in rounds/frame ===')
p('  0.284 ms/frame at 3.0GHz CPI2 -> %.1f rounds/frame equivalent' % (284.0 / per))
p()
p('=== TABLE 9: rounds needed to fill 0.284 ms (the per-FRAME anchor, see S15) ===')
p('| freq | CPI1 | CPI2 | CPI4 |')
p('|---|---|---|---|')
for fn, f in FREQS:
    row = ['| %s |' % fn]
    for c in CPIS:
        per_round_us = I_ROUND * c / f * 1e6
        row.append(' %.0f |' % (284.0 / per_round_us))
    p(''.join(row))
p()
p('=== TABLE 10: sub-step static instruction budget (one Drime::Process pass) ===')
p('| sub-step | functions (CFG instr count) | static instr, exclusive of A* rounds |')
p('|---|---|---|')
sub1 = ('(1) pathfinding call chain',
        '0x4D3920=669 + 0x4CBBA0=58 + 0x42C900=327 + 0x429A90=812 (non-round part 268)',
        669 + 58 + 327 + I_ASTOT)
sub2 = ('(2) along-path advance / coord update',
        '0x4B2630=2600 (whole) + 0x4B0F20=1655 (called 1-2x)', 2600 + 1655)
sub3 = ('(3) cell / grid update via vptr slot 73 (Limbo+Unlimbo)',
        '0x4D3780=61 + 0x5687F0=265 + 0x47EA90=84 + 0x5683C0=295 + 0x47E8A0=156 (+0x5657A0=18)',
        61 + 265 + 84 + 295 + 156 + 18)
sub4 = ('(4) other (effect/voice/render hook, alloc, frame stamp)',
        '0x421EA0=587 + 0x4C9480=17 + 0x4DF0D0=4 + 0x46B640=6 + 0x7C8E17=6', 587 + 17 + 4 + 6 + 6)
for nm, src, n in (sub1, sub2, sub3, sub4):
    p('| %s | %s | %d |' % (nm, src, n))
p()
p('  same sub-steps in time (ms), 3.0 GHz / CPI 2 (0.3627 us per 544-instr round):')
for nm, src, n in (sub1, sub2, sub3, sub4):
    p('    %-56s %8.4f ms' % (nm, n * 2 / 3e9 * 1e6 / 1000.0))
p('  A* rounds alone at 3.0 GHz / CPI 2: 1 round = 0.3627 us ; '
  '0.284 ms = %.0f rounds ; 4.54 ms = %.0f rounds' % (284.0 / per, 4540.0 / per))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EVIDENCE',
                       'S12_timebudget.txt'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')

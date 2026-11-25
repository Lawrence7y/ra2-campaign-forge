#!/usr/bin/env python3
# R130 r130g: self-audit / cross-checks for this round's deliverables.
# Every number quoted in this round's write-up is recomputed here from disk, and each
# assertion names the failure it would catch. Positive AND negative controls included.
import io
import json
import os
import subprocess
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R130 = os.path.join(ROOT, '_r130')

PASS, FAIL = [], []


def ck(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  PASS ' if cond else '  FAIL ') + name + (' :: ' + detail if detail else ''))
    return cond


def load(fn):
    return json.load(io.open(os.path.join(R130, fn), encoding='utf-8'))


def main():
    b = load('r130b_tables.json')
    c = load('r130c_factory.json')
    e = load('r130e_arbitrate.json')
    d = load('r130d_tautology.json')
    f = load('r130f_c17_vacuum.json')

    print('== A. table census (r130b) ==')
    ck('A1 instruction count is the full .text sweep', b['insn_count'] == 1394186,
       str(b['insn_count']))
    ck('A2 positive control: R129 loop recovered', b['posctl_r129_loop_found'] is True)
    ck('A3 census size is 117', b['table_loops'] == 117, str(b['table_loops']))
    rd = [h for h in b['hits'] if h['head_sec'] == '.rdata']
    ck('A4 .rdata-head loops == 9', len(rd) == 9, str(len(rd)))
    # the only stride>=8 .rdata table other than 0x7f3710 must be the terrain strings
    big = [h for h in rd if h['step'] >= 8 and h['table_head'] != '0x7f3710']
    ck('A5 stride>=8 .rdata tables besides 0x7f3710 are exactly the 2 terrain ones',
       sorted(h['table_head'] for h in big) == ['0x7e1b78', '0x7e1b88'],
       str(sorted(h['table_head'] for h in big)))
    ck('A6 those two are step 112', all(h['step'] == 112 for h in big))
    ck('A7 0x7f3710 is present with step 8 and count 1',
       any(h['table_head'] == '0x7f3710' and h['step'] == 8 and h['count'] == 1
           for h in rd))

    print('== B. wrapper uniqueness (r130c) ==')
    ck('B1 wrapper has exactly 2 call sites', len(c['wrapper_call_sites']) == 2,
       str(c['wrapper_call_sites']))
    ck('B2 both call sites are the known ones',
       c['wrapper_call_sites'] == ['0x6bc364', '0x6bc3aa'])
    ck('B3 exactly one census loop feeds the wrapper',
       len(c['feeding_loops']) == 1, str(len(c['feeding_loops'])))
    ck('B4 that loop is the 0x6bc34d one over table 0x7f3710',
       c['ctl_known_loop_feeds_wrapper'] is True)
    ent = c['feeding_loops'][0]['entries']
    ck('B5 the table has exactly 1 entry', len(ent) == 1, str(len(ent)))
    ck('B6 entry is (0x7e9500, blowfish.dll)',
       ent[0]['rclsid_ptr'] == '0x7e9500' and ent[0]['dll_name'] == 'blowfish.dll')
    ck('B7 CLSID bytes match R129 verbatim',
       ent[0]['guid_bytes'] == '10ad4014a86ad111b6f900a024ddafd1', ent[0]['guid_bytes'])

    print('== C. second-decoder arbitration (r130e) ==')
    ck('C1 capstone and objdump agree on the 2 call sites',
       e['ctl_two_decoders_agree'] is True)
    ck('C2 raw E8-rel32 byte scan agrees with objdump',
       e['ctl_e8_scan_matches_objdump'] is True)
    ck('C3 naive imm32 scan for the wrapper finds ZERO (calls are relative)',
       e['ctl_imm32_wrapper_is_zero_not_two'] is True,
       str(e['routeB_imm32_wrapper_data_occurrences']))
    ck('C4 table head constant appears as a data imm32 exactly once',
       e['n_head_const_sites'] == 1, str(e['n_head_const_sites']))
    ck('C5 objdump decoded more instructions than capstone (sanity, both ~1.4M)',
       abs(e['routeA_objdump_insns'] - b['insn_count']) < 10000,
       '%d vs %d' % (e['routeA_objdump_insns'], b['insn_count']))

    print('== D. claims-none check expressions (r130d) ==')
    s = d['summary']
    ck('D1 all 19 claims-none rows have a supported expression form',
       s['supported_forms'] == 19, str(s['supported_forms']))
    ck('D2 all 19 hold on the real product', s['real_holds'] == 19, str(s['real_holds']))
    ck('D3 NONE hold on an empty product (not tautologies)',
       s['empty_also_holds_TAUTOLOGY'] == 0, str(s['empty_also_holds_TAUTOLOGY']))
    ck('D4 NONE survive removal of the content they certify (coupled)',
       s['mutant_still_holds_DECOUPLED'] == 0,
       str(s['mutant_still_holds_DECOUPLED']))
    ck('D5 both controls pass for all 19', s['both_controls_pass'] == 19,
       str(s['both_controls_pass']))

    print('== E. C17 vacuum (r130f) ==')
    ck('E1 12 rows claim column 7 = yes', f['rows_claiming_yes'] == 12,
       str(f['rows_claiming_yes']))
    ck('E2 no product file is missing', f['product_files_missing'] == 0)
    ck('E3 zero DISC_RECHECK lines exist in those products',
       f['total_disc_recheck_lines_in_real_products'] == 0)
    ck('E4 all 12 rows individually have zero lines', f['rows_with_zero_lines'] == 12)
    ck('E5 scanner is NOT broken: 26 fixtures do carry lines (PC1)',
       f['fixture_files_carrying_lines'] == 26 and f['ctl_PC1_fixtures_scanned'])
    ck('E6 line counter counts a synthetic line (NC1)', f['ctl_NC1_line_counted'])
    ck('E7 per-id filter rejects a wrong id (NC2)', f['ctl_NC2_wrong_id_zero'])
    ck('E8 therefore C17 examines nothing', f['c17_is_vacuuming'] is True)

    print('== F. gate still green, artifacts untouched ==')
    p = subprocess.run([sys.executable, os.path.join(
        ROOT, 'lead/next_re_20261117_r14/check_disc.py')],
        capture_output=True, text=True, timeout=600)
    ck('F1 check_disc.py exit 0', p.returncode == 0, str(p.returncode))
    ck('F2 gate self-check reports R130 (this round bumped GATE_VER after the C16 pin)',
       'ok(R130)' in p.stdout)
    ck('F3 C17 checked=0 reproduced by the gate itself', 'checked=0' in p.stdout)
    ck('F4 C11 reports ok=0 (no false positives claimed)', 'ok=0' in p.stdout)

    print('== G. CR invariants ==')
    exp = [('R14_COMMON.md', 1081), ('STATUS_BOARD.md', 0),
           ('BOARD_ARCHIVE.md', 2952)]
    for fn, want in exp:
        pth = os.path.join(ROOT, 'lead/next_re_20261117_r14', fn)
        bb = io.open(pth, 'rb').read()
        ck('G CR %s == %d' % (fn, want), bb.count(b'\r') == want,
           str(bb.count(b'\r')))
    for fn, want in (('lead/LEAD_LOCK', 137),
                     ('lead/GOAL_THREE_TARGETS_20261018.md', 337)):
        bb = io.open(os.path.join(ROOT, fn), 'rb').read()
        ck('G CR %s == %d' % (fn, want), bb.count(b'\r') == want,
           str(bb.count(b'\r')))

    print()
    print('TOTAL PASS %d FAIL %d' % (len(PASS), len(FAIL)))
    if FAIL:
        print('FAILED: ' + repr(FAIL))
    return 0 if not FAIL else 1


if __name__ == '__main__':
    sys.exit(main())

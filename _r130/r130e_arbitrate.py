#!/usr/bin/env python3
# R130 r130e: byte-level second decoder (objdump) arbitration for the "only one
# class-factory table" result, plus a structural check that does NOT depend on my
# capstone loop classifier.
#
# R129's todo (1) asked: is 0x7f3710 the only table of its kind? Two independent
# routes are used here, neither reusing r130b's classifier:
#
#   Route A (objdump, second decoder): every call whose operand is 0x6bedb0.
#   Route B (bytes, no decoder at all): every imm32 occurrence of the wrapper address
#           and of the table head/bound constants in .text, located by raw byte scan.
#
# Controls:
#   - Route A must find exactly the two sites capstone found (0x6bc364, 0x6bc3aa).
#   - Route B must find the wrapper address as an imm32 exactly at those same sites
#     (E8 rel32 form: the encoded displacement is target-(site+5), NOT the target).
#     This is the trap: a naive imm32 scan for 0x6bedb0 finds ZERO, because calls are
#     relative. So Route B differs for call sites vs data pointers -- both are measured.
# Memory: objdump is a subprocess over a bounded range; byte scan is a single pass.
import io
import json
import re
import subprocess
import sys

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r130/r130e_arbitrate.json'
WRAPPER = 0x6bedb0
HEAD = 0x7f3710
BOUND = 0x7f3718
TEXT_VA = 0x401000
TEXT_RAW = 0x1000
TEXT_LEN = 0x3e0000


def objdump_calls():
    """Route A: second decoder. Return call sites targeting WRAPPER."""
    p = subprocess.run(
        ['i686-w64-mingw32-objdump', '-d', '--start-address=0x%x' % TEXT_VA,
         '--stop-address=0x%x' % (TEXT_VA + TEXT_LEN), EXE],
        capture_output=True, text=True, timeout=900)
    if p.returncode != 0:
        raise SystemExit('objdump failed: ' + p.stderr[:400])
    ins, sites = 0, []
    for ln in p.stdout.splitlines():
        m = re.match(r'^\s+([0-9a-f]+):\t', ln)
        if not m:
            continue
        ins += 1
        # Self-error S-201 (kept as evidence of the trap): the natural patterns
        #   r'call\s+([0-9a-f]+)\s'   and   r'call\s+([0-9a-f]+)(?!\S)'
        # BOTH fail, and for a subtle reason: [0-9a-f]+ matches the single character
        # '0' of the '0x' prefix and then stops at 'x', so the following \s / (?!\S)
        # can never be satisfied. Neither failure has anything to do with the binary.
        # The prefix must be consumed explicitly.
        m2 = re.search(r'\bcall\s+(?:0x)?([0-9a-f]+)\b', ln)
        if m2 and int(m2.group(1), 16) == WRAPPER:
            sites.append(int(m.group(1), 16))
    return ins, sorted(sites)


def byte_scan(needle_int):
    """Route B: locate every little-endian 4-byte occurrence in .text raw bytes."""
    d = io.open(EXE, 'rb').read()
    text = d[TEXT_RAW:TEXT_RAW + TEXT_LEN]
    pat = needle_int.to_bytes(4, 'little')
    out, i = [], text.find(pat)
    while i != -1:
        out.append(TEXT_VA + i)
        i = text.find(pat, i + 1)
    return sorted(out)


def main():
    ins, sites = objdump_calls()
    ea = byte_scan(WRAPPER)
    eh = byte_scan(HEAD)
    eb = byte_scan(BOUND)

    # every E8 rel32 whose target is WRAPPER -- the correct byte-level test for a call
    d = io.open(EXE, 'rb').read()
    text = d[TEXT_RAW:TEXT_RAW + TEXT_LEN]
    ecalls = []
    for i in range(len(text) - 5):
        if text[i] == 0xE8:
            rel = int.from_bytes(text[i + 1:i + 5], 'little', signed=True)
            va = TEXT_VA + i
            if va + 5 + rel == WRAPPER:
                ecalls.append(va)

    rec = {
        'routeA_objdump_insns': ins,
        'routeA_wrapper_calls': [hex(x) for x in sites],
        'routeB_imm32_wrapper_data_occurrences': [hex(x) for x in ea],
        'routeB_imm32_table_head': [hex(x) for x in eh],
        'routeB_imm32_table_bound': [hex(x) for x in eb],
        'routeB_E8_rel32_wrapper_calls': [hex(x) for x in sorted(ecalls)],
        'capstone_wrapper_calls': ['0x6bc364', '0x6bc3aa'],
    }
    cap = {'0x6bc364': 0x6bc364, '0x6bc3aa': 0x6bc3aa}
    rec['ctl_two_decoders_agree'] = (
        [hex(x) for x in sites] == ['0x6bc364', '0x6bc3aa'])
    rec['ctl_e8_scan_matches_objdump'] = (
        sorted(ecalls) == sites)
    rec['ctl_imm32_wrapper_is_zero_not_two'] = (len(ea) == 0)
    # table head constant should appear as a data imm32 somewhere; report count only
    rec['n_head_const_sites'] = len(eh)
    rec['n_bound_const_sites'] = len(eb)
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    for k in ('routeA_objdump_insns', 'routeA_wrapper_calls',
              'routeB_imm32_wrapper_data_occurrences',
              'routeB_E8_rel32_wrapper_calls',
              'n_head_const_sites', 'n_bound_const_sites',
              'ctl_two_decoders_agree', 'ctl_e8_scan_matches_objdump',
              'ctl_imm32_wrapper_is_zero_not_two'):
        print(k, '=', rec[k])
    ok = (rec['ctl_two_decoders_agree'] and rec['ctl_e8_scan_matches_objdump']
          and rec['ctl_imm32_wrapper_is_zero_not_two'])
    print('ALL CTL', ok)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

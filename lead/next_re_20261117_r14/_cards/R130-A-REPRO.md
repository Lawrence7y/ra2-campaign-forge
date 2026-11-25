# R130 dispatch card A — independent reproduction of the "one class-factory table" result

ROLE: executor. Provider magpie-anthropic, model work/cn:deepseek-v4.1-flash.
Budget 8 minutes. Do NOT use backticks anywhere in your report.

## Context you can rely on

Project root: /home/t628/projects/ra2-campaign-forge
Binary: ra2bench/gamemd.exe (PE32, ImageBase 0x400000).
Sections (VA, verified): .text 0x401000 len raw 0x3e0000 ; .rdata 0x7e1000 ;
.data 0x812000 (raw size 0x6c000, so .data virtual-only BSS tail above 0x87e000 has
NO file bytes) ; .rsrc 0xb7a000 ; .detour 0xb93000.

Prior round R129 established these byte facts (treat as hypotheses to re-derive, not gospel):
1. The function at 0x6bedb0 is a wrapper that calls CoCreateInstance, OleRun, call [ecx],
   and call [edx+8] (Release).
2. A loop at 0x6bc34d iterates a table whose head is 0x7f3710 with stride 8 and upper
   bound 0x7f3718, i.e. exactly one 8-byte entry.
3. That entry holds rclsid pointer 0x7e9500 and a pointer to the ASCII string blowfish.dll.
4. The CLSID bytes at 0x7e9500 are 10 ad 40 14 a8 6a d1 11 b6 f9 00 a0 24 dd af d1.

## Your task (mechanical, reproducible)

Re-derive independently, with your own script, and report exact numbers:

T1. Every call instruction anywhere in .text whose target is exactly 0x6bedb0.
    Report the count and every call site address.
T2. Are all of those call sites inside the address range of the loop 0x6bc34d .. jl back-edge?
    Report the back-edge address you find and whether each call is inside it.
T3. Scan all of .text for data-table iteration loops of this shape, in one aligned
    forward disassembly pass:
      mov REG, <immediate that lands in .rdata or .data>   (may be hoisted just BEFORE the loop head)
      add REG, <small step>
      cmp REG, <immediate bound>
      conditional jump back to the loop head, with the cmp IMMEDIATELY before the jump
    plus arithmetic consistency (bound minus head) mod step == 0 and count between 1 and 4096.
    Report the total count of such loops, and separately the count whose head is in .rdata.
    Positive control you must satisfy: your scan MUST find the loop at 0x6bc34d with
    head 0x7f3710, bound 0x7f3718, step 8, count 1. If it does not, your scan is wrong,
    not the binary — fix it and say what was wrong.
T4. Report whether any .rdata-head table with stride greater than or equal to 8 exists
    other than 0x7f3710, and give their head addresses, strides and counts.

## Hard constraints

- Memory: use disasm_lite only. Never set md.detail = True anywhere. Never materialise the
  whole .text instruction list; stream it. There is a 200 MB budget; the box has about 1 GB
  available and OOM kills the run.
- capstone prints SMALL immediates in DECIMAL (add esi, 8) and large ones in hex
  (cmp esi, 0x7f3718). Your immediate parser must accept BOTH forms. Do not repeat the
  mistake of accepting only 0x-prefixed literals.
- Do not decode a window starting from an arbitrary address: that desynchronises the
  decoder and yields false "not found". Do one aligned forward pass and keep a bounded
  history of the last 0x1000 bytes worth of instructions.
- Write your script to /home/t628/projects/ra2-campaign-forge/_r130/audit_a_repro.py and its
  JSON output next to it. Wrap the run in timeout 600.
- Do not modify any file outside _r130/. Do not touch check_disc.py, DISC_RECHECK.tsv,
  STATUS_BOARD.md, LEAD_LOCK, R14_COMMON.md.

## What to report back

Line 1: PASS or FAIL for each of T1..T4 with your numbers.
Then: the exact call-site list, the exact loop census numbers, the .rdata stride>=8 table list,
and a short note on anything where your numbers DIFFER from the four hypotheses above.
Differences matter more than agreement — state them plainly and do not paper over them.
No backticks, no markdown fences.

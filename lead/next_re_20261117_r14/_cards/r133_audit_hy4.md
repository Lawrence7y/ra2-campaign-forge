R133 AUDIT CARD - cross-family audit of the R133 load-bearing claims

You are the cross-family auditor. Your family is hy4. Do NOT trust the numbers below;
recompute them from the binary and report agreements AND disagreements.

BINARY
  /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  imagebase 0x400000. Sections: .text VA 0x401000 VSize 0x3df38d RawPtr 0x1000
  .rdata VA 0x7e1000 .data VA 0x812000 .detour VA 0xb93000

TOOLS on this machine
  python3 with capstone and pefile installed, i686-w64-mingw32-objdump, rg
  HARD RULE: never call md.disasm() with detail=True over the whole 4MB .text.
  Use md.disasm_lite() or <=64KiB blocks. detail=True only on <=0xc0 byte windows.

BACKGROUND (R132, already accepted)
  Two 136-byte identical COM-instantiation templates exist at VA 0x6bedb0 and 0x41c250.
  Each ends in ret 0xc (three cdecl args). Byte offset 0x4e and 0x70 differ between
  them, c0 versus b0.

CLAIMS TO AUDIT (each must be independently recomputed)

  C1. The 136-byte body at 0x6bedb0 and at 0x41c250 each differ in EXACTLY two byte
      offsets, 0x4e and 0x70, both c0 in A and b0 in B. Report the full sorted list of
      differing offsets you measure. Any additional offset is a disagreement.

  C2. Both differing bytes are byte index 1 of a push imm32 instruction (opcode 0x68)
      starting at offset 0x4d and 0x6f respectively. So the pushed POINTER differs in
      exactly one byte, while the 16-byte GUID each pointer refers to differs in 15 of
      16 bytes. State both numbers.

  C3. The 16 bytes at 0x817bc0 decode as {00000000-0000-0000-C000-000000000046}
      (IID_IUnknown) and the 16 bytes at 0x817bb0 as {070F3290-9841-11D1-B709-00A024DDAFD1},
      using Data1 little-endian dword, Data2 little-endian word, Data3 little-endian word,
      then 8 bytes verbatim. Report both strings and the byte-diff count.

  C4. The template has THREE push imm32 instructions pointing at IID constants, at body
      offsets +0x21, +0x4d, +0x6f. In A all three point at 0x817bc0; in B +0x21 points at
      0x817bc0 but +0x4d and +0x6f point at 0x817bb0. Report the three constants per
      instance.

  C5. Within each 136-byte body there is a test al, 0x14 followed by a je. Report the
      body offset of the test, the body offset of the je, and the je target VA.

  C6. For BOTH instances the je target is reached by exactly ONE branch in the 136-byte
      body (no second branch, no fallthrough into it). Report the number of branches in
      the body whose target equals the else entry, and the mnemonic+offset of the
      instruction that ends immediately before the else entry.

  C7. The else arm (starting at the je target) makes exactly ONE call and that call is
      dword ptr [0x7e15fc] (CoCreateInstance). The else arm contains NO reference to
      0x7e1600 (OleRun). The if arm DOES contain a call through 0x7e1600. Report the
      call list for each arm.

  C8. There are exactly 15 direct call sites into these two templates in the whole
      binary: 2 into 0x6bedb0 and 13 into 0x41c250. Report both counts and both address
      lists. Verify each hit decodes as a real 5-byte E8/E9 call or jmp landing exactly
      on the entry. Note that the entry VA is NOT stored as an imm32 anywhere, so an
      imm32 scan alone would wrongly report zero callers -- state whether you agree.

  C9. THE CENTRAL CLAIM, and the one most likely to be wrong. At every one of the 15
      call sites, the THIRD stack argument (arg3) is the constant 7. Method that works:
      one linear disasm_lite sweep with skipdata=True gives you addr -> (size, mnemonic,
      op_str). From the call site walk BACKWARDS requiring addr+size == next_addr at each
      step, stop at the first gap or first control transfer, collect the pushes in that
      contiguous tail, take the FIRST THREE (nearest the call), and arg3 is the EARLIEST
      of those three (the last in that nearest-three list, because cdecl pushes right to
      left). Report arg3 at all 15 sites. Two failure modes are known and must be avoided:
      disassembling a window from a non-instruction-boundary start, and a backward walk
      that does not enforce contiguity.

  C10. Consequence: since 7 AND 0x14 == 4 (non-zero), the je is NOT taken, so control
      falls through into the if arm. Show the arithmetic. Then state, precisely scoped,
      what follows: in THIS build, under the observed arg3, the else arm is not reached.
      Do you agree that this does NOT prove the else arm is unreachable for arbitrary
      inputs? Say explicitly whether the stronger claim is proven.

  C11. Negative controls you must run yourself, reporting each result:
      (a) reading 16 bytes at 0x817bd0 (16 after the IUnknown constant) must yield a
          DIFFERENT GUID string than 0x817bc0, proving the reader is not aliased;
      (b) formatting the same 16 bytes big-endian must yield a different string than
          little-endian, proving the formatter is order-sensitive;
      (c) scanning for the entry VA 0x6bedb0 as an imm32 must report ZERO in a binary
          where it demonstrably has 2 callers via rel32 -- proving an imm32 scan is the
          wrong tool for callers but the right tool for pointer tables.

SECOND TASK, SEPARATE FROM THE ABOVE - the C7 gate fix
  R133 also changed the discipline gate. Read these three files:
    lead/next_re_20261117_r14/check_disc.py
    lead/next_re_20261117_r14/DISC_RECHECK.tsv
    _r133/r133j2_c7nctl.py
  The gate gained a C7b block that pins the shape census
  {'grep=':24,'grepcount=':3,'rows=':4,'exists':0,'bytes=':0,'none':0} and FAILs on drift.
  Read the code and answer, briefly:
    G1. Does the pass/fail decision actually depend on every one of the six keys, or is
        any key inert? Name any inert key.
    G2. The comment claims a zero count is ABSENT from a frequency dict rather than
        present-with-value-zero, and that seeding every pinned shape at 0 is what makes
        exists=0 checkable. Is that reasoning correct for a plain dict of counts? Explain
        in two sentences.
    G3. Can the two loops be passed while the census is still wrong in a way a reviewer
        would care about? If yes, give the concrete case.
    G4. The controls in _r133/r133j2_c7nctl.py stage a temp copy of the gate. Read the
        stage()/derive_needed() logic and say whether the staged copy is genuinely
        equivalent to the real tree for the purposes of this gate. Name anything the gate
        reads that would NOT be staged.
  Do not modify these files. Report only.

WHAT TO RETURN
  A short report with one line per claim: AGREE or DISAGREE, the number you measured,
  and the command or script you used. Put DISAGREEMENTS first if there are any. Do not
  restate the card back to me. If a claim is true only under a narrower scope than
  stated, say so and give the narrower scope.

ARTIFACTS
  Put any scripts and json you produce under
  /home/t628/projects/ra2-campaign-forge/_r133/sub_hy4/
  with filenames starting r133hy_ . Do not modify anything under lead/ .

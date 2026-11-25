R134 EXECUTOR CARD - independently verify the C7/C7b gate holes and score the proposed fix

You are the executor. Do NOT trust the numbers below. Recompute everything from the files on disk.
Your family is deepseek. Another family (hy4) will audit separately; you are NOT the auditor.

WORKDIR
  /home/t628/projects/ra2-campaign-forge
  Gate under test: lead/next_re_20261117_r14/check_disc.py (GATE_VER R133)
  Row table:       lead/next_re_20261117_r14/DISC_RECHECK.tsv  (31 data rows, 7 columns, LF only)

HARD RULES
  - Never modify anything under lead/. Read only. Write only under _r134/sub_deepseek/
    with filenames starting with r134ds_ .
  - Do not copy the R14 tree with copytree: it is 811 MB and will fill tmpfs. If you need a
    sandbox, build it with symlinks and copy only check_disc.py plus DISC_RECHECK.tsv.
    (R133 lost a whole control run to exactly this mistake.)
  - Scripts must have a timeout. Report the exit code you measured, never the one you expect.
  - Use python3 with only stdlib plus what is already installed. No network.

BACKGROUND YOU SHOULD VERIFY, NOT ASSUME
  The gate has a block called C7 that runs each row's column 6 check expression against the
  file named in column 5. It classifies each expression by its FIRST TOKEN
  (grep= / grepcount= / rows= / exists / bytes= / none) and a second block C7b pins the
  census of those six shape counts at {'grep=':24,'grepcount=':3,'rows=':4,
  'exists':0,'bytes=':0,'none':0}, failing on drift.

TASKS

  T1. Reproduce the baseline. Run the gate unmodified. Report its exit code and the full
      list of any FAIL lines. Confirm the row count is 31 and the file is LF-only.

  T2. HOLE A - column 5 is not pinned by anything.
      For each of the 31 rows, compute the SET of column-5 candidate files (drawn from the
      23 distinct column-5 paths present in the table) for which that row's column-6
      expression would still evaluate TRUE. Report every row whose set has size >= 2, with
      the set contents. Then pick one such row, point its column 5 at a DIFFERENT member of
      its own set, and run the gate in a sandbox. Report the measured exit code.
      State plainly: can a row's product be silently redirected to another file while the
      gate stays green?

  T3. HOLE B - column 6 is not pinned beyond its first token.
      In a sandbox, take one row and append an alternation to its column 6 expression that
      can never fail, for example grep=(?m)^SOMETHING ·|(?m:^) . Run the gate. Report the
      measured exit code and any FAIL lines. Then independently prove the appended branch
      really is vacuous: show that on a completely empty temp file the ORIGINAL expression
      returns no hits while the AUGMENTED expression returns >= 1. Report both numbers.
      State plainly: can any row's check expression be made unconditionally true while the
      gate stays green?

  T4. NEGATIVE CONTROL for T2/T3 - prove the gate is not simply broken.
      (a) Change a row's column 6 first token from grep= to EXISTS . Report the exit code
          and whether a C7b line appears.
      (b) Change a row's column 5 to a file for which its expression is FALSE. Report the
          exit code and whether a C7 line appears.
      If either of these fails to go red, the gate is broader than claimed and you must say so.

  T5. VAQUITY CHECK on the existing 31 expressions. For every row with a regex expression
      (grep= or grepcount=), test whether the pattern matches the EMPTY STRING under re.M.
      Report the count of nullable patterns. The claim to check is that the number is 0,
      i.e. no existing row is already vacuously true. Also report, for each row, how many
      of the 23 candidate files its expression would match (a hit count of 23 would mean
      the expression is insensitive to which file it is pointed at).

  T6. Proposed fix under review. Do not implement it; evaluate it.
      FIX-1 (structural, no new counters): when parsing column 6, refuse any regex that
        matches the empty string, and refuse any grep= whose hit count on its own product
        is not exactly 1 in a way that the gate reports. The point is that a pattern which
        can match empty can never distinguish one product from another, so it must not be
        accepted as a check at all.
      FIX-2 (pin the object, not a counter): pin a sha256 fingerprint over the
        (id, column5, column6) triple for all 31 rows, in the same style as the existing
        C14 fingerprint of (id, col2, col3, col4). Any edit to either column then requires
        re-pinning the constant deliberately.
      For each of FIX-1 and FIX-2, answer:
        (i)   does it actually close HOLE A, HOLE B, both, or neither? Give the reasoning.
        (ii)  does it break any of the 31 existing rows? Concrete check, not opinion.
        (iii) what does it cost to run (measure wall time, do not guess)?
        (iv)  what does it still NOT protect against? Be specific and adversarial.
      Then say which single fix you would ship if you could ship only one, and why.

  T7. Report any OTHER hole you find in C7/C7b that this card did not name. If you find
      none, say none - do not manufacture one.

WHAT TO RETURN
  A short report, one line per task, with the number you measured and the command you used.
  Put DISAGREEMENTS first. Do not restate this card. Do not pad. If a claim is true only
  under a narrower scope than stated, say so and give the narrower scope.
  End with a single line: SHIP = FIX-1 or FIX-2 or NONE, then one sentence of justification.

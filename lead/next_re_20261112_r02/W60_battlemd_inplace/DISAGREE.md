# W60 · DISAGREE.md

1. **The generic content-conflict exemption for the inplace TARGET file.**
   v14 preinstall_plan() treated an unrecorded loose BATTLEMD.INI as a definite
   content conflict (strict refusal). For battlemd.mode=inplace that file IS the
   intended rewrite target, so W60 exempts ONLY the row (name == 'BATTLEMD.INI'
   AND plan is inplace) from that generic wording, and replaces it with the
   STRICTER RI.inplace_preflight(): official-baseline sha equality + orphan .bak
   check (exit 33/34) BEFORE any write. Every OTHER file keeps the v14 conflict
   rule verbatim (install.py:1412-1432). If Lead reads 'content-conflict 预检
   全部保持原语义' as forbidding even this target-specific replacement, the
   alternative is to pre-register the official file in the manifest (not
   implementable on a fresh install) -- W60's reading is that a stronger gate
   replacing a mis-applied one is not a weakening. Measured: INPLACE4 (orphan
   .bak refused), INPLACE5 (K2 still hard), INPLACE6 (append isolation).
2. **'In-place rewrite' is implemented as build-time byte-exact generation +
   install-time REPLACE to the SAME path, not as an in-process edit of the live
   file's bytes.** Mechanism-wise these are equivalent for the acceptance
   criteria (same path, no new BATTLEMD*.INI file, no cross-file duplicate id,
   byte-exact backup/restore). The build uses the bundled official baseline,
   hence the exit-33 content-consistency precheck. An alternative (install reads
   the live file, edits [SOV1], writes back) would tolerate a non-standard
   official file but would need a new write primitive and a larger change
   surface; W60 chose the smaller, fully-journaled v14 REPLACE path.
3. **verify was NOT extended with a backup-existence assertion.** The card's
   verify requirement (detect drift vs the manifest's post-install sha256) is
   already met by v14's per-file sha256 check and is measured in INPLACE3.
   Adding a new verify assertion would have changed verify.py, contradicting
   S4_8f's 'no other guard weakened/unchanged' invariant. Detection of a
   DELETED backup is documented in INPLACE_MODE.md §4 instead of being silently
   claimed as implemented.
4. **Route (b) BATTLEMD98.INI append is NOT deleted from the product.** W60 only
   isolates the modes: append still ships BATTLEMD98.INI, inplace ships
   BATTLEMD.INI. [转引] LEAD_VERIFY_W37 §2.3 judges (b) not engineering-feasible
   for the 'borrow official id' goal; W60 does not re-litigate that and does not
   remove the append capability (INPLACE6 measures the isolation).
5. **S4_7 / S4_8 assertions were adapted, not silently dropped.** S4_7 asserted
   the D5.2 exit-25 refusal; after the unfreeze it asserts SUPPORTED +
   run_resolve no longer refuses + W60 build emits BATTLEMD.INI. S4_8e/f now
   compare v14->v15 (local baseline copy) instead of v13->v14. Case COUNT is
   unchanged (90 inherited); only the 6 NEW INPLACE cases change the total.
6. [转引] D5.2 unfreeze does NOT overturn D6 (LEAD_RULING §2.5). W60 makes no
   claim about g3 reachability beyond the offline capability.
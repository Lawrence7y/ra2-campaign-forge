# done (W84 complete, 2026-11-14T11:26+08:00)

- [x] bootstrapped STARTED/HEARTBEAT/PROGRESS/EVIDENCE

- [x] toolchain written: w84_lib/offline/finalize (card copies of W83c, re-pointed), w84_common/build/run hand-written; designs: df (1x Russian TESLA vs 30 British MTNK Hunt, NO win objective -> auto AllDestroyed->Loser) + wv (survive(5) win control)
- [ ] offline build

- [x] offline build OK: df+russian_tesla=1/british_mtnk=30 hunt=30/loser ,2,0,8 + event ,11,0,8 present, no win trigger; wv survive(5)
- [ ] offline install df (FRESH)

- [x] offline install df OK (FRESH robocopy 647 files, pristine 21, verify exit 0); rules probe OK
- [ ] trip_df1 (defeat)

- [x] trip_df1: TASK_FAILED_DEFEAT_RESTART_DIALOG ok=True - dialog captured (controls+crop+memory text 任務失敗 banner; frame 274; never clicked; no_extra_start=True)
- [ ] trip_wv1 (win control)

- [x] trip_df2: reproduced defeat_restart_dialog (frame 274, same controls), ok=True
- [x] trip_wv1: victory_score_screen classified correctly (frame 165 = 15x5+90); ok=False benign race (score screen self-exit at t=54.7 < 60s window)
- [ ] trip_wv2 (clean win control, VICTORY_MIN_SEC=20)

- [x] trip_wv2: victory_score_screen + clicked Continue + no_extra_start=true (frame 165)
- [x] trip_wv3: victory_score_screen again (self-exit race at t~12.6; classification correct)
- [x] finalize: BATTLEMD.INI byte-restore 2733B 7e40691a==official==pristine==real PRE/POST; sandbox identical_tree=True (game .sav dropped); REAL identical_tree=True mtime_diff=0; sandbox deleted; lock owner=lead; residual 0
- [x] reports: DEFEAT_DIALOG_SAMPLE.md / UNKNOWNS.md / DISAGREE.md / REAL_DIR_PROOF.txt / EVIDENCE\phases_stdout.md

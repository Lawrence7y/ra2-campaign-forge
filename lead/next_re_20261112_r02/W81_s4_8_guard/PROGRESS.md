# done

## 夹具与脚本就绪
- W77 脚本 x4 + TRACK_B_gates.json + s1_revision + baseline_v14(23 files) + ra2forge_patched_v16b(26 files) 已复制
- s4_cases.py: rglob 恢复全包 x2, expected_added + docs/ONE_PACKAGE_AT_A_TIME.md
- regress_dlc_v16.py: W43_ROOT_NAME=W81_s4_8_guard, V12_ROOT=ra2forge_patched_v16b
- 下一步: S4_8 sanity -> STRAY 反向验证 -> 全量 97

## 完成
- S4_8 sanity: 首跑 FAIL(expected_added 顺序) -> 修正字典序 -> 7/7 PASS
- 反向验证: STRAY.txt -> S4_8e FAIL(EXIT=1, added 精确点名 STRAY.txt); 移走 -> EXIT=0
- 全量: 97/97 cases, 844 assertions, exit 0, Traceback=0
- 交付: S4_8_GUARD_FIX.md / UNKNOWNS.md / DISAGREE.md / out\(108 files)
# done

#!/usr/bin/env bash
# verify_kit selftest -- negative controls for all four tools.
#
# usage:  bash tools/verify_kit/selftest/run_selftest.sh <scratch_dir>
#
# Runs every negative control from VERIFY-KIT01 in a scratch directory and
# prints one PASS/FAIL line per assertion, then a final SELFTEST verdict.
# Exit code 0 only if every assertion passes.
set -u
export PYTHONDONTWRITEBYTECODE=1
KIT="$(cd "$(dirname "$0")/.." && pwd)"
S="${1:?usage: run_selftest.sh <scratch_dir>}"
# Pin the child-shell identity for run_rc-spawned commands: a bare "bash"
# resolved through Windows PATH may be WSL bash, not this shell.
if command -v cygpath >/dev/null 2>&1; then
  BASH_EXE="$(cygpath -w "$(command -v bash)")"
else
  BASH_EXE="$(command -v bash)"
fi
rm -rf "$S"
mkdir -p "$S"
fail=0
ok()  { printf 'PASS: %s\n' "$1"; }
bad() { printf 'FAIL: %s\n' "$1"; fail=1; }
expect_eq() { [ "$2" = "$3" ] && ok "$1" || bad "$1 (expected=$2 actual=$3)"; }
expect_grep() { grep -q -- "$2" "$3" && ok "$1" || bad "$1 (pattern '$2' not found in $3)"; }
py() { python -B "$@"; }

echo "== kit = $KIT  scratch = $S =="

# --- NC-1: snapshot+diff must DETECT a write -----------------------------
mkdir -p "$S/nc1_seed"
printf 'alpha\n'   > "$S/nc1_seed/a.txt"
printf 'bravo\n'   > "$S/nc1_seed/b.txt"
printf 'charlie\n' > "$S/nc1_seed/c.txt"
py "$KIT/snapshot.py" "$S/nc1_seed" --out "$S/nc1_pre.json"  >/dev/null
printf 'alpha2\n' > "$S/nc1_seed/a.txt"   # content change
touch     "$S/nc1_seed/b.txt"             # mtime only
rm        "$S/nc1_seed/c.txt"             # removal
printf 'delta\n'  > "$S/nc1_seed/d.txt"   # addition
py "$KIT/snapshot.py" "$S/nc1_seed" --out "$S/nc1_post.json" >/dev/null
py "$KIT/diff_snapshot.py" "$S/nc1_pre.json" "$S/nc1_post.json" > "$S/nc1_diff.txt"
rc=$?
expect_eq    "NC-1 diff rc==1 when writes happened" 1 "$rc"
expect_grep  "NC-1 verdict WRITES-DETECTED"  "VERDICT: WRITES-DETECTED" "$S/nc1_diff.txt"
expect_grep  "NC-1 counts ADDED=1"           "^ADDED: 1$"               "$S/nc1_diff.txt"
expect_grep  "NC-1 counts REMOVED=1"         "^REMOVED: 1$"             "$S/nc1_diff.txt"
expect_grep  "NC-1 counts CONTENT_CHANGED=1" "^CONTENT_CHANGED: 1$"     "$S/nc1_diff.txt"
expect_grep  "NC-1 counts MTIME_ONLY=1"      "^MTIME_ONLY: 1$"          "$S/nc1_diff.txt"

# --- NC-2: untouched seed must report zero-writes -------------------------
mkdir -p "$S/nc2_seed"
printf 'one\n' > "$S/nc2_seed/1.txt"
printf 'two\n' > "$S/nc2_seed/2.txt"
py "$KIT/snapshot.py" "$S/nc2_seed" --out "$S/nc2_pre.json"  >/dev/null
py "$KIT/snapshot.py" "$S/nc2_seed" --out "$S/nc2_post.json" >/dev/null
py "$KIT/diff_snapshot.py" "$S/nc2_pre.json" "$S/nc2_post.json" > "$S/nc2_diff.txt"
rc=$?
expect_eq   "NC-2 diff rc==0 when untouched" 0 "$rc"
expect_grep "NC-2 verdict zero-writes" "VERDICT: zero-writes" "$S/nc2_diff.txt"

# --- NC-2b: mtime-only touch still zero-writes but is flagged ------------
touch "$S/nc2_seed/1.txt"
py "$KIT/snapshot.py" "$S/nc2_seed" --out "$S/nc2b_post.json" >/dev/null
py "$KIT/diff_snapshot.py" "$S/nc2_pre.json" "$S/nc2b_post.json" > "$S/nc2b_diff.txt"
rc=$?
expect_eq   "NC-2b mtime-only keeps rc==0" 0 "$rc"
expect_grep "NC-2b verdict zero-writes"  "VERDICT: zero-writes" "$S/nc2b_diff.txt"
expect_grep "NC-2b mtime-only flagged"   "^MTIME_ONLY: 1$"      "$S/nc2b_diff.txt"

# --- NC-3: boundary_scan must HIT an implanted forbidden API --------------
cat > "$S/dirty_fixture.py" <<'FIXTURE'
import ctypes
k = ctypes.windll.kernel32
k.WriteProcessMemory(0, 0, 0, 0, 0)
k.VirtualAllocEx(0, 0, 0, 0, 0)
FIXTURE
py "$KIT/boundary_scan.py" "$S/dirty_fixture.py" > "$S/nc3_scan.txt"
rc=$?
expect_eq   "NC-3 dirty fixture rc==1" 1 "$rc"
expect_grep "NC-3 verdict FINDINGS"    "VERDICT: FINDINGS" "$S/nc3_scan.txt"

# --- NC-4: clean fixture must be CLEAN (negative control) -----------------
cat > "$S/clean_fixture.py" <<'FIXTURE'
import os
print(os.path.join("a", "b"))
FIXTURE
py "$KIT/boundary_scan.py" "$S/clean_fixture.py" > "$S/nc4_scan.txt"
rc=$?
expect_eq   "NC-4 clean fixture rc==0" 0 "$rc"
expect_grep "NC-4 verdict CLEAN"       "VERDICT: CLEAN" "$S/nc4_scan.txt"

# --- NC-5: self-exclusion works AND is not a no-op ------------------------
py "$KIT/boundary_scan.py" "$KIT/boundary_scan.py" > "$S/nc5_masked.txt"
rc=$?
expect_eq   "NC-5 self-scan masked rc==0"   0 "$rc"
expect_grep "NC-5 self-scan masked CLEAN"   "VERDICT: CLEAN" "$S/nc5_masked.txt"
py "$KIT/boundary_scan.py" --no-self-exclude "$KIT/boundary_scan.py" > "$S/nc5_unmasked.txt"
rc=$?
expect_eq   "NC-5 self-scan unmasked rc==1" 1 "$rc"
expect_grep "NC-5 self-scan unmasked FINDINGS" "VERDICT: FINDINGS" "$S/nc5_unmasked.txt"

# --- NC-6: run_rc records a real failure (exit 3) independently -----------
py "$KIT/run_rc.py" --out "$S/nc6" -- "$BASH_EXE" -c "echo boom; exit 3"
rc=$?
expect_eq "NC-6 run_rc rc==3 (pass-through)" 3 "$rc"
expect_eq "NC-6 .exitcode file says 3" "3" "$(cat "$S/nc6.exitcode")"
expect_grep "NC-6 child output captured" "boom" "$S/nc6"
if grep -q "__EXIT_CODE" "$S/nc6"; then bad "NC-6 no __EXIT_CODE embedded"; else ok "NC-6 no __EXIT_CODE embedded"; fi

# --- NC-7: run_rc success path --------------------------------------------
py "$KIT/run_rc.py" --out "$S/nc7" -- "$BASH_EXE" -c "echo hello; exit 0"
rc=$?
expect_eq "NC-7 run_rc rc==0" 0 "$rc"
expect_eq "NC-7 .exitcode file says 0" "0" "$(cat "$S/nc7.exitcode")"
expect_grep "NC-7 child output captured" "hello" "$S/nc7"

if [ "$fail" = "0" ]; then
  echo "SELFTEST: PASS"
else
  echo "SELFTEST: FAIL"
fi
exit "$fail"

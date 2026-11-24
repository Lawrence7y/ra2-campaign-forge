# W44 C-line E2E - full re-run entry point (PowerShell)
# Prerequisites: WinSta0\Default interactive desktop, no gamemd residual,
#                .game_instance.lock owner=lead, Python 3.12 + pywin32 + Pillow.
# The whole card is re-runnable; every phase writes its own out/<tag>.ndjson.
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$t = Join-Path $here 'tools'
$lock = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\.game_instance.lock'

function Run-Phase($name, $script) {
  Write-Host "=== PHASE $name ===" -ForegroundColor Cyan
  python -u -B -X utf8 (Join-Path $t $script)
  $code = $LASTEXITCODE
  Write-Host "PHASE $name EXIT=$code" -ForegroundColor $(if ($code -eq 0) {'Green'} else {'Red'})
  if ($code -ne 0) { throw "phase $name failed with exit $code" }
}

try {
  Run-Phase '0 desktop precheck'  '_bootstrap_lib.py'   # also regenerates w44_lib.py
  # Step-0 desktop precheck itself is a 30 s PowerShell probe (see card §0).
  # It is reproduced by w44_phase_prep.py's residual guard + each live phase's
  # live_lib.desktop_precheck (records window_station/thread/input desktop).
  Run-Phase '1 prep'              'w44_phase_prep.py'
  Run-Phase '2 build'             'w44_phase_build.py'
  Run-Phase '3 install'           'w44_phase_install.py'
  Run-Phase '4a live run K1'      'w44_phase_run.py'
  # NOTE: after K1, run w44_fix_record.py ONLY if a heal() version that still
  # restored ra2forge_install.json was used. Current w44_common.heal() no
  # longer touches the install record, so this is a no-op safety net.
  Run-Phase '4b live load K2'     'w44_phase_load.py'
  Run-Phase '4c CSF control arm'  'w44_phase_csf_control.py'
  Run-Phase '5a uninstall'        'w44_phase_uninstall.py'
  Run-Phase '5b restore proof'    'w44_phase_restore_proof.py'
}
finally {
  Write-Host '=== FINALIZE (always runs: heal + real_post + lock release) ===' -ForegroundColor Yellow
  python -u -B -X utf8 (Join-Path $t 'w44_finalize.py')
  Write-Host "FINALIZE EXIT=$LASTEXITCODE"
  Get-Content $lock -Raw
}

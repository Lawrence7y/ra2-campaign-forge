"""V5 driver (W24 copy, unchanged from W23): install a package with an
injected mid-install write failure.

Usage: python v7_fail_driver.py <package_dir> <game_dir> <fail_at_name> [patched_root]

Monkeypatches ra2forge.install._copy_verified so the copy of <fail_at_name>
raises OSError after the preceding steps already committed. Everything else is
the real production code path. fail_at == "@record" injects the failure into
the manifest write instead (_stage_text_and_replace), which is the LAST write
- the rollback then has to undo the orphan exits as well.

W24 copy: patched_root defaults to this card's ra2forge_patched_v7i
(byte-identical to W23's v7). Kept so the copied 22-case suite runs
self-contained in this card; the NEW @seal injection lives in
v7i_seal_fault_driver.py next to this file.
"""
import os
import sys

package, game, fail_at = sys.argv[1], sys.argv[2], sys.argv[3]
patched_root = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ra2forge_patched_v7i")
sys.path.insert(0, os.path.abspath(patched_root))

from ra2forge import install as inst  # noqa: E402

print("using install module:", inst.__file__)
real = inst._copy_verified
calls = {"n": 0}


def broken(src, dest, name):
    calls["n"] += 1
    if name == fail_at:
        raise OSError(f"simulated mid-install write failure (injected at copy #{calls['n']}: {name})")
    return real(src, dest, name)


inst._copy_verified = broken

if fail_at == "@record":
    def broken_record(text, dest, what):
        raise OSError("simulated manifest-write failure (injected at _stage_text_and_replace)")

    inst._stage_text_and_replace = broken_record

try:
    report = inst.install_package(package, game, allow_content_conflict=True)
    print("UNEXPECTED SUCCESS — failure was not injected:")
    for a in report["actions"]:
        print("  " + a)
    sys.exit(2)
except Exception as exc:  # noqa: BLE001 - driver must print whatever escapes
    print(f"install failed as expected (exit 1). exception type: {type(exc).__name__}")
    print("--- exception message ---")
    print(str(exc))
    print("--- end exception message ---")
    sys.exit(1)

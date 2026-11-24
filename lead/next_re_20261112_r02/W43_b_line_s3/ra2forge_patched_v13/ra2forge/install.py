"""Install / uninstall a built campaign package into a Yuri's Revenge directory.

Packaging contract (FORGE-1 plan B):
- BATTLEMD98.INI stays a LOOSE file: the engine enumerates the battle lists with
  FindFirstFileA("BATTLEMD*.INI") over the FILESYSTEM (VA 0x52CBA0 -> IAT
  0x7E1208, fallback "BATTLEMD.INI" at 0x826198/0x52CCCD) and merges the entries
  by battle id (0x46CE10), so a copy packed inside a MIX is never seen. The
  official BATTLEMD.INI is never written to by an install. [更正 2026-10-04 ·
  依据 A-69 AS-01] 'never written to by this tool' was only true of installs:
  'uninstall --legacy' restores the pre-override original INTO that slot, and
  --drop-legacy-battlemd moves the override out of it. Both are deliberate,
  gated, and printed as actions.
- expandmd98.mix carries maps only (no INI anywhere inside).
- Every file this module replaces is first copied to <name>.ra2forge.bak and
  recorded in ra2forge_install.json, so uninstall() restores the exact bytes.
  [更正 2026-10-04 · 依据 A-69 AS-02] except an adopted file: a slot that
  already holds the package's own bytes and is not listed in the record gets no
  backup slot - preinstall_plan says so in a notice, because uninstall will
  delete a file it never backed up.

Safety rules (DLC-STRICT01):
- ZERO-WRITE PREFLIGHT: the whole install is planned and classified read-only
  before the first byte is written. If the preflight refuses, install_package()
  raises InstallBlocked (an OSError) and the file system is left untouched.
- strict mode is the DEFAULT. Findings are reported in three separate classes:
  * definite content conflicts (a foreign file would be overwritten) - refused
    in strict mode; escapable ONLY via allow_content_conflict=True, and every
    released conflict is printed and recorded in the manifest;
  * unresolvable risks (state that cannot be judged reliably, e.g. a legacy
    ra2forge override of BATTLEMD.INI) - refused in strict mode; resolve the
    state instead (usually 'uninstall --legacy');
  * plain notices (normal install states - an official BATTLEMD.INI is one) -
    never block.
- the escape hatch covers CONTENT CONFLICTS ONLY: path-safety violations, a
  corrupt ra2forge_install.json and backup-slot protection are never bypassed;
- only the game directory passed on the command line is ever touched;
- an existing backup slot is never overwritten (the oldest original wins);
  [更正 2026-10-04 · 依据 A-69 AS-04, F-1] this used to hold only for a slot
  that was already there: an alias planted at <name>.ra2forge.bak after the last
  preflight check was swapped away by the staged backup write without a word.
  The write now refuses its own landing slot, so "never overwritten" covers the
  window too.
- uninstall() deletes only files whose sha256 still matches what was installed,
  so a file the user edited afterwards is preserved (unless force=True).

Safety rules (DLC-HIGH1-FIX01):
- a destination slot that is a symbolic link, or any alias resolving to a
  different name (inside or outside the game directory, hard links included),
  is a HARD blocker - never releasable by allow_content_conflict;
- uninstall() re-verifies the slot identity before removing it and again
  immediately before a restore write, and never claims a restore it did not
  perform (the backup slot is kept for manual recovery instead);
  [更正 2026-10-04 · 依据 A-69 AS-07, A-70 L-4] both halves were weaker than
  they read. Before removing, uninstall ran a two-form check (symbolic link /
  not a regular file) while install ran five, and the pre-restore "check" only
  asked whether the slot was empty. Before removing it now runs
  _dest_safety_error, the backup slot it consumes runs _bak_safety_error, and
  the restore write itself re-runs the derived-name criteria on its landing
  slot at the instant it commits.
- the package sources are re-checked for drift right before the first write,
  and every main copy is read back and verified before the manifest is
  written, so the install record always describes the bytes actually shipped.

Safety rules (DLC-HIGH2-FIX01):
- the backup slot <name>.ra2forge.bak passes the SAME identity checks as the
  destination slot (_bak_safety_error): a symbolic link there - dangling links
  included, they are NOT an empty slot - a hard link, or any non-regular file
  is a HARD blocker, never releasable by allow_content_conflict. The check
  runs in the preflight AND again immediately before the backup write, so an
  alias swapped into the preflight->write window is refused (TOCTOU);
  [更正 2026-10-04 · 依据 A-69 AS-09, F-1] the second half of that sentence was
  not true of the shipped code until now: the last backup-slot check ran in
  install_package()'s pre-write loop, i.e. before the FIRST write, while the
  write that consumes the slot is a later _write_step(). _write_step now runs
  _bak_safety_error itself, and _stage_and_replace re-runs the same criteria on
  its landing slot at the moment it commits.
- the backup bytes are staged with O_CREAT|O_EXCL inside the game directory
  and moved onto the slot with os.replace(), which swaps the directory entry
  instead of following a name, so the oldest original can never be diverted
  outside the game directory by a link planted in the residual race window;
- uninstall() applies the install-side name discipline to the record it reads
  (no separators, backup must be the slot this tool writes), refuses to read
  a backup through an alias, stages the restore the same alias-proof way, and
  keeps the install record whenever it refused an entry - deleting the record
  on a partial refusal orphaned the very backup slots it pointed at;
- the install record itself is never read or written through an alias: a
  ra2forge_install.json that is a symbolic link is a hard blocker.

Safety rules (DLC-HIGH3-FIX01) - the family above was not finished: the gates
covered the names the card named, and not the names DERIVED from them:
- every name this tool derives from a slot - the staging name, the install
  record, the removed-original backup - now passes the same identity criteria
  as the slot itself (symbolic link, lexists, real path landing on itself
  inside the game directory, non-regular file, hard link). HIGH-3 and HIGH-4
  were one miss seen twice: <slot>.ra2forge-stage and the record path were
  checked by none of the gates, so an alias planted on a derived name was
  invisible to all of them;
- O_CREAT|O_EXCL is NOT a link guard on Windows and must not be relied on as
  one: on a LIVE link it fails with FileExistsError, on a DANGLING reparse
  point it succeeds and creates the link's target (measured directly). The
  staging name therefore carries an unpredictable suffix (secrets.token_hex)
  so it cannot be occupied in advance, and is refused with lstat-class checks
  immediately before os.open(); O_EXCL is the backstop, not the guard. The
  check-then-act window itself is not eliminated - a writer that can create
  files in the game directory at an arbitrary instant can still name one we
  have not chosen yet only by guessing a 64-bit random value;
  [更正 2026-10-04 · 依据 A-69 AS-12] "only by guessing" was true of the
  staging name and of nothing else: the landing names are deterministic
  (<slot>.ra2forge.bak, ra2forge_install.json, <slot>.ra2forge.removed.bak), so
  that sentence described the narrowest window in this module as if it were the
  only one. What a writer planting one of those deterministic names gets away
  with changed: it used to be a silent swap of the planted alias by os.replace,
  and now it is a refusal, because the primitive re-checks its own landing slot
  at the instant it commits. The random value is still what protects the staging
  name; nothing about the landing names is unpredictable.
- every content copy in this module goes through the one staged, alias-proof
  primitive: the backup write, the restore writes, the MAIN COPY (MEDIUM-8: it
  was shutil.copy2(), which follows an alias at the destination) and the
  install record (HIGH-4: it was Path.write_text(), the same mechanism).
  [更正 2026-10-04 · 依据 A-69 AS-13/AS-14, F-2] the sentence that used to end
  this bullet - "the legacy removed-original move is a rename, which does not
  follow an alias" - was false twice over, and it was the sentence that let the
  last non-staged byte landing in this module stay. That write was
  shutil.move(), which is not os.rename: on a landing name that is a symlink to
  a directory it renames the SOURCE INTO that directory (measured: the bytes
  left the game directory, the link stayed, move returned normally and the
  action line "removed BATTLEMD.INI (moved to …removed.bak)" was printed about a
  name that was still a link); when os.rename fails it falls back to copy2 plus
  unlink, and copy2 follows the alias; and even the rename branch itself turned
  out to write THROUGH a live link to a file here. os.replace - what the
  primitive commits with - was re-measured over six shapes and never wrote
  outside. The removed-original move goes through the primitive now, so "every
  content copy in this module" is true of install.py as shipped; it does not
  reach ra2forge/cli.py, whose `example` subcommand still writes a user-named
  path outside any game directory.
- install_package() re-verifies the install record's identity in the pre-write
  re-verification loop, so the record is gated in the same window as the two
  slots, and its write is staged;
  [更正 2026-10-04 · 依据 A-69 AS-* / F-3] "in the same window as the two
  slots" was not: that loop runs before the FIRST write, and the record is
  written after the whole write loop, so an alias planted at
  ra2forge_install.json during the loop was swapped away by the staged record
  write instead of refused. The gate that belongs to the record now runs inside
  the record write, at the instant it commits. install_package() itself still
  contains no raise after the first write (the invariant the verifier's S1'
  assertion and this module's own comment both pin).
- uninstall() judges the record's identity BEFORE reading it (LOW-8: it used to
  follow the alias into the parser and refuse only afterwards).

Safety rules (DLC-UNINSTALL-LEGACY01):
- the legacy uninstall path (_uninstall_legacy: ra2forge <= FORGE-1 artefacts)
  applies the SAME gates as the rest of this module - no legacy-specific
  criteria: the legacy record ra2forge_uninstall.txt is never read or consumed
  through an alias (a live link must not drive the deletion set; a dangling
  link is NOT "no record", so the whole legacy pass is refused instead of
  falling back);
  [更正 2026-10-04 · 依据 A-70 H-1, L-5, A-69 F-4] "no legacy-specific criteria"
  was contradicted by the code it described: this record was gated by two forms
  (is_symlink / exists-not-is_file) while the install record was gated by five,
  and a HARD link is invisible to both of the two - so the weaker set WAS the
  legacy-specific criterion, and an aliased legacy record drove the deletion
  set through a shared inode. The legacy record and the fallback read of
  BATTLEMD.INI now call _derived_slot_error, the same function the install
  record's _record_slot_error is.
- every listing entry is validated by _dest_safety_error before anything is
  touched (plain file name, no separators, no '..', resolves to itself inside
  the game directory, never a link / hard link / directory, never a
  backup-namespace name, never the live install record), so a hand-edited
  legacy record cannot delete anything outside the game directory;
  [更正 2026-10-04 · 依据 A-70 H-2] "never the live install record" was tested
  with `name == MANIFEST_NAME`, an exact case-sensitive comparison on a volume
  that ignores case and strips trailing dots and spaces: RA2FORGE_INSTALL.JSON
  and "ra2forge_install.json." are that same directory entry, passed the guard,
  and deleted the record. Entries are compared by the directory entry they
  address now, and the legacy record protects itself the same way.
- a backup slot is consumed only after _bak_safety_error accepts it and BEFORE
  the recorded file is deleted, so a refused entry leaves the game directory
  byte-identical; every restore write goes through _stage_and_replace
  (staged, sha-checked, os.replace - never follows an alias);
  [更正 2026-10-04 · 依据 A-69 AS-24, F-8] true of the restore writes and false
  of the one remaining move: the removed-original copy was shutil.move. It goes
  through the same primitive now, so "every" covers it, and the "removed …"
  action line is only printed after the staged copy AND the removal of the
  original slot both completed - this module does not claim an action it did
  not perform.
- BATTLEMD.INI.ra2forge.removed.bak is never overwritten (the oldest original
  wins, same rule as the backup slots);
  [更正 2026-10-04 · 依据 A-69 AS-18, F-2] this held for every shape that was
  already there and not for one planted between the check and shutil.move,
  whose copy2 fallback would have overwritten whatever that alias pointed at,
  outside the game directory.
- the legacy record is kept whenever any entry was refused (MEDIUM-7), so the
  unresolved state stays visible and a later 'uninstall --legacy' can retry.
  [更正 2026-10-04 · 依据 A-70 M-3, I-6] two paths still got the record deleted
  with unresolved state: an entry whose file was gone while its backup slot was
  not was skipped without setting refused (the slot orphaned, which is exactly
  the state MEDIUM-7 exists to keep visible), and an entry naming the legacy
  record itself deleted it under the loop and then raised FileNotFoundError at
  the end of the pass, turning a finished run's exit 0 into exit 1.

Safety rules (DLC-HARDEN4-FIX01) - the fourth time this family was found by
static review of the whole write set rather than by the card that owned the
previous fix. Everything below is a defect in the code as shipped by
DLC-HIGH3-FIX01 / DLC-UNINSTALL-LEGACY01, both of which self-declared their
family closed:
- no write in this module commits onto a slot it has not just re-checked. The
  five identity criteria travel with the write: _stage_and_replace and
  _stage_text_and_replace run _derived_slot_error on their own landing slot
  immediately before os.replace(), and _write_step runs _bak_safety_error in
  front of the backup write. Gates that sit a write loop away from the write
  they guard are not TOCTOU gates, whatever the comment said;
- a deterministic landing name is allowed only with a refusal at the instant of
  the write. <slot>.ra2forge.removed.bak stays exactly that name on purpose -
  the oldest-original-wins rule, cli.py's documented name and the criteria
  above all key on it, so an unpredictable suffix would delete the protection
  instead of narrowing a window. What closes the window is that the write is
  staged: os.replace swaps the directory entry and refuses the slot;
- shutil.move is not usable here and the reason is measured, not quoted: the
  rename branch follows a live link to a file, the isdir branch relocates the
  source into a linked directory and returns normally, and the OSError branch
  falls back to copy2, which follows an alias (raw/10_move_probe.txt). os.replace
  does none of these across six shapes (raw/12_replace_probe.txt);
- the two records are the same directory entry as any spelling of them. Record
  protection compares entries (case, trailing dots and spaces normalised), not
  strings, and covers the legacy record as well as the install record;
- uninstall()'s own slots got the criteria the legacy path already had: the
  recorded slot before removal and the backup slot before it is read are judged
  by _dest_safety_error / _bak_safety_error (five forms each), not by the
  two-form inline checks that predated them;
  [更正 2026-10-05 · 依据 DLC-HARDEN4-REVIEW02 F-01] "before it is read" was
  true and the sentence still described a weaker order than the legacy path:
  that gate sat BELOW the main loop's dest.unlink(), so a refused backup slot
  was judged after the installed file it named had already been deleted. The
  backup slot is now judged before any removal, in the same order the legacy
  branch uses - "the criteria the legacy path already had" covers the order
  as well as the forms.
- a read that drives no action is disclosed rather than blocked.
  _scan_environment's BATTLEMD.INI read is the one read in this module with no
  gate, deliberately: the engine opens the same name through the same reparse
  point, and this read selects no write and no delete. What it says now names
  the slot it read from when that slot is an alias.

Safety rules (ORPHAN-FIX01) - the A -> A' upgrade path. Measured defect: after
installing A over nothing and then A' (whose package dropped A's map X), X.MAP
stayed in the game directory while the rewritten ra2forge_install.json no
longer named it - uninstall could neither see nor remove it, and the backups a
replacement wrote for files A itself had CREATED held our own previous bytes,
so uninstall "restored" our old version instead of the true original (which
never existed). The fix, judged from the record only:
- preinstall_plan plans the exit of every file the CURRENT record names and
  the new package dropped ("orphans", read-only like everything else):
  * file still matches the recorded sha256 -> ours: removed; when a
    <name>.ra2forge.bak slot is recorded and present, the ORIGINAL the slot
    holds is restored first and the slot is consumed - unless the entry (or
    the slot's absence, see below) proves the slot holds our own previous
    bytes, in which case both are removed;
  * file changed after install -> nobody's to judge: strict mode refuses with
    a risk; non-strict keeps the file and its backup slot, with a warning;
  * malformed or aliased entry names, aliases at the backup slots: hard
    blockers, like every other slot;
- ownership is judged ONLY from the manifest record + the recorded sha256.
  A file the record does not name is never touched; nothing outside the game
  directory is ever deleted;
- the new manifest records ONLY the new package's files; the transition is
  documented under "removed_orphans" (audit trail, not tracked state);
- when a replacement would create a backup for a file the PREVIOUS record
  names and no backup slot existed at preflight, that slot would hold OUR
  previous bytes, not a user original: the new entry is written with
  "original_absent": true, and uninstall() then removes file and slot instead
  of restoring our own version back. Manifests without the flag behave
  exactly as before;
- every copy this install commits is rolled back best-effort when a later
  step fails mid-run (created files unlinked; replaced files restored from
  the backup slot created for them this run, pre-existing slots kept), the
  rollback uses the same staged primitives, and what it did - and what it
  could not do - is reported in the raised error.

Safety rules (PKG-IDENT01) - package identity (RE-N10 item 5). The install
record gains four fields; every identity judgment below reads them, never
the install path:
- package_id: the stable identity of the installed package, declared by the
  package itself in <package>/ra2forge_package.json (written by 'build' when
  the design declares an optional "package": {"id": ..., "version": ...}
  object). It is NOT the install path and NOT the campaign's battle id from
  BATTLEMD*.INI - those are two independent namespaces (the battle id decides
  how the ENGINE merges campaign entries; package_id decides whether the
  INSTALLER treats a directory as this package's own). A package without the
  declaration carries package_id "unknown";
- package_version: the package's own version string, separate from this
  tool's `version` field (which tracks install.py itself, not the content);
- package_digest: SHA-256 over "<name> <sha256-of-package-member>" lines,
  one line per file package_files() ships (BATTLEMD98.INI, then *.MAP sorted,
  then expandmd98.mix), lines sorted by name, joined with "\n", UTF-8. It
  fingerprints exactly the bytes that land in the game directory - build
  reports and readmes are deliberately excluded, so the digest changes iff
  the installed content changes;
- files[].source_package_digest: the package_digest of the package that
  supplied that entry (multi-generation provenance). The new manifest also
  records "supersedes" (the previous record's identity) as audit trail only
  - judgments keep using the per-file record + sha256 discipline above.
Install-time identity judgment (zero-write, BEFORE any re-verification):
- no manifest -> fresh install; all new fields written;
- manifest package_id == this package's declared package_id -> upgrade path
  (ORPHAN-FIX01 exit planning runs as usual);
- manifest package_id declared and DIFFERENT -> refused, kind
  'package_mismatch' (CLI exit 3): this version does not support coexisting
  packages (初版不支持并存). NEVER releasable - not by --force, not by
  --allow-content-conflict, not by --adopt-legacy;
- manifest package_id "unknown" (an old manifest, or one written from an
  unstamped package), OR this package unstamped while the manifest declares
  an id -> refused, kind 'legacy_adopt_required' (CLI exit 4), unless the
  caller passes adopt_legacy=True (--adopt-legacy): the explicit user
  assertion "this install is the intended successor". Adoption treats the
  manifest's recorded files as ours so replacing them is not a content
  conflict; it releases NOTHING else - path safety, corrupt records, backup
  protection and strict risks still gate as before;
- --force has never had any effect on install and gains none: it cannot
  override an identity refusal. On uninstall it still means exactly "delete
  a recorded file whose bytes changed", nothing more.
Backward compatibility (reading v0.3/v0.4/v0.5 manifests): the new fields
are simply absent; missing fields read as "unknown", and uninstall()
ignores them entirely - a manifest without package_id installs nothing
differently and uninstalls byte-identically to the pre-PKG-IDENT behavior.

Safety rules (SEAL-CHAIN01) - the W23 trust chain (W21 UNCOVERED §3). The
manifest is plain-text JSON and uninstall() acts on it, so a hand-edited or
accidentally mangled manifest can silently drive deletions and restores.
This family adds a PROTECTED RECORD, not a signature:

- install writes <game>/ra2forge_install.json.seal right after the record it
  protects: {"kind": "install-seal", "tool_version", "package_id",
  "package_digest", "manifest_sha256", "sealed_at"}, where manifest_sha256
  is SHA-256 over the manifest's CANONICAL bytes (UTF-8, BOM tolerated,
  CRLF/CR normalized to LF). Newline normalization is deliberate: it is the
  only difference a text editor's re-save can make without touching content.
  Every content difference - one edited field, one removed entry,
  re-indented JSON - changes the hash;
- uninstall() gates on the seal BEFORE the first unlink: a seal-era manifest
  (written by tool >= 0.7) whose seal is missing (CLI exit 7) or
  mismatched/corrupt/aliased (CLI exit 8) refuses the WHOLE uninstall -
  nothing removed, nothing restored, record kept. --force does NOT release
  this gate: force means "delete a recorded file whose bytes changed", never
  "trust a record whose seal does not check out". Old manifests (no seal)
  are uninstalled as before, with an explicit degraded-mode warning;
- UNSEAL-FIX01 (tool 0.8): the uninstall's FINAL cleanup step - the seal
  removal - is fault-tolerant: when it fails (read-only seal, open handle)
  the completed uninstall is reported in full (status
  "completed_with_warnings", CLI exit 10, explicit warning naming the stray
  seal and the recovery) instead of escaping as exit 1 with the report
  lost. Tool 0.7 behavior exited 1 there. Normal uninstalls are unchanged
  (writable seal removed silently, exit 0);
- verify (ra2forge/verify.py) reports the same state read-only, plus
  structure, package_digest self-consistency, per-file disk drift and
  ra2forge orphans;
- BOUNDARY, in one sentence: the seal detects ACCIDENTS - it is NOT
  anti-tamper. Whoever can edit the manifest can recompute the seal; nothing
  here claims cryptographic trust, signing or attacker resistance. Recovery
  for an accidentally lost/damaged seal: re-run the install of the SAME
  package (it rewrites the record and a fresh seal), then uninstall;
- a failed install rolls the record back to its exact previous bytes if the
  seal write fails, so an install never leaves a seal-era record standing
  without its seal (the refused-uninstall state) silently.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
from datetime import datetime
from pathlib import Path

MANIFEST_NAME = "ra2forge_install.json"
BACKUP_SUFFIX = ".ra2forge.bak"
STAGE_INFIX = ".ra2forge-stage"
BATTLE_INI = "BATTLEMD98.INI"
MIX_NAME = "expandmd98.mix"
# W34: a loose MAPSELMD.INI in the game directory overrides the copy inside
# ra2md.mix (W29 Q1). It is a WHOLE-FILE override, so v11 ships a complete
# official clone + our appended stages and treats a foreign one as a
# never-releasable definite conflict in the preflight.
MAPSEL_NAME = "MAPSELMD.INI"
# W41: a loose ra2md.csf is a WHOLE-FILE override of the copy inside
# langmd.mix (W29 disk-first). W43/S3 (Lead D1/D2, W40 live arms): a
# MINIMAL/partial CSF makes the OFFICIAL UI TEXT render as MISSING:'...'
# (usability disaster) -- NOT "the game refuses to start": W40 A booted a
# legal minimal CSF in 19.34 s; only a BAD MAGIC (W40 D) fails to start.
# So v12/v13 ONLY ship a complete official-baseline clone
# (builder._emit_csf_artifacts + csf.assert_complete_csf enforce it).
# A foreign loose ra2md.csf is a never-releasable definite preflight conflict,
# exactly like MAPSELMD.INI. Original-absent semantics: the official game dir
# has NO loose ra2md.csf, so install is CREATE and uninstall is DELETE.
CSF_NAME = "ra2md.csf"
LEGACY_MANIFEST = "ra2forge_uninstall.txt"
LEGACY_BATTLE_INI = "BATTLEMD.INI"
FORGE_MARKER = b"Generated by RA2 Campaign Forge"
TOOL_VERSION = "1.0"
# PKG-IDENT01: the per-package identity declaration. Written by 'build' when
# the design carries an optional "package" object; its absence is what makes
# a package (and every manifest installed from it) read as "unknown".
PACKAGE_MANIFEST_NAME = "ra2forge_package.json"
UNKNOWN_PACKAGE_ID = "unknown"
# SEAL-CHAIN01: the protected record next to the manifest. Manifests written
# by tool versions >= SEAL_ERA_VERSION expect it; older manifests are handled
# in degraded mode (warned, never refused on the missing seal).
SEAL_SUFFIX = ".seal"
SEAL_NAME = MANIFEST_NAME + SEAL_SUFFIX
SEAL_KIND = "install-seal"
SEAL_ERA_VERSION = (0, 7)

# ---------------------------------------------------------------------------
# W43 / S3 -- W38-S1 version guard wired to the ACTUAL game-dir write entries.
# ---------------------------------------------------------------------------
# [本次读码] v12/v11 had ZERO build-identity checks: install.py's only guard
# was (game/"gamemd.exe").is_file() in preinstall_plan (L0, C06), and
# uninstall() only checked game.is_dir().  W38-S1 §4 E1/E3 requires the S1
# classify() identity verdict to gate those entries.
# [静态推断] The gate is OPT-IN: it runs ONLY when the caller passes a
# ``version_guard`` context (the new --version-guard switch).  With no switch
# this function is a no-op, so the 57 inherited regression cases and the
# byte-for-byte v12 compatibility are preserved.  Rationale: W38-S1 §3 step 2
# mandates UNKNOWN + NO_ADJUDICATED_BASELINE when no adjudicated BASELINE.json
# exists and §4 denies all game-dir writes under UNKNOWN/MISMATCH; enabling it
# by default would refuse every offline sandbox install.
# Gating the two TOP-LEVEL entries covers every HIGH/CRITICAL descendant row
# in WRITE_ENTRY_AUDIT.tsv (see s3_contract.WRITE_ENTRY_COVERAGE) because the
# private staged-write / rollback / orphan / legacy helpers are reachable only
# through them.
def _s3_guard_gate(entry_id: str, game, version_guard: dict | None) -> None:
    if version_guard is None:
        return                      # default path: byte-identical to v12
    from . import version_guard as _vg
    _vg.guard_write_entry(entry_id, Path(game), version_guard)


def _s3_csf_out_reclassified(csf_out, game_dirs) -> bool:
    """W38-S1 §1.2 path-attribution: realpath+commonpath inside a game dir
    reclassifies the E2b csf-out write point as E1 (install-level)."""
    if not csf_out or not game_dirs:
        return False
    try:
        resolved = Path(csf_out).resolve()
    except OSError:
        return False
    for gd in game_dirs:
        try:
            common = os.path.commonpath([str(resolved), str(Path(gd).resolve())])
            if common == str(Path(gd).resolve()):
                return True
        except ValueError:
            continue
    return False


# SEAL-CHAIN01: distinguishable exit codes for verify and the uninstall seal
# gate (argparse keeps the conventional 2; 1 stays the generic operational
# error; 3/4 are the PKG-IDENT01 install refusals).
EXIT_VERIFY_STRUCTURAL = 5   # manifest structure unusable
EXIT_VERIFY_DIGEST = 6       # package_digest does not match the records
EXIT_SEAL_MISSING = 7        # seal-era manifest, seal file absent
EXIT_SEAL_MISMATCH = 8       # seal present but stale / corrupt / aliased
EXIT_VERIFY_DRIFT = 9        # recorded files changed or missing on disk
# UNSEAL-FIX01 (W25, tool 0.8): uninstall completed its main lifecycle (the
# record was deleted, every recorded file was processed) but the FINAL
# cleanup failed - the install seal could not be removed. Partial
# completion: the report is preserved, status="completed_with_warnings",
# the warning names the stray seal and the recovery. Quoted in uninstall
# --help, VERIFY.md and UNSEAL_FIX.md.
EXIT_UNINSTALL_PARTIAL = 10


class InstallBlocked(OSError):
    """Preflight refused the install; not a single byte has been written.

    kind is one of 'path_safety', 'corrupt_manifest', 'backup_protection',
    'content_conflict', 'risk', 'state_changed'. Only 'content_conflict' is
    ever escapable (via allow_content_conflict=True); every other kind is a
    hard gate.
    """

    def __init__(self, message: str, kind: str = "content_conflict",
                 report: dict | None = None):
        super().__init__(message)
        self.kind = kind
        self.report = report if report is not None else {}


class PackageIdentityBlocked(InstallBlocked):
    """PKG-IDENT01: the identity judgment refused the install before any
    write. kind is one of:
      'package_mismatch'       - the directory holds a DIFFERENT declared
                                 package; coexistence is not supported and
                                 nothing releasable overrides this (CLI exit 3);
      'legacy_adopt_required'  - the identity of one side is undeclared
                                 ("unknown"), so proceeding would be a guess;
                                 pass adopt_legacy=True (--adopt-legacy) to
                                 assert this install is the intended successor
                                 (CLI exit 4).
    Subclasses InstallBlocked so callers that catch InstallBlocked keep
    working; the CLI maps the kinds to distinct exit codes.
    """


class PackageIdentityError(ValueError):
    """PKG-IDENT01: the package's ra2forge_package.json exists but does not
    declare a usable identity. Refusing beats guessing: a malformed identity
    declaration is a hard error, never silently "unknown"."""


def _read_package_identity(package_dir: Path) -> dict:
    """Read <package>/ra2forge_package.json (PKG-IDENT01), read-only.

    Returns {"package_id": <str>, "package_version": <str>, "declared": bool}.
    Without the file the package is UNDECLARED: both fields come back as
    "unknown". With the file, package_id must be a non-empty string and
    package_version (optional) a non-empty string; anything else raises
    PackageIdentityError - a planted-but-garbage identity file must not
    silently read as "no identity".
    """
    path = Path(package_dir) / PACKAGE_MANIFEST_NAME
    if not path.exists():
        return {"package_id": UNKNOWN_PACKAGE_ID,
                "package_version": UNKNOWN_PACKAGE_ID, "declared": False}
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise PackageIdentityError(
            f"{PACKAGE_MANIFEST_NAME} in {package_dir} exists but is not "
            f"readable JSON ({exc}) - refusing to install from a package "
            "whose identity declaration is garbage") from exc
    if not isinstance(raw, dict):
        raise PackageIdentityError(
            f"{PACKAGE_MANIFEST_NAME} in {package_dir} must be a JSON object")
    pid = raw.get("package_id")
    if not isinstance(pid, str) or not pid.strip():
        raise PackageIdentityError(
            f"{PACKAGE_MANIFEST_NAME} in {package_dir} lacks a non-empty "
            "string 'package_id' - fix or remove the file")
    ver = raw.get("package_version", UNKNOWN_PACKAGE_ID)
    if ver is None:
        ver = UNKNOWN_PACKAGE_ID
    if not isinstance(ver, str) or not ver.strip():
        raise PackageIdentityError(
            f"{PACKAGE_MANIFEST_NAME} in {package_dir}: 'package_version' "
            "must be a non-empty string when present")
    return {"package_id": pid.strip(),
            "package_version": ver.strip(), "declared": True}


def _manifest_package_id(manifest) -> str:
    """PKG-IDENT01: the declared identity of an install record, or "unknown".

    Old manifests (v0.3/v0.4/v0.5) and manifests written from unstamped
    packages have no usable package_id; both read as "unknown". A manifest
    that carries a non-string or empty value is treated the same way - the
    install side never trusts the record beyond its shape.
    """
    if not isinstance(manifest, dict):
        return UNKNOWN_PACKAGE_ID
    pid = manifest.get("package_id")
    if isinstance(pid, str) and pid.strip():
        return pid.strip()
    return UNKNOWN_PACKAGE_ID


def _manifest_str_field(manifest, key: str) -> str:
    """Same leniency as _manifest_package_id for informational fields."""
    if isinstance(manifest, dict):
        val = manifest.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return UNKNOWN_PACKAGE_ID


# ---------------------------------------------------------------------------
# SEAL-CHAIN01: the install seal - a protected record, NOT a signature.
#
# The manifest is plain-text JSON and uninstall() acts on it, so a
# hand-edited manifest can silently drive deletions (W21 UNCOVERED §3). The
# seal records the canonical hash of the manifest bytes AS THIS INSTALL WROTE
# THEM, so later edits are detected instead of trusted. BOUNDARY: this
# guards accidents and honest tooling only - whoever can edit the manifest
# can recompute the seal too. Nothing here is anti-tamper, and no output of
# this module may claim otherwise.
# ---------------------------------------------------------------------------

def _manifest_version_tuple(manifest) -> tuple | None:
    """Parse the manifest's 'version' (the TOOL version that wrote it) into a
    comparable tuple, or None when absent/garbage. A manifest with no
    parseable version predates the seal era."""
    if not isinstance(manifest, dict):
        return None
    ver = manifest.get("version")
    if not isinstance(ver, str):
        return None
    parts = ver.strip().split(".")
    nums: list[int] = []
    for part in parts:
        if not part.isdigit():
            return None
        nums.append(int(part))
    if not nums:
        return None
    while len(nums) < 2:
        nums.append(0)
    return tuple(nums)


def _manifest_is_seal_era(manifest) -> bool:
    """Does this manifest come from a tool version that writes and expects an
    install seal (tool >= 0.7)? Old manifests (v0.3/0.4/0.5/0.6, or with a
    missing/garbage version field) predate the seal and are handled in
    degraded mode."""
    ver = _manifest_version_tuple(manifest)
    return ver is not None and ver >= SEAL_ERA_VERSION


def manifest_canonical_sha256(manifest_path) -> str | None:
    """SHA-256 over the manifest's CANONICAL bytes: the file bytes decoded as
    UTF-8 (a BOM is tolerated), CRLF and lone CR normalized to LF, re-encoded
    UTF-8. Returns None when the file cannot be read or decoded."""
    try:
        text = Path(manifest_path).read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _seal_slot_error(game: Path) -> str | None:
    """The seal is a derived name like the record itself: same five identity
    criteria, never read or written through an alias."""
    return _derived_slot_error(game, SEAL_NAME, "install seal")


def evaluate_seal(game, manifest, manifest_path) -> dict:
    """Judge the install seal for a manifest that was read from game/.
    Read-only. Returns {"state", "detail", "recorded", "path"} with state:
      ok          - seal present, parses, and its manifest_sha256 matches the
                    canonical hash of the manifest bytes on disk (and its
                    package_digest agrees with the manifest's, when both
                    sides carry one);
      missing     - seal-era manifest but the seal file is absent;
      mismatch    - seal present but its hashes disagree (manifest edited
                    after install, or a stale/tampered seal);
      corrupt     - seal present but not readable JSON / not a seal object;
      aliased     - the seal slot is not a plain file - refusing to read it;
      not_expected- the manifest predates the seal era; a seal file may still
                    exist (stale residue), reported as detail - never a
                    refusal on its own.
    """
    game = Path(game)
    seal_path = game / SEAL_NAME
    if not _manifest_is_seal_era(manifest):
        stray = seal_path.is_file()
        return {"state": "not_expected",
                "detail": (f"a {SEAL_NAME} is present but the manifest "
                           "predates the seal era (tool version "
                           f"{manifest.get('version')!r}) - treated as "
                           "stale residue")
                if stray else None,
                "recorded": None, "path": str(seal_path)}
    err = _seal_slot_error(game)
    if err:
        return {"state": "aliased", "detail": err, "recorded": None,
                "path": str(seal_path)}
    if not seal_path.is_file():
        return {"state": "missing",
                "detail": f"{SEAL_NAME} is absent for a seal-era manifest "
                          f"(tool version {manifest.get('version')!r})",
                "recorded": None, "path": str(seal_path)}
    try:
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"state": "corrupt",
                "detail": f"{SEAL_NAME} is not readable JSON ({exc})",
                "recorded": None, "path": str(seal_path)}
    if not isinstance(seal, dict) or seal.get("kind") != SEAL_KIND:
        return {"state": "corrupt",
                "detail": f"{SEAL_NAME} is not a {SEAL_KIND!r} seal object",
                "recorded": None, "path": str(seal_path)}
    manifest_sha = manifest_canonical_sha256(manifest_path)
    if manifest_sha is None:
        return {"state": "corrupt",
                "detail": "the manifest bytes cannot be read/decoded for the "
                          "seal check",
                "recorded": seal, "path": str(seal_path)}
    recorded_sha = seal.get("manifest_sha256")
    if recorded_sha != manifest_sha:
        return {"state": "mismatch",
                "detail": f"the manifest's canonical sha256 "
                          f"{manifest_sha[:12]}... does not match the seal's "
                          f"recorded manifest_sha256 "
                          f"{str(recorded_sha)[:12]}... - the manifest "
                          "changed after install (or the seal is "
                          "stale/tampered)",
                "recorded": seal, "path": str(seal_path)}
    rec_digest = seal.get("package_digest")
    man_digest = manifest.get("package_digest")
    if (isinstance(rec_digest, str) and isinstance(man_digest, str)
            and rec_digest != man_digest):
        return {"state": "mismatch",
                "detail": f"the seal's package_digest {str(rec_digest)[:12]}"
                          f"... disagrees with the manifest's "
                          f"{str(man_digest)[:12]}...",
                "recorded": seal, "path": str(seal_path)}
    return {"state": "ok", "detail": None, "recorded": seal,
            "path": str(seal_path)}


def write_install_seal(game, manifest: dict) -> None:
    """Write the install seal next to the manifest, through the same staged,
    alias-proof primitive as the record itself.

    The seal must hash EXACTLY what the record write puts on disk, so it is
    computed over the LF form of the manifest JSON (what
    manifest_canonical_sha256() reconstructs from the CRLF file). Call it
    only AFTER the record write has landed.
    """
    canonical_lf = json.dumps(manifest, indent=2, ensure_ascii=False)
    seal = {
        "tool": "ra2forge",
        "kind": SEAL_KIND,
        "tool_version": TOOL_VERSION,
        "package_id": manifest.get("package_id"),
        "package_digest": manifest.get("package_digest"),
        "manifest_sha256": hashlib.sha256(canonical_lf.encode("utf-8"))
                           .hexdigest(),
        "sealed_at": datetime.now().isoformat(timespec="seconds"),
    }
    _stage_text_and_replace(json.dumps(seal, indent=2, ensure_ascii=False),
                            Path(game) / SEAL_NAME, "install seal")


def package_digest_from_steps(steps: list) -> str:
    """PKG-IDENT01: content fingerprint of the package this plan ships.

    SHA-256 over one UTF-8 line per shipped file, "<name> <sha256>",
    sorted by name, joined with "\n" (no trailing newline). Built from the
    plan's steps so the digest and the bytes actually copied can never
    disagree; package_files() defines the shipped set (BATTLEMD98.INI, the
    optional W34 MAPSELMD.INI, the *.MAP files, expandmd98.mix) - build
    reports and readmes are excluded on purpose because they never land in
    the game directory.
    """
    lines = [f"{s['name']} {s['new_sha']}"
             for s in sorted(steps, key=lambda s: s["name"])]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def sha256_of(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def package_files(package_dir) -> list[Path]:
    """Files an install copies, in order: INI first, then maps, then the MIX."""
    package_dir = Path(package_dir)
    if not package_dir.is_dir():
        raise FileNotFoundError(f"package directory not found: {package_dir}")
    ini = package_dir / BATTLE_INI
    if not ini.is_file():
        legacy = package_dir / LEGACY_BATTLE_INI
        hint = (" - this package was built by an older ra2forge that wrote "
                "BATTLEMD.INI; rebuild it") if legacy.is_file() else ""
        raise FileNotFoundError(f"{ini} not found in {package_dir}{hint}")
    files: list[Path] = [ini]
    # W34: MAPSELMD.INI is a loose whole-file override. It only ships when
    # the build was made with --mapselmd, so a v10 package is unaffected.
    mapsel = package_dir / MAPSEL_NAME
    if mapsel.is_file():
        files.append(mapsel)
    # W41: ra2md.csf is a loose whole-file override. It only ships when the
    # build was made with --csf-out (complete official-baseline clone), so a
    # v11/no-CSF package is unaffected -> backward compatibility is preserved.
    csf = package_dir / CSF_NAME
    if csf.is_file():
        files.append(csf)
    files += sorted(p for p in package_dir.glob("*.MAP") if p.is_file())
    mix = package_dir / MIX_NAME
    if mix.is_file():
        files.append(mix)
    return files


# ---------------------------------------------------------------------------
# DLC-STRICT01 preflight: a read-only classification of everything the install
# would touch, done BEFORE any write. Four classes:
#   blockers  - definite, NEVER escapable (path safety, corrupt install
#               record, backup-slot protection);
#   conflicts - definite content conflicts; escapable in exactly one explicit,
#               logged way (allow_content_conflict=True);
#   risks     - state that cannot be judged reliably (strict mode refuses);
#   notices   - ordinary hints, never block (an official BATTLEMD.INI is one).
# ---------------------------------------------------------------------------

def _dest_safety_error(game: Path, name: str) -> str | None:
    """Why writing game/<name> would be unsafe, or None."""
    if not name or name in (".", ".."):
        return f"unsafe destination name {name!r}"
    if Path(name).name != name or "/" in name or "\\" in name:
        return f"destination name contains a path separator: {name!r}"
    if name.endswith(BACKUP_SUFFIX):
        return f"destination collides with the backup namespace: {name!r}"
    dest = game / name
    # DLC-HIGH1-FIX01 (HIGH-1): the slot itself must be the plain destination
    # file. A symbolic link at the slot - even one pointing back INSIDE the
    # game directory (game/expandmd98.mix -> game/RA2MD.INI) - would make the
    # write land on a file the manifest never lists, and uninstall could
    # neither restore nor even name it. Hard blocker, never escapable via
    # allow_content_conflict.
    if dest.is_symlink():
        return (f"{name} is a symbolic link (to {dest.resolve()}) - refusing "
                f"to write through an alias; remove the link first")
    if dest.exists() and not dest.is_file():
        return (f"{name} exists in the game directory but is not a regular "
                f"file - refusing to write over or under it")
    try:
        resolved = dest.resolve()
        parent = resolved.parent
        game_resolved = game.resolve()
    except OSError as exc:
        return f"cannot resolve destination for {name}: {exc}"
    if parent != game_resolved:
        return (f"destination for {name} resolves outside the game directory "
                f"({parent})")
    # DLC-HIGH1-FIX01 (HIGH-1): the resolution must be the slot itself - a
    # link or junction landing on a DIFFERENT name inside the game directory
    # passes the parent check above but would write somewhere else. normcase
    # keeps the comparison case-insensitive like the filesystem it runs on.
    if (os.path.normcase(str(resolved))
            != os.path.normcase(str(game_resolved / name))):
        return (f"destination for {name} resolves to a different name inside "
                f"the game directory ({resolved}) - refusing to write through "
                f"an alias")
    # Same alias class without a link: a hard link shares its bytes with
    # another, unlisted name, so writing here would silently change that file.
    try:
        nlinks = dest.stat().st_nlink if dest.is_file() else 1
    except OSError:
        nlinks = 1
    if nlinks > 1:
        return (f"{name} is a hard link ({nlinks} names share its bytes) - "
                f"writing it would change another unlisted file")
    return None


def _bak_safety_error(game: Path, name: str) -> str | None:
    """DLC-HIGH2-FIX01 (HIGH-2): why the backup slot game/<name>.ra2forge.bak
    must not be created, kept or consumed as it is, or None.

    The slot gets the SAME identity checks as the destination slot. It used to
    be judged with is_file()/exists() only, and both FOLLOW symbolic links: a
    dangling link at the slot read as "empty", the plan picked backup=create,
    and copy2() wrote the oldest original THROUGH the link - to a path outside
    the game directory chosen by whoever planted the link (and the escape
    hatch released it, violating the rule that path safety is never bypassed).
    A live link made the "backup" live somewhere else, and uninstall() later
    "restored" through it. Every shape below is a HARD blocker, never
    escapable via allow_content_conflict.
    """
    slot = name + BACKUP_SUFFIX
    target = game / slot
    if target.is_symlink():
        return (f"backup slot {slot} is a symbolic link (to {target.resolve()})"
                f" - a dangling or live alias is never an empty backup slot; "
                f"remove the link first")
    if target.exists() and not target.is_file():
        return (f"backup slot {slot} exists but is not a regular file - "
                f"refusing to create the backup")
    try:
        resolved = target.resolve()
        parent = resolved.parent
        game_resolved = game.resolve()
    except OSError as exc:
        return f"cannot resolve backup slot for {slot}: {exc}"
    if parent != game_resolved:
        return (f"backup slot for {slot} resolves outside the game directory "
                f"({parent})")
    if (os.path.normcase(str(resolved))
            != os.path.normcase(str(game_resolved / slot))):
        return (f"backup slot for {slot} resolves to a different name inside "
                f"the game directory ({resolved}) - refusing to write through "
                f"an alias")
    try:
        nlinks = target.stat().st_nlink if target.is_file() else 1
    except OSError:
        nlinks = 1
    if nlinks > 1:
        return (f"backup slot {slot} is a hard link ({nlinks} names share its "
                f"bytes) - a backup that shares bytes with another unlisted "
                f"file cannot be trusted as the oldest original")
    return None


def _derived_slot_error(game: Path, name: str, what: str) -> str | None:
    """DLC-HIGH3-FIX01 (A1): why writing/reading game/<name> would be unsafe,
    for a name that is DERIVED from a slot name (staging file, install record,
    removed-original backup). Same identity criteria as the destination slot.

    HIGH-3 and HIGH-4 are one miss seen twice: the destination and the backup
    slot got the full alias checks, but a name built FROM a slot name was
    checked by none of the gates, so an alias planted there was invisible. A
    derived name must satisfy the same five criteria: not a symbolic link
    (dangling links included - they are not "absent"), not a special file, its
    real path lands on itself inside the game directory, and it is not a hard
    link. Every shape is a hard blocker, never releasable.
    """
    if not name or name in (".", ".."):
        return f"unsafe {what} name {name!r}"
    if Path(name).name != name or "/" in name or "\\" in name:
        return f"{what} name contains a path separator: {name!r}"
    target = game / name
    if target.is_symlink():
        return (f"{what} {name} is a symbolic link (to {target.resolve()}) - a "
                f"dangling or live alias is never an empty {what}; remove the "
                f"link first")
    if target.exists() and not target.is_file():
        return (f"{what} {name} exists but is not a regular file - refusing to "
                f"use it")
    try:
        resolved = target.resolve()
        parent = resolved.parent
        game_resolved = game.resolve()
    except OSError as exc:
        return f"cannot resolve {what} for {name}: {exc}"
    if parent != game_resolved:
        return (f"{what} {name} resolves outside the game directory ({parent})")
    if (os.path.normcase(str(resolved))
            != os.path.normcase(str(game_resolved / name))):
        return (f"{what} {name} resolves to a different name inside the game "
                f"directory ({resolved}) - refusing to use an alias")
    try:
        nlinks = target.stat().st_nlink if target.is_file() else 1
    except OSError:
        nlinks = 1
    if nlinks > 1:
        return (f"{what} {name} is a hard link ({nlinks} names share its bytes) "
                f"- a {what} that shares its bytes with another unlisted name "
                f"cannot be trusted")
    return None


def _same_directory_entry(name: str, other: str) -> bool:
    """Do these two names address ONE AND THE SAME file on this volume?

    [更正 2026-10-04 · 依据 A-70 H-2] A plain `==` between two names is not an
    identity test here: the volume this tool protects itself against is
    case-insensitive and strips trailing dots and spaces, so
    RA2FORGE_INSTALL.JSON and "ra2forge_install.json." are the same directory
    entry as ra2forge_install.json - the very file the legacy listing is
    forbidden to delete. Measured (see DLC-HARDEN4-FIX01 raw/42_*).
    """
    return (os.path.normcase(name.rstrip(". "))
            == os.path.normcase(other.rstrip(". ")))


def _refuse_aliased_landing_slot(dest: Path, what: str) -> None:
    """Refuse to commit onto a landing slot that stopped being itself.

    [更正 2026-10-04 · 依据 A-69 F-1/F-3] os.replace() does not follow an alias
    (measured again this round for live link / link to a directory / dangling /
    hard link / plain file / directory: no shape wrote a single byte outside),
    but "does not follow" and "refuses" are different promises: on a live or
    dangling link it silently SWAPPED the planted alias away, and the identity
    gates that used to back the promise ran a whole write loop - or one
    intervening backup write - before the commit. A gate belongs next to the
    write it guards, so every primitive re-runs the derived-name criteria on
    its own landing slot immediately before os.replace().
    """
    err = _derived_slot_error(dest.parent, dest.name, what)
    if err:
        raise OSError(f"the {what} slot was refused right before the write: {err}")


def _slot_namespace_errors(game: Path, name: str) -> list[tuple[str, str]]:
    """DLC-HIGH3-FIX01 (A1): the staging names the previous generation derived
    from this slot deterministically. They are gated even though this version
    no longer uses them, because that is where HIGH-3's alias was planted and
    because an aborted older run may have left an alias there.

    Returns [(class-prefix, reason)] for the ones that are not acceptable.
    """
    out: list[tuple[str, str]] = []
    for kind, derived in (
        ("path-safety", name + STAGE_INFIX),
        ("backup-protection", name + BACKUP_SUFFIX + STAGE_INFIX),
    ):
        err = _derived_slot_error(game, derived, "staging slot")
        if err:
            out.append((kind, err))
    return out


def _record_slot_error(game: Path) -> str | None:
    """DLC-HIGH3-FIX01 (HIGH-4): the install record under the same criteria."""
    return _derived_slot_error(game, MANIFEST_NAME, "install record")


def _source_safety_error(package: Path, src: Path) -> str | None:
    """Why reading package/<src> as a copy source would be unsafe, or None."""
    if not src.is_file():
        return f"package member {src.name} is not a regular file"
    try:
        src.resolve().relative_to(package.resolve())
    except (ValueError, OSError):
        return (f"package member {src.name} resolves outside the package "
                f"directory")
    return None


def _scan_environment(game: Path) -> tuple[list[str], list[str]]:
    """(risks, notices) about the surrounding game directory; read-only."""
    risks: list[str] = []
    notices: list[str] = []
    official = game / LEGACY_BATTLE_INI
    if official.exists():
        # [更正 2026-10-04 · 依据 A-69 DP-15 · 判定：这里不加门禁，加披露] this
        # read used to be the only one in the module with no identity criteria
        # at all. The five criteria are deliberately NOT applied here: this
        # function drives no write and no delete, and the engine enumerates this
        # very name with FindFirstFileA("BATTLEMD*.INI") and opens it through the
        # same reparse point, so refusing here would block an install over a
        # state the game itself is going to act on - while saying nothing would
        # describe bytes reached through an alias as if they were the slot's own
        # content. The verdict therefore stays, and names what it was read from.
        # The reads that ARE acted on - uninstall's legacy collection point,
        # which decides a deletion set - carry the full criteria.
        alias = _derived_slot_error(game, LEGACY_BATTLE_INI,
                                    "official battle list")
        alias_note = ("" if alias is None else
                      " NOTE: this slot is not a plain file of its own "
                      f"({alias}) - what follows describes the bytes reached "
                      "through it, which is also what the engine reads.")
        head = None
        try:
            head = official.read_bytes()[:400]
        except OSError as exc:
            risks.append(f"cannot read {LEGACY_BATTLE_INI} ({exc}) - its "
                         f"effect on this install cannot be judged")
        if head is not None:
            if FORGE_MARKER in head:
                risks.append(
                    f"{LEGACY_BATTLE_INI} is a legacy ra2forge override (an old "
                    "version rewrote the official campaign list); the engine "
                    "merges it with BATTLEMD98.INI by battle id, so the "
                    "campaign-menu outcome is unpredictable. Run 'python -m "
                    "ra2forge uninstall --game <dir> --legacy' first."
                    + alias_note)
            else:
                notices.append(
                    f"{LEGACY_BATTLE_INI} present (normal install state) and "
                    "left untouched; the campaign is appended by BATTLEMD98.INI "
                    "(the engine merges both by battle id). This is NOT a "
                    "conflict." + alias_note)
    for p in sorted(game.glob("BATTLEMD*.INI")):
        if p.name.upper() in (LEGACY_BATTLE_INI, BATTLE_INI):
            continue
        risks.append(
            f"{p.name} also matches BATTLEMD*.INI; between such files only the "
            "directory enumeration order decides which one loads last, so the "
            "battle-list merge outcome cannot be judged here.")
    if (game / "expandmd99.mix").is_file():
        risks.append(
            "expandmd99.mix exists: expandmd* mixes load in descending order, "
            "so 99 is loaded BEFORE 98 and wins for identical entries - "
            "whether it shadows this campaign cannot be judged without reading "
            "both mixes.")
    if (game / LEGACY_MANIFEST).is_file():
        risks.append(
            f"legacy {LEGACY_MANIFEST} found (placed by an older ra2forge); "
            "stale legacy artefacts may collide with this install. Run "
            "'python -m ra2forge uninstall --game <dir> --legacy' first.")
    return risks, notices


def preinstall_warnings(game) -> list[str]:
    """Legacy combined view of the environment scan (risks + notices)."""
    risks, notices = _scan_environment(Path(game))
    return risks + notices


def _plan_orphans(game: Path, old_entries: dict, package_names: set) -> list:
    """ORPHAN-FIX01: plan the exit of files the CURRENT record names that the
    new package no longer contains. Read-only; every dangerous shape lands in
    blockers via the caller's classes, never in the plan.

    Each orphan dict: {name, mode, backup, sha256}; mode is
      restore       - our file is still installed (sha matches the record);
                      the recorded backup holds the pre-install ORIGINAL, so
                      restore it over our file and consume the slot;
      remove_absent - like restore, but the record proves the slot holds OUR
                      own previous version (original_absent, or the slot was
                      already gone at preflight): remove file + slot;
      remove        - our file, no backup ever made (we created it): delete;
      changed       - the bytes no longer match the record: keep file and
                      backup slot, refuse in strict mode (a risk), warn in
                      non-strict; never deleted, never adopted;
      missing       - nothing left to clean (the slot may still restore an
                      original - see restore below); no write planned here.
    """
    orphans: list[dict] = []
    for entry in reversed(list(old_entries.values())):
        name = entry["name"]
        if name in package_names:
            continue
        if (name in (".", "..") or Path(name).name != name
                or "/" in name or "\\" in name
                or os.path.normcase(name.rstrip(". "))
                == os.path.normcase(MANIFEST_NAME)):
            # the caller turns this into a corrupt-manifest blocker
            orphans.append({"name": name, "mode": "invalid_name",
                            "backup": entry.get("backup"),
                            "sha256": entry.get("sha256")})
            continue
        err = _dest_safety_error(game, name)
        if err:
            orphans.append({"name": name, "mode": "unsafe_slot", "reason": err,
                            "backup": entry.get("backup"),
                            "sha256": entry.get("sha256")})
            continue
        backup = entry.get("backup")
        absent = bool(entry.get("original_absent"))
        dest = game / name
        dest_exists = dest.is_file()
        dest_sha = sha256_of(dest) if dest_exists else None
        ours = dest_exists and dest_sha == entry.get("sha256")
        bak_ok = True
        bak_exists = False
        if backup:
            if backup != name + BACKUP_SUFFIX:
                orphans.append({"name": name, "mode": "invalid_backup",
                                "backup": backup, "sha256": entry.get("sha256")})
                continue
            bak_exists = (game / backup).is_file()
            if bak_exists:
                bak_err = _bak_safety_error(game, name)
                if bak_err:
                    orphans.append({"name": name, "mode": "unsafe_backup",
                                    "reason": bak_err, "backup": backup,
                                    "sha256": entry.get("sha256")})
                    continue
            elif not dest_exists:
                bak_ok = False  # recorded slot gone and nothing to restore
        if dest_exists and not ours:
            orphans.append({"name": name, "mode": "changed", "backup": backup,
                            "sha256": entry.get("sha256"),
                            "dest_sha": dest_sha})
            continue
        if not dest_exists and not bak_exists:
            orphans.append({"name": name, "mode": "missing", "backup": backup,
                            "sha256": entry.get("sha256")})
            continue
        if backup and bak_exists and not absent:
            orphans.append({"name": name, "mode": "restore", "backup": backup,
                            "sha256": entry.get("sha256")})
        elif backup and bak_exists:
            orphans.append({"name": name, "mode": "remove_absent",
                            "backup": backup, "sha256": entry.get("sha256")})
        else:
            # no slot (we created it), or the recorded slot is already gone
            orphans.append({"name": name, "mode": "remove", "backup": backup,
                            "sha256": entry.get("sha256"), "bak_ok": bak_ok})
    return orphans


def preinstall_plan(package_dir, game_dir, *, adopt_legacy: bool = False) -> dict:
    """Read-only preflight for install_package(): classify BEFORE any write.

    Returns a dict with:
      blockers / conflicts / risks / notices : list[str]
      mapsel_conflicts : W34 - definite MAPSELMD.INI conflicts that
                  --allow-content-conflict must NEVER release (a foreign
                  whole-file campaign-progression registration);
      csf_conflicts : W41 - definite ra2md.csf conflicts that
                  --allow-content-conflict must NEVER release (a foreign
                  loose whole-file CSF override of langmd.mix);
      steps : the write plan - dicts {name, src, action, backup, conflict,
              recorded_backup, new_sha, dest_sha, size, original_absent};
              action is one of created/unchanged/replaced, backup is
              None/'create'/'keep'
      manifest / corrupt_manifest : parsed record or why it was rejected
      orphans : ORPHAN-FIX01 - planned exit of files the current record names
                that this package dropped (see _plan_orphans); entries whose
                name or slots fail the identity gates come back as
                invalid_name / unsafe_slot / invalid_backup / unsafe_backup
                and the caller turns them into hard blockers
      identity : PKG-IDENT01 - {verdict, old_package_id, new_package_id,
                new_package_version, package_digest, adopt_legacy, message};
                verdict is one of fresh / upgrade / adopt / reject_mismatch /
                reject_legacy. reject_* verdicts are raised by
                install_package() as PackageIdentityBlocked before any write;
                adopt (only with adopt_legacy=True) treats the current
                record's files as ours; package_digest is computed from the
                steps (see package_digest_from_steps).
    Raises FileNotFoundError exactly like before when the game directory does
    not look like one or the package is unusable (still zero writes), and
    PackageIdentityError when the package's ra2forge_package.json exists but
    is garbage (still zero writes).
    """
    package = Path(package_dir)
    game = Path(game_dir)
    if not (game / "gamemd.exe").is_file():
        raise FileNotFoundError(
            f"{game} does not look like a Yuri's Revenge directory "
            f"(gamemd.exe not found)")
    files = package_files(package)
    # PKG-IDENT01: the package's own identity declaration, read before
    # anything is planned. A planted-but-garbage declaration is a hard error.
    pkg_ident = _read_package_identity(package)

    blockers: list[str] = []
    conflicts: list[str] = []
    # W34: MAPSELMD.INI conflicts that --allow-content-conflict must NEVER
    # release (a whole-file override of another mod's / the official
    # registration must not be silently overwritten).
    mapsel_conflicts: list[str] = []
    # W41: the same never-releasable rule for a foreign loose ra2md.csf.
    csf_conflicts: list[str] = []
    steps: list[dict] = []

    manifest_path = game / MANIFEST_NAME
    manifest = None
    corrupt: str | None = None
    # DLC-HIGH2-FIX01: the install record itself is never read or written
    # through an alias - a dangling link here read as "no record" and the
    # final write_text() would have created the record OUTSIDE the game
    # directory through it.
    if manifest_path.is_symlink():
        corrupt = ("a symbolic link (refusing to read or write the install "
                   "record through an alias); resolve it manually")
    else:
        # DLC-HIGH3-FIX01 (A1/HIGH-4): a symbolic link is not the only alias
        # shape, and the record is a name like any other slot - it gets the
        # same five identity criteria BEFORE it is read.
        rec_err = _record_slot_error(game)
        if rec_err:
            corrupt = f"{rec_err}; resolve it manually"
        elif manifest_path.exists():
            try:
                parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                corrupt = f"unreadable or not valid JSON ({exc})"
            else:
                if (not isinstance(parsed, dict)
                        or not isinstance(parsed.get("files"), list)):
                    corrupt = ("malformed structure (expected an object with a "
                               "'files' list)")
                else:
                    manifest = parsed
    if corrupt:
        blockers.append(
            f"corrupt-manifest: {MANIFEST_NAME} exists but is {corrupt}. That "
            "record is what tells our own files apart from foreign ones and "
            "which *.ra2forge.bak slot belongs to which original; refusing "
            "instead of guessing. This refusal is NOT bypassable by "
            "--allow-content-conflict. Inspect the record and the backup "
            "slots manually, then repair or remove the file.")
    old_entries: dict[str, dict] = {}
    if manifest:
        for e in manifest.get("files", []):
            if isinstance(e, dict) and e.get("name"):
                old_entries[e["name"]] = e
    # PKG-IDENT01: the install-time identity judgment. The old path-equality
    # test (manifest["package"] == this directory) is GONE - from two
    # different paths, or the same path,先后两个不同包 was indistinguishable;
    # the identity now comes from the declared package_id on both sides.
    old_pkg_id = _manifest_package_id(manifest)
    new_pkg_id = pkg_ident["package_id"]
    if manifest is None:
        verdict = "fresh"
    elif old_pkg_id == UNKNOWN_PACKAGE_ID:
        # an old manifest (v0.3/0.4/0.5), or one written from an unstamped
        # package: identity undeclared, so any install here would be a guess
        verdict = "adopt" if adopt_legacy else "reject_legacy"
    elif new_pkg_id == UNKNOWN_PACKAGE_ID:
        # this package declares no identity while the record names one:
        # it cannot be proven to be that package's successor
        verdict = "adopt" if adopt_legacy else "reject_legacy"
    elif new_pkg_id == old_pkg_id:
        verdict = "upgrade"
    else:
        verdict = "reject_mismatch"
    identity_msg: str | None = None
    if verdict == "reject_mismatch":
        identity_msg = (
            f"package identity mismatch: {MANIFEST_NAME} records package_id "
            f"{old_pkg_id!r}, but this package declares package_id "
            f"{new_pkg_id!r}. This version does not support coexisting "
            "packages (初版不支持并存) - uninstall the recorded package "
            "first ('python -m ra2forge uninstall --game <dir>'). This "
            "refusal is NOT bypassable: not by --force, not by "
            "--allow-content-conflict, not by --adopt-legacy.")
    elif verdict == "reject_legacy":
        if old_pkg_id == UNKNOWN_PACKAGE_ID:
            side = (f"{MANIFEST_NAME} in this directory declares no "
                    "package_id (an old ra2forge manifest, or an install "
                    "made from an unstamped package)")
        else:
            side = (f"{MANIFEST_NAME} in this directory records package_id "
                    f"{old_pkg_id!r}, but this package declares no "
                    f"package_id (no {PACKAGE_MANIFEST_NAME} in the package)")
        identity_msg = (
            f"package identity undeclared: {side}, so installing here "
            "without more information would be a guess. Re-run with "
            "--adopt-legacy to assert explicitly that this install is the "
            "intended successor of whatever is recorded (its recorded files "
            "are then treated as ours and upgraded over), or uninstall the "
            "recorded package first. --force does NOT bypass this.")
    # "recorded entries are ours" for the per-file conflict classification:
    # true for a same-id upgrade and for an explicit adoption only. (The
    # pre-PKG-IDENT path-equality semantics die here - see the verdict block.)
    same_install = verdict in ("upgrade", "adopt")

    risks, notices = _scan_environment(game)

    # SEAL-CHAIN01: install REPLACES the trust anchor (a fresh seal is written
    # with the new record), so the previous record's seal is NOT a gate here -
    # but a seal-era record whose seal does not check out is disclosed as a
    # notice, never silently consumed.
    if manifest is not None:
        prev_seal = evaluate_seal(game, manifest, manifest_path)
        if prev_seal["state"] == "not_expected":
            if prev_seal["detail"]:
                notices.append(f"install seal note: {prev_seal['detail']}")
        elif prev_seal["state"] != "ok":
            notices.append(
                f"the existing {MANIFEST_NAME} is seal-era (tool version "
                f"{manifest.get('version')!r}) but its install seal is "
                f"{prev_seal['state']} ({prev_seal['detail']}) - this "
                "install replaces the record and writes a fresh seal "
                "WITHOUT gating on the old one; run 'python -m ra2forge "
                "verify --game <dir>' first if you did not expect this")

    for src in files:
        name = src.name
        new_sha = sha256_of(src)
        err = _source_safety_error(package, src) or _dest_safety_error(game, name)
        if err:
            blockers.append(f"path-safety: {err}")
            continue
        # DLC-HIGH3-FIX01 (A1): the names this tool DERIVES from the slot are
        # gated like the slots themselves. HIGH-3 was exactly such a name
        # (<slot>.ra2forge-stage) that no identity check ever looked at.
        derived = _slot_namespace_errors(game, name)
        if derived:
            for kind, derr in derived:
                blockers.append(f"{kind}: {derr}")
            continue
        dest = game / name
        previous = old_entries.get(name, {})
        recorded_backup = previous.get("backup")
        dest_sha = sha256_of(dest) if dest.is_file() else None
        conflict = False
        if dest_sha == new_sha:
            action, backup = "unchanged", None
            if name not in old_entries:
                # DLC-HIGH1-FIX01 (MEDIUM-2): never adopt an unregistered file
                # silently - uninstall deletes adopted files and this one has
                # no backup slot, so the user must be told NOW.
                notices.append(
                    f"{name} is byte-identical to the package copy but NOT "
                    f"recorded in {MANIFEST_NAME} (placed by hand or by "
                    "another tool?): this install adopts it as ours and a "
                    "later uninstall WILL DELETE it (it has no backup slot); "
                    "remove or rename it first if you want to keep a copy")
        elif dest_sha is None:
            action, backup = "created", None
        else:
            action = "replaced"
            if name in old_entries and dest_sha == previous.get("sha256"):
                if not same_install:
                    conflict = True
                    conflicts.append(
                        f"{name}: a previous ra2forge install (recorded in "
                        f"{MANIFEST_NAME}, package "
                        f"{manifest.get('package')!r}) would be replaced by "
                        "a DIFFERENT package - uninstall it first, or pass "
                        "--allow-content-conflict to release this one "
                        "conflict")
            elif name in old_entries:
                risks.append(
                    f"{name} changed after our install (its sha256 no longer "
                    f"matches {MANIFEST_NAME}) - what modified it cannot be "
                    "judged here; refusing in strict mode. 'uninstall' will "
                    "keep the changed file unless --force is given.")
            else:
                conflict = True
                # W34/W41: MAPSELMD.INI and ra2md.csf get one precise,
                # never-releasable conflict message from the post-loop pass
                # below; do not also emit the generic releasable wording.
                if name not in (MAPSEL_NAME, CSF_NAME):
                    conflicts.append(
                        f"{name}: would replace a file that {MANIFEST_NAME} does "
                        "not record as ours (another campaign/mod or a user file) "
                        "- the replaced content would only survive as a fresh "
                        "*.ra2forge.bak slot")
            # DLC-HIGH2-FIX01 (HIGH-2): the backup slot passes the SAME
            # identity checks as the destination slot, BEFORE the keep/create
            # decision - a dangling link there must never read as an empty
            # slot. Hard blocker, never releasable (R-03: the escape hatch
            # covers content conflicts only, never path safety).
            bak_err = _bak_safety_error(game, name)
            if bak_err:
                blockers.append(f"backup-protection: {bak_err}")
                continue
            bak = game / (name + BACKUP_SUFFIX)
            if bak.is_file():
                # an existing backup slot always wins: the oldest original is
                # never overwritten (DLC-STRICT01 backup protection)
                backup = "keep"
            else:
                backup = "create"
                if bak.exists():  # defense in depth; unreachable while the
                    # identity gates above hold
                    blockers.append(
                        f"backup-protection: backup slot {bak.name} exists but "
                        "is not a regular file; refusing to create the backup")
        # ORPHAN-FIX01: does the backup this replacement would write hold a
        # USER original (a slot already existed -> backup="keep") or OUR OWN
        # previous bytes (no slot existed and the previous record names this
        # file)? Drives the original_absent flag the new entry carries, which
        # makes uninstall() remove file + slot instead of "restoring" our own
        # earlier version over a file that never had an original.
        original_absent = bool(name in old_entries
                               and not (game / (name + BACKUP_SUFFIX)).is_file())
        if action == "unchanged":
            original_absent = bool(previous.get("original_absent"))
        steps.append({"name": name, "src": src, "action": action,
                      "backup": backup, "conflict": conflict,
                      "recorded_backup": recorded_backup, "new_sha": new_sha,
                      "dest_sha": dest_sha, "size": src.stat().st_size,
                      "original_absent": original_absent})

    # W34: a MAPSELMD.INI that already exists and is NOT one of ours (not
    # recorded in the current install record) is a definite preflight content
    # conflict that defaults to a refusal, and stays refused even when the
    # user passes --allow-content-conflict. Covering "created/replaced" and
    # the byte-identical-but-unrecorded "adopt" case alike.
    for step in steps:
        if (step["name"] == MAPSEL_NAME and step["dest_sha"] is not None
                and step["name"] not in old_entries):
            msg = (
                f"{MAPSEL_NAME}: a non-ra2forge {MAPSEL_NAME} already exists "
                "in the game directory (not recorded as ours in "
                f"{MANIFEST_NAME}). It is a WHOLE-FILE override of the "
                "campaign-progression registration; overwriting it would "
                "destroy another mod's or the official stages. Back it up "
                "and resolve the conflict by hand, then re-run the install. "
                "This definite conflict is NOT releasable by "
                "--allow-content-conflict.")
            if msg not in conflicts:
                conflicts.append(msg)
            mapsel_conflicts.append(msg)
            step["conflict"] = True

    # W41: a ra2md.csf that already exists and is NOT one of ours (not
    # recorded in the current install record) is a definite preflight content
    # conflict that defaults to a refusal and stays refused even when the user
    # passes --allow-content-conflict. It is a loose WHOLE-FILE override of
    # the copy inside langmd.mix (W29): overwriting a foreign one would
    # destroy another mod's / a hand-edited string table, and a partial one
    # breaks startup. Covers created/replaced and the byte-identical-but-
    # unrecorded "adopt" case alike (same shape as the W34 MAPSELMD rule).
    for step in steps:
        if (step["name"] == CSF_NAME and step["dest_sha"] is not None
                and step["name"] not in old_entries):
            msg = (
                f"{CSF_NAME}: a non-ra2forge {CSF_NAME} already exists in the "
                f"game directory (not recorded as ours in {MANIFEST_NAME}). "
                "It is a WHOLE-FILE override of the official string table "
                "inside langmd.mix; overwriting it would destroy another "
                "mod's / a hand-edited CSF, and a partial/minimal file would "
                "make the official UI text render as MISSING:'...' (W40 A/E; "
                "NOT a startup-failure rule - W40 A proved a legal minimal "
                "CSF still boots, only a bad magic fails to start). Back it "
                "up and resolve the conflict by "
                "hand, then re-run the install. This definite conflict is NOT "
                "releasable by --allow-content-conflict.")
            if msg not in conflicts:
                conflicts.append(msg)
            csf_conflicts.append(msg)
            step["conflict"] = True

    # ORPHAN-FIX01: plan the exit of files the CURRENT record names and this
    # package dropped. Read-only; dangerous shapes become hard blockers here,
    # a file changed after install becomes a risk (strict refuses), the rest
    # is executed by install_package() after the copies, before the record.
    orphans = _plan_orphans(game, old_entries, {src.name for src in files})
    for o in orphans:
        if o["mode"] == "invalid_name":
            blockers.append(
                f"corrupt-manifest: the record names {o['name']!r}, which is "
                "not a plain file name inside the game directory, and the "
                "new package does not include it - refusing to plan its "
                "removal instead of guessing")
        elif o["mode"] in ("unsafe_slot", "unsafe_backup"):
            blockers.append(
                f"path-safety: recorded file {o['name']} is no longer the "
                f"plain file/slot this record recorded ({o['reason']}) - "
                "refusing to remove or restore it")
        elif o["mode"] == "invalid_backup":
            blockers.append(
                f"corrupt-manifest: entry {o['name']} records backup "
                f"{o['backup']!r}, which is not the "
                f"{o['name'] + BACKUP_SUFFIX} slot this tool writes - "
                "refusing to act on it")
        elif o["mode"] == "changed":
            risks.append(
                f"{o['name']} is recorded in {MANIFEST_NAME} but this package "
                "does not include it, and its sha256 no longer matches the "
                "record - it changed after install. Keeping it would leave an "
                "untracked file (and an untracked backup slot); deleting it "
                "would delete bytes nobody recorded. Resolve it manually "
                "('uninstall --force' to drop it, or remove/restore it by "
                "hand) and re-run the install.")
        elif o["mode"] == "missing":
            notices.append(
                f"{o['name']} is recorded in {MANIFEST_NAME} but already gone "
                "and this package does not include it - nothing to clean")
        elif o["mode"] == "remove" and not o.get("bak_ok", True):
            notices.append(
                f"the backup {o['name'] + BACKUP_SUFFIX} recorded for "
                f"{o['name']} is missing - {o['name']} will be removed "
                "without restoring anything")

    return {"blockers": blockers, "conflicts": conflicts,
            "mapsel_conflicts": mapsel_conflicts,
            "csf_conflicts": csf_conflicts,
            "risks": risks, "notices": notices, "steps": steps, "manifest": manifest,
            "corrupt_manifest": corrupt, "orphans": orphans,
            "identity": {
                "verdict": verdict,
                "old_package_id": old_pkg_id,
                "old_package_version": _manifest_str_field(manifest,
                                                           "package_version"),
                "old_package_digest": _manifest_str_field(manifest,
                                                          "package_digest"),
                "new_package_id": new_pkg_id,
                "new_package_version": pkg_ident["package_version"],
                "adopt_legacy": bool(adopt_legacy),
                "message": identity_msg,
            },
            "package_digest": package_digest_from_steps(steps)}


def _refusal_text(plan: dict, allowed: list[str] | None = None) -> str:
    """Full three-class report used as the InstallBlocked message."""
    lines = ["install blocked by preflight - no file has been written:"]
    if plan["blockers"]:
        lines.append("  hard blockers (never bypassable: path safety / corrupt "
                     "install record / backup protection):")
        lines += [f"    - {b}" for b in plan["blockers"]]
    if plan["conflicts"]:
        if allowed is None:
            lines.append("  definite content conflicts (strict mode refuses "
                         "them; sole escape: --allow-content-conflict):")
        else:
            lines.append("  definite content conflicts (released THIS run by "
                         "--allow-content-conflict, logged in the manifest):")
        lines += [f"    - {c}" for c in plan["conflicts"]]
    if plan.get("mapsel_conflicts"):
        lines.append("  NEVER-releasable MAPSELMD.INI conflicts (a whole-file "
                     "override of a foreign registration; refused even with "
                     "--allow-content-conflict):")
        lines += [f"    - {c}" for c in plan["mapsel_conflicts"]]
    if plan.get("csf_conflicts"):
        lines.append("  NEVER-releasable ra2md.csf conflicts (a loose "
                     "WHOLE-FILE override of the official string table inside "
                     "langmd.mix; refused even with --allow-content-conflict):")
        lines += [f"    - {c}" for c in plan["csf_conflicts"]]
    if plan["risks"]:
        lines.append("  unresolvable risks (state cannot be judged reliably; "
                     "strict mode refuses; resolve the state instead):")
        lines += [f"    - {r}" for r in plan["risks"]]
    if plan["notices"]:
        lines.append("  notices (do not block):")
        lines += [f"    - {n}" for n in plan["notices"]]
    return "\n".join(lines)


def _copy_verified(src: Path, dest: Path, name: str) -> str:
    """Copy src -> dest and prove the bytes actually landed (MEDIUM-1).

    DLC-HIGH3-FIX01 (MEDIUM-8): the copy itself goes through the staged,
    alias-proof primitive - it used to be shutil.copy2(), which follows an
    alias at dest, so an alias swapped in after the identity gate put PACKAGE
    bytes into an unlisted file outside the game directory and the read-back
    below went through the same alias and could not see it. Now the bytes are
    moved onto the slot as a directory entry, and the read-back reads the file
    that is really there: a mismatch raises, and the caller must NOT write the
    install record when this raises, so a broken copy is never recorded as
    success. (Full write rollback stays out of scope: see DLC_STRICT_AUDIT
    MEDIUM-3.)
    """
    src_sha = sha256_of(src)
    _stage_and_replace(src, dest, src_sha, "install")
    landed = sha256_of(dest)
    if landed != src_sha:
        raise OSError(
            f"integrity check failed for {name}: the bytes read back from "
            f"the game directory do not match the package member that was "
            f"just copied ({landed[:12]}... != {src_sha[:12]}...). "
            f"{MANIFEST_NAME} was NOT written; inspect the game directory "
            f"and any *.ra2forge.bak slots before retrying")
    return landed


def _open_staging_file(dest: Path, what: str) -> tuple[Path, int]:
    """Create an exclusive staging file next to dest and return (path, fd).

    DLC-HIGH3-FIX01 (HIGH-3). Two properties, and both are needed:

    1. the name carries a cryptographically random suffix, so it is not a name
       an outside writer can work out from the slot it wants to divert. The
       previous generation used <dest.name>.ra2forge-stage, which is derived
       from the slot and therefore plantable in advance;
    2. the name is refused with lstat-class checks IMMEDIATELY before
       os.open(), because O_CREAT|O_EXCL is NOT the guard it is often taken to
       be on Windows: for a LIVE link it fails with FileExistsError, but for a
       DANGLING reparse point it succeeds and creates the link's target - the
       bytes land outside the game directory. That was measured directly (the
       minimal experiment is in the DLC-HIGH3-FIX01 raw evidence), so the
       pre-open refusal is the part that closes HIGH-3 and O_EXCL is the
       backstop for a live alias.

    A leftover name here is never deleted: refusing is the point, and an
    unlink-then-open would only re-open the check-then-act window.
    """
    stage = dest.with_name(f"{dest.name}{STAGE_INFIX}.{secrets.token_hex(8)}")
    # lexists() is the lstat-class test: it is True for a dangling link, where
    # exists() would read the slot as empty and let the write through.
    if os.path.lexists(stage) or stage.is_symlink():
        raise OSError(f"{stage.name} already exists or is an alias - refusing "
                      f"to use it as the {what} staging file")
    fd = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                 | getattr(os, "O_BINARY", 0))
    return stage, fd


def _stage_and_replace(src: Path, dest: Path, expected_sha: str | None,
                       what: str) -> None:
    """Copy src -> dest without ever following an alias at dest.

    The bytes are staged in the game directory under an unpredictable name
    created with O_CREAT|O_EXCL and moved onto dest with os.replace(), which
    swaps the directory entry instead of writing through whatever name it finds
    there (measured for live, dangling, directory and hard-link shapes). An
    alias planted at the slot can therefore never divert the bytes outside the
    game directory: at worst the planted link is replaced by the staged file
    and the link's target keeps its own bytes.
    """
    if expected_sha is None:
        expected_sha = sha256_of(src)
    stage, fd = _open_staging_file(dest, what)
    try:
        with os.fdopen(fd, "wb") as fdst:
            with open(src, "rb") as fsrc:
                shutil.copyfileobj(fsrc, fdst)
        landed = sha256_of(stage)
        if landed != expected_sha:
            raise OSError(
                f"integrity check failed for the {what}: the staged bytes do "
                f"not match the source contents the plan verified "
                f"({landed[:12]}... != {expected_sha[:12]}...); nothing was "
                f"put in place")
        shutil.copystat(src, stage)
        # [更正 2026-10-04 · 依据 A-69 F-1] the gate that owns this commit, at
        # the instant of the commit.
        _refuse_aliased_landing_slot(dest, what)
        os.replace(stage, dest)
    except BaseException:
        try:
            stage.unlink()
        except OSError:
            pass
        raise


def _stage_text_and_replace(text: str, dest: Path, what: str) -> None:
    """DLC-HIGH3-FIX01 (HIGH-4): write text to dest through the same
    alias-proof primitive the file copies use.

    Used for the install record, which used to be a Path.write_text() - a call
    that follows an alias at the record name, so an alias planted after the
    preflight wrote ra2forge_install.json outside the game directory. The bytes
    are laid out exactly as text mode would lay them out (a lone "\\n" becomes
    os.linesep), so the record stays byte-identical to the previous generation.
    """
    data = text.encode("utf-8")
    if os.linesep != "\n":
        data = data.replace(b"\n", os.linesep.encode("utf-8"))
    stage, fd = _open_staging_file(dest, what)
    try:
        with os.fdopen(fd, "wb") as fdst:
            fdst.write(data)
        landed = sha256_of(stage)
        if landed != hashlib.sha256(data).hexdigest():
            raise OSError(f"integrity check failed for the {what}: the staged "
                          f"record bytes do not match what was meant to be "
                          f"written; nothing was put in place")
        # [更正 2026-10-04 · 依据 A-69 F-3] the record's own identity re-check,
        # at the instant the record is committed, not one write loop earlier.
        _refuse_aliased_landing_slot(dest, what)
        os.replace(stage, dest)
    except BaseException:
        try:
            stage.unlink()
        except OSError:
            pass
        raise


def _write_step(game: Path, step: dict) -> tuple[str, str]:
    """Execute one planned non-unchanged step: backup slot, then verified copy.

    Returns (backup_name, landed_sha). Keep the copies and post-write
    integrity raises here, not in install_package(): that function must
    contain nothing but preflight/state raises followed by the manifest
    write, so the replayable first-write-ordering assertion keeps holding.
    """
    name = step["name"]
    # DLC-HIGH2-FIX01 (MEDIUM-5): last identity gate before the copy - this
    # runs in the same instant as the write, the narrowest check-then-act
    # window this module can offer without O_NOFOLLOW-class primitives.
    # [更正 2026-10-04 · 依据 A-69 AS-23] it was not the narrowest and not the
    # same instant: one whole backup write sits between this gate and the copy
    # it claims to guard. Kept because it names the destination slot in the
    # message; the narrowest gate is now the one inside _stage_and_replace, at
    # the instant that call commits.
    err = _dest_safety_error(game, name)
    if err:
        raise OSError(f"destination identity check failed right before the "
                      f"write: {err} - nothing was written for {name}")
    dest = game / name
    backup_name = step["recorded_backup"]
    if step["backup"] == "keep":
        backup_name = name + BACKUP_SUFFIX
    elif step["backup"] == "create":
        # [更正 2026-10-04 · 依据 A-69 F-1, AS-09] the backup slot's OWN gate,
        # here, in front of the write that consumes it. Until now the only
        # backup-slot checks ran at the preflight and in install_package()'s
        # pre-write loop - both before the first write - while this is the step
        # that writes the slot, so an alias swapped into that window was
        # silently swapped away rather than refused. (The staged write re-runs
        # the same criteria at the instant of the commit; this one is the gate
        # that names the backup slot in its message.)
        bak_err = _bak_safety_error(game, name)
        if bak_err:
            raise OSError(f"backup slot refused right before the backup write: "
                          f"{bak_err} - nothing was written for {name}")
        _stage_and_replace(dest, game / (name + BACKUP_SUFFIX),
                           step["dest_sha"], "backup")
        backup_name = name + BACKUP_SUFFIX
    return backup_name, _copy_verified(step["src"], dest, name)


def _execute_orphan_plan(game: Path, plan: dict, actions: list[str],
                         undo: list) -> list[dict]:
    """ORPHAN-FIX01: execute the planned exit of the old record's dropped
    files. Runs AFTER the package copies landed and BEFORE the record is
    written, so a copy failure rolls back to the exact pre-run state and the
    new record never names a file that is already gone. Every slot is
    re-checked here, at the instant of its write or removal (same discipline
    as _write_step). Returns the removed_orphans audit list for the manifest.
    """
    removed: list[dict] = []
    old_pkg = (plan.get("manifest") or {}).get("package")
    for o in plan.get("orphans", []):
        mode = o["mode"]
        if mode in ("missing", "changed"):
            continue  # planned notes only; nothing to write, never adopted
        name = o["name"]
        dest = game / name
        err = _dest_safety_error(game, name)
        if err:
            raise OSError(
                f"orphan slot identity check failed right before the write: "
                f"{err} - nothing was written for {name}")
        backup = o.get("backup")
        if backup:
            bak_err = _bak_safety_error(game, name)
            if bak_err:
                raise OSError(
                    f"orphan backup slot identity check failed right before "
                    f"the write: {bak_err} - nothing was written for {name}")
        # journal BEFORE acting, so a failure anywhere below rolls this back
        undo.append({"kind": "orphan", "name": name,
                     "sha": o.get("sha256"), "old_pkg": old_pkg})
        if mode == "restore":
            bak = game / backup
            if not dest.is_file():
                raise OSError(
                    f"state changed under the preflight: orphan {name} is "
                    "gone; re-run the install")
            _stage_and_replace(bak, dest, None, "orphan-restore")
            bak.unlink()
            actions.append(
                f"restored   {backup} -> {name} (orphan: this package no "
                "longer includes it; the pre-install original is back)")
            removed.append({"name": name, "action": "restored_backup",
                            "backup": backup})
        elif mode == "remove_absent":
            if dest.is_file():
                dest.unlink()
            if backup:
                bak = game / backup
                if bak.is_file():
                    bak.unlink()
            actions.append(
                f"removed    {name} (orphan: this package no longer includes "
                "it; its backup slot held our own previous version - the "
                "file never had an original, both are gone)")
            removed.append({"name": name, "action": "removed_with_own_backup"})
        else:  # remove
            if dest.is_file():
                dest.unlink()
                actions.append(
                    f"removed    {name} (orphan: recorded by the previous "
                    "install, absent from this package)")
                removed.append({"name": name, "action": "removed"})
            else:
                actions.append(
                    f"missing    {name} (orphan already gone; its recorded "
                    "backup slot is missing too)")
                removed.append({"name": name, "action": "already_gone"})
    return removed


def _rollback(game: Path, undo: list,
              errors: list[str] | None = None) -> list[str]:
    """ORPHAN-FIX01 / UNSEAL-FIX02: best-effort undo of what a FAILED install
    already wrote.

    Each undo item is isolated in its own try/except Exception block so a
    failure restoring or removing one path never aborts rolling back the rest.
    Replaced files are restored from the backup slot created for them THIS run
    (pre-existing "keep" slots are restored but kept); created files are
    unlinked; an orphan removal is undone by re-installing the file from the
    previous package the old record names, when that package still holds bytes
    matching the recorded sha256. Any unrecoverable item or OS/step error is
    appended both to the returned report lines and (when supplied) to errors.
    """
    lines: list[str] = []
    for u in reversed(undo):
        item_name = (
            u.get("name")
            or (u.get("step") or {}).get("name")
            or "?"
        )
        try:
            if u["kind"] == "copy_step":
                step = u["step"]
                name = step["name"]
                dest = game / name
                if step["backup"] in ("create", "keep"):
                    slot = name + BACKUP_SUFFIX
                    bak = game / slot
                    if bak.is_file():
                        _stage_and_replace(bak, dest, None, "rollback-restore")
                        lines.append(
                            f"rolled back {name} (restored from {slot})")
                        if step["backup"] == "create":
                            try:
                                bak.unlink()
                            except Exception as unlink_exc:
                                msg = (f"rollback cleanup of {slot} failed: "
                                       f"{unlink_exc}")
                                lines.append(msg)
                                if errors is not None:
                                    errors.append(msg)
                        continue
                    msg = (
                        f"could not roll back {name}: its backup slot {slot} "
                        "is missing - the file is left as this failed install "
                        "wrote it")
                    lines.append(msg)
                    if errors is not None:
                        errors.append(msg)
                elif step["action"] == "created":
                    if dest.is_file():
                        dest.unlink()
                    lines.append(f"rolled back {name} (created file removed)")
                else:
                    msg = (
                        f"could not roll back {name}: a replaced file without "
                        "a backup slot cannot be restored - left as written")
                    lines.append(msg)
                    if errors is not None:
                        errors.append(msg)
            elif u["kind"] == "orphan":
                name = u["name"]
                dest = game / name
                old_pkg = u.get("old_pkg")
                src = (Path(old_pkg) / name) if old_pkg else None
                if (src is not None and src.is_file()
                        and u.get("sha")
                        and sha256_of(src) == u["sha"]):
                    _stage_and_replace(src, dest, u["sha"], "rollback-orphan")
                    lines.append(
                        f"rolled back the orphan removal of {name} "
                        f"(re-installed from the previous package {old_pkg})")
                else:
                    msg = (
                        f"could not roll back the orphan removal of {name}: "
                        "the previous package is gone or does not match the "
                        "recorded sha256 - whatever the pre-upgrade state "
                        "was for this file, it is not restored by this run")
                    lines.append(msg)
                    if errors is not None:
                        errors.append(msg)
        except Exception as exc:
            msg = f"rollback of {item_name} failed: {exc}"
            lines.append(msg)
            if errors is not None:
                errors.append(msg)
    return lines


def install_package(package_dir, game_dir, force: bool = False, *,
                    strict: bool = True,
                    allow_content_conflict: bool = False,
                    adopt_legacy: bool = False,
                    version_guard: dict | None = None) -> dict:
    """Copy a built package into a game directory, backing up what it replaces.

    DLC-STRICT01: everything is preflighted read-only first (preinstall_plan).
    With the default strict=True a definite content conflict or an
    unresolvable risk refuses the whole install (InstallBlocked) BEFORE the
    first write, so a refused install leaves the directory byte-identical.
    allow_content_conflict=True releases ONLY the definite-content-conflict
    class; each released file is printed and recorded under
    precheck.allowed_content_conflicts in the manifest. force is accepted for
    signature compatibility but has never had an effect in this function -
    in particular it can NEVER override a package-identity refusal
    (PKG-IDENT01). adopt_legacy=True (--adopt-legacy) is the explicit
    assertion that this install is the intended successor of a record whose
    package_id is undeclared ("unknown"); it releases the identity gate ONLY,
    nothing else.

    W43/S3: ``version_guard`` is an OPT-IN W38-S1 guard context.  When
    supplied, classify() runs BEFORE preinstall_plan (i.e. before the L0
    gamemd.exe existence check is allowed to stand in for identity) and any
    non-KNOWN_GOOD verdict refuses with ZERO writes (exit 20/21/22).  When
    None (default) the behaviour is byte-for-byte v12's.
    """
    game = Path(game_dir)
    _s3_guard_gate("E1", game, version_guard)
    plan = preinstall_plan(package_dir, game, adopt_legacy=adopt_legacy)
    identity = plan["identity"]

    # PKG-IDENT01: the identity verdict gates BEFORE the conflict/risk
    # machinery (after the corrupt-record/path-safety blockers, which must
    # stay first - a record that failed its shape checks proves no identity).
    if identity["verdict"] in ("reject_mismatch", "reject_legacy"):
        kind = ("package_mismatch" if identity["verdict"] == "reject_mismatch"
                else "legacy_adopt_required")
        lines = ["install blocked by package identity - no file has been "
                 "written:", f"  - {identity['message']}"]
        report = _refusal_text(plan)
        if report:
            lines.append("  full preflight report (informational; releasing "
                         "these classes would still NOT pass the identity "
                         "gate):")
            lines += [f"    {ln}" for ln in report.splitlines()[1:]]
        raise PackageIdentityBlocked("\n".join(lines), kind=kind, report=plan)

    if plan["blockers"]:
        kind = "corrupt_manifest" if plan["corrupt_manifest"] else "path_safety"
        raise InstallBlocked(_refusal_text(plan), kind=kind, report=plan)
    # W34: a foreign MAPSELMD.INI is a definite content conflict that the
    # escape hatch must never release - no silent overwrite of a whole-file
    # campaign-progression registration.
    if plan.get("mapsel_conflicts"):
        raise InstallBlocked(_refusal_text(plan), kind="content_conflict",
                             report=plan)
    # W41: a foreign loose ra2md.csf is a definite content conflict that the
    # escape hatch must never release - no silent overwrite of a whole-file
    # string-table override (same never-releasable rule as MAPSELMD.INI).
    if plan.get("csf_conflicts"):
        raise InstallBlocked(_refusal_text(plan), kind="content_conflict",
                             report=plan)
    allowed: list[str] = []
    if plan["conflicts"]:
        if allow_content_conflict:
            allowed = list(plan["conflicts"])
        else:
            raise InstallBlocked(_refusal_text(plan), kind="content_conflict",
                                 report=plan)
    if strict and plan["risks"]:
        # nothing is released here even with allow_content_conflict: the run
        # is refused, so the conflicts must not be advertised as released
        raise InstallBlocked(_refusal_text(plan), kind="risk", report=plan)

    # Re-verify the planned-from state right before writing (still zero
    # writes): refuse if anything moved between the preflight reads and here.
    for step in plan["steps"]:
        dest = game / step["name"]
        # DLC-HIGH2-FIX01 (MEDIUM-5): re-run the FULL identity gates at action
        # time - the content re-checks below cannot see an alias swapped into
        # the slot inside the preflight->write window when the victim carries
        # the very bytes the plan recorded.
        err = _dest_safety_error(game, step["name"])
        if err:
            raise InstallBlocked(
                f"state changed under the preflight: {step['name']} no longer "
                f"passes the destination identity checks ({err}) - re-run the "
                "install", kind="path_safety", report=plan)
        now_sha = sha256_of(dest) if dest.is_file() else None
        if now_sha != step["dest_sha"]:
            raise InstallBlocked(
                f"state changed under the preflight: {step['name']} is no "
                "longer in the state this plan was built from - re-run the "
                "install", kind="state_changed", report=plan)
        # DLC-HIGH1-FIX01 (MEDIUM-1): the package source is re-checked too -
        # until now only the destination side had a re-verification, so a
        # package rewritten after the preflight was installed with the
        # planned-time sha recorded instead of the bytes actually shipped.
        try:
            src_now = sha256_of(step["src"])
        except OSError as exc:
            raise InstallBlocked(
                f"state changed under the preflight: package member "
                f"{step['name']} became unreadable ({exc}) - re-run the "
                "install", kind="state_changed", report=plan) from exc
        if src_now != step["new_sha"]:
            raise InstallBlocked(
                f"state changed under the preflight: package member "
                f"{step['name']} changed after the plan was built (its bytes "
                "no longer match the planned sha256) - re-run the install",
                kind="state_changed", report=plan)
        # DLC-HIGH2-FIX01 (HIGH-2, TOCTOU side): the backup slot identity is
        # re-checked here too, so a link swapped in after the preflight is
        # refused before the first write instead of being written through.
        if step["backup"] in ("create", "keep"):
            bak_err = _bak_safety_error(game, step["name"])
            if bak_err:
                raise InstallBlocked(
                    f"state changed under the preflight: backup slot "
                    f"{step['name'] + BACKUP_SUFFIX} no longer passes the "
                    f"identity checks ({bak_err}) - re-run the install",
                    kind="backup_protection", report=plan)
            bak = game / (step["name"] + BACKUP_SUFFIX)
            if step["backup"] == "create" and bak.exists():
                raise InstallBlocked(
                    f"state changed under the preflight: backup slot "
                    f"{bak.name} appeared after the plan was built - refusing "
                    "to overwrite a backup slot",
                    kind="backup_protection", report=plan)
            if step["backup"] == "keep" and not bak.is_file():
                raise InstallBlocked(
                    f"state changed under the preflight: backup slot "
                    f"{bak.name} is gone after the plan was built - re-run "
                    "the install", kind="backup_protection", report=plan)

    # DLC-HIGH3-FIX01 (HIGH-4): the install record is a slot too, and its
    # identity used to be checked in the preflight and in uninstall() only -
    # never here. An alias planted at it inside the preflight->write window
    # diverted the record itself outside the game directory, which is the one
    # artefact that tells our files and backup slots apart from foreign ones.
    rec_err = _record_slot_error(game)
    if rec_err:
        raise InstallBlocked(
            f"state changed under the preflight: the install record "
            f"{MANIFEST_NAME} no longer passes its identity checks ({rec_err}) "
            "- re-run the install", kind="corrupt_manifest", report=plan)

    # ---- first filesystem write happens below this line ----
    # ORPHAN-FIX01: the whole write phase is journaled; any failure from here
    # to the record write rolls back what this run already committed
    # (best-effort, reported) instead of leaving an unrecorded half-install.
    actions: list[str] = []
    entries: list[dict] = []
    undo: list = []
    rolled_back = False
    try:
        for step in plan["steps"]:
            name = step["name"]
            if step["action"] == "unchanged":
                entry = {"name": name, "action": "unchanged",
                         "bytes": step["size"], "sha256": step["new_sha"],
                         "backup": step["recorded_backup"]}
                if step["original_absent"]:
                    entry["original_absent"] = True
                entries.append(entry)
                actions.append(f"unchanged  {name} (already up to date)")
                continue
            if step["backup"] == "keep":
                actions.append(f"kept       {name + BACKUP_SUFFIX} (original "
                               "backup of a previous install, not overwritten)")
            elif step["backup"] == "create":
                actions.append(f"backup     {name} -> {name + BACKUP_SUFFIX}")
            undo.append({"kind": "copy_step", "step": step, "name": name})
            backup_name, landed = _write_step(game, step)
            entry = {"name": name, "action": step["action"],
                     "bytes": step["size"], "sha256": landed,
                     "backup": backup_name}
            if step["original_absent"]:
                entry["original_absent"] = True
            entries.append(entry)
            actions.append(f"{step['action']:10s} {name} ({step['size']} bytes)")
            if step["conflict"]:
                actions.append(f"ALLOWED    {name}: content conflict released by "
                               "--allow-content-conflict (recorded in the manifest)")

        # ORPHAN-FIX01: the old record's dropped files leave AFTER the copies
        # landed, BEFORE the record is written.
        removed_orphans = _execute_orphan_plan(game, plan, actions, undo)

        warnings = plan["risks"] + plan["notices"]
        # PKG-IDENT01: every entry carries the digest of the package version
        # that supplied it; the record gains the package's declared identity.
        pkg_digest = plan["package_digest"]
        for entry in entries:
            entry["source_package_digest"] = pkg_digest
        manifest = {
            "tool": "ra2forge",
            "version": TOOL_VERSION,
            "package_id": identity["new_package_id"],
            "package_version": identity["new_package_version"],
            "package_digest": pkg_digest,
            "installed_at": datetime.now().isoformat(timespec="seconds"),
            "package": str(Path(package_dir).resolve()),
            "game_dir": str(game.resolve()),
            "files": entries,
            "warnings": warnings,
            "precheck": {
                "strict": strict,
                "allowed_content_conflicts": allowed,
                "risks": plan["risks"],
                "notices": plan["notices"],
                "conflicts_seen": plan["conflicts"],
                "blockers": [],
            },
        }
        if manifest is not None and plan["manifest"] is not None:
            # audit trail only - judgments never read this block (they keep
            # using the per-file record + sha256 discipline of ORPHAN-FIX01)
            manifest["supersedes"] = {
                "package_id": identity["old_package_id"],
                "package_version": identity["old_package_version"],
                "package_digest": identity["old_package_digest"],
                "package": plan["manifest"].get("package"),
                "adopted_legacy": identity["verdict"] == "adopt",
            }
        if removed_orphans:
            manifest["removed_orphans"] = removed_orphans
        manifest_path = game / MANIFEST_NAME
        # SEAL-CHAIN01: this install REPLACES the record; keep its previous
        # bytes so a seal-write failure can restore them exactly. The
        # preflight already parsed this record as UTF-8 JSON, so the decode
        # below cannot fail for the state this function was planned from.
        prev_record_text: str | None = None
        if manifest_path.is_file():
            prev_record_text = (manifest_path.read_bytes()
                                .decode("utf-8-sig")
                                .replace("\r\n", "\n").replace("\r", "\n"))
        _stage_text_and_replace(
            json.dumps(manifest, indent=2, ensure_ascii=False), manifest_path,
            "install record")
        # SEAL-CHAIN01: the seal is written AFTER the record it protects. If
        # it cannot be written, the fresh record is rolled back to the exact
        # previous bytes (or removed, when there was none) rather than left
        # standing without its seal - a seal-era record without a seal is the
        # REFUSED state (CLI exit 7 on uninstall), so an install must never
        # manufacture one silently.
        try:
            write_install_seal(game, manifest)
        except BaseException as seal_exc:
            # UNSEAL-FIX02 (W26): isolate record rollback and package file
            # rollback in separate try/except blocks so a failure in either
            # never skips the other, and aggregate all errors cleanly instead
            # of swallowing PermissionError and claiming success.
            rec_err: Exception | None = None
            try:
                if prev_record_text is None:
                    manifest_path.unlink()
                else:
                    _stage_text_and_replace(prev_record_text, manifest_path,
                                            "install record restore")
            except Exception as r_exc:
                rec_err = r_exc

            rollback_errors: list[str] = []
            file_exc: Exception | None = None
            report: list[str] = []
            try:
                report = _rollback(game, undo, rollback_errors)
            except Exception as f_exc:
                file_exc = f_exc
                rollback_errors.append(f"file rollback aborted: {f_exc}")
            rolled_back = True

            if not isinstance(seal_exc, Exception):
                raise

            if rec_err is None and not rollback_errors:
                msg = (
                    f"the install seal ({SEAL_NAME}) could not be written "
                    f"({seal_exc}) - the install record was rolled back to its "
                    "previous bytes, the package files are UNCHANGED; nothing "
                    "was left in the unsealed state"
                )
                if report:
                    msg += (
                        "\n  install aborted mid-write; best-effort "
                        "rollback of what this run wrote:\n    "
                        + "\n    ".join(report)
                    )
                raise OSError(msg) from seal_exc

            summary = (
                f"the install seal ({SEAL_NAME}) could not be written "
                f"({seal_exc})"
            )
            if rec_err is not None:
                action_desc = (
                    f"remove {MANIFEST_NAME}" if prev_record_text is None
                    else f"restore {MANIFEST_NAME} to its previous bytes"
                )
                rec_note = (
                    f"install record rollback FAILED (could not {action_desc}: "
                    f"{rec_err}; {MANIFEST_NAME} may be left standing without "
                    f"a matching {SEAL_NAME})"
                )
            else:
                rec_note = (
                    f"install record rolled back cleanly ({MANIFEST_NAME} "
                    "restored/removed)"
                )
            if rollback_errors:
                file_note = (
                    f"package file rollback had failures "
                    f"({len(rollback_errors)}): "
                    + "; ".join(rollback_errors)
                )
            elif report:
                file_note = (
                    "package files rolled back cleanly (all other writes "
                    "of this run undone)"
                )
            else:
                file_note = "package files were unchanged"
            msg = f"{summary} - {rec_note}; {file_note}"
            if report:
                msg += (
                    "\n  install aborted mid-write; best-effort rollback of what "
                    "this run wrote:\n    " + "\n    ".join(report)
                )
            raise OSError(msg) from (rec_err or file_exc or seal_exc)
        actions.append(f"written    {SEAL_NAME}")
    except BaseException as exc:
        if not rolled_back:
            report = _rollback(game, undo)
            if report:
                if isinstance(exc, Exception):
                    raise OSError(
                        f"{exc}\n  install aborted mid-write; best-effort "
                        "rollback of what this run wrote:\n    "
                        + "\n    ".join(report)) from exc
        raise
    actions.append(f"written    {MANIFEST_NAME}")
    return {"game_dir": game, "manifest": manifest_path, "actions": actions,
            "warnings": warnings, "files": entries, "risks": plan["risks"],
            "notices": plan["notices"], "conflicts_allowed": allowed}


def uninstall(game_dir, legacy: bool = False, drop_legacy_battlemd: bool = False,
              force: bool = False, *,
              version_guard: dict | None = None) -> dict:
    """Undo an install: delete our files, restore every backup, drop the manifest.

    With legacy=True it also cleans the artefacts of ra2forge <= FORGE-1
    (BATTLEMD.INI override, loose maps, mix, ra2forge_uninstall.txt).

    SEAL-CHAIN01: before the first unlink, the install seal is judged. A
    seal-era manifest (tool >= 0.7) whose seal is MISSING, MISMATCHED,
    CORRUPT or ALIASED refuses the whole uninstall - nothing removed, nothing
    restored, the record kept - and the report carries
    refused="seal_missing" / "seal_mismatch" (CLI exits 7 / 8). --force does
    NOT release this gate. Old manifests (no seal) uninstall as before, with
    an explicit degraded-mode warning. On a completed uninstall the seal is
    removed together with the record it protects.

    UNSEAL-FIX01 (tool 0.8): the seal removal is the FINAL cleanup step -
    by then the record is deleted and every recorded file was already
    processed - so a failure there (a read-only seal, an open handle) must
    not abort the command or lose the report. It becomes an explicit
    warning (stray seal path + recovery), the report carries
    status="completed_with_warnings" and the CLI exits 10 (tool 0.7 exited
    1 here and lost the actions report). The report dict always carries
    one of three statuses - "completed" / "completed_with_warnings" /
    "failed" - mirrored by uninstall --json; the exit-code table is quoted
    in uninstall --help, VERIFY.md and UNSEAL_FIX.md. A normal (writable)
    seal is still removed silently, exactly as before.
    """
    game = Path(game_dir)
    # W43/S3: E3 uninstall guard. v12 had ONLY game.is_dir() (L0); the S1
    # identity verdict now gates the delete/restore/record-removal entry.
    _s3_guard_gate("E3", game, version_guard)
    if not game.is_dir():
        raise FileNotFoundError(f"game directory not found: {game}")
    actions: list[str] = []
    warnings: list[str] = []
    seal_removed = False
    # UNSEAL-FIX01: status bookkeeping for the three report states.
    cleanup_failed = False
    record_refused = False
    record_unlink_failed = False
    legacy_failed = False

    manifest_path = game / MANIFEST_NAME
    # DLC-HIGH3-FIX01 (A1 / HIGH-4 read side / LOW-8): the install record is
    # checked BEFORE it is read, and with the full identity criteria. It used
    # to be read first and judged afterwards, so the alias was already
    # followed into the parser; and only a symbolic link was judged at all.
    record_err = _record_slot_error(game)
    manifest = None if record_err else _load_manifest(manifest_path)
    if record_err:
        warnings.append(
            f"{MANIFEST_NAME} does not qualify as a plain install record "
            f"({record_err}) - refusing to read or act on it; resolve it "
            "manually")
        # UNSEAL-FIX01: nothing was acted on, so the report says so; the
        # CLI exit stays 0 (behavior unchanged since tool 0.7) and the
        # table in uninstall --help documents this sub-case.
        record_refused = True
    elif manifest is None:
        warnings.append(f"no {MANIFEST_NAME} in {game}: nothing recorded to remove "
                        f"(use --legacy for installs made by an older ra2forge)")
        if (game / SEAL_NAME).is_file():
            warnings.append(
                f"a {SEAL_NAME} is present without an install record - left "
                "in place (this tool only removes it as part of the "
                "record's completed lifecycle); delete it by hand if it is "
                "stale")
    else:
        # SEAL-CHAIN01: the seal gate, BEFORE the first unlink. uninstall()
        # deletes and restores exactly what this record names, so on an
        # unverified record that is the W21 UNCOVERED §3 forgery surface -
        # refuse instead of trusting it. --force never releases this: force
        # means "delete a recorded file whose bytes changed", never "trust a
        # record whose seal does not check out".
        seal_info = evaluate_seal(game, manifest, manifest_path)
        if seal_info["state"] == "not_expected":
            if seal_info["detail"]:
                warnings.append(f"install seal note: {seal_info['detail']}")
            warnings.append(
                f"legacy manifest (tool version "
                f"{manifest.get('version')!r}): no install seal expected - "
                "proceeding WITHOUT seal protection (degraded mode; the "
                "record is not verified against a seal)")
        elif seal_info["state"] != "ok":
            kind = ("seal_missing" if seal_info["state"] == "missing"
                    else "seal_mismatch")
            warnings.append(
                f"uninstall REFUSED: install seal {seal_info['state']} - "
                f"{seal_info['detail']}. The manifest and every recorded "
                "file and backup slot are UNTOUCHED. Run 'python -m "
                "ra2forge verify --game <dir>' for the drift report; if "
                "the manifest is the one you want, re-run the install of "
                "the SAME package to re-establish the seal, then uninstall "
                "again. --force does NOT bypass this refusal.")
            return {"game_dir": game, "actions": actions,
                    "warnings": warnings, "seal": seal_info,
                    "refused": kind, "status": "failed"}
        seal_removed = seal_info["state"] == "ok"
        refused = False
        for entry in reversed(manifest.get("files", [])):
            name = entry.get("name", "")
            if not name:
                continue
            # DLC-HIGH2-FIX01 (MEDIUM-6): the record is trusted for WHAT was
            # installed, never for WHERE to write. install() validates every
            # destination name; uninstall() must apply the same discipline,
            # or a hand-edited / foreign record turns 'uninstall' into
            # deletes and restores outside the game directory.
            if (name in (".", "..") or Path(name).name != name
                    or "/" in name or "\\" in name):
                warnings.append(
                    f"manifest entry {name!r} is not a plain file name inside "
                    f"the game directory - refusing to touch it (the record "
                    f"may be corrupted or foreign); {MANIFEST_NAME} is kept")
                refused = True
                continue
            dest = game / name
            # DLC-HIGH1-FIX01 (HIGH-1 follow-up): verify the slot's identity
            # before touching it. What this manifest installed was a plain
            # file; a symbolic link (or any non-regular file) at the slot now
            # means the recorded file is not what is there. Removing a link
            # restores nothing, and restoring through it would clobber a file
            # the manifest never listed - so refuse, speak, and keep the
            # backup for manual recovery.
            # [更正 2026-10-04 · 依据 A-69 F-5, A-70 L-4] the slot gets the SAME
            # five criteria the install side applies, not the two forms this
            # check could see: is_symlink() has no signal for a hard link, and
            # the inline form also knew nothing about the backup namespace, so
            # a forged record entry <name>.ra2forge.bak used to be deletable.
            slot_err = _dest_safety_error(game, name)
            if slot_err:
                warnings.append(
                    f"{name} no longer qualifies as the plain file this "
                    f"manifest recorded ({slot_err}) - refusing to remove or "
                    f"restore it; the backup "
                    f"{name + BACKUP_SUFFIX} (if any) is kept, resolve the "
                    f"slot manually")
                refused = True
                continue
            backup = entry.get("backup")
            if backup:
                # DLC-HIGH2-FIX01 (MEDIUM-6): only the slot name this tool
                # writes is ever consumed as a backup.
                if backup != name + BACKUP_SUFFIX:
                    warnings.append(
                        f"manifest backup name {backup!r} is not the "
                        f"{name + BACKUP_SUFFIX} slot this tool writes - "
                        f"refusing to consume it; {MANIFEST_NAME} is kept")
                    refused = True
                    continue
                bak = game / backup
                # [更正 2026-10-04 · 依据 A-70 L-4] the legacy path has been
                # gating this same slot with the full five criteria all along;
                # the main path still had the HIGH-2 two-form check, so a
                # hard-linked backup was read through its shared inode and the
                # slot was "restored" to another, unlisted file's bytes while
                # 'restored' was printed. Same function as the legacy side.
                bak_err = _bak_safety_error(game, name)
                if bak_err:
                    warnings.append(
                        f"{bak_err} - refusing to read it as the backup this "
                        f"manifest recorded; resolve it manually")
                    refused = True
                    continue
                # [更正 2026-10-05 · 依据 DLC-HARDEN4-REVIEW02 F-01 / FIX02 F1]
                # the criteria matched the legacy side and the ORDER did not:
                # this gate sat below dest.unlink(), so a slot that failed it
                # (hard link, live or dangling alias, directory) had already
                # lost the installed file - refused to restore, nothing left to
                # restore onto, only the record kept. It is judged above, before
                # anything moves, so a refusal leaves THAT entry's file exactly
                # where it is instead of deleting first and refusing to restore
                # second. (The legacy comment at the removed-original branch
                # calls this "leaves the game directory byte-identical"; what a
                # refusal guarantees is the refused entry's own file - the other
                # entries of the same record are still processed. Measured:
                # DLC-HARDEN4-FIX02 raw/MB_*_post.txt, fsdiff 2, not 0.)
            # ORPHAN-FIX01: the record can prove the backup slot holds OUR own
            # previous version (the file was created by an earlier install and
            # later replaced) - such a slot is removed with the file, never
            # "restored" over a file that never had an original. Old manifests
            # without the flag behave exactly as before.
            absent = bool(entry.get("original_absent"))
            if not dest.is_file():
                actions.append(f"missing    {name} (already gone)")
            elif force or sha256_of(dest) == entry.get("sha256"):
                try:
                    dest.unlink()
                except OSError as exc:
                    warnings.append(
                        f"could not remove {name} ({exc}) - kept; "
                        f"{MANIFEST_NAME} is kept for a later retry")
                    refused = True
                    continue
                actions.append(f"removed    {name}")
            else:
                warnings.append(
                    f"{name} changed after install (sha256 mismatch) - kept; "
                    f"re-run with --force to delete it anyway")
                # DLC-HIGH2-FIX01 (MEDIUM-7): the recorded lifecycle did not
                # complete - keep the record so this refusal stays visible
                # and the --force re-run the warning promises can happen.
                refused = True
                continue
            if backup:
                if bak.is_file():
                    if absent:
                        try:
                            bak.unlink()
                        except OSError as exc:
                            warnings.append(
                                f"could not remove backup {backup} ({exc}) - "
                                f"{name} was removed, {MANIFEST_NAME} is kept")
                            refused = True
                        else:
                            actions.append(
                                f"removed    {backup} (original absent - the slot "
                                "held our own previous version, nothing to restore)")
                    else:
                        # DLC-HIGH1-FIX01: identity re-check immediately before
                        # the restore write - the slot must still be empty, never
                        # a link or a file that appeared after the recorded file
                        # was removed (a restore through it would write into
                        # whatever that alias points at).
                        if dest.is_symlink() or dest.exists():
                            warnings.append(
                                f"cannot restore {backup} -> {name}: something "
                                f"now occupies the slot after the recorded file "
                                f"was removed - backup {backup} kept, resolve "
                                f"the slot manually")
                            refused = True
                            continue
                        # expected_sha=None: the staged bytes are verified against
                        # the backup itself - the manifest records the sha of what
                        # was INSTALLED, not of the original the backup holds.
                        try:
                            _stage_and_replace(bak, dest, None, "restore")
                        except OSError as exc:
                            warnings.append(
                                f"could not restore {backup} -> {name} "
                                f"({exc}) - backup {backup} kept, resolve the "
                                "slot manually")
                            refused = True
                            continue
                        actions.append(f"restored   {backup} -> {name}")
                        try:
                            bak.unlink()
                        except OSError as exc:
                            warnings.append(
                                f"restored {name}, but could not remove "
                                f"leftover backup slot {backup} ({exc}); "
                                f"delete {backup} manually")
                elif not absent:
                    warnings.append(
                        f"backup {backup} is missing - {name} was not restored")
        if refused:
            # DLC-HIGH2-FIX01 (MEDIUM-7): deleting the record while entries
            # were refused orphaned the very backup slots the warnings point
            # at (a link at the slot + an orphan .bak + 'nothing recorded to
            # remove' afterwards). The record is what tells our backup slots
            # apart from foreign files - keep it until the user resolves the
            # refusals and re-runs uninstall.
            warnings.append(
                f"{MANIFEST_NAME} is KEPT: at least one entry above was "
                "refused, so the install record stays for a later 'uninstall' "
                "to retry once the refused slots are resolved manually")
        else:
            manifest_removed = False
            try:
                manifest_path.unlink()
            except OSError as exc:
                record_unlink_failed = True
                warnings.append(
                    f"could not remove install record {MANIFEST_NAME} ({exc}) - "
                    "every recorded file above was already processed, so "
                    f"{MANIFEST_NAME} (and {SEAL_NAME}, if present) is kept "
                    "to match the surviving record; clear the obstacle (e.g. "
                    "remove the read-only attribute) and delete it or re-run "
                    "uninstall")
            else:
                manifest_removed = True
                actions.append(f"removed    {MANIFEST_NAME}")
            # SEAL-CHAIN01: the seal completes its lifecycle together with
            # the record it protects - only when the seal itself was verified
            # (a stale seal on a legacy record is left for the user, never
            # silently consumed).
            # UNSEAL-FIX01 (W25, tool 0.8): this is the FINAL cleanup step -
            # the record is already deleted and every recorded file was
            # already processed above - so a failure here (a read-only seal,
            # an open handle: PermissionError / WinError 5) must not abort
            # the command and lose the actions report, and must not read as
            # a total failure of an uninstall that DID complete its main
            # lifecycle. The failure becomes an explicit warning (naming the
            # stray seal, where it stands and how to recover), the report
            # carries status="completed_with_warnings" and the CLI exits
            # EXIT_UNINSTALL_PARTIAL (10). This is NOT "the seal can be
            # ignored": the stray seal is disclosed every subsequent time
            # (uninstall / verify) until removed. A normal (writable) seal
            # is still removed silently, exactly as before.
            if manifest_removed and seal_removed and (game / SEAL_NAME).is_file():
                try:
                    (game / SEAL_NAME).unlink()
                    actions.append(f"removed    {SEAL_NAME}")
                except OSError as exc:
                    cleanup_failed = True
                    warnings.append(
                        f"the install seal ({SEAL_NAME}) could not be "
                        f"removed ({exc}) - the uninstall itself is "
                        "COMPLETE (the record was deleted and every "
                        "recorded file was processed above), but the seal "
                        "file is left standing at "
                        f"{game / SEAL_NAME}; clear the obstacle (e.g. "
                        "remove the read-only attribute or close the "
                        "process holding the file) and delete it by hand, "
                        "or re-run the install of the SAME package and "
                        "uninstall again")

    if legacy:
        # files already handled by the manifest (removed + restored to their
        # pre-install state) must not be deleted again by the legacy pass
        handled = {e.get("name", "") for e in (manifest or {}).get("files", [])}
        legacy_failed = _uninstall_legacy(
            game, actions, warnings, drop_legacy_battlemd, handled)

    # UNSEAL-FIX01 / UNSEAL-FIX02: the three report states.
    # "completed_with_warnings" is reserved for partial completion (main
    # lifecycle done, final seal cleanup failed; CLI exit 10). "failed"
    # covers refusals that acted on nothing (seal gate -> CLI 7/8;
    # non-qualifying record slot -> CLI 0, unchanged since tool 0.7) as well
    # as post-entry record-removal failure (failed_step="manifest_unlink" or
    # "legacy_manifest_unlink" -> CLI 1, actions preserved in report).
    failed_step = None
    if record_unlink_failed or legacy_failed:
        status = "failed"
        failed_step = ("manifest_unlink" if record_unlink_failed
                       else "legacy_manifest_unlink")
    elif cleanup_failed:
        status = "completed_with_warnings"
    elif record_refused:
        status = "failed"
    else:
        status = "completed"
    report = {"game_dir": game, "actions": actions, "warnings": warnings,
              "refused": None, "status": status}
    if failed_step:
        report["failed_step"] = failed_step
    return report


def _uninstall_legacy(game: Path, actions: list[str], warnings: list[str],
                      drop_legacy_battlemd: bool,
                      handled: set[str] | None = None) -> bool:
    """Clean the artefacts of a ra2forge <= FORGE-1 install.

    DLC-UNINSTALL-LEGACY01: this path used to trust the legacy listing and the
    slots blindly (no alias checks, no name discipline, record deleted even
    when entries could not be resolved). It now reuses exactly the same family
    of gates as install_package()/uninstall(): _dest_safety_error for every
    listed name, _bak_safety_error for every backup slot, _stage_and_replace
    for every restore write, and a refused flag that keeps the listing alive
    whenever an entry could not be resolved.
    """
    handled = handled or set()
    listing = game / LEGACY_MANIFEST
    # S-1 family: the legacy record itself is never read or consumed through
    # an alias. A live link would let a file OUTSIDE the game directory drive
    # the deletion set; a dangling link must not read as "no record" (that is
    # the exact mechanism HIGH-2 was found through) - refuse the whole legacy
    # pass, including the fallback, and leave everything untouched.
    # [更正 2026-10-04 · 依据 A-70 H-1] that used to be exactly two forms
    # (is_symlink + exists-not-is_file), while the install record gets five: a
    # HARD link at this name is invisible to both, and its shared inode then
    # feeds the deletion set. The audit's "应复用而未复用" is the point - the
    # legacy record now goes through the very same derived-name criteria as the
    # install record (_record_slot_error is this call with MANIFEST_NAME).
    listing_err = _derived_slot_error(game, LEGACY_MANIFEST, "legacy record")
    if listing_err:
        warnings.append(
            f"{listing_err} - refusing to act on an aliased legacy record; the "
            "whole legacy pass is skipped and nothing is touched. Resolve it "
            "manually")
        return
    record_present = listing.is_file()
    names: list[str] = []
    if record_present:
        text = listing.read_text(encoding="ascii", errors="replace")
        names = [ln.strip() for ln in text.splitlines()[1:] if ln.strip()]
    else:
        warnings.append(
            f"no {LEGACY_MANIFEST}: falling back to the known legacy artefact set "
            f"(the campaign MIX, loose ECH*.MAP files and a marked BATTLEMD.INI)")
        names = [MIX_NAME] + sorted(p.name for p in game.glob("ECH*.MAP"))
        official = game / LEGACY_BATTLE_INI
        # never read the override through an alias while collecting it: the
        # marker verdict belongs to the record's own slot, not to whatever a
        # planted link points at.
        # [更正 2026-10-04 · 依据 A-70 L-5] two forms again, so a hard link at
        # this name read an outside file's bytes and let them decide whether
        # BATTLEMD.INI joins the deletion set. Same criteria as everywhere else.
        official_err = _derived_slot_error(game, LEGACY_BATTLE_INI,
                                           "official battle list")
        if official_err:
            warnings.append(
                f"{official_err} - refusing to read it through an alias; it is "
                "not collected either; resolve it manually")
        elif official.is_file() and FORGE_MARKER in official.read_bytes()[:400]:
            names.append(LEGACY_BATTLE_INI)

    refused = False
    for name in names:
        dest = game / name
        if name in handled:
            actions.append(f"kept       {name} (already restored by "
                           f"{MANIFEST_NAME}; pre-install state wins)")
            continue
        # MEDIUM-6 family: the legacy record is trusted for WHAT was installed
        # in the past, never for WHERE to act. Same name/slot discipline as
        # uninstall(): separators, '..', aliases, non-regular files, hard
        # links and backup-namespace names are refused here, so a hand-edited
        # listing cannot turn the legacy cleanup into deletes outside the
        # game directory.
        err = _dest_safety_error(game, name)
        if err:
            warnings.append(
                f"legacy record entry {name!r} refused: {err} - "
                f"{LEGACY_MANIFEST} is kept")
            refused = True
            continue
        # The live install record is never deletable through a legacy listing
        # (record protection: it is what tells our own backup slots apart from
        # foreign files; _dest_safety_error cannot know this name because an
        # install never deletes it).
        # [更正 2026-10-04 · 依据 A-70 H-2, I-6] this used to be
        # `if name == MANIFEST_NAME:` - an exact, case-sensitive comparison on
        # a volume that answers case-insensitively and strips trailing dots and
        # spaces, so RA2FORGE_INSTALL.JSON and "ra2forge_install.json." passed
        # the guard, passed the slot identity checks (same directory entry, so
        # they resolve identically) and deleted the install record. Compared by
        # directory entry now, and the legacy record itself joins the protected
        # set: an entry naming it used to delete the listing under the loop and
        # then crash on the second unlink at the end of the pass.
        protected = None
        for record, what in ((MANIFEST_NAME, "install record"),
                             (LEGACY_MANIFEST, "legacy record")):
            if _same_directory_entry(name, record):
                protected = (record, what)
                break
        if protected:
            record, what = protected
            warnings.append(
                f"legacy record entry {name!r} addresses the {what} {record} "
                "(the same directory entry, whatever the spelling) - refusing "
                "to delete it; resolve the two records manually")
            refused = True
            continue
        if not dest.is_file():
            # [更正 2026-10-04 · 依据 A-70 M-3] a silent continue here, with the
            # listing deleted at the end of the pass, orphaned the oldest
            # original: the entry's file is gone while its backup slot is still
            # there, and after the listing goes nothing says which original that
            # slot belongs to.
            if os.path.lexists(str(game / (name + BACKUP_SUFFIX))):
                warnings.append(
                    f"{name} is not in the game directory but "
                    f"{name + BACKUP_SUFFIX} still is - that slot is the only "
                    "thing naming this entry's original, so the entry is "
                    f"refused and {LEGACY_MANIFEST} is kept; restore the file "
                    "from the slot yourself, or remove the slot if the file was "
                    "meant to stay deleted")
                refused = True
            continue
        if name.upper() == LEGACY_BATTLE_INI:
            if FORGE_MARKER not in dest.read_bytes()[:400]:
                actions.append(f"kept       {name} (not a ra2forge override)")
                continue
            # HIGH-2 family: the backup slot passes the SAME identity checks
            # as everywhere else, BEFORE any byte moves.
            bak = game / (name + BACKUP_SUFFIX)
            bak_err = _bak_safety_error(game, name)
            if bak_err:
                warnings.append(
                    f"backup slot for {name} refused: {bak_err} - "
                    f"{LEGACY_MANIFEST} is kept")
                refused = True
                continue
            if bak.is_file():
                # staged, alias-proof restore (never follows the slot, never
                # an alias at the slot)
                try:
                    _stage_and_replace(bak, dest, None, "restore")
                except OSError as exc:
                    warnings.append(
                        f"could not restore {bak.name} -> {name} ({exc}) - "
                        f"backup {bak.name} kept, {LEGACY_MANIFEST} is kept")
                    refused = True
                    continue
                actions.append(f"restored   {bak.name} -> {name}")
                try:
                    bak.unlink()
                except OSError as exc:
                    warnings.append(
                        f"restored {name}, but could not remove leftover "
                        f"backup slot {bak.name} ({exc}); delete {bak.name} "
                        "manually")
            elif drop_legacy_battlemd:
                moved = game / (name + ".ra2forge.removed.bak")
                # DLC-HIGH3-FIX01 (A1): this is a derived name too - the same
                # five criteria as every other slot, before anything moves.
                moved_err = _derived_slot_error(game, moved.name,
                                                "removed-original backup slot")
                if moved_err:
                    warnings.append(
                        f"{moved_err} - {LEGACY_MANIFEST} is kept")
                    refused = True
                    continue
                if moved.exists() or os.path.lexists(moved):
                    warnings.append(
                        f"{moved.name} already exists - refusing to overwrite "
                        "a previous removed copy (the oldest original wins); "
                        f"{LEGACY_MANIFEST} is kept")
                    refused = True
                    continue
                # [更正 2026-10-04 · 依据 A-69 F-2 · 本族第 4 次漏网] the line
                # this replaced was shutil.move(str(dest), str(moved)), and
                # shutil.move is NOT os.rename: stdlib Lib/shutil.py L833-842
                # takes a landing name that is a symlink to a DIRECTORY and
                # renames the SOURCE INTO that directory, L846-868 falls back to
                # copy_function (= copy2, which follows an alias) + os.unlink
                # whenever os.rename fails, and the plain rename itself turned
                # out to write THROUGH a live link to a file too. All three
                # measured this round (raw/10_move_probe.txt P1/P2/P3), together
                # with the os.replace() this write now uses, which never wrote a
                # byte outside across six shapes (raw/12_replace_probe.txt).
                # The landing name stays deterministic on purpose: the "oldest
                # original wins" rule, cli.py's documented name and the gate
                # above all key on exactly this name, so a random suffix would
                # remove the refusal rather than narrow a window. What closes
                # the window is the primitive: stage under an unpredictable name
                # inside the game directory, sha-check it, then os.replace,
                # which swaps this directory entry instead of following it and
                # refuses this slot outright if it stopped being itself.
                if os.path.lexists(moved):
                    # the exists() test above, at the instant of the write: an
                    # alias or a file planted in between must still not get the
                    # oldest original.
                    warnings.append(
                        f"{moved.name} appeared between the check and the "
                        "write - refusing to overwrite a previous removed copy "
                        f"(the oldest original wins); {LEGACY_MANIFEST} is kept")
                    refused = True
                    continue
                try:
                    _stage_and_replace(dest, moved, None,
                                       "removed-original backup")
                except OSError as exc:
                    warnings.append(
                        f"could not move {name} to {moved.name}: {exc} - the "
                        f"override is still where it was and {LEGACY_MANIFEST} "
                        "is kept; resolve the slot and re-run 'uninstall "
                        "--legacy --drop-legacy-battlemd'")
                    refused = True
                    continue
                # An action line is printed for work that was confirmed. The
                # move is not over while the original slot is still in place:
                # shutil.move used to leave the bytes at BOTH names when the
                # copy succeeded and the unlink did not (measured: a file held
                # open by another process fails the unlink with WinError 32 and
                # the exception then escaped the whole pass).
                try:
                    dest.unlink()
                except OSError as exc:
                    warnings.append(
                        f"{name} is still in the game directory: it was staged "
                        f"into {moved.name} but could not be removed ({exc}) - "
                        "remove it yourself once the game has it closed, keep "
                        f"{moved.name} as the oldest original, and "
                        f"{LEGACY_MANIFEST} is kept")
                    refused = True
                    continue
                actions.append(f"removed    {name} (moved to {moved.name})")
            else:
                warnings.append(
                    "BATTLEMD.INI is a legacy ra2forge override without a backup: "
                    "the official campaign list has to come from the game files "
                    "(reinstall/repair), or delete the override with "
                    "--drop-legacy-battlemd")
                # the recorded lifecycle did not complete - keep the listing
                # so the state stays visible and retryable (MEDIUM-7)
                refused = True
            continue
        # HIGH-2 family: gate the backup slot BEFORE deleting the recorded
        # file, so a refusal (dangling/live link, hard link, directory) leaves
        # the game directory byte-identical instead of deleting first and
        # refusing to restore second.
        bak = game / (name + BACKUP_SUFFIX)
        bak_err = _bak_safety_error(game, name)
        if bak_err:
            warnings.append(
                f"backup slot for {name} refused: {bak_err} - "
                f"{LEGACY_MANIFEST} is kept")
            refused = True
            continue
        try:
            dest.unlink()
        except OSError as exc:  # noqa: BLE001
            warnings.append(f"could not delete {name}: {exc}")
            refused = True
            continue
        actions.append(f"removed    {name}")
        if bak.is_file():
            try:
                _stage_and_replace(bak, dest, None, "restore")
            except OSError as exc:
                warnings.append(
                    f"could not restore {bak.name} -> {name} ({exc}) - "
                    f"backup {bak.name} kept, {LEGACY_MANIFEST} is kept")
                refused = True
                continue
            actions.append(f"restored   {bak.name} -> {name}")
            try:
                bak.unlink()
            except OSError as exc:
                warnings.append(
                    f"restored {name}, but could not remove leftover backup "
                    f"slot {bak.name} ({exc}); delete {bak.name} manually")

    if record_present:
        if refused:
            # MEDIUM-7 family: deleting the listing while entries were
            # refused orphaned the very backup slots the warnings point at.
            warnings.append(
                f"{LEGACY_MANIFEST} is KEPT: at least one entry above was "
                "refused, so the legacy record stays for a later "
                "'uninstall --legacy' to retry once the refused slots are "
                "resolved manually")
        else:
            # [更正 2026-10-04 · 依据 A-70 I-6] this unlink used to raise
            # FileNotFoundError when an entry above had already removed this
            # very name (a record entry spelling the legacy record itself, case
            # or trailing-dot included): every file operation of the pass had
            # completed, and the crash turned exit 0 into exit 1. Entries may
            # not address a record any more, and the removal is still only
            # claimed when it actually happened.
            if os.path.lexists(str(listing)):
                try:
                    listing.unlink()
                except OSError as exc:
                    warnings.append(
                        f"could not remove legacy record {LEGACY_MANIFEST} "
                        f"({exc}) - files above were processed, so "
                        f"{LEGACY_MANIFEST} is kept; clear the obstacle and "
                        "delete it or re-run 'uninstall --legacy'")
                    return True
                actions.append(f"removed    {LEGACY_MANIFEST}")
            else:
                warnings.append(
                    f"{LEGACY_MANIFEST} is already gone - it was removed "
                    "during this pass, so no second deletion is claimed")
    return False


def _load_manifest(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

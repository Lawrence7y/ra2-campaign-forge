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
LEGACY_MANIFEST = "ra2forge_uninstall.txt"
LEGACY_BATTLE_INI = "BATTLEMD.INI"
FORGE_MARKER = b"Generated by RA2 Campaign Forge"
TOOL_VERSION = "0.4"


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


def preinstall_plan(package_dir, game_dir) -> dict:
    """Read-only preflight for install_package(): classify BEFORE any write.

    Returns a dict with:
      blockers / conflicts / risks / notices : list[str]
      steps : the write plan - dicts {name, src, action, backup, conflict,
              recorded_backup, new_sha, dest_sha, size}; action is one of
              created/unchanged/replaced, backup is None/'create'/'keep'
      manifest / corrupt_manifest : parsed record or why it was rejected
    Raises FileNotFoundError exactly like before when the game directory does
    not look like one or the package is unusable (still zero writes).
    """
    package = Path(package_dir)
    game = Path(game_dir)
    if not (game / "gamemd.exe").is_file():
        raise FileNotFoundError(
            f"{game} does not look like a Yuri's Revenge directory "
            f"(gamemd.exe not found)")
    files = package_files(package)

    blockers: list[str] = []
    conflicts: list[str] = []
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
    same_install = (manifest is not None and manifest.get("package") is not None
                    and str(manifest["package"]) == str(package.resolve()))

    risks, notices = _scan_environment(game)

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
                        f"{MANIFEST_NAME}, package {manifest['package']!r}) "
                        "would be replaced by a DIFFERENT package - uninstall "
                        "it first, or pass --allow-content-conflict to "
                        "release this one conflict")
            elif name in old_entries:
                risks.append(
                    f"{name} changed after our install (its sha256 no longer "
                    f"matches {MANIFEST_NAME}) - what modified it cannot be "
                    "judged here; refusing in strict mode. 'uninstall' will "
                    "keep the changed file unless --force is given.")
            else:
                conflict = True
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
        steps.append({"name": name, "src": src, "action": action,
                      "backup": backup, "conflict": conflict,
                      "recorded_backup": recorded_backup, "new_sha": new_sha,
                      "dest_sha": dest_sha, "size": src.stat().st_size})

    return {"blockers": blockers, "conflicts": conflicts, "risks": risks,
            "notices": notices, "steps": steps, "manifest": manifest,
            "corrupt_manifest": corrupt}


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


def install_package(package_dir, game_dir, force: bool = False, *,
                    strict: bool = True,
                    allow_content_conflict: bool = False) -> dict:
    """Copy a built package into a game directory, backing up what it replaces.

    DLC-STRICT01: everything is preflighted read-only first (preinstall_plan).
    With the default strict=True a definite content conflict or an
    unresolvable risk refuses the whole install (InstallBlocked) BEFORE the
    first write, so a refused install leaves the directory byte-identical.
    allow_content_conflict=True releases ONLY the definite-content-conflict
    class; each released file is printed and recorded under
    precheck.allowed_content_conflicts in the manifest. force is accepted for
    signature compatibility but has never had an effect in this function.
    """
    game = Path(game_dir)
    plan = preinstall_plan(package_dir, game)

    if plan["blockers"]:
        kind = "corrupt_manifest" if plan["corrupt_manifest"] else "path_safety"
        raise InstallBlocked(_refusal_text(plan), kind=kind, report=plan)
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
    actions: list[str] = []
    entries: list[dict] = []
    for step in plan["steps"]:
        name = step["name"]
        if step["action"] == "unchanged":
            entries.append({"name": name, "action": "unchanged",
                            "bytes": step["size"], "sha256": step["new_sha"],
                            "backup": step["recorded_backup"]})
            actions.append(f"unchanged  {name} (already up to date)")
            continue
        if step["backup"] == "keep":
            actions.append(f"kept       {name + BACKUP_SUFFIX} (original "
                           "backup of a previous install, not overwritten)")
        elif step["backup"] == "create":
            actions.append(f"backup     {name} -> {name + BACKUP_SUFFIX}")
        backup_name, landed = _write_step(game, step)
        entries.append({"name": name, "action": step["action"],
                        "bytes": step["size"], "sha256": landed,
                        "backup": backup_name})
        actions.append(f"{step['action']:10s} {name} ({step['size']} bytes)")
        if step["conflict"]:
            actions.append(f"ALLOWED    {name}: content conflict released by "
                           "--allow-content-conflict (recorded in the manifest)")

    warnings = plan["risks"] + plan["notices"]
    manifest = {
        "tool": "ra2forge",
        "version": TOOL_VERSION,
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
    manifest_path = game / MANIFEST_NAME
    _stage_text_and_replace(
        json.dumps(manifest, indent=2, ensure_ascii=False), manifest_path,
        "install record")
    actions.append(f"written    {MANIFEST_NAME}")
    return {"game_dir": game, "manifest": manifest_path, "actions": actions,
            "warnings": warnings, "files": entries, "risks": plan["risks"],
            "notices": plan["notices"], "conflicts_allowed": allowed}


def uninstall(game_dir, legacy: bool = False, drop_legacy_battlemd: bool = False,
              force: bool = False) -> dict:
    """Undo an install: delete our files, restore every backup, drop the manifest.

    With legacy=True it also cleans the artefacts of ra2forge <= FORGE-1
    (BATTLEMD.INI override, loose maps, mix, ra2forge_uninstall.txt).
    """
    game = Path(game_dir)
    if not game.is_dir():
        raise FileNotFoundError(f"game directory not found: {game}")
    actions: list[str] = []
    warnings: list[str] = []

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
    elif manifest is None:
        warnings.append(f"no {MANIFEST_NAME} in {game}: nothing recorded to remove "
                        f"(use --legacy for installs made by an older ra2forge)")
    else:
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
            if not dest.is_file():
                actions.append(f"missing    {name} (already gone)")
            elif force or sha256_of(dest) == entry.get("sha256"):
                dest.unlink()
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
                    _stage_and_replace(bak, dest, None, "restore")
                    bak.unlink()
                    actions.append(f"restored   {backup} -> {name}")
                else:
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
            manifest_path.unlink()
            actions.append(f"removed    {MANIFEST_NAME}")

    if legacy:
        # files already handled by the manifest (removed + restored to their
        # pre-install state) must not be deleted again by the legacy pass
        handled = {e.get("name", "") for e in (manifest or {}).get("files", [])}
        _uninstall_legacy(game, actions, warnings, drop_legacy_battlemd, handled)

    return {"game_dir": game, "actions": actions, "warnings": warnings}


def _uninstall_legacy(game: Path, actions: list[str], warnings: list[str],
                      drop_legacy_battlemd: bool,
                      handled: set[str] | None = None) -> None:
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
                _stage_and_replace(bak, dest, None, "restore")
                bak.unlink()
                actions.append(f"restored   {bak.name} -> {name}")
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
            _stage_and_replace(bak, dest, None, "restore")
            bak.unlink()
            actions.append(f"restored   {bak.name} -> {name}")

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
                listing.unlink()
                actions.append(f"removed    {LEGACY_MANIFEST}")
            else:
                warnings.append(
                    f"{LEGACY_MANIFEST} is already gone - it was removed "
                    "during this pass, so no second deletion is claimed")


def _load_manifest(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

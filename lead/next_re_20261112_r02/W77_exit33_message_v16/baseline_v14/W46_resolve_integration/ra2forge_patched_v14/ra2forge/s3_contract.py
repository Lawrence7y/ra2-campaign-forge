"""W43 / B-line S3 -- contract constants consumed by the runtime.

This module is DATA + tiny helpers only. It is imported *lazily* by the
opt-in S3 entry points (``version_guard`` / ``feature_subset`` / the new
``resolve`` CLI subcommand).  NONE of the legacy ``build``/``install``/
``uninstall``/``verify`` code paths import it, so with no new switch the
package stays byte-for-byte identical to v12 (verified by out/SHA256_COMPAT*.txt).

Sources (all READ-ONLY, not modified by this card):
  * W38_version_guard_s1/VERSION_GUARD_CONTRACT.md          (13 criteria, 3x7 table)
  * W38_version_guard_s1/EVIDENCE/guard_decision_table.json (21 cells)
  * W38_version_guard_s1/WRITE_ENTRY_AUDIT.tsv              (80 rows)
  * W42_b_line_s2/FEATURE_SUBSET_CONTRACT.md                (shipped/action/K1-K12)
  * W42_b_line_s2/EVIDENCE/coupling_rules.json             (12 rules)
  * REVIEW/LEAD_DECISIONS_W42.md                           (D1-D4, all binding)

Grading of statements in this file: [本次读码] / [静态推断] / [转引].
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# D1 -- REVISED W38-S1 E1 KNOWN_GOOD allow-list
# ---------------------------------------------------------------------------
# W38-S1 §4 E1 KNOWN_GOOD originally allowed exactly four loose target
# classes: *.MAP / BATTLEMD98.INI / MAPSELMD.INI / expandmd98.mix, and
# "rejects any unregistered target file".  Lead verdict D1 (2026-11-13)
# authorises S3 to add ra2md.csf in the SAME patch, with these reasons:
#   [签发] W40 A/E arms prove a loose ra2md.csf DOES override the copy in
#          langmd.mix and its values drive UI rendering;
#   [签发] W40 A arm: a legal minimal CSF still STARTS the game (19.34 s);
#   [签发] W40 D arm: only a BAD MAGIC fails to start;
#   => the guard's correct shape is an INTEGRITY gate, not a drop ban.
# W41 v12 signed 57/57 by routing ra2md.csf through package_files/manifest/
# backup/uninstall, so the E1 allow-list must now name it.
E1_KNOWN_GOOD_TARGETS_V38 = (
    "*.MAP", "BATTLEMD98.INI", "MAPSELMD.INI", "expandmd98.mix",
)
E1_KNOWN_GOOD_TARGETS = (
    "*.MAP", "BATTLEMD98.INI", "MAPSELMD.INI", "expandmd98.mix",
    "ra2md.csf",
)
E1_REVISION_ID = "W43-S3-D1"
E1_REVISION_REASON = (
    "LEAD_DECISIONS_W42.md D1: loose ra2md.csf covers the langmd.mix copy and "
    "its values drive UI rendering (W40 A/E); a legal minimal CSF still starts "
    "(W40 A); only a bad magic fails to start (W40 D). Therefore the guard is "
    "a COMPLETENESS/INTEGRITY gate, NOT a drop ban and NOT a startup-failure "
    "rule. W41 v12 signed 57/57 with ra2md.csf in install/backup/uninstall."
)
# Machine-checkable record of the revision (also shipped as
# s1_revision/E1_KNOWN_GOOD.json + s1_revision/guard_decision_table.json,
# with the relative-path patch + rollback in APPLY.md).
E1_REVISION_RECORD = {
    "schema_version": "w38-s1-1",
    "revision": E1_REVISION_ID,
    "amended_contract": "W38_version_guard_s1/VERSION_GUARD_CONTRACT.md §4 E1",
    "amended_artifact": "W38_version_guard_s1/EVIDENCE/guard_decision_table.json",
    "allowed_targets_before": list(E1_KNOWN_GOOD_TARGETS_V38),
    "allowed_targets_after": list(E1_KNOWN_GOOD_TARGETS),
    "added": ["ra2md.csf"],
    "guard_shape": "completeness_integrity_gate",
    "not": ["drop_ban", "startup_failure_rule"],
    "reason": E1_REVISION_REASON,
}


# ---------------------------------------------------------------------------
# D2 -- .detour classification default + the CORRECT csf gate reason
# ---------------------------------------------------------------------------
# LEAD_DECISIONS_W42.md D2: westwood_native.  Note [本次实测] (Lead, W42
# signoff §4): .detour Characteristics = 0xC0000040 = MEM_READ|MEM_WRITE|
# CNT_INITIALIZED_DATA, NO MEM_EXECUTE bit.
DETOUR_CLASSIFICATION_DEFAULT = "westwood_native"
DETOUR_CLASSIFICATION_ALLOWED = (
    "westwood_native", "third_party_injected", "undetermined",
)
DETOUR_CHARACTERISTICS = 0xC0000040
DETOUR_HAS_EXECUTE_BIT = False

# The reason that MUST be used for the "minimal CSF" refusal.
# [签发] W40 A 115 B minimal CSF -> normal boot, 19.34 s -> main menu.
# [签发] W40 E overwriting GUI:SinglePlayer rendered OUR text.
# [签发] W40 D bad magic -> "Unable to initialize 'ra2.csf'" -> no boot.
# So: reject a minimal CSF because the OFFICIAL UI TEXT turns into
# MISSING:'...' (usability disaster), NOT because "the game won't start".
CSF_INTEGRITY_GATE_REASON = (
    "A loose ra2md.csf is a WHOLE-FILE override of the copy inside "
    "langmd.mix. A CSF containing only our own labels leaves every official "
    "label unresolved, so the official UI text renders as MISSING:'...' "
    "(W40 A/E: usability disaster). This is NOT a startup-failure rule: "
    "W40 A proved a legal minimal CSF still boots (19.34 s) and only a BAD "
    "MAGIC (W40 D) produces \"Unable to initialize 'ra2.csf'\". The gate "
    "therefore requires a COMPLETE official-base clone (>= 5211 official "
    "labels) plus our appended labels."
)
# Wrong reason text that must NOT appear in any S3 csf gate message.
CSF_GATE_FORBIDDEN_PHRASES = (
    "break game startup", "refuses to start", "game refuses to start",
    "would not start", "启动失败", "无法启动", "不能启动",
)
CSF_OFFICIAL_FULL_MIN = 5211          # [转引·待运行验证] W38 C10 / W36 §3.1.1
MAPSELMD_OFFICIAL_STAGE_COUNT = 14
MAPSELMD_OFFICIAL_SIZE_BYTES = 5573
MAPSELMD_BUNDLED_OFFICIAL_SHA256 = (
    "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"
)


# ---------------------------------------------------------------------------
# S2 feature-set model / shipped() / FILE_UNIVERSE
# ---------------------------------------------------------------------------
FEATURE_NAMES = ("maps", "battlemd", "mix", "csf", "mapselmd")
FILE_UNIVERSE_META = ("ra2forge_install.json", "ra2forge_install.json.seal")
MANIFEST_NAME = "ra2forge_install.json"
SEAL_NAME = "ra2forge_install.json.seal"
BACKUP_SUFFIX = ".ra2forge.bak"

# S2 reason codes -- ORTHOGONAL to W38-S1 guardVerdict.reason_codes.
S2_REASON_CODES = frozenset((
    "BATTLEMD_MODE_CONFLICT",
    "CSF_WITHOUT_BATTLEMD",
    "CSF_LABEL_UNBOUND",
    "MINIMAL_CSF_REFUSED",
    "MAPS_WITHOUT_MIX",
    "MIX_WITHOUT_MAPS",
    "MIX_MAP_SET_MISMATCH",
    "MAPSELMD_WITHOUT_MAPS",
    "MAPSELMD_SCENARIO_UNRESOLVED",
    "MAPSELMD_NOT_FULL_CLONE",
    "CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1",
    "G4_METADATA_DESYNC",
))
# W38-S1 guardVerdict.reason_codes (for the orthogonality check B17.3).
S1_REASON_CODES = frozenset((
    "NO_ADJUDICATED_BASELINE", "NO_BASELINE_MATCH", "CRITERION_MISSING",
    "CRITERION_UNREADABLE", "MULTI_COPY_AMBIGUOUS", "EDITION_UNKNOWN",
    "FULL_SHA_MISMATCH", "TEXT_SHA_MISMATCH", "SIZE_MISMATCH",
    "SECTION_TABLE_MISMATCH", "DDRAW_IDENTITY_MISMATCH",
    "ORIGINAL_BYTE_WINDOW_MISMATCH", "PATCHED_BY_THIRD_PARTY",
    "GAMEMD_ABSENT", "DIR_INVALID", "FORCE_UNKNOWN_READONLY_ONLY",
    "BASELINE_NOT_ADJUDICATED",
))

GUARD_STATES = ("KNOWN_GOOD", "UNKNOWN", "MISMATCH", "DIR_INVALID")
WRITE_ENTRIES = ("E1", "E2a", "E2b", "E3", "E4", "E5", "E6")
GUARD_EXIT_CODES = {"UNKNOWN": 20, "MISMATCH": 21, "DIR_INVALID": 22,
                    "GUARD_EVIDENCE_INCOMPLETE": 23}

# D3 -- G3 "medium" coupling warning channel.  A WARNING, never a violation.
G3_WARNING_CODE = "G3_MID_COUPLING_NOTICE"
G3_WARNING_TEXT = (
    "csf and MAPSELMD are both enabled while BATTLEMD98.INI is not in the "
    "shipped set: without a BATTLEMD98.INI entry pointing at A1 the "
    "MAPSELMD campaign progression cannot be triggered (functional coupling). "
    "This is a WARNING ONLY (Lead verdict D3): no hard refusal, because "
    "legitimate uses (maps-only sandbox, CSF-only text fix) do not need a "
    "complete campaign. The three STRONG pairs keep their hard refusals."
)


# ---------------------------------------------------------------------------
# K1-K12 -- machine-readable coupling rules (mirrors W42 EVIDENCE file)
# ---------------------------------------------------------------------------
COUPLING_RULES = (
    {"id": "K1", "code": "BATTLEMD_MODE_CONFLICT", "kind": "mutex"},
    {"id": "K2", "code": "CSF_WITHOUT_BATTLEMD", "kind": "requires"},
    {"id": "K3", "code": "CSF_LABEL_UNBOUND", "kind": "requires"},
    {"id": "K4", "code": "MINIMAL_CSF_REFUSED", "kind": "integrity"},
    {"id": "K5", "code": "MAPSELMD_NOT_FULL_CLONE", "kind": "integrity"},
    {"id": "K6", "code": "MAPS_WITHOUT_MIX", "kind": "requires"},
    {"id": "K7", "code": "MIX_WITHOUT_MAPS", "kind": "requires"},
    {"id": "K8", "code": "MIX_MAP_SET_MISMATCH", "kind": "content_alignment"},
    {"id": "K9", "code": "MAPSELMD_WITHOUT_MAPS", "kind": "requires"},
    {"id": "K10", "code": "MAPSELMD_SCENARIO_UNRESOLVED", "kind": "content_alignment"},
    {"id": "K11", "code": "G4_METADATA_DESYNC", "kind": "requires"},
    {"id": "K12", "code": "CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1", "kind": "requires"},
)


# ---------------------------------------------------------------------------
# W38-S1 WRITE_ENTRY_AUDIT.tsv HIGH/CRITICAL coverage map
# ---------------------------------------------------------------------------
# "版本守卫接线" gates the TWO top-level entry functions install_package()
# (E1) and uninstall() (E3); every HIGH/CRITICAL descendant row in the audit
# is reachable ONLY through them (read-code fact: _stage_and_replace /
# _write_step / _rollback / _execute_orphan_plan / _uninstall_legacy are all
# private helpers called from those two functions).  E2b (--csf-out) is
# reclassified to E1 by cli._s3_precheck_csf_out when it resolves inside a
# game directory.  build --install routes through install_package() (E1).
# This table is machine-checkable (S3_GUARD_WIRING) and documents exactly
# which audit rows are covered.
WRITE_ENTRY_COVERAGE = (
    {"entry": "E1", "gate_function": "install.install_package",
     "audit_rows": ["cli.py:312", "cli.py:326", "builder.py:161",
                    "builder.py:434", "builder.py:435-437",
                    "csf.py:410", "csf.py:416", "csf.py:417", "csf.py:421",
                    "csf.py:475", "install.py:1140-1143", "install.py:1498",
                    "install.py:1537", "install.py:1558", "install.py:1560",
                    "install.py:1568", "install.py:1572", "install.py:1575",
                    "install.py:1596", "install.py:1597", "install.py:1606",
                    "install.py:1609", "install.py:1653", "install.py:1656",
                    "install.py:1697", "install.py:1698", "install.py:1706",
                    "install.py:1710", "install.py:1718", "install.py:1761",
                    "install.py:1766", "install.py:1783", "install.py:1800",
                    "install.py:1955-1981", "install.py:1995",
                    "install.py:2045-2047", "install.py:2064",
                    "install.py:2066", "install.py:2075", "install.py:2141"],
     "risk": "CRITICAL/HIGH"},
    {"entry": "E3", "gate_function": "install.uninstall (+ _uninstall_legacy)",
     "audit_rows": ["install.py:2184", "install.py:2340", "install.py:2361",
                    "install.py:2389", "install.py:2399", "install.py:2422",
                    "install.py:2454", "install.py:2474", "install.py:2642",
                    "install.py:2651", "install.py:2705", "install.py:2722",
                    "install.py:2756", "install.py:2764", "install.py:2773",
                    "install.py:2798"],
     "risk": "CRITICAL/HIGH"},
    {"entry": "E2b->E1", "gate_function": "cli._s3_precheck_csf_out + builder._csf_out_ownership_guard",
     "audit_rows": ["builder.py:161", "builder.py:434", "builder.py:435-437",
                    "csf.py:410", "csf.py:416", "csf.py:417", "csf.py:421",
                    "csf.py:475", "cli.py:140-146"],
     "risk": "CRITICAL/HIGH"},
)
# XCHAIN ra2opt rows are OUT OF SCOPE for ra2forge (separate package, not
# shipped in v13).  Declared in UNCOVERED.md, not silently skipped.
XCHAIN_ROWS_OUT_OF_SCOPE = (
    "ra2opt/optimize.py:112-325", "ra2opt/backup.py:158",
    "ra2opt/backup.py:307", "ra2opt/safewrite.py:56-62",
    "ra2opt/cddraw.py:251", "ra2opt/launcher.py:52",
    "ra2opt/inifile.py:208", "ra2opt/pe.py:282", "ra2opt/pe.py:330",
    "ra2opt/optimize.py:294",
)


def e1_target_allowed(name: str) -> bool:
    """Revised W38-S1 E1 KNOWN_GOOD target allow-list (D1)."""
    if name == "ra2md.csf":
        return True
    if name.upper().endswith(".MAP"):
        return True
    return name in ("BATTLEMD98.INI", "MAPSELMD.INI", "expandmd98.mix")


def is_s1_reason(code: str) -> bool:
    return code in S1_REASON_CODES


def is_s2_reason(code: str) -> bool:
    return code in S2_REASON_CODES

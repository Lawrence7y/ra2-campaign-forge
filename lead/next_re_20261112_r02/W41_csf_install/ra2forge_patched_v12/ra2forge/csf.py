"""CSF (Compiled String File) reader/writer for Red Alert 2 / Yuri's Revenge.

Binary format (CSF v3, verified byte-for-byte against official ra2md.csf and ra2.csf):
  Header (24 bytes, little-endian):
    0x00  4s   magic        b" FSC" (0x43534620 = "CSF " in LE uint32)
    0x04  I    version      3 (also accepts 2)
    0x08  I    num_labels   number of LBL records
    0x0C  I    num_strings  total number of string values across all labels
    0x10  I    unused       0x00000000 in official ra2md.csf / ra2.csf (NOT a CRC)
    0x14  I    language     0=English(US), ..., 9=Chinese

  Label record (repeated num_labels times):
    4s   lbl_magic    b" LBL" (0x4C424C20 = "LBL " in LE uint32)
    I    num_values   number of value records attached to this label
    I    name_len     byte length of ASCII label name
    *    name         ASCII label name (name_len bytes)

  Value record (repeated num_values times per label):
    4s   val_magic    b" RTS" (0x53545220 = "STR " in LE) or b"WRTS" (0x57525453 = "STRW" in LE)
    I    char_count   number of UTF-16LE code units (payload is char_count * 2 bytes)
    *    text_bytes   UTF-16LE bytes with every byte bitwise-inverted (b ^ 0xFF)
    [if val_magic == b"WRTS"]:
      I    extra_len  byte length of ASCII extra string (e.g. EVA/sound tag)
      *    extra      ASCII extra string (extra_len bytes)

CRC / Checksum / Offset table notes:
  CSF v3 has NO CRC/checksum field and NO offset/index table. Header offset 0x10
  (4 bytes) is an unused/reserved field (0x00000000 in both official ra2md.csf
  and ra2.csf). Mutating a CSF therefore requires updating `num_labels` and
  `num_strings` consistently (and preserving `unused` / `language`).

Pure Python standard library only.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import struct
from dataclasses import dataclass, field
from pathlib import Path

CSF_MAGIC = b" FSC"
LBL_MAGIC = b" LBL"
STR_MAGIC = b" RTS"
WRTS_MAGIC = b"WRTS"

HEADER_STRUCT = struct.Struct("<4sIIIII")
LABEL_STRUCT = struct.Struct("<4sII")
UINT32_STRUCT = struct.Struct("<I")

LANGUAGE_NAMES = {
    0: "English (US)",
    1: "English (UK)",
    2: "German",
    3: "French",
    4: "Spanish",
    5: "Italian",
    6: "Japanese",
    7: "Jabberwockie",
    8: "Korean",
    9: "Chinese",
}

_XOR_TRANS = bytes(b ^ 0xFF for b in range(256))

# ---------------------------------------------------------------------------
# W41: official CSF baseline + "complete & legal" guard
#
# W29 (static, signed): a LOOSE ra2md.csf in the game directory overrides the
# copy inside langmd.mix (disk-first CCFileClass::Get_File 0x473D10). The
# engine's " FSC" check at 0x734799 fails on a minimal/partial CSF and
# 0x6BD85A pops "Unable to initialize 'ra2.csf'" -> startup failure. So a
# loose ra2md.csf MUST be a COMPLETE legal CSF carrying every official label.
# The only safe production path is therefore "clone the official base, then
# append our label" - a from-scratch / minimal CSF is refused outright.
#
# The official ra2md.csf below was extracted READ-ONLY from
#   D:\Project\ra2-campaign-forge\ra2bench\langmd.mix
# (index id 0xBD835079 = ts_crc_hash("ra2md.csf"), 332,973 bytes), measured
# in W41/EVIDENCE/step1_extract_official_csf.py. Byte-exact clone, not a
# reconstruction. It is bundled so the guard and the builder need no live MIX.
# ---------------------------------------------------------------------------
OFFICIAL_CSF_FILE = (Path(__file__).resolve().parent / "data"
                     / "RA2MD.OFFICIAL.CSF")
OFFICIAL_CSF_LABELS_FILE = (Path(__file__).resolve().parent / "data"
                            / "RA2MD.OFFICIAL.LABELS.txt")
OFFICIAL_CSF_SIZE = 332973
OFFICIAL_CSF_SHA256 = (
    "1b90bb0756137f46ff529af043fe798d7f1f9fa1713a4110f17e1d674de81f1c")
OFFICIAL_CSF_LABEL_COUNT = 5211
OFFICIAL_CSF_VERSION = 3
OFFICIAL_CSF_LANGUAGE = 9
# Value-type magics measured in the official CSF (W41 step1): only these two.
OFFICIAL_VALUE_KINDS = frozenset((STR_MAGIC, WRTS_MAGIC))


class CsfError(ValueError):
    """Raised when a CSF file is malformed, truncated, or unsupported."""


class CsfIncompleteError(CsfError):
    """W41: a CSF that is not a complete, legal official-baseline clone.

    Raised by assert_complete_csf() / write_csf(require_complete=True) /
    append_or_set_label(require_complete=True). Subclasses CsfError so the
    builder's existing `except (OSError, csf_mod.CsfError)` already catches it.
    """


@dataclass
class CsfValue:
    """One value entry under a CSF label."""

    kind: bytes
    text: str | None
    extra: str | None = None
    raw_bytes: bytes | None = None

    @property
    def is_known(self) -> bool:
        return self.kind in (STR_MAGIC, WRTS_MAGIC) and self.raw_bytes is None

    def to_bytes(self) -> bytes:
        if self.raw_bytes is not None:
            return self.raw_bytes
        if self.text is None:
            raise CsfError(f"cannot serialize value of kind {self.kind!r} with text=None")
        raw_u16 = self.text.encode("utf-16-le")
        if len(raw_u16) % 2 != 0:
            raise CsfError("internal error: UTF-16LE byte length is odd")
        char_count = len(raw_u16) // 2
        inv_u16 = raw_u16.translate(_XOR_TRANS)
        if self.kind == STR_MAGIC:
            return STR_MAGIC + UINT32_STRUCT.pack(char_count) + inv_u16
        if self.kind == WRTS_MAGIC:
            extra_bytes = (self.extra or "").encode("ascii")
            return (
                WRTS_MAGIC
                + UINT32_STRUCT.pack(char_count)
                + inv_u16
                + UINT32_STRUCT.pack(len(extra_bytes))
                + extra_bytes
            )
        raise CsfError(f"unsupported CSF value type for serialization: {self.kind!r}")


@dataclass
class CsfLabel:
    """One labeled entry in a CSF file."""

    name: str
    values: list[CsfValue] = field(default_factory=list)

    @property
    def text(self) -> str | None:
        return self.values[0].text if self.values else None

    def to_bytes(self) -> bytes:
        name_bytes = self.name.encode("ascii")
        parts = [LABEL_STRUCT.pack(LBL_MAGIC, len(self.values), len(name_bytes)), name_bytes]
        for v in self.values:
            parts.append(v.to_bytes())
        return b"".join(parts)


@dataclass
class CsfFile:
    """In-memory representation of a parsed CSF file."""

    version: int = 3
    unused: int = 0
    language: int = 0
    labels: list[CsfLabel] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknown_records: list[dict] = field(default_factory=list)
    has_unparsed_tail: bool = False
    header_num_labels: int | None = None
    header_num_strings: int | None = None

    @property
    def num_labels(self) -> int:
        return len(self.labels)

    @property
    def num_strings(self) -> int:
        return sum(len(lbl.values) for lbl in self.labels)

    def _match(self, a: str, b: str, *, case_insensitive: bool) -> bool:
        return a.lower() == b.lower() if case_insensitive else a == b

    def get_label(self, label: str, *, case_insensitive: bool = False) -> CsfLabel | None:
        for lbl in self.labels:
            if self._match(lbl.name, label, case_insensitive=case_insensitive):
                return lbl
        return None

    def get(self, label: str, *, case_insensitive: bool = False) -> str | None:
        lbl = self.get_label(label, case_insensitive=case_insensitive)
        return lbl.text if lbl is not None else None

    def set(
        self,
        label: str,
        text: str,
        *,
        extra: str | None = None,
        case_insensitive: bool = False,
    ) -> str:
        """Set or append a label's primary string value. Returns 'updated' or 'appended'."""
        if not label or not label.isascii():
            raise CsfError(f"label name must be non-empty ASCII, got {label!r}")
        if extra is not None and not extra.isascii():
            raise CsfError(f"WRTS extra string must be ASCII, got {extra!r}")
        if self.has_unparsed_tail:
            raise CsfError("cannot mutate a CSF file that contains an unparsed unknown value tail")
        kind = WRTS_MAGIC if extra is not None else STR_MAGIC
        val = CsfValue(kind=kind, text=text, extra=extra)
        existing = self.get_label(label, case_insensitive=case_insensitive)
        if existing is not None:
            existing.values = [val]
            return "updated"
        self.labels.append(CsfLabel(name=label, values=[val]))
        return "appended"

    def to_dict(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for lbl in self.labels:
            if lbl.text is not None:
                out[lbl.name] = lbl.text
        return out

    def to_bytes(self) -> bytes:
        if self.has_unparsed_tail:
            raise CsfError(
                "cannot re-serialize CSF with an unparsed unknown value tail "
                "(remaining label count/boundaries are unknown)"
            )
        n_labels = len(self.labels)
        n_strings = sum(len(lbl.values) for lbl in self.labels)
        header = HEADER_STRUCT.pack(
            CSF_MAGIC,
            self.version,
            n_labels,
            n_strings,
            self.unused,
            self.language,
        )
        chunks = [header]
        for lbl in self.labels:
            chunks.append(lbl.to_bytes())
        return b"".join(chunks)


def parse_csf(data: bytes, *, strict: bool = False) -> CsfFile:
    """Parse raw CSF bytes into a CsfFile.

    Raises CsfError on truncated headers/records, bad magic, or invalid UTF-16.
    When strict=False (default), unknown value type magics (other than b" RTS"
    and b"WRTS") are honestly reported in CsfFile.warnings / unknown_records
    with their raw bytes preserved; when strict=True, unknown value types raise
    CsfError.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise CsfError(f"expected bytes-like input, got {type(data).__name__}")
    buf = bytes(data)
    total_len = len(buf)
    if total_len < HEADER_STRUCT.size:
        raise CsfError(
            f"truncated CSF header: got {total_len} bytes, need at least {HEADER_STRUCT.size}"
        )

    magic, version, num_labels, num_strings, unused, language = HEADER_STRUCT.unpack_from(buf, 0)
    if magic != CSF_MAGIC:
        raise CsfError(f"bad CSF magic {magic!r}, expected {CSF_MAGIC!r}")
    if version not in (2, 3):
        raise CsfError(f"unsupported CSF version {version} (expected 2 or 3)")

    pos = HEADER_STRUCT.size
    labels: list[CsfLabel] = []
    warnings: list[str] = []
    unknown_records: list[dict] = []
    has_unparsed_tail = False
    parsed_values = 0

    for lbl_idx in range(num_labels):
        if pos + LABEL_STRUCT.size > total_len:
            raise CsfError(
                f"truncated LBL header at offset {pos} (label {lbl_idx}/{num_labels})"
            )
        lbl_magic, n_vals, name_len = LABEL_STRUCT.unpack_from(buf, pos)
        pos += LABEL_STRUCT.size
        if lbl_magic != LBL_MAGIC:
            raise CsfError(
                f"bad LBL magic {lbl_magic!r} at offset {pos - LABEL_STRUCT.size} "
                f"(label {lbl_idx}/{num_labels})"
            )
        if pos + name_len > total_len:
            raise CsfError(
                f"truncated label name at offset {pos} (need {name_len} bytes, "
                f"{total_len - pos} left)"
            )
        name_bytes = buf[pos:pos + name_len]
        pos += name_len
        try:
            name = name_bytes.decode("ascii")
        except UnicodeDecodeError as exc:
            raise CsfError(
                f"non-ASCII label name at label {lbl_idx}: {name_bytes!r}"
            ) from exc

        values: list[CsfValue] = []
        aborted_on_unknown = False
        for val_idx in range(n_vals):
            if pos + 4 > total_len:
                raise CsfError(
                    f"truncated value magic at offset {pos} (label {name!r} value {val_idx}/{n_vals})"
                )
            val_start = pos
            vmagic = buf[pos:pos + 4]
            pos += 4

            if vmagic in (STR_MAGIC, WRTS_MAGIC):
                if pos + 4 > total_len:
                    raise CsfError(
                        f"truncated string length at offset {pos} (label {name!r})"
                    )
                char_count = UINT32_STRUCT.unpack_from(buf, pos)[0]
                pos += 4
                byte_len = char_count * 2
                if pos + byte_len > total_len:
                    raise CsfError(
                        f"truncated string payload at offset {pos} (label {name!r}: "
                        f"need {byte_len} bytes, {total_len - pos} left)"
                    )
                enc_bytes = buf[pos:pos + byte_len]
                pos += byte_len
                raw_u16 = enc_bytes.translate(_XOR_TRANS)
                try:
                    text = raw_u16.decode("utf-16-le")
                except UnicodeDecodeError as exc:
                    raise CsfError(
                        f"invalid UTF-16LE string in label {name!r} at offset {pos - byte_len}"
                    ) from exc

                extra: str | None = None
                if vmagic == WRTS_MAGIC:
                    if pos + 4 > total_len:
                        raise CsfError(
                            f"truncated WRTS extra length at offset {pos} (label {name!r})"
                        )
                    extra_len = UINT32_STRUCT.unpack_from(buf, pos)[0]
                    pos += 4
                    if pos + extra_len > total_len:
                        raise CsfError(
                            f"truncated WRTS extra bytes at offset {pos} (label {name!r}: "
                            f"need {extra_len} bytes, {total_len - pos} left)"
                        )
                    extra_bytes = buf[pos:pos + extra_len]
                    pos += extra_len
                    try:
                        extra = extra_bytes.decode("ascii")
                    except UnicodeDecodeError as exc:
                        raise CsfError(
                            f"non-ASCII WRTS extra field in label {name!r}: {extra_bytes!r}"
                        ) from exc

                values.append(CsfValue(kind=vmagic, text=text, extra=extra))
                parsed_values += 1
            else:
                if strict:
                    raise CsfError(
                        f"unsupported CSF value type {vmagic!r} at offset {val_start} "
                        f"(label {name!r})"
                    )
                raw_rest = buf[val_start:]
                is_terminal = (lbl_idx == num_labels - 1) and (val_idx == n_vals - 1)
                msg = (
                    f"unsupported CSF value type {vmagic!r} at offset {val_start} "
                    f"(label {name!r}, value {val_idx + 1}/{n_vals}); "
                    f"preserved {len(raw_rest)} raw bytes"
                )
                if not is_terminal:
                    msg += " (unknown record size prevents parsing subsequent entries)"
                    has_unparsed_tail = True
                warnings.append(msg)
                unknown_records.append(
                    {
                        "label": name,
                        "label_index": lbl_idx,
                        "value_index": val_idx,
                        "offset": val_start,
                        "magic": vmagic,
                        "raw_bytes": raw_rest,
                        "terminal": is_terminal,
                    }
                )
                values.append(
                    CsfValue(kind=vmagic, text=None, extra=None, raw_bytes=raw_rest)
                )
                parsed_values += 1
                pos = total_len
                aborted_on_unknown = True
                break

        labels.append(CsfLabel(name=name, values=values))
        if aborted_on_unknown:
            break

    if not has_unparsed_tail and not unknown_records and pos != total_len:
        raise CsfError(
            f"trailing bytes in CSF: parsed {pos} bytes for {num_labels} labels, "
            f"but file has {total_len} bytes"
        )

    if not unknown_records and parsed_values != num_strings:
        msg = (
            f"CSF header num_strings={num_strings} disagrees with parsed value count "
            f"{parsed_values}"
        )
        if strict:
            raise CsfError(msg)
        warnings.append(msg)

    return CsfFile(
        version=version,
        unused=unused,
        language=language,
        labels=labels,
        warnings=warnings,
        unknown_records=unknown_records,
        has_unparsed_tail=has_unparsed_tail,
        header_num_labels=num_labels,
        header_num_strings=num_strings,
    )


def read_csf(path: str | Path, *, strict: bool = False) -> CsfFile:
    """Read and parse a CSF file from disk."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"CSF file not found: {p}")
    return parse_csf(p.read_bytes(), strict=strict)


def write_csf(path: str | Path, csf: CsfFile, *,
              require_complete: bool = False) -> Path:
    """Serialize a CsfFile and write it safely via a staged temporary file.

    W41: when require_complete=True the payload must ALSO pass the mandatory
    "complete & legal" guard (assert_complete_csf) BEFORE any byte reaches
    disk. Default False keeps the primitive writer general-purpose (the W30
    low-level CSF1..CSF6 unit cases build minimal CSFs on purpose); the
    install-artifact production path in builder._emit_csf_artifacts() passes
    require_complete=True so no minimal CSF can ever become a loose ra2md.csf.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = csf.to_bytes()
    # In-memory verification before touching disk
    parse_csf(payload, strict=True)
    if require_complete:
        assert_complete_csf(payload)
    stage = p.parent / f"{p.name}.tmp-{secrets.token_hex(6)}"
    try:
        stage.write_bytes(payload)
        os.replace(stage, p)
    finally:
        if stage.exists():
            try:
                stage.unlink()
            except OSError:
                pass
    return p


def create_csf(
    entries: dict[str, str] | list[tuple[str, str]] | None = None,
    *,
    language: int = 0,
    version: int = 3,
) -> CsfFile:
    """Create a fresh CsfFile from initial label->text mappings."""
    csf = CsfFile(version=version, unused=0, language=language)
    if entries:
        items = entries.items() if isinstance(entries, dict) else entries
        for label, text in items:
            csf.set(str(label), str(text))
    return csf


def append_or_set_label(
    csf_path: str | Path,
    label: str,
    text: str,
    *,
    extra: str | None = None,
    language: int = 0,
    create_if_missing: bool = False,
    case_insensitive: bool = False,
    verify: bool = True,
    require_complete: bool = False,
) -> dict:
    """Append or update `label` -> `text` in `csf_path` without corrupting existing entries.

    Reads and strictly validates the existing file first; if malformed, raises
    CsfError without modifying the file on disk. After writing atomically,
    re-reads the file from disk using read_csf() and asserts byte-exact text
    equality for `label` as well as full preservation of every pre-existing label.

    W41: require_complete=True additionally enforces the mandatory "complete &
    legal" guard on every write (see write_csf). Default False preserves the
    W30 low-level semantics; the install-artifact path passes True.
    """
    p = Path(csf_path)
    if p.exists():
        csf = read_csf(p, strict=True)
    elif create_if_missing:
        csf = CsfFile(version=3, unused=0, language=language)
    else:
        raise FileNotFoundError(f"CSF file not found: {p}")

    # Snapshot pre-existing labels & values for roundtrip verification
    before_snapshot = [
        (lbl.name, [(v.kind, v.text, v.extra) for v in lbl.values])
        for lbl in csf.labels
    ]

    action = csf.set(label, text, extra=extra, case_insensitive=case_insensitive)
    write_csf(p, csf, require_complete=require_complete)

    if verify:
        readback = read_csf(p, strict=True)
        got = readback.get(label, case_insensitive=case_insensitive)
        if got != text:
            raise CsfError(
                f"CSF roundtrip verification failed for {label!r}: "
                f"wrote {text!r}, read back {got!r}"
            )
        if extra is not None:
            got_lbl = readback.get_label(label, case_insensitive=case_insensitive)
            got_extra = got_lbl.values[0].extra if got_lbl and got_lbl.values else None
            if got_extra != extra:
                raise CsfError(
                    f"CSF roundtrip WRTS extra mismatch for {label!r}: "
                    f"wrote {extra!r}, read back {got_extra!r}"
                )
        expected_len = len(before_snapshot) + (1 if action == "appended" else 0)
        if readback.num_labels != expected_len:
            raise CsfError(
                f"CSF roundtrip label count mismatch: expected {expected_len}, "
                f"got {readback.num_labels}"
            )
        if readback.num_strings != sum(len(l.values) for l in readback.labels):
            raise CsfError("CSF roundtrip num_strings self-consistency check failed")

        # Assert every pre-existing label (other than the updated one) is untouched
        after_map = [
            (lbl.name, [(v.kind, v.text, v.extra) for v in lbl.values])
            for lbl in readback.labels
        ]
        for idx, (orig_name, orig_vals) in enumerate(before_snapshot):
            is_target = (
                orig_name.lower() == label.lower()
                if case_insensitive
                else orig_name == label
            )
            if is_target:
                continue
            if after_map[idx] != (orig_name, orig_vals):
                raise CsfError(
                    f"CSF roundtrip altered existing label {orig_name!r} at index {idx}"
                )

    return {
        "path": str(p),
        "action": action,
        "label": label,
        "num_labels": csf.num_labels,
        "num_strings": csf.num_strings,
        "language": csf.language,
    }


# ---------------------------------------------------------------------------
# W41: official baseline + mandatory "complete & legal" guard
# ---------------------------------------------------------------------------

def official_baseline_labels() -> frozenset[str]:
    """Return the 5,211 official label names (case-folded) measured in W41.

    Source of truth: the sorted unique label-name list bundled next to the
    byte-exact official CSF (data/RA2MD.OFFICIAL.LABELS.txt), produced by
    W41/EVIDENCE/step1_extract_official_csf.py from ra2bench\\langmd.mix.
    Names are case-folded because the engine resolves CSF labels
    case-insensitively (get_label(case_insensitive=True) / append_or_set_label).
    """
    if not OFFICIAL_CSF_LABELS_FILE.is_file():
        raise CsfIncompleteError(
            f"official CSF baseline label set is missing at "
            f"{OFFICIAL_CSF_LABELS_FILE}")
    names = [ln.strip() for ln in
             OFFICIAL_CSF_LABELS_FILE.read_text(encoding="utf-8").splitlines()]
    names = [n for n in names if n]
    if len(names) != OFFICIAL_CSF_LABEL_COUNT:
        raise CsfIncompleteError(
            f"official CSF baseline label set has {len(names)} names, expected "
            f"{OFFICIAL_CSF_LABEL_COUNT} - bundled resource is corrupt")
    return frozenset(n.upper() for n in names)


def load_official_csf() -> CsfFile:
    """Return a fresh CsfFile parsed from the bundled byte-exact official CSF.

    Self-checks size + SHA-256 against the measured values, then strict-parses
    and runs assert_complete_csf() on it - so a damaged bundled resource can
    never silently become a "complete" base.
    """
    if not OFFICIAL_CSF_FILE.is_file():
        raise CsfIncompleteError(
            f"bundled official ra2md.csf is missing at {OFFICIAL_CSF_FILE}")
    raw = OFFICIAL_CSF_FILE.read_bytes()
    if (len(raw) != OFFICIAL_CSF_SIZE
            or hashlib.sha256(raw).hexdigest() != OFFICIAL_CSF_SHA256):
        raise CsfIncompleteError(
            "bundled official ra2md.csf is not the measured byte-exact clone "
            "(size/sha256 mismatch) - refusing to use it as a base")
    csf = parse_csf(raw, strict=True)
    assert_complete_csf(csf)
    return csf


def assert_complete_csf(csf_or_bytes: "CsfFile | bytes | bytearray",
                        *, baseline_labels: frozenset[str] | None = None) -> dict:
    """W41 mandatory completeness guard: refuse a minimal / partial CSF.

    A loose ra2md.csf is a WHOLE-FILE override (W29), so it MUST be a complete
    legal CSF carrying every official label. This is the single choke point:
    builder._emit_csf_artifacts() and write_csf(require_complete=True) route
    every install-artifact write through it.

    Checks (all mandatory, in order):
      1. strict parse (magic b" FSC", version in {2,3}, no truncation, no
         trailing bytes, num_strings self-consistency, no unknown value tails);
      2. version == 3 (official ra2md.csf is v3; a v2 CSF is not this base);
      3. header num_labels == parsed label count AND header num_strings ==
         parsed value count ("标签数一致");
      4. every value kind is b" RTS" or b"WRTS" (the only kinds measured in
         the official file), and no warnings/unknown records;
      5. the case-folded label-name set is a SUPERSET of the official baseline
         label set extracted from langmd.mix - any missing label is refused.

    Returns a report dict. Raises CsfIncompleteError (a CsfError) otherwise.
    Accepts either a CsfFile or raw bytes; when bytes are given they are
    strict-parsed first. `baseline_labels` can be injected for testing.
    """
    if isinstance(csf_or_bytes, CsfFile):
        csf = csf_or_bytes
    else:
        csf = parse_csf(bytes(csf_or_bytes), strict=True)

    # (2) version 3
    if csf.version != OFFICIAL_CSF_VERSION:
        raise CsfIncompleteError(
            f"CSF version is {csf.version}, expected "
            f"{OFFICIAL_CSF_VERSION} - a complete loose ra2md.csf must be "
            "the official v3 base")
    # (3) header/label/value count consistency ("标签数一致")
    if csf.header_num_labels is not None and \
            csf.header_num_labels != csf.num_labels:
        raise CsfIncompleteError(
            f"CSF header num_labels={csf.header_num_labels} disagrees with "
            f"parsed label count {csf.num_labels} - refusing an inconsistent CSF")
    if csf.header_num_strings is not None and \
            csf.header_num_strings != csf.num_strings:
        raise CsfIncompleteError(
            f"CSF header num_strings={csf.header_num_strings} disagrees with "
            f"parsed value count {csf.num_strings} - refusing an inconsistent CSF")
    # (4) value kinds + clean parse
    if csf.warnings or csf.unknown_records or csf.has_unparsed_tail:
        raise CsfIncompleteError(
            "CSF has warnings / unknown value records / an unparsed tail - "
            "not a clean complete official clone")
    bad_kinds = sorted({v.kind for lbl in csf.labels for v in lbl.values}
                       - OFFICIAL_VALUE_KINDS)
    if bad_kinds:
        raise CsfIncompleteError(
            f"CSF contains non-official value kinds {bad_kinds!r}; the official "
            "base has only b' RTS' / b'WRTS'")
    # (5) official baseline label set (from langmd.mix)
    base = (official_baseline_labels() if baseline_labels is None
            else frozenset(n.upper() for n in baseline_labels))
    present = frozenset(lbl.name.upper() for lbl in csf.labels)
    missing = base - present
    if missing:
        sample = sorted(missing)[:12]
        raise CsfIncompleteError(
            f"CSF is PARTIAL: {len(missing)} of {len(base)} official baseline "
            "labels are missing (e.g. " + ", ".join(sample) + "). A loose "
            "ra2md.csf overrides the copy inside langmd.mix; a partial/minimal "
            "file makes the engine's \" FSC\" check fail and the game refuses "
            "to start. Only a complete official-base clone is allowed.")
    if csf.num_labels < len(base):
        raise CsfIncompleteError(
            f"CSF has {csf.num_labels} labels, fewer than the "
            f"{len(base)}-label official baseline")
    return {
        "version": csf.version,
        "language": csf.language,
        "num_labels": csf.num_labels,
        "num_strings": csf.num_strings,
        "baseline_labels": len(base),
        "extra_labels": csf.num_labels - len(base),
    }

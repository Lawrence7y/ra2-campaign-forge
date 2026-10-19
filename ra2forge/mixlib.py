"""MIX archive reader/writer for Command & Conquer TS / Red Alert 2 / Yuri's Revenge.

Format references (public knowledge, verified against WAE/OpenRA sources):
- OpenRA.Mods.Cnc FileSystem/MixFile.cs + FileFormats/Blowfish*.cs
- https://modenc.renegadeprojects.com/MIX_Format
- WAE MapEditorLibrary/CCEngine/MixCRC.cs

Python implementation notes:
- Westwood's RSA-protected blowfish key: the encrypted 80-byte header holds two
  40-byte RSA (signature-style) blocks; "decrypting" with the PUBLIC key yields
  39 bytes each; concatenated and truncated to 56 bytes = the blowfish key.
- The C bignum code in OpenRA/BlowfishKeyProvider is little-endian; we mirror it
  with int.from_bytes(..., 'little').
"""

from __future__ import annotations

import base64
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Blowfish (standard algorithm, constants = hex digits of pi, self-checked)
# ---------------------------------------------------------------------------

WESTWOOD_PUBLIC_KEY = "AihRvNoIbTn85FZRYNZRcT+i6KpU+maCsEqr3Q5q+LDB5tH7Tz2qQ38V"


def _pi_hex_digits(ndigits: int) -> str:
    """Return `ndigits` fractional hex digits of pi (Chudnovsky, Decimal)."""
    from decimal import Decimal, getcontext

    prec = int(ndigits * 1.20411998265) + 25  # hex -> decimal digits
    getcontext().prec = prec

    def sqrt(n: int) -> Decimal:
        x = Decimal(n).sqrt()
        return x

    # Chudnovsky: 1/pi = 12 * sum_k (-1)^k (6k)! (A+Bk) / ((3k)!(k!)^3 640320^(3k+3/2))
    # pi = 426880*sqrt(10005) / S, S = sum_k C_k * (A + Bk)
    # with C_0 = 1, C_k/C_{k-1} = -24*(6k-5)(2k-1)(6k-1) / (k^3 * 640320^3)
    getcontext().prec += 2
    A, B = 13591409, 545140134
    ck = Decimal(1)
    total = Decimal(0)
    target_terms = prec // 14 + 4
    for k in range(target_terms):
        total += ck * Decimal(A + B * k)
        ck *= Decimal(-24 * (6 * k + 1) * (2 * k + 1) * (6 * k + 5)) / (
            Decimal(k + 1) ** 3 * Decimal(640320) ** 3
        )
    getcontext().prec -= 2
    pi = 426880 * sqrt(10005) / total
    scaled = int(pi * (1 << (4 * ndigits)))
    h = format(scaled, "x")
    assert h[0] == "3", "pi integer part mismatch"
    return h[1: 1 + ndigits]


_BF_TABLES_CACHE = None


def _blowfish_tables():
    global _BF_TABLES_CACHE
    if _BF_TABLES_CACHE is not None:
        return _BF_TABLES_CACHE
    hexdigits = _pi_hex_digits(8336 + 16)
    words = [int(hexdigits[i * 8:(i + 1) * 8], 16) for i in range(1042)]
    p = words[:18]
    s = [words[18:18 + 256], words[18 + 256:18 + 512],
         words[18 + 512:18 + 768], words[18 + 768:18 + 1024]]
    assert p[0] == 0x243F6A88 and p[1] == 0x85A308D3, "blowfish P check failed"
    assert s[0][0] == 0xD1310BA6 and s[0][1] == 0x98DFB5AC, "blowfish S check failed"
    _BF_TABLES_CACHE = (p, s)
    return _BF_TABLES_CACHE


class Blowfish:
    """Standard Blowfish, ECB, block words read as little-endian (matches OpenRA)."""

    def __init__(self, key: bytes):
        p0, s0 = _blowfish_tables()
        # copy! the key schedule below mutates the tables, and the pristine
        # tables are cached module-wide
        self.P = list(p0)
        self.S = [list(box) for box in s0]
        p = self.P
        s = self.S
        j = 0
        for i in range(18):
            data = 0
            for _ in range(4):
                data = ((data << 8) | key[j]) & 0xFFFFFFFF
                j = (j + 1) % len(key)
            p[i] ^= data
        l = r = 0
        for i in range(0, 18, 2):
            l, r = self._encrypt(l, r)
            p[i], p[i + 1] = l, r
        for box in s:
            for i in range(0, 256, 2):
                l, r = self._encrypt(l, r)
                box[i], box[i + 1] = l, r

    def _f(self, x: int) -> int:
        s = self.S
        a = (x >> 24) & 0xFF
        b = (x >> 16) & 0xFF
        c = (x >> 8) & 0xFF
        d = x & 0xFF
        return (((s[0][a] + s[1][b]) & 0xFFFFFFFF) ^ s[2][c]) + s[3][d] & 0xFFFFFFFF

    def _encrypt(self, l: int, r: int):
        p = self.P
        for i in range(0, 16, 2):
            l ^= p[i]
            r ^= self._f(l)
            r ^= p[i + 1]
            l ^= self._f(r)
        l ^= p[16]
        r ^= p[17]
        return r, l

    def _decrypt(self, l: int, r: int):
        p = self.P
        for i in range(17, 1, -2):
            l ^= p[i]
            r ^= self._f(l)
            r ^= p[i - 1]
            l ^= self._f(r)
        l ^= p[1]
        r ^= p[0]
        return r, l

    def decrypt_block(self, block: bytes) -> bytes:
        assert len(block) == 8
        # standard Blowfish block order (big-endian words); OpenRA achieves the
        # same by byteswapping each LE-read uint32 before the cipher
        l, r = struct.unpack(">II", block)
        l, r = self._decrypt(l, r)
        return struct.pack(">II", l, r)

    def decrypt(self, data: bytes) -> bytes:
        out = bytearray()
        for i in range(0, len(data) - len(data) % 8, 8):
            out += self.decrypt_block(data[i:i + 8])
        return bytes(out)


# ---------------------------------------------------------------------------
# Westwood key block (RSA "decryption" with the public key)
# ---------------------------------------------------------------------------

def _parse_public_key() -> int:
    blob = base64.b64decode(WESTWOOD_PUBLIC_KEY)
    assert blob[0] == 0x02, "unexpected key blob tag"
    j = 1
    if blob[j] & 0x80:
        nlen_bytes = blob[j] & 0x7F
        mod_len = 0
        for i in range(nlen_bytes):
            mod_len = (mod_len << 8) | blob[j + 1 + i]
        j += nlen_bytes + 1
    else:
        mod_len = blob[j]
        j += 1
    return int.from_bytes(blob[j:j + mod_len], "big")


_RSA_MODULUS = _parse_public_key()
_RSA_EXPONENT = 0x10001


def westwood_decrypt_key_block(src: bytes) -> bytes:
    """Decrypt the 80-byte encrypted header block, return the 56-byte key.

    Mirrors WAE's KeyDecryptor.DecryptBlowfishKey: two 40-byte RSA chunks,
    each decrypted to a minimal little-endian integer byte string, then
    concatenated into a 56-byte key buffer (zero-filled).
    """
    key = bytearray(56)
    j = 0
    for i in (0, 40):
        chunk = src[i:i + 40]
        c = int.from_bytes(chunk, "little", signed=True)
        m = pow(c, _RSA_EXPONENT, _RSA_MODULUS)
        length = max(1, (m.bit_length() + 7) // 8)
        raw = m.to_bytes(length, "little").rstrip(b"\x00") or b"\x00"
        take = min(len(raw), 56 - j)
        if take > 0:
            key[j:j + take] = raw[:take]
        j += len(raw)
        if j >= 56:
            break
    return bytes(key)


# ---------------------------------------------------------------------------
# Filename hashes
# ---------------------------------------------------------------------------

def crc_hash(filename: str) -> int:
    """TS/RA2 (and TS-era) file ID: CRC-32 of the uppercased filename."""
    return zlib.crc32(filename.upper().encode("ascii", "replace")) & 0xFFFFFFFF


def classic_hash(filename: str) -> int:
    """Tiberian Sun / RA2 fallback "classic" hash used by some old files."""
    name = filename.upper().replace("\\", "").replace(":", "")[:12]
    h = 0
    for ch in name:
        h = (((h >> 21) | (h << 11)) & 0xFFFFFFFF) + ord(ch)
        h &= 0xFFFFFFFF
    return h


# ---------------------------------------------------------------------------
# MIX reading
# ---------------------------------------------------------------------------

@dataclass
class MixEntry:
    id: int
    offset: int
    size: int


class MixFile:
    def __init__(self, path):
        self.path = Path(path)
        self._fh = open(self.path, "rb")
        self.entries, self.data_start = self._read_index()

    def close(self):
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _read_index(self):
        fh = self._fh
        fh.seek(0)
        first = struct.unpack("<H", fh.read(2))[0]
        if first != 0:
            raise ValueError(f"{self.path}: not a TS/RA2 MIX (C&C format unsupported)")
        flags = struct.unpack("<H", fh.read(2))[0]
        if flags & 0x2:  # encrypted header
            fh.seek(4)
            key = westwood_decrypt_key_block(fh.read(80))
            fish = Blowfish(key)
            fh.seek(84)
            first_block = fish.decrypt_block(fh.read(8))
            num_files = struct.unpack("<H", first_block[:2])[0]
            block_count = (13 + num_files * 12) // 8
            fh.seek(84)
            header = fish.decrypt(fh.read(block_count * 8))
            return self._parse_entries(header[6:], num_files), 84 + block_count * 8
        # plain: [word 0][word flags][word count][dword size][entries...]
        fh.seek(4)
        num_files = struct.unpack("<H", fh.read(2))[0]
        fh.read(4)  # body size
        raw = fh.read(num_files * 12)
        return self._parse_entries(raw, num_files), 10 + num_files * 12

    @staticmethod
    def _parse_entries(raw: bytes, num_files: int):
        entries = []
        for i in range(num_files):
            hid, off, size = struct.unpack_from("<III", raw, i * 12)
            entries.append(MixEntry(hid, off, size))
        return entries

    def names(self) -> dict[int, str]:
        """Resolve known names via CRC/classic hash for common game files."""
        out = {}
        for e in self.entries:
            out.setdefault(e.id, f"_{e.id:08X}")
        return out

    def get(self, filename: str) -> bytes | None:
        for e in self.entries:
            if e.id in (crc_hash(filename), classic_hash(filename)):
                return self.read_entry(e)
        return None

    def read_entry(self, entry: MixEntry) -> bytes:
        self._fh.seek(self.data_start + entry.offset)
        return self._fh.read(entry.size)

    def all_entries(self):
        return list(self.entries)


# ---------------------------------------------------------------------------
# MIX writing (plain TS/RA2 format; the game accepts unencrypted mixes)
# ---------------------------------------------------------------------------

def xcc_local_database(names: list[str]) -> bytes:
    """'local mix database.dat' content (format via OpenRA XccLocalDatabase.cs).

    External tools (XCC, WAE) use this file to enumerate a MIX by name; the
    YR engine itself does NOT: the image contains no "local mix database"
    string at all and MixFileClass lookups are pure CRC32 hits (0x5B44D5).

    Do not confuse it with the INI wildcard loading: the battle/rules lists are
    enumerated on the FILESYSTEM with FindFirstFileA ("BATTLEMD*.INI" at
    VA 0x8261A8, pushed at 0x52CBA0; "BATTLEMD.INI" fallback at 0x826198,
    pushed at 0x52CCCD), so a same-named file packed inside a MIX is never
    matched by that wildcard - only a loose file in the game directory is.
    (Earlier revisions of this comment claimed the wildcard went through this
    database; that is wrong - see docs/re/fs_mix_load_chain_deep.md.)
    """
    out = bytearray()
    out += b"XCC by Olaf van der Spek"
    out += bytes([0x1A, 0x04, 0x17, 0x27, 0x10, 0x19, 0x80, 0x00])
    out += struct.pack("<i", sum(len(n) for n in names) + len(names) + 52)
    out += struct.pack("<i", 0)  # type
    out += struct.pack("<i", 0)  # version
    out += struct.pack("<i", 0)  # game/format
    out += struct.pack("<i", len(names))
    for n in names:
        out += n.encode("ascii") + b"\x00"
    return bytes(out)


def write_mix(path, files: dict[str, bytes], include_database: bool = True):
    """Write a plain (unencrypted) TS/RA2-format MIX. `files` maps filename->bytes.

    include_database adds the XCC "local mix database.dat" name list. The game
    engine does not read it (see xcc_local_database), and because an
    expandmdNN.mix is loaded *before* ra2md.mix a database here would shadow an
    official one for external tools - ra2forge passes False.
    """
    files = dict(files)
    if include_database:
        files["local mix database.dat"] = xcc_local_database(
            sorted(n.upper() for n in files))
    names = sorted(files)
    entries = []
    offset = 0
    for name in names:
        data = files[name]
        entries.append((crc_hash(name), offset, len(data)))
        offset += len(data)
    header = struct.pack("<HHHI", 0, 0, len(names), offset)  # fmt, flags, count, size
    entry_bytes = b"".join(struct.pack("<III", *e) for e in entries)
    out = bytearray(header + entry_bytes)
    for name in names:
        out += files[name]
    Path(path).write_bytes(bytes(out))
    return Path(path)

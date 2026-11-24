# -*- coding: utf-8 -*-
"""[2]0LoadBench_U0400.yrm 大版/小版逐维比对（只读磁盘，不启动游戏、不读活进程）。

大版: ra2bench/[2]0LoadBench_U0400.yrm           (92,332 B)
小版: out/loadbench/[2]0LoadBench_U0400.yrm      (25,604 B)
参照: out/loadbench/pristine/old/[2]0LoadBench_U0400.yrm
旁证（维度 6 用，只读）:
  out/re_work/.../qc161_u0400_trip/evidence/20261018T082850842354/XMP29U2.MAP  (222,799 B, T32 时代)
  out/re_work/.../PRESERVED_DIFF/.../20261018T194837677387/XMP29U2.MAP         (311,822 B, l1 时代)
  out/re_work/.../qc104_live_trip/carrier/[2]0LoadBench_U0400.yrm              (222,799 B)

输出: _ld_diff_out.txt / _ld_diff_out.json（与本脚本同目录）。
"""
import sys

sys.dont_write_bytecode = True

import base64
import hashlib
import json
import math
import re
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "big": ROOT / "ra2bench" / "[2]0LoadBench_U0400.yrm",
    "small": ROOT / "out" / "loadbench" / "[2]0LoadBench_U0400.yrm",
    "ref": ROOT / "out" / "loadbench" / "pristine" / "old" / "[2]0LoadBench_U0400.yrm",
    "xmp_t32": ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead"
               / "qc161_u0400_trip" / "evidence" / "20261018T082850842354" / "XMP29U2.MAP",
    "xmp_l1": ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead"
              / "qc161_carrier_cleanup_20261023" / "PRESERVED_DIFF" / "qc161_u0400_trip"
              / "evidence" / "20261018T194837677387" / "XMP29U2.MAP",
    "carrier_qc104": ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead"
                     / "qc104_live_trip" / "carrier" / "[2]0LoadBench_U0400.yrm",
}

SEC_RE = re.compile(r"^\[([^\[\]]+)\]$", re.M)


def read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def fingerprint(data: bytes) -> dict:
    n = len(data)
    md5 = hashlib.md5(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    crc32 = "%08x" % (zlib.crc32(data) & 0xFFFFFFFF)
    # 香农熵（bit/byte）
    if n:
        cnt = Counter(data)
        ent = -sum((c / n) * math.log2(c / n) for c in cnt.values())
    else:
        ent = 0.0
    printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13)) / max(n, 1)
    crlf = data.count(b"\r\n")
    lf_total = data.count(b"\n")
    return {
        "size": n,
        "md5": md5,
        "sha256": sha256,
        "crc32": crc32,
        "entropy_bits_per_byte": round(ent, 4),
        "printable_ascii_ratio": round(printable, 6),
        "crlf_pairs": crlf,
        "lf_total": lf_total,
        "bare_lf": lf_total - crlf,
        "zlib_magic_0x78": bool(n >= 2 and data[0] == 0x78 and data[1] in (0x01, 0x9C, 0xDA, 0x5E)),
    }


def head32(data: bytes) -> str:
    return data[:32].decode("latin-1")


def parse_sections(data: bytes) -> "dict[str, list[tuple[str, str]]]":
    text = data.decode("latin-1")
    secs: dict = {}
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        m = re.match(r"^\[([^\[\]]+)\]$", line.strip())
        if m:
            cur = m.group(1)
            secs.setdefault(cur, [])
            continue
        if cur is None or line.startswith(";") or not line.strip():
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            secs[cur].append((k.strip(), v))
    return secs


def entity_counts(secs) -> dict:
    out = {}
    for sec in ("Units", "Infantry", "Structures"):
        rows = secs.get(sec, [])
        per_house = Counter()
        for k, v in rows:
            house = v.split(",", 1)[0]
            per_house[house] += 1
        out[sec] = {
            "rows": len(rows),
            "per_house": dict(sorted(per_house.items())),
            "present": sec in secs,
        }
    return out


def unit_type_multiset(secs, sec):
    c = Counter()
    for _, v in secs.get(sec, []):
        parts = v.split(",")
        if len(parts) >= 2:
            c[(parts[0], parts[1])] += 1
    return c


def basic_map(secs) -> dict:
    def get(sec, key):
        for k, v in secs.get(sec, []):
            if k.lower() == key.lower():
                return v
        return None
    return {
        "Basic.Name": get("Basic", "Name"),
        "Basic.Author": get("Basic", "Author"),
        "Basic.NewINIFormat": get("Basic", "NewINIFormat"),
        "Map.Size": get("Map", "Size"),
        "Map.LocalSize": get("Map", "LocalSize"),
        "Map.Theater": get("Map", "Theater"),
        "Header.Width": get("Header", "Width"),
        "Header.Height": get("Header", "Height"),
    }


PACKS = ("PreviewPack", "IsoMapPack5", "OverlayPack", "OverlayDataPack")


def pack_sizes(secs) -> dict:
    out = {}
    for name in PACKS:
        rows = secs.get(name, [])
        b64 = "".join(v.strip() for _, v in rows).encode("latin-1")
        raw = None
        dec_err = None
        try:
            raw = base64.b64decode(b64 + b"=" * (-len(b64) % 4))
        except Exception as e:  # noqa: BLE001
            dec_err = str(e)
        zlib_ok = []
        if raw:
            for label, wb in (("zlib", 15), ("raw-deflate", -15), ("gzip", 31)):
                try:
                    zlib.decompress(raw, wb)
                    zlib_ok.append(label)
                except Exception:  # noqa: BLE001, PERF203
                    pass
        out[name] = {
            "b64_lines": len(rows),
            "b64_bytes": len(b64),
            "decoded_bytes": len(raw) if raw is not None else None,
            "decode_error": dec_err,
            "zlib_decompress_ok": zlib_ok,
            "decoded_head_hex": raw[:8].hex() if raw else None,
        }
    return out


def main() -> None:
    data = {k: read_bytes(p) for k, p in FILES.items() if p.exists()}
    missing = [k for k, p in FILES.items() if not p.exists()]
    fps = {k: fingerprint(v) for k, v in data.items()}
    heads = {k: head32(v) for k, v in data.items()}
    secs = {k: parse_sections(v) for k, v in data.items()}
    ents = {k: entity_counts(s) for k, s in secs.items()}
    bm = {k: basic_map(s) for k, s in secs.items()}
    packs = {k: pack_sizes(s) for k, s in secs.items()}

    big_sec = set(secs["big"])
    small_sec = set(secs["small"])
    sec_common = sorted(big_sec & small_sec)
    sec_big_only = sorted(big_sec - small_sec)
    sec_small_only = sorted(small_sec - big_sec)

    mu_big = unit_type_multiset(secs["big"], "Units")
    mu_small = unit_type_multiset(secs["small"], "Units")
    overlap_units = sum((mu_big & mu_small).values())
    mi_big = unit_type_multiset(secs["big"], "Infantry")
    mi_small = unit_type_multiset(secs["small"], "Infantry")
    overlap_inf = sum((mi_big & mi_small).values())

    def sample_rows(sec, n=3):
        def take(s):
            return [f"{k}={v}" for k, v in secs[s].get(sec, [])[:n]]
        return {"big": take("big"), "small": take("small")}

    same_big_ref = fps["big"]["md5"] == fps["ref"]["md5"]

    report = {
        "generated_at": "2026-11-10",
        "rule": "只读磁盘文件；不启动游戏、不读活进程",
        "files": {
            k: {"path": str(FILES[k]), "exists": k in data,
                **(fps.get(k, {}))} for k in FILES
        },
        "missing_inputs": missing,
        "ref_is_identical_to_big": same_big_ref,
        "head32": heads,
        "basic_and_map": bm,
        "entity_counts": ents,
        "pack_sections": packs,
        "sections": {
            "big_count": len(big_sec),
            "small_count": len(small_sec),
            "common_count": len(sec_common),
            "common": sec_common,
            "big_only": sec_big_only,
            "small_only": sec_small_only,
        },
        "unit_type_multiset": {
            "units_overlap_of_240": overlap_units,
            "infantry_overlap_of_160": overlap_inf,
            "units_sample": sample_rows("Units"),
            "infantry_sample": sample_rows("Infantry"),
        },
        "compression_test": {
            "small_zlib_magic": fps["small"]["zlib_magic_0x78"],
            "small_entropy": fps["small"]["entropy_bits_per_byte"],
            "big_entropy": fps["big"]["entropy_bits_per_byte"],
            "small_printable_ratio": fps["small"]["printable_ascii_ratio"],
        },
        "fingerprint_unresolved": {
            "ledger_93c2974b": "台账 T32『U0400 字节（93c2974b）』未匹配到任何在盘候选的 "
                               "md5/sha1前缀/crc32（big=3c47bff8/ad4855d, small=d9a57d5f/db493c05, "
                               "T32变体=11ec8ff6/4c2cebd9）；map-name 内 fp:xxxx 为项目内部指纹，"
                               "已证非文件 md5 前缀（U0800_H1 md5 前缀 11b3672276da ≠ fp:1189b6b550ff）",
        },
    }

    # ---------------- 六维 Difference ----------------
    b, s = fps["big"], fps["small"]
    diffs = [
        {
            "dim": "1. 头 32 字节（魔数/版本/section 个数/标志位）",
            "big": "前 32 字节 = '; Map created with FinalAlert 2(t'（CRLF 行尾），FinalAlert 2 标准注释头；"
                   "随后 '; Get it at http://www.westwood.com'。文本 INI，无二进制魔数/版本号/section 计数/标志位字段；"
                   "格式标识就是 FA2 注释头 + [Header](Width=46/Height=44/StartX=232…NumberStartingPoints=2)",
            "small": "前 32 字节 = '[Header]\\nWidth=100\\nHeight=100\\nSt'（纯 LF 行尾，全文件 0 个 CR vs 大版 1808 个）；"
                   "无 FA2 注释头，直接 [Header]，且 [Header] 键集不同（Width=100/Height=100/StartX=200/"
                   "Waypoint1=220,60 逗号坐标风格——非 RA2 标准 [Waypoints] 小节风格）",
            "meaning": "两版头 32 字节不一致，且都不是二进制容器——『魔数/版本/section 个数/标志位』这类字段不存在，"
                       "能比的是文本头与行尾。行尾（CRLF vs LF）与头的写法证明两文件出自不同工具链"
                       "（FA2 派生 vs 生成器直排），不是同一份文件的两个副本。对『实载哪一版』："
                       "实载判定不能在这两份之间二选一，必须引入第三者（见维度 6 的 T32 变体）。",
            "matters": True,
        },
        {
            "dim": "2. [Units]/[Infantry]/[Structures] 行数",
            "big": "[Units]=240（Americans 120 + Russians 120）、[Infantry]=160（各 80）、"
                   "[Structures]=41（全 Neutral）——共 1575 键行",
            "small": "[Units]=240（Americans 120 + Russians 120）、[Infantry]=160（各 80）、"
                   "[Structures] 小节整个不存在（0 行）——共 643 键行",
            "meaning": "数量层面两版前两项完全相同（240/160，且 U0400 命名 = 240+160=400 实体），"
                       "但小版不是大版的子集：240 units 的 (House,Type) 多重集重叠仅 %d/240，"
                       "160 infantry 重叠 %d/160；坐标（大版 8,11 起 vs 小版 80,33 起）、任务（Area Guard vs Hunt）、"
                       "型别序列均不同。关键分歧在 [Structures]：41 只存在于大版。台账『1680/1120/41 建筑』"
                       "与大版对不上 1680/1120、与小版对不上 41——两份都不是台账描述的那份，"
                       "但 41 建筑把实载谱系锁定在大版一脉（52×53 底图派生系）。" % (overlap_units, overlap_inf),
            "matters": True,
        },
        {
            "dim": "3. 可读字符串/小节清单（strings 等价物：全文件皆可打印 ASCII，strings 无增益，用小节差集）",
            "big": "34 个小节。小版缺的 21 节全部在大版：[Structures] [Terrain](267 行) [Smudge] [Triggers] [Tags] "
                   "[Events] [Actions] [ScriptTypes] [VehicleTypes] [AircraftTypes] [AITriggerTypesEnable] "
                   "[Digest] [Ranking] [GAYARD] [NAYARD] [YAYARD] [NEGLAMP] [INGALITE] [INYELWLAMP] "
                   "[06E16DE0] [0786DA60-G]",
            "small": "28 个小节。小版独有 15 节：[Houses] + 14 个 house 小节（Americans/Alliance/French/Germans/"
                   "British/Africans/Arabs/Confederation/Russians/YuriCountry/GDI/Nod/Neutral/Special）。"
                   "共同小节 13 个；小版 [Waypoints] 仅 2 行（大版 19 行）",
            "meaning": "小版是『纯兵力摆放』图：没有地形物件（Terrain 267 行全缺）、没有触发/标签/动作/脚本/AI 触发、"
                       "没有 [Digest]。大版是 FA2 完整图。若实载的是小版，游戏内不可能出现触发与建筑行为；"
                       "这也解释了大小差 3.6 倍的主体来源（Terrain/IsoMapPack/建筑与触发系文本）。"
                       "小版多出 15 个 house 小节说明它按 14+1 个国家显式布房，而大版不写（交给游戏默认）。",
            "matters": True,
        },
        {
            "dim": "4. section 表（容器与四个 Pack 小节）",
            "big": "非 Pack/IsoMap 二进制容器——两版都是文本 INI，『section 表』即小节序列（34 节，集合见 json）。"
                   "[Map] Size=0,0,52,53 / LocalSize=2,5,47,42（城市突击战 Urban Rush Pro 底图几何）；"
                   "IsoMapPack5 b64=%d B（awk 复核 528 行/36,912 字符一致），解码 %d B＝真实地块数据"
                   % (packs["big"]["IsoMapPack5"]["b64_bytes"],
                      packs["big"]["IsoMapPack5"]["decoded_bytes"]),
            "small": "同样非二进制容器（28 节）。[Map] Size=0,0,100,100 / LocalSize=1,1,98,98——与底图几何完全不同；"
                   "IsoMapPack5 b64=%d B（awk 复核 1 行/16 字符一致），解码仅 %d B＝桩，"
                   "无真实地块数据（生成器全族皆如此：U0800 plain/U0800 H1/XMP29U2.MAP-U0800H1 的 "
                   "IsoMapPack5 解码同为 12 B 桩；游戏侧等效全缺省 clear 地块=平地效果）"
                   % (packs["small"]["IsoMapPack5"]["b64_bytes"],
                      packs["small"]["IsoMapPack5"]["decoded_bytes"]),
            "meaning": "两版都无二进制 section 表可列，但 Pack 尺寸与 [Map] 几何证明这是两张不同的图"
                       "（52×53 vs 100×100，IsoMapPack5 体积不同）。"
                       "谱系上：大版 52×53 与 T32 时代实载变体（XMP29U2.MAP 证据件，同为 Size=0,0,52,53/"
                       "LocalSize=2,5,47,42）同底图；小版 100×100 与 U0800 H1 系（3360/2240 那份 .MAP）同几何。"
                       "对『实载哪一版』是直接定位证据。",
            "matters": True,
        },
        {
            "dim": "5. 压缩/编码（小版是否大版的 LZO/zlib 压缩形态）",
            "big": "明文 INI：可打印 ASCII 占比 %.4f，熵 %.3f bit/byte（文本典型值），首字节 ';'（0x3B）非任何压缩流魔数"
                   % (b["printable_ascii_ratio"], b["entropy_bits_per_byte"]),
            "small": "明文 INI：可打印 ASCII 占比 %.4f，熵 %.3f bit/byte，首字节 '['（0x5B）；"
                   "zlib 魔数 0x78 检测=%s；无 LZO 容器结构；内容层面直接否证——压缩不改变语义，"
                   "而两版 [Map] 尺寸/Author/小节集合/单位坐标全部不同，故小版不是大版的任何压缩或变换形态"
                   % (s["printable_ascii_ratio"], s["entropy_bits_per_byte"], fps["small"]["zlib_magic_0x78"]),
            "meaning": "『差 3.6 倍 = 差在压缩』假设被三重证据排除：熵（两者都是文本熵，非 8 bit/byte 的压缩流）、"
                       "头字节（可读文本起头）、内容结构矛盾（压缩是等价变换，两版语义不同）。"
                       "大小差来自内容量不同（1575 vs 643 键行、Terrain/触发系/建筑系整段缺失），不是编码。"
                       "对『实载哪一版』：排除压缩解释后，唯一剩余解释就是两版本就是两张不同的图。",
            "matters": True,
        },
        {
            "dim": "6. 三份 .yrm 与实载 XMP29U2.MAP 的关系",
            "big": "ra2bench/（=游戏目录，内有 YURI.exe/game.exe/BINKW32.DLL）中的 [2]0LoadBench_U0400.yrm，"
                   "92,332 B，md5=3c47bff8…，与参照件 pristine/old/ 逐字节同一（md5+sha256 全等：%s）。"
                   "Content=Urban Rush Pro 底图 + 2 房各 120 车/80 步 + 41 建筑。"
                   "旁证：h1_install/tmp/restore_probe(_badbak) 两份副本同为 3c47bff8" % same_big_ref,
            "small": "out/loadbench/ 中同名文件，25,604 B，md5=d9a57d5f…，mtime 2026-09-25 18:41 "
                   "（比大版 20:38 早约 2 小时）＝生成器第一代合成图（100×100、IsoMapPack5 仅 12 B 桩无真实地块、"
                   "240/160、0 建筑、2 waypoint）。"
                   "第三份（参照件）与大版同一件。真正实载的字节是第四份：T32 时代 XMP29U2.MAP=222,799 B、"
                   "md5=11ec8ff6、[Basic].Name='[2] 0LoadBench U0400'、Urban Rush 底图 52×53、"
                   "14 房×(120 车+80 步)=1680/1120 + 41 建筑——即台账『1680/1120/41 建筑』描述的那份"
                   "（qc104_live_trip/carrier, 2026-10-16 08:20 在盘同 md5）；"
                   "l1 时代 XMP29U2.MAP 换成 U0800 H1 字节（311,822 B，14 房×240 车+160 步=3360/2240、"
                   "0 建筑、Special=240）——即台账『3360/2240/0 建筑』与判据『.MAP Special 预置 240』的那份",
            "meaning": "实载既不是大版也不是小版：台账判据（c5574 八帧恒 240 = .MAP 的 Special 预置 240，"
                       "而任何 U0400 yrm 变体每房只有 120 车）在三份 .yrm 上全部成立——"
                       "大版/小版/参照件的 [Units] 每 house 都是 120，谁也产不出 240。"
                       "三份 .yrm 的身份：参照件=大版的逐字节存档（给指纹 3c47bff8/cb5785a1…）；"
                       "大版=游戏目录当前在位件（Sep 25 世代）；小版=生成器首代合成图（Sep 25 18:41，"
                       "被 20:38 的 FA2 系取代后遗留在 out/loadbench）。台账里的『[2]0LoadBench_U0400.yrm（1680/1120/41）』"
                       "实指 222,799 B 的第三世代变体，其字节以 XMP29U2.MAP 之名松散补缺被游戏实载——文件名相同、字节不同。"
                       "台账指纹 93c2974b 未能在在盘候选的 md5/sha1 前缀/CRC32 上复现（各候选值已列 json），"
                       "判为项目内部指纹格式，本项未破解，如实标注。",
            "matters": True,
        },
    ]

    verdict = {
        "small_is": "out/loadbench/[2]0LoadBench_U0400.yrm（25,604 B）是 RA2 Campaign Forge 生成器于 2026-09-25 18:41 "
                    "生成的第一代合成 LoadBench 图：100×100、IsoMapPack5 仅 12 B 桩（无真实地块）、"
                    "240 units+160 infantry（每房 120/80）、0 建筑、2 waypoint、15 个 house 小节、LF 行尾"
                    "——与 92,332 B 大版（Urban Rush Pro 底图 + 真实地块 27,684 B + 41 建筑 + 触发系）"
                    "不是同一张图、不是其子集、不是其压缩形态；两份只是共享同一个文件名",
        "same_format": "不是同一种『格式产物』但同属 RA2 文本 INI 地图方言：大版=FinalAlert 2 派生（CRLF、FA2 注释头、"
                       "完整触发/地形/建筑系），小版=生成器直排（LF、无注释头、无 [Structures]/Terrain/Triggers/Digest）。"
                       "称不上『两种格式』（游戏读取器同源可解析），但确定是两条产出链",
        "loaded_one": "台账判据所指实载字节 = 222,799 B 变体（md5 11ec8ff6，[Basic].Name='[2] 0LoadBench U0400'，"
                      "1680/1120/41）以 XMP29U2.MAP 名被载入；其后 l1 时代换成 U0800 H1 字节（3360/2240/0，Special=240）。"
                      "大版/小版/参照件三份 .yrm 均非该判据的实载字节",
        "confidence": "高。每一项结论都有在盘文件直接证据（md5/sha256/小节计数/键行样例），无推测项；"
                      "唯一未决是台账指纹 93c2974b 的具体算法（已列所有否证数值）",
    }

    report["differences"] = diffs
    report["verdict"] = verdict

    outdir = Path(__file__).resolve().parent
    (outdir / "_ld_diff_out.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    a = lines.append
    a("=" * 78)
    a("[2]0LoadBench_U0400.yrm 大版/小版逐维比对  (2026-11-10, 只读磁盘)")
    a("=" * 78)
    a("")
    a("[指纹]")
    for k in ("big", "small", "ref", "xmp_t32", "xmp_l1", "carrier_qc104"):
        if k in fps:
            f = fps[k]
            a("  %-14s %9d B  md5=%s  crc32=%s  entropy=%.3f  printable=%.4f  CRLF=%d LF=%d"
              % (k, f["size"], f["md5"], f["crc32"], f["entropy_bits_per_byte"],
                 f["printable_ascii_ratio"], f["crlf_pairs"], f["lf_total"]))
        else:
            a("  %-14s <missing: %s>" % (k, FILES[k]))
    a("  参照件 pristine/old 与大版同一份（md5+sha256 全等）: %s" % same_big_ref)
    a("")
    a("[头 32 字节]")
    for k in ("big", "small"):
        a("  %-6s %r" % (k, heads[k]))
    a("")
    a("[Basic]/[Map]")
    for k in ("big", "small", "xmp_t32", "xmp_l1"):
        if k in bm:
            a("  %-9s %s" % (k, bm[k]))
    a("")
    a("[实体行数]")
    for k in ("big", "small", "xmp_t32", "xmp_l1"):
        if k in ents:
            e = ents[k]
            a("  %-9s Units=%s Infantry=%s Structures=%s"
              % (k, e["Units"]["rows"], e["Infantry"]["rows"], e["Structures"]["rows"]))
            for sec in ("Units", "Infantry", "Structures"):
                if e[sec]["per_house"]:
                    a("      %-10s %s" % (sec, e[sec]["per_house"]))
    a("")
    a("[小节差集] big=%d small=%d common=%d" % (len(big_sec), len(small_sec), len(sec_common)))
    a("  big-only (%d): %s" % (len(sec_big_only), " ".join(sec_big_only)))
    a("  small-only(%d): %s" % (len(sec_small_only), " ".join(sec_small_only)))
    a("")
    a("[Pack 小节]")
    for k in ("big", "small"):
        a("  %s:" % k)
        for name, info in packs[k].items():
            a("    %-15s b64=%7d B  decoded=%s  zlib_ok=%s  head=%s"
              % (name, info["b64_bytes"], info["decoded_bytes"],
                 info["zlib_decompress_ok"], info["decoded_head_hex"]))
    a("")
    a("[多重集重叠] units %d/240, infantry %d/160" % (overlap_units, overlap_inf))
    a("  Units 样例 big   : %s" % report["unit_type_multiset"]["units_sample"]["big"])
    a("  Units 样例 small : %s" % report["unit_type_multiset"]["units_sample"]["small"])
    a("")
    a("[压缩检验] small zlib_magic=%s entropy=%.3f printable=%.4f  => 明文 INI，非压缩形态"
      % (fps["small"]["zlib_magic_0x78"], fps["small"]["entropy_bits_per_byte"],
         fps["small"]["printable_ascii_ratio"]))
    a("")
    a("[六维 Difference]")
    for d in diffs:
        a("-" * 78)
        a("◆ %s" % d["dim"])
        a("  大版: %s" % d["big"])
        a("  小版: %s" % d["small"])
        a("  含义: %s" % d["meaning"])
        a("  matters=%s" % d["matters"])
    a("-" * 78)
    a("[结论] %s" % verdict["small_is"])
    a("[实载] %s" % verdict["loaded_one"])
    a("[置信] %s" % verdict["confidence"])
    a("[未决] %s" % report["fingerprint_unresolved"]["ledger_93c2974b"])

    (outdir / "_ld_diff_out.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("written:", outdir / "_ld_diff_out.txt")
    print("written:", outdir / "_ld_diff_out.json")


if __name__ == "__main__":
    main()

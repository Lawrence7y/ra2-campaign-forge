#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R16-COMMON-D47 verification (re-runnable).

Checks the CURRENT on-disk state of the two target files:
  1. R14_COMMON.md is a pure APPEND: the first N bytes (N = pre-change length)
     hash to the pre-change full-file sha256, and the tail equals the exact
     appended byte segment recorded at apply time.
  2. COVERAGE/PANEL.md is an INSERT: deleting the inserted segment at the
     recorded offset reproduces the pre-change file byte-for-byte, whose
     sha256 equals the pre-change sha256. (Prefix hash is deliberately NOT
     used for PANEL.)
  3. Line-ending deltas match exactly the bytes we inserted/appended
     (i.e. our edits introduced no CRLF).

Run:  python -X utf8 verify.py
Exit 0 = all PASS; exit 1 = at least one FAIL.
"""
import os, base64, hashlib

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
R14 = os.path.join(BASE, "R14_COMMON.md")
PANEL = os.path.join(BASE, "COVERAGE", "PANEL.md")

# ---- constants recorded at apply time (pre-change state) ----
R14_BEFORE_LEN = 227963
R14_BEFORE_SHA = "5e63809f09dd0092963b5c254e633a3d62b3317876fe5aaf95bdddb9e8ccdb7e"
R14_APPEND_B64 = (
    'CiMjIyDCpzEyLjQg44CQQ09NTU9OLVIxNiDov73liqDvvIwyMDI2LTExLTIw44CRRC00NyDoo4HlhrMg4oCU4oCUIEQtNDMoQSkg'
    '5LyY5YWI77yMwqcxMi4zIOWvueOAjOa0uyB2dGFibGUg5qe95L2N44CN5b2i5oCB5q2j5byP6K6p5L2NCgo+IOOAkOaWh+S7tuWu'
    'muS9jeOAkeacrOiKguaMieeUqOaItyAyMDI2LTExLTIwIOijgeWGs+aIkOaWh++8m+i/veWKoOS6juaWh+S7tuacgOacq++8iOaW'
    'h+S7tuacq+WwvuWOn+S4uiDCpzE2LjHvvInvvIzoh6rmiJDkuIDoioLjgIIKCioq5Yay56qB6YeN6L+wKirvvJpELTQzKEEpIOaK'
    'iiBgdnRbc2xvdF0gPT0gZW50cnlgIOWGmei/myDikaMg55qE5a6a5LmJ77ybwqcxMi4zIOemgeatoiDikaHikaMg5YWx55So5ZCM'
    '5LiA6Jma6KGo5qe9IOKHkiDjgIzmtLsgdnRhYmxlIOanveS9jeOAjeW9ouaAgeeahCDikaMg5b+F54S26L+d5Y+NIMKnMTIuM+OA'
    'gioq6L+Z5LiN5piv5Liq5qGIKirvvIxTMTMg55qEIDYg6KGM44CBYE5BTUVEX1BVU0hfQVVESVQyYCDnmoQgMTAg6KGM44CBTTcx'
    'IOaJgOi/sCDiiaUyMSDooYzjgIHku6Xlj4ogdHJhY2Utb25seSDnmoQgNDMg6KGMIGBzbG90TmAg5YWo6YOo6JC95Zyo6K+l5Yay'
    '56qB6YeM44CCCgoqKuijgeWGsyoq77yaKipELTQzKEEpIOS8mOWFiO+8jMKnMTIuMyDlr7nor6XlvaLmgIHorqnkvY3jgIIqKiDn'
    'kIbnlLHvvJpELTQzKEEpIOaYr+abtOWFt+S9k+eahOaIkOaWh+WPo+W+hO+8m+aSpOmUgOWwhui/nuW4pue/u+i9rCBgW+W3suiv'
    'gV1gICoqMTU54oCTMjQwIOihjCArIHRyYWNlLW9ubHkgNDMg6KGMKirvvIzogIzmlY/mhJ/luqblrp7mtYvmmL7npLoqKuS4jee/'
    'u+i9rOS7u+S9lei+vuagh+WIpOWumioq77yI5ZCN5LmJ5LuNIDMvMjLjgIHkuKXmoLzku40gMS8yMuOAgVMxNyDku43ovr7moIfv'
    'vInjgIIKCioq5pWI5Yqb6IyD5Zu077yI5b+F6aG75YaZ5q2777yJKirvvJrmnKzoo4HlhrMqKuWPqioq6Kej6Zmk44CM5rS7IHZ0'
    'YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOS4jiDCpzEyLjMg55qE5Yay56qB77ybKirCpzEyLjMg5a+55YW25a6D5b2i5oCB57un'
    '57ut5pyJ5pWIKirigJTigJTljbPvvJrlh6Eg4pGjIOS4jeaYr+ivpeanveS9jeWNoOeUqOOAgeiAjOaYr+WPpuacieeLrOeri+mT'
    'vuiAhe+8jOS7jeS4jeW+l+S4jiDikaEg5YWx55So5ZCM5LiA5qe944CCCgoqKuW8leeUqOe6quW+i++8iOW/hemhu+WGmeatu++8'
    'iSoq77ya5LuK5ZCO5Lu75L2V5byV55So44CM5rS7IHZ0YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOeahOihjO+8jCoq5b+F6aG7'
    '5ZCM5pe25byV55So5pys5p2h5LiOIFBBTkVMIOeahOWvueW6lOaKq+mcsioq77yMKirkuI3lvpcqKuihqOi/sOS4uuOAjOW3sui/'
    'hyDCpzEyLjPjgI3jgIIKCioq5pS55Yik57qq5b6L77yI5b+F6aG75YaZ5q2777yJKirvvJroi6Xml6XlkI7mlLnliKQgwqcxMi4z'
    'IOiDnOWHuu+8jOmhuyoq5LiA5qyh5oCn5pW05om55aSE572uKirvvIzkuI3lvpfpm7bmlaPmlLnliKTjgIIKCioq6YeP5YyW5ZCO'
    '5p6c77yI54Wn5b2V77yM5LiN6YeN566X77yJKirvvJpgW+W3suivgV1gIOmHjCAxNTnigJMyNDAg6KGMICsgdHJhY2Utb25seSA0'
    'MyDooYwgYHNsb3ROYO+8m+WFtuS4rSA0MyDooYzlnKggwqcxMi4zIOS4peagvOivu+azleS4iyDikaMgKiowIOihjOWPr+ihpSoq'
    '44CB5oyJ5pys6KOB5YazKirlhajpg6jlj6/ooaUqKuOAggoKKiror4Hmja7mjIfpkogqKu+8mmBsZWFkXFBFTkRJTkdfREVDSVNJ'
    'T05TLm1kYO+8iEQtNDcg5p2h77yMMjAyNi0xMS0yMCDnlKjmiLfoo4HlhrPvvInvvJtgQ09WRVJBR0VcUEFORUwubWRgIEwxNjHi'
    'gJMxNjXvvIhNNzQg5oqr6Zyy77yJ77ybYFBST0JFXzgwMlxSRVBPUlQubWRg77ybYF9jYXJkc1xfQk9BUkRfUjExMS5tZGDvvJtg'
    'bGVhZFxuZXh0X3JlXzIwMjYxMTE3X3IxNFxSMTRfQ09NTU9OLm1kYCDCpzEyLjPjgIIK'
)
R14_APPEND_LE = {"crlf": 0, "lf": 18, "cr": 0}   # line endings inside appended bytes

PANEL_BEFORE_SHA = "968b3dccf7294a48be9b6f026a37d2d791bc1e662cf3123c0908cfa119abea49"
PANEL_INSERT_OFFSET = 73211
PANEL_INSERT_B64 = (
    'PiAqKuKchSBNODQg6KOB5Yaz6JC95a6a77yaRC00NyDlt7Loo4HvvIhB77yJ4oCU4oCUIEQtNDMoQSkg5LyY5YWI77yMwqcxMi4z'
    'IOWvueOAjOa0uyB2dGFibGUg5qe95L2N44CN5b2i5oCB5q2j5byP6K6p5L2NKirvvIjnlKjmiLcgMjAyNi0xMS0yMCDoo4HlhrPv'
    'vIkKPiBNNzQg5omA6L+w44CM5Lik5p2h5oiQ5paH6KeE5YiZ5q2j6Z2i5Yay56qB77yI5b6F6KOB77yJ44CNKirlt7Loo4EqKu+8'
    'jOacrOadoeWPluS7o+WFtuOAjOW+heijgeOAjeeKtuaAge+8iE03NCDljp/mlofkuI3mlLnvvIzlj6rlnKjlhbblkI7ooaXmnKzm'
    'iqvpnLLvvInjgIIKPiDlvbHlk43pnaLvvJpgW+W3suivgV1gICoqMTU54oCTMjQwIOihjCArIHRyYWNlLW9ubHkgNDMg6KGMIGBz'
    'bG90TmAqKu+8myoq5LiN57+76L2s5Lu75L2V6L6+5qCH5Yik5a6aKirvvIjlkI3kuYkgMy8yMuOAgeS4peagvCAxLzIy44CBUzE3'
    'IOS7jei+vuagh++8ieOAggo+ICoqNDMg6KGMIGBzbG90TmAg55qEIOKRoyDnlLHjgIwwIOihjOWPr+ihpeOAjeWPmOS4uuOAjOWF'
    'qOmDqOWPr+ihpeOAjSoq77yIwqcxMi4zIOS4peagvOivu+azleS4i+S4uiAw77yJ44CCCj4g5byV55So57qq5b6L77ya5byV55So'
    '44CM5rS7IHZ0YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOeahOihjCoq5b+F6aG75ZCM5byV5pys5p2hKirvvIwqKuS4jeW+lyoq'
    '6KGo6L+w5Li644CM5bey6L+HIMKnMTIuM+OAje+8m+aUueWIpOmhu+S4gOasoeaAp+aVtOaJueWkhOe9ruOAggo+IOaIkOaWh+S9'
    'jee9ru+8mmBSMTRfQ09NTU9OLm1kIMKnMTIuNGDjgIIK'
)
PANEL_INSERT_LE = {"crlf": 0, "lf": 6, "cr": 0}   # line endings inside inserted bytes


def sha(b):
    return hashlib.sha256(b).hexdigest()


def line_endings(b):
    crlf = lf = cr = 0
    n = len(b)
    for i, x in enumerate(b):
        if x == 10:
            if i > 0 and b[i-1] == 13:
                crlf += 1
            else:
                lf += 1
        elif x == 13 and (i == n-1 or b[i+1] != 10):
            cr += 1
    return {"crlf": crlf, "lf": lf, "cr": cr}


def check(name, ok, detail):
    print(("[PASS] " if ok else "[FAIL] ") + name + " :: " + detail)
    return ok


def main():
    all_ok = True
    r14 = open(R14, "rb").read()
    panel = open(PANEL, "rb").read()
    r14_append = base64.b64decode("".join(['CiMjIyDCpzEyLjQg44CQQ09NTU9OLVIxNiDov73liqDvvIwyMDI2LTExLTIw44CRRC00NyDoo4HlhrMg4oCU4oCUIEQtNDMoQSkg', '5LyY5YWI77yMwqcxMi4zIOWvueOAjOa0uyB2dGFibGUg5qe95L2N44CN5b2i5oCB5q2j5byP6K6p5L2NCgo+IOOAkOaWh+S7tuWu', 'muS9jeOAkeacrOiKguaMieeUqOaItyAyMDI2LTExLTIwIOijgeWGs+aIkOaWh++8m+i/veWKoOS6juaWh+S7tuacgOacq++8iOaW', 'h+S7tuacq+WwvuWOn+S4uiDCpzE2LjHvvInvvIzoh6rmiJDkuIDoioLjgIIKCioq5Yay56qB6YeN6L+wKirvvJpELTQzKEEpIOaK', 'iiBgdnRbc2xvdF0gPT0gZW50cnlgIOWGmei/myDikaMg55qE5a6a5LmJ77ybwqcxMi4zIOemgeatoiDikaHikaMg5YWx55So5ZCM', '5LiA6Jma6KGo5qe9IOKHkiDjgIzmtLsgdnRhYmxlIOanveS9jeOAjeW9ouaAgeeahCDikaMg5b+F54S26L+d5Y+NIMKnMTIuM+OA', 'gioq6L+Z5LiN5piv5Liq5qGIKirvvIxTMTMg55qEIDYg6KGM44CBYE5BTUVEX1BVU0hfQVVESVQyYCDnmoQgMTAg6KGM44CBTTcx', 'IOaJgOi/sCDiiaUyMSDooYzjgIHku6Xlj4ogdHJhY2Utb25seSDnmoQgNDMg6KGMIGBzbG90TmAg5YWo6YOo6JC95Zyo6K+l5Yay', '56qB6YeM44CCCgoqKuijgeWGsyoq77yaKipELTQzKEEpIOS8mOWFiO+8jMKnMTIuMyDlr7nor6XlvaLmgIHorqnkvY3jgIIqKiDn', 'kIbnlLHvvJpELTQzKEEpIOaYr+abtOWFt+S9k+eahOaIkOaWh+WPo+W+hO+8m+aSpOmUgOWwhui/nuW4pue/u+i9rCBgW+W3suiv', 'gV1gICoqMTU54oCTMjQwIOihjCArIHRyYWNlLW9ubHkgNDMg6KGMKirvvIzogIzmlY/mhJ/luqblrp7mtYvmmL7npLoqKuS4jee/', 'u+i9rOS7u+S9lei+vuagh+WIpOWumioq77yI5ZCN5LmJ5LuNIDMvMjLjgIHkuKXmoLzku40gMS8yMuOAgVMxNyDku43ovr7moIfv', 'vInjgIIKCioq5pWI5Yqb6IyD5Zu077yI5b+F6aG75YaZ5q2777yJKirvvJrmnKzoo4HlhrMqKuWPqioq6Kej6Zmk44CM5rS7IHZ0', 'YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOS4jiDCpzEyLjMg55qE5Yay56qB77ybKirCpzEyLjMg5a+55YW25a6D5b2i5oCB57un', '57ut5pyJ5pWIKirigJTigJTljbPvvJrlh6Eg4pGjIOS4jeaYr+ivpeanveS9jeWNoOeUqOOAgeiAjOaYr+WPpuacieeLrOeri+mT', 'vuiAhe+8jOS7jeS4jeW+l+S4jiDikaEg5YWx55So5ZCM5LiA5qe944CCCgoqKuW8leeUqOe6quW+i++8iOW/hemhu+WGmeatu++8', 'iSoq77ya5LuK5ZCO5Lu75L2V5byV55So44CM5rS7IHZ0YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOeahOihjO+8jCoq5b+F6aG7', '5ZCM5pe25byV55So5pys5p2h5LiOIFBBTkVMIOeahOWvueW6lOaKq+mcsioq77yMKirkuI3lvpcqKuihqOi/sOS4uuOAjOW3sui/', 'hyDCpzEyLjPjgI3jgIIKCioq5pS55Yik57qq5b6L77yI5b+F6aG75YaZ5q2777yJKirvvJroi6Xml6XlkI7mlLnliKQgwqcxMi4z', 'IOiDnOWHuu+8jOmhuyoq5LiA5qyh5oCn5pW05om55aSE572uKirvvIzkuI3lvpfpm7bmlaPmlLnliKTjgIIKCioq6YeP5YyW5ZCO', '5p6c77yI54Wn5b2V77yM5LiN6YeN566X77yJKirvvJpgW+W3suivgV1gIOmHjCAxNTnigJMyNDAg6KGMICsgdHJhY2Utb25seSA0', 'MyDooYwgYHNsb3ROYO+8m+WFtuS4rSA0MyDooYzlnKggwqcxMi4zIOS4peagvOivu+azleS4iyDikaMgKiowIOihjOWPr+ihpSoq', '44CB5oyJ5pys6KOB5YazKirlhajpg6jlj6/ooaUqKuOAggoKKiror4Hmja7mjIfpkogqKu+8mmBsZWFkXFBFTkRJTkdfREVDSVNJ', 'T05TLm1kYO+8iEQtNDcg5p2h77yMMjAyNi0xMS0yMCDnlKjmiLfoo4HlhrPvvInvvJtgQ09WRVJBR0VcUEFORUwubWRgIEwxNjHi', 'gJMxNjXvvIhNNzQg5oqr6Zyy77yJ77ybYFBST0JFXzgwMlxSRVBPUlQubWRg77ybYF9jYXJkc1xfQk9BUkRfUjExMS5tZGDvvJtg', 'bGVhZFxuZXh0X3JlXzIwMjYxMTE3X3IxNFxSMTRfQ09NTU9OLm1kYCDCpzEyLjPjgIIK']))
    panel_insert = base64.b64decode("".join(['PiAqKuKchSBNODQg6KOB5Yaz6JC95a6a77yaRC00NyDlt7Loo4HvvIhB77yJ4oCU4oCUIEQtNDMoQSkg5LyY5YWI77yMwqcxMi4z', 'IOWvueOAjOa0uyB2dGFibGUg5qe95L2N44CN5b2i5oCB5q2j5byP6K6p5L2NKirvvIjnlKjmiLcgMjAyNi0xMS0yMCDoo4HlhrPv', 'vIkKPiBNNzQg5omA6L+w44CM5Lik5p2h5oiQ5paH6KeE5YiZ5q2j6Z2i5Yay56qB77yI5b6F6KOB77yJ44CNKirlt7Loo4EqKu+8', 'jOacrOadoeWPluS7o+WFtuOAjOW+heijgeOAjeeKtuaAge+8iE03NCDljp/mlofkuI3mlLnvvIzlj6rlnKjlhbblkI7ooaXmnKzm', 'iqvpnLLvvInjgIIKPiDlvbHlk43pnaLvvJpgW+W3suivgV1gICoqMTU54oCTMjQwIOihjCArIHRyYWNlLW9ubHkgNDMg6KGMIGBz', 'bG90TmAqKu+8myoq5LiN57+76L2s5Lu75L2V6L6+5qCH5Yik5a6aKirvvIjlkI3kuYkgMy8yMuOAgeS4peagvCAxLzIy44CBUzE3', 'IOS7jei+vuagh++8ieOAggo+ICoqNDMg6KGMIGBzbG90TmAg55qEIOKRoyDnlLHjgIwwIOihjOWPr+ihpeOAjeWPmOS4uuOAjOWF', 'qOmDqOWPr+ihpeOAjSoq77yIwqcxMi4zIOS4peagvOivu+azleS4i+S4uiAw77yJ44CCCj4g5byV55So57qq5b6L77ya5byV55So', '44CM5rS7IHZ0YWJsZSDmp73kvY3jgI3lvaLmgIEg4pGjIOeahOihjCoq5b+F6aG75ZCM5byV5pys5p2hKirvvIwqKuS4jeW+lyoq', '6KGo6L+w5Li644CM5bey6L+HIMKnMTIuM+OAje+8m+aUueWIpOmhu+S4gOasoeaAp+aVtOaJueWkhOe9ruOAggo+IOaIkOaWh+S9', 'jee9ru+8mmBSMTRfQ09NTU9OLm1kIMKnMTIuNGDjgIIK']))

    # 1) R14_COMMON.md -- prefix hash (append verification)
    prefix = r14[:R14_BEFORE_LEN]
    prefix_sha = sha(prefix)
    all_ok &= check("R14 prefix-length sha256 == pre-change full-file sha256",
                    prefix_sha == R14_BEFORE_SHA,
                    "len=%d sha=%s expected=%s" % (len(prefix), prefix_sha, R14_BEFORE_SHA))
    all_ok &= check("R14 tail bytes == exact appended segment",
                    r14[R14_BEFORE_LEN:] == r14_append,
                    "tail_len=%d append_len=%d" % (len(r14)-R14_BEFORE_LEN, len(r14_append)))
    expect_len = R14_BEFORE_LEN + len(r14_append)
    all_ok &= check("R14 after-size == before-size + appended length",
                    len(r14) == expect_len,
                    "%d == %d" % (len(r14), expect_len))

    # 2) PANEL.md -- restoration hash (insert verification, NOT prefix hash)
    off = PANEL_INSERT_OFFSET
    nins = len(panel_insert)
    restored = panel[:off] + panel[off+nins:]
    restored_sha = sha(restored)
    all_ok &= check("PANEL insert-removed byte stream == pre-change file (sha256)",
                    restored_sha == PANEL_BEFORE_SHA,
                    "restored_sha=%s expected=%s" % (restored_sha, PANEL_BEFORE_SHA))
    all_ok &= check("PANEL inserted segment present at recorded offset",
                    panel[off:off+nins] == panel_insert,
                    "offset=%d insert_len=%d" % (off, nins))
    all_ok &= check("PANEL after-size == before-size + inserted length",
                    len(panel) == len(restored) + nins,
                    "%d == %d + %d" % (len(panel), len(restored), nins))

    # 3) line-ending deltas
    r14_le = line_endings(r14)
    panel_le = line_endings(panel)
    exp_r14 = {"crlf": 1081 + R14_APPEND_LE["crlf"],
               "lf": 474 + R14_APPEND_LE["lf"],
               "cr": 0 + R14_APPEND_LE["cr"]}
    exp_panel = {"crlf": 0 + PANEL_INSERT_LE["crlf"],
                 "lf": 589 + PANEL_INSERT_LE["lf"],
                 "cr": 0 + PANEL_INSERT_LE["cr"]}
    all_ok &= check("R14 CRLF/LF/CR counts == before + appended bytes",
                    r14_le == exp_r14, "got=%s expected=%s" % (r14_le, exp_r14))
    all_ok &= check("PANEL CRLF/LF/CR counts == before + inserted bytes",
                    panel_le == exp_panel, "got=%s expected=%s" % (panel_le, exp_panel))

    print("RESULT:", "ALL PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

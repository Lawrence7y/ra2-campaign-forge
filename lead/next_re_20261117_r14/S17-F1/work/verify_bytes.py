"""
S17-F1 independent byte re-verification of clue-doc claims.
All reads from disk (read-only). capstone skipdata=True.
"""
import pe_util as P

CHECKS = [
    # (va, expected_hex, label)
    (0x67D300, '83ec08535556 8bf1', 'Save_Core prologue'),
    (0x67D310, 'e8fbbf0000', 'call 0x689310 pre-save helper'),
    (0x67D31B, 'e82090e4ff', 'call 0x4C6340 0x44-byte writer'),
    (0x67D327, 'e80474ffff', 'call 0x674730 Rules block'),
    (0x67D32C, 'a160418b00', 'mov eax,[0x8B4160] vector#1 count'),
    (0x67D342, 'ff5110', 'call [ecx+0x10] IStream::Write'),
    (0x67D351, '8b2df4157e00', 'mov ebp,[0x7E15F4] OleSaveToStream'),
    (0x67D386, 'ffd5', 'call ebp = OleSaveToStream'),
    (0x67D1AF, 'e84c010000', 'call 0x67D300 (only caller)'),
    (0x67DF0F, 'e8dc1e0000', 'call 0x67FDF0 block#1'),
    (0x67DF08, 'ba303ea800', 'mov edx,0xA83E30 arg block#1'),
    (0x67E3AA, 'e8412b0000', 'call 0x680EF0 block#35'),
    (0x67E3BD, '833d38b2a80005', 'cmp [0xA8B238],5 Skirmish'),
    (0x67E3D9, 'e882d10100', 'call 0x69B560 Write_Skirmish_Session_Options'),
    (0x67FDF0, '83ec08535657 8bfa8bd9', 'template block fn #1 prologue'),
    (0x67FE6E, 'c3', 'template block fn #1 ret (127B end)'),
    (0x67FE6F, '90', 'template block fn #1 pad (128B)'),
    (0x680EF0, '83ec08535657 8bfa8bd9', 'template block fn #35 prologue'),
    (0x6805F0, '83ec08535657 8bfa8bd9', 'Save_Sides same template'),
    (0x67E0AF, 'e83c250000', 'call 0x6805F0 Save_Sides'),
    # Load core
    (0x67CEF0, '81ec90040000', 'Game outer prologue sub esp,0x490'),
    (0x67CF42, 'ff15c8157e00', 'call [0x7E15C8] StgCreateDocfile'),
    (0x67CF70, 'a160d58300', 'mov eax,[0x83D560] magic'),
    (0x67CF7D, 'e8fe400000', 'call 0x681080 setter'),
    (0x67E440, '81ec08050000', 'Load_Core prologue sub esp,0x508'),
    (0x67E489, '8b1de4157e00', 'mov ebx,[0x7E15E4] StgOpenStorage'),
    (0x67E4E3, 'e8e82d0000', 'call 0x6812D0 GameMode'),
    (0x67E4E8, 'a338b2a800', 'mov [0xA8B238],eax'),
    (0x67E56C, '68a8d58300', 'push 0x83D5A8 "CONTENTS"'),
    (0x67E572, 'ff5110', 'call [ecx+0x10] IStorage::OpenStream'),
    (0x67E840, '8b3df8157e00', 'mov edi,[0x7E15F8] OleLoadFromStream'),
    # gating chain (W157/§894)
    (0x55DBCD, '393d38b2a800', 'cmp [0xA8B238],edi'),
    (0x55DBD3, '0f85c0000000', 'jne 0x55DC99'),
    (0x55DBD9, 'a008ceab00', 'mov al,[0xABCE08]'),
    (0x55DBDE, '84c0', 'test al,al'),
    (0x55DBE0, '0f85b3000000', 'jne 0x55DC99'),
    (0x55DBEE, 'c60508ceab0001', 'mov byte [0xABCE08],1'),
    (0x55DC92, 'e859f21100', 'call 0x67CEF0'),
    # scalar CurrentFrame
    (0x67F819, '6884eda800', 'push 0xA8ED84 CurrentFrame'),
    (0x67D421, 'e8ba230000', 'call 0x67F7E0 scalar writer'),
    (0x67E8B5, 'e806110000', 'call 0x67F9C0 scalar reader'),
    # magic
    (0x83D560, '98b80200', 'Savegame_Magic 0x2B898'),
    (0x681080, '8b4424048901c20400', 'setter 0x681080'),
    # Swizzle
    (0x6CF0C8, 'c70510c1b00008417f00', 'mov [0xB0C110],0x7F4108 SwizzleMgr vptr'),
    (0x6CF2A8, 'c70700000000', 'mov dword [edi],0 (Here_I_Am zero; true ModRM=07)'),
    (0x7F7C80, '0901000000000000c000000000000046', 'IID_IPersistStream'),
]

def norm(h): return h.replace(' ', '').lower()

ok = bad = noup = 0
for va, exp, label in CHECKS:
    got = P.read(va, len(exp)//2)
    g = got.hex() if got else None
    e = norm(exp)
    if g is None:
        st = 'NOREAD'; noup += 1
    elif g == e:
        st = 'OK'; ok += 1
    else:
        st = 'MISMATCH'; bad += 1
    print(f"{st:9s} 0x{va:08X} exp={e:32s} got={g or '--':32s} {label}")

print(f"\nTOTAL={len(CHECKS)} OK={ok} MISMATCH={bad} NOREAD={noup}")

# Which constructors register an `AbstractClass`?

All statements below are `[已证]` unless marked otherwise. Addresses are VAs in `gamemd.exe` (ImageBase `0x400000`).

## 1. `AbstractClass`'s own constructors

`AbstractClass` has four vftables (`0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`; primary `0x7E1F50`). Exactly **5** function bodies in `.text` install three or more of them:

### `0x00410170`

```
00410170  mov     eax, ecx
00410172  xor     ecx, ecx
00410174  mov     dword ptr [eax + 8], 0x7e1fbc
0041017B  mov     dword ptr [eax + 0xc], 0x7e1fb4
00410182  mov     dword ptr [eax + 0x18], ecx
00410185  mov     dword ptr [eax + 0x1c], ecx
00410188  mov     byte ptr [eax + 0x20], cl
0041018B  mov     cl, byte ptr [eax + 0x14]
0041018E  and     cl, 0xf8
00410191  mov     dword ptr [eax + 0x10], 0xffffffff
00410198  mov     dword ptr [eax], 0x7e1f50
0041019E  mov     dword ptr [eax + 4], 0x7e1f34
004101A5  mov     dword ptr [eax + 8], 0x7e1f2c
004101AC  mov     dword ptr [eax + 0xc], 0x7e1f24
004101B3  mov     byte ptr [eax + 0x14], cl
004101B6  ret     
```

- installs: `0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`
- inlined `AddItem`/`RemoveItem` on `0xB0F720`: **none**
- direct `call`ers in `.text`: **45**

### `0x004101C0`

```
004101C0  mov     eax, ecx
004101C2  mov     dword ptr [eax + 8], 0x7e1fbc
004101C9  mov     dword ptr [eax + 0xc], 0x7e1fb4
004101D0  mov     dword ptr [eax], 0x7e1f50
004101D6  mov     dword ptr [eax + 4], 0x7e1f34
004101DD  mov     dword ptr [eax + 8], 0x7e1f2c
004101E4  mov     dword ptr [eax + 0xc], 0x7e1f24
004101EB  ret     4
```

- installs: `0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`
- inlined `AddItem`/`RemoveItem` on `0xB0F720`: **none**
- direct `call`ers in `.text`: **44**

### `0x004101F0`

```
004101F0  mov     dword ptr [ecx], 0x7e1f50
004101F6  mov     dword ptr [ecx + 4], 0x7e1f34
004101FD  mov     dword ptr [ecx + 8], 0x7e1f2c
00410204  mov     dword ptr [ecx + 0xc], 0x7e1f24
0041020B  ret     
```

- installs: `0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`
- inlined `AddItem`/`RemoveItem` on `0xB0F720`: **none**
- direct `call`ers in `.text`: **47**

### `0x004105A0`

```
004105A0  mov     al, byte ptr [esp + 4]
004105A4  push    esi
004105A5  mov     esi, ecx
004105A7  test    al, 1
004105A9  mov     dword ptr [esi], 0x7e1f50
004105AF  mov     dword ptr [esi + 4], 0x7e1f34
004105B6  mov     dword ptr [esi + 8], 0x7e1f2c
004105BD  mov     dword ptr [esi + 0xc], 0x7e1f24
004105C4  je      0x4105cf
004105C6  push    esi
004105C7  call    0x7c8b3d
004105CC  add     esp, 4
004105CF  mov     eax, esi
004105D1  pop     esi
004105D2  ret     4
```

- installs: `0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`
- inlined `AddItem`/`RemoveItem` on `0xB0F720`: **none**
- direct `call`ers in `.text`: **0**

### `0x006E8000`

```
006E8000  mov     edx, dword ptr [esp + 4]
006E8004  mov     eax, ecx
006E8006  push    esi
006E8007  push    edi
006E8008  mov     dword ptr [eax + 8], 0x7e1fbc
006E800F  mov     dword ptr [eax + 0xc], 0x7e1fb4
006E8016  mov     ecx, dword ptr [edx + 0x10]
006E8019  lea     esi, [edx + 0x24]
006E801C  mov     dword ptr [eax + 0x10], ecx
006E801F  mov     cl, byte ptr [edx + 0x14]
006E8022  mov     byte ptr [eax + 0x14], cl
006E8025  mov     ecx, dword ptr [edx + 0x18]
006E8028  mov     dword ptr [eax + 0x18], ecx
006E802B  mov     ecx, dword ptr [edx + 0x1c]
006E802E  mov     dword ptr [eax + 0x1c], ecx
006E8031  mov     cl, byte ptr [edx + 0x20]
006E8034  mov     byte ptr [eax + 0x20], cl
006E8037  lea     edi, [eax + 0x24]
006E803A  mov     ecx, 6
006E803F  mov     dword ptr [eax], 0x7e1f50
006E8045  mov     dword ptr [eax + 4], 0x7e1f34
006E804C  mov     dword ptr [eax + 8], 0x7e1f2c
006E8053  mov     dword ptr [eax + 0xc], 0x7e1f24
006E805A  rep movsd dword ptr es:[edi], dword ptr [esi]
```

- installs: `0x7E1F24`, `0x7E1F2C`, `0x7E1F34`, `0x7E1F50`
- inlined `AddItem`/`RemoveItem` on `0xB0F720`: **none**
- direct `call`ers in `.text`: **1**

## 2. Is the registration in the root ctor?

**No.** None of the 5 `AbstractClass` constructor bodies encodes a single occurrence of `0xB0F720`, `0xB0F724`, `0xB0F728`, `0xB0F730` or `0xB0F734`. Each body is short enough to show in full above; the longest (`0x006E8000`, a copy-constructor form) only copies `+0x10`, `+0x14`, `+0x18`, `+0x1C`, `+0x20` and 24 bytes of payload. `[已证]`

Consequence: constructing a derived object runs only the base initialisation; the object is **not** put into `0xB0F720` by the base. Registration is therefore the responsibility of each concrete (leaf or intermediate) constructor — it is *not* automatic. `[已证]`

## 3. Where registration actually happens

The registry `AddItem` is inlined **into a per-class constructor**, and the matching `RemoveItem` into the per-class destructor (or, for a class with several constructors, into one of them). The table is generated from the `[Count]` stores found in each function; `inc`/`dec` decides the direction.

| function | class | AddItem (+1) store | RemoveItem (−1) store |
|---|---|---|---|
| `0x00420960` | `AlphaShapeClass` | `0x00420A62` | — |
| `0x00420AF0` | `AlphaShapeClass` | `0x00420BBF` | — |
| `0x00421730` | `AlphaShapeClass` | — | `0x004217C1` |
| `0x004C98B0` | `FactoryClass` | `0x004C99EC` | — |
| `0x004CA770` | `FactoryClass` | — | `0x004CA818` |
| `0x004F54A0` | `HouseClass` | `0x004F5FF5` | — |
| `0x005F3900` | `ObjectClass` | `0x005F3A7F` | — |
| `0x005F3B80` | `ObjectClass` | — | `0x005F3C66` |
| `0x0062DC50` | `ParticleSystemClass` | `0x0062DEF6` | — |
| `0x0062DF20` | `ParticleSystemClass` | `0x0062E05B` | — |
| `0x0062E070` | `ParticleSystemClass` | — | `0x0062E21E` |
| `0x006E8A90` | `TeamClass` | `0x006E8C87` | — |
| `0x006E8DE0` | `TeamClass` | — | `0x006E8F2D` |

## 4. The asymmetry that settles it

### 4a. A construction path that only ever removes

`0x00421730` is an `AlphaShapeClass` constructor form. It installs all four `AlphaShapeClass` vtables, performs the full field initialisation, then runs an inlined `RemoveItem` on `0xB0F720` (`dec ecx` @`0x4217BE`, `mov [0xB0F730], ecx` @`0x4217C1`), calls `0x4101F0`, and returns. It contains **no** `AddItem`. `[已证]`

So there is at least one constructor body whose net effect on the registry is −1. Construction and registration are therefore not coupled: whether an object appears in the array depends on *which* constructor form the caller picked, not on the object's type. `[已证]`

### 4b. A class with two constructors and one destructor

`AlphaShapeClass` has `AddItem` in `0x00420960` and in `0x00420AF0`, but `RemoveItem` in `0x00421730`. A balanced pair exists only if every construction goes through the two adding forms and every destruction through the removing one; `0x00421730` demonstrates a construction form that removes. `[已证]`

## 5. What this means for completeness

Because the base ctor is registry-free, completeness requires **every** concrete constructor of **every** `AbstractClass`-derived class to inline the `AddItem`. Observations:

- functions with an `AddItem` on `0xB0F720`: **8**
- functions with a `RemoveItem` on `0xB0F720`: **5**
- classes attributed to a function that actually mutates the registry: **6** (`AlphaShapeClass`, `FactoryClass`, `HouseClass`, `ObjectClass`, `ParticleSystemClass`, `TeamClass`)
- classes in the `AbstractClass` heritage with **zero** registry mutation found (`class_atlas_v2.tsv` primary vtable present, no `AddItem`/`RemoveItem` in the function that installs it): `TechnoClass`
- `AbstractClass`-derived classes the engine defines: several hundred (`class_atlas_v2.tsv` enumerates them). `[已证]` for the enumeration, `[未证]` for the exact count of constructor bodies.

This is a sampled result: 8 of 23 attributed push sites is nowhere near enough insertion points to cover every leaf class in the engine, which is itself the argument — see `report.md`. `[已证]` for the counts, `[未证]` for the claim that no unscanned constructor adds.


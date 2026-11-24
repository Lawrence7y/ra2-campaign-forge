0055CFD0  a184eda800             mov eax, dword ptr [0xa8ed84]
0055CFD5  83ec7c                 sub esp, 0x7c
0055CFD8  a9ff030000             test eax, 0x3ff
0055CFDD  53                     push ebx
0055CFDE  56                     push esi
0055CFDF  eb78                   jmp 0x55d059
0055CFE1  e8ba27f4ff             call 0x49f7a0
0055CFE6  84c0                   test al, al
0055CFE8  756f                   jne 0x55d059
0055CFEA  a14c3da800             mov eax, dword ptr [0xa83d4c]
0055CFEF  6a08                   push 8
0055CFF1  8b4830                 mov ecx, dword ptr [eax + 0x30]
0055CFF4  51                     push ecx
0055CFF5  8d4c241c               lea ecx, [esp + 0x1c]
0055CFF9  e8c296f6ff             call 0x4c66c0
0055CFFE  813dc802a80080000000   cmp dword ptr [0xa802c8], 0x80
0055D008  7d4f                   jge 0x55d059
0055D00A  8b0dd002a800           mov ecx, dword ptr [0xa802d0]
0055D010  57                     push edi
0055D011  8bf0                   mov esi, eax
0055D013  8d14c9                 lea edx, [ecx + ecx*8]
0055D016  8d0c91                 lea ecx, [ecx + edx*4]
0055D019  8dbc49d402a800         lea edi, [ecx + ecx*2 + 0xa802d4]
0055D020  b91b000000             mov ecx, 0x1b
0055D025  f3a5                   rep movsd dword ptr es:[edi], dword ptr [esi]
0055D027  66a5                   movsw word ptr es:[edi], word ptr [esi]
0055D029  a4                     movsb byte ptr es:[edi], byte ptr [esi]
0055D02A  ff1530157e00           call dword ptr [0x7e1530]
0055D030  8b0dd002a800           mov ecx, dword ptr [0xa802d0]
0055D036  5f                     pop edi
0055D037  89048d543aa800         mov dword ptr [ecx*4 + 0xa83a54], eax
0055D03E  8b15d002a800           mov edx, dword ptr [0xa802d0]
0055D044  a1c802a800             mov eax, dword ptr [0xa802c8]
0055D049  42                     inc edx
0055D04A  83e27f                 and edx, 0x7f
0055D04D  40                     inc eax
0055D04E  8915d002a800           mov dword ptr [0xa802d0], edx
0055D054  a3c802a800             mov dword ptr [0xa802c8], eax
0055D059  a0493da800             mov al, byte ptr [0xa83d49]
0055D05E  33db                   xor ebx, ebx
0055D060  3ac3                   cmp al, bl
0055D062  751c                   jne 0x55d080
0055D064  381dd0eca800           cmp byte ptr [0xa8ecd0], bl
0055D06A  7514                   jne 0x55d080
0055D06C  381dc0418b00           cmp byte ptr [0x8b41c0], bl
0055D072  750c                   jne 0x55d080
0055D074  381d483da800           cmp byte ptr [0xa83d48], bl
0055D07A  0f84c7020000           je 0x55d347
0055D080  ff05b4daa800           inc dword ptr [0xa8dab4]
0055D086  e8b5711200             call 0x684240
0055D08B  a0493da800             mov al, byte ptr [0xa83d49]
0055D090  3ac3                   cmp al, bl
0055D092  750c                   jne 0x55d0a0
0055D094  381dd0eca800           cmp byte ptr [0xa8ecd0], bl
0055D09A  0f846c010000           je 0x55d20c
0055D0A0  8b0d68738800           mov ecx, dword ptr [0x887368]
0055D0A6  3bcb                   cmp ecx, ebx
0055D0A8  740b                   je 0x55d0b5
0055D0AA  53                     push ebx
0055D0AB  e8f0701c00             call 0x7241a0
0055D0B0  a0493da800             mov al, byte ptr [0xa83d49]
0055D0B5  3ac3                   cmp al, bl
0055D0B7  750c                   jne 0x55d0c5
0055D0B9  381dd0eca800           cmp byte ptr [0xa8ecd0], bl
0055D0BF  0f8447010000           je 0x55d20c
0055D0C5  8b0d3cb2a800           mov ecx, dword ptr [0xa8b23c]
0055D0CB  8b1538b2a800           mov edx, dword ptr [0xa8b238]
0055D0D1  3bcb                   cmp ecx, ebx
0055D0D3  741e                   je 0x55d0f3
0055D0D5  83fa03                 cmp edx, 3
0055D0D8  7405                   je 0x55d0df
0055D0DA  83fa04                 cmp edx, 4
0055D0DD  7514                   jne 0x55d0f3
0055D0DF  8b11                   mov edx, dword ptr [ecx]
0055D0E1  50                     push eax
0055D0E2  ff92a0000000           call dword ptr [edx + 0xa0]
0055D0E8  a0493da800             mov al, byte ptr [0xa83d49]
0055D0ED  8b1538b2a800           mov edx, dword ptr [0xa8b238]
0055D0F3  3ac3                   cmp al, bl
0055D0F5  0f8482000000           je 0x55d17d
0055D0FB  83fa04                 cmp edx, 4
0055D0FE  7523                   jne 0x55d123
0055D100  381d00f9a800           cmp byte ptr [0xa8f900], bl
0055D106  751b                   jne 0x55d123
0055D108  391dc479b700           cmp dword ptr [0xb779c4], ebx
0055D10E  7407                   je 0x55d117
0055D110  c605c1b8a80001         mov byte ptr [0xa8b8c1], 1
0055D117  e804b71600             call 0x6c8820
0055D11C  32c9                   xor cl, cl
0055D11E  e82d9e1600             call 0x6c6f50
0055D123  881dd0eca800           mov byte ptr [0xa8ecd0], bl
0055D129  881d493da800           mov byte ptr [0xa83d49], bl
0055D12F  881dc0418b00           mov byte ptr [0x8b41c0], bl
0055D135  881d483da800           mov byte ptr [0xa83d48], bl
0055D13B  e8700e1d00             call 0x72dfb0
0055D140  b938b2a800             mov ecx, 0xa8b238
0055D145  e8f6e91300             call 0x69bb40
0055D14A  e821851200             call 0x685670
0055D14F  b938b2a800             mov ecx, 0xa8b238
0055D154  e857e91300             call 0x69bab0
0055D159  8b0d68738800           mov ecx, dword ptr [0x887368]
0055D15F  881d58cdab00           mov byte ptr [0xabcd58], bl
0055D165  3bcb                   cmp ecx, ebx
0055D167  0f84d4010000           je 0x55d341
0055D16D  a080eba800             mov al, byte ptr [0xa8eb80]
0055D172  50                     push eax
0055D173  e828701c00             call 0x7241a0
0055D178  e9c4010000             jmp 0x55d341
0055D17D  381dd0eca800           cmp byte ptr [0xa8ecd0], bl
0055D183  0f8483000000           je 0x55d20c
0055D189  83fa04                 cmp edx, 4
0055D18C  7523                   jne 0x55d1b1
0055D18E  381d00f9a800           cmp byte ptr [0xa8f900], bl
0055D194  751b                   jne 0x55d1b1
0055D196  391dc479b700           cmp dword ptr [0xb779c4], ebx
0055D19C  7407                   je 0x55d1a5
0055D19E  c605c1b8a80001         mov byte ptr [0xa8b8c1], 1
0055D1A5  e876b61600             call 0x6c8820
0055D1AA  32c9                   xor cl, cl
0055D1AC  e89f9d1600             call 0x6c6f50
0055D1B1  881d493da800           mov byte ptr [0xa83d49], bl
0055D1B7  881dd0eca800           mov byte ptr [0xa8ecd0], bl
0055D1BD  881dc0418b00           mov byte ptr [0x8b41c0], bl
0055D1C3  881d483da800           mov byte ptr [0xa83d48], bl
0055D1C9  e8e20d1d00             call 0x72dfb0
0055D1CE  b938b2a800             mov ecx, 0xa8b238
0055D1D3  e868e91300             call 0x69bb40
0055D1D8  e8e38b1200             call 0x685dc0
0055D1DD  b938b2a800             mov ecx, 0xa8b238
0055D1E2  e8c9e81300             call 0x69bab0
0055D1E7  8b0d68738800           mov ecx, dword ptr [0x887368]
0055D1ED  881d58cdab00           mov byte ptr [0xabcd58], bl
0055D1F3  3bcb                   cmp ecx, ebx
0055D1F5  0f8446010000           je 0x55d341
0055D1FB  8a1580eba800           mov dl, byte ptr [0xa8eb80]
0055D201  52                     push edx
0055D202  e8996f1c00             call 0x7241a0
0055D207  e935010000             jmp 0x55d341
0055D20C  381dc0418b00           cmp byte ptr [0x8b41c0], bl
0055D212  743c                   je 0x55d250
0055D214  b938b2a800             mov ecx, 0xa8b238
0055D219  881d493da800           mov byte ptr [0xa83d49], bl
0055D21F  881dd0eca800           mov byte ptr [0xa8ecd0], bl
0055D225  881dc0418b00           mov byte ptr [0x8b41c0], bl
0055D22B  881d483da800           mov byte ptr [0xa83d48], bl
0055D231  e80ae91300             call 0x69bb40
0055D236  e8a5911200             call 0x6863e0
0055D23B  b938b2a800             mov ecx, 0xa8b238
0055D240  e86be81300             call 0x69bab0
0055D245  881d58cdab00           mov byte ptr [0xabcd58], bl
0055D24B  e9f1000000             jmp 0x55d341
0055D250  381d483da800           cmp byte ptr [0xa83d48], bl
0055D256  0f84e5000000           je 0x55d341
0055D25C  881d493da800           mov byte ptr [0xa83d49], bl
0055D262  881dd0eca800           mov byte ptr [0xa8ecd0], bl
0055D268  881dc0418b00           mov byte ptr [0x8b41c0], bl
0055D26E  881d483da800           mov byte ptr [0xa83d48], bl
0055D274  e8370d1d00             call 0x72dfb0
0055D279  b938b2a800             mov ecx, 0xa8b238
0055D27E  e8bde81300             call 0x69bb40
0055D283  e8e8921200             call 0x686570
0055D288  b938b2a800             mov ecx, 0xa8b238
0055D28D  e81ee81300             call 0x69bab0
0055D292  881d58cdab00           mov byte ptr [0xabcd58], bl
0055D298  6844a08200             push 0x82a044
0055D29D  e83e96eaff             call 0x4068e0
0055D2A2  a138b2a800             mov eax, dword ptr [0xa8b238]
0055D2A7  83c404                 add esp, 4
0055D2AA  83f804                 cmp eax, 4
0055D2AD  0f858e000000           jne 0x55d341
0055D2B3  391d28768800           cmp dword ptr [0x887628], ebx
0055D2B9  0f8482000000           je 0x55d341
0055D2BF  381da0dba800           cmp byte ptr [0xa8dba0], bl
0055D2C5  747a                   je 0x55d341
0055D2C7  391d0ceaa800           cmp dword ptr [0xa8ea0c], ebx
0055D2CD  745a                   je 0x55d329
0055D2CF  b9d052b000             mov ecx, 0xb052d0
0055D2D4  e857721000             call 0x664530
0055D2D9  8d4c240c               lea ecx, [esp + 0xc]
0055D2DD  e85eb91600             call 0x6c8c40
0055D2E2  bee0010000             mov esi, 0x1e0
0055D2E7  89442408               mov dword ptr [esp + 8], eax
0055D2EB  89742410               mov dword ptr [esp + 0x10], esi
0055D2EF  eb04                   jmp 0x55d2f5
0055D2F1  8b742410               mov esi, dword ptr [esp + 0x10]
0055D2F5  837c2408ff             cmp dword ptr [esp + 8], -1
0055D2FA  7413                   je 0x55d30f
0055D2FC  8d4c240c               lea ecx, [esp + 0xc]
0055D300  e83bb91600             call 0x6c8c40
0055D305  2b442408               sub eax, dword ptr [esp + 8]
0055D309  3bc6                   cmp eax, esi
0055D30B  7d1c                   jge 0x55d329
0055D30D  2bf0                   sub esi, eax
0055D30F  3bf3                   cmp esi, ebx
0055D311  7416                   je 0x55d329
0055D313  e868fdf2ff             call 0x48d080
0055D318  b9d052b000             mov ecx, 0xb052d0
0055D31D  53                     push ebx
0055D31E  6a0a                   push 0xa
0055D320  e8eb721000             call 0x664610
0055D325  84c0                   test al, al
0055D327  74c8                   je 0x55d2f1
0055D329  8b0d3cb2a800           mov ecx, dword ptr [0xa8b23c]
0055D32F  3bcb                   cmp ecx, ebx
0055D331  7409                   je 0x55d33c
0055D333  8b01                   mov eax, dword ptr [ecx]
0055D335  ff5008                 call dword ptr [eax + 8]
0055D338  84c0                   test al, al
0055D33A  7505                   jne 0x55d341
0055D33C  e85f500f00             call 0x6523a0
0055D341  ff0db4daa800           dec dword ptr [0xa8dab4]
0055D347  8a0da0e9a800           mov cl, byte ptr [0xa8e9a0]
0055D34D  33c0                   xor eax, eax
0055D34F  3acb                   cmp cl, bl
0055D351  5e                     pop esi
0055D352  0f94c0                 sete al
0055D355  5b                     pop ebx
0055D356  83c47c                 add esp, 0x7c
0055D359  c3                     ret 
0055D35A  90                     nop 
0055D35B  90                     nop 
0055D35C  90                     nop 
0055D35D  90                     nop 
0055D35E  90                     nop 
0055D35F  90                     nop 

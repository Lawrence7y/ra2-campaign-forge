0048C8B0  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C8B5  81ec58010000         sub esp, 0x158
0048C8BB  55                   push ebp
0048C8BC  33ed                 xor ebp, ebp
0048C8BE  3bc5                 cmp eax, ebp
0048C8C0  0f84b4030000         je 0x48cc7a
0048C8C6  392d38b2a800         cmp dword ptr [0xa8b238], ebp
0048C8CC  744a                 je 0x48c918
0048C8CE  a14c3da800           mov eax, dword ptr [0xa83d4c]
0048C8D3  8a88f8010000         mov cl, byte ptr [eax + 0x1f8]
0048C8D9  84c9                 test cl, cl
0048C8DB  0f85a9000000         jne 0x48c98a
0048C8E1  8a88f7010000         mov cl, byte ptr [eax + 0x1f7]
0048C8E7  84c9                 test cl, cl
0048C8E9  0f859b000000         jne 0x48c98a
0048C8EF  8a88f6010000         mov cl, byte ptr [eax + 0x1f6]
0048C8F5  84c9                 test cl, cl
0048C8F7  0f858d000000         jne 0x48c98a
0048C8FD  8a0dfc2c8200         mov cl, byte ptr [0x822cfc]
0048C903  84c9                 test cl, cl
0048C905  7511                 jne 0x48c918
0048C907  8a88f5010000         mov cl, byte ptr [eax + 0x1f5]
0048C90D  84c9                 test cl, cl
0048C90F  7479                 je 0x48c98a
0048C911  c605fc2c820001       mov byte ptr [0x822cfc], 1
0048C918  e893751f00           call 0x683eb0
0048C91D  8b0d40768800         mov ecx, dword ptr [0x887640]
0048C923  8b01                 mov eax, dword ptr [ecx]
0048C925  ff5014               call dword ptr [eax + 0x14]
0048C928  8b0d40768800         mov ecx, dword ptr [0x887640]
0048C92E  8b11                 mov edx, dword ptr [ecx]
0048C930  ff5228               call dword ptr [edx + 0x28]
0048C933  85c0                 test eax, eax
0048C935  741a                 je 0x48c951
0048C937  8b0d40768800         mov ecx, dword ptr [0x887640]
0048C93D  8b01                 mov eax, dword ptr [ecx]
0048C93F  ff5010               call dword ptr [eax + 0x10]
0048C942  8b0d40768800         mov ecx, dword ptr [0x887640]
0048C948  8b11                 mov edx, dword ptr [ecx]
0048C94A  ff5228               call dword ptr [edx + 0x28]
0048C94D  85c0                 test eax, eax
0048C94F  75e6                 jne 0x48c937
0048C951  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C956  56                   push esi
0048C957  3bc5                 cmp eax, ebp
0048C959  57                   push edi
0048C95A  0f84d7020000         je 0x48cc37
0048C960  8d48ff               lea ecx, [eax - 1]
0048C963  83f908               cmp ecx, 8
0048C966  7748                 ja 0x48c9b0
0048C968  ff248d84cc4800       jmp dword ptr [ecx*4 + 0x48cc84]
0048C96F  8b0d30b2a800         mov ecx, dword ptr [0xa8b230]
0048C975  e8a62b1d00           call 0x65f520
0048C97A  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C97F  83f809               cmp eax, 9
0048C982  0f84a9020000         je 0x48cc31
0048C988  eb26                 jmp 0x48c9b0
0048C98A  892da0eda800         mov dword ptr [0xa8eda0], ebp
0048C990  5d                   pop ebp
0048C991  81c458010000         add esp, 0x158
0048C997  c3                   ret 
0048C998  b9e8f78700           mov ecx, 0x87f7e8
0048C99D  e82ebd1c00           call 0x6586d0
0048C9A2  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C9A7  83f808               cmp eax, 8
0048C9AA  0f8481020000         je 0x48cc31
0048C9B0  3bc5                 cmp eax, ebp
0048C9B2  0f847f020000         je 0x48cc37
0048C9B8  eba6                 jmp 0x48c960
0048C9BA  e821470600           call 0x4f10e0
0048C9BF  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C9C4  83f801               cmp eax, 1
0048C9C7  ebe1                 jmp 0x48c9aa
0048C9C9  8d4c2410             lea ecx, [esp + 0x10]
0048C9CD  e82e530500           call 0x4e1d00
0048C9D2  a1a0eda800           mov eax, dword ptr [0xa8eda0]
0048C9D7  83f805               cmp eax, 5
0048C9DA  75d4                 jne 0x48c9b0
0048C9DC  b801000000           mov eax, 1
0048C9E1  a3a0eda800           mov dword ptr [0xa8eda0], eax
0048C9E6  e975ffffff           jmp 0x48c960
0048C9EB  8d4c240f             lea ecx, [esp + 0xf]
0048C9EF  e83c982200           call 0x6b6230
0048C9F4  b805000000           mov eax, 5
0048C9F9  a3a0eda800           mov dword ptr [0xa8eda0], eax
0048C9FE  e95dffffff           jmp 0x48c960
0048CA03  b960eba800           mov ecx, 0xa8eb60
0048CA08  e8e3f41600           call 0x5fbef0
0048CA0D  b805000000           mov eax, 5
0048CA12  a3a0eda800           mov dword ptr [0xa8eda0], eax
0048CA17  e944ffffff           jmp 0x48c960
0048CA1C  e81f4e0600           call 0x4f1840
0048CA21  83c0fe               add eax, -2
0048CA24  83f803               cmp eax, 3
0048CA27  0f8704020000         ja 0x48cc31
0048CA2D  ff2485a8cc4800       jmp dword ptr [eax*4 + 0x48cca8]
0048CA34  a14c3da800           mov eax, dword ptr [0xa83d4c]
0048CA39  6a08                 push 8
0048CA3B  8b4830               mov ecx, dword ptr [eax + 0x30]
0048CA3E  51                   push ecx
0048CA3F  8d4c241c             lea ecx, [esp + 0x1c]
0048CA43  e8789c0300           call 0x4c66c0
0048CA48  813dc802a80080000000 cmp dword ptr [0xa802c8], 0x80
0048CA52  7d4d                 jge 0x48caa1
0048CA54  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CA5A  8bf0                 mov esi, eax
0048CA5C  8d14c9               lea edx, [ecx + ecx*8]
0048CA5F  8d0c91               lea ecx, [ecx + edx*4]
0048CA62  8dbc49d402a800       lea edi, [ecx + ecx*2 + 0xa802d4]
0048CA69  b91b000000           mov ecx, 0x1b
0048CA6E  f3a5                 rep movsd dword ptr es:[edi], dword ptr [esi]
0048CA70  66a5                 movsw word ptr es:[edi], word ptr [esi]
0048CA72  a4                   movsb byte ptr es:[edi], byte ptr [esi]
0048CA73  ff1530157e00         call dword ptr [0x7e1530]
0048CA79  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CA7F  89048d543aa800       mov dword ptr [ecx*4 + 0xa83a54], eax
0048CA86  8b15d002a800         mov edx, dword ptr [0xa802d0]
0048CA8C  a1c802a800           mov eax, dword ptr [0xa802c8]
0048CA91  42                   inc edx
0048CA92  83e27f               and edx, 0x7f
0048CA95  40                   inc eax
0048CA96  8915d002a800         mov dword ptr [0xa802d0], edx
0048CA9C  a3c802a800           mov dword ptr [0xa802c8], eax
0048CAA1  c605fc2c820000       mov byte ptr [0x822cfc], 0
0048CAA8  e8f3a61b00           call 0x6471a0
0048CAAD  e97f010000           jmp 0x48cc31
0048CAB2  a14c3da800           mov eax, dword ptr [0xa83d4c]
0048CAB7  6a08                 push 8
0048CAB9  8b4830               mov ecx, dword ptr [eax + 0x30]
0048CABC  51                   push ecx
0048CABD  8d8c248c000000       lea ecx, [esp + 0x8c]
0048CAC4  e8f79b0300           call 0x4c66c0
0048CAC9  813dc802a80080000000 cmp dword ptr [0xa802c8], 0x80
0048CAD3  7d4d                 jge 0x48cb22
0048CAD5  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CADB  8bf0                 mov esi, eax
0048CADD  8d14c9               lea edx, [ecx + ecx*8]
0048CAE0  8d0c91               lea ecx, [ecx + edx*4]
0048CAE3  8dbc49d402a800       lea edi, [ecx + ecx*2 + 0xa802d4]
0048CAEA  b91b000000           mov ecx, 0x1b
0048CAEF  f3a5                 rep movsd dword ptr es:[edi], dword ptr [esi]
0048CAF1  66a5                 movsw word ptr es:[edi], word ptr [esi]
0048CAF3  a4                   movsb byte ptr es:[edi], byte ptr [esi]
0048CAF4  ff1530157e00         call dword ptr [0x7e1530]
0048CAFA  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CB00  89048d543aa800       mov dword ptr [ecx*4 + 0xa83a54], eax
0048CB07  8b15d002a800         mov edx, dword ptr [0xa802d0]
0048CB0D  a1c802a800           mov eax, dword ptr [0xa802c8]
0048CB12  42                   inc edx
0048CB13  83e27f               and edx, 0x7f
0048CB16  40                   inc eax
0048CB17  8915d002a800         mov dword ptr [0xa802d0], edx
0048CB1D  a3c802a800           mov dword ptr [0xa802c8], eax
0048CB22  c605fc2c820000       mov byte ptr [0x822cfc], 0
0048CB29  e903010000           jmp 0x48cc31
0048CB2E  c605c0418b0001       mov byte ptr [0x8b41c0], 1
0048CB35  e9f7000000           jmp 0x48cc31
0048CB3A  392dc810ac00         cmp dword ptr [0xac10c8], ebp
0048CB40  740a                 je 0x48cb4c
0048CB42  e859a61b00           call 0x6471a0
0048CB47  e9e5000000           jmp 0x48cc31
0048CB4C  a14c3da800           mov eax, dword ptr [0xa83d4c]
0048CB51  8a88f5010000         mov cl, byte ptr [eax + 0x1f5]
0048CB57  84c9                 test cl, cl
0048CB59  0f85d2000000         jne 0x48cc31
0048CB5F  8a88f7010000         mov cl, byte ptr [eax + 0x1f7]
0048CB65  84c9                 test cl, cl
0048CB67  0f85c4000000         jne 0x48cc31
0048CB6D  8a88f8010000         mov cl, byte ptr [eax + 0x1f8]
0048CB73  84c9                 test cl, cl
0048CB75  0f85b6000000         jne 0x48cc31
0048CB7B  8a88f6010000         mov cl, byte ptr [eax + 0x1f6]
0048CB81  84c9                 test cl, cl
0048CB83  0f85a8000000         jne 0x48cc31
0048CB89  68e7010000           push 0x1e7
0048CB8E  68f8d48100           push 0x81d4f8
0048CB93  33d2                 xor edx, edx
0048CB95  b9e8d48100           mov ecx, 0x81d4e8
0048CB9A  e8c1822a00           call 0x734e60
0048CB9F  8bc8                 mov ecx, eax
0048CBA1  e82a951300           call 0x5c60d0
0048CBA6  85c0                 test eax, eax
0048CBA8  0f8483000000         je 0x48cc31
0048CBAE  a14c3da800           mov eax, dword ptr [0xa83d4c]
0048CBB3  6a08                 push 8
0048CBB5  8b4830               mov ecx, dword ptr [eax + 0x30]
0048CBB8  51                   push ecx
0048CBB9  8d8c24fc000000       lea ecx, [esp + 0xfc]
0048CBC0  e8fb9a0300           call 0x4c66c0
0048CBC5  813dc802a80080000000 cmp dword ptr [0xa802c8], 0x80
0048CBCF  7d4d                 jge 0x48cc1e
0048CBD1  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CBD7  8bf0                 mov esi, eax
0048CBD9  8d14c9               lea edx, [ecx + ecx*8]
0048CBDC  8d0c91               lea ecx, [ecx + edx*4]
0048CBDF  8dbc49d402a800       lea edi, [ecx + ecx*2 + 0xa802d4]
0048CBE6  b91b000000           mov ecx, 0x1b
0048CBEB  f3a5                 rep movsd dword ptr es:[edi], dword ptr [esi]
0048CBED  66a5                 movsw word ptr es:[edi], word ptr [esi]
0048CBEF  a4                   movsb byte ptr es:[edi], byte ptr [esi]
0048CBF0  ff1530157e00         call dword ptr [0x7e1530]
0048CBF6  8b0dd002a800         mov ecx, dword ptr [0xa802d0]
0048CBFC  89048d543aa800       mov dword ptr [ecx*4 + 0xa83a54], eax
0048CC03  8b15d002a800         mov edx, dword ptr [0xa802d0]
0048CC09  a1c802a800           mov eax, dword ptr [0xa802c8]
0048CC0E  42                   inc edx
0048CC0F  83e27f               and edx, 0x7f
0048CC12  40                   inc eax
0048CC13  8915d002a800         mov dword ptr [0xa802d0], edx
0048CC19  a3c802a800           mov dword ptr [0xa802c8], eax
0048CC1E  e87da51b00           call 0x6471a0
0048CC23  c605fc2c820000       mov byte ptr [0x822cfc], 0
0048CC2A  eb05                 jmp 0x48cc31
0048CC2C  e80f0c2f00           call 0x77d840
0048CC31  892da0eda800         mov dword ptr [0xa8eda0], ebp
0048CC37  a15035b700           mov eax, dword ptr [0xb73550]
0048CC3C  50                   push eax
0048CC3D  ff156c147e00         call dword ptr [0x7e146c]
0048CC43  8b0d30b2a800         mov ecx, dword ptr [0xa8b230]
0048CC49  5f                   pop edi
0048CC4A  5e                   pop esi
0048CC4B  8a81a2350000         mov al, byte ptr [ecx + 0x35a2]
0048CC51  84c0                 test al, al
0048CC53  740b                 je 0x48cc60
0048CC55  8b0d40768800         mov ecx, dword ptr [0x887640]
0048CC5B  8b11                 mov edx, dword ptr [ecx]
0048CC5D  ff520c               call dword ptr [edx + 0xc]
0048CC60  8b0d40768800         mov ecx, dword ptr [0x887640]
0048CC66  8b01                 mov eax, dword ptr [ecx]
0048CC68  ff5018               call dword ptr [eax + 0x18]
0048CC6B  b938b2a800           mov ecx, 0xa8b238
0048CC70  e83bee2000           call 0x69bab0
0048CC75  e836731f00           call 0x683fb0
0048CC7A  5d                   pop ebp
0048CC7B  81c458010000         add esp, 0x158
0048CC81  c3                   ret 
0048CC82  8bff                 mov edi, edi
0048CC84  bac948003a           mov edx, 0x3a0048c9
0048CC89  cb                   retf 
0048CC8A  48                   dec eax
0048CC8B  001cca               add byte ptr [edx + ecx*8], bl
0048CC8E  48                   dec eax
0048CC8F  0003                 add byte ptr [ebx], al
0048CC91  ca4800               retf 0x48
0048CC94  c9                   leave 
0048CC95  c9                   leave 
0048CC96  48                   dec eax
0048CC97  00eb                 add bl, ch
0048CC99  c9                   leave 
0048CC9A  48                   dec eax
0048CC9B  002ccc               add byte ptr [esp + ecx*8], ch
0048CC9E  48                   dec eax
0048CC9F  0098c948006f         add byte ptr [eax + 0x6f0048c9], bl
0048CCA5  c9                   leave 
0048CCA6  48                   dec eax
0048CCA7  00a8ca480034         add byte ptr [eax + 0x340048ca], ch
0048CCAD  ca4800               retf 0x48
0048CCB0  b2ca                 mov dl, 0xca
0048CCB2  48                   dec eax
0048CCB3  002e                 add byte ptr [esi], ch
0048CCB5  cb                   retf 
0048CCB6  48                   dec eax
0048CCB7  009090909090         add byte ptr [eax - 0x6f6f6f70], dl
0048CCBD  90                   nop 
0048CCBE  90                   nop 
0048CCBF  90                   nop 

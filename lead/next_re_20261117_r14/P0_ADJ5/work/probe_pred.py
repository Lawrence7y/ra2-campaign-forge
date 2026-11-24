#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigate predecessor bytes: does a HARD terminator end exactly at va, or is it only nop padding?"""
from engine import Bin
bin_=Bin()
addrs=[0x402F80,0x405AB0,0x40BDA0,0x40D260,0x411B00,0x412AE0,0x42E990,0x433560,0x407080,0x420130]
for va in addrs:
    b=bin_.read(va-20,20)
    print(f'{va:08X} bytes[va-20:va] =', ' '.join(f'{x:02X}' for x in b))

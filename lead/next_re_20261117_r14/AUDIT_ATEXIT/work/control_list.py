
# -*- coding: utf-8 -*-
"""Positive control: run the A/B/C/D classifier over the 26 entries already
adjudicated FAIL/降级 by a-S13-K12 (14) and a-S20-KPROVED (12). Expect B for all."""
import importlib.util, sys, os, json, pickle
OUT=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('az', os.path.join(OUT,'analyze_lib.py'))
S13_BLACK=[0x0040B740,0x0040B820,0x0040F680,0x0040F760,0x0040FC50,0x0040FD30,0x0046B6A0,
           0x0046B780,0x0054E930,0x0054E9E0,0x0062B110,0x0062B1F0,0x0065BF90,0x0065C070]
S13_WHITE=[0x0040F870,0x0054E890,0x0054EA70]
S20_DEMOTE=[0x0040EF60,0x0040F040,0x0053C560,0x00551370,0x00551450,0x00556F50,0x00557030,
            0x00422BE0,0x00423930,0x004253B0,0x00425530,0x004A7C10]
S20_PASS_EXACT=[0x0040F0A0,0x0040F150,0x0053C6A0,0x005514B0,0x00551560,0x00557090,0x00557140]

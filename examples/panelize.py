#!/usr/bin/env python

import sys, os
import gerberex
from gerberex import DxfFile, GerberComposition, DrillComposition

exts = ['GTL', 'GTO', 'GTP', 'GTS', 'GBL', 'GBO', 'GBP', 'GBS', 'TXT']
boards=[
    ('inputs/sonopi-digi.', 0, 0, 0),
    ('inputs/sonopi-digi.', 0, 22.5, 0),
    ('inputs/rcstick-f-small.', 0, 60, 0),
    ('inputs/rcstick-f-small.', 20, 60, 0),
    ('inputs/rcstick-f-small.', 40, 60, 0),
    ('inputs/rcstick-f.', 92.216, 55.238, 190),
    ('inputs/rcstick-jig.', 0, 44, 0),
    ('inputs/stm32breakout.', 78.0, 59.36, 90),
    ('inputs/stm32breakout.', 100.0, 59.36, 90),
]
outline =    'inputs/outline.dxf'
mousebites = 'inputs/mousebites.dxf'
fill =       'inputs/fill.dxf'
outputs =    'outputs/panelized'

os.chdir(os.path.dirname(__file__))
try:
    os.mkdir('outputs')
except FileExistsError:
    pass

def putstr(text):
    sys.stdout.write(text)
    sys.stdout.flush()

for ext in exts:
    putstr('merging %s: ' % ext)
    if ext == 'TXT':
        ctx = DrillComposition()
    else:
        ctx = GerberComposition()
    for path, x_offset, y_offset, theta in boards:
        file = gerberex.read(path + ext)
        file.to_metric()
        file.rotate(theta)
        file.offset(x_offset, y_offset)
        ctx.merge(file)
        putstr('.')
    if ext == 'TXT':
        file = gerberex.read(mousebites)
        file.draw_mode = DxfFile.DM_MOUSE_BITES
        file.width = 0.5
        file.format = (3, 3)
        ctx.merge(file)
    else:
        file = gerberex.read(outline)
        ctx.merge(file)
    ctx.dump(outputs + '.' + ext)
    putstr(' end\n')

putstr('generating GML: ')
file = gerberex.read(outline)
file.write(outputs + '.GML')
putstr('.')
ctx = GerberComposition()
file = gerberex.read(fill)
file.to_metric()
file.draw_mode = DxfFile.DM_FILL
ctx.merge(file)
ctx.dump(outputs + '-fill.GML')

putstr('. end\n')

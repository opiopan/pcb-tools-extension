#!/usr/bin/env python
import os
import gerberex
from gerberex.dxf import DxfFile

exts = ['GTL', 'GTO', 'GTP', 'GTS', 'GBL', 'GBO', 'GBP', 'GBS', 'TXT']
boards=[
    ('../../sonopi-digi/pcb/CAMOutputs/sonopi-digi.', 0, 0),
    ('../../sonopi-digi/pcb/CAMOutputs/sonopi-digi.', 0, 22.5),
    ('../../rcstick-f/pcb/small/CAMOutputs/rcstick-f-small.', 0, 60),
    ('../../rcstick-f/pcb/small/CAMOutputs/rcstick-f-small.', 20, 60),
    ('../../rcstick-f/pcb/small/CAMOutputs/rcstick-f-small.', 40, 60),
    ('../../rcstick-f/pcb/large/CAMOutputs/rcstick-f.', 72.4, 0),
    ('../../rcstick-f/pcb/jig/CAMOutputs/rcstick-jig.', 0, 44),
    ('../../stm32breakout/pcb/CAMOutputs/stm32breakout.', 78.0, 59.36),
    ('../../stm32breakout/pcb/CAMOutputs/stm32breakout.', 100.0, 59.36),
]
outline = 'outline.dxf'
fill = 'fill.dxf'

outputs = 'outputs/elecrow-panelized'

os.chdir(os.path.dirname(__file__))

for ext in exts:
    print('merging %s: ' % ext ,end='', flush=True)
    if ext == 'TXT':
        ctx = gerberex.DrillComposition()
    else:
        ctx = gerberex.GerberComposition()
    for board in boards:
        file = gerberex.read(board[0] + ext)
        file.to_metric()
        file.offset(board[1], board[2])
        ctx.merge(file)
        print('.', end='', flush=True)
    if ext != 'TXT':
        file = gerberex.read(outline)
        ctx.merge(file)
    ctx.dump(outputs + '.' + ext)
    print(' end', flush=True)

print('generating GML: ', end='', flush=True)
file = gerberex.read(outline)
file.write(outputs + '.GML')
print('.', end='', flush=True)
file = gerberex.read(fill)
file.to_metric()
file.draw_mode = DxfFile.DM_FILL
file.write(outputs + '-fill.GML')
print('. end', flush=True)

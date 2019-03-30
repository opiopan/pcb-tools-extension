import os
import gerberex
from gerberex.dxf import DxfFile
import gerber
from gerber.render.cairo_backend import GerberCairoContext

def merge():
    ctx = gerberex.GerberComposition()
    a = gerberex.read('test.GTL')
    a.to_metric()
    ctx.merge(a)

    b = gerberex.read('test.GTL')
    b.to_metric()
    b.offset(0, 25)
    ctx.merge(b)

    c = gerberex.read('test2.GTL')
    c.to_metric()
    c.offset(0, 60)
    ctx.merge(c)

    c = gerberex.read('test.GML')
    c.to_metric()
    ctx.merge(c)

    ctx.dump('test-merged.GTL')

def merge2():
    ctx = gerberex.DrillComposition()
    a = gerberex.read('test.TXT')
    a.to_metric()
    ctx.merge(a)

    b = gerberex.read('test.TXT')
    b.to_metric()
    b.offset(0, 25)
    ctx.merge(b)

    c = gerberex.read('test2.TXT')
    c.to_metric()
    c.offset(0, 60)
    ctx.merge(c)

    ctx.dump('test-merged.TXT')


os.chdir(os.path.dirname(__file__))

#merge2()

ctx = gerberex.DrillComposition()
base = gerberex.read('data/base.txt')
dxf = gerberex.read('data/mousebites.dxf')
dxf.draw_mode = DxfFile.DM_MOUSE_BITES
dxf.to_metric()
dxf.width = 0.5
ctx.merge(base)
ctx.merge(dxf)
ctx.dump('outputs/merged.txt')

dxf = gerberex.read('data/mousebite.dxf')
dxf.zero_suppression = 'leading'
dxf.write('outputs/a.gtl')
dxf.draw_mode = DxfFile.DM_MOUSE_BITES
dxf.width = 0.5
dxf.write('outputs/b.gml')
dxf.format = (3,3)
dxf.write('outputs/b.txt', filetype=DxfFile.FT_EXCELLON)
top = gerber.load_layer('outputs/a.gtl')
drill = gerber.load_layer('outputs/b.txt')
ctx = GerberCairoContext(scale=50)
ctx.render_layer(top)
ctx.render_layer(drill)
ctx.dump('outputs/b.png')

file = gerberex.read('data/test.GTL')
file.rotate(45)
file.write('outputs/test_changed.GTL')
file = gerberex.read('data/test.TXT')
file.rotate(45)
file.write('outputs/test_changed.TXT')

file = gerberex.read('data/outline.dxf')
file.to_metric()
w = file.width
file.draw_mode = DxfFile.DM_FILL
file.write('outline.GML')

copper = gerber.load_layer('test-merged.GTL')
ctx = GerberCairoContext(scale=10)
ctx.render_layer(copper)
outline = gerber.load_layer('test.GML')
outline.cam_source.to_metric()
ctx.render_layer(outline)
drill = gerber.load_layer('test-merged.TXT')
ctx.render_layer(drill)
ctx.dump('test.png')

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


#merge2()

file = gerberex.read('outline.dxf')
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

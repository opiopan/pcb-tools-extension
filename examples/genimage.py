#!/usr/bin/env python
import sys, os
from gerber import load_layer
from gerber.render import RenderSettings, theme
from gerber.render.cairo_backend import GerberCairoContext

os.chdir(os.path.dirname(__file__))

def putstr(text):
    sys.stdout.write(text)
    sys.stdout.flush()

putstr('loading ')
copper = load_layer('outputs/panelized.GTL')
putstr('.')
mask = load_layer('outputs/panelized.GTS')
putstr('.')
silk = load_layer('outputs/panelized.GTO')
putstr('.')
drill = load_layer('outputs/panelized.TXT')
putstr('.')
outline = load_layer('outputs/panelized-fill.GML')
putstr('. end\n')
 
putstr('drawing ')
ctx = GerberCairoContext(scale=20)
putstr('.')

metal_settings = RenderSettings(color=(30.0/255.0, 119.0/255.0, 93/255.0))
bg_settings = RenderSettings(color=(30.0/300.0, 110.0/300.0, 93/300.0))
ctx.render_layer(copper, settings=metal_settings, bgsettings=bg_settings)
putstr('.')

copper_settings = RenderSettings(color=(0.7*1.2, 0.5*1.2, 0.1*1.2))
ctx.render_layer(mask, settings=copper_settings)
putstr('.')

our_settings = RenderSettings(color=theme.COLORS['white'], alpha=0.80)
ctx.render_layer(silk, settings=our_settings)
putstr('.')

ctx.render_layer(outline)
putstr('.')
ctx.render_layer(drill)
putstr('. end\n')

putstr('dumping ... ')
ctx.dump('outputs/board-top.png')
putstr('end \n')

ctx.clear()
putstr('loading bottom ')
copper = load_layer('outputs/panelized.GBL')
putstr('.')
mask = load_layer('outputs/panelized.GBS')
putstr('.')
silk = load_layer('outputs/panelized.GBO')
putstr('. end\n')

putstr('drawing bottom ')
ctx.render_layer(copper, settings=metal_settings, bgsettings=bg_settings)
putstr('.')
ctx.render_layer(mask, settings=copper_settings)
putstr('.')
ctx.render_layer(silk, settings=our_settings)
putstr('.')
ctx.render_layer(outline)
putstr('.')
ctx.render_layer(drill)
putstr('. end\n')

putstr('dumping bottom ...')
ctx.dump('outputs/board-bottom.png')
putstr(' end\n')

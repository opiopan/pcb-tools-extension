#!/usr/bin/env python
from gerber import load_layer
from gerber.render import RenderSettings, theme
from gerber.render.cairo_backend import GerberCairoContext

print('loading ', end='', flush=True)
copper = load_layer('panelized.GTL')
print('.', end='', flush=True)
mask = load_layer('panelized.GTS')
print('.', end='', flush=True)
silk = load_layer('panelized.GTO')
print('.', end='', flush=True)
drill = load_layer('panelized.TXT')
print('.', end='', flush=True)
outline = load_layer('panelized-fill.GML')
print('.', end='', flush=True)
print('. end', flush=True)
 
print('panelizing ', end='', flush=True)
ctx = GerberCairoContext(scale=30)
print('.', end='', flush=True)
ctx.render_layer(copper)
print('.', end='', flush=True)
ctx.render_layer(mask)
print('.', end='', flush=True)

our_settings = RenderSettings(color=theme.COLORS['white'], alpha=0.85)
ctx.render_layer(silk, settings=our_settings)
print('.', end='', flush=True)

ctx.render_layer(outline)
print('.', end='', flush=True)
ctx.render_layer(drill)
print('.', end='', flush=True)
print('. end', flush=True)

print('dumping top...')
ctx.dump('panelized.png')

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import io
from math import pi, cos, sin, tan, atan, atan2, acos, asin, sqrt
from gerber.cam import CamFile, FileSettings
from gerber.utils import inch, metric, write_gerber_value
from gerber.gerber_statements import ADParamStmt
import dxfgrabber

class DxfStatement(object):
    def __init__(self, entity):
        self.entity = entity

    def to_gerber(self, settings=None):
        pass

    def to_inch(self):
        pass
    
    def to_metric(self):
        pass

class DxfLineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfLineStatement, self).__init__(entity)
    
    def to_gerber(self, settings=FileSettings):
        x0 = self.entity.start[0]
        y0 = self.entity.start[1]
        x1 = self.entity.end[0]
        y1 = self.entity.end[1]
        return 'G01*\nX{0}Y{1}D02*\nX{2}Y{3}D01*'.format(
            write_gerber_value(x0, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0, settings.format,
                               settings.zero_suppression),
            write_gerber_value(x1, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y1, settings.format,
                               settings.zero_suppression)
        )

    def to_inch(self):
        self.entity.start[idx] = (
            inch(self.entity.start[idx][0]), inch(self.entity.start[idx][1]))
        self.entity.end[idx] = (
            inch(self.entity.end[idx][0]), inch(self.entity.end[idx][1]))

    def to_metric(self):
        self.entity.start[idx] = (
            metric(self.entity.start[idx][0]), inch(self.entity.start[idx][1]))
        self.entity.end[idx] = (
            metric(self.entity.end[idx][0]), inch(self.entity.end[idx][1]))

class DxfCircleStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfCircleStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings):
        r = self.entity.radius
        x0 = self.entity.center[0]
        y0 = self.entity.center[1]
        return 'G01*\nX{0}Y{1}D02*\n' \
               'G75*\nG03*\nX{2}Y{3}I{4}J{5}D01*'.format(
            write_gerber_value(x0 + r, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0, settings.format,
                               settings.zero_suppression),

            write_gerber_value(x0 + r, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0, settings.format,
                               settings.zero_suppression),
            write_gerber_value(-r, settings.format,
                               settings.zero_suppression),
            write_gerber_value(0, settings.format,
                               settings.zero_suppression)
        )

    def to_inch(self):
        self.entity.radius = inch(self.entity.radius)
        self.entity.center[idx] = (
            inch(self.entity.center[idx][0]), inch(self.entity.center[idx][1]))

    def to_metric(self):
        self.entity.radius = metric(self.entity.radius)
        self.entity.center[idx] = (
            metric(self.entity.center[idx][0]), metric(self.entity.center[idx][1]))

class DxfArcStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfArcStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings):
        deg0 = self.entity.start_angle
        deg1 = self.entity.end_angle
        r = self.entity.radius
        x0 = self.entity.center[0]
        y0 = self.entity.center[1]
        begin_x = x0 + r * cos(deg0 / 180. * pi)
        begin_y = y0 + r * sin(deg0 / 180. * pi)
        end_x = x0 + r * cos(deg1 / 180. * pi)
        end_y = y0 + r * sin(deg1 / 180. * pi)

        return 'G01*\nX{0}Y{1}D02*\n' \
               'G75*\nG{2}*\nX{3}Y{4}I{5}J{6}D01*'.format(
            write_gerber_value(begin_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(begin_y, settings.format,
                               settings.zero_suppression),
            '03',
            write_gerber_value(end_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(end_y, settings.format,
                               settings.zero_suppression),
            write_gerber_value(x0 - begin_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0 - begin_y, settings.format,
                               settings.zero_suppression)
        )

    def to_inch(self):
        self.entity.start_angle = inch(self.entity.start_angle)
        self.entity.end_angle = inch(self.entity.end_angle)
        self.entity.radius = inch(self.entity.radius)
        self.entity.center[idx] = (
            inch(self.entity.center[idx][0]), inch(self.entity.center[idx][1]))

    def to_metric(self):
        self.entity.start_angle = metric(self.entity.start_angle)
        self.entity.end_angle = metric(self.entity.end_angle)
        self.entity.radius = metric(self.entity.radius)
        self.entity.center[idx] = (
            metric(self.entity.center[idx][0]), metric(self.entity.center[idx][1]))

class DxfPolylineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfPolylineStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings()):
        x0 = self.entity.points[0][0]
        y0 = self.entity.points[0][1]
        b = self.entity.bulge[0]
        gerber = 'G01*\nX{0}Y{1}D02*\nG75*'.format(
            write_gerber_value(x0, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0, settings.format,
                               settings.zero_suppression),
        )
        
        def ptseq():
            for i in range(1, len(self.entity.points)):
                yield i
            if self.entity.is_closed:
                yield 0
        
        for idx in ptseq():
            pt = self.entity.points[idx]
            x1 = pt[0]
            y1 = pt[1]
            if b == 0:
                gerber += '\nG01*\nX{0}Y{1}D01*'.format(
                    write_gerber_value(x1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(y1, settings.format,
                                       settings.zero_suppression),
                )
            else:
                ang = 4 * atan(b)
                xm = x0 + x1
                ym = y0 + y1
                t = 1 / tan(ang / 2)
                xc = (xm - t * (y1 - y0)) / 2
                yc = (ym + t * (x1 - x0)) / 2
                r = sqrt((x0 - xc)*(x0 - xc) + (y0 - yc)*(y0 - yc))

                gerber += '\nG{0}*\nX{1}Y{2}I{3}J{4}D01*'.format(
                    '03' if ang > 0 else '02',
                    write_gerber_value(x1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(y1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(xc - x0, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(yc - y0, settings.format,
                                       settings.zero_suppression)
                )

            x0 = x1
            y0 = y1
            b = self.entity.bulge[idx]
        
        return gerber

    def to_inch(self):
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                inch(self.entity.points[idx][0]), inch(self.entity.points[idx][1]))
            self.entity.bulge[idx] = inch(self.entity.bulge[idx])

    def to_metric(self):
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                metric(self.entity.points[idx][0]), metric(self.entity.points[idx][1]))
            self.entity.bulge[idx] = metric(self.entity.bulge[idx])

class DxfStatements(object):
    def __init__(self, entities, units, dcode=10, draw_mode=None):
        if draw_mode == None:
            draw_mode = DxfFile.DM_LINE
        self._units = units
        self.dcode = dcode
        self.draw_mode = draw_mode
        self.statements = []
        for entity in entities:
            if entity.dxftype == 'LWPOLYLINE':
                self.statements.append(DxfPolylineStatement(entity))
            elif entity.dxftype == 'LINE':
                self.statements.append(DxfLineStatement(entity))
            elif entity.dxftype == 'CIRCLE':
                self.statements.append(DxfCircleStatement(entity))
            elif entity.dxftype == 'ARC':
                self.statements.append(DxfArcStatement(entity))

    @property
    def units(self):
        return _units

    def to_gerber(self, settings=FileSettings()):
        def gerbers():
            yield 'D{0}*'.format(self.dcode)
            if self.draw_mode == DxfFile.DM_FILL:
                yield 'G36*'
                for statement in self.statements:
                    if isinstance(statement, DxfCircleStatement) or \
                        (isinstance(statement, DxfPolylineStatement) and statement.entity.is_closed):
                        yield statement.to_gerber(settings)
                yield 'G37*'
            else:
                for statement in self.statements:
                    yield statement.to_gerber(settings)

        return '\n'.join(gerbers())

    def to_inch(self):
        if self._units == 'metric':
            self._units = 'inch'
            for statement in self.statements:
                statement.to_inch()

    def to_metric(self):
        if self._units == 'inch':
            self._units = 'metric'
            for statement in self.statements:
                statement.to_metric()

class DxfHeaderStatement(object):
    def to_gerber(self, settings):
        return 'G75*\n'\
               '%MO{0}*%\n'\
               '%OFA0B0*%\n'\
               '%FS{1}AX{2}{3}Y{4}{5}*%\n'\
               '%IPPOS*%\n'\
               '%LPD*%'.format(
            'IN' if settings.units == 'inch' else 'MM',
            'L' if settings.zero_suppression == 'leading' else 'T',
            settings.format[0], settings.format[1],
            settings.format[0], settings.format[1]
        )

    def to_inch(self):
        pass

    def to_metric(self):
        pass

class DxfFile(CamFile):
    DM_LINE = 0
    DM_FILL = 1

    def __init__(self, dxf, settings=FileSettings(), draw_mode=None, filename=None):
        if draw_mode == None:
            draw_mode = self.DM_LINE
        if dxf.header['$INSUNITS'] == 1:
            settings.units = 'inch'
            settings.format = (2, 5)
        else:
            settings.units = 'metric'
            settings.format = (3, 4)

        super(DxfFile, self).__init__(settings=settings, filename=filename)
        self._draw_mode = draw_mode
        self.header = DxfHeaderStatement()
        self.aperture = ADParamStmt.circle(dcode=10, diameter=0.0)
        self.statements = DxfStatements(dxf.entities, self.units, dcode=self.aperture.d, draw_mode=self.draw_mode)

    @property
    def dcode(self):
        return self.aperture.dcode

    @dcode.setter
    def dcode(self, value):
        self.aperture.d = value
        self.statements.dcode = value

    @property
    def width(self):
        return self.aperture.modifiers[0][0]

    @width.setter
    def width(self, value):
        self.aperture.modifiers = ([float(value),],)

    @property
    def draw_mode(self):
        return self._draw_mode
    
    @draw_mode.setter
    def draw_mode(self, value):
        self._draw_mode = value
        self.statements.draw_mode = value
    
    def write(self, filename=None):
        if self.settings.notation != 'absolute':
            raise Exception('DXF file\'s notation must be absolute ')

        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:
            f.write(self.header.to_gerber(self.settings) + '\n')
            f.write(self.aperture.to_gerber(self.settings) + '\n')
            f.write(self.statements.to_gerber(self.settings) + '\n')
            f.write('M02*\n')

    def to_inch(self):
        if self.units == 'metric':
            self.header.to_inch()
            self.aperture.to_inch()
            self.statements.to_inch()
            self.units = 'inch'

    def to_metric(self):
        if self.units == 'inch':
            self.header.to_metric()
            self.aperture.to_metric()
            self.statements.to_metric()
            self.units = 'metric'

    def offset(self, ofset_x, offset_y):
        raise Exception('Not supported')

def loads(data, filename=None):
    stream = io.StringIO(data)
    dxf = dxfgrabber.read(stream)
    return DxfFile(dxf)

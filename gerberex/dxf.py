#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import io
from math import pi, cos, sin, tan, atan, atan2, acos, asin, sqrt
from gerber.cam import CamFile, FileSettings
from gerber.utils import inch, metric, write_gerber_value
from gerber.gerber_statements import ADParamStmt
from gerber.excellon_statements import ExcellonTool
from gerber.excellon_statements import CoordinateStmt
import dxfgrabber

class DxfStatement(object):
    def __init__(self, entity):
        self.entity = entity

    def to_gerber(self, settings=None, pitch=0, width=0):
        pass

    def to_excellon(self, settings=None, pitch=0, width=0):
        pass

    def to_inch(self):
        pass
    
    def to_metric(self):
        pass

class DxfLineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfLineStatement, self).__init__(entity)
    
    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch == 0:
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
        else:
            gstr = ""
            for p in self._dots(pitch, width):
                gstr += 'X{0}Y{1}D03*\n'.format(
                    write_gerber_value(p[0], settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(p[1], settings.format, 
                                       settings.zero_suppression))
            return gstr

    def to_excellon(self, settings=FileSettings(), pitch=0, width=0):
        if not pitch:
            return
        gstr = ""
        for p in self._dots(pitch, width):
            gstr += CoordinateStmt(x=p[0], y=p[1]).to_excellon(settings) + '\n'
        return gstr

    def to_inch(self):
        self.entity.start = (
            inch(self.entity.start[0]), inch(self.entity.start[1]))
        self.entity.end = (
            inch(self.entity.end[0]), inch(self.entity.end[1]))

    def to_metric(self):
        self.entity.start = (
            metric(self.entity.start[0]), inch(self.entity.start[1]))
        self.entity.end = (
            metric(self.entity.end[0]), inch(self.entity.end[1]))

    def _dots(self, pitch, width):
        x0 = self.entity.start[0]
        y0 = self.entity.start[1]
        x1 = self.entity.end[0]
        y1 = self.entity.end[1]
        xp = x1 - x0
        yp = y1 - y0
        l = sqrt(xp * xp + yp * yp)
        xd = xp * pitch / l
        yd = yp * pitch / l

        d = 0;
        while d < l + width / 2:
            yield (x0, y0)
            x0 += xd
            y0 += yd
            d += pitch

class DxfCircleStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfCircleStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch:
            return
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
        self.entity.center = (
            inch(self.entity.center[0]), inch(self.entity.center[1]))

    def to_metric(self):
        self.entity.radius = metric(self.entity.radius)
        self.entity.center = (
            metric(self.entity.center[0]), metric(self.entity.center[1]))

class DxfArcStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfArcStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch:
            return
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
        self.entity.center = (
            inch(self.entity.center[0]), inch(self.entity.center[1]))

    def to_metric(self):
        self.entity.start_angle = metric(self.entity.start_angle)
        self.entity.end_angle = metric(self.entity.end_angle)
        self.entity.radius = metric(self.entity.radius)
        self.entity.center = (
            metric(self.entity.center[0]), metric(self.entity.center[1]))

class DxfPolylineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfPolylineStatement, self).__init__(entity)

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch:
            return
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
        self.pitch = inch(1) if self._units == 'unit' else 1
        self.width = 0
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
                    yield statement.to_gerber(
                        settings, 
                        pitch=self.pitch if self.draw_mode == DxfFile.DM_MOUSE_BITES else 0,
                        width=self.width)

        return '\n'.join(gerbers())

    def to_excellon(self, settings=FileSettings()):
        if not self.draw_mode == DxfFile.DM_MOUSE_BITES:
            return
        def drills():
            for statement in self.statements:
                if isinstance(statement, DxfLineStatement):
                    yield statement.to_excellon(settings, pitch=self.pitch, width=self.width)
        return '\n'.join(drills())

    def to_inch(self):
        if self._units == 'metric':
            self._units = 'inch'
            self.pitch = inch(self.pitch)
            for statement in self.statements:
                statement.to_inch()

    def to_metric(self):
        if self._units == 'inch':
            self._units = 'metric'
            self.pitch = metric(self.pitch)
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
    
    def to_excellon(self, settings):
        return 'M48\n'\
               'FMAT,2\n'\
               'ICI,{0}\n'\
               '{1},{2},{3}.{4}\n'\
               '{5}'.format(
            'ON' if settings.notation == 'incremental' else 'OFF',
            'INCH' if settings.units == 'inch' else 'METRIC',
            'TZ' if settings.zero_suppression == 'leading' else 'LZ',
            '0' * settings.format[0], '0' * settings.format[1],
            'M72' if settings.units == 'inch' else 'M71'
        )

    def to_inch(self):
        pass

    def to_metric(self):
        pass

class DxfHeader2Statement(object):
    def to_gerber(self, settings):
        pass

    def to_excellon(self, settings):
        return '%'

    def to_inch(self):
        pass

    def to_metric(self):
        pass

class DxfFile(CamFile):
    DM_LINE = 0
    DM_FILL = 1
    DM_MOUSE_BITES = 2

    FT_RX274X = 0
    FT_EXCELLON = 1

    def __init__(self, dxf, settings=None, draw_mode=None, filename=None):
        if not settings:
            settings = FileSettings(zero_suppression='leading')

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
        
        self.header2 = DxfHeader2Statement()
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
        self.statements.width = value

    @property
    def draw_mode(self):
        return self._draw_mode
    
    @draw_mode.setter
    def draw_mode(self, value):
        self._draw_mode = value
        self.statements.draw_mode = value

    @property
    def pitch(self):
        return self.statements.pitch
    
    @pitch.setter
    def pitch(self, value):
        self.statements.pitch = value
    
    def write(self, filename=None, filetype=FT_RX274X):
        if self.settings.notation != 'absolute':
            raise Exception('DXF file\'s notation must be absolute ')
        
        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:
            if filetype == self.FT_RX274X:
                f.write(self.header.to_gerber(self.settings) + '\n')
                f.write(self.aperture.to_gerber(self.settings) + '\n')
                f.write(self.statements.to_gerber(self.settings) + '\n')
                f.write('M02*\n')
            else:
                tool = ExcellonTool(self.settings, number=1, diameter=self.width)
                f.write(self.header.to_excellon(self.settings) + '\n')
                f.write(tool.to_excellon(self.settings) + '\n')
                f.write(self.header2.to_excellon(self.settings) + '\n')
                f.write('T01\n')
                f.write(self.statements.to_excellon(self.settings) + '\n')
                f.write('M30\n')


    def to_inch(self):
        if self.units == 'metric':
            self.header.to_inch()
            self.aperture.to_inch()
            self.statements.to_inch()
            self.pitch = inch(self.pitch)
            self.units = 'inch'

    def to_metric(self):
        if self.units == 'inch':
            self.header.to_metric()
            self.aperture.to_metric()
            self.statements.to_metric()
            self.pitch = metric(self.pitch)
            self.units = 'metric'

    def offset(self, ofset_x, offset_y):
        raise Exception('Not supported')

def loads(data, filename=None):
    stream = io.StringIO(data)
    dxf = dxfgrabber.read(stream)
    return DxfFile(dxf)

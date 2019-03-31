#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import io
from math import pi, cos, sin, tan, atan, atan2, acos, asin, sqrt
import dxfgrabber
from gerber.cam import CamFile, FileSettings
from gerber.utils import inch, metric, write_gerber_value
from gerber.gerber_statements import ADParamStmt
from gerber.excellon_statements import ExcellonTool
from gerber.excellon_statements import CoordinateStmt
from gerberex.dxf_path import generate_closed_paths

ACCEPTABLE_ERROR = 0.001

def is_equal_value(a, b, error_range=0):
    return a - b <= error_range and a - b >= -error_range

def is_equal_point(a, b, error_range=0):
    return is_equal_value(a[0], b[0], error_range) and \
           is_equal_value(a[1], b[1], error_range)

class DxfStatement(object):
    def __init__(self, entity):
        self.entity = entity
        self.start = None
        self.end = None
        self.is_closed = False

    def to_gerber(self, settings=None, pitch=0, width=0):
        pass

    def to_excellon(self, settings=None, pitch=0, width=0):
        pass

    def to_inch(self):
        pass
    
    def to_metric(self):
        pass

    def is_equal_to(self, target, error_range=0):
        return False

    def reverse(self):
        raise Exception('Not implemented')

class DxfLineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfLineStatement, self).__init__(entity)
        self.start = (self.entity.start[0], self.entity.start[1])
        self.end = (self.entity.end[0], self.entity.end[1])
    
    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch == 0:
            x0, y0 = self.start
            x1, y1 = self.end
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
        self.start = (
            inch(self.start[0]), inch(self.start[1]))
        self.end = (
            inch(self.end[0]), inch(self.end[1]))

    def to_metric(self):
        self.start = (
            metric(self.start[0]), inch(self.start[1]))
        self.end = (
            metric(self.end[0]), inch(self.end[1]))

    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfLineStatement):
            return False
        return (is_equal_point(self.start, target.start, error_range) and \
                is_equal_point(self.end, target.end, error_range)) or \
               (is_equal_point(self.start, target.end, error_range) and \
                is_equal_point(self.end, target.start, error_range))

    def reverse(self):
        pt = self.start
        self.start = self.end
        self.end = pt

    def _dots(self, pitch, width):
        x0, y0 = self.start
        x1, y1 = self.end
        y1 = self.end[1]
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
        self.radius = self.entity.radius
        self.center = (self.entity.center[0], self.entity.center[1])
        self.start = (self.center[0] + self.radius, self.center[1])
        self.end = self.start
        self.is_closed = True

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch:
            return
        r = self.radius
        x0, y0 = self.center
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
        self.radius = inch(self.radius)
        self.center = (
            inch(self.center[0]), inch(self.center[1]))

    def to_metric(self):
        self.radius = metric(self.radius)
        self.center = (
            metric(self.center[0]), metric(self.center[1]))

    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfCircleStatement):
            return False
        return is_equal_point(self.center, target.enter, error_range) and \
               is_equal_value(self.radius, target.radius)

    def reverse(self):
        pass

class DxfArcStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfArcStatement, self).__init__(entity)
        self.start_angle = self.entity.start_angle
        self.end_angle = self.entity.end_angle
        self.radius = self.entity.radius
        self.center = (self.entity.center[0], self.entity.center[1])
        self.start = (
            self.center[0] + self.radius * cos(self.start_angle / 180. * pi),
            self.center[1] + self.radius * sin(self.start_angle / 180. * pi),
        )
        self.end = (
            self.center[0] + self.radius * cos(self.end_angle / 180. * pi),
            self.center[1] + self.radius * sin(self.end_angle / 180. * pi),
        )
        angle = self.end_angle - self.start_angle
        self.is_closed = angle >= 360 or angle <= -360

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        if pitch:
            return
        x0 = self.center[0]
        y0 = self.center[1]
        start_x, start_y = self.start
        end_x, end_y = self.end

        return 'G01*\nX{0}Y{1}D02*\n' \
               'G75*\nG{2}*\nX{3}Y{4}I{5}J{6}D01*'.format(
            write_gerber_value(start_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(start_y, settings.format,
                               settings.zero_suppression),
            '02' if self.start_angle > self.end_angle else '03',
            write_gerber_value(end_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(end_y, settings.format,
                               settings.zero_suppression),
            write_gerber_value(x0 - start_x, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0 - start_y, settings.format,
                               settings.zero_suppression)
        )

    def to_inch(self):
        self.radius = inch(self.radius)
        self.center = (inch(self.center[0]), inch(self.center[1]))
        self.start = (inch(self.start[0]), inch(self.start[1]))
        self.end = (inch(self.end[0]), inch(self.end[1]))

    def to_metric(self):
        self.radius = metric(self.radius)
        self.center = (metric(self.center[0]), metric(self.center[1]))
        self.start = (metric(self.start[0]), metric(self.start[1]))
        self.end = (metric(self.end[0]), metric(self.end[1]))

    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfArcStatement):
            return False
        aerror_range = error_range / pi * self.radius * 180
        return is_equal_point(self.center, target.center, error_range) and \
               is_equal_value(self.radius, target.radius, error_range) and \
               ((is_equal_value(self.start_angle, target.start_angle, aerror_range) and 
                 is_equal_value(self.end_angle, target.end_angle, aerror_range)) or
                (is_equal_value(self.start_angle, target.end_angle, aerror_range) and
                 is_equal_value(self.end_angle, target.end_angle, aerror_range)))

    def reverse(self):
        tmp = self.start_angle
        self.start_angle = self.end_angle
        self.end_angle = tmp
        tmp = self.start
        self.start = self.end
        self.end = tmp

class DxfPolylineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfPolylineStatement, self).__init__(entity)
        self.start = (self.entity.points[0][0], self.entity.points[0][1])
        self.is_closed = self.entity.is_closed
        if self.is_closed:
            self.end = self.start
        else:
            self.end = (self.entity.points[-1][0], self.entity.points[-1][1])

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
        self.start = (inch(self.start[0]), inch(self.start[1]))
        self.end = (inch(self.end[0]), inch(self.end[1]))
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                inch(self.entity.points[idx][0]), inch(self.entity.points[idx][1]))
            self.entity.bulge[idx] = inch(self.entity.bulge[idx])

    def to_metric(self):
        self.start = (metric(self.start[0]), metric(self.start[1]))
        self.end = (metric(self.end[0]), metric(self.end[1]))
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
        self.pitch = inch(1) if self._units == 'inch' else 1
        self.width = 0
        self.error_range = inch(ACCEPTABLE_ERROR) if self._units == 'inch' else ACCEPTABLE_ERROR
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
        self.paths = generate_closed_paths(self.statements, self.error_range)

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
                for path in self.paths:
                    yield path.to_gerber(settings)
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
            self.error_range = inch(self.error_range)
            for statement in self.statements:
                statement.to_inch()
            for path in self.paths:
                path.to_inch()

    def to_metric(self):
        if self._units == 'inch':
            self._units = 'metric'
            self.pitch = metric(self.pitch)
            self.error_range = metric(self.error_range)
            for statement in self.statements:
                statement.to_metric()
            for path in self.paths:
                path.to_metric()

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

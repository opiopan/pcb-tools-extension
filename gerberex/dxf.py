#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import io, sys
from math import pi, cos, sin, tan, atan, atan2, acos, asin, sqrt
import dxfgrabber
from gerber.cam import CamFile, FileSettings
from gerber.utils import inch, metric, write_gerber_value, rotate_point
from gerber.gerber_statements import ADParamStmt
from gerber.excellon_statements import ExcellonTool
from gerber.excellon_statements import CoordinateStmt
from gerberex.utility import is_equal_point, is_equal_value
from gerberex.dxf_path import generate_closed_paths

ACCEPTABLE_ERROR = 0.001

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

    def offset(self, offset_x, offset_y):
        raise Exception('Not supported')
    
    def rotate(self, angle, center=(0, 0)):
        raise Exception('Not supported')


class DxfLineStatement(DxfStatement):
    @classmethod
    def from_entity(cls, entity):
        start = (entity.start[0], entity.start[1])
        end = (entity.end[0], entity.end[1])
        return cls(entity, start, end)

    def __init__(self, entity, start, end):
        super(DxfLineStatement, self).__init__(entity)
        self.start = start
        self.end = end
    
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
            metric(self.start[0]), metric(self.start[1]))
        self.end = (
            metric(self.end[0]), metric(self.end[1]))

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

    def offset(self, offset_x, offset_y):
        self.start = (self.start[0] + offset_x, self.start[1] + offset_y)
        self.end = (self.end[0] + offset_x, self.end[1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        self.start = rotate_point(self.start, angle, center)
        self.end = rotate_point(self.end, angle, center)

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

    def offset(self, offset_x, offset_y):
        self.center = (self.center[0] + offset_x, self.center[1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        self.center = rotate_point(self.center, angle, center)

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

    def offset(self, offset_x, offset_y):
        self.center = (self.center[0] + offset_x, self.center[1] + offset_y)
        self.start = (self.start[0] + offset_x, self.start[1] + offset_y)
        self.end = (self.end[0] + offset_x, self.end[1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        self.start_angle += angle
        self.end_angle += angle
        self.center = rotate_point(self.center, angle, center)
        self.start = rotate_point(self.start, angle, center)
        self.end = rotate_point(self.end, angle, center)

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

    def to_metric(self):
        self.start = (metric(self.start[0]), metric(self.start[1]))
        self.end = (metric(self.end[0]), metric(self.end[1]))
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                metric(self.entity.points[idx][0]), metric(self.entity.points[idx][1]))
    
    def offset(self, offset_x, offset_y):
        for idx in range(len(self.entity.points)):
            self.entity.points[idx] = (
                self.entity.points[idx][0] + offset_x, self.entity.points[idx][1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        for idx in range(len(self.entity.points)):
            self.entity.points[idx] = rotate_point(self.entity.points[idx], angle, center)


class DxfStatements(object):
    def __init__(self, statements, units, dcode=10, draw_mode=None):
        if draw_mode == None:
            draw_mode = DxfFile.DM_LINE
        self._units = units
        self.dcode = dcode
        self.draw_mode = draw_mode
        self.pitch = inch(1) if self._units == 'inch' else 1
        self.width = 0
        self.error_range = inch(ACCEPTABLE_ERROR) if self._units == 'inch' else ACCEPTABLE_ERROR
        self.statements = statements
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
    
    def offset(self, offset_x, offset_y):
        for statement in self.statements:
            statement.offset(offset_x, offset_y)

    def rotate(self, angle, center=(0, 0)):
        for statement in self.statements:
            statement.rotate(angle, center)

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

    @classmethod
    def from_dxf(cls, dxf, settings=None, draw_mode=None, filename=None):
        fsettings = settings if settings else \
            FileSettings(zero_suppression='leading')

        if dxf.header['$INSUNITS'] == 1:
            fsettings.units = 'inch'
            if not settings:
                fsettings.format = (2, 5)
        else:
            fsettings.units = 'metric'
            if not settings:
                fsettings.format = (3, 4)

        statements = []
        for entity in dxf.entities:
            if entity.dxftype == 'LWPOLYLINE':
                statements.append(DxfPolylineStatement(entity))
            elif entity.dxftype == 'LINE':
                statements.append(DxfLineStatement.from_entity(entity))
            elif entity.dxftype == 'CIRCLE':
                statements.append(DxfCircleStatement(entity))
            elif entity.dxftype == 'ARC':
                statements.append(DxfArcStatement(entity))
        
        return cls(statements, fsettings, draw_mode, filename)
    
    @classmethod
    def rectangle(cls, width, height, left=0, bottom=0, units='metric', draw_mode=None, filename=None):
        if units == 'metric':
            settings = FileSettings(units=units, zero_suppression='leading', format=(3,4))
        else:
            settings = FileSettings(units=units, zero_suppression='leading', format=(2,5))
        statements = [
            DxfLineStatement(None, (left, bottom), (left + width, bottom)),
            DxfLineStatement(None, (left + width, bottom), (left + width, bottom + height)),
            DxfLineStatement(None, (left + width, bottom + height), (left, bottom + height)),
            DxfLineStatement(None, (left, bottom + height), (left, bottom)),
        ]
        return cls(statements, settings, draw_mode, filename)

    def __init__(self, statements, settings=None, draw_mode=None, filename=None):
        if not settings:
            settings = FileSettings(units='metric', format=(3,4), zero_suppression='leading')
        if draw_mode == None:
            draw_mode = self.DM_LINE

        super(DxfFile, self).__init__(settings=settings, filename=filename)
        self._draw_mode = draw_mode
        self.header = DxfHeaderStatement()
        
        self.header2 = DxfHeader2Statement()
        self.aperture = ADParamStmt.circle(dcode=10, diameter=0.0)
        self.statements = DxfStatements(
            statements, self.units, dcode=self.aperture.d, draw_mode=self.draw_mode)

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

    def offset(self, offset_x, offset_y):
        self.statements.offset(offset_x, offset_y)
    
    def rotate(self, angle, center=(0, 0)):
        self.statements.rotate(angle, center)

def loads(data, filename=None):
    if sys.version_info.major == 2:
        data = unicode(data)
    stream = io.StringIO(data)
    dxf = dxfgrabber.read(stream)
    return DxfFile.from_dxf(dxf)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import operator

from gerber.excellon import ExcellonParser, detect_excellon_format, ExcellonFile, DrillHit, DrillSlot
from gerber.excellon_statements import UnitStmt, CoordinateStmt, UnknownStmt, SlotStmt, DrillModeStmt, \
                                       ToolSelectionStmt, ZAxisRoutPositionStmt, \
                                       RetractWithClampingStmt, RetractWithoutClampingStmt, \
                                       EndOfProgramStmt
from gerber.cam import FileSettings
from gerber.utils import inch, metric, write_gerber_value, parse_gerber_value
from gerberex.utility import rotate

def loads(data, filename=None, settings=None, tools=None, format=None):
    if not settings:
        settings = FileSettings(**detect_excellon_format(data))
        if format:
            settings.format = format
    file = ExcellonParser(settings, tools).parse_raw(data, filename)
    return ExcellonFileEx.from_file(file)

class ExcellonFileEx(ExcellonFile):
    @classmethod
    def from_file(cls, file):
        def correct_statements():
            lazy_stmt = None
            modifier = None
            for stmt in file.statements:
                modifier = lazy_stmt
                lazy_stmt = None
                if isinstance(stmt, UnitStmt):
                    yield UnitStmtEx.from_statement(stmt)
                elif isinstance(stmt, CoordinateStmt):
                    new_stmt = CoordinateStmtEx.from_statement(stmt)
                    if modifier and new_stmt.mode is None:
                        new_stmt.mode = modifier
                    yield new_stmt
                elif isinstance(stmt, UnknownStmt):
                    line = stmt.stmt.strip()
                    mode = None
                    if line[:3] == 'G02':
                        mode = CoordinateStmtEx.MODE_CIRCULER_CW
                    elif line[:3] == 'G03':
                        mode = CoordinateStmtEx.MODE_CIRCULER_CCW
                    else:
                        yield stmt
                        continue
                    if len(line) == 3:
                        lazy_stmt = mode
                        continue
                    new_stmt = CoordinateStmtEx.from_excellon(line[3:], file.settings)
                    new_stmt.mode = mode
                    yield new_stmt
                else:
                    yield stmt

        def generate_hits(statements):
            STAT_DRILL = 0
            STAT_ROUT_UP = 1
            STAT_ROUT_DOWN = 2
            status = STAT_DRILL
            current_tool = None
            rout_statements = []

            def make_rout(status, statements):
                if status != STAT_ROUT_DOWN or len(statements) == 0 or current_tool is None:
                    return None
                return DrillRout.from_coordinates(current_tool, statements)

            for stmt in statements:
                if isinstance(stmt, ToolSelectionStmt):
                    current_tool = file.tools[stmt.tool]
                elif isinstance(stmt, DrillModeStmt):
                    rout = make_rout(status, rout_statements)
                    rout_statements = []
                    if rout is not None:
                        yield rout
                    status = STAT_DRILL
                elif isinstance(stmt, ZAxisRoutPositionStmt) and status == STAT_ROUT_UP:
                    status = STAT_ROUT_DOWN
                elif isinstance(stmt, RetractWithClampingStmt) or isinstance(stmt, RetractWithoutClampingStmt):
                    rout = make_rout(status, rout_statements)
                    rout_statements = []
                    if rout is not None:
                        yield rout
                    status = STAT_ROUT_UP
                elif isinstance(stmt, SlotStmt):
                    yield DrillSlotEx(current_tool, (stmt.x_start, stmt.y_start), 
                                      (stmt.x_end, stmt.y_end), DrillSlotEx.TYPE_G85)
                elif isinstance(stmt, CoordinateStmtEx):
                    if stmt.mode is None:
                        if status != STAT_DRILL:
                            raise Exception('invalid statement sequence')
                        yield DrillHitEx(current_tool, (stmt.x, stmt.y))
                    else:
                        if stmt.mode == stmt.MODE_ROUT:
                            status = STAT_ROUT_UP
                        if status == STAT_ROUT_UP:
                            rout_statements = [stmt]
                        elif status == STAT_ROUT_DOWN:
                            rout_statements.append(stmt)
                        else:
                            raise Exception('invalid statement sequence')

        statements = [s for s in correct_statements()]
        hits = [h for h in generate_hits(statements)]
        return cls(statements, file.tools, hits, file.settings, file.filename)
    
    @property
    def primitives(self):
        return []

    def __init__(self, statements, tools, hits, settings, filename=None):
        super(ExcellonFileEx, self).__init__(statements, tools, hits, settings, filename)

    def rotate(self, angle, center=(0,0)):
        if angle % 360 == 0:
            return
        for hit in self.hits:
            hit.rotate(angle, center)
    
    def to_inch(self):
        if self.units == 'metric':
            for stmt in self.statements:
                stmt.to_inch()
            for tool in self.tools:
                self.tools[tool].to_inch()
            for hit in self.hits:
                hit.to_inch()

    def to_metric(self):
        if self.units == 'inch':
            for stmt in self.statements:
                stmt.to_metric()
            for tool in self.tools:
                self.tools[tool].to_metric()
            for hit in self.hits:
                hit.to_metric()
    
    def write(self, filename=None):
        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:

            for statement in self.statements:
                if not isinstance(statement, ToolSelectionStmt):
                    f.write(statement.to_excellon(self.settings) + '\n')
                else:
                    break

            for tool in iter(self.tools.values()):
                f.write(ToolSelectionStmt(
                    tool.number).to_excellon(self.settings) + '\n')
                for hit in self.hits:
                    if hit.tool.number == tool.number:
                        f.write(hit.to_excellon(self.settings) + '\n')
            f.write(EndOfProgramStmt().to_excellon() + '\n')

class DrillHitEx(DrillHit):
    def to_inch(self):
        self.position = tuple(map(inch, self.position))

    def to_metric(self):
        self.position = tuple(map(metric, self.position))

    def rotate(self, angle, center=(0, 0)):
        self.position = rotate(*self.position, angle, center)

    def to_excellon(self, settings):
        return CoordinateStmtEx(*self.position).to_excellon(settings)

class DrillSlotEx(DrillSlot):
    def to_inch(self):
        self.start = tuple(map(inch, self.start))
        self.end = tuple(map(inch, self.end))

    def to_metric(self):
        self.start = tuple(map(metric, self.start))
        self.end = tuple(map(metric, self.end))

    def rotate(self, angle, center=(0,0)):
        self.start = rotate(*self.start, angle, center)
        self.end = rotate(*self.end, angle, center)

    def to_excellon(self, settings):
        return SlotStmt(*self.start, *self.end).to_excellon(settings)

class DrillRout(object):
    class Node(object):
        def __init__(self, mode, x, y, radius):
            self.mode = mode
            self.position = (x, y)
            self.radius = radius

    @classmethod
    def from_coordinates(cls, tool, coordinates):
        nodes = [cls.Node(c.mode, c.x, c.y, c.radius) for c in coordinates]
        return cls(tool, nodes)

    def __init__(self, tool, nodes):
        self.tool = tool
        self.nodes = nodes

    def to_excellon(self, settings):
        node = self.nodes[0]
        excellon = CoordinateStmtEx(*node.position, node.radius, 
                                    CoordinateStmtEx.MODE_ROUT).to_excellon(settings) + '\nM15\n'
        for node in self.nodes[1:]:
            excellon += CoordinateStmtEx(*node.position, node.radius,
                                        node.mode).to_excellon(settings) + '\n'
        excellon += 'M16\nG05'
        return excellon

    def to_inch(self):
        for node in self.nodes:
            node.position = tuple(map(inch, node.position))
            node.radius = inch(
                node.radius) if node.radius is not None else None

    def to_metric(self):
        for node in self.nodes:
            node.position = tuple(map(metric, node.position))
            node.radius = metric(
                node.radius) if node.radius is not None else None

    def offset(self, x_offset=0, y_offset=0):
        for node in self.nodes:
            node.position = tuple(map(operator.add, node.position, (x_offset, y_offset)))

    def rotate(self, angle, center=(0, 0)):
        for node in self.nodes:
            node.position = rotate(*node.position, angle, center)

class UnitStmtEx(UnitStmt):
    @classmethod
    def from_statement(cls, stmt):
        return cls(units=stmt.units, zeros=stmt.zeros, format=stmt.format, id=stmt.id)

    def __init__(self, units='inch', zeros='leading', format=None, **kwargs):
        super(UnitStmtEx, self).__init__(units, zeros, format, **kwargs)
    
    def to_excellon(self, settings=None):
        format = settings.format if settings else self.format
        stmt = '%s,%s,%s.%s' % ('INCH' if self.units == 'inch' else 'METRIC',
                          'LZ' if self.zeros == 'leading' else 'TZ',
                          '0' * format[0], '0' * format[1])
        return stmt

class CoordinateStmtEx(CoordinateStmt):
    MODE_ROUT = 'ROUT'
    MODE_LINEAR = 'LINEAR'
    MODE_CIRCULER_CW = 'CW'
    MODE_CIRCULER_CCW = 'CCW'

    @classmethod
    def from_statement(cls, stmt):
        newStmt = cls(x=stmt.x, y=stmt.y)
        newStmt.mode = stmt.mode
        newStmt.radius = stmt.radius if isinstance(stmt, CoordinateStmtEx) else None
        return newStmt

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        parts = line.split('A')
        stmt = cls.from_statement(CoordinateStmt.from_excellon(parts[0], settings))
        if len(parts) > 1:
            stmt.radius = parse_gerber_value(
                parts[1], settings.format, settings.zero_suppression)
        return stmt

    def __init__(self, x=None, y=None, radius=None, mode=None, **kwargs):
        super(CoordinateStmtEx, self).__init__(x, y, **kwargs)
        self.mode = mode
        self.radius = radius
    
    def to_excellon(self, settings):
        stmt = ''
        if self.mode == self.MODE_ROUT:
            stmt += "G00"
        if self.mode == self.MODE_LINEAR:
            stmt += "G01"
        if self.mode == self.MODE_CIRCULER_CW:
            stmt += "G02"
        if self.mode == self.MODE_CIRCULER_CCW:
            stmt += "G03"
        if self.x is not None:
            stmt += 'X%s' % write_gerber_value(self.x, settings.format,
                                               settings.zero_suppression)
        if self.y is not None:
            stmt += 'Y%s' % write_gerber_value(self.y, settings.format,
                                               settings.zero_suppression)
        if self.radius is not None:
            stmt += 'A%s' % write_gerber_value(self.radius, settings.format,
                                               settings.zero_suppression)
        return stmt

    def __str__(self):
        coord_str = ''
        if self.x is not None:
            coord_str += 'X: %g ' % self.x
        if self.y is not None:
            coord_str += 'Y: %g ' % self.y
        if self.radius is not None:
            coord_str += 'A: %g ' % self.radius

        return '<Coordinate Statement: %s(%s)>' % \
            (coord_str, self.mode if self.mode else 'HIT')

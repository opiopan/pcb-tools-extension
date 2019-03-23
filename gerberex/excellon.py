#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from gerber.excellon import (ExcellonParser, detect_excellon_format, ExcellonFile)
from gerber.excellon_statements import UnitStmt
from gerber.cam import FileSettings
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
        statements = [
            UnitStmtEx.from_statement(s) if isinstance(s, UnitStmt) else s \
                for s in file.statements
        ]
        return cls(statements, file.tools, file.hits, file.settings, file.filename)

    def __init__(self, statements, tools, hits, settings, filename=None):
        super(ExcellonFileEx, self).__init__(statements, tools, hits, settings, filename)

    def rotate(self, angle, center=(0,0)):
        if angle % 360 == 0:
            return
        for hit in self.hits:
            hit.position = rotate(hit.position[0], hit.position[1], angle, center)

class UnitStmtEx(UnitStmt):
    @classmethod
    def from_statement(cls, stmt):
        return cls(units=stmt.units, zeros=stmt.zeros, format=stmt.format, id=stmt.id)

    def __init__(self, units='inch', zeros='leading', format=None, **kwargs):
        super(UnitStmtEx, self).__init__(units, zeros, format, **kwargs)
    
    def to_excellon(self, settings=None):
        stmt = '%s,%s,%s.%s' % ('INCH' if self.units == 'inch' else 'METRIC',
                          'LZ' if self.zeros == 'leading' else 'TZ',
                          '0' * self.format[0], '0' * self.format[1])
        return stmt

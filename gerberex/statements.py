#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from gerber.gerber_statements import AMParamStmt
from gerberex.am_primitive import to_primitive_defs

class AMParamStmtEx(AMParamStmt):
    @classmethod
    def from_stmt(cls, stmt):
        return cls(stmt.param, stmt.name, stmt.macro)

    def __init__(self, param, name, macro):
        super(AMParamStmtEx, self).__init__(param, name, macro)
        self.primitive_defs = to_primitive_defs(self.instructions)
    
    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            for p in self.primitive_defs:
                p.to_inch()

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            for p in self.primitive_defs:
                p.to_metric()

    def to_gerber(self, settings = None):
        def plist():
            for p in self.primitive_defs:
                yield p.to_gerber(settings)
        return "%%AM%s*\n%s%%" % (self.name, '\n'.join(plist()))

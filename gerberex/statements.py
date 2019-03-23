#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from gerber.gerber_statements import AMParamStmt
from gerberex.am_primitive import to_primitive_defs

class AMParamStmtEx(AMParamStmt):
    @classmethod
    def from_stmt(cls, stmt):
        return cls(stmt.param, stmt.name, stmt.macro)

    @classmethod
    def circle(cls, name):
        return cls('AM', name, '1,1,$1,0,0,0*1,0,$2,0,0,0')

    @classmethod
    def rectangle(cls, name):
        return cls('AM', name, '21,1,$1,$2,0,0,0*1,0,$3,0,0,0')
    
    @classmethod
    def landscape_obround(cls, name):
        return cls(
            'AM', name,
            '$4=$1-$2*'
            '21,1,$1-$4,$2,0,0,0*'
            '1,1,$4,$4/2,0,0*'
            '1,1,$4,-$4/2,0,0*'
            '1,0,$3,0,0,0')

    @classmethod
    def portrate_obround(cls, name):
        return cls(
            'AM', name,
            '$4=$2-$1*'
            '21,1,$1,$2-$4,0,0,0*'
            '1,1,$4,0,$4/2,0*'
            '1,1,$4,0,-$4/2,0*'
            '1,0,$3,0,0,0')
    
    @classmethod
    def polygon(cls, name):
        return cls('AM', name, '5,1,$2,0,0,$1,$3*1,0,$4,0,0,0')

    def __init__(self, param, name, macro):
        super(AMParamStmtEx, self).__init__(param, name, macro)
        self.primitive_defs = list(to_primitive_defs(self.instructions))
    
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

    def rotate(self, angle, center=None):
        for primitive_def in self.primitive_defs:
            primitive_def.rotate(angle, center)

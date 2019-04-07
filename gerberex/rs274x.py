#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import gerber.rs274x
from gerber.gerber_statements import ADParamStmt, CoordStmt
from gerberex.gerber_statements import AMParamStmt, AMParamStmtEx, ADParamStmtEx
from gerberex.utility import rotate

class GerberFile(gerber.rs274x.GerberFile):
    @classmethod
    def from_gerber_file(cls, gerber_file):
        if not isinstance(gerber_file, gerber.rs274x.GerberFile):
            raise Exception('only gerber.rs274x.GerberFile object is specified')
        
        def swap_statement(statement):
            if isinstance(statement, AMParamStmt) and not isinstance(statement, AMParamStmtEx):
                return AMParamStmtEx.from_stmt(statement)
            elif isinstance(statement, ADParamStmt) and not isinstance(statement, AMParamStmtEx):
                return ADParamStmtEx.from_stmt(statement)
            else:
                return statement
        statements = [swap_statement(statement) for statement in gerber_file.statements]
        return cls(statements, gerber_file.settings, gerber_file.primitives,\
                   gerber_file.apertures, gerber_file.filename)

    def __init__(self, statements, settings, primitives, apertures, filename=None):
        super(GerberFile, self).__init__(statements, settings, primitives, apertures, filename)

    def offset(self, x_offset=0, y_offset=0):
        for statement in self.statements:
            if isinstance(statement, CoordStmt):
                if statement.x is not None:
                    statement.x += x_offset
                if statement.y is not None:
                    statement.y += y_offset
            else:
                statement.offset(x_offset, y_offset)
        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)

    def rotate(self, angle, center=(0,0)):
        if angle % 360 == 0:
            return
        self._generalize_aperture()
        last_x = 0
        last_y = 0
        last_rx = 0
        last_ry = 0
        for statement in self.statements:
            if isinstance(statement, AMParamStmtEx):
                statement.rotate(angle, center)
            elif isinstance(statement, CoordStmt) and statement.x != None and statement.y != None:
                if statement.i != None and statement.j != None:
                    cx = last_x + statement.i
                    cy = last_y + statement.j
                    cx, cy = rotate(cx, cy, angle, center)
                    statement.i = cx - last_rx
                    statement.j = cy - last_ry
                last_x = statement.x
                last_y = statement.y
                last_rx, last_ry = rotate(statement.x, statement.y, angle, center)
                statement.x = last_rx
                statement.y = last_ry
    
    def _generalize_aperture(self):
        RECTANGLE = 0
        LANDSCAPE_OBROUND = 1
        PORTRATE_OBROUND = 2
        POLYGON = 3
        macro_defs = [
            ('MACR', AMParamStmtEx.rectangle),
            ('MACLO', AMParamStmtEx.landscape_obround),
            ('MACPO', AMParamStmtEx.portrate_obround),
            ('MACP', AMParamStmtEx.polygon)
        ]

        need_to_change = False
        insert_point = 0
        last_aperture = 0
        macros = {}
        for idx in range(0, len(self.statements)):
            statement = self.statements[idx]
            if isinstance(statement, AMParamStmtEx):
                macros[statement.name] = statement
                if not need_to_change:
                    insert_point = idx + 1
            if isinstance(statement, ADParamStmt) and statement.shape in ['R', 'O', 'P']:
                need_to_change = True
                last_aperture = idx
        
        if need_to_change:
            for idx in range(0, len(macro_defs)):
                macro_def = macro_defs[idx]
                name = macro_def[0]
                num = 1
                while name in macros:
                    name = '%s_%d' % (macro_def[0], num)
                    num += 1
                self.statements.insert(insert_point, macro_def[1](name, self.units))
                macro_defs[idx] = (name, macro_def[1])
            for idx in range(insert_point, last_aperture + len(macro_defs) + 1):
                statement = self.statements[idx]
                if isinstance(statement, ADParamStmt):
                    if statement.shape == 'R':
                        statement.shape = macro_defs[RECTANGLE][0]
                    elif statement.shape == 'O':
                        x = statement.modifiers[0][0] \
                            if len(statement.modifiers[0]) > 0 else 0
                        y = statement.modifiers[0][1] \
                            if len(statement.modifiers[0]) > 1 else 0
                        statement.shape = macro_defs[LANDSCAPE_OBROUND][0] \
                                          if x > y else macro_defs[PORTRATE_OBROUND][0] 
                    elif statement.shape == 'P':
                        statement.shape = macro_defs[POLYGON][0]

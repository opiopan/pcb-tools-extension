#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import gerber.rs274x
from gerberex.statements import (AMParamStmt, AMParamStmtEx)

class GerberFile(gerber.rs274x.GerberFile):
    @classmethod
    def from_gerber_file(cls, gerber_file):
        if not isinstance(gerber_file, gerber.rs274x.GerberFile):
            raise Exception('only gerber.rs274x.GerberFile object is specified')
        
        def swap_statement(statement):
            if isinstance(statement, AMParamStmt) and not isinstance(statement, AMParamStmtEx):
                return AMParamStmtEx.from_stmt(statement)
            else:
                return statement
        statements = [swap_statement(statement) for statement in gerber_file.statements]
        return cls(statements, gerber_file.settings, gerber_file.primitives,\
                   gerber_file.apertures, gerber_file.filename)

    def __init__(self, statements, settings, primitives, apertures, filename=None):
        super(GerberFile, self).__init__(statements, settings, primitives, apertures, filename)

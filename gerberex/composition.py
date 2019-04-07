#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>
import os
from functools import reduce
from gerber.cam import FileSettings
from gerber.gerber_statements import EofStmt
from gerber.excellon_statements import *
import gerberex.rs274x
import gerberex.excellon
import gerberex.dxf

class Composition(object):
    def __init__(self, settings = None, comments = None):
        self.settings = settings
        self.comments = comments if comments != None else []

class GerberComposition(Composition):
    APERTURE_ID_BIAS = 10

    def __init__(self, settings=None, comments=None):
        super(GerberComposition, self).__init__(settings, comments)
        self.param_statements = []
        self.aperture_macros = {}
        self.apertures = []
        self.drawings = []

    def merge(self, file):
        if isinstance(file, gerberex.rs274x.GerberFile):
            self._merge_gerber(file)
        elif isinstance(file, gerberex.dxf.DxfFile):
            self._merge_dxf(file)
        else:
            raise Exception('unsupported file type')

    def dump(self, path):
        def statements():
            for s in self.param_statements:
                yield s
            for k in self.aperture_macros:
                yield self.aperture_macros[k]
            for s in self.apertures:
                yield s
            for s in self.drawings:
                yield s
            yield EofStmt()
        with open(path, 'w') as f:
            for statement in statements():
                f.write(statement.to_gerber(self.settings) + '\n')

    def _merge_gerber(self, file):
        param_statements = []
        aperture_macro_map = {}
        aperture_map = {}

        if self.settings:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        for statement in file.statements:
            if statement.type == 'COMMENT':
                self.comments.append(statement.comment)
            elif statement.type == 'PARAM':
                if statement.param == 'AM':
                    name = statement.name
                    newname = self._register_aperture_macro(statement)
                    aperture_macro_map[name] = newname
                elif statement.param == 'AD':
                    if not statement.shape in ['C', 'R', 'O']:
                        statement.shape = aperture_macro_map[statement.shape]
                    dnum = statement.d
                    newdnum = self._register_aperture(statement)
                    aperture_map[dnum] = newdnum
                elif statement.param == 'LP':
                    self.drawings.append(statement)
                else:
                    param_statements.append(statement)
            elif statement.type in ['EOF', "DEPRECATED"]:
                pass
            else:
                if statement.type == 'APERTURE':
                    statement.d = aperture_map[statement.d]
                self.drawings.append(statement)
        
        if not self.settings:
            self.settings = file.settings
            self.param_statements = param_statements

    def _merge_dxf(self, file):
        if self.settings:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        file.dcode = self._register_aperture(file.aperture)
        self.drawings.append(file.statements)

        if not self.settings:
            self.settings = file.settings
            self.param_statements = [file.header]


    def _register_aperture_macro(self, statement):
        name = statement.name
        newname = name
        offset = 0
        while newname in self.aperture_macros:
            offset += 1
            newname = '%s_%d' % (name, offset)
        statement.name = newname
        self.aperture_macros[newname] = statement
        return newname

    def _register_aperture(self, statement):
        statement.d = len(self.apertures) + self.APERTURE_ID_BIAS
        self.apertures.append(statement)
        return statement.d

class DrillComposition(Composition):
    def __init__(self, settings=None, comments=None):
        super(DrillComposition, self).__init__(settings, comments)
        self.header1_statements = []
        self.header2_statements = []
        self.tools = []
        self.hits = []
        self.dxf_statements = []
    
    def merge(self, file):
        if isinstance(file, gerberex.excellon.ExcellonFileEx):
            self._merge_excellon(file)
        elif isinstance(file, gerberex.DxfFile):
            self._merge_dxf(file)
        else:
            raise Exception('unsupported file type')

    def dump(self, path):
        def statements():
            for s in self.header1_statements:
                yield s.to_excellon(self.settings)
            for t in self.tools:
                yield t.to_excellon(self.settings)
            for s in self.header2_statements:
                yield s.to_excellon(self.settings)
            for t in self.tools:
                yield ToolSelectionStmt(t.number).to_excellon(self.settings)
                for h in self.hits:
                    if h.tool.number == t.number:
                        yield CoordinateStmt(*h.position).to_excellon(self.settings)
                for num, statement in self.dxf_statements:
                    if num == t.number:
                        yield statement.to_excellon(self.settings)
            yield EndOfProgramStmt().to_excellon()
        
        with open(path, 'w') as f:
            for statement in statements():
                f.write(statement + '\n')

    def _merge_excellon(self, file):
        tool_map = {}

        if not self.settings:
            self.settings = file.settings
        else:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        if not self.header1_statements:
            in_header1 = True
            for statement in file.statements:
                if not isinstance(statement, ToolSelectionStmt):
                    if isinstance(statement, ExcellonTool):
                        in_header1 = False
                    else:
                        if in_header1:
                            self.header1_statements.append(statement)
                        else:
                            self.header2_statements.append(statement)
                else:
                    break
        
        for tool in iter(file.tools.values()):
            num = tool.number
            tool_map[num] = self._register_tool(tool)
        
        for hit in file.hits:
            hit.tool = tool_map[hit.tool.number]
            self.hits.append(hit)
    
    def _merge_dxf(self, file):
        if not self.settings:
            self.settings = file.settings
        else:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        if not self.header1_statements:
            self.header1_statements = [file.header]
            self.header2_statements = [file.header2]
        
        tool = self._register_tool(ExcellonTool(self.settings, number=1, diameter=file.width))
        self.dxf_statements.append((tool.number, file.statements))

    def _register_tool(self, tool):
        for existing in self.tools:
            if existing.equivalent(tool):
                return existing
        new_tool = ExcellonTool.from_tool(tool)
        new_tool.settings = self.settings
        def toolnums():
            for tool in self.tools:
                yield tool.number
        max_num = reduce(lambda x, y: x if x > y else y, toolnums(), 0)
        new_tool.number = max_num + 1
        self.tools.append(new_tool)
        return new_tool

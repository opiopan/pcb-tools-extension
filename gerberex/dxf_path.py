#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from gerber.utils import inch, metric, write_gerber_value
from gerber.cam import FileSettings
from gerberex.utility import is_equal_point, is_equal_value

class DxfPath(object):
    def __init__(self, statement, error_range=0):
        self.statements = [statement]
        self.error_range = error_range
    
    @property
    def start(self):
        return self.statements[0].start
    
    @property
    def end(self):
        return self.statements[-1].end

    @property
    def is_closed(self):
        return len(self.statements) > 1 and \
               is_equal_point(self.start, self.end, self.error_range)
    
    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfPath):
            return False
        if len(self.statements) != len(target.statements):
            return False
        if is_equal_point(self.start, target.start, error_range) and \
           is_equal_point(self.end, target.end, error_range):
            for i in range(0, len(self.statements)):
               if not self.statements[i].is_equal_to(target.statements[i], error_range):
                   return False
            return True
        elif is_equal_point(self.start, target.end, error_range) and \
             is_equal_point(self.end, target.start, error_range):
            for i in range(0, len(self.statements)):
               if not self.statements[i].is_equal_to(target.statements[-1 - i], error_range):
                   return False
            return True
        return False

    def to_inch(self):
        self.error_range = inch(self.error_range)

    def to_metric(self):
        self.error_range = metric(self.error_range)

    def reverse(self):
        rlist = []
        for statement in reversed(self.statements):
            statement.reverse()
            rlist.append(statement)
        self.statements = rlist
    
    def merge(self, element, error_range=0):
        if self.is_closed or element.is_closed:
            return False
        if not error_range:
            error_range = self.error_range
        if is_equal_point(self.end, element.start, error_range):
            return self._append_at_end(element, error_range)
        elif is_equal_point(self.end, element.end, error_range):
            element.reverse()
            return self._append_at_end(element, error_range)
        elif is_equal_point(self.start, element.end, error_range):
            return self._insert_on_top(element, error_range)
        elif is_equal_point(self.start, element.start, error_range):
            element.reverse()
            return self._insert_on_top(element, error_range)
        else:
            return False
    
    def _append_at_end(self, element, error_range=0):
        if isinstance(element, DxfPath):
            if self.is_equal_to(element, error_range):
                return False
            for i in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[-1 - i].is_equal_to(element.statements[i]):
                    break
            for j in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[j].is_equal_to(element.statements[-1 - j]):
                    break
            if i + j >= len(element.statements):
                return False
            mergee = list(element.statements)
            if i > 0:
                del mergee[0:i]
                del self.statements[-i]
            if j > 0:
                del mergee[-j]
                del self.statements[0:j]
            self.statements.extend(mergee)
            return True
        else:
            if self.statements[-1].is_equal_to(element, error_range) or \
               self.statements[0].is_equal_to(element, error_range):
                return False
            self.statements.appen(element)
            return True

    def _insert_on_top(self, element, error_range=0):
        if isinstance(element, DxfPath):
            if self.is_equal_to(element, error_range):
                return False
            for i in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[-1 - i].is_equal_to(element.statements[i]):
                    break
            for j in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[j].is_equal_to(element.statements[-1 - j]):
                    break
            if i + j >= len(element.statements):
                return False
            mergee = list(element.statements)
            if i > 0:
                del mergee[0:i]
                del self.statements[-i]
            if j > 0:
                del mergee[-j]
                del self.statements[0:j]
            self.statements[0:0] = mergee
            return True
        else:
            if self.statements[-1].is_equal_to(element, error_range) or \
               self.statements[0].is_equal_to(element, error_range):
                return False
            self.statements.insert(0, element)
            return True

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        from gerberex.dxf import DxfArcStatement
        if pitch:
            return

        x0, y0 = self.statements[0].start
        gerber = 'G01*\nX{0}Y{1}D02*\nG75*'.format(
            write_gerber_value(x0, settings.format,
                               settings.zero_suppression),
            write_gerber_value(y0, settings.format,
                               settings.zero_suppression),
        )

        for statement in self.statements:
            x0, y0 = statement.start
            x1, y1 = statement.end
            if isinstance(statement, DxfArcStatement):
                xc, yc = statement.center
                gerber += '\nG{0}*\nX{1}Y{2}I{3}J{4}D01*'.format(
                    '03' if statement.end_angle > statement.start_angle else '02',
                    write_gerber_value(x1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(y1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(xc - x0, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(yc - y0, settings.format,
                                       settings.zero_suppression)
                )
            else:
                gerber += '\nG01*\nX{0}Y{1}D01*'.format(
                    write_gerber_value(x1, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(y1, settings.format,
                                       settings.zero_suppression),
                )

        return gerber

def generate_closed_paths(statements, error_range=0):
    from gerberex.dxf import DxfLineStatement, DxfArcStatement

    unique_statements = []
    redundant = 0
    for statement in statements:
        for target in unique_statements:
            if not isinstance(statement, DxfLineStatement) and \
               not isinstance(statement, DxfArcStatement):
                break
            if statement.is_equal_to(target, error_range):
                redundant += 1
                break
        else:
            unique_statements.append(statement)

    paths = [DxfPath(s, error_range) for s in unique_statements]

    prev_paths_num = 0
    while prev_paths_num != len(paths):
        working = []
        for i in range(len(paths)):
            mergee = paths[i]
            for j in range(i + 1, len(paths)):
                target = paths[j]
                if target.merge(mergee, error_range):
                    break
            else:
                working.append(mergee)
        prev_paths_num = len(paths)
        paths = working
    return list(filter(lambda p: p.is_closed, paths))
    

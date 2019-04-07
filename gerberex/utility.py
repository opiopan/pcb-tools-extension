#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from math import cos, sin, pi

def rotate(x, y, angle, center):
    x0 = x - center[0]
    y0 = y - center[1]
    angle = angle * pi / 180.0
    return (cos(angle) * x0 - sin(angle) * y0 + center[0],
            sin(angle) * x0 + cos(angle) * y0 + center[1])

def is_equal_value(a, b, error_range=0):
    return (a - b) * (a - b) <= error_range * error_range

def is_equal_point(a, b, error_range=0):
    return is_equal_value(a[0], b[0], error_range) and \
        is_equal_value(a[1], b[1], error_range)

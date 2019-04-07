#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import os
import unittest
import gerberex


class TestExcellon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))
        cls.INDIR = 'data'
        cls.OUTDIR = 'outputs'
        cls.EXPECTSDIR = 'expects'
        cls.OUTPREFIX = 'excellon_'
        cls.METRIC_FILE = os.path.join(cls.INDIR, 'ref_drill_metric.txt')
        cls.INCH_FILE = os.path.join(cls.INDIR, 'ref_drill_inch.txt')
        try:
            os.mkdir(cls.OUTDIR)
        except FileExistsError:
            pass

    def _checkResult(self, file):
        with open(file, 'r') as f:
            data = f.read()
        with open(os.path.join(self.EXPECTSDIR, os.path.basename(file)), 'r') as f:
            expect = f.read()
        self.assertEqual(data, expect)
        pass

    def test_save(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'save.txt')
        drill = gerberex.read(self.METRIC_FILE)
        drill.write(outfile)
        self._checkResult(outfile)

    def test_to_inch(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'to_inch.txt')
        drill = gerberex.read(self.METRIC_FILE)
        drill.to_inch()
        drill.format = (2, 4)
        drill.write(outfile)
        self._checkResult(outfile)

    def test_to_metric(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'to_metric.txt')
        drill = gerberex.read(self.INCH_FILE)
        drill.to_metric()
        drill.format = (3, 3)
        drill.write(outfile)
        self._checkResult(outfile)

    def test_offset(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'offset.txt')
        drill = gerberex.read(self.METRIC_FILE)
        drill.offset(11, 5)
        drill.write(outfile)
        self._checkResult(outfile)

    def test_rotate(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'rotate.txt')
        drill = gerberex.read(self.METRIC_FILE)
        drill.rotate(20, (10, 10))
        drill.write(outfile)
        self._checkResult(outfile)


if __name__ == '__main__':
    unittest.main()

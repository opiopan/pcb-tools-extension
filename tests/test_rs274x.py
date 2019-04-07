#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import os
import unittest
import gerberex

class TestRs274x(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.dirname(__file__))
        cls.INDIR = 'data'
        cls.OUTDIR = 'outputs'
        cls.EXPECTSDIR = 'expects'
        cls.OUTPREFIX = 'RS2724x_'
        cls.METRIC_FILE = os.path.join(cls.INDIR, 'ref_gerber_metric.gtl')
        cls.INCH_FILE = os.path.join(cls.INDIR, 'ref_gerber_inch.gtl')
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

    def test_save(self):
        outfile=os.path.join(self.OUTDIR, self.OUTPREFIX + 'save.gtl')
        gerber = gerberex.read(self.METRIC_FILE)
        gerber.write(outfile)
        self._checkResult(outfile)

    def test_to_inch(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'to_inch.gtl')
        gerber = gerberex.read(self.METRIC_FILE)
        gerber.to_inch()
        gerber.format = (2,5)
        gerber.write(outfile)
        self._checkResult(outfile)

    def test_to_metric(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'to_metric.gtl')
        gerber = gerberex.read(self.INCH_FILE)
        gerber.to_metric()
        gerber.format = (3, 4)
        gerber.write(outfile)
        self._checkResult(outfile)

    def test_offset(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'offset.gtl')
        gerber = gerberex.read(self.METRIC_FILE)
        gerber.offset(11, 5)
        gerber.write(outfile)
        self._checkResult(outfile)

    def test_rotate(self):
        outfile = os.path.join(self.OUTDIR, self.OUTPREFIX + 'rotate.gtl')
        gerber = gerberex.read(self.METRIC_FILE)
        gerber.rotate(20, (10,10))
        gerber.write(outfile)
        self._checkResult(outfile)

if __name__ == '__main__':
    unittest.main()

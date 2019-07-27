#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import unittest
from gerberex.am_expression import *
from gerberex.am_expression import AMOperatorExpression as Op
from gerber.utils import inch, metric
from gerber.am_read import read_macro

class TestAMConstantExpression(unittest.TestCase):
    def setUp(self):
        self.const_int_value = 7
        self.const_int = AMConstantExpression(self.const_int_value)
        self.const_float_value = 1.2345
        self.const_float = AMConstantExpression(self.const_float_value)

    def test_contruct(self):
        self.assertEqual(self.const_int.value, self.const_int_value)
        self.assertEqual(self.const_float.value, self.const_float_value)

    def test_optimize(self):
        ov = self.const_int.optimize()
        self.assertEqual(ov.value, self.const_int_value)
        ov = self.const_float.optimize()
        self.assertEqual(ov.value, self.const_float_value)
    
    def test_to_gerber(self):
        self.assertEqual(self.const_int.to_gerber(), '7.000000')
        self.assertEqual(self.const_float.to_gerber(), '1.234500')

    def test_to_instructions(self):
        self.const_int.to_instructions()
        self.const_float.to_instructions()

class TestAMVariableExpression(unittest.TestCase):
    def setUp(self):
        self.var1_num = 1
        self.var1 = AMVariableExpression(self.var1_num)
        self.var2_num = 512
        self.var2 = AMVariableExpression(self.var2_num)

    def test_construction(self):
        self.assertEqual(self.var1.number, self.var1_num)
        self.assertEqual(self.var2.number, self.var2_num)
    
    def test_optimize(self):
        ov = self.var1.optimize()
        self.assertTrue(isinstance(ov, AMVariableExpression))
        self.assertEqual(ov.number, self.var1_num)
        ov = self.var2.optimize()
        self.assertTrue(isinstance(ov, AMVariableExpression))
        self.assertEqual(ov.number, self.var2_num)

    def test_to_gerber(self):
        self.assertEqual(self.var1.to_gerber(), '$1')
        self.assertEqual(self.var2.to_gerber(), '$512')

    def test_to_instructions(self):
        self.var1.to_instructions()
        self.var2.to_instructions()

class TestAMOperatorExpression(unittest.TestCase):
    def setUp(self):
        self.c1 = 10
        self.c2 = 20
        self.v1 = 5
        self.v2 = 9
        c1 = AMConstantExpression(self.c1)
        c2 = AMConstantExpression(self.c2)
        v1 = AMVariableExpression(self.v1)
        v2 = AMVariableExpression(self.v2)

        self.cc_exps = [
            (Op.ADD, AMOperatorExpression(Op.ADD, c1, c2)),
            (Op.SUB, AMOperatorExpression(Op.SUB, c1, c2)),
            (Op.MUL, AMOperatorExpression(Op.MUL, c1, c2)),
            (Op.DIV, AMOperatorExpression(Op.DIV, c1, c2)),
        ]

        self.cv_exps = [
            (Op.ADD, AMOperatorExpression(Op.ADD, c1, v2)),
            (Op.SUB, AMOperatorExpression(Op.SUB, c1, v2)),
            (Op.MUL, AMOperatorExpression(Op.MUL, c1, v2)),
            (Op.DIV, AMOperatorExpression(Op.DIV, c1, v2)),
        ]
        self.vc_exps = [
            (Op.ADD, AMOperatorExpression(Op.ADD, v1, c2)),
            (Op.SUB, AMOperatorExpression(Op.SUB, v1, c2)),
            (Op.MUL, AMOperatorExpression(Op.MUL, v1, c2)),
            (Op.DIV, AMOperatorExpression(Op.DIV, v1, c2)),
        ]

        self.composition = AMOperatorExpression(Op.ADD, 
                                                self.cc_exps[0][1], self.cc_exps[0][1])
    
    def test_optimize(self):
        self.assertEqual(self.cc_exps[0][1].optimize().value, self.c1 + self.c2)
        self.assertEqual(self.cc_exps[1][1].optimize().value, self.c1 - self.c2)
        self.assertEqual(self.cc_exps[2][1].optimize().value, self.c1 * self.c2)
        self.assertEqual(self.cc_exps[3][1].optimize().value, self.c1 / self.c2)

        for op, expression in self.cv_exps:
            o = expression.optimize()
            self.assertTrue(isinstance(o, AMOperatorExpression))
            self.assertEqual(o.op, op)
            self.assertEqual(o.lvalue.value, self.c1)
            self.assertEqual(o.rvalue.number, self.v2)
        
        for op, expression in self.vc_exps:
            o = expression.optimize()
            self.assertTrue(isinstance(o, AMOperatorExpression))
            self.assertEqual(o.op, op)
            self.assertEqual(o.lvalue.number, self.v1)
            self.assertEqual(o.rvalue.value, self.c2)

        self.assertEqual(self.composition.optimize().value, (self.c1 + self.c2) * 2)

    def test_to_gerber(self):
        for op, expression in self.cc_exps:
            self.assertEqual(expression.to_gerber(),
                             '(%.6f)%s(%.6f)' % (self.c1, op, self.c2))
        for op, expression in self.cv_exps:
            self.assertEqual(expression.to_gerber(),
                             '(%.6f)%s($%d)' % (self.c1, op, self.v2))
        for op, expression in self.vc_exps:
            self.assertEqual(expression.to_gerber(),
                             '($%d)%s(%.6f)' % (self.v1, op, self.c2))
        self.assertEqual(self.composition.to_gerber(), 
                         '((%.6f)+(%.6f))+((%.6f)+(%.6f))' % (
                             self.c1, self.c2, self.c1, self.c2
                         ))
    
    def test_to_instructions(self):
        for of, expression in self.vc_exps + self.cv_exps + self.cc_exps:
            expression.to_instructions()
        self.composition.to_instructions()

class TestAMExpression(unittest.TestCase):
    def setUp(self):
        self.c1 = 10
        self.c1_exp = AMConstantExpression(self.c1)
        self.v1 = 5
        self.v1_exp = AMVariableExpression(self.v1)
        self.op_exp = AMOperatorExpression(Op.ADD, self.c1_exp, self.v1_exp)

    def test_to_inch(self):
        o = self.c1_exp.to_inch().optimize()
        self.assertEqual(o.value, inch(self.c1))
        o = self.v1_exp.to_inch().optimize()
        self.assertTrue(isinstance(o, AMOperatorExpression))
        self.assertEqual(o.op, Op.DIV)
        o = self.op_exp.to_inch().optimize()
        self.assertTrue(isinstance(o, AMOperatorExpression))
        self.assertEqual(o.op, Op.DIV)

    def test_to_metric(self):
        o = self.c1_exp.to_metric().optimize()
        self.assertEqual(o.value, metric(self.c1))
        o = self.v1_exp.to_metric().optimize()
        self.assertTrue(isinstance(o, AMOperatorExpression))
        self.assertEqual(o.op, Op.MUL)
        o = self.op_exp.to_metric().optimize()
        self.assertTrue(isinstance(o, AMOperatorExpression))
        self.assertEqual(o.op, Op.MUL)

class TestEvalMacro(unittest.TestCase):
    def test_eval_macro(self):
        macros = [
            ('$1=5.5*', '$1=5.500000*'),
            ('$1=0.0000001*', '$1=0.000000*'),
            ('$2=$3*', '$2=$3*'),
            ('$3=(1.23)+(4.56)*', '$3=(1.230000)+(4.560000)*'),
            ('$3=(1.23)-(4.56)*', '$3=(1.230000)-(4.560000)*'),
            ('$3=(1.23)X(4.56)*', '$3=(1.230000)X(4.560000)*'),
            ('$3=(1.23)/(4.56)*', '$3=(1.230000)/(4.560000)*'),
            ('$3=(10.2)X($2)*', '$3=(10.200000)X($2)*'),
            ('1,1.2*', '1,1.200000*'),
            ('1,$2*', '1,$2*'),
            ('1,($2)+($3)*', '1,($2)+($3)*'),
            #('1,(2.0)-($3)*', '1,(2.0)-($3)*'),  # This doesn't pass due to pcb-tools bug
            ('1,($2)X($3)*', '1,($2)X($3)*'),
            ('1,($2)/($3)*', '1,($2)/($3)*'),
            ('1,2.1,3.2*2,(3.1)/($1),$2*', '1,2.100000,3.200000*2,(3.100000)/($1),$2*'),
        ]
        for macro, expected in macros:
            self._eval_macro_string(macro, expected)

    def _eval_macro_string(self, macro, expected):
        expressions = eval_macro(read_macro(macro))
        gerber = self._to_gerber(expressions)
        self.assertEqual(gerber, expected)

    def _to_gerber(self, expressions_list):
        gerber = ''
        for number, expressions in expressions_list:
            self.assertTrue(isinstance(number, int))
            if number > 0:
                egerbers = [exp.to_gerber() for exp in expressions]
                gerber += '{0},{1}*'.format(number, ','.join(egerbers))
            else:
                self.assertEqual(len(expressions), 1)
                gerber += '${0}={1}*'.format(-number, expressions[0].to_gerber())
        return gerber

if __name__ == '__main__':
    unittest.main()

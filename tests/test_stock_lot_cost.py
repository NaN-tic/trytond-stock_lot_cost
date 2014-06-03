#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    '''
    Test module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_lot_cost')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.category = POOL.get('product.category')
        self.uom = POOL.get('product.uom')
        self.model_data = POOL.get('ir.model.data')
        self.lot = POOL.get('stock.lot')
        self.lot_cost_line = POOL.get('stock.lot.cost_line')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('stock_lot_cost')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test0010lot_cost_price(self):
        '''
        Test Lot.cost_price.
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            category, = self.category.create([{
                        'name': 'Test Lot.cost_price',
                        }])
            kg, = self.uom.search([('name', '=', 'Kilogram')])
            g, = self.uom.search([('name', '=', 'Gram')])
            template, = self.template.create([{
                        'name': 'Test Lot.cost_price',
                        'type': 'goods',
                        'list_price': Decimal(20),
                        'cost_price': Decimal(10),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': kg.id,
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])
            lot_cost_category_id = self.model_data.get_id('stock_lot_cost',
                'cost_category_standard_price')

            lot = self.lot(
                number='1',
                product=product.id
                )
            lot.save()

            # Lot.product.on_change test
            lot_vals = lot.on_change_product()
            lot_vals['cost_lines'] = [(k.replace('add', 'create'), [value])
                for (k, v) in lot_vals['cost_lines'].iteritems()
                for _, value in v]
            self.lot.write([lot], lot_vals)
            self.assertEqual(lot.cost_price, template.cost_price)

            self.lot_cost_line.create([{
                        'lot': lot.id,
                        'category': lot_cost_category_id,
                        'unit_price': Decimal(3),
                        }, {
                        'lot': lot.id,
                        'category': lot_cost_category_id,
                        'unit_price': Decimal(2),
                        }])
            self.assertEqual(lot.cost_price, Decimal(15))


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite

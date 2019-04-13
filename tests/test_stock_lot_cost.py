#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class TestCase(ModuleTestCase):
    'Test module'
    module = 'stock_lot_cost'

    @with_transaction()
    def test0010lot_cost_price(self):
        'Test Lot.cost_price'
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        ModelData = pool.get('ir.model.data')
        Lot = pool.get('stock.lot')
        LotCostLine = pool.get('stock.lot.cost_line')

        kg, = Uom.search([('name', '=', 'Kilogram')])
        g, = Uom.search([('name', '=', 'Gram')])
        template, = Template.create([{
                    'name': 'Test Lot.cost_price',
                    'type': 'goods',
                    'list_price': Decimal(20),
                    'cost_price_method': 'fixed',
                    'default_uom': kg.id,
                    }])
        product, = Product.create([{
                    'template': template.id,
                    'cost_price': Decimal(10),
                    }])
        lot_cost_category_id = ModelData.get_id('stock_lot_cost',
            'cost_category_standard_price')

        lot = Lot(
            number='1',
            product=product.id
            )
        lot.save()

        # Lot.product.on_change test
        lot_vals = lot._on_change_product_cost_lines()
        values = {}
        for (k, v) in lot_vals.items():
            vals = v[0][1]
            values['cost_lines'] = [(k.replace('add', 'create'),
                    [vals])]
        Lot.write([lot], values)
        self.assertEqual(lot.cost_price, template.cost_price)

        LotCostLine.create([{
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

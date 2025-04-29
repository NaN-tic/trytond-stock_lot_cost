
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import (
    CompanyTestMixin, create_company, set_company)
from trytond.pool import Pool


class StockLotCostTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockLotCost module'
    module = 'stock_lot_cost'
    extras = ['production']

    @with_transaction()
    def test_move_production(self):
        'Test products_by_location'
        pool = Pool()
        Uom = pool.get('product.uom')
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Location = pool.get('stock.location')
        Move = pool.get('stock.move')
        Lot = pool.get('stock.lot')
        Date = pool.get('ir.date')

        unit, = Uom.search([('name', '=', 'Unit')])
        today = Date.today()

        template1, template2 = Template.create([{
                    'name': 'Test1',
                    'type': 'goods',
                    'default_uom': unit.id,
                    }, {
                    'name': 'Test2',
                    'type': 'goods',
                    'default_uom': unit.id,
                    }])
        product1, = Product.create([{
                    'template': template1.id,
                    }])
        product2, = Product.create([{
                    'template': template2.id,
                    }])
        supplier, = Location.search([('code', '=', 'SUP')])
        customer, = Location.search([('code', '=', 'CUS')])
        storage, = Location.search([('code', '=', 'STO')])
        production, = Location.search([('type', '=', 'production')])

        company = create_company()
        currency = company.currency
        with set_company(company):
            lot1, lot2 = Lot.create([{
                        'number': '1',
                        'product': product1.id,
                        }, {
                        'number': '2',
                        'product': product1.id,
                        }])

            moves = Move.create([{
                        'product': product1.id,
                        'lot': lot1.id,
                        'unit': unit.id,
                        'quantity': 5,
                        'from_location': supplier.id,
                        'to_location': storage.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }, {
                        'product': product1.id,
                        'lot': lot2.id,
                        'unit': unit.id,
                        'quantity': 10,
                        'from_location': supplier.id,
                        'to_location': storage.id,
                        'company': company.id,
                        'unit_price': Decimal('1.2'),
                        'currency': currency.id,
                        }, {
                        'product': product2.id,
                        'unit': unit.id,
                        'quantity': 2,
                        'from_location': storage.id,
                        'to_location': customer.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }])
            Move.do(moves)

            self.assertEqual(lot1.cost_price, Decimal('1.0000'))
            self.assertEqual(lot2.cost_price, Decimal('1.2000'))

            move = Move()
            move.from_location = storage
            move.to_location = production
            move.effective_date = Date.today()
            move.product = product1
            move.on_change_product()
            move.lot = lot1
            move.quantity = Decimal(1)
            move.save()
            Move.do([move])
            self.assertEqual(move.state, 'done')
            self.assertEqual(move.get_cost_price(), Decimal('1.0000'))

            move = Move()
            move.from_location = storage
            move.to_location = production
            move.effective_date = Date.today()
            move.product = product2
            move.on_change_product()
            move.quantity = Decimal(1)
            move.save()
            Move.do([move])
            self.assertEqual(move.state, 'done')
            self.assertEqual(move.get_cost_price(), Decimal('0.0000'))


del ModuleTestCase

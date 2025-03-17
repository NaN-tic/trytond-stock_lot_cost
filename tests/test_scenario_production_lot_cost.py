import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate modules
        activate_modules(['stock_lot_cost', 'production'])
        ProductTemplate = Model.get('product.template')
        Production = Model.get('production')
        Production = Model.get('production')
        Sequence = Model.get('ir.sequence')
        SequenceType = Model.get('ir.sequence.type')
        UoM = Model.get('product.uom')

        # Create company
        _ = create_company()
        company = get_company()

        # Create lot sequence
        sequence_type, = SequenceType.find([('name', '=', "Stock Lot")],
                                           limit=1)
        sequence = Sequence(name="Lot",
                            sequence_type=sequence_type,
                            company=None)
        sequence.save()

        # Create product
        unit, = UoM.find([('name', '=', 'Unit')])
        template = ProductTemplate(
            name='Product',
            default_uom=unit,
            type='goods',
            producible=True,
            list_price=Decimal('10.0000'),
            lot_required=['storage'],
            lot_sequence=sequence,
            )
        template.save()
        product, = template.products

        template2 = ProductTemplate(
            name='Product2',
            default_uom=unit,
            type='goods',
            producible=True,
            list_price=Decimal('10.0000'),
            )
        template2.save()
        product2, = template2.products
        product2.cost_price = Decimal('2.0000')
        product2.save()

        # Get stock locations
        Location = Model.get('stock.location')
        supplier_loc, = Location.find([('code', '=', 'SUP')])
        storage_loc, = Location.find([('code', '=', 'STO')])

        # Create lot
        Lot = Model.get('stock.lot')
        lot = Lot()
        lot.number = 'LOT'
        lot.product = product
        lot.save()

        # Create supplier moves move
        Move = Model.get('stock.move')
        move1_in = Move(
            from_location=supplier_loc,
            to_location=storage_loc,
            product=product,
            company=company,
            lot=lot,
            quantity=100,
            unit_price=Decimal('1'),
            currency=company.currency,
            )
        move1_in.save()
        move1_in.click('do')
        move2_in = Move(
            from_location=supplier_loc,
            to_location=storage_loc,
            product=product,
            company=company,
            lot=lot,
            quantity=100,
            unit_price=Decimal('2'),
            currency=company.currency,
            )
        move2_in.save()
        move2_in.click('do')

        move3_in = Move(
            from_location=supplier_loc,
            to_location=storage_loc,
            product=product2,
            company=company,
            quantity=100,
            unit_price=Decimal('3'),
            currency=company.currency,
            )
        move3_in.save()
        move3_in.click('do')

        # Check the lot costs
        lot = Lot(lot.id)
        self.assertEqual(lot.cost_price, Decimal('1.5000'))
        self.assertEqual(lot.total_cost, Decimal('300.0000'))

        # Make a production
        production = Production()
        input = production.inputs.new()
        input.from_location = production.warehouse.storage_location
        input.to_location = production.location
        input.product = product
        input.quantity = 1
        input = production.inputs.new()
        input.from_location = production.warehouse.storage_location
        input.to_location = production.location
        input.product = product2
        input.quantity = 2
        output = production.outputs.new()
        output.from_location = production.location
        output.to_location = production.warehouse.storage_location
        output.product = product
        output.quantity = 1
        output.unit_price = Decimal(0)
        output.currency = production.company.currency
        production.click('wait')

        # production cost price from product2
        self.assertEqual(production.cost, Decimal('4.0000'))
        input1, = [input for input in production.inputs if input.product == product]
        input1.lot = lot
        input1.save()

        # production cost price from product2 (product.cost_price)+ product (move.get_cost_price())
        production.reload()
        self.assertEqual(production.cost, Decimal('5.5000'))

        production.click('assign_try')
        self.assertEqual(production.state, 'assigned')
        production.click('run')
        self.assertEqual(production.state, 'running')

        input1, input2 = production.inputs
        self.assertEqual(input1.state, 'done')
        self.assertEqual(input1.cost_price, Decimal('2'))
        self.assertEqual(input2.state, 'done')
        self.assertEqual(input2.cost_price, Decimal('0'))

        # production cost price from product2 (product.cost_price)+ product (move.get_cost_price())
        production.reload()
        self.assertEqual(production.cost, Decimal('5.5000'))

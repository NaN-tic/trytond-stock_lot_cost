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
        template = ProductTemplate()
        template.name = "Product"
        template.default_uom = unit
        template.type = 'goods'
        template.producible = True
        template.list_price = Decimal('10.0000')
        template.lot_required = ['storage']
        template.lot_sequence = sequence
        template.save()
        product, = template.products

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
        move1_in = Move()
        move1_in.from_location = supplier_loc
        move1_in.to_location = storage_loc
        move1_in.product = product
        move1_in.company = company
        move1_in.lot = lot
        move1_in.quantity = 100
        move1_in.unit_price = Decimal('1')
        move1_in.currency = company.currency
        move1_in.save()
        move1_in.click('do')
        move2_in = Move()
        move2_in.from_location = supplier_loc
        move2_in.to_location = storage_loc
        move2_in.product = product
        move2_in.company = company
        move2_in.lot = lot
        move2_in.quantity = 100
        move2_in.unit_price = Decimal('2')
        move2_in.currency = company.currency
        move2_in.save()
        move2_in.click('do')

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
        output = production.outputs.new()
        output.from_location = production.location
        output.to_location = production.warehouse.storage_location
        output.product = product
        output.quantity = 1
        output.unit_price = Decimal(0)
        output.currency = production.company.currency
        production.click('wait')
        self.assertEqual(production.cost, Decimal('0.0000'))
        input, = production.inputs
        input.lot = lot
        input.save()
        production = Production(production.id)
        self.assertEqual(production.cost, Decimal('1.5000'))

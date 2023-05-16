=======================
Stock Lot Cost Scenario
=======================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal

    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import (
    ...     create_company, get_company)
    >>> today = datetime.date.today()

Activate modules::

    >>> config = activate_modules('stock_lot_cost')
    >>> Location = Model.get('stock.location')
    >>> Lot = Model.get('stock.lot')
    >>> Party = Model.get('party.party')
    >>> ProductTemplate = Model.get('product.template')
    >>> ProductUom = Model.get('product.uom')
    >>> Move = Model.get('stock.move')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create product::

    >>> unit, = ProductUom.find([('name', '=', 'Unit')])

    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product, = template.products

Get stock locations::

    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])

Create lot::

    >>> lot = Lot()
    >>> lot.number = 'LOT'
    >>> lot.product = product
    >>> lot.save()

Create supplier moves move::

    >>> move1_in = Move()
    >>> move1_in.from_location = supplier_loc
    >>> move1_in.to_location = storage_loc
    >>> move1_in.product = product
    >>> move1_in.company = company
    >>> move1_in.lot = lot
    >>> move1_in.quantity = 100
    >>> move1_in.unit_price = Decimal('1')
    >>> move1_in.save()
    >>> move1_in.click('do')

    >>> move2_in = Move()
    >>> move2_in.from_location = supplier_loc
    >>> move2_in.to_location = storage_loc
    >>> move2_in.product = product
    >>> move2_in.company = company
    >>> move2_in.lot = lot
    >>> move2_in.quantity = 100
    >>> move2_in.unit_price = Decimal('2')
    >>> move2_in.save()
    >>> move2_in.click('do')


Check the lot costs::

    >>> lot.cost_price
    Decimal('1.5000')
    >>> lot.total_cost
    Decimal('300.0000')

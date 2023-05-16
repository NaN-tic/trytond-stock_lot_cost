
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.tests.test_tryton import ModuleTestCase
from trytond.modules.company.tests import CompanyTestMixin


class StockLotCostTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockLotCost module'
    module = 'stock_lot_cost'


del ModuleTestCase

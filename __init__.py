#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
#from .product import *
from .stock import *


def register():
    Pool.register(
        LotCostCategory,
        LotCostLine,
        Lot,
        Move,
        #Product,
        module='stock_lot_cost', type_='model')

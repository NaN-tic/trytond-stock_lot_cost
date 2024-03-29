#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.pool import Pool
from . import stock

def register():
    Pool.register(
        stock.LotCostCategory,
        stock.Lot,
        stock.Move,
        module='stock_lot_cost', type_='model')

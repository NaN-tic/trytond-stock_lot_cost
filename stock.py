# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


class LotCostCategory(ModelSQL, ModelView):
    '''Stock Lot Cost Category'''
    __name__ = 'stock.lot.cost_category'

    name = fields.Char('Name', translate=True, required=True)

    @classmethod
    def __setup__(cls):
        super(LotCostCategory, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('name_uniq', Unique(t, t.name),
                'stock_lot_cost.msg_category_name_unique'),
            ]


class Lot(metaclass=PoolMeta):
    __name__ = 'stock.lot'

    cost_price = fields.Function(fields.Numeric("Cost Price"),
        'get_lot_prices')
    total_cost = fields.Function(fields.Numeric("Total Cost"),
        'get_lot_prices')

    @classmethod
    def get_lot_prices(cls, lots, names):
        pool = Pool()
        Move = pool.get('stock.move')

        res = {}
        ids = [x.id for x in lots]

        for name in ['cost_price', 'total_cost']:
            res[name] = dict.fromkeys(ids)

        for lot in lots:
            # Don't search moves where the origin is another move
            moves = Move.search([
                ('lot', '=', lot.id),
                ('origin', 'not like', 'stock.move,%'),
            ])

            total_price = Decimal(sum(
                    m.unit_price for m in moves if m.unit_price))

            total_quantity = Decimal(0)
            for move in moves:
                if move.quantity:
                    if move.to_location.type not in ['storage']:
                        total_quantity += Decimal(-move.quantity)
                    else:
                        total_quantity += Decimal(move.quantity)

            res['total_cost'][lot.id] = Decimal(0)
            res['cost_price'][lot.id] = Decimal(0)
            if total_price and total_quantity:
                res['total_cost'][lot.id] = total_price * total_quantity
                res['cost_price'][lot.id] = (
                    total_price*total_quantity/total_quantity)

        for name in list(res.keys()):
            if name not in names:
                del res[name]
        return res


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls.lot.context['from_move'] = Eval('id')

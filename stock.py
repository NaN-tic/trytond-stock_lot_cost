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

        lot_ids = list(set(lot.id for lot in lots))
        moves = Move.search([
            ('lot', 'in', lot_ids),
            ('origin', 'not like', 'stock.move,%'),
            ('from_location.type', '=', 'supplier'),
            ('to_location.type', '=', 'storage'),
            ('state', '=', 'done'),
            ])

        lot_moves = {}
        for move in moves:
            if move.lot.id not in lot_moves:
                lot_moves[move.lot.id] = []
            lot_moves[move.lot.id].append(move)

        for lot in lots:
            res['total_cost'][lot.id] = Decimal(0)
            res['cost_price'][lot.id] = Decimal(0)
            if not lot.id in lot_moves:
                continue
            total_price = Decimal(sum(Decimal(m.unit_price) * Decimal(
                m.internal_quantity) for m in lot_moves[lot.id] if (
                    m.unit_price and m.internal_quantity)))
            total_quantity = Decimal(
                sum(m.internal_quantity for m in lot_moves[lot.id]))

            res['total_cost'][lot.id] = total_price
            res['cost_price'][lot.id] = total_price/total_quantity

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

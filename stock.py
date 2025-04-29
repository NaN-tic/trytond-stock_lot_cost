# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
import datetime
from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.modules.product import round_price


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
        Product = pool.get('product.product')
        Location = pool.get('stock.location')

        res = {}
        ids = [x.id for x in lots]
        for name in ['cost_price', 'total_cost']:
            res[name] = dict.fromkeys(ids)

        warehouse_ids = [location.id for location in Location.search(
            [('type', '=', 'warehouse')])]
        product_ids = list(set(lot.product.id for lot in lots if lot.product))
        lot_ids = list(set(lot.id for lot in lots))

        moves = Move.search([
            ('lot', 'in', lot_ids),
            ('from_location.type', 'in', ['supplier', 'production']),
            ('to_location.type', '=', 'storage'),
            ('state', '=', 'done'),
            ])

        stock_date_end = Transaction().context.get('date', datetime.date.max)
        with Transaction().set_context(stock_date_end=stock_date_end):
            pbl = Product.products_by_location(warehouse_ids,
                with_childs=True,
                grouping=('product', 'lot'),
                grouping_filter=(product_ids, lot_ids))

        lot_moves = {}
        for move in moves:
            if move.lot not in lot_moves:
                lot_moves[move.lot] = []
            lot_moves[move.lot].append(move)

        for lot in lots:
            res['total_cost'][lot.id] = None
            res['cost_price'][lot.id] = None
            if not lot in lot_moves or not lot.product:
                continue

            warehouse_quantity = Decimal(0)
            for k, v in pbl.items():
                key = k[1:]
                if key == (lot.product.id, lot.id):
                    warehouse_quantity += Decimal(v)

            total_price = Decimal(sum(Decimal(m.unit_price) * Decimal(
                m.internal_quantity) for m in lot_moves[lot] if (
                    m.unit_price and m.internal_quantity)))
            total_quantity = Decimal(
                sum(m.internal_quantity for m in lot_moves[lot]))

            if not total_quantity:
                continue

            res['cost_price'][lot.id] = round_price(total_price/total_quantity)
            res['total_cost'][lot.id] = round_price(
                total_price/total_quantity) * warehouse_quantity

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

    def get_cost_price(self, product_cost_price=None):
        pool = Pool()
        Lot = pool.get('stock.lot')

        cost_price = super().get_cost_price(product_cost_price=None)

        if self.lot and self.to_location.type == 'production':
            with Transaction().set_context(date=self.effective_date):
                lot = Lot(self.lot.id) # Need to reinstantiate to ensure the context is correct
                if lot.cost_price is not None:
                    return round_price(lot.cost_price)
        return cost_price

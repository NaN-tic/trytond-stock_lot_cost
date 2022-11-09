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


class LotCostLine(ModelSQL, ModelView):
    '''Stock Lot Cost Line'''
    __name__ = 'stock.lot.cost_line'

    lot = fields.Many2One('stock.lot', 'Lot', required=True,
        ondelete='CASCADE')
    category = fields.Many2One('stock.lot.cost_category', 'Category',
        required=True)
    unit_price = fields.Numeric('Unit Price', required=True)
    origin = fields.Reference('Origin', selection='get_origin', readonly=True)

    @classmethod
    def _get_origin(cls):
        'Return list of Model names for origin Reference'
        return [
            'stock.move',
            ]

    @classmethod
    def get_origin(cls):
        pool = Pool()
        Model = pool.get('ir.model')
        models = cls._get_origin()
        models = Model.search([
                ('model', 'in', models),
                ])
        return [('', '')] + [(m.model, m.name) for m in models]


class Lot(metaclass=PoolMeta):
    __name__ = 'stock.lot'

    cost_lines = fields.One2Many('stock.lot.cost_line', 'lot', 'Cost Lines')
    cost_price = fields.Function(fields.Numeric('Cost Price'),
        'get_cost_price')

    def get_cost_price(self, name):
        if not self.cost_lines:
            return
        return sum(l.unit_price for l in self.cost_lines if l.unit_price is not
            None)

    @fields.depends('product', 'cost_lines')
    def on_change_product(self):
        try:
            super(Lot, self).on_change_product()
        except AttributeError:
            pass

        if not self.id or self.id <= 0:
            return

        cost_lines = self._on_change_product_cost_lines()
        if cost_lines:
            cost_lines = cost_lines.get('add')
            LotCostLine = Pool().get('stock.lot.cost_line')
            lot_cost_lines = LotCostLine.search([
                    ('lot', '=', self.id),
                    ('category', '=', cost_lines[0][1]['category']),
                    ('unit_price', '=', cost_lines[0][1]['unit_price']),
                    ])
            if lot_cost_lines:
                self.cost_lines = lot_cost_lines

    def _on_change_product_cost_lines(self):
        pool = Pool()
        ModelData = pool.get('ir.model.data')

        if not self.product:
            return {}

        category_id = ModelData.get_id('stock_lot_cost',
            'cost_category_standard_price')
        return {
            'add': [(0, {
                        'category': category_id,
                        'unit_price': self.product.cost_price,
                        })],
            }


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls.lot.context['from_move'] = Eval('id')

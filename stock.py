#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['LotCostCategory', 'LotCostLine', 'Lot', 'Move']
__metaclass__ = PoolMeta


class LotCostCategory(ModelSQL, ModelView):
    '''Stock Lot Cost Category'''
    __name__ = 'stock.lot.cost_category'

    name = fields.Char('Name', translate=True, required=True)

    @classmethod
    def __setup__(cls):
        super(LotCostCategory, cls).__setup__()
        cls._sql_constraints += [
            ('name_uniq', 'UNIQUE (name)',
                'The Name of the Lot Cost Category must be unique.'),
            ]


class LotCostLine(ModelSQL, ModelView):
    '''Stock Lot Cost Line'''
    __name__ = 'stock.lot.cost_line'

    lot = fields.Many2One('stock.lot', 'Lot', required=True, select=True,
        ondelete='CASCADE')
    category = fields.Many2One('stock.lot.cost_category', 'Category',
        required=True)
    unit_price = fields.Numeric('Unit Price', digits=(16, 4), required=True)
    origin = fields.Many2One('stock.move', 'Origin', readonly=True,
        select=True)


class Lot:
    __name__ = 'stock.lot'

    cost_lines = fields.One2Many('stock.lot.cost_line', 'lot', 'Cost Lines')
    cost_price = fields.Function(fields.Numeric('Cost Price', digits=(16, 4)),
        'get_cost_price')

    @classmethod
    def __setup__(cls):
        super(Lot, cls).__setup__()
        if not cls.product.on_change:
            cls.product.on_change = []
        if 'product' not in cls.product.on_change:
            cls.product.on_change.append('product')
        cls.product.on_change.append('cost_lines')

    def get_cost_price(self, name):
        return sum(l.unit_price for l in self.cost_lines)

    def on_change_product(self):
        try:
            result = super(Lot, self).on_change_product()
        except AttributeError:
            result = {}

        cost_lines = self._on_change_product_cost_lines()
        if cost_lines:
            result['cost_lines'] = cost_lines
        return result

    def _on_change_product_cost_lines(self):
        pool = Pool()
        ModelData = pool.get('ir.model.data')

        if not self.product:
            return None

        category_id = ModelData.get_id('stock_lot_cost',
            'cost_category_standard_price')
        return {
            'add': [{
                    'category': category_id,
                    'unit_price': self.product.cost_price,
                    }],
            }


class Move:
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls.lot.context['from_move'] = Eval('id')

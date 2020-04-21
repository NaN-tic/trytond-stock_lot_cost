# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.modules.product import price_digits

__all__ = ['LotCostCategory', 'LotCostLine', 'Lot', 'Move', 'Product',
    'Location']


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

    lot = fields.Many2One('stock.lot', 'Lot', required=True, select=True,
        ondelete='CASCADE')
    category = fields.Many2One('stock.lot.cost_category', 'Category',
        required=True)
    unit_price = fields.Numeric('Unit Price', digits=price_digits,
        required=True)
    origin = fields.Reference('Origin', selection='get_origin', readonly=True,
        select=True)

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
    cost_price = fields.Function(fields.Numeric('Cost Price',
            digits=price_digits),
        'get_cost_price')

    def get_cost_price(self, name):
        return (sum(l.unit_price or 0 for l in self.cost_lines)
            if self.cost_lines else None)

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


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    @classmethod
    def get_cost_value(cls, products, name):
        pool = Pool()
        Lot = pool.get('stock.lot')

        product_by_id = dict((p.id, p) for p in products)
        cost_values = {}.fromkeys(product_by_id.keys(), None)

        context = {}
        trans_context = Transaction().context
        if 'stock_date_end' in context:
            context['_datetime'] = trans_context['stock_date_end']
        location_ids = trans_context.get('locations')
        with Transaction().set_context(context):
            pbl = cls.products_by_location(location_ids=location_ids,
                grouping_filter=(list(product_by_id.keys()),), with_childs=True,
                grouping=('product', 'lot'))

            for (location_id, product_id, lot_id), qty in pbl.items():
                cost_value = None
                if lot_id:
                    lot = Lot(lot_id)
                    if isinstance(lot.cost_price, Decimal):
                        cost_value = (Decimal(str(qty)) * lot.cost_price)
                else:
                    product = product_by_id[product_id]
                    if isinstance(product.cost_price, Decimal):
                        cost_value = (Decimal(str(qty)) * product.cost_price)

                if cost_value is not None:
                    if cost_values[product_id] is not None:
                        cost_value += cost_values[product_id]
                    cost_values[product_id] = cost_value
        return cost_values


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'

    @classmethod
    def get_cost_value(cls, locations, name):
        pool = Pool()
        Lot = pool.get('stock.lot')
        Product = pool.get('product.product')

        trans_context = Transaction().context
        product_id = trans_context.get('product')
        lot_id = trans_context.get('lot')
        if not product_id and not lot_id:
            return dict((l.id, None) for l in locations)

        cost_values, context = {}, {}
        if 'stock_date_end' in context:
            context['_datetime'] = trans_context['stock_date_end']
        with Transaction().set_context(context):
            if lot_id:
                lot = Lot(lot_id)
                for location in locations:
                    # The date could be before the product creation
                    if not isinstance(lot.cost_price, Decimal):
                        cost_values[location.id] = None
                    else:
                        cost_values[location.id] = (
                            Decimal(str(location.quantity)) * lot.cost_price)
            else:
                product = Product(product_id)
                pbl = Product.products_by_location(
                    location_ids=[l.id for l in locations],
                    grouping_filter=([product_id],), with_childs=True,
                    grouping=('product', 'lot'))

                cost_values = dict((l.id, None) for l in locations)
                for key, qty in pbl.items():
                    if len(key) != 3:
                        continue
                    location_id, product_id, lot_id = key
                    cost_value = None
                    if lot_id:
                        lot = Lot(lot_id)
                        if isinstance(lot.cost_price, Decimal):
                            cost_value = (Decimal(str(qty)) * lot.cost_price)
                    else:
                        if isinstance(product.cost_price, Decimal):
                            cost_value = (Decimal(str(qty))
                                * product.cost_price)

                    if cost_value is not None:
                        if cost_values[location_id] is not None:
                            cost_value += cost_values[location_id]
                        cost_values[location_id] = cost_value
        return cost_values

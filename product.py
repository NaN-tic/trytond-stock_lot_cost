#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from decimal import Decimal

from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Product']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.product'

    #@classmethod
    #def get_cost_value(cls, products, name):
    #    pool = Pool()
    #    Location = pool.get('stock.lot')
    #    Lot = pool.get('stock.lot')

    #    lot_products = []
    #    no_lot_products = []
    #    for product in products:
    #        if 'storage' in [t.code for t in product.lot_required]:
    #            lot_products.append(product)
    #        else:
    #            no_lot_products.append(product)

    #    cost_values = super(Product, cls).get_cost_value(no_lot_products, name)
    #    if not lot_products:
    #        return cost_values

    #    context = {}
    #    trans_context = Transaction().context
    #    if 'stock_date_end' in trans_context:
    #        context['stock_date_end'] = trans_context['stock_date_end']
    #        context['_datetime'] = trans_context['stock_date_end']
    #        context['forecast'] = trans_context.get('forecast')

    #    location_ids = trans_context.get('locations')
    #    with_childs = False
    #    if not location_ids:
    #        warehouses = Location.search([('type', '=', 'warehouse')])
    #        location_ids = [w.storage_location.id for w in warehouses]
    #        with_childs = True

    #    with Transaction().set_context(context):
    #        pbl = cls.products_by_location(location_ids,
    #            product_ids=[p.id for p in lot_products],
    #            with_childs=with_childs,
    #            grouping=('product', 'lot'))

    #        for product in lot_products:
    #            if not pbl[product.id]:
    #                cost_values[product.id] = None
    #            else:
    #                cost_values[product.id] = Decimal('0.0')
    #                for lot_id, qty in pbl[product.id].items():
    #                    lot = Lot(lot_id)
    #                    cost_values[product.id] += (Decimal(str(qty))
    #                        * lot.cost_price)
    #    return cost_values

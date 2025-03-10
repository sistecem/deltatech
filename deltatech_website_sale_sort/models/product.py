# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging
from datetime import time, timedelta

from odoo import api, fields, models
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # the standard field sales_count is not store
    # urmatoarele campuri sunt caclulata prin cron

    sales_count2 = fields.Float(string="Sold2", store=True)
    visit_count = fields.Integer(string="Visits", store=True)
    comment_count = fields.Integer(string="Comments")

    rating_count2 = fields.Integer("Rating count2")
    rating_avg2 = fields.Float("Rating Average2")
    in_stock = fields.Boolean()
    price_from_pricelist = fields.Float(string="Price from pricelist")

    def _update_statistics(self):
        domain = [("res_model", "=", self._name), ("res_id", "in", self.ids), ("consumed", "=", True)]
        read_group_res = self.env["rating.rating"].read_group(
            domain, ["rating:avg"], groupby=["res_id"], lazy=False
        )  # force average on rating column
        mapping = {
            item["res_id"]: {"rating_count": item["__count"], "rating_avg": item["rating"]} for item in read_group_res
        }

        for record in self:
            sales_count2 = sum(p.sales_count2 for p in record.with_context(active_test=False).product_variant_ids)
            visit_count = sum(p.visit_count for p in record.with_context(active_test=False).product_variant_ids)
            rating_count2 = mapping.get(record.id, {}).get("rating_count", 0)
            rating_avg2 = mapping.get(record.id, {}).get("rating_avg", 0)
            record.write(
                {
                    "sales_count2": sales_count2,
                    "visit_count": visit_count,
                    "rating_count2": rating_count2,
                    "rating_avg2": rating_avg2,
                    "in_stock": record.qty_available > 0,
                }
            )

    @api.model
    def _cron_update_statistics(self):
        self.env["product.product"]._cron_update_statistics()
        products = self.search([])
        products._update_statistics()

    def set_pricelist_price(self):
        self.product_variant_ids.set_pricelist_price()


class ProductProduct(models.Model):
    _inherit = "product.product"

    sales_count2 = fields.Float(string="Sold2", store=True)
    visit_count = fields.Integer(string="Visits", store=True)
    price_from_pricelist = fields.Float(string="Price from pricelist (tax included)")

    def _update_statistics(self):
        date_from = fields.Datetime.to_string(
            fields.datetime.combine(fields.datetime.now() - timedelta(days=365), time.min)
        )

        done_states = self.env["sale.report"]._get_done_states()

        domain = [
            ("state", "in", done_states),
            ("product_id", "in", self.ids),
            ("date", ">=", date_from),
        ]

        results = self.env["sale.report"].read_group(domain, ["product_id", "product_uom_qty"], ["product_id"])

        sale_mapping = {item["product_id"]: {"sales_count": item["product_uom_qty"]} for item in results}

        results = self.env["website.track"].read_group(
            domain=[("product_id", "!=", False)],
            fields=["product_id", "id:count_distinct"],
            groupby=["product_id"],
            lazy=False,
        )
        visit_mapping = {item["product_id"]: {"visit_count": item["__count"]} for item in results}

        for product in self:
            visit_count = visit_mapping.get(product.id, {}).get("visit_count", 0)
            sales_count2 = float_round(sale_mapping.get(product.id, 0), precision_rounding=product.uom_id.rounding)
            product.write({"visit_count": visit_count, "sales_count2": sales_count2})

    @api.model
    def _cron_update_statistics(self):
        products = self.search([])
        products._update_statistics()

    def set_pricelist_price(self):
        pricelist_id = self.env["ir.config_parameter"].sudo().get_param("sale.product_price_pricelist")
        with_taxes = self.env["ir.config_parameter"].sudo().get_param("sale.price_from_pricelist_taxes")
        if pricelist_id:
            pricelist = self.env["product.pricelist"].browse(int(pricelist_id))
            quantities = [1] * len(self)
            partners = [False] * len(self)
            prices = pricelist.get_products_price(self, quantities, partners)
            for product in self:
                pricelist_price = prices.get(product.id, 0.0)

                # get taxes
                if with_taxes:
                    taxes = product.taxes_id.compute_all(pricelist_price, quantity=1, product=product)["taxes"]
                    taxes_amount = 0.0
                    for tax in taxes:
                        taxes_amount += tax["amount"]
                    pricelist_price += taxes_amount
                product.write({"price_from_pricelist": pricelist_price})
                if product.product_tmpl_id.product_variant_count == 1:
                    product.product_tmpl_id.write({"price_from_pricelist": pricelist_price})
                else:
                    # TODO: compute minimum price from variants
                    pass

    @api.model
    def set_pricelist_price_cron(self):
        products = self.search([("website_published", "=", True)])
        products.set_pricelist_price()

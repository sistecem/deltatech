# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_length = fields.Float(string="Length", default=1)
    product_width = fields.Float(string="Width", default=1)
    product_height = fields.Float(string="Height", default=1)

    @api.onchange("product_length", "product_width", "product_height")
    def _onchange_dimension(self):
        if self.product_length and self.product_width and self.product_height:
            self.volume = self.product_length * self.product_width * self.product_height / 1000000

    @api.depends("product_length", "product_width", "product_height")
    def _compute_volume(self):
        super()._compute_volume()
        for product in self:
            if product.product_length and product.product_width and product.product_height:
                product.volume = product.product_length * product.product_width * product.product_height / 1000000

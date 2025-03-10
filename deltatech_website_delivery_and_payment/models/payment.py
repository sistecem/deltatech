# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    value_limit = fields.Float(string="Value Limit")
    restrict_label_ids = fields.Many2many("res.partner.category")
    submit_txt = fields.Char(string="Submit text", default="Finalize order", translate=True)

    def is_restricted(self, partner_id):
        self.ensure_one()
        for label in self.sudo().restrict_label_ids:
            if label in partner_id.sudo().category_id:
                return True
        return False

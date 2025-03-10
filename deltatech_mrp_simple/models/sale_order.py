# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    simple_mrp_picking_ids = fields.One2many("stock.picking", "sale_simple_mrp_id", string="Simple MRP Transfers")
    simple_mrp_count = fields.Integer(string="MRP Simple", compute="_compute_simple_mrp_picking_ids")

    @api.depends("simple_mrp_picking_ids")
    def _compute_simple_mrp_picking_ids(self):
        for order in self:
            order.simple_mrp_count = len(order.simple_mrp_picking_ids) / 2

    def action_view_mrp(self):
        self.ensure_one()
        mrps = self.env["mrp.simple"].search([("sale_order_id", "=", self.id)], limit=1)
        if mrps:
            mrp_id = mrps[0].id
        return {
            "res_id": mrp_id,
            "target": "current",
            "name": _("Simple production"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mrp.simple",
            "view_id": self.env.ref("deltatech_mrp_simple.view_mrp_simple_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }
        # action = self.env.ref("stock.action_picking_tree_all").read()[0]
        # pickings = self.mapped("simple_mrp_picking_ids")
        # if len(pickings) > 1:
        #     action["domain"] = [("id", "in", pickings.ids)]
        # elif pickings:
        #     form_view = [(self.env.ref("stock.view_picking_form").id, "form")]
        #     if "views" in action:
        #         action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
        #     else:
        #         action["views"] = form_view
        #     action["res_id"] = pickings.id
        # # Prepare the context.
        # picking_id = pickings.filtered(lambda l: l.picking_type_id.code == "outgoing")
        # if picking_id:
        #     picking_id = picking_id[0]
        # else:
        #     picking_id = pickings[0]
        # action["context"] = dict(
        #     self._context,
        #     default_partner_id=self.partner_id.id,
        #     default_picking_type_id=picking_id.picking_type_id.id,
        #     default_origin=self.name,
        #     default_group_id=picking_id.group_id.id,
        # )
        # return action

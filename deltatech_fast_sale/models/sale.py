# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_pickings(self):
        for picking in self.picking_ids:
            if picking.state not in ["done", "cancel"]:
                picking.action_assign()  # verifica disponibilitate
                products_unavailable = []
                for move in picking.move_lines:
                    if move.state != "assigned":
                        products_unavailable.append(move.product_id.display_name)
                if products_unavailable:
                    raise UserError(_("Not all products are available: %s" % ", ".join(products_unavailable)))

    def action_button_confirm_to_invoice(self):
        if self.state in ["draft", "sent"]:
            self.action_confirm()  # confirma comanda

        self._prepare_pickings()
        for picking in self.picking_ids:
            if picking.state not in ["done", "cancel"]:
                for move_line in picking.move_lines:
                    if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                        move_line.write({"quantity_done": move_line.product_uom_qty})
                    else:
                        move_line.unlink()
                picking.with_context(force_period_date=self.date_order)._action_done()

        action_obj = self.env.ref("sale.action_view_sale_advance_payment_inv")
        action = action_obj.read()[0]
        action["context"] = {"force_period_date": self.date_order}
        return action

    def action_button_confirm_notice(self):
        self._prepare_pickings()

        picking_ids = self.env["stock.picking"]
        for picking in self.picking_ids:
            if picking.state == "assigned":
                if "notice" in picking._fields:
                    picking.write({"notice": True})
                if "l10n_ro_notice" in picking._fields:
                    picking.write({"l10n_ro_notice": True})
                picking_ids |= picking

        if not picking_ids:
            return

        action = self.env.ref("stock.action_picking_tree_all")
        result = action.read()[0]

        result["context"] = {}

        pick_ids = picking_ids.ids
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            result["domain"] = "[('id','in',%s)]" % pick_ids.ids
        elif len(pick_ids) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = picking_ids.id
        return result

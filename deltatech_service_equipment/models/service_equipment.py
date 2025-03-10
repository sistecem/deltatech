# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ServiceEquipment(models.Model):
    _name = "service.equipment"
    _description = "Service Equipment"
    _inherits = {"maintenance.equipment": "base_equipment_id"}
    _inherit = ["mail.thread", "mail.activity.mixin"]

    base_equipment_id = fields.Many2one("maintenance.equipment", required=True, ondelete="cascade")

    # campuri care se gasesc in echipament
    # name = fields.Char(string='Name', index=True, required=True, copy=False)
    display_name = fields.Char(compute="_compute_display_name")

    # camp in echipament
    # categ_id = fields.Many2one('service.equipment.category', related="type_id.categ_id", string="Category")

    state = fields.Selection(
        [
            ("available", "Available"),
            ("installing", "In installing"),
            ("installed", "Installed"),
            ("inactive", "Inactive"),
            ("backuped", "Backuped"),
        ],
        default="available",
        string="Status",
        copy=False,
    )

    agreement_id = fields.Many2one("service.agreement", string="Contract Service")
    agreement_type_id = fields.Many2one(
        "service.agreement.type", string="Agreement Type", related="agreement_id.type_id", store=True
    )
    agreement_state = fields.Selection(string="Status contract", store=True, related="agreement_id.state")

    # se gaseste in echipmanet campul technician_user_id
    # user_id = fields.Many2one('res.users', string='Responsible', tracking=True)

    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)

    address_id = fields.Many2one(
        "res.partner",
        string="Address",
        readonly=True,
        help="The address where the equipment is located",
    )

    location_state_id = fields.Many2one(
        "res.country.state",
        string="Region",
        related="address_id.state_id",
        store=True,
    )
    emplacement = fields.Char(
        string="Emplacement",
        readonly=True,
        help="Detail of location of the equipment in working point",
    )

    # install_date = fields.Date(string='Installation Date',  readonly=True)

    contact_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        tracking=True,
        domain=[("type", "=", "contact"), ("is_company", "=", False)],
    )

    # se va calcula din suma consumurilor de servicii
    total_revenues = fields.Float(string="Total Revenues", readonly=True)
    # se va calcula din suma avizelor
    total_costs = fields.Float(string="Total cost", readonly=True)
    # se va calcula (costs/revenues)*100
    total_percent = fields.Float(string="Total percent equipment", readonly=True)

    note = fields.Text(string="Notes")
    start_date = fields.Date(string="Start Date")

    meter_ids = fields.One2many("service.meter", "equipment_id", string="Meters", copy=True)

    type_id = fields.Many2one("service.equipment.type", required=False, string="Type")

    readings_status = fields.Selection(
        [("", "N/A"), ("unmade", "Unmade"), ("done", "Done")],
        string="Readings Status",
        compute="_compute_readings_status",
        default="unmade",
        store=True,
    )

    group_id = fields.Many2one("service.agreement.group", string="Service Group")
    internal_type = fields.Selection([("equipment", "Equipment")], default="equipment")

    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic", ondelete="restrict")

    product_id = fields.Many2one(
        "product.product", string="Product", ondelete="restrict", domain=[("type", "=", "product")]
    )
    product_category_id = fields.Many2one("product.category", related="product_id.categ_id", store=True)
    serial_id = fields.Many2one("stock.production.lot", string="Serial Number", ondelete="restrict", copy=False)
    # quant_id = fields.Many2one('stock.quant', string='Quant', copy=False)  #  ondelete="restrict",
    location_id = fields.Many2one(
        "stock.location", "Stock Location", store=True, compute="_compute_location"
    )  # related='quant_id.location_id'

    ean_code = fields.Char(string="EAN Code")

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer")
    common_history_ids = fields.One2many("service.history", "equipment_id", string="Equipment History")

    location_type = fields.Selection(
        [
            ("stock", "In Stock"),
            ("rental", "In rental"),  # green  success
            ("customer", "Customer"),  # blue  info
            ("unavailable", "Unavailable"),  # red  danger
        ],
        default="stock",
        store=True,
        compute="_compute_location_type",
    )

    reading_day = fields.Integer(
        string="Reading Day",
        default=-1,
        help="""Day of the month, set -1 for the last day of the month.
                                     If it's positive, it gives the day of the month. Set 0 for net days .""",
    )
    last_reading = fields.Date("Last Reading Date", readonly=True, default="2000-01-01")
    next_reading = fields.Date("Next reading date", readonly=True, default="2000-01-01")
    last_reading_value = fields.Float(string="Last reading value")
    installation_date = fields.Date("Installation Date")

    _sql_constraints = [
        ("ean_code_uniq", "unique(ean_code)", "EAN Code already exist!"),
    ]

    @api.model
    def create(self, vals):
        if ("name" not in vals) or (vals.get("name") in ("/", False)):
            sequence = self.env.ref("deltatech_service_equipment.sequence_equipment")
            if sequence:
                vals["name"] = sequence.next_by_id()

        return super().create(vals)

    def write(self, vals):
        if ("name" in vals) and (vals.get("name") in ("/", False)):
            self.ensure_one()
            sequence = self.env.ref("deltatech_service_equipment.sequence_equipment")
            if sequence:
                vals["name"] = sequence.next_by_id()
        return super().write(vals)

    @api.depends("serial_id.quant_ids")
    def _compute_location(self):
        for equipment in self:
            if not equipment.serial_id:  # multiple quants, can be in different locations
                equipment.location_id = False
            else:
                quants = equipment.serial_id.quant_ids.filtered(lambda x: x.quantity > 0)
                if len(quants) == 1:
                    equipment.location_id = quants.location_id
                else:
                    equipment.location_id = False

    def compute_totals(self):
        self.compute_costs()
        self.compute_revenues()

    def compute_revenues(self):
        if self:
            query = """
            SELECT equipment_id, sum(sc.revenues) as revenues_total
            FROM service_consumption sc
            WHERE equipment_id in %(equipment)s AND
                state = %(state)s
            GROUP BY equipment_id
            """
            params = {
                "equipment": tuple(self.ids),
                "state": "done",
            }
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            for row in res:
                equipment = self.env["service.equipment"].browse(row[0])
                equipment.write({"total_revenues": round(row[1], 2)})
                equipment.compute_total_percent()

    def compute_costs(self):
        """
        Used to recompute costs from pickings, if necessary.
        The costs are added at each picking validation, if the picking has the
        picking_type_for_service type (see button_validate function)
        :return: nothing
        """
        if self:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            picking_type_id = safe_eval(get_param("service.picking_type_for_service", "False"))
            query = """
                    SELECT sp.equipment_id, sum(sv.value) as svls_total
                    FROM stock_picking sp
                    LEFT JOIN stock_move sm ON sm.picking_id = sp.id
                    LEFT JOIN stock_valuation_layer sv ON sm.id = sv.stock_move_id
                    WHERE equipment_id in %(equipment)s AND
                        sp.state = %(state)s AND
                        sp.picking_type_id = %(picking_type)s
                    GROUP BY equipment_id
                    """
            params = {
                "equipment": tuple(self.ids),
                "state": "done",
                "picking_type": picking_type_id,
            }
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            for row in res:
                equipment = self.env["service.equipment"].browse(row[0])
                equipment.write({"total_costs": round(row[1], 2)})
                equipment.compute_total_percent()

    def costs_and_revenues(self):
        self.compute_totals()

    @api.depends("location_id")
    def _compute_location_type(self):
        for equipment in self:
            if equipment.location_id.usage == "customer":
                equipment.location_type = "customer"
            elif equipment.location_id.usage == "internal":
                equipment.location_type = "stock"
            else:
                equipment.location_type = "unavailable"

            if equipment.location_id.rental:
                equipment.location_type = "rental"

    def _compute_readings_status(self):
        for equi in self:
            if equi.last_reading:
                next_date = max(date.today(), equi.last_reading)
            else:
                next_date = date.today()

            if equi.reading_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=0)
                next_date = next_first_date + relativedelta(days=equi.reading_day)
            if equi.reading_day > 0:
                next_date += relativedelta(day=equi.reading_day, months=0)

            next_reading_date = next_date

            equi.readings_status = "done"
            for meter in equi.meter_ids:
                if not meter.last_meter_reading_id:
                    equi.readings_status = "unmade"
                    break
                else:
                    equi.last_reading = meter.last_meter_reading_id.date
                if not (meter.last_meter_reading_id.date >= next_reading_date):
                    equi.readings_status = "unmade"
                    break

            if next_reading_date < equi.last_reading:
                next_date += relativedelta(months=1)
            equi.next_reading = next_date

    # def _compute_readings_status(self):
    #     from_date = date.today() + relativedelta(day=1, months=0, days=0)
    #     to_date = date.today() + relativedelta(day=1, months=1, days=-1)
    #     from_date = fields.Date.to_string(from_date)
    #     to_date = fields.Date.to_string(to_date)
    #
    #     for equi in self:
    #         equi.readings_status = "done"
    #         for meter in equi.meter_ids:
    #             if not meter.last_meter_reading_id:
    #                 equi.readings_status = "unmade"
    #                 break
    #             if not (from_date <= meter.last_meter_reading_id.date <= to_date):
    #                 equi.readings_status = "unmade"
    #                 break
    #             else:
    #                 equi.last_reading

    def invoice_button(self):
        consumptions = self.env["service.consumption"].search([("equipment_id", "=", self.id)])

        invoices = self.env["account.move"]
        for consumption in consumptions:
            if consumption.state == "done":
                invoices |= consumption.invoice_id

        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_service.action_service_invoice")
        action["domain"] = [("id", "=", invoices.ids)]
        return action

    def create_meters_button(self):
        categs = self.env["service.meter.category"]
        for equi in self:
            for template in equi.type_id.template_meter_ids:
                categs |= template.meter_categ_id
            for categ in categs:
                equi.meter_ids.create({"equipment_id": equi.id, "meter_categ_id": categ.id, "uom_id": categ.uom_id.id})

    def update_meter_status(self):
        self._compute_readings_status()

    # o fi ok sa elimin echipmanetul din contract
    def remove_from_agreement_button(self):
        self.ensure_one()
        if self.agreement_id.state == "draft":
            lines = self.env["service.agreement.line"].search(
                [("agreement_id", "=", self.agreement_id.id), ("equipment_id", "=", self.id)]
            )
            # lines.unlink()
            # if not self.agreement_id.agreement_line:
            #     self.agreement_id.unlink()
            lines.write({"active": False, "quantity": 0})
            self.agreement_id = False
        else:
            raise UserError(_("The agreement %s is in state %s") % (self.agreement_id.name, self.agreement_id.state))

    def do_agreement(self):
        pass

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            domain = [("product_id", "=", self.product_id.id)]
        else:
            domain = []
        return {"domain": {"serial_id": domain}}

    def common_history_button(self):
        return {
            "domain": [("id", "in", self.common_history_ids.ids)],
            "name": "History",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.history",
            "view_id": False,
            "type": "ir.actions.act_window",
        }

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        res_serial = []
        if name and len(name) > 3:
            equipment_ids = self.search(["|", ("serial_id", "ilike", name), ("ean_code", "ilike", name)], limit=10)
            if equipment_ids:
                res_serial = equipment_ids.name_get()
        res = super().name_search(name, args, operator=operator, limit=limit) + res_serial
        return res

    def name_get(self):
        res = []
        for equipment in self:
            name = equipment.name
            if equipment.address_id:
                name += "/" + equipment.address_id.name
            if equipment.serial_id:
                name += "/" + equipment.serial_id.name
            if equipment.emplacement:
                name += "/" + equipment.emplacement
            res.append((equipment.id, name))
        return res

    def compute_total_percent(self):
        for equipment in self:
            if equipment.total_revenues:
                equipment.write(
                    {"total_percent": round(((-1 * equipment.total_costs) / equipment.total_revenues) * 100, 2)}
                )
            else:
                equipment.write({"total_percent": 0.0})


# se va utiliza maintenance.equipment.category
class ServiceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    template_meter_ids = fields.One2many("service.template.meter", "categ_id")


class ServiceEquipmentType(models.Model):
    _name = "service.equipment.type"
    _description = "Service Equipment Type"
    name = fields.Char(string="Type", translate=True)

    categ_id = fields.Many2one("maintenance.equipment.category", string="Category")

    template_meter_ids = fields.One2many("service.template.meter", related="categ_id.template_meter_ids")

    @api.depends("categ_id")
    def _compute_template_meter_ids(self):
        for equipment_type in self:
            equipment_type.template_meter_ids = equipment_type.categ_id.template_meter_ids


# este utilizat pentru generare de pozitii noi in contract si pentru adugare contori noi
class ServiceTemplateMeter(models.Model):
    _name = "service.template.meter"
    _description = "Service Template Meter"

    categ_id = fields.Many2one("maintenance.equipment.category", string="Category")
    type_id = fields.Many2one("service.equipment.type", string="Type")
    product_id = fields.Many2one(
        "product.product", string="Service", ondelete="set null", domain=[("type", "=", "service")]
    )
    meter_categ_id = fields.Many2one("service.meter.category", string="Meter category")
    bill_uom_id = fields.Many2one("uom.uom", string="Billing Unit of Measure")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, domain=[("name", "in", ["RON", "EUR"])]
    )

    @api.onchange("meter_categ_id")
    def onchange_meter_categ_id(self):
        self.bill_uom_id = self.meter_categ_id.bill_uom_id

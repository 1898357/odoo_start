# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html#odoo-apps).

from odoo import _, api, models, fields


class SendcloudShippingMethodCountry(models.Model):
    _name = "sendcloud.shipping.method.country"
    _description = "Sendcloud Shipping Method Country"

    name = fields.Char(compute="_compute_country_id")
    country_id = fields.Many2one(
        "res.country", compute="_compute_country_id", string="To Country"
    )
    sendcloud_code = fields.Integer(required=True)
    iso_2 = fields.Char(required=True)
    iso_3 = fields.Char()
    from_name = fields.Char(compute="_compute_country_id")
    from_country_id = fields.Many2one("res.country", compute="_compute_country_id")
    from_iso_2 = fields.Char()
    from_iso_3 = fields.Char()
    price = fields.Float()
    method_code = fields.Integer(required=True)
    sendcloud_is_return = fields.Boolean()
    company_id = fields.Many2one("res.company", required=True)
    price_custom = fields.Float(
        compute="_compute_price_custom",
        inverse="_inverse_price_custom",
        readonly=False,
        string="Custom Price",
        help='This price will override the standard price and will be applied to the shipping price.'
    )
    price_check = fields.Selection(
        [
            ("standard", "Standard"),
            ("custom", "Custom"),
            ("unavailable", "Unavailable"),
        ],
        compute="_compute_price_custom",
    )

    @api.depends("iso_2", "company_id", "method_code")
    def _compute_price_custom(self):
        for item in self:
            custom = self.env[
                "sendcloud.shipping.method.country.custom"].search(
                [
                    ("iso_2", "=", item.iso_2),
                    ("company_id", "=", item.company_id.id),
                    ("method_code", "=", item.method_code),
                ],
                limit=1,
            )
            if custom and custom.price != False:
                item.price_custom = custom.price
                item.price_check = "custom"
            else:
                item.price_custom = item.price
                item.price_check = "standard"

    def _inverse_price_custom(self):
        for item in self:
            shipping_method_country = self.env[
                "sendcloud.shipping.method.country.custom"].search(
                [
                    ("iso_2", "=", item.iso_2),
                    ("company_id", "=", item.company_id.id),
                    ("method_code", "=", item.method_code),
                ],
                limit=1,
            )
            if shipping_method_country:
                shipping_method_country.price = item.price_custom
            else:
                self.env[
                    "sendcloud.shipping.method.country.custom"].create(
                    {
                        "iso_2": item.iso_2,
                        "company_id": item.company_id.id,
                        "method_code": item.method_code,
                        "price": item.price_custom,
                    }
                )

    @api.depends("iso_2", "from_iso_2")
    def _compute_country_id(self):
        iso_2_list = self.mapped("iso_2")
        from_iso_2_list = self.mapped("from_iso_2")
        all_countries = self.env["res.country"].search(
            [("code", "in", iso_2_list + from_iso_2_list)]
        )
        for record in self:
            to_countries = all_countries.filtered(lambda c: c.code == record.iso_2)
            record.country_id = fields.first(to_countries)
            record.name = record.country_id.name
            from_countries = all_countries.filtered(
                lambda c: c.code == record.from_iso_2
            )
            record.from_country_id = fields.first(from_countries)
            record.from_name = record.from_country_id.name

    def sendcloud_custom_price_details(self):
        self.ensure_one()
        return {
            "name": _("Custom Price Details"),
            "type": "ir.actions.act_window",
            "res_model": "sendcloud.custom.price.details.wizard",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_shipping_method_country_id": self.id,
            },
        }
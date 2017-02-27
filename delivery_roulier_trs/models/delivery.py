# coding: utf-8

from openerp import models, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """Add TRS carrier type."""
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('trs', 'Trs'),)
        return res
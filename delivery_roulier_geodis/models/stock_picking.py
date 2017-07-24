# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, api, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

GEODIS_DEFAULT_OPTIONS = {
    'MES': "3",
    'MEI': "3",
    'CXI': "1",
    'CX': "1",
    'EEX': "1",
}

GEODIS_DEFAULT_TOD = {
    'MES': 'P',
    'MEI': 'DAP',
    'CXI': 'P',
    'EEX': 'DAP',
}


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    geodis_shippingid = fields.Char(help="Shipping Id in Geodis terminology")

    def _geodis_get_shipping_date(self, package_id):
        """Estimate shipping date."""
        self.ensure_one()
        shipping_date = self.min_date
        if self.date_done:
            shipping_date = self.date_done

        shipping_date = datetime.strptime(
            shipping_date, DEFAULT_SERVER_DATETIME_FORMAT)

        tomorrow = datetime.now() + timedelta(1)
        if shipping_date < tomorrow:
            # don't send in the past
            shipping_date = tomorrow

        return shipping_date.strftime('%Y%m%d')

    def _geodis_convert_address(self, partner):
        """Truncate address and name to 35 chars."""
        address = self._roulier_convert_address(partner) or {}
        # get_split_adress from partner_helper module
        streets = partner._get_split_address(partner, 3, 35)
        address['street1'], address['street2'], address['street3'] = streets
        for field in ('name', 'city'):
            address[field] = address[field][0:35]
        return address

    def _geodis_get_options(self, package):
        """Define options for the shippment."""
        return GEODIS_DEFAULT_OPTIONS.get(self.carrier_code, '')

    def _geodis_prepare_edi(self):
        """Return a dict."""
        self.ensure_one()
        picking = self

        packages = picking._get_packages_from_picking()
        parcels = [{
            "barcode": pack.geodis_cab,
            "weight": pack.weight
        } for pack in packages]

        return [{
            "product": picking.carrier_code,
            "productOption": picking._get_options(None),
            "productTod": GEODIS_DEFAULT_TOD[picking.carrier_code],
            "to_address": self._convert_address(
                picking._get_receiver(None)),
            "reference1": picking.origin,
            "reference2": "",
            "reference3": "",
            "shippingId": picking.geodis_shippingid,
            "parcels": parcels
        }]

    @api.multi
    def _gen_shipping_id(self):
        """Generate a shipping id.

        Shipping id is persisted on the picking and it's
        calculated from a sequence since it should be
        8 char long and unique for at least 1 year
        """
        def gen_id():
            sequence = self.env['ir.sequence'].next_by_code(
                "geodis.nrecep.number")
            # this is prefixed by year_ so we split it befor use
            year, number = sequence.split('_')
            # pad with 0 to build an 8digits number (string)
            return '%08d' % int(number)

        for picking in self:
            picking.geodis_shippingid = (
                picking.geodis_shippingid or gen_id()
            )
        return True

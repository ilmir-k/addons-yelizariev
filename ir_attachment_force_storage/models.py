# -*- coding: utf-8 -*-
from openerp import api
from openerp import models
from openerp.exceptions import AccessError
from openerp.tools.translate import _
from openerp.addons.attachment_large_object.ir_attachment import LARGE_OBJECT_LOCATION
STORAGE_KEY = 'ir_attachment.location'


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def _attachment_force_storage(self, previous_value):
        self.env['ir.attachment'].force_storage_previous(previous_value=previous_value)

    @api.model
    def create(self, vals):
        res = super(IrConfigParameter, self).create(vals)
        if vals and vals.get('key') == STORAGE_KEY:
            default_value = self.env['ir.attachment']._storage()
            self._attachment_force_storage(default_value)
        return res

    @api.multi
    def _get_storage_value(self):
        for r in self:
            if self.key == STORAGE_KEY:
                return r.value
        return None

    @api.multi
    def write(self, vals):
        storage_value = self._get_storage_value()
        res = super(IrConfigParameter, self).write(vals)
        if storage_value:
            self._attachment_force_storage(storage_value)
        return res

    @api.multi
    def unlink(self):
        storage_value = self._get_storage_value()
        res = super(IrConfigParameter, self).unlink()
        if storage_value:
            self._attachment_force_storage(storage_value)
        return res


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def force_storage_previous(self, previous_value=None):
        """Force all attachments to be stored in the currently configured storage"""
        if not self.env.user._is_admin():
            raise AccessError(_('Only administrators can execute this action.'))
        new_value = self._storage()
        if LARGE_OBJECT_LOCATION in [previous_value, new_value]:
            # Update all records if large object is participated
            domain = []
        else:
            # Switching between file and db.
            # We can reduce records to be updated.
            domain = {
                'db': [('store_fname', '!=', False)],
                'file': [('db_datas', '!=', False)],
            }.get(new_value, [])

        # trick to disable addional filtering in ir.attachment's method _search
        domain += [('id', '!=', -1)]

        for attach in self.search(domain):
            # we add url because in some environment mimetype is not computed correctly
            # see https://github.com/odoo/odoo/issues/11978
            attach.write({'datas': attach.datas, 'url': attach.url})
        return True

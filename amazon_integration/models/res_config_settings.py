from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    amazon_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Commercial')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', 'amazon_user_id',
                      self.amazon_user_id.id)
        return True

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            {
                'amazon_user_id': IrDefault.get(
                    'res.config.settings', 'amazon_user_id'),
            }
        )
        return res

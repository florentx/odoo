# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from lxml import etree
from openerp.osv.orm import setup_modifiers

class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    _columns = {
         'analytics_id':fields.many2one('account.analytic.plan.instance','Analytic Distribution'),
    }


class purchase_order(osv.osv):
    _name='purchase.order'
    _inherit='purchase.order'

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order, self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res['analytics_id'] = order_line.analytics_id.id
        return res

class account_analytic_plan_instance(osv.osv):
    _name = "account.analytic.plan.instance"
    _inherit="account.analytic.plan.instance"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_analytic_plan_instance, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        nodes = res['fields']['account_ids']['views']['tree']['fields']['analytic_account_id']
        nodes['context'].update({'model': context.get('model',False)})
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

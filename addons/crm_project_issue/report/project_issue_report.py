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
from openerp import tools
from openerp.addons.crm import crm

class project_issue_report(osv.osv):
    _inherit = "project.issue.report"
    _auto = False

    _columns = {
        'section_id':fields.many2one('crm.case.section', 'Sale Team', readonly=True),
        'channel_id': fields.many2one('crm.case.channel', 'Channel',readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'project_issue_report')
        cr.execute("""
            CREATE OR REPLACE VIEW project_issue_report AS (
                SELECT
                    c.id as id,
                    to_char(c.create_date, 'YYYY') as name,
                    to_char(c.create_date, 'MM') as month,
                    to_char(c.create_date, 'YYYY-MM-DD') as day,
                    to_char(c.date_open, 'YYYY-MM-DD') as opening_date,
                    to_char(c.create_date, 'YYYY-MM-DD') as creation_date,
                    date_trunc('day',c.date_last_stage_update) as date_last_stage_update,
                    c.user_id,
                    c.working_hours_open,
                    c.working_hours_close,
                    c.section_id,
                    c.stage_id,
                    to_char(c.date_closed, 'YYYY-mm-dd') as date_closed,
                    c.company_id as company_id,
                    c.priority as priority,
                    c.project_id as project_id,
                    c.version_id as version_id,
                    1 as nbr,
                    c.partner_id,
                    c.channel_id,
                    c.task_id,
                    date_trunc('day',c.create_date) as create_date,
                    c.day_open as delay_open,
                    c.day_close as delay_close,
                    (SELECT count(id) FROM mail_message WHERE model='project.issue' AND res_id=c.id) AS email

                FROM
                    project_issue c
                WHERE c.active= 'true'
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

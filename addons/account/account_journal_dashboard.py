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
#########################################################################

from datetime import datetime, date, timedelta

from openerp.osv import fields, osv
from dateutil.relativedelta import relativedelta

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _prepare_where_clause_dashboard(self, cr, uid, journal_id, context=None):
        if context is None:
            context = {}
        where_clause = "journal_id = %s" % (journal_id)
        fiscalyear_id = self.pool.get('account.fiscalyear').find(cr, uid, context=context)
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        if company_id:
            where_clause += " AND company_id = %s" % (company_id)
        if fiscalyear_id:
            where_clause += " AND period_id in (SELECT account_period.id from account_period WHERE account_period.fiscalyear_id = %s)" % (fiscalyear_id)
        return where_clause
            
    def _get_remaining_payment_stats(self, cr, uid, journal_id, context=None):
        where_clause = self._prepare_where_clause_dashboard(cr, uid, journal_id, context=context)
        where_clause += " AND state = 'open'"
        cr.execute("SELECT date_due, sum(residual) FROM account_invoice WHERE %s GROUP BY date_due" % where_clause);
        residual_values = cr.fetchall()
        todo_payment_amount, overdue_amount_today, overdue_amount_month = 0,0,0
        
        overdue_today_date = date.today()
        overdue_month_end_date = date.today() + relativedelta(day=1, months=+1, days=-1)
        for date_due, overdue_invoice_amount in residual_values:
            todo_payment_amount +=  overdue_invoice_amount
            due_date = datetime.strptime(date_due,"%Y-%m-%d").date()
            if due_date <= overdue_today_date:
                overdue_amount_today += overdue_invoice_amount
            if due_date <= overdue_month_end_date:
                overdue_amount_month += overdue_invoice_amount
        
        res = {
            'overdue_invoice_amount' : overdue_amount_today,
            'overdue_invoice_amount_month': overdue_amount_month,
            'todo_payment_amount': todo_payment_amount
        }
        
        return res
        
    def get_stats(self, cr, uid, journal_id, context=None):
        where_clause = self._prepare_where_clause_dashboard(cr, uid, journal_id, context=context)
        cr.execute('SELECT state, sum(amount_total) FROM account_invoice WHERE %s GROUP BY state' % (where_clause));
        invoice_stats = cr.fetchall()
        res = {}
        for state, amount_total in invoice_stats:
            if state in ('draft', 'proforma', 'proforma2'):
                res['draft_invoice_amount'] = amount_total
            elif state == 'open':   
                res['open_invoice_amount'] = amount_total
            elif state == 'paid':
                res['paid_invoice_amount'] = amount_total
        
        remaining_payment_stats = self._get_remaining_payment_stats(cr, uid, journal_id, context=context)
        res.update(remaining_payment_stats)
        return res

class account_journal(osv.osv):
    _inherit = "account.journal"
    
    def _kanban_dashboard(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for journal_id in ids:
            res[journal_id] = self.get_journal_dashboard_datas(cr, uid, journal_id, context=context)
        return res
    def _kanban_graph(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for journal_id in ids:
            res[journal_id] = self._prepare_graph_data(cr, uid, journal_id, context=context)
        return res
        
    _columns = {
        'kanban_dashboard':fields.function(_kanban_dashboard, type="text"),
        'kanban_graph':fields.function(_kanban_graph, type="text"),
    }
    
    def get_journal_dashboard_datas(self, cr, uid, journal_id, context=None):
        invoice_obj = self.pool['account.invoice']
        move_line_obj = self.pool['account.move.line']
        
        journal = self.browse(cr, uid, journal_id ,context=context)
        
        balance, date = self._get_last_statement(cr, uid, journal_id, context=context)
        values = invoice_obj.get_stats(cr, uid, journal_id, context=context)
        
        currency_symbol = journal.company_id.currency_id.symbol
        if journal.currency:
            currency_symbol = journal.currency.symbol
        
        fiscalyear_id = self.pool.get('account.fiscalyear').find(cr, uid, context=context)
        total_reconcile_amount = move_line_obj.search(cr, uid, [('journal_id', '=', journal_id), ('period_id.fiscalyear_id', '=', fiscalyear_id), ('reconcile_partial_id','!=',False)], count=True ,context=context)
        
        values.update({
            'currency_symbol' : currency_symbol,
            'last_statement_amount' : balance,
            'last_statement_date' : date,
            'total_reconcile_amount' : total_reconcile_amount,
            'credit_account_name': journal.default_credit_account_id.name,
            'credit_account_balance' : journal.default_credit_account_id.balance,
        })
        return values

    
    def _get_last_statement(self, cr, uid, journal_id, context=None):
        """Get last bank statement amount and date."""
        balance = False
        date = False
        statement_obj = self.pool['account.bank.statement']
        date_format = self.pool['res.lang'].search_read(cr, uid, [('code','=', context.get('lang', 'en_US'))], ['date_format'], context=context)[0]['date_format']
        statement_ids = statement_obj.search(cr, uid, [('journal_id', '=', journal_id)], order='create_date desc', limit=1, context=context)
        if statement_ids:
            statement = statement_obj.browse(cr, uid, statement_ids[0], context=context)
            if statement.journal_id.type == 'cash':
                balance = statement.balance_end
            elif statement.journal_id.type == 'bank':
                balance = statement.balance_end_real
            date = datetime.strptime(str(statement.date), '%Y-%m-%d').date().strftime(date_format)
        return (balance , date)

    def _prepare_graph_data(self, cr, uid, journal_id, context=None):
        """Prepare data to show graph in kanban of journals which will be called from the js"""
        res = False
        journal = self.browse(cr, uid, journal_id, context=context)
        if journal.type in ['general','situation']:
            return res
        if journal.type in ['cash','bank']:
            res = self._get_moves_per_day(cr, uid, journal, context=context)
        else:
            res = self._get_moves_per_month(cr, uid, journal, context=context)
        return res

    def _get_moves_per_month(self, cr, uid, journal, context=None):
        """Get amount of moves related to the perticular journals per month"""
        total = {}
        fiscalyear_pool = self.pool.get('account.fiscalyear')
        fiscalyear_id = fiscalyear_pool.find(cr, uid, context=context)
        fiscalyear = fiscalyear_pool.browse(cr, uid, fiscalyear_id, context=context)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        state = ['posted'] if journal.type=='sale' else ['draft','posted']
        
                    
        cr.execute("SELECT to_char(line.date, 'MM') as month, SUM(line.debit) as amount\
                    FROM account_move_line AS line LEFT JOIN account_move AS move ON line.move_id=move.id\
                    WHERE line.journal_id = %s AND line.period_id in (SELECT account_period.id from account_period WHERE account_period.fiscalyear_id = %s) \
                    AND move.state in %s\
                    GROUP BY to_char(line.date, 'MM') \
                    ORDER BY to_char(line.date, 'MM')", (journal.id, fiscalyear_id, tuple(state)))
        
        values = []
        for month, amount in cr.fetchall():
            values.append({
                'x': months[int(month) - 1],
                'y': amount
            })
        data = {
            'values': [],
            'bar': True,
            'key': fiscalyear.name
        }
        for month in months:
            amount = 0
            for value in values:
                if month == value['x']:
                    amount = value['y']
            data['values'].append({'x': month, 'y': amount})
        return data

    def _get_moves_per_day(self, cr, uid, journal, context=None):
        """Get total transactions per day for related journals"""
        data = {'values': [], 'key': 'Total'}
        date_format = self.pool['res.lang'].search_read(cr, uid, [('code', '=', context.get('lang', 'en_US'))], ['date_format'], context=context)[0]['date_format']
        move_date = date.today()-timedelta(days=14)
        fiscalyear_id = self.pool.get('account.fiscalyear').find(cr, uid, context=context)
        #left join on account_move if we want only posted entries then we can use.
        cr.execute("SELECT SUM(line.debit), line.date\
                         FROM account_move_line AS line LEFT JOIN account_move AS move ON line.move_id=move.id\
                         WHERE line.journal_id = %s AND line.period_id in (SELECT account_period.id from account_period WHERE account_period.fiscalyear_id = %s) \
                         AND line.date >= %s\
                         GROUP BY line.date \
                         ORDER BY line.date",(journal.id, fiscalyear_id, move_date))
        for value in cr.dictfetchall():
            data['values'].append({
                'x': datetime.strptime(str(value['date']), '%Y-%m-%d').date().strftime(date_format),
                'y': value['sum']
            })
        if not data['values']:
            data['values'].append({'x': datetime.strptime(str(date.today()), '%Y-%m-%d').date().strftime(date_format), 'y': 0})
        return data
        
    def open_action(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ir_model_obj = self.pool.get('ir.model.data')
        rec = self.browse(cr, uid, ids[0], context=context)
        if rec.type == 'bank':
            action_name = 'action_bank_statement_tree'
        elif rec.type == 'cash':
            action_name = 'action_view_bank_statement_tree'
        elif rec.type == 'sale':
            action_name = 'action_invoice_tree1'
        elif rec.type == 'purchase':
            action_name = 'action_invoice_tree2'
        elif rec.type == 'sale_refund':
            action_name = 'action_invoice_tree3'
        elif rec.type == 'purchase_refund':
            action_name = 'action_invoice_tree4'
        action_name = context.get('action_name',action_name)
        ctx = context.copy()
        _journal_invoice_type_map = {'sale': 'out_invoice', 'purchase': 'in_invoice', 'sale_refund': 'out_refund', 'purchase_refund': 'in_refund', 'bank': 'bank', 'cash': 'cash'}
        invoice_type = _journal_invoice_type_map[rec.type]
        ctx.update({'journal_type': rec.type,'default_journal_id': rec.id,'search_default_journal_id': rec.id,'default_type': invoice_type,'type': invoice_type})
        domain = [('journal_id.type', '=', rec.type),('journal_id', '=', rec.id)]
        model, action_id = ir_model_obj.get_object_reference(cr, uid, 'account', action_name)
        action = self.pool.get(model).read(cr, uid, action_id, context=context)
        action['context'] = ctx
        action['domain'] = domain
        return action

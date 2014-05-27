{
    'name': 'Lead to Issue',
    'version': '1.0',
    'summary': 'Create Issues from Leads',
    'sequence': '19',
    'category': 'Project Management',
    'complexity': 'easy',
    'author': 'OpenERP SA',
    'description': """
Lead to Issues
==============

Link module to map leads to issues
        """,
    'data': [
        'project_issue_view.xml',
        'report/project_issue_report_view.xml',
    ],
    'depends': ['crm', 'project_issue'],
    'demo': ['project_issue_demo.xml'],
    'installable': True,
}

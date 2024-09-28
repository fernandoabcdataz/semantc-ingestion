import os
from typing import Dict, Any

def get_env_variable(var_name: str) -> str:
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set")
    return value

def get_client_config() -> Dict[str, Any]:
    client_name = get_env_variable("CLIENT_NAME")
    project_id = get_env_variable("GOOGLE_CLOUD_PROJECT")
    client_token = get_env_variable("CLIENT_TOKEN")
    bucket_name = get_env_variable("BUCKET_NAME")
    
    return {
        "CLIENT_NAME": client_name,
        "PROJECT_ID": project_id,
        "CLIENT_TOKEN": client_token,
        "BUCKET_NAME": bucket_name,
        "SECRETS_PATH": f"projects/{project_id}/secrets",
        "BATCH_SIZE": int(os.environ.get("BATCH_SIZE", 100))
    }

TOKEN_URL = 'https://identity.xero.com/connect/token'
ENDPOINT_BASE = 'https://api.xero.com/api.xro/2.0/'

ENDPOINTS = {
    'accounts': ENDPOINT_BASE + 'Accounts',
    'bank_transactions': ENDPOINT_BASE + 'BankTransactions',
    'bank_transfers': ENDPOINT_BASE + 'BankTransfers',
    'batch_payments': ENDPOINT_BASE + 'BatchPayments',
    'branding_themes': ENDPOINT_BASE + 'BrandingThemes',
    'budgets': ENDPOINT_BASE + 'Budgets',
    'contact_groups': ENDPOINT_BASE + 'ContactGroups',
    'contacts': ENDPOINT_BASE + 'Contacts',
    'credit_notes': ENDPOINT_BASE + 'CreditNotes',
    'currencies': ENDPOINT_BASE + 'Currencies',
    'employees': ENDPOINT_BASE + 'Employees',
    'invoices': ENDPOINT_BASE + 'Invoices',
    'items': ENDPOINT_BASE + 'Items',
    'journals': ENDPOINT_BASE + 'Journals',
    'linked_transactions': ENDPOINT_BASE + 'LinkedTransactions',
    'manual_journals': ENDPOINT_BASE + 'ManualJournals',
    'organisation': ENDPOINT_BASE + 'Organisation',
    'overpayments': ENDPOINT_BASE + 'Overpayments',
    'payment_services': ENDPOINT_BASE + 'PaymentServices',
    'payments': ENDPOINT_BASE + 'Payments',
    'prepayments': ENDPOINT_BASE + 'Prepayments',
    'purchase_orders': ENDPOINT_BASE + 'PurchaseOrders',
    'quotes': ENDPOINT_BASE + 'Quotes',
    'repeating_invoices': ENDPOINT_BASE + 'RepeatingInvoices',
    'reports__balance_sheet': ENDPOINT_BASE + 'Reports/BalanceSheet',
    'reports__bank_summary': ENDPOINT_BASE + 'Reports/BankSummary',
    'reports__budget_summary': ENDPOINT_BASE + 'Reports/BudgetSummary',
    'reports__executive_summary': ENDPOINT_BASE + 'Reports/ExecutiveSummary',
    'reports__trial_balance': ENDPOINT_BASE + 'Reports/TrialBalance',
    'tax_rates': ENDPOINT_BASE + 'TaxRates',
    'tracking_categories': ENDPOINT_BASE + 'TrackingCategories',
    'users': ENDPOINT_BASE + 'Users',
}

CONFIG = {
    **get_client_config(),
    "TOKEN_URL": TOKEN_URL,
    "ENDPOINTS": ENDPOINTS,
}
import os

import gspread
from ansible_vault import Vault
from oauth2client.service_account import ServiceAccountCredentials

def connect_google_sheets(encrypted_secrets_file='secrets/lupyanlab.json'):
    """Connect to the Google Sheets API with gspread.

    Args:
        encrypted_secrets_file: Path to json file containing the
            Google API Service Account Credentials encrypted using
            Ansible Vault. Requires ANSIBLE_VAULT_PASSWORD_FILE to
            be set in the current environment.
    """
    password = open(os.environ['ANSIBLE_VAULT_PASSWORD_FILE']).read()
    json_data = Vault(password).load(open(encrypted_secrets_file).read())
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            json_data,
            ['https://spreadsheets.google.com/feeds'])
    return gspread.authorize(credentials)

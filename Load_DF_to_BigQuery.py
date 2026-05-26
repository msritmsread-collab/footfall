import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd, pytz

current_folder_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_folder_path)

project_id = 'msr-msia-sales-analysis'
dataset_id = 'Footfall'
table = 'Footfall_012023_082023_count_hour'
table_id = '{}.{}.{}'.format(project_id, dataset_id, table)
print('***** Name of Table is', table_id)


def _get_credentials():
    """Get BigQuery credentials from file or Secret Manager."""
    from gcp_secrets import get_secret, is_cloud

    if is_cloud():
        cred_json = json.loads(get_secret("connector-bq-service-account"))
        return service_account.Credentials.from_service_account_info(cred_json)
    else:
        key_path = f'{current_folder_path}/BigQuery_Credential.json'
        return service_account.Credentials.from_service_account_file(key_path)


key_path = f'{current_folder_path}/BigQuery_Credential.json'
credentials = _get_credentials()

print('Credentials loaded')


def load_table_dataframe_config(key_path, project_id, table_id, data):
    credentials = _get_credentials()
    client = bigquery.Client(credentials=credentials, project=project_id)
    job_config = bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
    job = client.load_table_from_dataframe(data, table_id, job_config=job_config)
    job.result()
    result = client.get_table(table_id)
    return result
from datetime import datetime, timedelta

from gcp_secrets import get_secret

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
query = {
    "BranchId": ["30273", "6513", "26061", "26549", "27497", "27769", "30187", "30250"],
    "Daterange": [yesterday, yesterday],
    "granularity": "day"
}

# Token loaded at runtime from Secret Manager
tokens = None

newname = {
    "ffc_site_summary.CompanyId": "CompanyId",
    "ffc_site_summary.CompanyName": "name",
    "ffc_site_summary.SiteId": "BranchId",
    "ffc_site_summary.SiteName": "BranchName",
    "ffc_site_summary.Time": "Date",
    "ffc_site_summary.Time.day": "Date2",
    "ffc_site_summary.A05": "Outside_Traffic",
    "ffc_site_summary.B01": "Turn_In_Rate",
    "ffc_site_summary.A04": "Average_Visit_Duration",
    "ffc_area_summary.SiteId": "BranchId",
    "ffc_area_summary.SiteName": "BranchName",
    "ffc_area_summary.Time": "DateTime",
    "ffc_area_summary.A01": "CountIn",
    "ffc_area_summary.A02": "CountOut"
}

payloadday = {
    "queryType": "multi",
    "query": {
        "measures": [
            "ffc_site_summary.A05",
            "ffc_site_summary.B01",
            "ffc_site_summary.A04"
        ],
        "dimensions": [
            "ffc_site_summary.CompanyId",
            "ffc_site_summary.CompanyName",
            "ffc_site_summary.SiteId",
            "ffc_site_summary.SiteName",
            "ffc_site_summary.Time"
        ],
        "filters": [{
            "member": "ffc_site_summary.SiteId",
            "operator": "equals",
            "values": query["BranchId"]
        }],
        "timeDimensions": [{
            "dimension": "ffc_site_summary.Time",
            "dateRange": query["Daterange"],
            "granularity": query["granularity"]
        }],
        "order": {
            "ffc_site_summary.Time": "asc"
        }
    }
}

payload = {
    "query": {
        "measures": [
            "ffc_area_summary.A01",
            "ffc_area_summary.A02"
        ],
        "dimensions": [
            "ffc_area_summary.SiteId",
            "ffc_area_summary.SiteName",
            "ffc_area_summary.Time"
        ],
        "filters": [
            {
                "member": "ffc_area_summary.SiteId",
                "operator": "equals",
                "values": query["BranchId"]
            },
            {
                "member": "ffc_area_summary.IsOperating",
                "operator": "equals",
                "values": ["1"]
            }
        ],
        "timeDimensions": [{
            "dimension": "ffc_area_summary.Time",
            "dateRange": query["Daterange"],
            "granularity": "hour"
        }],
        "order": {
            "ffc_area_summary.Time": "asc"
        }
    }
}


def load_config():
    """Load secrets from Secret Manager at runtime."""
    global tokens
    tokens = get_secret("connector-footfall-token")
    return tokens


def get_bq_credentials():
    """Get BigQuery service account JSON from Secret Manager."""
    return get_secret("connector-bq-service-account")
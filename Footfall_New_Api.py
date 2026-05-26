import datetime, time, pandas as pd, requests, variables as var, Load_DF_to_BigQuery as loadBQ

var.load_config()

url = "https://cube.footfallcam.com/API/v1/load"

dictnew = {
    'name': ['payloadday', 'payloadhour'],  # ['payloadday', 'payloadhour']
    'query': [var.payloadday, var.payload],
    'tableid': [
        'msr-msia-sales-analysis.Footfall.Footfall_092023',
        'msr-msia-sales-analysis.Footfall.Footfall_092023_count_hour'
    ]
}

headers = {
    'Authorization': 'Bearer ' + var.tokens,
    'Content-Type': 'application/json'
}

def request(payload):
    r = requests.post(url, json=payload, headers=headers)
    return r

# DataFrame for daily data
def DF(r):
    data = r.json()['results'][0]["data"]
    df = pd.DataFrame(data).rename(columns=var.newname)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%dT00:00:00')
    df['Date2'] = pd.to_datetime(df['Date2'], errors='coerce').dt.strftime('%d/%m/%Y')
    df['Average_Visit_Duration'] = pd.to_numeric(df['Average_Visit_Duration'], errors='coerce')
    df['Average_Visit_Duration'] = (df['Average_Visit_Duration'] / 60).round(2)  

    return df


# DataFrame for hourly data
def DFhour(r):
    try:
        response_json = r.json()
        if 'data' not in response_json:
            print(f"'data' key not found in API response: {response_json}")
            return pd.DataFrame() 

        data = response_json['data']
        df = pd.DataFrame(data).rename(columns=var.newname)
        df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        df = df[(df['DateTime'].dt.hour >= 10) & (df['DateTime'].dt.hour <= 22)]
        df['DateTime'] = df['DateTime'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        if 'ffc_area_summary.Time.hour' in df.columns:
            df.drop(columns=['ffc_area_summary.Time.hour'], inplace=True)
        return df

    except Exception as e:
        print(f"Error processing hourly data: {e}\nFull response: {r.text}")
        return pd.DataFrame()


# Main function to process request and fetch data
def main(type, payload):
    r = request(payload)
    if r is None:
        print("Request failed.")
        return None

    if r.status_code == 200 and type == 'payloadday':
        df = DF(r)
        return df
    elif r.status_code == 200 and type == 'payloadhour':
        df = DFhour(r)
        return df
    else:
        print(f"Request failed with status code {r.status_code}. Response: {r.json()}")
        return None

# Ensure the correct data types are used for BigQuery upload
def convert_to_bigquery_types(df, type):
    if type == 'payloadday':
        if 'CompanyId' in df.columns:
            df['CompanyId'] = df['CompanyId'].astype('int64')
        if 'BranchId' in df.columns:
            df['BranchId'] = df['BranchId'].astype('int64')
        if 'Outside_Traffic' in df.columns:
            df['Outside_Traffic'] = df['Outside_Traffic'].astype('int64')
        if 'Turn_In_Rate' in df.columns:
            df['Turn_In_Rate'] = df['Turn_In_Rate'].astype('float64')
        if 'Average_Visit_Duration' in df.columns:
            df['Average_Visit_Duration'] = df['Average_Visit_Duration'].astype('float64')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        if 'Date2' in df.columns:
            df['Date2'] = df['Date2'].astype('str')
        if 'BranchName' in df.columns:
            df['BranchName'] = df['BranchName'].astype('str')
    elif type == 'payloadhour':
        if 'CountIn' in df.columns:
            df['CountIn'] = df['CountIn'].astype('int64')
        if 'CountOut' in df.columns:
            df['CountOut'] = df['CountOut'].astype('int64')
        if 'DateTime' in df.columns:
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        if 'BranchId' in df.columns:
            df['BranchId'] = df['BranchId'].astype('int64')
        if 'BranchName' in df.columns:
            df['BranchName'] = df['BranchName'].astype('str')

    return df

num_elements = len(dictnew['name'])
for i in range(num_elements):
    row = {key: dictnew[key][i] for key in dictnew}
    print(f"Query: {row['name']} & Upload to {row['tableid']}\n")

    dffinal = main(row['name'], row['query'])

    if dffinal is not None:
        print("Columns in DataFrame:", dffinal.columns)

        dffinal.columns = dffinal.columns.str.strip()

        if 'CountIn' in dffinal.columns or row['name'] == 'payloadday':
            dffinal = convert_to_bigquery_types(dffinal, row['name'])

        if dffinal is not None:
            print(dffinal)

            try:
                file_path = f"{loadBQ.current_folder_path}\\{row['tableid']}{str(datetime.datetime.now().strftime('%d%m%YT%H%M'))}.csv"
                dffinal.to_csv(file_path, index=False)
                print(f"Data saved to CSV: {file_path}")
            except Exception as e:
                print(f"Error saving to CSV for {row['tableid']}: {e}")

            try:
                print(f"Attempting to upload data to BigQuery: {row['tableid']}")
                print(f"Upload parameters:\nProject ID: {loadBQ.project_id}\nTable ID: {row['tableid']}\nDataFrame Shape: {dffinal.shape}")
                upload_result = loadBQ.load_table_dataframe_config(
                    loadBQ.key_path,
                    loadBQ.project_id,
                    row['tableid'],
                    dffinal
                )
                print(f"Success adding the data to {row['tableid']}: {upload_result}")
            except Exception as e:
                print(f"Failed to load data to BigQuery for {row['tableid']}: {e}")

    time.sleep(5)

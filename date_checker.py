import os
import pandas as pd
import datetime

# Set up paths
current_folder_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_folder_path)

# File paths
processed_dates_log = os.path.join(current_folder_path, 'processed_dates.csv')

# Ensure log exists
if not os.path.exists(processed_dates_log):
    pd.DataFrame(columns=['ProcessedDate']).to_csv(processed_dates_log, index=False)

# Load processed dates
processed_dates = pd.read_csv(processed_dates_log)['ProcessedDate'].tolist()

# Identify the latest daily CSV
csv_files = [f for f in os.listdir(current_folder_path) if f.startswith('msr-msia-sales-analysis.Footfall.Footfall_092023') and f.endswith('.csv')]
csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

if not csv_files:
    print("No CSV files found.")
else:
    latest_file = csv_files[0]
    print(f"Latest file: {latest_file}")

    # Load the latest CSV
    df = pd.read_csv(latest_file)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Identify missing dates
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    all_dates = pd.date_range(min_date, max_date, freq='D')

    missing_dates = [d for d in all_dates if d.strftime('%Y-%m-%dT00:00:00') not in df['Date'].dt.strftime('%Y-%m-%dT00:00:00').values]
    new_records = []

    # Add missing dates
    for missing_date in missing_dates:
        if missing_date.strftime('%Y-%m-%d') not in processed_dates:
            new_records.append({
                'CompanyId': None,
                'name': None,
                'BranchId': None,
                'BranchName': None,
                'Date': missing_date.strftime('%Y-%m-%dT00:00:00'),
                'Date2': missing_date.strftime('%d/%m/%Y'),
                'Outside_Traffic': 0,
                'Turn_In_Rate': 0.0,
                'Average_Visit_Duration': 0.0
            })

    # Merge new records
    if new_records:
        df = pd.concat([df, pd.DataFrame(new_records)], ignore_index=True)
        df.sort_values('Date', inplace=True)
        df.to_csv(latest_file, index=False)
        print(f"Missing dates added and saved to {latest_file}")
    else:
        print("No missing dates found.")

    # Update processed dates log
    processed_dates.extend([d.strftime('%Y-%m-%d') for d in missing_dates])
    pd.DataFrame({'ProcessedDate': processed_dates}).to_csv(processed_dates_log, index=False)

print("Missing date handling completed.")

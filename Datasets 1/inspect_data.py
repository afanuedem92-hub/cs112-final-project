import pandas as pd
import glob
import os

# Find all CSV files in this folder
files = glob.glob("*.csv")

if len(files) == 0:
    print("No CSV files found.")
else:
    for file in files:
        print("\n" + "=" * 50)
        print("Checking:", file)
        print("=" * 50)

        df = pd.read_csv(file)

        print("\nNumber of rows:", len(df))
        print("Number of columns:", len(df.columns))

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nMissing values:")
        print(df.isnull().sum())

        print("\nDuplicate rows:")
        print(df.duplicated().sum())

        print("\nData types:")
        print(df.dtypes)

        print("\nFirst 5 rows:")
        print(df.head())

print("\nInspection finished!")
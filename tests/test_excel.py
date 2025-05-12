import pandas as pd

def test_excel_structure():
    # Read the Excel file
    df = pd.read_excel("prompts/LoncaFAQs.xlsx")
    
    # Print column names
    print("Column names:", df.columns.tolist())
    
    # Print first few rows
    print("\nFirst few rows:")
    print(df.head())
    
    # Print unique values in each column
    print("\nUnique values in each column:")
    for col in df.columns:
        print(f"\n{col}:")
        print(df[col].unique())

if __name__ == "__main__":
    test_excel_structure() 
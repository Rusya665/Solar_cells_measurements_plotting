import pandas as pd
from icecream import ic

from JV_plotter_GUI.instruments import open_file


# Function to calculate percentage difference
def percentage_difference(value1, value2):
    if value1 == 0 and value2 == 0:
        return 0
    return 100 * abs(value1 - value2) / abs(value1)


# Function to compare excel sheets
def compare_excel_sheets(file1_path, sheet1_name, file2_path, sheet2_name):
    # Read the data from the specified sheets
    data1 = pd.read_excel(file1_path, sheet_name=sheet1_name)
    data2 = pd.read_excel(file2_path, sheet_name=sheet2_name)
    data2.rename(columns={
        'Label': 'Sample',
        'Short-circuit current density (mA/cm²)': 'Short-circuit current density (mA/cm^2)',
        'Current density at MPP (mA/cm²)': 'Current density at MPP (mA/cm^2)'
    }, inplace=True)
    # Applying the transformation to the "Sample" column in data2
    data2['Sample'] = data2['Sample'].apply(lambda input_string: input_string.replace("-", "_").replace(" ", ""))
    data2 = data2.drop('Active area, (cm²)', axis=1)
    # data2 = data2.drop('Device order', axis=1)
    ic(data1.head(), data2.head())
    # Converting the "Scan direction" column to string in both datasets
    data1['Scan direction'] = data1['Scan direction'].astype(str)
    data2['Scan direction'] = data2['Scan direction'].astype(str)
    # Create a new dataframe to hold the differences
    difference_df = data1.copy()

    # Iterate through the rows of data1 and data2, calculate the percentage differences
    for index, row in data1.iterrows():
        # ic(row)
        corresponding_row_data2 = data2[
            (data2['Sample'] == row['Sample']) & (data2['Scan direction'] == row['Scan direction'])]
        if corresponding_row_data2.shape[0] > 0:
            for column in difference_df.columns:
                if column not in {'Sample', 'Scan direction'}:
                    value1 = row[column]
                    value2 = corresponding_row_data2[column].iloc[0]
                    percent_diff = percentage_difference(value1, value2)
                    ic(percent_diff)
                    difference_df.at[index, column] = percent_diff

    return difference_df


pd.set_option('display.max_rows', None)

# Example usage:
file1_path = r'IVparameters.xlsx'
sheet1_name = 'All'
file2_path = r'2023-08-27 Washed out JV plots and calculations.xlsx'
sheet2_name = 'Tabel_Total'
# sheet2_name = 'Sheet1'
differences = compare_excel_sheets(file1_path, sheet1_name, file2_path, sheet2_name)

# Set any percentage difference less than 1% to 0 for numeric columns only
for column in differences.select_dtypes(include=['number']).columns:
    differences[column] = differences[column].apply(lambda x: 0 if x < 1 else x)

# Define the path for the output text file
output_xlsx_path = r'Desktop/washed_checking.xlsx'

# Save the differences dataframe to an Excel file
differences.to_excel(output_xlsx_path, index=False)
open_file(output_xlsx_path)

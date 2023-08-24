from datetime import timedelta

import pandas as pd
from icecream import ic


def read_IV_data_with_print(path: str, encoding: str = 'ISO-8859-1') -> pd.DataFrame:
    i_values, v_values, time_values = [], [], []
    num_header_lines, i_index, v_index, time_index, current_unit = None, None, None, None, None
    preconditioning_time = None

    with open(path, 'r', encoding=encoding) as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if "Nb header lines" in line:
                num_header_lines = int(line.split(":")[1].strip())
                continue

            if line.startswith("ti (h:m:s)"):
                time_str = line.split("ti (h:m:s)")[1]
                hours, minutes, seconds = map(float, time_str.split(':'))
                preconditioning_time = timedelta(hours=hours, minutes=minutes,
                                                 seconds=seconds).total_seconds()
                continue

            if num_header_lines is None:
                continue

            values = line.split("\t")
            if line_number == num_header_lines:
                i_index, v_index = values.index(next(h for h in values if "<I>" in h)), values.index(
                    next(h for h in values if "Ewe" in h))
                # Check if the time column exists
                time_index = next((i for i, h in enumerate(values) if "time" in h), None)
                current_unit = values[i_index].split("/")[-1]  # Extracting the current unit
                ic(i_index, v_index, time_index, current_unit)
            elif line_number > num_header_lines and time_index is not None:
                time_str = values[time_index].split(' ')[1]
                hours, minutes, seconds = map(float, time_str.split(':'))
                total_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
                time_values.append(float(total_seconds))
                i_values.append(float(values[i_index]))
                v_values.append(float(values[v_index]))

    # Creating a DataFrame with the I, V, and time values
    df = pd.DataFrame({'I': i_values, 'V': v_values, 'Time': time_values})
    # Creating a mask that checks if the 'Time' value is higher than the first 'Time' value plus preconditioning_time
    mask = df['Time'] > preconditioning_time + df['Time'].iloc[0]
    # Use the mask to filter the DataFrame
    df = df[mask].drop(columns=['Time']).reset_index(drop=True)
    return df


# Set pandas' console output width
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# Running the function with the first .mpt file
path = r'C:/Users/runiza.TY2206042/OneDrive - O365 Turun yliopisto/IV_plotting_project/Input/2.mpt'
# Testing the function with the given file
test_current_unit = read_IV_data_with_print(path)

# print(test_current_unit)

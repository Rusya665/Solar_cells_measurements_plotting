import csv
import os
from datetime import timedelta, datetime

import pandas as pd


def convert_mpt_to_csv(mpt_path):
    i_values, v_values, time_values = [], [], []
    num_header_lines, i_index, v_index, time_index, current_unit = None, None, None, None, None
    preconditioning_time = None
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(mpt_path, 'r', encoding='ISO-8859-1') as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if "Nb header lines" in line:
                num_header_lines = int(line.split(":")[1].strip())
                continue

            if line.startswith("ti (h:m:s)"):
                time_str = line.split("ti (h:m:s)")[1]
                hours, minutes, seconds = map(float, time_str.split(':'))
                preconditioning_time = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
                continue

            if num_header_lines is None:
                continue

            values = line.split("\t")
            if line_number == num_header_lines:
                i_index, v_index = values.index(next(h for h in values if "<I>" in h)), values.index(
                    next(h for h in values if "Ewe" in h))
                time_index = next((i for i, h in enumerate(values) if "time" in h), None)
                current_unit = values[i_index].split("/")[-1]
            elif line_number > num_header_lines and time_index is not None:
                time_str = values[time_index].split(' ')[1]
                hours, minutes, seconds = map(float, time_str.split(':'))
                total_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
                time_values.append(float(total_seconds))
                i_values.append(float(values[i_index]))
                v_values.append(float(values[v_index]))

    df = pd.DataFrame({'I': i_values, 'V': v_values, 'Time': time_values})
    mask = df['Time'] > preconditioning_time + df['Time'].iloc[0]
    df_filtered = df[mask].drop(columns=['Time']).reset_index(drop=True)

    output_csv_path = mpt_path.replace('.mpt', '.csv')
    with open(output_csv_path, 'w', newline='', encoding='utf-16') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Date and time:,' + current_datetime])
        csvwriter.writerow(['Notes:'])
        csvwriter.writerow([])
        csvwriter.writerow(['Cyclic Voltammetry: CV i vs E'])
        csvwriter.writerow(['Date and time measurement:,' + current_datetime])
        csvwriter.writerow(['V', current_unit])
        for _, row in df_filtered.iterrows():
            csvwriter.writerow([row['V'], row['I']])

    return output_csv_path


def convert_folder_mpt_to_csv(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.mpt'):
            mpt_path = os.path.join(folder_path, filename)
            convert_mpt_to_csv(mpt_path)


path = r'D:/OneDrive - O365 Turun yliopisto/IV_plotting_project/Test for Maryam/Washed out'
convert_folder_mpt_to_csv(path)

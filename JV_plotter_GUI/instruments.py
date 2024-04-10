import math
import os
import random
import subprocess
import sys
from collections import OrderedDict

import pandas as pd
from natsort import natsorted
from pandas import DataFrame


def open_file(path_to_file):
    """
    Run a file. Works on different platforms
    :param path_to_file: Path to a file
    :return:
    """
    if sys.platform == "win32":
        os.startfile(path_to_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path_to_file])


def print_nested_dict(d, indent=0) -> None:
    """
    Recursively prints keys and values of a nested dictionary.

    :param d: Dictionary to be printed.
    :param indent: Initial indentation for pretty printing. Default is 0.
    """
    for key, value in d.items():
        print('  ' * indent + str(key))
        if isinstance(value, dict):
            print_nested_dict(value, indent + 1)
        else:
            print('  ' * (indent + 1) + str(value))


def flip_data_if_necessary(df: DataFrame) -> DataFrame:
    """
    Flip the data if necessary so that the Maximum Power Point (MPP) is on positive I and V.

    :param df: The DataFrame containing the IV data with columns 'I' and 'V'
    :return: The DataFrame with data flipped if necessary
    """
    df.loc[:, 'I'] = df['I'].astype(float)
    df.loc[:, 'V'] = df['V'].astype(float)
    ind_voc = abs(df['I']).idxmin()
    v_oc_test = df['V'][ind_voc]
    ind_isc = abs(df['V']).idxmin()
    i_sc_test = df['I'][ind_isc]

    # Check if flipping is necessary, and flip if required
    if v_oc_test < 0:
        df.loc[:, 'V'] = -df['V']
    if i_sc_test < 0:
        df.loc[:, 'I'] = -df['I']

    return df


def row_to_excel_col(row_num):
    """
    Convert a row number to an Excel column letter.

    :param row_num: Row number.
    :return: Excel column letter.
    """
    col = ''
    while row_num:
        remainder = (row_num - 1) % 26
        col = chr(65 + remainder) + col
        row_num = (row_num - 1) // 26
    return col


def custom_round(max_value):
    """
    Custom rounding function.

    :param max_value: Maximum value to round.
    :return: Rounded value.
    """
    if max_value <= 9:
        next_rounded_value = math.ceil(max_value)
    elif max_value <= 99:
        next_rounded_value = math.ceil(max_value / 5) * 5
    elif max_value <= 999:
        next_rounded_value = math.ceil(max_value / 50) * 50
    elif max_value <= 9999:
        next_rounded_value = math.ceil(max_value / 100) * 100
    else:
        next_rounded_value = math.ceil(max_value / 10) * 10  # Default rounding to next 10
    return next_rounded_value


def random_color() -> str:
    """
    Generate a random color in hexadecimal RGB format.

    :return: A string representing the random color in hexadecimal format (e.g., '#FFFFFF').
    :rtype: str
    """
    return f"#{''.join([f'{random.randint(0, 255):02X}' for _ in range(3)])}"


def convert_df_to_dict(obj):
    """
    Recursively convert Pandas DataFrames to dictionaries within a nested dictionary.

    :param obj: The object to convert. It can be a dictionary or a Pandas DataFrame.
    :type obj: object

    :return: The converted object. If the input was a dictionary, all nested DataFrames will be converted to dicts.
    :rtype: object
    """
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    elif isinstance(obj, dict):
        for key in obj.keys():
            obj[key] = convert_df_to_dict(obj[key])
    return obj


def remove_data_key(d):
    """
    Recursively remove the 'data' key from a dictionary.

    :param d: dictionary to process
    :return: new dictionary without 'data' keys
    """
    new_dict = {}
    for key, value in d.items():
        if key == 'data':
            continue
        if isinstance(value, dict):
            new_dict[key] = remove_data_key(value)
        else:
            new_dict[key] = value
    return new_dict


def sort_inner_keys(data):
    """
    Sorts the inner keys of a nested dictionary while keeping the outer keys intact.

    :param data: The nested dictionary with data to be sorted.
    :return: A new dictionary with sorted inner keys.
    """
    sorted_data = {}

    for date, inner_dict in data.items():
        sorted_keys = natsorted(inner_dict.keys())
        sorted_inner_dict = OrderedDict((key, inner_dict[key]) for key in sorted_keys)
        sorted_data[date] = sorted_inner_dict
    return sorted_data


def get_newest_file_global(root_dir, suffix: str):
    """
    Get the newest file that contains the given suffix in the specified directory and its subdirectories.

    :param root_dir: The root directory to start the search
    :param suffix: The suffix to look for in filenames
    :return: The path to the newest file that contains the suffix, or None if no such file is found
    """
    newest_file = None
    newest_time = 0

    # Walk through the directory, including subdirectories
    for dir_path, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if suffix in filename:
                full_path = os.path.join(dir_path, filename)
                m_time = os.path.getmtime(full_path)
                if m_time > newest_time:
                    newest_time = m_time
                    newest_file = full_path

    return newest_file


def remove_non_monotonic_last_value(df: DataFrame) -> DataFrame:
    # Determine the monotonicity trend between the second-to-last and third-to-last value
    increasing = df['V'].iloc[-3] < df['V'].iloc[-2]
    decreasing = df['V'].iloc[-3] > df['V'].iloc[-2]

    # Remove the last value if it breaks the monotonicity trend
    if increasing and not df['V'][-3:].is_monotonic_increasing:
        return df[:-1]
    elif decreasing and not df['V'][-3:].is_monotonic_decreasing:
        return df[:-1]
    return df


def validate_numeric_entry(event):
    """Validate the entry to allow only numeric input, including negative values."""
    entry_widget = event.widget
    text = entry_widget.get()

    # Allow negative numbers and numbers with a single decimal point
    if text and not (text.replace('.', '', 1).isdigit() or
                     (text.startswith('-') and text[1:].replace('.', '', 1).isdigit())):
        # If the current value isn't empty, it's not numeric, and it's not a negative number
        # (allowing one decimal point), reset the text to the last valid value.
        entry_widget.delete(0, 'end')  # Remove current text
        try:
            entry_widget.insert(0, entry_widget.last_valid_value)  # Insert last valid value
        except AttributeError:
            pass
    else:
        # If the input is valid, store the current value as the last valid value.
        entry_widget.last_valid_value = text

import math
import os
import sys
import subprocess
import random

import pandas as pd


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


def flip_data_if_necessary(df):
    """
    Flip the data if necessary so that the Maximum Power Point (MPP) is on positive I and V.

    :param df: The DataFrame containing the IV data with columns 'I' and 'V'
    :return: The DataFrame with data flipped if necessary
    """
    df['I'] = df['I'].astype(float)
    df['V'] = df['V'].astype(float)
    ind_voc = abs(df['I']).idxmin()
    v_oc_test = df['V'][ind_voc]
    ind_isc = abs(df['V']).idxmin()
    i_sc_test = df['I'][ind_isc]

    # Check if flipping is necessary, and flip if required
    if v_oc_test < 0:
        df['V'] = -df['V']
    if i_sc_test < 0:
        df['I'] = -df['I']

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

    :param obj: The object to convert. Can be a dictionary or a Pandas DataFrame.
    :type obj: object

    :return: The converted object. If the input was a dictionary, all nested DataFrames will be converted to dictionaries.
    :rtype: object
    """
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    elif isinstance(obj, dict):
        for key in obj.keys():
            obj[key] = convert_df_to_dict(obj[key])
    return obj

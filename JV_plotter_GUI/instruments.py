import math
import os
import sys
import subprocess


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

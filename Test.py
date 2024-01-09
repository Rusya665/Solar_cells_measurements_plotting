import json

from icecream import ic

path = r'C:/Users/runiza_admin/OneDrive - O365 Turun yliopisto/Documents/Aging tests/2023 Carbon revival/3. New thing, dark storage/Measurememnts separated/Mahboubeh/2023-12-07 Mahboubeh data.json'


def print_json_structure(data, indent=0):
    """
    Recursively prints the structure of a JSON object.

    :param data: The JSON data to print the structure of.
    :param indent: The indentation level (used for nested structures).
    """
    for key, value in data.items():
        print(' ' * indent + str(key), end=': ')
        if isinstance(value, dict):
            print("{Dictionary}")
            print_json_structure(value, indent + 4)
        # elif isinstance(value, list):
        #     print("{List}")
        else:
            print(f"{type(value).__name__}")

# Read the JSON file
with open(path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Print the structure
print_json_structure(json_data)
# for key, val in json_data.items():
#     for key1 in val.keys():
#         ic(key, key1)
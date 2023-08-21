import os
from icecream import ic


def find_common_prefix(s1, s2):
    i = 0
    while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
        i += 1
    return s1[:i]


def find_common_suffix(s1, s2):
    i = -1
    while abs(i) <= len(s1) and abs(i) <= len(s2) and s1[i] == s2[i]:
        i -= 1
    return s1[i + 1:] if i != -1 else ''


def adjust_filename(filename, matched_file):
    stripped_name = os.path.splitext(filename)[0]
    stripped_matched = os.path.splitext(matched_file)[0]

    # Find common prefix and suffix
    common_prefix = find_common_prefix(stripped_name, stripped_matched)
    common_suffix = find_common_suffix(stripped_name, stripped_matched)

    # Extract distinguishing middle section from the filename
    middle_section = stripped_name[len(common_prefix):-len(common_suffix) or None]
    ic(common_prefix, common_suffix)
    return f"{common_prefix}{middle_section}{common_suffix}.txt"


# Test
filename1 = '13FC2LgFw-slow.txt'
matched_file1 = '13FC2LgRv-slow.txt'
print(adjust_filename(filename1, matched_file1))

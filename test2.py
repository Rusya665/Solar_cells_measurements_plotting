def find_pairs(file_list):
    forward_files = {}
    reverse_files = {}
    unpaired_files = []

    for file in file_list:
        if "Fw" in file:
            key = file.replace("-Fw", "").replace("Fw", "").replace("-slow", "")
            if key in reverse_files:
                print(f'Pair found: "{file}" and "{reverse_files[key]}"')
                del reverse_files[key]
            else:
                forward_files[key] = file

        elif "Rv" in file:
            key = file.replace("-Rv", "").replace("Rv", "").replace("-slow", "")
            if key in forward_files:
                print(f'Pair found: "{forward_files[key]}" and "{file}"')
                del forward_files[key]
            else:
                reverse_files[key] = file

    unpaired_files = list(forward_files.values()) + list(reverse_files.values())

    if unpaired_files:
        print("\nUnpaired files:")
        for file in unpaired_files:
            print(file)
    else:
        print("All files are paired.")


# Call the function with your list of files
find_pairs([
    "13FC2LgFw-slow (axis cros).txt",
    "13FC2LgFw-slow.txt",
    "13FC2LgFw.txt",
    "13FC2LgRv-slow.txt",
    "13FC2LgRV.txt",
    "1CC4LgFw.txt",
    "1CC4LgRv.txt"
])

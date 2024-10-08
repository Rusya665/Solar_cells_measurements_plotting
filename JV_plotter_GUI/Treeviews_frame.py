from functools import partial
from tkinter import ttk, END

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from JV_plotter_GUI.Active_areas_detector import ActiveAreaDetector


class TableFrames(ctk.CTkFrame):
    def __init__(self, parent, height=200, *args, **kwargs):
        super().__init__(master=parent, height=height, *args, **kwargs)
        self.scrollbar_x = None
        self.active_areas_table_frame = None
        self.scrollbar = None
        self.active_areas_canvas = None
        self.height = height
        self.parent = parent
        self.files_table_frame = ctk.CTkFrame(master=self, width=350, height=self.height)
        self.files_table_frame.grid(row=0, column=0, sticky='nsew')
        self.active_areas_scrollable_frame = ctk.CTkScrollableFrame(master=self, width=350, height=self.height,
                                                                    corner_radius=0, fg_color="transparent")
        self.active_areas_scrollable_frame.grid(row=0, column=1, sticky="nsew")
        self.active_areas_table = None
        self.active_areas_table_scrollbar = None
        self.files_table = None
        self.files_table_scrollbar = None
        self.devices = {}
        self.cached_areas = {}
        self.areas_auto_detected = {}
        self.files_table_insert()

    def files_table_insert(self):
        self.files_table_scrollbar = ctk.CTkScrollbar(master=self.files_table_frame)
        self.files_table_scrollbar.pack(side='right', fill='y')
        self.files_table = ttk.Treeview(master=self.files_table_frame, columns=('Device', 'I unit'),
                                        selectmode='extended', height=self.parent.table_size,
                                        yscrollcommand=self.files_table_scrollbar.set)
        self.files_table.heading('#0', text='Name', anchor='w')
        self.files_table.heading(0, text='Device', anchor='w')
        self.files_table.heading(1, text='I unit', anchor='w')
        self.files_table.column('#0', width=300)
        self.files_table.column(0, width=100)
        self.files_table.column(1, width=100)
        self.files_table.pack(side='left', fill='y')
        self.files_table_scrollbar.configure(command=self.files_table.yview)

    def construct_active_areas_entries(self, data, path_for_auto_aa_detect, path_to_aa_file=None) -> None:
        self.areas_auto_detected = None
        for child in self.active_areas_scrollable_frame.winfo_children():
            child.destroy()
        self.devices = data
        label0 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text='№', fg_color="transparent")
        label1 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text="Device", fg_color="transparent")
        label2 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text="Active area, mm²", fg_color="transparent")
        label0.grid(row=0, column=0, sticky='nsew', padx=5)
        label1.grid(row=0, column=1, sticky='nsew', padx=5)
        label2.grid(row=0, column=2, sticky='nsew')

        self.active_areas_scrollable_frame.columnconfigure(1, weight=1)
        aa_detector = ActiveAreaDetector(path=path_for_auto_aa_detect, active_area_json=path_to_aa_file)
        if path_to_aa_file is None:
            self.areas_auto_detected = aa_detector.check_directory()
        else:
            self.areas_auto_detected = aa_detector.load_predefined_areas()
        default_area = ''

        if self.areas_auto_detected:
            # Check if areas is a nested dictionary
            if all(isinstance(value, dict) for value in self.areas_auto_detected.values()):
                # Nested structure case
                first_folder = next(iter(self.areas_auto_detected.values()))
                default_area = next(iter(first_folder.values()))
            else:
                # Single key-value pair case (old logic)
                default_area = next(iter(self.areas_auto_detected.values()))

        # Initialize self.cached_areas if it's empty
        if not self.cached_areas:
            for folder_name, devices in self.devices.items():
                self.cached_areas[folder_name] = {device_name: {} for device_name in devices}

        unique_devices = set()
        row_counter = 1
        for folder_name, devices in self.devices.items():
            for device_name, device_data in devices.items():
                if device_name not in unique_devices:
                    unique_devices.add(device_name)
                    device_counter = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                                  text=f'{row_counter}', fg_color="transparent")
                    device_counter.grid(row=row_counter, column=0, sticky='nsew', padx=5)
                    device_label = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                                text=device_name, fg_color='transparent')
                    device_label.grid(row=row_counter, column=1, sticky='nsew')
                    active_area_entry = ctk.CTkEntry(master=self.active_areas_scrollable_frame)
                    active_area_entry.grid(row=row_counter, column=2, sticky='nsew')
                    active_area_entry.bind('<KeyRelease>', partial(self.type_dict_fill,
                                                                   folder_name=folder_name, device_name=device_name))

                    if self.areas_auto_detected:
                        # Check if the folder and device names exist in the detected areas dictionary
                        if (isinstance(self.areas_auto_detected.get(folder_name), dict) and
                                device_name in self.areas_auto_detected[folder_name]):
                            active_area_entry.insert(END, self.areas_auto_detected[folder_name][device_name])
                        elif device_name in self.areas_auto_detected:
                            active_area_entry.insert(END, self.areas_auto_detected[device_name])
                        elif self.parent.iaa:
                            active_area_entry.insert(END, default_area)
                        else:
                            active_area_entry.insert(END,
                                                     '')  # If the key isn't in the dictionary, add an empty string

                    row_counter += 1

    def type_dict_fill(self, event, folder_name, device_name):
        """
        Handle the event when a key is released in an Entry widget for active areas.
        If self.parent.iaa is True, update all other Entry widgets with the entered value.
        Otherwise, update the cached_areas dictionary for the specific device.
        If the entered value is empty or only contains whitespace, no action is taken.

        :param event: The event object which contains information about the key release event.
        :param folder_name: The name of the folder containing the device.
        :param device_name: The name of the device for which the active area is being entered.
        """
        # Get the Entry widget that fired the event
        entry_widget = event.widget
        # Extract the value typed by the user into the Entry widget
        entered_value = entry_widget.get().strip()  # Using strip() to remove leading and trailing whitespace

        # If the entered value is empty, return without doing anything
        if not entered_value:
            return

        # If self.parent.iaa is True, then update all other Entry widgets with the entered value
        if self.parent.iaa:
            for child in self.active_areas_scrollable_frame.winfo_children():
                if isinstance(child,
                              ctk.CTkEntry) and child != entry_widget:  # Exclude the original entry
                    # from being updated again
                    child.delete(0, END)
                    child.insert(0, entered_value)
        else:
            # Only update the cached_areas dictionary for the specific device
            if folder_name not in self.cached_areas:
                self.cached_areas[folder_name] = {}
            self.cached_areas[folder_name][device_name] = entered_value

    def update_entries_from_cache(self):
        """
        Update the Entry widgets from the cached self.cached_areas dictionary based on device names (keys).
        """
        # Loop through the children of the active_areas_scrollable_frame to find Entry widgets
        for child in self.active_areas_scrollable_frame.winfo_children():
            if isinstance(child, ctk.CTkEntry):
                # Assuming the device name (key) is the text of the preceding label (child.grid_info()['row']
                # gives the row number)
                device_label = self.active_areas_scrollable_frame.grid_slaves(row=child.grid_info()['row'], column=1)[0]
                device_name = device_label.cget(
                    'text')  # Getting the text of the label which corresponds to the device name

                entry_value = None  # Initialize entry_value to None

                # Iterate through the cached_areas to find the corresponding value
                for folder, devices in self.cached_areas.items():
                    if device_name in devices:
                        entry_value = devices[device_name]
                        break

                # Check if entry_value is found and not an empty dictionary
                if entry_value is not None and entry_value != {}:
                    child.delete(0, END)  # Clear the Entry
                    child.insert(0, entry_value)

    def devices_by_folder(self, items):
        folder_file_dict = {}
        topmost_folder = None

        for item in items:
            parent = self.files_table.parent(item)

            if not parent:
                folder_name = self.files_table.item(item)["text"]

                if self.parent.aging_mode:
                    topmost_folder = folder_name
                    continue
                else:
                    if folder_name not in folder_file_dict:
                        folder_file_dict[folder_name] = []
            else:
                folder_name = self.files_table.item(parent)["text"]
                if folder_name == topmost_folder:
                    continue

                file_name = self.files_table.item(item)["text"]
                if folder_name not in folder_file_dict:
                    folder_file_dict[folder_name] = []
                folder_file_dict[folder_name].append(file_name)
        matched_devices = {}
        for folder, selected_files in folder_file_dict.items():
            for device, sub_keys in self.devices[folder].items():
                if isinstance(sub_keys['Used files'], tuple):
                    if any(file in selected_files for file in sub_keys['Used files']):
                        if folder not in matched_devices:
                            matched_devices[folder] = {}
                        matched_devices[folder][device] = sub_keys
                else:
                    if sub_keys['Used files'] in selected_files:
                        if folder not in matched_devices:
                            matched_devices[folder] = {}
                        matched_devices[folder][device] = sub_keys

        return self.update_matched_devices_from_entries(matched_devices)

    def update_matched_devices_from_entries(self, matched_devices):
        """
        Update the 'Active area' sub-key in matched_devices with the corresponding entry values.

        :param matched_devices: Dictionary containing the matched devices.
        """

        for child in self.active_areas_scrollable_frame.winfo_children():
            if isinstance(child, ctk.CTkEntry):
                device_label = self.active_areas_scrollable_frame.grid_slaves(row=child.grid_info()['row'], column=1)[0]
                device_name = device_label.cget('text')
                entry_value = child.get()
                for folder, devices in matched_devices.items():
                    if device_name in devices:
                        if not entry_value:
                            CTkMessagebox(title='Warning!',
                                          message=f"Missing active area value for the device:\n{device_name}",
                                          icon="warning", option_1='Okay, this is bad')
                            return
                        try:
                            entry_value = float(entry_value)
                            if entry_value <= 0:
                                CTkMessagebox(title='Warning!',
                                              message=f"Invalid active area value for the device: {device_name}. "
                                                      f"Please enter a positive numerical value greater"
                                                      f" than 0 (e.g., 5 or 5.25).",
                                              icon="warning", option_1='Okay, this is bad')
                                return
                        except ValueError:
                            CTkMessagebox(title='Warning!',
                                          message=f"Invalid active area value for the device: {device_name}. "
                                                  f"Please enter a positive numerical value greater than 0"
                                                  f" (e.g., 5 or 5.25).",
                                          icon="warning", option_1='Okay, this is bad')
                            return
                        # Update matched_devices with the active area
                        # Case when Active Areas were successfully autodetect (or a user pointed ot the file)
                        # and it's a nested dictionary.
                        if (isinstance(self.areas_auto_detected, dict) and
                                isinstance(self.areas_auto_detected.get(folder), dict) and
                                device_name in self.areas_auto_detected[folder]):
                            matched_devices[folder][device_name]['Active area (cm²)'] =\
                                self.areas_auto_detected[folder][device_name] / 100
                        # Case when Active Areas were successfully autodetect (or a user pointed ot the file)
                        # and it's not a nested dictionary.
                        elif self.areas_auto_detected and device_name in self.areas_auto_detected:
                            matched_devices[folder][device_name]['Active area (cm²)'] =\
                                self.areas_auto_detected[device_name] / 100
                        # Manually given active areas. If active ares were successfully detected, this will override
                        # only not nested ones.
                        else:
                            matched_devices[folder][device_name]['Active area (cm²)'] = entry_value / 100

                        matched_devices[folder][device_name]['Light intensity (W/cm²)'] = \
                            float(self.parent.additional_settings.light_intensity_entry.get()) / 10000  # Store values
                        matched_devices[folder][device_name]['Distance to light source (mm)'] = \
                            float(self.parent.additional_settings.distance_to_light_entry.get())
        return matched_devices

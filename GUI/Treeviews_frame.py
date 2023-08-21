from functools import partial
from tkinter import ttk, END
import customtkinter as ctk

from tkinter import messagebox
from GUI.Device_filter import DeviceDetector
from Active_areas import ActiveAreaDetector


class TableFrames(ctk.CTkFrame):
    def __init__(self, parent, height=200, *args, **kwargs):
        super().__init__(master=parent, height=height, *args, **kwargs)
        self.scrollbar_x = None
        self.active_areas_table_frame = None
        self.scrollbar = None
        self.active_areas_canvas = None
        self.height = height
        self.parent = parent
        self.files_table_frame = ctk.CTkFrame(master=self, width=300, height=self.height)
        self.files_table_frame.grid(row=0, column=0, sticky='nsew')
        self.active_areas_scrollable_frame = ctk.CTkScrollableFrame(master=self, width=300, height=self.height,
                                                                    corner_radius=0, fg_color="transparent")
        self.active_areas_scrollable_frame.grid(row=0, column=1, sticky="nsew")
        self.active_areas_table = None
        self.active_areas_table_scrollbar = None
        self.files_table = None
        self.files_table_scrollbar = None
        self.devices = {}
        self.cached_areas = {}
        self.files_table_insert()

    def files_table_insert(self):
        self.files_table_scrollbar = ctk.CTkScrollbar(master=self.files_table_frame)
        self.files_table_scrollbar.pack(side='right', fill='y')
        self.files_table = ttk.Treeview(master=self.files_table_frame, columns=('Device', 'Efficiency'),
                                        selectmode='extended', height=self.parent.table_size,
                                        yscrollcommand=self.files_table_scrollbar.set)
        self.files_table.heading('#0', text='Name', anchor='w')
        self.files_table.heading(0, text='Device', anchor='w')
        self.files_table.heading(1, text='Efficiency', anchor='w')
        self.files_table.column('#0', width=300)
        self.files_table.column(0, width=100)
        self.files_table.column(1, width=100)
        self.files_table.pack(side='left', fill='y')
        self.files_table_scrollbar.configure(command=self.files_table.yview)
        # self.files_table.bind('<<TreeviewSelect>>', lambda event: self.parent.items_select())

    def get_selected_devices_from_treeview(self):
        """
        Extract and return the names of devices from the selected items in the Treeview.
        """
        selected_items = self.files_table.selection()
        return [self.files_table.item(item)["text"] for item in selected_items]

    def construct_active_areas_entries(self, data, path) -> None:
        for child in self.active_areas_scrollable_frame.winfo_children():
            child.destroy()
        self.devices = DeviceDetector(data_dict=data).detect_and_filter()
        label0 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text='№', fg_color="transparent")
        label1 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text="Device", fg_color="transparent")
        label2 = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                              text="Active area", fg_color="transparent")
        label0.grid(row=0, column=0, sticky='nsew', padx=5)
        label1.grid(row=0, column=1, sticky='nsew', padx=5)
        label2.grid(row=0, column=2, sticky='nsew')
        areas = ActiveAreaDetector(path=path).check_directory()
        # Only initialize self.cached_areas if it's empty
        if not self.cached_areas:
            self.cached_areas = {key: {} for key in self.devices}

        for i, (key, value) in enumerate(self.devices.items()):
            device_counter = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                          text=i + 1, fg_color="transparent")
            device_counter.grid(row=i + 1, column=0, sticky='nsew', padx=5)
            device_name = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                       text=key, fg_color='transparent')
            device_name.grid(row=i + 1, column=1, sticky='nsew')
            active_area_entry = ctk.CTkEntry(master=self.active_areas_scrollable_frame)
            active_area_entry.bind('<KeyRelease>', partial(self.type_dict_fill, device_name=key))

            # Commenting out the binding as it seems unnecessary for current functionality.
            # active_area_entry.bind('<KeyRelease>', lambda event: self.type_dict_fill())
            active_area_entry.grid(row=i + 1, column=2, sticky='nsew')

            if areas:
                if self.parent.iaa is True:
                    _, first_value = next(iter(areas.items()))
                    active_area_entry.insert(END, first_value)
                else:
                    # Check if the key (device name) exists in the detected areas dictionary
                    if key in areas:
                        active_area_entry.insert(END, areas[key])
                    else:
                        active_area_entry.insert(END, '')  # If the key isn't in the dictionary, add an empty string

    def type_dict_fill(self, event, device_name):
        # Get the Entry widget that fired the event
        entry_widget = event.widget
        # Extract the value typed by the user into the Entry widget
        entered_value = entry_widget.get()

        # If self.parent.iaa is True, then update all other Entry widgets with the entered value
        if self.parent.iaa:
            for child in self.active_areas_scrollable_frame.winfo_children():
                if isinstance(child, ctk.CTkEntry) and child != entry_widget:  # Exclude the original entry from
                    # being updated again
                    child.delete(0, END)
                    child.insert(0, entered_value)
        else:
            # Only update the cached_areas dictionary for the specific device
            self.cached_areas[device_name] = entered_value

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
                # Check if the device name exists in the cached dictionary and update the Entry content
                if device_name in self.cached_areas and self.cached_areas[device_name]:
                    child.delete(0, END)  # Clear the Entry
                    child.insert(0, self.cached_areas[device_name])

    def devices_by_folder(self, items):
        folder_file_dict = {}
        for item in items:
            parent = self.files_table.parent(item)
            if not parent:  # This is a top-level node, i.e., a folder
                folder_name = self.files_table.item(item)["text"]
                # Initialize an empty list for this folder if it doesn't exist yet.
                if folder_name not in folder_file_dict:
                    folder_file_dict[folder_name] = []
            else:
                folder_name = self.files_table.item(parent)["text"]
                file_name = self.files_table.item(item)["text"]
                if folder_name not in folder_file_dict:
                    folder_file_dict[folder_name] = []
                folder_file_dict[folder_name].append(file_name)

        # Create a list of devices to retain
        devices_to_retain = []

        for folder, selected_files in folder_file_dict.items():
            for device, subkeys in self.devices.items():
                if isinstance(subkeys['Used files'], tuple):  # if the 'Used files' is a tuple
                    if any(file in selected_files for file in subkeys['Used files']):
                        devices_to_retain.append(device)
                else:
                    if subkeys['Used files'] in selected_files:
                        devices_to_retain.append(device)

        # Make devices_to_retain unique
        devices_to_retain = list(set(devices_to_retain))

        # Extract only the devices that match from self.devices
        matched_devices = {k: self.devices[k] for k in devices_to_retain}
        return self.update_matched_devices_from_entries(matched_devices)

    def update_matched_devices_from_entries(self, matched_devices):
        """
        Update the 'Active area' sub-key in matched_devices with the corresponding entry values.

        :param matched_devices: Dictionary containing the matched devices.
        """
        # Loop through the children of the active_areas_scrollable_frame
        for child in self.active_areas_scrollable_frame.winfo_children():
            if isinstance(child, ctk.CTkEntry):
                # Get the corresponding label (assuming it's in the previous column of the same row)
                device_label = self.active_areas_scrollable_frame.grid_slaves(row=child.grid_info()['row'], column=1)[0]
                device_name = device_label.cget('text')

                # If device_name is not in matched_devices, skip this iteration
                if device_name not in matched_devices:
                    continue

                entry_value = child.get()

                # Check if entry_value is missing data
                if not entry_value.strip():
                    messagebox.showerror('Warning!', f"Missing data for device: {device_name}")
                    return

                # Check if entry_value can be interpreted as a float
                try:
                    entry_value = float(entry_value)
                except ValueError:
                    # Display an error message to the user if conversion to float fails
                    messagebox.showerror('Warning!',
                                         f"Invalid data for device: {device_name}."
                                         f" Please enter a valid numerical value (e.g., 5 or 5.25).")
                    return

                # Update the matched_devices dictionary
                matched_devices[device_name]['Active area'] = entry_value

        return matched_devices

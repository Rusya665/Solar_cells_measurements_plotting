import os
from functools import partial
from tkinter import ttk, END
from icecream import ic
import customtkinter as ctk

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
        self.given_areas = {}
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
        self.files_table.bind('<<TreeviewSelect>>', lambda event: self.parent.items_select())

    def construct_active_areas_entries(self, data, path) -> None:
        for child in self.active_areas_scrollable_frame.winfo_children():
            child.destroy()
        devices = DeviceDetector(data_dict=data).detect_and_filter()
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
        self.given_areas = {key: {} for key in devices}

        for i, (key, value) in enumerate(devices.items()):
            device_counter = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                          text=i + 1, fg_color="transparent")
            device_counter.grid(row=i + 1, column=0, sticky='nsew', padx=5)
            device_name = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                       text=key, fg_color='transparent')
            device_name.grid(row=i + 1, column=1, sticky='nsew')
            active_area_entry = ctk.CTkEntry(master=self.active_areas_scrollable_frame)
            active_area_entry.bind('<KeyRelease>', partial(self.type_dict_fill, device_name=key))
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
        # Update the self.given_areas dictionary
        self.given_areas[device_name] = entered_value
        ic(self.given_areas)

import os
from tkinter import ttk, END

import customtkinter as ctk

from GUI.Device_filter import DeviceDetector


class TableFrames(ctk.CTkFrame):
    def __init__(self, parent, height=200, *args, **kwargs):
        super().__init__(master=parent, height=height, *args, **kwargs)
        self.scrollbar_x = None
        self.active_areas_table_frame = None
        self.scrollbar = None
        self.active_areas_canvas = None
        self.height = height
        self.parent = parent
        self.files_table_frame = ctk.CTkFrame(master=self, width=600, height=self.height)
        self.files_table_frame.grid(row=0, column=0, sticky='nsew')
        self.active_areas_scrollable_frame = ctk.CTkScrollableFrame(master=self, width=200, height=self.height,
                                                                    corner_radius=0, fg_color="transparent")
        self.active_areas_scrollable_frame.grid(row=0, column=1, sticky="nsew")
        self.active_areas_table = None
        self.active_areas_table_scrollbar = None
        self.files_table = None
        self.files_table_scrollbar = None
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
        self.files_table.column('#0', width=350)
        self.files_table.column(0, width=150)
        self.files_table.column(1, width=100)
        self.files_table.pack(side='left', fill='y')
        self.files_table_scrollbar.configure(command=self.files_table.yview)
        self.files_table.bind('<<TreeviewSelect>>', lambda event: self.parent.items_select())

    def construct_active_areas_entries(self, data) -> None:
        for child in self.active_areas_scrollable_frame.winfo_children():
            child.destroy()
        devices = DeviceDetector(data_dict=data).detector()
        for i, (key, value) in enumerate(data.items()):
            device_counter = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
                                          text=f'{i + 1}', fg_color="transparent")
            # device_counter = ctk.CTkLabel(master=self.active_areas_scrollable_frame,
            #                               text=os.path.splitext(key)[0], fg_color="transparent")
            device_counter.grid(row=i, column=0, sticky='nsew', padx=5)
            device_name = ctk.CTkEntry(master=self.active_areas_scrollable_frame)
            device_name.grid(row=i, column=1, sticky='nsew')
            device_name.insert(END, os.path.splitext(key)[0])

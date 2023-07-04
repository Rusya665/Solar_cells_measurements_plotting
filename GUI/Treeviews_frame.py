import os
from tkinter import ttk, END

import customtkinter as ctk

from Device_filter import DeviceDetector


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
        self.active_areas_parental_frame = ctk.CTkFrame(master=self, width=200, height=self.height,
                                                        fg_color="transparent")
        self.active_areas_parental_frame.grid(row=0, column=1, sticky='nsew')
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.active_areas_table = None
        self.active_areas_table_scrollbar = None
        self.files_table = None
        self.files_table_scrollbar = None
        self.files_table_insert()
        self.construct_active_areas_child_frame()

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

    def construct_active_areas_child_frame(self):
        self.active_areas_canvas = ctk.CTkCanvas(master=self.active_areas_parental_frame, width=200, height=self.height)
        self.active_areas_canvas.configure(bg='gray17')

        self.active_areas_canvas.grid(row=0, column=0, sticky='nsew')
        self.active_areas_table_frame = ctk.CTkFrame(master=self.active_areas_parental_frame, width=200, height=self.height,
                                                     fg_color="transparent")

        # self.active_areas_table_frame.grid(minsize=(200, self.height))  # setting minsize
        self.active_areas_canvas.create_window((0, 0), window=self.active_areas_table_frame, anchor='nw')

        self.active_areas_table_frame.bind('<Configure>', self.on_frame_configure)
        self.scrollbar = ctk.CTkScrollbar(master=self.active_areas_canvas, orientation='vertical',
                                          command=self.active_areas_canvas.yview)
        self.scrollbar_x = ctk.CTkScrollbar(master=self.active_areas_canvas, orientation='horizontal',
                                            command=self.active_areas_canvas.xview)
        self.active_areas_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.active_areas_canvas.configure(xscrollcommand=self.scrollbar_x.set)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.scrollbar_x.grid(row=1, column=0, sticky='we')

    def on_frame_configure(self, event=None):
        self.active_areas_canvas.configure(scrollregion=self.active_areas_canvas.bbox('all'))

    def construct_active_areas_entries(self, data) -> None:
        for child in self.active_areas_table_frame.winfo_children():
            child.destroy()
        DeviceDetector(data_dict=data).detector()
        for i, (key, value) in enumerate(data.items()):
            device_counter = ctk.CTkLabel(master=self.active_areas_table_frame, text=f'{i + 1}', fg_color="transparent")
            device_counter.grid(row=i, column=0, sticky='nsew', padx=5)
            device_name = ctk.CTkEntry(master=self.active_areas_table_frame)
            device_name.grid(row=i, column=1, sticky='nsew')
            device_name.insert(END, os.path.splitext(key)[0])

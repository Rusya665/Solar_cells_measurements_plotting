import customtkinter as ctk
from tkinter import ttk


class TableFrames(ctk.CTkFrame):
    def __init__(self, parent, height=200, *args, **kwargs):
        super().__init__(master=parent, height=height, *args, **kwargs)
        self.parent = parent
        self.files_table_frame = ctk.CTkFrame(master=self, width=600, height=height)
        self.active_areas_table_frame = ctk.CTkFrame(master=self, width=200, height=height)
        self.files_table_frame.grid(row=0, column=0, sticky='nsew')
        self.active_areas_table_frame.grid(row=0, column=1, sticky='nsew')
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.active_areas_table = None
        self.active_areas_table_scrollbar = None
        self.files_table = None
        self.files_table_scrollbar = None
        self.files_table_insert()
        self.active_areas_table_insert()

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

    def active_areas_table_insert(self):
        self.active_areas_table_scrollbar = ctk.CTkScrollbar(master=self.active_areas_table_frame)
        self.active_areas_table_scrollbar.pack(side='right', fill='y')
        self.active_areas_table = ttk.Treeview(master=self.active_areas_table_frame, columns=('#1', '#2'),
                                               selectmode='extended', height=self.parent.table_size, show="headings",
                                               yscrollcommand=self.active_areas_table_scrollbar.set)
        self.active_areas_table.heading('#1', text='Name', anchor='w')
        self.active_areas_table.heading('#2', text='Active area', anchor='w')
        self.active_areas_table.column('#1', width=250)
        self.active_areas_table.column('#2', width=150)
        self.active_areas_table.pack(side='right', fill='y')
        self.active_areas_table_scrollbar.configure(command=self.files_table.yview)
        self.active_areas_table.bind('<<TreeviewSelect>>', lambda event: self.parent.items_select())

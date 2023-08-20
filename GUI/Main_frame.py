import os
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from Treeviews_frame import TableFrames
from The_lower_frames import LowestFrame, ProceedFrame
from Top_frame import FirstFrame
from GUI.Potentostats_check import PotentiostatFileChecker


class IVProcessingMainClass(ctk.CTkFrame):
    def __init__(self, parent, get_data, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)

        # Some variables
        self.parent = parent
        self.table_size = 15
        self.potentiostat = 'All'
        self.file_directory = '/'
        self.files_selected = []
        self.get_data = get_data
        self.added_iv = defaultdict(dict)
        self.aging_mode = False
        self.iaa = True
        # self.cached_active_areas = {}

        # widgets
        self.pack(fill=ctk.BOTH, expand=True)
        self.label_1 = ctk.CTkLabel(self, text='Specify a directory with images to work with')
        self.label_1.pack()

        self.button_1 = ctk.CTkButton(self, text='Choose a directory', command=lambda: self.ask_directory())
        self.button_1.pack()

        self.table_frame = TableFrames(parent=self, height=400)
        self.first_frame = FirstFrame(parent=self, width=350, height=70, fg_color='transparent')
        self.first_frame.pack()

        self.table_frame.pack(pady=10)

        self.frame = ProceedFrame(parent=self, width=200, height=200)
        self.frame.pack(pady=10)

        self.lowest_frame = LowestFrame(self, fg_color='transparent')
        self.lowest_frame.pack(fill='x')

        self.progress_bar = ctk.CTkProgressBar(master=self, width=300)
        self.progress_bar.pack()
        self.progress_bar.set(0)

    def aging_mode_activator(self) -> None:
        """
        Activate the "Aging mode"
        :return: None
        """
        self.aging_mode = bool(self.first_frame.aging_mode_checkbox.get())
        self.list_files()

    def identical_active_areas_activator(self) -> None:
        """
        Apply the same active areas for all devices
        :return: None
        """
        self.iaa = bool(self.first_frame.identical_areas_CheckBox.get())
        # self.list_files()

    def exit(self) -> None:
        """
        Close Tkinter and script
        :return: None
        """
        self.quit()

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str) -> None:
        """
        Change the Tkinter appearance mode
        :param new_appearance_mode: Type of appearance mode
        :return: None
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def final_output(self, state) -> None:
        """
        Choose the state to work on
        :param state: Selected some files or all the files
        :return: None
        """
        self.files_selected = []
        if state == "Selected":
            for item in self.table_frame.files_table.selection():
                self.treeview_expand_collapse(item, True, select=True)
                self.table_frame.files_table.set(item)
            self.items_select()
            self.out()
        if state == 'All':
            self.table_frame.files_table.selection_add(self.table_frame.files_table.get_children())
            for item in self.table_frame.files_table.get_children():
                self.treeview_expand_collapse(item, True, select=True)
            self.items_select()
            self.out()

    def expand_collapse(self, expand=True) -> None:
        """
        Only expand/collapse item in treeview
        :param expand: expand if True, collapse if False
        :return: None
        """
        for item in self.table_frame.files_table.get_children():
            self.treeview_expand_collapse(item, expand, select=False)

    def treeview_expand_collapse(self, item, expand_collapse, select=False) -> None:
        """
        Expand/collapse treeview. Select all nested elements in a table and expand parental ones
        :param select: select expanded values
        :param expand_collapse: True for expanding, False - collapsing
        :param item: Item to select
        :return: None
        """
        # Expand items
        self.table_frame.files_table.item(item, open=expand_collapse)
        if expand_collapse and select:
            self.table_frame.files_table.selection_add(item)
        # Select all nested (children) items
        if self.table_frame.files_table.get_children(item):
            for item_inner in self.table_frame.files_table.get_children(item):
                self.treeview_expand_collapse(item_inner, expand_collapse, select)

    def items_select(self) -> None:
        """
        Returns selected value/clues from the table
        :return: None
        """
        for i in self.table_frame.files_table.selection():
            if self.table_frame.files_table.item(i)['tags'] == ['file']:
                self.files_selected.append(self.table_frame.files_table.item(i)['values'][-1])

    def ask_directory(self) -> None:
        """
        Built-in Tkinter function to return a str with a path
        :return: String with a path
        """
        # self.file_directory = filedialog.askdirectory(mustexist=True)
        self.file_directory = r'D:\OneDrive - O365 Turun yliopisto\IV_plotting_project\Input'
        self.list_files()
        self.label_1.configure(text=self.file_directory)

    def set_potentiostat(self, event):
        """
        Set potentiostat for filtering all unnecessary files
        :param event: Chose potentiostat through the ComboBox or choose All
        """
        self.potentiostat = event
        if self.file_directory == '/':
            return
        self.list_files()

    def list_files(self):
        """
        Update and fill the file table with filtered files
        """
        if self.file_directory == '/':
            return
        # Check if there are any items in the treeview
        for i in self.table_frame.files_table.get_children():
            self.table_frame.files_table.delete(i)
        abspath = os.path.abspath(self.file_directory).replace('\\', '/')
        root_node = self.table_frame.files_table.insert('', 'end', text=os.path.basename(abspath), open=True)
        self.process_directory(root_node, abspath)

    def process_directory(self, parent, path, depth=1):
        """
        Insert to a table and into the file_list filtered by extension type of files, including nested folders.
        Will show folders only if it contains required file.
        :param parent: parent folder
        :param path: path to work with
        :param depth: depth of the folders path
        :return: None
        """
        potentiostat_checker = PotentiostatFileChecker(potentiostat_choice=self.potentiostat)
        self.added_iv.clear()
        for file in os.listdir(path):
            abspath = os.path.join(path, file).replace('\\', '/')
            b = path.replace(self.file_directory, '').count('/')
            if os.path.isfile(abspath):
                checking = potentiostat_checker.check_file(abspath)
                if checking[0]:  # Insert a file only if it's potentiostats file
                    potentiostat = checking[2]
                    data = [potentiostat, checking[1], abspath]
                    self.added_iv[f'{file}'] = {"path": abspath,
                                                'measurement device': potentiostat,
                                                'encoding': checking[1],
                                                'Sweeps': checking[3]["Counts"],
                                                'data': checking[3]["Data"]}
                    self.table_frame.files_table.insert(parent=parent, index=tk.END, text=file, values=data,
                                                        tags='file')
            if os.path.isdir(abspath):
                device_detected = False
                for dir_path, dir_names, files in os.walk(abspath):
                    for filename in files:
                        f_name = os.path.join(dir_path, filename).replace('\\', '/')
                        checking = potentiostat_checker.check_file(f_name)
                        if checking[0]:
                            device_detected = True
                if device_detected:
                    if b == depth:  # Nested folders with the deep of 1 only
                        # allowed for the Processed folders
                        return messagebox.showerror('Waring!', f"Too many sub folders in"
                                                               f" a folder {abspath}")
                    oid = self.table_frame.files_table.insert(parent, 'end', text=file, open=False, tags='folder',
                                                              values=['', '', abspath])
                    self.process_directory(oid, abspath)
        self.table_frame.construct_active_areas_entries(data=self.added_iv, path=self.file_directory)

    def out(self):
        """
        Resize images accordingly and generate output dict
        :return: None
        """
        if not self.files_selected:
            messagebox.showerror('Waring!', "Choose a folder(s) or an image(s) to continue!")
        else:
            folder_name = []
            counter = 0
            for ind, file in enumerate(self.files_selected):
                self.progress_bar.set(round((1 - (len(self.files_selected) - ind - 1) /
                                             len(self.files_selected)), 2))
                self.update_idletasks()
                dir_name = os.path.basename(Path(file).parents[0])
                if 'Processed/' in file:
                    dir_name = Path(file.split('Processed/')[0]).name
                folder_name.append(dir_name)
                if ind != 0 and not folder_name[ind - 1] == folder_name[ind]:
                    counter = 0
                counter += 1
            for widget in self.winfo_children():
                widget.quit()
            self.pack_forget()
            self.get_data(data=self.added_iv, extension=self.potentiostat, first_img=self.aging_mode)

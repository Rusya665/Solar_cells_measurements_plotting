import os
import tkinter as tk
from collections import defaultdict
from tkinter import messagebox, filedialog

import customtkinter as ctk

from JV_plotter_GUI.Potentostats_check import PotentiostatFileChecker
from JV_plotter_GUI.Plotter import DevicePlotter
from JV_plotter_GUI.Slide_frame import SettingsPanel
from JV_plotter_GUI.The_lower_frames import LowestFrame, ProceedFrame
from JV_plotter_GUI.TimeLine_detector import TimeLineProcessor
from JV_plotter_GUI.Top_frame import TopmostFrame
from JV_plotter_GUI.Treeviews_frame import TableFrames
from JV_plotter_GUI.settings import settings
from JV_plotter_GUI.Additional_settings_panel import AdditionalSettings


class IVProcessingMainClass(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)

        # Some variables
        self.parent = parent
        self.table_size = settings['Main frame']['table_size']
        self.potentiostat = 'All'
        self.file_directory = ""
        self.timeline_df = None
        self.files_selected = []
        self.added_iv = defaultdict(dict)
        self.aging_mode = False
        self.iaa = True
        self.open_wb = True

        # widgets
        self.pack(fill=ctk.BOTH, expand=True)
        self.table_frame = TableFrames(parent=self, height=400)
        self.additional_settings = AdditionalSettings(parent=self, start_pos=-0.25, end_pos=0)
        self.slide_frame = SettingsPanel(parent=self, start_pos=1.0, end_pos=0.75)
        self.label_1 = ctk.CTkLabel(self, text='Specify a directory with images to work with')
        self.label_1.pack()

        self.ask_directory_button = ctk.CTkButton(self, text='Choose a directory', command=lambda: self.ask_directory())
        self.ask_directory_button.pack()

        self.topmost_frame = TopmostFrame(parent=self, width=350, height=70, fg_color='transparent')
        self.topmost_frame.pack()

        self.table_frame.pack(pady=10)

        self.frame = ProceedFrame(parent=self, width=200, height=200)
        self.frame.pack(pady=10)

        self.lowest_frame = LowestFrame(self, fg_color='transparent')
        self.lowest_frame.pack(fill='x')

    def aging_mode_activator(self) -> None:
        """
        Activate the "Aging mode"
        :return: None
        """
        self.aging_mode = bool(self.slide_frame.aging_mode_checkbox.get())
        self.slide_frame.timeline_detector_button.configure(
            state='normal' if self.slide_frame.aging_mode_checkbox.get() else 'disabled')
        self.frame.button_selected.configure(
            state='disabled' if self.slide_frame.aging_mode_checkbox.get() else 'normal')
        self.list_files()

    def identical_active_areas_activator(self) -> None:
        """
        Apply the same active areas for all devices
        :return: None
        """
        self.iaa = bool(self.slide_frame.identical_areas_CheckBox.get())

    def open_wb_activator(self) -> None:
        """
        Open workbook at the end of the code
        :return: None
        """
        self.open_wb = bool(self.slide_frame.open_wb_checkbox.get())

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
        if self.file_directory is None:
            messagebox.showerror('Warning!', "Choose a folder to continue!")
            return
        items = []
        if state == "Selected":
            # This should fetch selected items and not all top-level items
            items = list(self.table_frame.files_table.selection())
        elif state == "All":
            if self.aging_mode and self.timeline_df is None:
                messagebox.showerror('Warning!', "For aging mode the timeline mast be set!")
                return
            # This should fetch all items in the tree, including children of top-level items
            items = list(self.table_frame.files_table.get_children(''))
            for top_level_item in items:
                child_items = list(self.table_frame.files_table.get_children(top_level_item))
                items.extend(child_items)
        matched = self.table_frame.devices_by_folder(items)
        DevicePlotter(parent=self, matched_devices=matched)
        self.exit()

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

    def ask_directory(self) -> None:
        """
        Built-in Tkinter function to return a str with a path
        :return: String with a path
        """
        if not self.additional_settings.in_start_pos:
            self.additional_settings.animate_additional_settings(step=1)
        if not self.slide_frame.in_start_pos:
            self.slide_frame.animate(step=1)
        self.file_directory = filedialog.askdirectory(mustexist=True)
        if self.file_directory == "":
            self.label_1.configure(text='Specify a directory with images to work with')
            return
        self.list_files()
        self.label_1.configure(text=self.file_directory)

    def specify_timeline(self):
        path_to_timeline = filedialog.askopenfilename()
        if path_to_timeline == "":
            self.slide_frame.time_label.configure(text='Aging time: undefined.\n Specify the path')
            return
        self.timeline_df = TimeLineProcessor(path_to_check=path_to_timeline).check_the_path()
        if self.timeline_df is None:
            self.slide_frame.time_label.configure(text='Aging time: failed to read.\n Specify the path')
        else:
            max_time = round(self.timeline_df.max().values[0])
            self.slide_frame.time_label.configure(text=f'Aging time: {max_time} h')

    def set_potentiostat(self, event):
        """
        Set potentiostat for filtering all unnecessary files
        :param event: Chose potentiostat through the ComboBox or choose All
        """
        self.potentiostat = event
        self.list_files()

    def list_files(self):
        """
        Update and fill the file table with filtered files
        """
        if self.file_directory == "":
            return
        # Check if there are any items in the treeview
        for i in self.table_frame.files_table.get_children():
            self.table_frame.files_table.delete(i)
        abspath = os.path.abspath(self.file_directory).replace('\\', '/')
        root_node = self.table_frame.files_table.insert('', 'end', text=os.path.basename(abspath), open=True)
        self.added_iv.clear()
        self.process_directory(root_node, abspath)

    def process_directory(self, parent, path, is_root_call=True):
        """
        Insert to a table and into the file_list filtered by extension type of files, including nested folders.
        Will show folders only if it contains required file.
        :param parent: Parent folder
        :param path: path to work with
        :param is_root_call: A boolean flag,
        that checks whether the current call to process_directory is the initial (root-level) call.
        :return: None
        """
        depth = 1 if self.aging_mode else 0
        potentiostat_checker = PotentiostatFileChecker(parent=self, potentiostat_choice=self.potentiostat)

        for file in os.listdir(path):
            abspath = os.path.join(path, file).replace('\\', '/')
            b = path.replace(self.file_directory, '').count('/')
            if os.path.isfile(abspath):
                checking = potentiostat_checker.check_file(abspath)
                if checking[0]:  # Insert a file only if it's potentiostats file
                    potentiostat = checking[2]
                    # data = [potentiostat, checking[1], abspath]
                    data = [potentiostat, checking[-1]['Unit'], abspath]
                    folder_name = os.path.basename(path)
                    if folder_name not in self.added_iv:
                        self.added_iv[folder_name] = {}
                    self.added_iv[folder_name][file] = {
                        "path": abspath,
                        'measurement device': potentiostat,
                        'encoding': checking[1],
                        'Sweeps': checking[3]["Counts"],
                        'data': checking[3]["Data"],
                        'unit': checking[3]['Unit'],
                        'Used files': file,
                        'Active area': None,
                        'Light Intensity': None,
                        'Distance to light source': None,
                    }
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
                    if b == depth:  # Nested folders with the deep of one only
                        # allowed for the Processed folders
                        return messagebox.showerror('Waring!', f"Too many sub folders in"
                                                               f" a folder {abspath}")
                    oid = self.table_frame.files_table.insert(parent, 'end', text=file, open=False, tags='folder',
                                                              values=['', '', abspath])
                    self.process_directory(oid, abspath, is_root_call=False)
        # Only run the following lines if it's the root call
        if is_root_call:
            self.table_frame.construct_active_areas_entries(data=self.added_iv, path=self.file_directory)

import json
import os
import re
import tkinter as tk
from datetime import date
from functools import partial
from tkinter import filedialog
from typing import Optional, Union, Dict, List

import customtkinter as ctk
import natsort
from CTkMenuBar import *
from CTkMessagebox import CTkMessagebox

from JV_plotter_GUI.instruments import get_newest_file_global


class PixelGroupingManager:
    def __init__(self, pixel_list: List[str]):
        self.pixel_list = natsort.natsorted(pixel_list)

    def group_pixels_by_substrate(self) -> dict:
        """
        Group pixels by determining their substrates

        :return: A dictionary with the pixels sorted by substrates.
        """
        grouped = {}
        for pixel in self.pixel_list:
            substrate = self.determine_substrate_name(pixel)
            if substrate not in grouped:
                grouped[substrate] = []
            grouped[substrate].append(pixel)
        return grouped

    def determine_substrate_name(self, pixel_name: str) -> str:
        """
        Process a list of pixel names to determine the substrate name and, if applicable, the contact number.
        The function checks if all pixel names in the list end with 'C' followed by digits.
        If so, it uses a regex to extract the base name and contact number.
        Otherwise, it uses a regex to extract just the substrate name.

        :param pixel_name: A string of the pixel name to find the potential substrate.
        :return:  A substrate name as a string if found ot pixel name as it is.
        """
        # Check if all pixel names in the list end with 'C' followed by digits
        all_end_with_c = all(re.search(r"C\d+$", name) for name in self.pixel_list)
        if all_end_with_c:
            # Use the regex pattern for contact number
            pattern = r"^(.+?)(C\d+)?$"
        else:
            pattern = r"^(.*?)(-\D*\d{1,2})?$"
        match = re.match(pattern, pixel_name)
        if match:
            if match.group(1).endswith('_'):
                return match.group(1)[:-1]
            return match.group(1)

        return pixel_name


class PixelSorterInterface(ctk.CTkToplevel):
    def __init__(self, parent, sorted_dict: dict, pixel_list: List[str], file_directory: str):
        super().__init__()
        self.error_metric_button = None
        self.parent = parent
        self.menu = None
        self.current_layout_state = None
        self.save_and_proceed_button = None
        self.file_directory = file_directory
        self.pixel_list = pixel_list
        self.sorted_dict = sorted_dict
        self.add_frame_button = None
        self.column_frames = []
        self.substrate_frames = {}  # To store frames for each substrate
        self.initialize_ui()
        self.protocol("WM_DELETE_WINDOW", self.exit_and_terminate)

    def initialize_ui(self) -> None:
        """
        Initialize the window layout, buttons for adding/removing frames, etc.
        :return: None
        """
        self.title("Pixel Sorter")
        self.geometry("800x600")

        # Add and configure menu
        self.menu = CTkMenuBar(master=self)
        if ctk.get_appearance_mode().lower() == "dark":
            self.menu.configure(bg_color='#2b2b2b')
        elif ctk.get_appearance_mode().lower() == "light":
            self.menu.configure(bg_color='#dbdbdb')
        menu_button = self.menu.add_cascade("Menu")
        edit_button = self.menu.add_cascade("Edit")
        view_button = self.menu.add_cascade("View")
        self.error_metric_button = self.menu.add_cascade("Error Metric")

        menu_dropdown = CustomDropdownMenu(widget=menu_button)
        menu_dropdown.add_option(option="Dump JSON", command=self.dump_json_pixels)
        menu_dropdown.add_separator()
        menu_dropdown.add_option("Fast Read JSON", command=self.populate_substrate_dict_from_file)
        menu_dropdown.add_separator()
        menu_dropdown.add_option("Read JSON", command=lambda: self.populate_substrate_dict_from_file(
            path_to_file=filedialog.askdirectory(mustexist=True)))
        menu_dropdown.add_separator()
        menu_dropdown.add_option("Exit and terminate instance", command=self.exit_and_terminate)

        edit_dropdown = CustomDropdownMenu(widget=edit_button, padx=-10)
        edit_dropdown.add_option(option='Rebuild sorting', command=self.initialize_pixels_placement)
        edit_dropdown.add_separator()
        edit_dropdown.add_option(option='Remove all', command=self.delete_all_frames)
        edit_dropdown.add_separator()

        view_dropdown = CustomDropdownMenu(widget=view_button, padx=-20)
        submenu = view_dropdown.add_submenu(submenu_name='Set columns')
        for i in range(1, 11):
            command = partial(self.initialize_pixels_placement, None, True, i)
            submenu.add_option(f'{i}', command=command)

        error_metric_dropdown = CustomDropdownMenu(widget=self.error_metric_button, padx=-30)
        error_metric_dropdown.add_option(option='Standard Deviation',
                                         command=lambda: self.parent.main_frame.activate_setting('std_dev'))
        error_metric_dropdown.add_separator()

        error_metric_dropdown.add_option(option='Mean Absolute Error',
                                         command=lambda: self.parent.main_frame.activate_setting('mae'))
        error_metric_dropdown.add_separator()

        error_metric_dropdown.add_option(option='Mean Squared Error',
                                         command=lambda: self.parent.main_frame.activate_setting('mse'))
        error_metric_dropdown.add_separator()

        error_metric_dropdown.add_option(option='Root Mean Squared Error',
                                         command=lambda: self.parent.main_frame.activate_setting('rmse'))
        error_metric_dropdown.add_separator()

        error_metric_dropdown.add_option(option='Mean Absolute Percentage Error',
                                         command=lambda: self.parent.main_frame.activate_setting('mape'))
        error_metric_dropdown.add_separator()

        error_metric_dropdown.add_option(option='Median Absolute Deviation',
                                         command=lambda: self.parent.main_frame.activate_setting('mad'))
        error_metric_dropdown.add_separator()

        self.save_and_proceed_button = ctk.CTkButton(self, text="Save and Proceed", command=self.withdraw_and_proceed)
        self.save_and_proceed_button.pack(side=tk.BOTTOM, pady=10)
        self.initialize_pixels_placement(rebuild_column_frames=True)

    def initialize_pixels_placement(self, data_dict: Optional[Dict] = None,
                                    rebuild_column_frames: Optional[bool] = False,
                                    number_of_columns: Optional[int] = 3):
        """
    Initializes or rebuilds the pixel placement in the GUI. This can involve setting up new columns
    for frames, adding substrate frames based on provided data, and configuring the layout.

    :param data_dict: Optional dictionary containing substrate names and their corresponding pixels.
    :param rebuild_column_frames: A boolean to determine if the column frames should be (re)built.
    :param number_of_columns: The number of columns to display the substrate frames in.
        """
        if rebuild_column_frames and number_of_columns:
            if data_dict is None and len(self.substrate_frames) > 0:
                data_dict = self.extract_data_to_dict()
            self.delete_all_frames()
            for frame in self.column_frames:
                for child in frame.winfo_children():
                    child.destroy()
                frame.pack_forget()
                frame.destroy()
            self.column_frames = []
            for _ in range(number_of_columns):
                column = ctk.CTkScrollableFrame(self)
                self.column_frames.append(column)
                column.pack(side=tk.LEFT, fill='both', expand=True)

            # Define the add_frame_button before calling update_add_frame_button_visibility or add_frame
            self.add_frame_button = ctk.CTkButton(self, text="Add Substrate", command=self.on_add_frame,
                                                  font=('Open Sans', 15))
        self.delete_all_frames()
        data = self.sorted_dict if data_dict is None else data_dict
        for substrate, pixels in data.items():
            self.add_substrate_frame(substrate, pixels, update_comboboxes=False)
        # After all frames have been added, now pack the add_frame_button and update its visibility
        self.update_add_frame_button_visibility()

    def on_add_frame(self):
        """
        Handles the event when the 'Add Frame' button is clicked. It generates a new substrate frame
        with a default name and adds it to the interface.
        """
        new_substrate_name = "NewSubstrate_{}".format(len(self.substrate_frames) + 1)
        self.add_substrate_frame(new_substrate_name, [])
        # Since we're adding a new frame, we need to check if we've reached the max frames
        self.update_add_frame_button_visibility()

    def add_substrate_frame(self, substrate_name: str, pixels: List[str], update_comboboxes: Optional[bool] = True) \
            -> None:
        """
        Adds a new frame with comboboxes for the given substrate name.

        :param substrate_name: The name of the substrate.
        :param pixels: List of pixel names for this substrate.
        :param update_comboboxes: Update comboboxes lists while adding them
        :return: None
        """

        # Decide which column to put the frame in based on the number of existing frames
        column = self.find_appropriate_column()

        # Add a frame to have a nice border, since ctk Scrollable Frame cannot make border properly
        wrap_up_frame = ctk.CTkFrame(column, border_color="#d0d0d0", border_width=2)
        wrap_up_frame.pack(pady=10, padx=15, fill='x')

        # Add an entry for the substrate name
        substrate_entry = ctk.CTkEntry(wrap_up_frame, font=("Open Sans", 15), justify='center')
        substrate_entry.insert(0, substrate_name)
        substrate_entry.pack(fill='x', pady=(10, 0), padx=5)

        frame = ctk.CTkScrollableFrame(wrap_up_frame)
        frame.pack(pady=10, padx=15, fill='x')

        # Initialize an empty list for comboboxes in frame_info
        self.substrate_frames[substrate_name] = {'wrap_up_frame': wrap_up_frame, 'frame': frame, 'comboboxes': [],
                                                 'add_button': None, 'combobox_vars': [], 'combobox_delete': [],
                                                 'substrate_entry': substrate_entry}
        # Update button visibility after adding a frame
        self.update_add_frame_button_visibility()
        for pixel in pixels:
            self.add_combobox_to_frame(substrate_name=substrate_name, initial_pixel=pixel,
                                       update_comboboxes=update_comboboxes)
        self.update_comboboxes()
        # Add "+" button to add a new combobox to the frame
        add_combobox_button = ctk.CTkButton(
            frame,
            text="+",
            width=10,  # Make the button smaller than the "Add Frame" button
            command=lambda: self.add_combobox_to_frame(substrate_name)
        )
        add_combobox_button.pack(side=tk.TOP, pady=(5, 10))
        self.substrate_frames[substrate_name]['add_button'] = add_combobox_button
        self.repack_add_button(substrate_name)

        # Instead of lambda, use a partial function to bind the command with the correct substrate name
        delete_command = partial(self.remove_frame, substrate_name)
        delete_button = ctk.CTkButton(frame, text="Delete Substrate", command=delete_command)
        delete_button.pack(side=tk.BOTTOM, pady=5)

    def remove_frame(self, substrate_name: str) -> None:
        """
        Removes the frame associated with the given substrate name.

        :param substrate_name: The name of the substrate.
        """
        # Retrieve the frame information from the dictionary
        frame_info = self.substrate_frames.get(substrate_name)
        if frame_info:
            # Destroy all child widgets inside the scrollable frame
            for child in frame_info['wrap_up_frame'].winfo_children():
                child.destroy()

            # Destroy the comboboxes and their delete buttons
            for combobox, delete_button in zip(frame_info['comboboxes'], frame_info['combobox_delete']):
                delete_button.destroy()
            # Forget packing and destroy the scrollable frame itself
            frame_info['wrap_up_frame'].pack_forget()
            frame_info['wrap_up_frame'].destroy()

            # Force the parent widget to update
            self.update()

            # Finally, remove the entry from the dictionary
            del self.substrate_frames[substrate_name]

            # Update button visibility after removing a frame
            self.repack_add_button(substrate_name)
            self.update_add_frame_button_visibility()

    def update_add_frame_button_visibility(self):
        """
        Update the visibility of the add frame button based on the number of current frames
        and the length of the input list. Place the button in the column with the least
        number of substrate frames. If multiple columns have the same number, place it in
        the rightmost column.
        """
        # Use the new method to find the appropriate column
        if len(self.substrate_frames) < len(self.pixel_list):
            column = self.find_appropriate_column(prefer='rightmost')
            self.add_frame_button.pack_forget()
            self.add_frame_button.pack(in_=column, side=tk.TOP, pady=(20, 10))
        else:
            self.add_frame_button.pack_forget()

    def find_appropriate_column(self, prefer: Optional[str] = 'leftmost'):
        """
        Find the column with the fewest frames. If there's a tie, choose based on preference.

        :param prefer: Use 'leftmost' to return the leftmost column in case of a tie, or 'rightmost' for the rightmost.
        :return: The appropriate column to add a new frame.
        """
        # Count the frames in each column
        frame_counts = [self.count_frames_in_column(column) for column in self.column_frames]

        # Determine the index of the appropriate column based on preference
        if prefer == 'leftmost':
            # Find the leftmost column with the minimum number of frames
            appropriate_column_index = frame_counts.index(min(frame_counts))
        elif prefer == 'rightmost':
            # Find the rightmost column with the minimum number of frames
            appropriate_column_index = len(frame_counts) - 1 - frame_counts[::-1].index(min(frame_counts))
        else:
            raise ValueError("Invalid preference. Choose 'leftmost' or 'rightmost'.")

        # Return the appropriate column
        return self.column_frames[appropriate_column_index]

    @staticmethod
    def count_frames_in_column(column: ctk.CTkScrollableFrame) -> int:
        """
        Count the number of substrate frames in a given column.

        :param column: The column widget to count frames in.
        :return: The number of substrate frames in the column.
        """
        # Count only the wrap_up_frames as they are direct children of columns
        return len([child for child in column.winfo_children() if isinstance(child, ctk.CTkFrame)])

    def add_combobox_to_frame(self, substrate_name: str, initial_pixel=None, update_comboboxes: Optional[bool] = True):
        """
        Adds a new CTkComboBox to the frame associated with the given substrate name.
        Optionally sets an initial pixel value.
        """
        frame_info = self.substrate_frames.get(substrate_name)
        combobox_frame = ctk.CTkFrame(frame_info['frame'])
        combobox_frame.pack(fill='x', padx=10, pady=1)
        # Define a StringVar for this combobox
        combobox_var = ctk.StringVar()
        # Create the "delete" button
        delete_combobox_button = ctk.CTkButton(
            combobox_frame,
            text="-",
            width=5,
            command=lambda cb_frame=combobox_frame: self.delete_combobox_from_frame(substrate_name, cb_frame)
        )
        delete_combobox_button.pack(side=tk.LEFT, fill='y', padx=(0, 5))

        # Initialize combobox values
        current_values = set(var.get() for var in self.get_all_combobox_vars())
        available_options = [pixel for pixel in self.pixel_list if pixel not in current_values]
        # Create the combobox
        combobox = ctk.CTkOptionMenu(combobox_frame, variable=combobox_var, values=available_options)
        combobox.pack(side=tk.RIGHT, expand=True, fill='x')

        # Set an initial value if given, otherwise set the first available option
        if not initial_pixel or initial_pixel in current_values:
            for option in available_options:
                if option not in current_values:
                    initial_pixel = option
                    break

        combobox_var.set(initial_pixel)

        # Trace changes in the StringVar
        combobox_var.trace_add("write", self.update_comboboxes)
        # Store the combobox and delete button as a tuple
        frame_info['comboboxes'].append(combobox)
        frame_info['combobox_delete'].append(delete_combobox_button)
        frame_info['combobox_vars'].append(combobox_var)
        # Update the "+" button position if any exist in the given substrate-frame
        if frame_info['add_button'] is not None and update_comboboxes:
            self.repack_add_button(substrate_name)

        if update_comboboxes:
            self.update_comboboxes()
        self.update()

    def delete_combobox_from_frame(self, substrate_name: str, combobox_frame):
        """
        Deletes the given CTkComboBox from the frame associated with the given substrate name.
        """
        frame_info = self.substrate_frames.get(substrate_name)
        # Find the index of the combobox to be deleted based on its frame
        for i, (combobox, delete_button) in enumerate(zip(frame_info['comboboxes'], frame_info['combobox_delete'])):
            if combobox.master == combobox_frame:
                # Remove the combobox and its delete button from the lists
                frame_info['comboboxes'].pop(i)
                frame_info['combobox_delete'].pop(i)
                frame_info['combobox_vars'].pop(i)

                # Destroy the combobox, delete button, and its frame
                combobox.destroy()
                delete_button.destroy()
                combobox_frame.destroy()

                # Break after the combobox is found and removed
                break
        self.repack_add_button(substrate_name)  # Repack the "+" button after deletion
        self.update_comboboxes()
        frame_info['frame'].update_idletasks()  # Update the UI to close gaps if necessary

    def update_comboboxes(self, *args):
        """
        Callback function to handle selection changes in any combobox.

        """
        # Gather all the currently selected values
        selected_values = set(var.get() for var in self.get_all_combobox_vars() if var.get())

        # Iterate over all comboboxes to update their values
        for var in self.get_all_combobox_vars():
            combobox = self.get_combobox_from_var(var)
            if combobox:
                # Calculate the unused options without the current value of this combobox
                unused_values = [value for value in self.pixel_list if
                                 value not in selected_values or value == var.get()]

                # Ensure the current value is not in the options
                if var.get() in unused_values and selected_values != var.get():
                    unused_values.remove(var.get())

                # Update the combobox values while maintaining the current selection
                combobox.configure(values=unused_values)

    def get_all_combobox_vars(self):
        """
        Retrieve all StringVar objects from the comboboxes in all frames.

        :return: A list of StringVar instances.
        """
        all_vars = []
        for frame_info in self.substrate_frames.values():
            all_vars.extend(frame_info['combobox_vars'])
        return all_vars

    def get_combobox_from_var(self, var):
        """
        Retrieve the combobox widget that is associated with the given StringVar.

        :param var: StringVar associated with a combobox.
        :return: The CTkComboBox widget associated with the given StringVar.
        """
        for frame_info in self.substrate_frames.values():
            if var in frame_info['combobox_vars']:
                index = frame_info['combobox_vars'].index(var)
                combobox = frame_info['comboboxes'][index]
                return combobox
        return None

    def repack_add_button(self, substrate_name: str):
        """
        Repacks the "+" button, so it always appears at the bottom of the frame after comboboxes are added or removed.
        """
        frame_info = self.substrate_frames.get(substrate_name)
        if frame_info:
            add_button = frame_info['add_button']
            add_button.pack_forget()  # Remove the button from its current location
            add_button.pack(side=tk.TOP, pady=(5, 10))  # Repack it at the bottom

        total_comboboxes = sum(len(frame_info['comboboxes']) for frame_info in self.substrate_frames.values())
        if total_comboboxes >= len(self.pixel_list):
            for frame_info in self.substrate_frames.values():
                frame_info['add_button'].configure(state='disabled')
        else:
            for frame_info in self.substrate_frames.values():
                frame_info['add_button'].configure(state='normal')

    def extract_data_to_dict(self) -> Union[Dict, None]:
        """
        Extracts the current data from the GUI and forms a dictionary where each key is a substrate
        name from the entry widgets, and each value is a list of pixel names extracted from the
        corresponding comboboxes.

        :return: A dictionary representing the updated substrate to pixels mapping.
        """
        data_dict = {}
        seen = set()
        for frame_info in self.substrate_frames.values():
            # Retrieve the substrate name from the entry widget
            substrate_name = frame_info['substrate_entry'].get()
            if substrate_name in seen:
                CTkMessagebox(title="Error",
                              message=f"Duplicate substrate name found:\n{substrate_name}"
                                      f"\nDelete the duplicate to proceed.",
                              icon="cancel")
                return
            seen.add(substrate_name)
            # Retrieve the pixels from comboboxes
            pixels = [combobox_var.get() for combobox_var in frame_info['combobox_vars']]

            # Assign to the dictionary
            data_dict[substrate_name] = pixels
        return data_dict

    def dump_json_pixels(self) -> None:
        """
        Dumps the current GUI data into a JSON file within the specified directory. The JSON file is
        named with the current date and a base directory name, appended with 'pixels sorted.json'.
        """
        base_dir = os.path.basename(self.file_directory)
        current_date = date.today()
        json_name = os.path.join(self.file_directory,
                                 f"{current_date} {base_dir} pixels sorted.json")
        data_dict = self.extract_data_to_dict()
        if data_dict:
            with open(json_name, 'w') as f:
                json.dump(data_dict, f, indent=4)
            CTkMessagebox(title='Success', message=f'JSON\n{json_name}\nwas successfully dumped',
                          icon="check", option_1="Thanks")

    def populate_substrate_dict_from_file(self, path_to_file: Optional[str] = None) -> None:
        """
        Populates the substrate dictionary from a JSON file. If a path to the file is provided, it uses
        that file; otherwise, it searches for the newest 'pixels sorted' JSON file in the file directory.

        :param path_to_file: Optional; the path to the JSON file to load.
        :return: None.
        """
        final_path = self.file_directory if path_to_file is None else get_newest_file_global(path_to_file,
                                                                                             'pixels sorted')
        if final_path is None:
            CTkMessagebox(title="File not found error", message="No suitable json was found", icon="cancel")
            return
        final_path = path_to_file if path_to_file else get_newest_file_global(self.file_directory, 'pixels sorted')
        with open(final_path, 'r') as f:
            substrates_data = json.load(f)
        for substrate, pixels in substrates_data.items():
            if not all(pixel in self.pixel_list for pixel in pixels):
                CTkMessagebox(title="Error",
                              message=f"Invalid pixels found in substrate:\n'{substrate}'\n",
                              icon="cancel")
                return
        self.initialize_pixels_placement(substrates_data)
        return

    def delete_all_frames(self):
        """
         Deletes all existing substrate frames from the interface. This is used for clearing the interface
         or preparing it for a new layout or data loading.
        """
        if list(self.substrate_frames.keys()):
            for substrate_name in list(self.substrate_frames.keys()):
                self.remove_frame(substrate_name)

    def withdraw_and_proceed(self):
        read_data = self.extract_data_to_dict()
        if read_data:
            # Capture the current layout state
            self.current_layout_state = read_data

            # Flatten the list of current unique devices
            updated_devices = self.pixel_list.copy()

            for substrate, pixels in read_data.items():
                # Check if each pixel is in the current unique devices list
                for pixel in pixels:
                    if pixel in self.pixel_list:
                        # Remove the pixel and add the substrate instead
                        updated_devices.remove(pixel)
                # Add the substrate name if not already in the list
                if substrate not in updated_devices:
                    updated_devices.append(substrate)

            # Update the all_unique_devices list
            self.parent.main_frame.all_unique_devices = updated_devices

            # Minimize or hide the window, keeping it in memory
            self.withdraw()
            if self.parent.state().lower() != 'normal':
                self.parent.state('normal')

    def return_sorted_dict(self):
        return self.current_layout_state

    def exit_and_terminate(self):
        self.withdraw()
        if self.parent.state().lower() != 'normal':
            self.parent.state('normal')
        self.parent.main_frame.pixel_sorter_instance = None
        self.parent.main_frame.additional_settings.filter1_checkbox.configure(state='disabled')

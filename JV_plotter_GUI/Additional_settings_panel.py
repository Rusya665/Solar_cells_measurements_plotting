from idlelib.tooltip import Hovertip
from tkinter import END

import customtkinter as ctk

from JV_plotter_GUI.settings import settings


class AdditionalSettings(ctk.CTkFrame):
    def __init__(self, parent, start_pos, end_pos):
        super().__init__(master=parent)
        self.parent = parent
        # general attributes
        self.start_pos = start_pos - 0.03
        self.end_pos = end_pos + 0.04
        self.width = abs(start_pos - end_pos)

        # animation logic
        self.pos = self.start_pos
        self.in_start_pos = True
        self.rely = 0.05
        self.relative_height = 0.85
        # layout
        self.additional_settings_label = ctk.CTkLabel(self, text="Additional Settings")
        self.additional_settings_label.cget("font").configure(size=20)

        self.light_intensity_label = ctk.CTkLabel(self, text="Light intensity, W/m²")
        self.light_intensity_entry = ctk.CTkEntry(self)
        self.light_intensity_entry.insert(END, settings['Light intensity (W/cm²)'])

        self.distance_to_light_label = ctk.CTkLabel(self, text="Distance to light source, mm")
        self.distance_to_light_entry = ctk.CTkEntry(self)
        self.distance_to_light_entry.insert(END, settings['Distance to light source (mm)'])

        self.excel_label = ctk.CTkLabel(self, text='Excel settings')
        self.excel_label.cget("font").configure(size=18)
        self.open_wb_checkbox = ctk.CTkCheckBox(self, text='Open WB',
                                                command=lambda: self.parent.activate_setting('open_wb'))
        self.open_wb_checkbox.select()
        self.color_wb_checkbox = ctk.CTkCheckBox(self, text='Colorful tabs',
                                                 command=lambda: self.parent.activate_setting('color_wb'))
        self.color_wb_checkbox.select()
        # self.dump_json_label = ctk.CTkLabel(self, text='Dump json')
        self.dump_json_checkbox = ctk.CTkCheckBox(self, text='Dump JSON',
                                                  command=lambda: self.parent.activate_setting('dump_json'))

        self.additional_settings_label.pack(pady=10)

        self.filtering_label = ctk.CTkLabel(self, text="Data filters")
        self.filtering_label.cget("font").configure(size=18)
        self.filter1_checkbox = ctk.CTkCheckBox(self, text='Filter 1',
                                                command=lambda: self.parent.activate_setting('filter1'))
        self.filter2_checkbox = ctk.CTkCheckBox(self, text='Filter 2',
                                                command=lambda: self.parent.activate_setting('filter2'))
        widgets = [
            self.light_intensity_label,
            self.light_intensity_entry,
            self.distance_to_light_label,
            self.distance_to_light_entry,
            self.excel_label,
            self.open_wb_checkbox,
            self.color_wb_checkbox,
            self.dump_json_checkbox,
            self.filtering_label,
            self.filter1_checkbox,
            self.filter2_checkbox
        ]
        for widget in widgets:
            widget.pack(pady=8)
        self.hovers()

    def hovers(self):
        hover_delay = 400

        hover_additional_settings = "Additional Settings 🛠️\nConfigure extra parameters here."
        hover_light_intensity = ("  How Bright? 🌞  \n"
                                 "  Set the light intensity in W/m²  \n"
                                 "  to simulate real-world conditions! 📊  ")
        hover_distance_to_light = ("  How Close? 📏  \n"
                                   "  Specify the distance to the light source in mm.  \n"
                                   "  Distance matters! 🌈  ")
        hover_excel_settings = "Excel Settings 📝\nConfigure the Excel export settings here."
        hover_text_open_wb = "  Workbook reveal!  \n  Open when done! 🎉  "
        hover_color_wb = "Color Tabs 🌈\nChoose to color your workbook tabs. Note: may affect speed."
        hover_dump_json = "Dump JSON 💾\nChoose to dump data as a JSON file."
        hover_filtering_label = ("Data Filters: Use at Your Own Risk ⚠️\n"
                                 "These filters manipulate the dataset based on specific criteria.\n"
                                 "Be cautious: changes can significantly impact data analysis results.\n"
                                 "Ensure you understand each filter's function before applying.")
        hover_filter1 = ("Filter 1: Pixel Efficiency Analysis 🔄\n"
                         "This filter evaluates each pixel's efficiency within substrates.\n"
                         "Pixels with an average efficiency below 0.01 are considered 'dead'.\n"
                         "If all pixels in a substrate are 'dead', none are deleted to maintain substrate representation.\n"
                         "This ensures comprehensive data analysis, keeping at least one 'dead' pixel when necessary.")
        hover_filter2 = ("Filter 2: Measurement Point Accuracy 🔍\n"
                         "This filter scrutinizes each device's measurement points.\n"
                         "It specifically identifies and removes points where efficiency anomalously\n"
                         "drops below 0.01 and then inexplicably recovers.\n"
                         "By filtering out these erratic efficiency fluctuations, Filter 2 ensures\n"
                         "the reliability and consistency of the overall dataset.")
        Hovertip(self.light_intensity_label, hover_light_intensity, hover_delay=hover_delay)
        Hovertip(self.light_intensity_entry, hover_light_intensity, hover_delay=hover_delay)
        Hovertip(self.distance_to_light_label, hover_distance_to_light, hover_delay=hover_delay)
        Hovertip(self.distance_to_light_entry, hover_distance_to_light, hover_delay=hover_delay)
        Hovertip(self.light_intensity_label, "\nGo back to work you lazy\n", hover_delay=hover_delay * 16)
        Hovertip(self.light_intensity_label, "\n                    I said\n"
                                             "GO BACK TO YOUR WORK!\n", hover_delay=hover_delay * 32)
        Hovertip(self.excel_label, hover_excel_settings, hover_delay=hover_delay)
        Hovertip(self.open_wb_checkbox, hover_text_open_wb, hover_delay=hover_delay)
        Hovertip(self.color_wb_checkbox, hover_color_wb, hover_delay=hover_delay)

        Hovertip(self.additional_settings_label, hover_additional_settings, hover_delay=hover_delay)
        Hovertip(self.dump_json_checkbox, hover_dump_json, hover_delay=hover_delay)
        Hovertip(self.filtering_label, hover_filtering_label, hover_delay=hover_delay)
        Hovertip(self.filter1_checkbox, hover_filter1, hover_delay=hover_delay)
        Hovertip(self.filter2_checkbox, hover_filter2, hover_delay=hover_delay)

    def animate_additional_settings(self, step=0.03):
        if self.in_start_pos:  # If the frame is about to be shown
            self.parent.bind("<Button-1>", self.hide_if_clicked_outside)  # Bind the event
            self.parent.table_frame.files_table.bind("<Button-1>", self.hide_if_clicked_outside)
            self.parent.table_frame.active_areas_scrollable_frame.bind("<Button-1>", self.hide_if_clicked_outside)
        target_pos = self.end_pos if self.in_start_pos else self.start_pos
        step = step if self.in_start_pos else -1 * step
        self.animate_to_target(target_pos, step)
        self.in_start_pos = not self.in_start_pos

    def animate_to_target(self, target_pos, step):
        if (step > 0 and self.pos < target_pos) or (step < 0 and self.pos > target_pos):
            self.pos += step
            self.place(relx=self.pos, rely=self.rely, relwidth=self.width, relheight=self.relative_height)
            self.lift()  # Bring the frame to the top
            self.after(10, lambda: self.animate_to_target(target_pos, step))
        else:
            if self.in_start_pos:  # If the frame is fully hidden
                self.parent.unbind("<Button-1>")  # Unbind the event
                self.parent.table_frame.files_table.unbind("<Button-1>")  # Unbind the event
                self.parent.table_frame.active_areas_scrollable_frame.unbind("<Button-1>")  # Unbind the event

    def hide_if_clicked_outside(self, event):
        x, y, _, _ = self.bbox("insert")
        if event.x < x or event.x > x + self.winfo_width() or event.y < y or event.y > y + self.winfo_height():
            self.animate_additional_settings()  # Assuming you have a method to hide the slide frame

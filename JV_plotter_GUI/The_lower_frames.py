import customtkinter as ctk


class ProceedFrame(ctk.CTkFrame):
    def __init__(self, parent, width=200, height=200, *args, **kwargs):
        super().__init__(master=parent, width=width, height=height, *args, **kwargs)
        self.parent = parent
        self.label_in_frame = ctk.CTkLabel(master=self, text='Proceed with selected or all the files:')
        self.button_selected = ctk.CTkButton(self, text='Selected', width=50,
                                             command=lambda: self.parent.final_output("Selected"))
        self.button_all = ctk.CTkButton(self, text='All', width=50, command=lambda: self.parent.final_output("All"))
        self.label_in_frame.pack(fill='x', padx=5)
        self.button_selected.pack(side='left', padx=15)
        self.button_all.pack(side='right', padx=15)


class LowestFrame(ctk.CTkFrame):
    def __init__(self, parent, fg_color='transparent', *args, **kwargs):
        super().__init__(master=parent, fg_color=fg_color, *args, **kwargs)
        self.parent = parent
        self.lowest_frame_left = ctk.CTkFrame(self, fg_color='transparent')
        self.lowest_frame_right = ctk.CTkFrame(self, fg_color='transparent')
        self.lowest_frame_left.pack(side='left', padx=15)
        self.lowest_frame_right.pack(side='right', padx=15)
        self.appearance_mode_label = ctk.CTkLabel(self.lowest_frame_left, text='Appearance mode')
        self.appearance_mode_label.pack()
        self.appearance_mode = ctk.CTkOptionMenu(self.lowest_frame_left, values=["System", "Dark", "Light"], width=100,
                                                 command=self.parent.change_appearance_mode_event)
        self.appearance_mode.pack()
        self.exit_button = ctk.CTkButton(self.lowest_frame_right, text='Exit', width=70,
                                         command=lambda: self.parent.exit())
        self.exit_button.pack(side='bottom')

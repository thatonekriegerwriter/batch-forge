# /Users/Trevor/Documents/Scripts/batch-forge python

from glob import glob
from math import floor, ceil
from tkinter import *
from tkinter import ttk

import get_pdf_data as get_pdf
from batch_forge_config import BATCHING_VARS as BV
from batch_forge_config import BATCHING_VARS_HIDDEN as BVH
from batch_forge_config import GENERAL_VARS as GV
from batch_forge_config import GENERAL_VARS_HIDDEN as GVH
from batch_logic import build_a_batch
from batch_sorting import *

# Necessary Caldera Directories
SORTING_DIR = GVH["Caldera Dirs"]["Sorting"]
HEIGHT_LIST = BV["Height List"]
BATCH_CONTENTS = BVH["Batch Content Options"]
PAPER_TYPES = GV["Paper Types"]


def batch_orders_window(root) -> None:
    """
    Accepts root window. Opens the window for batching orders.
    """

    # Initialize Batch Window
    batch_window = Toplevel(root)
    batch_window.title("Build-A-Batch")
    # batch_window.geometry("728x591")
    # batch_window.minsize(728, 591)
    # batch_window.maxsize(728, 591)

    # Set the rows and columns to adjust as the window resizes
    batch_window.columnconfigure(0, weight=1)
    batch_window.columnconfigure(1, weight=1)
    batch_window.rowconfigure(0, weight=1)
    batch_window.rowconfigure(1, weight=1)

    # Initialize frame that contains counts of different PDF heights
    panel_count_label = Frame(batch_window, padx=10, pady=10, relief=SUNKEN, bd=8)
    panel_count_label.grid(column=0, row=0, rowspan=4, sticky="nsew")

    row_count = 1
    for height in HEIGHT_LIST:
        if height == 9:
            height = "Samples"
        elif height == 146.25:
            height = "12\nFeet"
        else:
            height = str(int((height - 4.25) / 12)) + "\nFeet"
        height_label = Label(panel_count_label, text=(str(height)))
        height_label.grid(row=row_count, column=0, padx=1, pady=1)
        row_count += 1

    column_count = 1
    for paper in PAPER_TYPES:
        column_count = display_pdf_counts(panel_count_label, paper, column_count)

    """
    Initialize Options Frame and Widgets
    """

    # Options Frame Row Count
    options_frame_row_count = 0
    # Options Frame
    options_frame = Frame(batch_window, padx=10, pady=10, bd=8, relief=SUNKEN)
    options_frame.grid(column=1, row=options_frame_row_count, sticky="nsew")

    # Material Selection
    material_label = Label(
        options_frame, text="Please select a material:", justify=LEFT
    )
    material_label.grid(row=0, column=0)

    global batch_material_var
    batch_material_var = StringVar()

    for material in PAPER_TYPES:
        material_btn = Radiobutton(
            options_frame,
            variable=batch_material_var,
            value=material,
            text=material,
            command=lambda: update_batch_specs(),
        )
        material_btn.grid(row=options_frame_row_count, column=1, sticky=W)
        options_frame_row_count += 1

    batch_material_var.set(PAPER_TYPES["Smooth"]["Name"])

    # Include Samples Label and Checkbutton
    batch_contents_label = Label(options_frame, text="Batch Contents:", justify=LEFT)
    batch_contents_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global batch_contents_var
    batch_contents_var = IntVar()

    for option in BATCH_CONTENTS:
        content_checkbutton = Radiobutton(
            options_frame,
            variable=batch_contents_var,
            value=option,
            text=BATCH_CONTENTS[option],
            justify=LEFT,
            command=lambda: update_batch_specs(),
        )
        content_checkbutton.grid(row=options_frame_row_count, column=1, sticky=W)
        options_frame_row_count += 1
        if option == 0:
            batch_contents_var.set(option)

    # Order Trouble Label and Checkbutton
    order_trouble_label = Label(
        options_frame, text="Include Order Troubles?", justify=LEFT
    )
    order_trouble_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global batch_ot_var
    batch_ot_var = BooleanVar()
    batch_ot_var.set(True)
    batch_ot_checkbutton = Checkbutton(
        options_frame,
        variable=batch_ot_var,
        onvalue=True,
        offvalue=False,
        justify=LEFT,
        command=lambda: update_batch_specs(),
    )
    batch_ot_checkbutton.select()
    batch_ot_checkbutton.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Head Waste and Checkbutton
    head_waste_label = Label(
        options_frame, text="Include Head Waste?", justify=LEFT
    )
    head_waste_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global head_waste_var
    head_waste_var = BooleanVar()
    head_waste_var.set(True)
    head_waste_checkbutton = Checkbutton(
        options_frame,
        variable=head_waste_var,
        onvalue=True,
        offvalue=False,
        justify=LEFT,
        command=lambda: update_batch_specs(),
    )
    head_waste_checkbutton.select()
    head_waste_checkbutton.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Tail Waste and Checkbutton
    tail_waste_label = Label(
        options_frame, text="Include Tail Waste?", justify=LEFT
    )
    tail_waste_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global tail_waste_var
    tail_waste_var = BooleanVar()
    tail_waste_var.set(True)
    tail_waste_checkbutton = Checkbutton(
        options_frame,
        variable=tail_waste_var,
        onvalue=True,
        offvalue=False,
        justify=LEFT,
        command=lambda: update_batch_specs(),
    )
    tail_waste_checkbutton.select()
    tail_waste_checkbutton.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Minimum Length Enforcement Label and Checkbutton
    """Currently Disabled"""
    batch_minimum_label = Label(
        options_frame, text="Enforce minimum length?", justify=LEFT
    )
    batch_minimum_label.grid(row=options_frame_row_count, column=0, sticky=W)

    batch_minimum_var = BooleanVar()
    batch_minimum_var.set(True)
    batch_minimum_checkbutton = Checkbutton(
        options_frame,
        variable=batch_minimum_var,
        onvalue=True,
        offvalue=False,
        justify=LEFT,
        state=DISABLED,
    )
    batch_minimum_checkbutton.select()
    batch_minimum_checkbutton.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Length Label, Spinbox, and Reset Button
    length_label = Label(options_frame, text="Batch Length:", justify=LEFT)
    length_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global batch_length_var
    batch_length_var = IntVar()
    batch_length_spinbox = Spinbox(
        options_frame,
        width=5,
        from_=10,
        to=150,
        increment=1,
        textvariable=batch_length_var,
        command=lambda: update_batch_specs(),
    )
    batch_length_var.set(150)
    batch_length_spinbox.grid(row=options_frame_row_count, column=1, sticky=W)

    length_reset_btn = Button(
        options_frame,
        text="Reset",
        command=lambda: update_batch_specs(reset_length=True),
    )
    length_reset_btn.grid(row=options_frame_row_count, column=2)
    options_frame_row_count += 1

    # Number of batches with these specifications
    available_batch_label = Label(
        options_frame, text="Available batches:", justify=LEFT
    )
    available_batch_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global batch_qty_label
    batch_qty_label = Label(
        options_frame,
        justify=LEFT,
        text=str(
            get_available_batches(
                batch_material_var.get(),
                batch_length_var.get(),
                batch_ot_var.get(),
                batch_contents_var.get(),
            )
        ),
    )
    batch_qty_label.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Number of batches to make with current specifications
    batch_quantity_label = Label(options_frame, text="Batches to make:", justify=LEFT)

    batch_quantity_label.grid(row=options_frame_row_count, column=0, sticky=W)

    global batch_quantity_var
    global batch_quantity_spinbox
    batch_quantity_var = IntVar()
    batch_quantity_spinbox = Spinbox(
        options_frame,
        width=5,
        from_=0,
        textvariable=batch_quantity_var,
        increment=1,
        to=get_available_batches(
            batch_material_var.get(),
            batch_length_var.get(),
            batch_ot_var.get(),
            batch_contents_var.get(),
        ),
    )

    batch_quantity_var.set(
        default_batch_quantity(
            batch_material_var.get(),
            batch_length_var.get(),
            batch_ot_var.get(),
            batch_contents_var.get(),
        )
    )

    batch_quantity_spinbox.grid(row=options_frame_row_count, column=1, sticky=W)
    options_frame_row_count += 1

    # Initialize Batch Progress Bar
    batch_progress_frame = Frame(batch_window, padx=5, pady=9, bd=8, relief=SUNKEN)
    batch_progress_frame.grid(row=2, column=1, sticky="nsew")

    batch_progress_label = Label(batch_progress_frame, text="Idle.", padx=2)
    batch_progress_label.grid(columnspan=2)

    batch_progress_bar = ttk.Progressbar(
        batch_progress_frame, orient="horizontal", length=200, mode="determinate"
    )
    batch_progress_bar.grid(row=1, columnspan=2)

    global progress_done_btn
    progress_done_btn = Button(
        batch_progress_frame,
        text="Done!",
        width=15,
        command=lambda: update_batch_specs(reset_length=True, disable_done_button=True),
        state=DISABLED,
    )

    progress_done_btn.grid(row=0, column=2, rowspan=2, sticky=E)

    # Initialize Batch Button
    batch_btn_frame = Frame(batch_window, padx=5, pady=10, bd=8, relief=SUNKEN)
    batch_btn_frame.grid(row=1, column=1, sticky="nsew")

    global batch_btn
    batch_btn = Button(
        batch_btn_frame,
        text="Batch!",
        width=20,
        height=2,
        command=lambda: build_a_batch(
            batch_progress_frame,
            batch_progress_label,
            batch_progress_bar,
            progress_done_btn,
            batch_quantity_var.get(),
            batch_material_var.get(),
            batch_length_var.get(),
            batch_contents_var.get(),
            batch_ot_var.get(),
            head_waste_var.get(),
            tail_waste_var.get(),
            batch_minimum_var.get(),
        ),
    )
    batch_btn.pack()

    # Initialize Return Button
    close_btn_frame = Frame(batch_window, padx=5, pady=10, bd=8, relief=SUNKEN)
    close_btn_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")

    close_btn = Button(
        close_btn_frame,
        text="Return to Main Menu",
        width=20,
        height=2,
        command=batch_window.destroy,
    )
    close_btn.pack()

    # Show Directory Path
    directory_frame = Frame(batch_window, padx=2, pady=2, bd=1, relief=SUNKEN)
    directory_frame.grid(row=5, column=0, columnspan=2, sticky="nsew")

    directory_label = Label(directory_frame, text="Sorted Directory: " + SORTING_DIR)
    directory_label.pack()

    return


def button_state_check(value: bool):
    """
    Accepts a true/false and returns Normal/Disabled for button configurations.
    """
    if value is True:
        return NORMAL
    else:
        return DISABLED


def reopen_window(window) -> None:
    """
    Accepts a window name. Closes and reopens that window when called.
    """
    window.destroy()
    batch_orders_window()
    return


def default_batch_quantity(
    material: str, batch_length: int, include_OT: bool = True, batch_contents: int = 0
) -> int:
    """
    Accepts material as a string, batch_length as an int, and whether or not
    to include OTs as a bool.
    When the batch window is open, sets the default batch quantity to 3 if more
    than 3 batches are available, or to the number of batches available if
    less than 3 are available.
    """
    batch_count = get_available_batches(
        material, batch_length, include_OT, batch_contents
    )
    if batch_count >= 3:
        return 3
    else:
        return batch_count


def update_batch_specs(reset_length=False, disable_done_button=False) -> None:
    """
    Single function to call to update all other options based on related
    options changes. Optionally accepts a True/False value to reset the
    default batch length.
    """
    if reset_length is True:
        batch_length_var.set(150)

    if disable_done_button is True:
        progress_done_btn.config(state=DISABLED)

    material = batch_material_var.get()
    batch_length = batch_length_var.get()
    include_OT = batch_ot_var.get()
    batch_contents = batch_contents_var.get()

    available_batches = get_available_batches(
        material, batch_length, include_OT, batch_contents
    )

    if available_batches == 0:
        batch_btn.config(text="No available batches", state=DISABLED)
    else:
        batch_btn.config(text="Batch!", state=NORMAL)

    default_batches_to_make = default_batch_quantity(
        material, batch_length, include_OT, batch_contents
    )

    batch_qty_label.config(text=str(available_batches))
    batch_quantity_var.set(
        default_batch_quantity(material, batch_length, include_OT, batch_contents)
    )

    batch_quantity_spinbox.config(
        textvariable=default_batches_to_make, to=available_batches
    )

    return


def get_available_batches(
    material: str, batch_length: int, include_OT: bool = True, batch_contents: int = 0
) -> int:
    """
    Accepts a material type and batch_length, and optionally accepts include_OT
    as a boolean and batch_contents as an int. Calls get_length_of_pdfs to get
    a list of matching PDFs, then returns a count of available batches.
    """
    potential_length = 0
    for height in HEIGHT_LIST:
        if batch_contents == 1:
            if height == 9:
                pass
            else:
                potential_length += get_length_of_pdfs(
                    material, height, include_OT, batch_contents
                )
        elif batch_contents == 2:
            if height != 9:
                pass
            else:
                potential_length += get_length_of_pdfs(
                    material, height, include_OT, batch_contents
                )
        else:
            potential_length += get_length_of_pdfs(
                material, height, include_OT, batch_contents
            )

    # Get Printer Waste
    printer_waste = 0
    if head_waste_var:
        printer_waste += GV["Waste"]["Head"]
    if tail_waste_var:
        printer_waste += GV["Waste"]["Tail"]

    available_batches = ceil(potential_length / (((batch_length * 12)) - printer_waste))

    return available_batches


def get_length_of_pdfs(
    material: str, height: int, include_OT: bool = True, batch_contents: int = 0
) -> int:
    """
    Accepts a material type and panel height, and optionally accepts include_OT
    as a boolean. Calls get_list_of_pdfs to get a list of matching PDFs, then
    returns a length of matching PDFs.
    """

    full_list_to_measure = []
    sample_quantity = 0

    list_to_measure = get_list_of_pdfs(material, height, include_OT, batch_contents)
    for print_pdf in list_to_measure:
        if "-Full-" in print_pdf:
            full_list_to_measure.append(print_pdf)
        else:
            sample_quantity += get_pdf.quantity(print_pdf)

    full_length = calculate_full_length(sort_pdf_list(full_list_to_measure))

    sample_length = floor(((sample_quantity / 2) + sample_quantity % 2) * 9.5)

    potential_length: int = full_length + sample_length

    return potential_length


def display_pdf_counts(frame, material, column) -> int:
    """
    Accepts a frame name and material name. Displays counts of
    panels on screen, returns a row count for the succeeding rows.
    """

    row_count = 0
    if row_count == 0:
        material_label = Label(frame, text=material)
        material_label.grid(column=column, row=row_count, padx=1, pady=1)
        row_count += 1
    for height in HEIGHT_LIST:
        # height_count = Label(frame, text=(str(get_qty_of_pdfs(material, height))))
        height_count = Label(frame, text=(str(get_length_of_pdfs(material, height))))
        height_count.grid(column=column, row=row_count, padx=1, pady=1, sticky=EW)
        row_count += 1
    column += 1
    return column


def get_qty_of_pdfs(
    material: str, height: float, include_OT: bool = True, batch_contents: int = 0
) -> int:
    """
    Accepts a material type and panel height, and optionally accepts include_OT
    as a boolean. Calls get_list_of_pdfs to get a list of matching PDFs, then
    returns a count of how many panels match the list.
    """

    list_to_count = get_list_of_pdfs(material, height, include_OT, batch_contents)

    count = 0

    for print_pdf in list_to_count:
        count += get_pdf.quantity(print_pdf)

    return count
        

def get_list_of_pdfs(
    material: str, height: float, include_OT: bool = True, batch_contents: int = 0
) -> list:
    """
    Accepts a material type and panel height, and optionally accepts include_OT
    as a boolean. Then uses glob to find and return a list of matching PDFs.
    """

    list_to_return = []

    # Change height to ht for readability below
    ht = height

    # Specify first part of glob path
    if include_OT is True:
        mtrl_path = (SORTING_DIR + "*/" + material + "/",)
    else:
        mtrl_path = (
            SORTING_DIR + "2 - Late/" + material + "/",
            SORTING_DIR + "3 - Today/" + material + "/",
            SORTING_DIR + "4 - Tomorrow/" + material + "/",
            SORTING_DIR + "5 - Future/" + material + "/",
        )

    # If looking for a sample
    if batch_contents == 1:
        pass
    else:
        if height == 9:
            for due_date in mtrl_path:
                # This variable name doesn't mean anything. It's just to keep
                # the character count under 80 characters.
                short = due_date + "Sample/*.pdf"
                short = glob(short)
                list_to_return.extend(short)

    # If looking for a full order
    if batch_contents == 2:
        pass
    else:
        for due_date in mtrl_path:
            # This variable name doesn't mean anything. It's just to keep
            # the character count under 80 characters.
            short = due_date + "Full/*/*/*-Full-*H" + str(ht) + ".pdf"
            short = glob(due_date + "Full/*/*/*-Full-*H" + str(ht) + ".pdf")
            list_to_return.extend(short)

    return list_to_return

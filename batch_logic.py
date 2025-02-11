# /Users/Trevor/Documents/Scripts/batch-forge python

from glob import glob
from math import floor
from os import listdir, mkdir, rmdir, walk
from shutil import copy
from tkinter import *

import macos_tags
from PyPDF2 import errors

import batch_sorting as BS
import get_pdf_data as get_pdf
import pdf_splitter
from batch_forge_config import BATCHING_VARS as BV
from batch_forge_config import BATCHING_VARS_HIDDEN as BVH
from batch_forge_config import GENERAL_VARS as GV
from batch_forge_config import GENERAL_VARS_HIDDEN as GVH
from batch_forge_config import (
    reset_available_pdfs,
    reset_batch_dict,
    get_batch_id
    )
from datetime import date
from wallpaper_sorter_functions import try_to_move_pdf

TODAY = date.today()

BATCH_FOLDERS_DIR = GVH["Caldera Dirs"]["Batches"]
SORTING_DIR = GVH["Caldera Dirs"]["Sorting"]

def build_a_batch(
    batch_progress_frame,
    batch_progress_label,
    batch_progress_bar,
    progress_done_btn,
    batches_to_make: int,
    material: str,
    batch_length: int,
    contents: int = 0,
    include_OTs: bool = True,
    include_head_waste: bool = True,
    include_tail_waste: bool = True,
    care_min_length: bool = True,
) -> None:
    """
    Accepts seven variables: a tkinter window to open a new window from;
    batches_to_make as an int; material as a string;
    batch_length as an int; contents as an int (default 0);
    include_OTs as a bool (default True); min_length as a bool (default True).

    Creates batches based on the provided arguments that are ready to import
    into Caldera.

    Returns nothing.
    """

    progress_done_btn.config(state=DISABLED)
    batch_progress_label.config(text="Working...")

    # # Initialize window and progress bar
    # batch_progress = Toplevel(window)

    # Title check to see if it should say batch or batches
    # batch_plural = 'batches'
    # if batches_to_make == 1:
    #     batch_plural = 'batch'
    # batch_progress.title(f'Making {batches_to_make} {batch_plural}.')

    # # Initialize progress frame
    # batch_progress_frame = LabelFrame(batch_progress,
    #                                   text='Progress.',
    #                                   padx=10,
    #                                   pady=10,
    #                                   width=250)
    # batch_progress_frame.pack(padx=10, pady=10)

    # # Sets progress bar
    # batch_progress_label = Label(batch_progress_frame, text='Working')
    # batch_progress_label.pack()

    # Get Printer Waste
    printer_waste = 0
    if include_head_waste:
        printer_waste += GV["Waste"]["Head"]
    if include_tail_waste:
        printer_waste += GV["Waste"]["Tail"]

    # Changes batch_length to inches
    batch_length = (batch_length * 12) - printer_waste

    # Sets progress bar maximum
    batch_progress_bar["maximum"] = batches_to_make

    # Starts for loop to make the specified number of batches
    for batch_num in range(batches_to_make):
        batch_num_label = batch_num + 1
        # Resets the batch dict and available PDFs dict
        global batch_dict
        batch_dict = reset_batch_dict()
        global available_pdfs
        available_pdfs = reset_available_pdfs()

        # Sets details about the batch
        batch_details = batch_dict["batch_details"]
        batch_details["care_about_minimum_length"] = care_min_length
        batch_details["material_length"] = batch_length
        batch_details["include_OTs"] = include_OTs
        batch_details["material"] = material
        batch_details["contents"] = contents
        batch_details["ID"] = get_batch_id()

        # Variables of batch_dict for easy reference
        material = batch_details["material"]
        min_batch_length = batch_details["material_length"] * BV["Minimum Length"]

        # Updates status label fo finding PDFs
        batch_progress_label.config(
            text=f"Finding available PDFs\nfor batch {batch_num_label}"
        )
        batch_progress_frame.update()

        # Gets available print PDFs
        fill_available_pdfs_dict(material, contents, include_OTs)

        # If enforce minimum length is true, this will ensure there are
        # sufficient PDFs to meet the minimum length.
        if care_min_length is True:
            check_min_length(material, min_batch_length)

        # Updates status label to creating batch
        batch_progress_label.config(text="PDFs found. Creating batch.")
        batch_progress_frame.update()

        # Begins batch creation
        batch_dict = create_batch(batch_dict, available_pdfs)

        # Updates status label to grouping PDFs
        batch_progress_label.config(text="Batch created. Grouping PDFs.")
        batch_progress_frame.update()

        # Groups PDF
        batch_dict = create_batch_folders(batch_dict)

        # Updates progress bar
        batch_progress_bar["value"] += 1
        batch_progress_label.config(text=f"Finished batch {batch_num_label}")
        batch_progress_frame.update()

    progress_done_btn.config(state=NORMAL)

    return reset_batch_dicts()


def create_batch_folders(batch_dict: dict) -> None:
    """
    Creates a new batch folder and fills it with the relevant PDFs.
    Accepts batch_dict as a dict.

    Returns nothing.
    """

    # Variables from batch_dict for the new batch directory
    batch_ID = batch_dict["batch_details"]["ID"]
    batch_priority = batch_dict["batch_details"]["priority"]
    batch_material = batch_dict["batch_details"]["material"]
    batch_length = batch_dict["batch_details"]["length"]
    if (str(batch_length).endswith(".0")) or (str(batch_length).endswith(".5")):
        batch_length = str(batch_length) + "0"
    tag = "Hotfolder"

    # New batch directory name and path assembly
    batch_dir_name_1 = BATCH_FOLDERS_DIR + "Batch #"
    batch_dir_name_2 = str(batch_ID) + " " + batch_material
    batch_dir_name_3 = " L" + str(batch_length) + " P-" + str(batch_priority)
    batch_directory = batch_dir_name_1 + batch_dir_name_2 + batch_dir_name_3

    # Make new batch directory and the Full and Sample hotfolders
    mkdir(batch_directory)
    make_batch_dirs(batch_directory)

    # Print new batch confirmation
    print("\n| New Batch:", str(batch_ID))
    print("| Material:", batch_material)
    print("| Length:", batch_length)

    # List of batch lists to iterate through and move pdfs
    list_of_batch_lists = (
        batch_dict["OT"]["full"]["batch_list"],
        batch_dict["OT"]["sample"]["batch_list"],
        batch_dict["Late"]["full"]["batch_list"],
        batch_dict["Late"]["sample"]["batch_list"],
        batch_dict["Today"]["full"]["batch_list"],
        batch_dict["Today"]["sample"]["batch_list"],
        batch_dict["Tomorrow"]["full"]["batch_list"],
        batch_dict["Tomorrow"]["sample"]["batch_list"],
        batch_dict["Future"]["full"]["batch_list"],
        batch_dict["Future"]["sample"]["batch_list"],
    )

    # Setup for iterating through the proper dirs inside a batch folder
    priority_counter = 0
    priority_dict = {
        1: batch_directory + "/1 - OT/Full",
        2: batch_directory + "/1 - OT/Samples",
        3: batch_directory + "/2 - Late/Full",
        4: batch_directory + "/2 - Late/Samples",
        5: batch_directory + "/3 - Today/Full",
        6: batch_directory + "/3 - Today/Samples",
        7: batch_directory + "/4 - Tomorrow/Full",
        8: batch_directory + "/4 - Tomorrow/Samples",
        9: batch_directory + "/5 - Future/Full",
        10: batch_directory + "/5 - Future/Samples",
    }

    # begin moving PDFs in the batch_dict to the new directory folders
    for batch_list in list_of_batch_lists:
        priority_counter += 1
        if len(batch_list) > 0:
            for print_pdf in batch_list:
                if "BlankPdf" in print_pdf:
                    pdf_height = str(get_pdf.height(print_pdf))
                    blank_panel = BVH["Blank Panels"][pdf_height]
                    batch_dir = priority_dict[priority_counter]
                    new_name = batch_dir + "/" + print_pdf.split("/")[-1]
                    copy(blank_panel, new_name)
                else:
                    try_to_move_pdf(
                        print_pdf,
                        priority_dict[priority_counter],
                        get_pdf.friendly_name(print_pdf),
                    )
                    continue
    priority_counter = 0

    # After moving items, iterate through full orders and split any that
    # are >2 repeat. If anything isn't cropped, it returns the manual tag.
    tag = split_full_pdfs(batch_directory)

    # Check if a color guide or roll stickers needs to be added, then add them.
    color_guide_short = batch_dict["batch_details"]["color_guides"]
    if color_guide_short["unique_filename"] != "":
        copy(
            color_guide_short["default"],
            batch_directory + color_guide_short["unique_filename"],
        )
    roll_sticker_short = batch_dict["batch_details"]["roll_stickers"]
    if roll_sticker_short["unique_filename"] != "":
        copy(
            roll_sticker_short["default"],
            batch_directory + roll_sticker_short["unique_filename"],
        )

    # Apply the manual or hotfolder tag
    apply_tag(tag, batch_directory)
    remove_empty_directories(batch_directory)

    return


def make_batch_dirs(batch_directory: str) -> None:
    """
    Accepts batch_directory as a string. Makes all the proper batch
    directories for the batch folder to keep it organized

    Returns nothing.
    """

    batch_listDict = (
        batch_directory + "/1 - OT",
        batch_directory + "/2 - Late",
        batch_directory + "/3 - Today",
        batch_directory + "/4 - Tomorrow",
        batch_directory + "/5 - Future",
        batch_directory + "/6 - Utility",
    )
    batch_listDict2 = (
        batch_listDict[0] + "/Full",
        batch_listDict[0] + "/Samples",
        batch_listDict[1] + "/Full",
        batch_listDict[1] + "/Samples",
        batch_listDict[2] + "/Full",
        batch_listDict[2] + "/Samples",
        batch_listDict[3] + "/Full",
        batch_listDict[3] + "/Samples",
        batch_listDict[4] + "/Full",
        batch_listDict[4] + "/Samples",
    )

    for batch_list in batch_listDict:
        mkdir(batch_list)

    for batch_list in batch_listDict2:
        mkdir(batch_list)


def create_batch(batch_dict: dict, available_pdfs: dict) -> dict:
    """
    Gathers PDFs for the new batch. Accepts batch_dict and
    available_pdfs as dicts

    Returns a dict.
    """

    # Not using include_OTs because it should have been handled prior to this.
    includeOTs = batch_dict["batch_details"]["include_OTs"]
    cur_length = batch_dict["batch_details"]["length"]
    mat_length = batch_dict["batch_details"]["material_length"]

    for priority in BV["Priorities"]:
        priority = BV["Priorities"][priority]
        batch_dict = batch_loop_controller(priority, "full", batch_dict, available_pdfs)
        if cur_length < (mat_length - 10):
            batch_dict = batch_loop_controller(
                priority, "sample", batch_dict, available_pdfs
            )
        else:
            continue

    """
    Original code was below this. I'm confident that the for loop above will
    handle this properly, but I'm not entirely sure, mainly because I don't
    know what I was thinking when I wrote the original code.

    If the above code didn't work, retrieve the code that was below this
    from a previous commit. Look for commit with SHA 23bb6c

    Line to help find the code:
    if includeOTs == True: #checks whether or not the batch should contain
    """

    batch_dict["batch_details"]["priority"] = set_batch_priority(batch_dict)
    batch_dict = add_color_guides(batch_dict)

    return batch_dict


def batch_loop_controller(
    due_date: str, full_or_samp: str, batch_dict: dict, available_pdfs: dict
) -> dict:
    """
    Controls calling the proper batch loop based on order size. Accepts
    due_date and full_or_samp as a string, and batch_dict and available_pdfs
    as a dict.

    Returns batch_dict as a dict.
    """

    batch_due = batch_dict[due_date]
    batch_size = batch_due[full_or_samp]
    batch_deets = batch_dict["batch_details"]
    available_list = available_pdfs[due_date][full_or_samp]

    if full_or_samp.lower() == "full":
        batch_size = batch_loop_full(
            batch_deets, batch_size, available_list["batch_list"]
        )
        batch_deets["length"] += batch_size["batch_length"]
    else:
        batch_size = batch_loop_samp(
            batch_deets, batch_size, available_list["batch_list"]
        )
        batch_deets["length"] += batch_size["batch_length"]
    return batch_dict


def batch_loop_samp(
    batch_dict: dict, batch_date_dict: dict, available_pdfs: dict
) -> dict:
    """
    Loop for adding samples to a batch and calculating length. Accepts
    batch_dict, batch_date_dict, and available_pdfs each as a dict.

    Returns a dict.
    """
    # assign variables for ease of use
    current_length = batch_dict["length"]
    max_length = batch_dict["material_length"]
    sorted_list = available_pdfs
    batch_list = []

    """
    Get the number of samples we can fit in the remaining length.
    Because samples are a fixed size, we calculate the number of samples
    that can fixed rather than the remaining percentage

    Take the availalbe length, subtract the current length, divide by 9.5
    (the length of a sample, plus a bit more), round down, then multiply by
    two because we can fit two samples side by side.
    """

    samples_allowed = (floor((max_length - current_length) / BV["Sample Size"])) * 2
    samples_added = 0

    # Main sample loop
    for print_pdf in sorted_list:
        room_in_order = same_order_samples(
            get_pdf.order_number(print_pdf), sorted_list, samples_allowed, samples_added
        )
        if not room_in_order:
            continue
        else:
            batch_list.append(print_pdf)
            samples_added += 1
            if samples_added == samples_allowed:
                break
    # Calculate length to add to the current batch. Take the number of samples
    # and divide it by two, rounded down, for the number of full rows. Then
    # take the number of samples mod 2 to see if there's a single sample
    # row. Add the two together, then multiply by 9.5 for the length.
    length_to_add = (floor(samples_added / 2) + (samples_added % 2)) * BV["Sample Size"]

    if len(batch_list) % 2 == 1:
        temp_height = get_pdf.height(batch_list[-1])
        temp_num = get_pdf.order_number(batch_list[-1])
        temp_lookup = BVH["Blank Panels"][str(temp_height)]
        temp_name = temp_lookup.replace("999999999", temp_num)
        batch_list.append(temp_name)

    batch_date_dict["batch_list"] = batch_list
    batch_date_dict["batch_length"] = length_to_add
    return batch_date_dict


def batch_loop_full(batch_dict: dict, batch_date_dict: dict, available_pdfs) -> dict:
    """
    Accepts batch_dict, batch_date_dict, and available_pdfs each as a dict.
    Loop for adding full pdfs to a batch and calculating length.

    Returns batch_date_dict as a dict.
    """

    current_length = batch_dict["length"]
    max_length = batch_dict["material_length"]
    sorted_list = available_pdfs
    batch_list = []
    if max_length >= 480:
        split_formula = max_length * GV["Full Samp Split"]
    else:
        split_formula = max_length

    current_section_length = 0
    find_odd = False
    odd_match_height = 0

    # Begins to iterate over sorted list
    for print_pdf in sorted_list:
        # If the remaining length is ever less than 39", break the loop.
        # No full panles are shohrter than 40", so this should save
        # some time.
        if current_section_length + current_length > (max_length - 39):
            break

        # Variables for ease of use
        pdf_length = get_pdf.length(print_pdf)
        pdf_odd_or_even = get_pdf.odd_or_even(print_pdf)
        pdf_height = get_pdf.height(print_pdf)

        if find_odd == True:
            if pdf_height != odd_match_height:
                find_odd = False
                temp_height = get_pdf.height(batch_list[-1])
                temp_num = get_pdf.order_number(batch_list[-1])
                temp_lookup = BVH["Blank Panels"][str(temp_height)]
                temp_name = temp_lookup.replace("999999999", temp_num)
                batch_list.append(temp_name)


        # Program will attempt to match odd-quantity orders next to
        # similar odd-quantity orders. This allows material to be saved
        # as orders are printed next to one another.
        if find_odd is False:
            # If the current item in the iteration will put the batch over
            # max length, skip it.
            potential_length = current_section_length + current_length
            if potential_length + pdf_length > split_formula:
                continue
            else:
                # Add the length of the item to the length of the batch
                current_section_length += pdf_length
                # Add the path of the item to the batch list
                batch_list.append(print_pdf)
                # If the item was odd, set the flags to search
                # for an item with a matching height.
                if pdf_odd_or_even == 1:
                    find_odd = True
                    odd_match_height = pdf_height
        # If the current iteration needs to find an odd item:
        elif find_odd is True:
            # If the current item in the iteration is odd
            if pdf_odd_or_even == 1:
                # If the current item also matches the height of the
                # last added item
                if odd_match_height == pdf_height:
                    # If adding the current odd item will make the current
                    # length greater than the max length, skip it
                    potential_length = current_section_length + current_length
                    odd_adjustment = pdf_length - (pdf_height + 0.5)
                    if potential_length + odd_adjustment > split_formula:
                        continue
                    else:
                        # If the last item and current item match heights, are
                        # both odd, and won't make the batch too long, add the
                        # length of the new item to the current length but
                        # remove the height of one row. This is because two
                        # matching odd panels will fit in a single row and the
                        # length of that row doesn't need to be added twice.
                        current_section_length += odd_adjustment
                        # Add the path of the item to the batch list
                        batch_list.append(print_pdf)
                        find_odd = False
                else:
                    # If the current item in the iteration will
                    # put the batch over the max length, skip it.
                    potential_length = current_section_length + current_length
                    if potential_length + pdf_length > split_formula:
                        continue
                    else:
                        # If the next item in the list doesn't match the
                        # pdf_height, add a blank panel to the batch. Shouldn't
                        # need to change the height because it should always
                        # fit for odds.
                        if pdf_height != odd_match_height:
                            # Appends the batch list with a blank panel that
                            # has the default "999999999" replaced with the
                            # order's number. The height of the PDF is selected
                            # based on the last item in the batch list
                            temp_height = get_pdf.height(batch_list[-1])
                            temp_num = get_pdf.order_number(batch_list[-1])
                            temp_lookup = BVH["Blank Panels"][str(temp_height)]
                            temp_name = temp_lookup.replace("999999999", temp_num)
                            batch_list.append(temp_name)
                        # Because we feed the loop a sorted list, the very
                        # next item in the list should match. If it doesn't,
                        # it means there are no matching items and the current
                        # PDF should be added to the batch and the length
                        # added normally.
                        current_section_length += pdf_length
                        batch_list.append(print_pdf)
                        odd_match_height = pdf_height
                        find_odd = False
    """
    Commenting this out because I believe it's adding an erroneous
    extra panel, making batches a single panel too long.
    """
    # # Because we add a blank filler PDF for an item on the succeeding
    # # iteration, add a check for the last item in the loop.
    # try:
    #     if get_pdf.odd_or_even (batch_list[-1]) == 1:
    #         temp_height = get_pdf.height(batch_list[-1])
    #         temp_num = get_pdf.order_number(batch_list[-1])
    #         temp_lookup = bv.blank_panels[str(temp_height)]
    #         temp_name = temp_lookup.replace('999999999',
    #                                           temp_num)
    #         batch_list.append(temp_name)
    # except:
    #     pass

    batch_date_dict["batch_list"] = batch_list
    batch_date_dict["batch_length"] = current_section_length
    return batch_date_dict


def check_min_length(material: str, min_batch_length: int) -> None:
    """
    Iterates through the priorities of the available_pdfs dict to figure out
    if the available PDFs are enough for a minimum batch length.
    """
    batch_length = 0
    for priority in BV["Priorities"]:
        priority = BV["Priorities"][priority]
        full_length = available_pdfs[priority]["full"]["batch_length"]
        samp_length = available_pdfs[priority]["sample"]["batch_length"]
        batch_length += full_length + samp_length

    if batch_length < min_batch_length:
        print(f"Not enough {material} PDFs to make a batch with given specs.")
        return
    else:
        return


def fill_available_pdfs_dict(material: str, contents: int, include_OTs: bool) -> None:
    """
    Accepts material as a string, contents as an integer, and include OTs as a
    boolean. Iterates through print PDFs according to the parameters and fills
    the available PDFs dict.
    """

    for priority in BV["Priorities"]:
        avlbl_short = available_pdfs[BV["Priorities"][priority]]
        if priority == "OT":
            if include_OTs is False:
                continue
        if contents == 2:
            pass
        else:
            # Name shortener for readability
            avlbl_size = avlbl_short["full"]
            # Retrieves a sorted list of full PDFs
            glob_lst = get_pdf_glob(priority, material, "full")
            avlbl_size["batch_list"] = BS.sort_pdf_list(glob_lst)
            # Calculates a length for the sorted list of full PDFs
            avlbl_size["batch_length"] = BS.calculate_full_length(
                avlbl_size["batch_list"]
            )
        if contents == 1:
            pass
        else:
            # Name shortener for readability
            avlbl_size = avlbl_short["sample"]
            # Retrieves a sorted list of sample PDFs
            glob_lst = get_pdf_glob(priority, material, "sample")
            avlbl_size["batch_list"] = BS.sort_pdfs_by_order_number(glob_lst)
            # Calculates a length for the sorted list of sample PDFs
            avlbl_size["batch_length"] = BS.calculate_sample(avlbl_size["batch_list"])


def get_pdf_glob(due_date: str, material: str, full_or_samp: str) -> list:
    """
    Accepts a "due date" (OT, Late, Today, Tomorrow, Future), a material type
    as a string, and full or sample as a string, then returns a glob list.
    """
    due_date_lookup = {
        1: "1 - OT/",
        2: "2 - Late/",
        3: "3 - Today/",
        4: "4 - Tomorrow/",
        5: "5 - Future/",
        "all": "*/",
    }
    material = GVH["Lookups"]["Paper Dirs"][material]
    if full_or_samp.lower() == "full":
        full_or_samp = "Full/**/*.pdf"
    elif full_or_samp.lower() == "sample":
        full_or_samp = "Sample/*.pdf"
    else:
        full_or_samp = "**/*.pdf"

    # Neatly assemble glob string for readability
    glob_date = due_date_lookup[due_date]
    glob_list = SORTING_DIR + glob_date + material + full_or_samp

    return glob(glob_list, recursive=True)


def set_batch_priority(batch_dict: dict) -> str:
    """
    Accepts batch_dict as a dict. Iterates over each batch list and sets
    the appropriate priority. Returns priority as a string.
    """
    ot_full = batch_dict["OT"]["full"]["batch_list"]
    ot_samp = batch_dict["OT"]["sample"]["batch_list"]
    late_full = batch_dict["Late"]["full"]["batch_list"]
    lateSamp = batch_dict["Late"]["sample"]["batch_list"]
    todayFull = batch_dict["Today"]["full"]["batch_list"]
    todaySamp = batch_dict["Today"]["sample"]["batch_list"]
    tomorrowFull = batch_dict["Tomorrow"]["full"]["batch_list"]
    tomorrowSamp = batch_dict["Tomorrow"]["sample"]["batch_list"]
    futureFull = batch_dict["Future"]["full"]["batch_list"]
    futureSamp = batch_dict["Future"]["sample"]["batch_list"]

    if (len(ot_full) > 0) or (len(ot_samp) > 0):
        return "OT"
    elif (len(late_full) > 0) or (len(lateSamp) > 0):
        return "Late"
    elif (len(todayFull) > 0) or (len(todaySamp) > 0):
        return "Today"
    elif (len(tomorrowFull) > 0) or (len(tomorrowSamp) > 0):
        return "Tomorrow"
    elif (len(futureFull) > 0) or (len(futureSamp) > 0):
        return "Future"


def add_color_guides(batch_dict: dict) -> dict:
    """
    Accepts batch_dict as a dict. Checks if the total length can fit color
    guides or roll stickers, and adds them appropriately
    """
    batch_details = batch_dict["batch_details"]
    batch_material = batch_details["material"]
    batch_length = batch_details["length"]
    material_length = batch_details["material_length"]
    color_guides = batch_details["color_guides"]
    roll_stickers = batch_details["roll_stickers"]

    if batch_length <= material_length - 8:
        utlty_qty = floor((material_length - batch_length) / BV["Sample Size"])
        if utlty_qty == 0:
            utlty_qty = 1
            color_guides["unique_filename"] = utlty_name_assy(
                "color_guides", batch_material, utlty_qty
            )
            batch_length += utlty_qty * BV["Sample Size"]
        elif utlty_qty <= 11:
            color_guides["unique_filename"] = utlty_name_assy(
                "color_guides", batch_material, utlty_qty
            )
            batch_length += utlty_qty * BV["Sample Size"]
        elif utlty_qty > 11:
            sticker_qty = 2
            utlty_qty = utlty_qty - sticker_qty
            color_guides["unique_filename"] = utlty_name_assy(
                "color_guides", batch_material, utlty_qty
            )
            roll_stickers["unique_filename"] = utlty_name_assy(
                "roll_stickers", batch_material, sticker_qty
            )
            batch_length += utlty_qty * BV["Sample Size"]
            batch_length += 19

    batch_details["length"] = batch_length

    return batch_dict


def utlty_name_assy(utility_type: str, material: str, quantity: int) -> str:
    """
    Accepts a material as a string and quantity as an int. Assembles a unique
    filename for utility files.

    Returns a string.

    Final file name will look similar to:
    '/6 - Utility/999999999-1-(YYYY-MM-DD)-Stnd-Sm-Samp-Rp 2-
    Qty 4-Roll Stickers-L19-W25-H9.pdf'
    """

    section_1 = "/6 - Utility/999999999-1-("
    due_date = str(TODAY)
    section_2 = ")-Stnd-"
    material = GV["Paper Types"][material]["Short Name"]
    section_3 = "-Samp-Rp 2-Qty "
    quantity = str(quantity * 2)
    if utility_type == "color_guides":
        section_4 = "-Color Chart-L"
        length = str((int(quantity) * BV["Sample Size"])/2)
        section_5 = "-W25-H9.pdf"
    elif utility_type == "roll_stickers":
        section_4 = "-Roll Stickers-"
        length = str((int(quantity) * BV["Sample Size"])/2)
        section_5 = "-W25-H9.pdf"

    unique_name_1 = section_1 + due_date + section_2 + material + section_3
    unique_name_2 = quantity + section_4 + length + section_5

    unique_name = unique_name_1 + unique_name_2

    return unique_name


def same_order_samples(
    order_number: str, sorted_list: list, samples_allowed: int, samples_added: int
) -> bool:
    """
    When adding samples to a batch, checks for and counts other samples in
    the same order, ensures they will all fit in the batch.
    """

    samples_in_order = 0

    for print_pdf in sorted_list:
        if order_number in print_pdf:
            samples_in_order += 1
    if samples_added + samples_in_order > samples_allowed:
        return False
    return True


def apply_tag(tag_name: str, path: str) -> None:
    """
    Accepts a tag_name as a string and a path as a string. Uses macos_tags
    module to add a tag inside macOS finder.

    Returns nothing.
    """
    tag = tag_name
    macos_tags.add(tag, file=path)


def remove_empty_directories(batch_directory: str) -> None:
    """
    Once a batch folder has been made, walks through the batch folder and
    removes any empty directories.

    Returns nothing.
    """

    dir_to_walk = list(walk(batch_directory))
    for path, _, _ in dir_to_walk[::-1]:
        if len(listdir(path)) == 0:
            rmdir(path)
    return


def split_full_pdfs(batch_directory: str) -> str:
    """
    Accepts batch_directory as a string. Iterates through the directory
    looking for full orders that have a repeat of more than 2'. If it
    finds one, calls pdf_splitter.crop_multi_panel_pdfs to separate
    the PDF into multiple, 2' panels to import into caldera easily.

    Returns a tag to be used in macOS so the user knows if the batch can
    be imported via a hotfolder or if it needs to be done manually.
    """

    dirs_to_loop = [
        "/1 - OT",
        "/2 - Late",
        "/3 - Today",
        "/4 - Tomorrow",
        "/5 - Future",
    ]
    tag = "Hotfolder"

    for due_date in dirs_to_loop:
        glob_dir = batch_directory + due_date + "/Full/*.pdf"
        for print_pdf in glob(glob_dir, recursive=True):
            if "999999999" in print_pdf:
                continue
            if get_pdf.repeat(print_pdf) > 2:
                try:
                    crop_dir = batch_directory + due_date + "/Full"
                    pdf_splitter.crop_multipanel_pdfs(print_pdf, crop_dir)
                except errors.PdfReadError:
                    print("| Couldn't split file. In case it's needed, a")
                    print("copy of the original file is in")
                    print('"#Past Orders/Original Files"')
                    print("| PDF:", get_pdf.friendly_name(print_pdf))
                    tag = "Manual"

    return tag


def reset_batch_dicts():
    """
    Resets both batch dictionaries.

    Accepts nothing.

    Returns nothing.
    """
    available_pdfs = reset_available_pdfs()
    batch_dict = reset_batch_dict()
    return

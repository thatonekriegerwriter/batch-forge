# /Users/Trevor/Documents/Scripts/batch-forge python
# UI Script for Batch Forge

from glob import glob
from tkinter import *

from batch_sorting import *
from batching_window import batch_orders_window
from caldera_importing_window import caldera_import_window
from sorter_window import sort_zipped_packages_window
from wallpaper_sorter_functions import moveForDueDates
from batch_forge_config import GENERAL_VARS_HIDDEN as GVH
from batch_forge_config import INSTALLATION_DIR

sort_results = []

# Necessary Caldera Directories
DOWNLOAD_DIR = GVH["Caldera Dirs"]["Downloads"]
SORTING_DIR = GVH["Caldera Dirs"]["Sorting"]


# Initilize TK and main menu window
root = Tk()
app_image = Image("photo", file=INSTALLATION_DIR + "assets/batch_forge_icon.png")
root.call("wm", "iconphoto", root._w, app_image)
root.title("Batch Forge")
root.geometry("300x350")
root.minsize(300, 350)
root.maxsize(300, 350)

main_menu_frame = LabelFrame(root, text="Main Menu", padx=10, pady=10)

main_menu_frame.pack(padx=10, pady=10)

button_sort_orders = Button(
    main_menu_frame,
    text="Sort Orders",
    width=20,
    height=2,
    command=lambda: sort_zipped_packages_window(root),
)

button_sort_orders.pack()

if len(glob(DOWNLOAD_DIR + "*.zip")) == 0:
    button_sort_orders["text"] = "No Orders to Sort"
    button_sort_orders["state"] = DISABLED

button_batch_orders = Button(
    main_menu_frame,
    text="Build-A-Batch",
    width=20,
    height=2,
    command=lambda: batch_orders_window(root),
).pack()

button_caldera_importer = (
    Button(
        main_menu_frame,
        text="Caldera Importer",
        width=20,
        height=2,
        command=lambda: caldera_import_window(root),
    ).pack(),
)

button_drive_downloader = Button(
    main_menu_frame, text="Download from Drive", width=20, height=2
).pack()

button_dates_update = Button(
    main_menu_frame,
    text="Update Sort for Due Dates",
    width=20,
    height=2,
    command=lambda: moveForDueDates(glob(SORTING_DIR + "**/*.pdf", recursive=True)),
).pack()

button_quit = Button(
    main_menu_frame, text="Quit Batch Forge", width=20, height=2, command=root.quit
).pack()

root.mainloop()

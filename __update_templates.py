import glob
import os
import shutil

root_folder = "./_templates"

# doc templates
src_folder = f"{root_folder}/base"
lst_src_files = glob.glob("{}/_*.tex".format(src_folder))
lst_fig_files = glob.glob("{}/figs/*".format(src_folder))

lst_dst_folders = [
    f"{root_folder}/paper",
    f"{root_folder}/report",
]
# tex files
for f in lst_src_files:
    fnm = os.path.basename(f)
    print(fnm)
    for d in lst_dst_folders:
        print(f"--- copied to {d}")
        dst_f = f"{d}/{fnm}"
        shutil.copy(
            src=f,
            dst=dst_f
        )
# fig files
for f in lst_fig_files:
    fnm = os.path.basename(f)
    print(fnm)
    for d in lst_dst_folders:
        print(f"--- copied to {d}")
        dst_f = f"{d}/figs/{fnm}"
        shutil.copy(
            src=f,
            dst=dst_f
        )
import shutil
from pathlib import Path

from losalamos.docs import Drawing

if __name__ == "__main__":

    '''
    TESTING FOR THE OFFSET PROBLEM
    
    Description: somehow the text items get whitespaces while in the .save() method of the Drawing() object.
    
    Weird: the issue seems to depend on the input file! May be is something in the source file, not the code.
    
    For now the offsetting problem is showing up only in the fig_b.svg. fig_a.svg goes just fine.
    
    '''

    print("Hello world")
    print("Testing the Drawing method")

    # ****** SETUP ******

    # set output folder:
    output_folder = Path("data")
    output_folder.mkdir(parents=True, exist_ok=True)

    # set up multiple testing
    dc_figs = {
        "fig_a": {
            "layers2hide": ["frame", "labels_pt"],
            "layers2show": ["drawings", "labels_en"],
        },
        "fig_b": {
            "layers2hide": ["frame", "leaderlines"],
            "layers2show": ["main", "labels_details"],
        }
    }

    # run tests
    for fig in dc_figs:
        print(f">> testing {fig}")
        # set source SVG file (it is in the repo '_templates' folder)
        source_file = Path(f"_templates/{fig}.svg")

        # make a copy of source file to ensure testing reproducibility
        input_file = f"{output_folder}/{fig}_copy.svg"
        shutil.copy(source_file, input_file)

        # ****** TESTS ******

        # instatiate the object
        dw = Drawing()

        # load data to object
        dw.load_data(file_data=input_file)

        # Test 1 -- simple export (default from template)
        print(">> TEST 1: simple export")
        dw.export_image(
            output_file=f"{output_folder}/{fig}_test1_simple.png",
            dpi=300,
            drawing_id="mainframe",
            to_jpg=False,
            layers2hide=None, # here is the catch
            layers2show=None, # here is the catch
        )

        # Test 2 -- hide and show layers
        print(">> TEST 2: hide and show layers export")
        dw.export_image(
            output_file=f"{output_folder}/{fig}_test1_hide.png",
            dpi=300,
            drawing_id="mainframe",
            to_jpg=False,
            layers2hide=dc_figs[fig]["layers2hide"],  # here is the catch
            layers2show=dc_figs[fig]["layers2show"],  # here is the catch
        )

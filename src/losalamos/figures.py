# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
from PIL import Image, ImageOps
from lxml import etree

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import DataSet


# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Figure(DataSet):

    # todo docstring

    def __init__(self, name="MyFig", alias="Fig"):

        super().__init__(name=name, alias=alias)

    def load_data(self, file_data):

        self.file_data = Path(file_data).absolute()

    @staticmethod
    def scale_image(file_input, file_output, scale_factor, dpi=300):
        """
        Scale an image by a numerical factor while maintaining its original aspect ratio.

        :param file_input: Path to the source image file.
        :type file_input: str
        :param file_output: Path where the scaled image will be saved.
        :type file_output: str
        :param scale_factor: Multiplier for the image dimensions (e.g., 0.5 for half size).
        :type scale_factor: float
        :param dpi: Resolution in dots per inch for the output file metadata. Default value = ``300``
        :type dpi: int
        :return: No value is returned.
        :rtype: None

        .. note::

             The resizing process utilizes the ``Image.Resampling.LANCZOS`` filter to ensure high-quality downsampling or upsampling. The output is saved with a fixed quality compression of ``95``.

        """
        img = Image.open(file_input)

        # Compute new dimensions while maintaining aspect ratio
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        # Resize image using high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save the image with 300 DPI
        img.save(file_output, dpi=(dpi, dpi), quality=95)
        return None

    @staticmethod
    def make_thumbnail(
        file_input,
        file_output,
        size=(512, 512),
        figure_ratio=None,
        mode="crop",
        dpi=300,
        quality=85,
        background=(255, 255, 255),
    ):
        """
        Generate a lightweight JPEG thumbnail from an input image with resizing options.

        :param file_input: Path to the source image file.
        :type file_input: str
        :param file_output: Path where the generated thumbnail will be saved.
        :type file_output: str
        :param size: Target dimensions for the output image. Default value = ``(512, 512)``
        :type size: tuple
        :param figure_ratio: [optional] Aspect ratio used to calculate target height from width.
        :type figure_ratio: tuple
        :param mode: Resizing strategy, either ``crop`` to fill dimensions or ``fit`` to pad. Default value = ``crop``
        :type mode: str
        :param dpi: Resolution in dots per inch for the output file. Default value = ``300``
        :type dpi: int
        :param quality: JPEG compression quality from 1 to 100. Default value = ``85``
        :type quality: int
        :param background: RGB color used for padding when mode is ``fit``. Default value = ``(255, 255, 255)``
        :type background: tuple
        :return: No value is returned.
        :rtype: None

        .. note::

             The function automatically converts non-compatible image modes to ``RGB`` to ensure JPEG compatibility.
             If ``figure_ratio`` is provided as ``(width, height)``,
             it overrides the height specified in the ``size`` parameter.

        """

        img = Image.open(file_input)

        # Ensure compatibility with JPEG
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        target_w, target_h = size

        # Override size using figure ratio if requested
        if figure_ratio is not None:
            rw, rh = figure_ratio
            target_h = int(target_w * rh / rw)

        if mode == "crop":
            img = ImageOps.fit(
                img,
                (target_w, target_h),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

        elif mode == "fit":
            img.thumbnail(
                (target_w, target_h),
                resample=Image.Resampling.LANCZOS,
            )

            # Optional padding to exact size
            canvas = Image.new("RGB", (target_w, target_h), background)
            offset = (
                (target_w - img.width) // 2,
                (target_h - img.height) // 2,
            )
            canvas.paste(img, offset)
            img = canvas

        else:
            raise ValueError("mode must be 'crop' or 'fit'")

        img.save(
            file_output,
            format="JPEG",
            quality=quality,
            optimize=True,
            dpi=(dpi, dpi),
        )

        return None

    @staticmethod
    def image_to_jpg(file_input, file_output, quality=95, dpi=300):
        """
        Convert an image file to JPEG format with specified quality and resolution.

        :param file_input: Path to the input image file.
        :type file_input: str
        :param file_output: Path where the output JPEG will be saved.
        :type file_output: str
        :param quality: Compression quality from 1 to 100. Default value = ``95``
        :type quality: int
        :param dpi: Resolution in dots per inch. Default value = ``300``
        :type dpi: int
        :return: None
        :rtype: NoneType
        """
        with Image.open(file_input) as img:
            # Convert to RGB if the image has an alpha channel
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Save with specified quality and DPI
            save_params = {"format": "JPEG", "quality": quality}
            if dpi:
                save_params["dpi"] = (dpi, dpi)
            img.save(file_output, **save_params)
        return None


class FigureSVG(Figure):

    def __init__(self, name="MySVG", alias="SVG"):

        super().__init__(name=name, alias=alias)

        self.tree = None

        # set defaults
        # --------------------------------------------------
        self.inkscape_src = "C:/Program Files/Inkscape/bin"
        self.name_spaces = {
            "svg": "http://www.w3.org/2000/svg",
            "inkscape": "http://www.inkscape.org/namespaces/inkscape",
        }

    def load_data(self, file_data):
        """
        Load and parse SVG XML data from a file path into the object instance.

        :param file_data: The file system path pointing to the source SVG data.
        :type file_data: str
        :return: No value is returned.
        :rtype: None

        .. important::

             This method converts the input path to an absolute path and utilizes
             an ``etree.XMLParser`` with ``huge_tree`` enabled to handle large datasets.
             It populates the ``tree`` and ``data`` attributes before triggering an internal ``update`` call.

        """

        # overwrite relative path input
        # --------------------------------------------------
        self.file_data = Path(file_data).absolute()

        # load tree
        # --------------------------------------------------
        parser = etree.XMLParser(huge_tree=True)
        self.tree = etree.parse(self.file_data, parser)

        # get the root
        # --------------------------------------------------
        self.data = self.tree.getroot()

        # update
        # --------------------------------------------------
        self.update()

        # ... continues in downstream objects ... #

        return None

    def save(self):
        # todo docstring
        xml_str = etree.tostring(
            self.tree, encoding="utf-8", xml_declaration=True, pretty_print=False
        )

        with open(self.file_data, "wb") as f:
            f.write(xml_str)

        return None

    def export(self, folder, filename, data_suffix=None):
        # todo docstring
        if data_suffix is None:
            data_suffix = ""
        output_file = str(Path(folder) / f"{filename}{data_suffix}.svg")
        original_file = str(self.file_data)[:]
        self.file_data = output_file
        self.save()
        self.file_data = Path(original_file[:])
        return None

    def find_layer(self, label="frames"):
        # todo docstring
        key = "{" + self.name_spaces["inkscape"] + "}"
        # Find the <g> group with the specific Inkscape label
        layer = self.data.find(
            f".//svg:g[@inkscape:label='{label}']", namespaces=self.name_spaces
        )
        return layer

    def hide_layer(self, label="frames"):
        # todo docstring
        layer = self.data.find(
            f".//svg:g[@inkscape:label='{label}']", namespaces=self.name_spaces
        )
        layer.set("style", "display:none")  # Hide the layer
        return None

    def show_layer(self, label="frames"):
        # todo docstring
        layer = self.data.find(
            f".//svg:g[@inkscape:label='{label}']", namespaces=self.name_spaces
        )
        layer.set("style", "display:inline")  # Show the layer
        return None

    def to_image(
        self,
        output_file=None,
        dpi=300,
        drawing_id=None,
        to_jpg=False,
        remove_png=True,
        hidden_layers=None,
        show_layers=None,
    ):
        """
        Export the current drawing as an image file, optionally adjusting layers and format.


        """
        import subprocess

        # Get abspath
        output_file = Path(output_file).resolve()

        # handle visibility of layers
        if hidden_layers is not None:
            for lbl in hidden_layers:
                self.hide_layer(label=lbl)
                self.save()

        if show_layers is not None:
            for lbl in show_layers:
                self.show_layer(label=lbl)
                self.save()

        # set return file
        return_file = output_file

        # move to inkscape source
        """
        current_directory = os.getcwd()
        os.chdir(self.inkscape_src)
        """

        # build command
        # -----------------------------------------------------------------------
        if output_file is None:
            s_command = 'inkscape --export-dpi={} --export-type="png" "{}"'.format(
                dpi, self.file_data
            )
        else:
            s_command = 'inkscape --export-dpi={} --export-type="png" '.format(dpi)
            s_command = s_command + '--export-filename="{}" "{}"'.format(
                output_file, self.file_data
            )

        if drawing_id:
            s_aux = "inkscape --export-id=" + drawing_id
            s_command = s_command.replace("inkscape", s_aux)

        # call inkscape process
        # -----------------------------------------------------------------------
        subprocess.run(s_command)

        # go back
        # os.chdir(current_directory)

        # handle jpg conversion
        # -----------------------------------------------------------------------
        """
        if to_jpg:
            # print(str(output_file))
            new_file = str(output_file).replace(".png", ".jpg")
            Drawing.convert_png_to_jpg(
                input_file=output_file, output_file=new_file, dpi=dpi
            )
            if remove_png:
                os.remove(output_file)
            # reset return file
            return_file = new_file[:]
        """

        return return_file


# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}

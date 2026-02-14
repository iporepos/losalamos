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
import pprint
import shutil
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
    def image_to_jpeg(file_input, file_output, quality=95, dpi=300):
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
        self.inkscape_src = "C:/Program Files/Inkscape/bin"  # None # inkscape.exe folder in Windows (consider add to PATH).
        self.name_spaces = {
            "svg": "http://www.w3.org/2000/svg",
            "inkscape": "http://www.inkscape.org/namespaces/inkscape",
            "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        }

    def _get_namedview(self):
        namedview = self.data.find("sodipodi:namedview", namespaces=self.name_spaces)

        if namedview is None:
            namedview = etree.SubElement(
                self.data,
                f"{{{self.name_spaces['sodipodi']}}}namedview",
                id="namedview1",
            )

        return namedview

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
        """
        Serializes the current XML tree and writes it to the local file system.

        :return: Always returns ``None``
        :rtype: None
        """
        xml_str = etree.tostring(
            self.tree, encoding="utf-8", xml_declaration=True, pretty_print=False
        )

        with open(self.file_data, "wb") as f:
            f.write(xml_str)

        return None

    '''
    # keeping this code block in case bugs in save() arise again

    def save_old(self):
        """
        Serializes the current XML tree and writes it to the local file system.

        :return: Always returns ``None``
        :rtype: None
        """
        root = self.tree.getroot()
        xml_str = etree.tostring(
            root, encoding="utf-8", xml_declaration=True, pretty_print=True
        )

        with open(self.file_data, "wb") as f:
            f.write(xml_str)

        return None

    '''

    def export(self, folder, filename, data_suffix=None):
        """
        Saves the current SVG data to a specific directory with an optional filename suffix.

        :param folder: The destination directory path
        :type folder: str
        :param filename: The base name of the output file
        :type filename: str
        :param data_suffix: [optional] An additional string appended to the filename
        :type data_suffix: str
        :return: Always returns ``None``
        :rtype: None

        .. note::
             This method temporarily overrides the internal ``file_data`` path to execute the
             save operation before restoring the original path.

        """
        if data_suffix is None:
            data_suffix = ""
        output_file = str(Path(folder) / f"{filename}{data_suffix}.svg")
        original_file = str(self.file_data)[:]
        self.file_data = output_file
        self.save()
        self.file_data = Path(original_file[:])
        return None

    def hide_layer(self, label="frames"):
        """
        Modifies the style attribute of a specific layer to make it invisible.

        :param label: The Inkscape label of the layer to hide. Default value = ``frames``
        :type label: str
        :return: Always returns ``None``
        :rtype: None
        """
        layer = self.data.find(
            f".//svg:g[@inkscape:label='{label}']", namespaces=self.name_spaces
        )
        layer.set("style", "display:none")  # Hide the layer
        return None

    def hide_layers(self, labels):
        """
        Hide multiple layers based on a list of provided labels.

        :param labels: A list of layer labels to be hidden.
        :type labels: list
        :return: None
        :rtype: NoneType
        """
        for lbl in labels:
            self.hide_layer(label=lbl)
        return None

    def show_layer(self, label="frames"):
        """
        Modifies the style attribute of a specific layer to make it visible.

        :param label: The Inkscape label of the layer to display. Default value = ``frames``
        :type label: str
        :return: Always returns ``None``
        :rtype: None
        """
        layer = self.data.find(
            f".//svg:g[@inkscape:label='{label}']", namespaces=self.name_spaces
        )
        layer.set("style", "display:inline")  # Show the layer
        return None

    def show_layers(self, labels, inclusive=True):
        """
        Show specified layers and optionally hide all others.

        :param labels: A list of layer labels to be made visible.
        :type labels: list
        :param inclusive: Determines if other layers stay visible or are hidden. Default value = ``True``
        :type inclusive: bool
        :return: None
        :rtype: NoneType

        .. note::

            If ``inclusive`` is set to ``True``, the specified layers are made visible without
            affecting others. If ``False``, the method performs a "show only" operation by
            hiding any layer not present in the ``labels`` list.

        """

        if inclusive:
            for lbl in labels:
                self.show_layer(label=lbl)

        else:
            all_layers = self.get_layers_labels()
            for lbl in all_layers and lbl not in labels:
                self.hide_layer(label=lbl)

        return None

    def get_layers(self):
        """
        Return a dictionary of top-level Inkscape layers indexed by their label.

        :return: Dictionary mapping layer labels to lxml Elements
        :rtype: dict[str, etree.Element]

        .. note::

            Only <g> elements that are direct children of the root <svg> element and
            have inkscape:groupmode="layer" are considered.

        """
        if self.data is None:
            return {}

        layers = self.data.findall(
            "svg:g[@inkscape:groupmode='layer']",
            namespaces=self.name_spaces,
        )

        label_attr = f"{{{self.name_spaces['inkscape']}}}label"

        layer_dc = {}
        for layer in layers:
            label = layer.get(label_attr)

            # Skip layers without labels (defensive)
            if label is None:
                continue

            # If duplicate labels exist, last one wins
            layer_dc[label] = layer

        return layer_dc

    def get_layers_labels(self):
        """
        Return the list of layers labels

        """
        dc = self.get_layers()
        return list(dc.keys())

    def set_page_opacity(self, opacity=1.0):
        """
        Set the Inkscape page background opacity.

        :param opacity: Opacity value in range [0.0, 1.0] (1=opaque)
        :type opacity: float
        """
        opacity = max(0.0, min(1.0, float(opacity)))

        namedview = self._get_namedview()
        namedview.set(
            f"{{{self.name_spaces['inkscape']}}}pageopacity",
            f"{opacity:.6f}",
        )
        return None

    def set_page_color(self, color="#ffffff"):
        """
        Set the Inkscape page background color.

        :param color: Hex color string (e.g. '#ffffff')
        :type color: str
        """
        namedview = self._get_namedview()
        namedview.set("pagecolor", color)
        return None

    def set_element_color(self, element, fill=None, stroke=None):
        """
        Set fill and/or stroke color of an SVG element.

        :param element: lxml SVG element
        :param fill: Fill color (e.g. '#00ff00') or None
        :param stroke: Stroke color or None
        """
        style = self._parse_style(element.get("style"))

        if fill is not None:
            style["fill"] = fill

        if stroke is not None:
            style["stroke"] = stroke

        element.set("style", self._style_to_string(style))
        return None

    def get_layer_elements(self, label, drawable_only=True):
        """
        Return drawable SVG elements from a layer, indexed by element ID.

        :param label: Inkscape layer label
        :param drawable_only: Exclude non-drawable tags (image, defs, etc.)
        :return: dict[str, dict]
        """
        layer = self.get_layers().get(label)

        if layer is None:
            raise ValueError(f"Layer '{label}' not found")

        drawable_tags = {
            "rect",
            "path",
            "circle",
            "ellipse",
            "line",
            "polyline",
            "polygon",
            "text",
        }

        out = {}

        for el in layer.findall(".//*", namespaces=self.name_spaces):
            tag = etree.QName(el).localname

            if drawable_only and tag not in drawable_tags:
                continue

            el_id = el.get("id")
            if el_id is None:
                # Skip elements without IDs (Inkscape usually assigns one)
                continue

            # Defensive: last one wins (should not happen in Inkscape)
            out[el_id] = {
                "element": el,
                "tag": tag,
            }

        return out

    def to_image(
        self,
        file_output=None,
        dpi=300,
        crop_id=None,
        hide_layers=None,
        show_layers=None,
        show_inclusive=True,
        to_jpeg=False,
        remove_png=True,
    ):
        """
        Export the current drawing as an image file, optionally adjusting layers and format.

        :param file_output: [optional] The destination path for the exported image. If None, it defaults to the source file name.
        :type file_output: str or :class:`pathlib.Path`
        :param dpi: Dots per inch for the export resolution. Default value = ``300``
        :type dpi: int
        :param crop_id: [optional] The specific object ID to crop instead of the whole page.
        :type crop_id: str
        :param hide_layers: [optional] List of layer labels to set to hidden before export.
        :type hide_layers: list
        :param show_layers: [optional] List of layer labels to set to visible before export.
        :type show_layers: list
        :param show_inclusive: Whether to show layers inclusively when using ``show_layers``. Default value = ``True``
        :type show_inclusive: bool
        :param to_jpeg: Convert the final output from PNG to JPEG format. Default value = ``False``
        :type to_jpeg: bool
        :param remove_png: Delete the intermediate PNG file if ``to_jpeg`` is True. Default value = ``True``
        :type remove_png: bool
        :return: The path to the generated image file.
        :rtype: :class:`pathlib.Path`

        .. warning::

            This method requires ``inkscape`` to be installed and available in the system PATH.


        .. note::

            The method modifies layer visibility before export based on the provided labels.
            It saves the current state of the drawing to disk before calling Inkscape
            via a subprocess to perform the rendering.

        """
        import subprocess
        from losalamos.utils import make_local_tempfile

        # handle output file
        # -----------------------------------------------------------------------
        if file_output is None:
            file_output = self.file_data.parent / str(self.file_data.stem + ".png")

        # handle svg file copy
        # -----------------------------------------------------------------------
        src_file = self.file_data
        dst_file = make_local_tempfile(src_file=src_file)
        shutil.copy(src=self.file_data, dst=dst_file)
        self.file_data = dst_file

        # Get abspath
        file_output = Path(file_output).resolve()

        # handle visibility of layers
        # -----------------------------------------------------------------------
        b_save = False

        if hide_layers is not None:
            self.hide_layers(labels=hide_layers)
            b_save = True

        if show_layers is not None:
            self.show_layers(labels=hide_layers, inclusive=show_inclusive)
            b_save = True

        # save to temporary file
        if b_save:
            self.save()

        # set return file
        return_file = file_output

        # build command
        # -----------------------------------------------------------------------
        cmd = [
            "inkscape",
            self.file_data,
            "--export-type=png",
            "--export-dpi={}".format(dpi),
            "--export-filename={}".format(file_output),
        ]

        if crop_id is not None:
            cmd = cmd + ["--export-id={}".format(crop_id)]

        # call inkscape process
        # -----------------------------------------------------------------------
        subprocess.run(cmd)

        # handle jpg conversion
        # -----------------------------------------------------------------------
        if to_jpeg:
            new_name = file_output.stem + ".jpeg"
            new_file = Path(file_output.parent / new_name)

            self.image_to_jpeg(file_input=file_output, file_output=new_file, dpi=dpi)
            if remove_png:
                os.remove(file_output)

            # reset return file
            return_file = new_file

        # restore file data and cleanup
        # -----------------------------------------------------------------------
        self.file_data = src_file
        # print(temp_folder)
        os.remove(dst_file)

        return return_file

    @staticmethod
    def _parse_style(style_str):
        """
        Parse an SVG style string into a dict.
        """
        if not style_str:
            return {}

        return dict(item.split(":", 1) for item in style_str.split(";") if ":" in item)

    @staticmethod
    def _style_to_string(style_dict):
        """
        Serialize a style dict back to a SVG style string.
        """
        return ";".join(f"{k}:{v}" for k, v in style_dict.items())


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

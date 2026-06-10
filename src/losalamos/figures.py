# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
SVG and raster figure handling for export pipelines.

Provides classes for loading, manipulating, and exporting figures
in SVG, PDF, PNG, and JPEG formats using Inkscape as the rendering backend.

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
    """

    Base class for figure objects.

    Extends :class:`~losalamos.root.DataSet` with image utility methods
    for scaling, thumbnail generation, and format conversion.
    """

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
    """
    SVG figure with layer control and multi-format export.

    Loads an Inkscape SVG file and exposes methods to manipulate layer
    visibility and export the drawing to SVG, PDF, PNG, or JPEG via
    Inkscape subprocess calls.

    :param name: Internal object name. Default value = ``MySVG``
    :type name: str
    :param alias: Short display alias. Default value = ``SVG``
    :type alias: str

    .. note::

        All export methods (``to_svg``, ``to_pdf``, ``to_image``) operate
        on a temporary copy of the source file, leaving the original untouched.

    .. warning::

        Requires ``inkscape`` to be installed and available in the system PATH.

    """

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
            for lbl in all_layers:
                if lbl not in labels:
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

    def get_property(self, element, key):
        """
        Get a visual or geometric property from an SVG element.

        Searches the element's ``style`` attribute first, then falls back
        to bare XML attributes.

        :param element: The lxml SVG element to read.
        :type element: etree.Element
        :param key: Property name (e.g. ``'fill'``, ``'width'``, ``'opacity'``).
        :type key: str
        :return: The property value, or ``None`` if not found in either location.
        :rtype: str or None

        .. seealso::

            :meth:`set_property`

        """
        style = self._parse_style(element.get("style", ""))

        if key in style:
            return style[key]

        return element.get(key)

    def get_text(self, element):
        """
        Get the text content of a SVG text element.

        Reads from the first ``<tspan>`` descendant if present,
        since Inkscape stores the actual string there rather than
        directly on the ``<text>`` node. Falls back to the element's
        own text if no tspan is found.

        :param element: The lxml SVG text element to read.
        :type element: etree.Element
        :return: The text content, or an empty string if none is found.
        :rtype: str

        .. seealso::

            :meth:`set_text`

        """
        for child in element.iter():
            if etree.QName(child).localname == "tspan":
                return child.text or ""

        return element.text or ""

    def get_text_lines(self, element):
        """
        Return all text lines from a multi-line SVG text element.

        Each ``<tspan sodipodi:role='line'>`` is treated as one line.

        :param element: The lxml SVG text element to read.
        :type element: etree.Element
        :return: List of strings, one per tspan.
        :rtype: list[str]
        """
        lines = []
        for child in element.iter():
            if etree.QName(child).localname == "tspan":
                lines.append(child.text or "")
        return lines

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

    def set_property(self, element, key, value):
        """
        Set a visual or geometric property on an SVG element.

        Searches for the key in the element's ``style`` attribute first,
        then in bare XML attributes. Writes to whichever location already
        holds the key, falling back to the ``style`` string if the key is
        not found in either. If the key exists in both locations, the bare
        attribute is removed and the ``style`` string is kept as the single
        source of truth.

        :param element: The lxml SVG element to modify.
        :type element: etree.Element
        :param key: Property name (e.g. ``'fill'``, ``'width'``, ``'opacity'``).
        :type key: str
        :param value: New value to assign.
        :type value: str
        :return: None
        :rtype: NoneType

        .. note::

            Mutations are applied in place on the lxml tree. A subsequent
            call to :meth:`save` or :meth:`export` will persist the changes
            to disk.

        .. warning::

            When the same property exists in both the ``style`` string and
            as a bare XML attribute, the bare attribute is silently removed
            to resolve the ambiguity. This normalisation is intentional but
            changes the element structure beyond the requested property.

        """
        style = self._parse_style(element.get("style", ""))
        in_style = key in style
        in_attr = element.get(key) is not None

        if in_style and in_attr:
            # clean up the duplicate — remove bare attr, keep style
            del element.attrib[key]
            in_attr = False

        if in_style:
            style[key] = value
            element.set("style", self._style_to_string(style))
        elif in_attr:
            element.set(key, value)
        else:
            style[key] = value
            element.set("style", self._style_to_string(style))

        return None

    def set_color(self, element, fill=None, stroke=None):
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

    def set_font(self, element, font_family, variant=None):
        """
        Set the font family on a text element and all its ``<tspan>`` descendants.

        Updates both ``font-family`` and ``-inkscape-font-specification`` to
        keep Inkscape's internal font state consistent with the rendered output.
        The method iterates over the element itself and all child nodes, applying
        changes only to ``<text>`` and ``<tspan>`` tags.

        :param element: The lxml SVG text element to modify.
        :type element: etree.Element
        :param font_family: Target font family name (e.g. ``'Arial'``, ``'Georgia'``).
        :type font_family: str
        :param variant: Font variant to apply (e.g. ``'Normal'``, ``'Bold'``, ``'Italic'``).
            If ``None``, the variant is read from the existing
            ``-inkscape-font-specification`` of each node and preserved
            individually, so mixed variants within the same text element
            are handled correctly. Default value = ``None``
        :type variant: str or None
        :return: None
        :rtype: NoneType

        .. note::

            When ``variant`` is ``None`` and no ``-inkscape-font-specification``
            is present on a node, the variant defaults to ``'Normal'``.

        .. seealso::

            :meth:`set_property`, :meth:`_extract_variant`

        """
        for node in [element, *element.iter()]:
            tag = etree.QName(node).localname
            if tag not in ("text", "tspan"):
                continue

            style = self._parse_style(node.get("style", ""))

            if variant is None:
                current_spec = style.get("-inkscape-font-specification", "")
                resolved_variant = self._extract_variant(current_spec)
            else:
                resolved_variant = variant

            self.set_property(node, "font-family", font_family)
            self.set_property(
                node,
                "-inkscape-font-specification",
                f"'{font_family}, {resolved_variant}'",
            )

        return None

    def set_text(self, element, content):
        """
        Set the text content of a SVG text element.

        Writes to the first ``<tspan>`` descendant if present,
        since Inkscape stores the actual string there rather than
        directly on the ``<text>`` node.
        Falls back to writing on the element itself if no tspan is found.

        :param element: The lxml SVG text element to modify.
        :type element: etree.Element
        :param content: The new text string.
        :type content: str
        :return: None
        :rtype: NoneType
        """
        for child in element.iter():
            if etree.QName(child).localname == "tspan":
                child.text = content
                return None

        # fallback: no tspan found
        element.text = content
        return None

    def set_font_layers(self, font_family, variant=None, layers=None):
        """
        Set the font family on all text elements across specified layers.

        Scans every specified layer in the document and applies :meth:`set_font`
        to each ``<text>`` element found, preserving individual node
        variants unless ``variant`` is explicitly provided.

        :param font_family: Target font family name (e.g. ``'Arial'``, ``'Georgia'``).
        :type font_family: str
        :param variant: Font variant to apply (e.g. ``'Normal'``, ``'Bold'``, ``'Italic'``).
            If ``None``, the existing variant of each node is preserved.
            Default value = ``None``
        :type variant: str or None
        :param layers: List of layer labels to process. If ``None``, all layers
            in the document are scanned. Default value = ``None``
        :type layers: list[str] or None
        :return: None
        :rtype: NoneType

        .. seealso::

            :meth:`set_font`, :meth:`get_layers`, :meth:`get_layer_elements`

        """
        all_layers = self.get_layers()

        if layers is None:
            target_layers = all_layers
        else:
            target_layers = {k: v for k, v in all_layers.items() if k in layers}

        for label in target_layers:
            elements = self.get_layer_elements(label, drawable_only=True)
            for el_id, el_data in elements.items():
                if el_data["tag"] == "text":
                    self.set_font(el_data["element"], font_family, variant=variant)

        return None

    def rename_layer(self, label, new_label):
        """
        Rename an Inkscape layer by updating its label attribute.

        :param label: Current label of the layer to rename.
        :type label: str
        :param new_label: New label to assign to the layer.
        :type new_label: str
        :return: None
        :rtype: NoneType

        :raises ValueError: If no layer with the given label is found.

        .. note::

            Only the ``inkscape:label`` attribute is updated. The element
            ``id`` attribute is left unchanged as it may be referenced
            elsewhere in the document.

        .. seealso::

            :meth:`get_layers`, :meth:`get_layers_labels`

        """
        layers = self.get_layers()

        if label not in layers:
            raise ValueError(f"Layer '{label}' not found in document.")

        label_attr = f"{{{self.name_spaces['inkscape']}}}label"
        layers[label].set(label_attr, new_label)

        return None

    def rename_element_id(self, old_id, new_id):
        """
        Rename an element ID and update all references to it within the document.

        Updates the ``id`` attribute on the target element and scans the
        entire SVG tree for cross-references (``clip-path``, ``mask``,
        ``xlink:href``, ``href``) that point to the old ID, replacing them
        with the new one.

        :param old_id: Current ID of the element to rename.
        :type old_id: str
        :param new_id: New ID to assign.
        :type new_id: str
        :return: None
        :rtype: NoneType

        :raises ValueError: If no element with ``old_id`` is found in the document.

        .. note::

            This method is required when changing the target of the ``crop_id``
            parameter in :meth:`to_image`, :meth:`to_pdf`, and :meth:`to_svg`,
            since Inkscape's ``--export-id`` flag resolves elements by their
            ``id`` attribute.

        .. warning::

            ID uniqueness is not enforced by this method. Passing a ``new_id``
            that already exists in the document will produce duplicate IDs,
            which is invalid SVG and may cause undefined behaviour in Inkscape
            and browsers.

        .. seealso::

            :meth:`to_image`, :meth:`to_pdf`, :meth:`to_svg`

        """
        # find the target element
        target = self.data.find(f".//*[@id='{old_id}']")

        if target is None:
            raise ValueError(f"Element with id '{old_id}' not found in document.")

        # rename the element id
        target.set("id", new_id)

        # update all cross-references in the tree
        ref_attrs = {
            "clip-path": f"url(#{old_id})",
            "mask": f"url(#{old_id})",
            "href": f"#{old_id}",
            f"{{{self.name_spaces.get('xlink', 'http://www.w3.org/1999/xlink')}}}href": f"#{old_id}",
        }

        for element in self.data.iter():
            for attr, old_ref in ref_attrs.items():
                if element.get(attr) == old_ref:
                    element.set(attr, old_ref.replace(old_id, new_id))

        return None

    def rename_element_label(self, old_label, new_label, tag=None):
        """
        Rename an element's ``inkscape:label`` attribute within the document.

        Searches the entire SVG tree for the first element whose
        ``inkscape:label`` matches ``old_label`` and updates it to ``new_label``.
        Optionally restricts the search to a specific SVG tag name.

        :param old_label: Current ``inkscape:label`` value to find.
        :type old_label: str
        :param new_label: New label value to assign.
        :type new_label: str
        :param tag: [optional] Local tag name to restrict the search
            (e.g. ``'g'``, ``'rect'``, ``'text'``). If ``None``, all
            element types are searched. Default value = ``None``
        :type tag: str or None
        :return: None
        :rtype: NoneType

        :raises ValueError: If no element with the given ``old_label`` is found.

        .. note::

            Unlike :meth:`rename_layer`, which operates only on top-level layer
            ``<g>`` elements, this method searches the entire document tree and
            works on any element type.

        .. seealso::

            :meth:`rename_layer`, :meth:`rename_element_id`

        """
        label_attr = f"{{{self.name_spaces['inkscape']}}}label"

        for element in self.data.iter():
            if tag is not None and etree.QName(element).localname != tag:
                continue
            if element.get(label_attr) == old_label:
                element.set(label_attr, new_label)
                return None

        raise ValueError(
            f"Element with inkscape:label '{old_label}' not found in document."
        )

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

        # handle page opacity for jpeg render
        # -----------------------------------------------------------------------
        if to_jpeg:
            self.set_page_opacity(opacity=1.0)
            self.save()

        # Get abspath
        file_output = Path(file_output).resolve()

        # handle visibility of layers
        # -----------------------------------------------------------------------
        b_save = False

        if hide_layers is not None:
            self.hide_layers(labels=hide_layers)
            b_save = True

        if show_layers is not None:
            self.show_layers(labels=show_layers, inclusive=show_inclusive)
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

    def to_pdf(
        self,
        file_output=None,
        crop_id=None,
        hide_layers=None,
        show_layers=None,
        show_inclusive=True,
    ):
        """
        Export the current drawing as a PDF file.

        This method uses a two-stage vector export pipeline when ``crop_id``
        is provided:

            original.svg
                -> temporary cropped svg
                -> final pdf

        This approach preserves SVG clipping semantics more reliably than
        direct PDF export from Inkscape.

        :param file_output: [optional] Destination PDF path.
        :type file_output: str or :class:`pathlib.Path`

        :param crop_id: [optional] Object ID used for cropping/export.
        :type crop_id: str

        :param hide_layers: [optional] List of layer labels to hide.
        :type hide_layers: list

        :param show_layers: [optional] List of layer labels to show.
        :type show_layers: list

        :param show_inclusive:
            Whether ``show_layers`` should act inclusively.
        :type show_inclusive: bool

        :return: Path to generated PDF file.
        :rtype: :class:`pathlib.Path`

        .. warning::

            Requires ``inkscape`` available in system PATH.

        """
        import os
        import shutil
        import subprocess

        from pathlib import Path
        from losalamos.utils import make_local_tempfile

        # handle output file
        # -------------------------------------------------------------------------
        if file_output is None:
            file_output = self.file_data.parent / (self.file_data.stem + ".pdf")

        file_output = Path(file_output).resolve()

        # enforce extension
        # -------------------------------------------------------------------------
        if file_output.suffix.lower() != ".pdf":
            file_output = file_output.with_suffix(".pdf")

        # create temporary working copy
        # -------------------------------------------------------------------------
        src_file = self.file_data
        dst_file = make_local_tempfile(src_file=src_file)

        shutil.copy(src=self.file_data, dst=dst_file)

        self.file_data = dst_file

        # handle layer visibility
        # -------------------------------------------------------------------------
        b_save = False

        if hide_layers is not None:
            self.hide_layers(labels=hide_layers)
            b_save = True

        if show_layers is not None:
            self.show_layers(
                labels=show_layers,
                inclusive=show_inclusive,
            )
            b_save = True

        # save temporary document if modified
        # -------------------------------------------------------------------------
        if b_save:
            self.save()

        # -------------------------------------------------------------------------
        # CROPPED VECTOR EXPORT
        # -------------------------------------------------------------------------
        if crop_id is not None:

            temp_svg = make_local_tempfile(src_file=self.file_data.with_suffix(".svg"))

            # stage 1:
            # export cropped standalone svg
            # ---------------------------------------------------------------------
            cmd_svg = [
                "inkscape",
                self.file_data,
                "--export-type=svg",
                f"--export-filename={temp_svg}",
                f"--export-id={crop_id}",
                # "--export-id-only",
            ]

            subprocess.run(cmd_svg, check=True)

            # stage 2:
            # export svg -> pdf
            # ---------------------------------------------------------------------
            cmd_pdf = [
                "inkscape",
                temp_svg,
                "--export-type=pdf",
                "--export-area-page",
                f"--export-filename={file_output}",
            ]

            subprocess.run(cmd_pdf, check=True)

            # cleanup temporary svg
            # ---------------------------------------------------------------------
            if os.path.exists(temp_svg):
                os.remove(temp_svg)

        # -------------------------------------------------------------------------
        # STANDARD FULL-PAGE EXPORT
        # -------------------------------------------------------------------------
        else:

            cmd_pdf = [
                "inkscape",
                self.file_data,
                "--export-type=pdf",
                "--export-area-page",
                f"--export-filename={file_output}",
            ]

            subprocess.run(cmd_pdf, check=True)

        # restore original state
        # -------------------------------------------------------------------------
        self.file_data = src_file

        # cleanup temporary working file
        # -------------------------------------------------------------------------
        if os.path.exists(dst_file):
            os.remove(dst_file)

        return file_output

    def to_svg(
        self,
        file_output=None,
        crop_id=None,
        hide_layers=None,
        show_layers=None,
        show_inclusive=True,
    ):
        """
        Export the current drawing as an SVG file.

        :param file_output: [optional] Destination SVG path. Defaults to the source file name.
        :type file_output: str or :class:`pathlib.Path`
        :param crop_id: [optional] Object ID to crop the export to.
        :type crop_id: str
        :param hide_layers: [optional] List of layer labels to hide before export.
        :type hide_layers: list
        :param show_layers: [optional] List of layer labels to show before export.
        :type show_layers: list
        :param show_inclusive: Whether to show layers inclusively. Default value = ``True``
        :type show_inclusive: bool
        :return: Path to the generated SVG file.
        :rtype: :class:`pathlib.Path`

        :raises FileExistsError: If ``file_output`` resolves to the same path as the source file.

        .. warning::

            This method requires ``inkscape`` to be installed and available in the system PATH.

        """
        import subprocess
        from losalamos.utils import make_local_tempfile

        # handle output file
        # -----------------------------------------------------------------------
        if file_output is None:
            file_output = self.file_data.parent / (self.file_data.stem + ".svg")

        file_output = Path(file_output).resolve()

        if file_output.suffix.lower() != ".svg":
            file_output = file_output.with_suffix(".svg")

        # guard against overwriting the source file
        # -----------------------------------------------------------------------
        if file_output == self.file_data.resolve():
            raise FileExistsError(
                f"file_output resolves to the source file: {file_output}\n"
                f"Provide an explicit destination path to avoid overwriting the master SVG."
            )

        # create temporary working copy
        # -----------------------------------------------------------------------
        src_file = self.file_data
        dst_file = make_local_tempfile(src_file=src_file)
        shutil.copy(src=self.file_data, dst=dst_file)
        self.file_data = dst_file

        # handle layer visibility
        # -----------------------------------------------------------------------
        b_save = False

        if hide_layers is not None:
            self.hide_layers(labels=hide_layers)
            b_save = True

        if show_layers is not None:
            self.show_layers(labels=show_layers, inclusive=show_inclusive)
            b_save = True

        if b_save:
            self.save()

        # build and run inkscape command
        # -----------------------------------------------------------------------
        cmd = [
            "inkscape",
            self.file_data,
            "--export-type=svg",
            f"--export-filename={file_output}",
        ]

        if crop_id is not None:
            cmd.append(f"--export-id={crop_id}")

        subprocess.run(cmd, check=True)

        # restore original state and cleanup
        # -----------------------------------------------------------------------
        self.file_data = src_file

        if os.path.exists(dst_file):
            os.remove(dst_file)

        return file_output

    @staticmethod
    def _extract_variant(spec):
        """
        Extract the variant portion from an inkscape font specification string.

        e.g. "'Arial, Bold'"  -> "Bold"
             "'Arial, Normal'" -> "Normal"
             "" -> "Normal"
        """
        # strip quotes and whitespace
        spec = spec.strip("'\" ")
        if "," in spec:
            return spec.split(",", 1)[1].strip()
        return "Normal"

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

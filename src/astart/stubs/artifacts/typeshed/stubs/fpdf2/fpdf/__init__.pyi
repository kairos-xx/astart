from pathlib import Path

from .enums import Align as Align
from .enums import TextMode as TextMode
from .enums import XPos as XPos
from .enums import YPos as YPos
from .fonts import FontFace as FontFace
from .fonts import TextStyle as TextStyle
from .fpdf import FPDF as FPDF
from .fpdf import FPDFException as FPDFException
from .fpdf import TitleStyle as TitleStyle
from .html import HTML2FPDF as HTML2FPDF
from .html import HTMLMixin as HTMLMixin
from .prefs import ViewerPreferences as ViewerPreferences
from .template import FlexTemplate as FlexTemplate
from .template import Template as Template
from .util import get_scale_factor as get_scale_factor

__license__: str
__version__: str
FPDF_VERSION: str
FPDF_FONT_DIR: Path
__all__ = [
    "FPDF",
    "FPDF_FONT_DIR",
    "FPDF_VERSION",
    "HTML2FPDF",
    "Align",
    "FPDFException",
    "FlexTemplate",
    "FontFace",
    "HTMLMixin",
    "Template",
    "TextMode",
    "TextStyle",
    "TitleStyle",
    "ViewerPreferences",
    "XPos",
    "YPos",
    "__license__",
    "__version__",
    "get_scale_factor",
]

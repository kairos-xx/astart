from tkinter import Frame, Misc, Scrollbar, Text

__all__ = ["ScrolledText"]

class ScrolledText(Text):
    frame: Frame
    vbar: Scrollbar
    def __init__(self, master: Misc | None = None, **kwargs) -> None: ...

from pyexpat import *

class ExpatError(Exception):
    code: int
    lineno: int
    offset: int

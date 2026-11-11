from ctypes import Structure, Union

class BigEndianStructure(Structure):
    __slots__ = ()

class LittleEndianStructure(Structure): ...

class BigEndianUnion(Union):
    __slots__ = ()

class LittleEndianUnion(Union): ...

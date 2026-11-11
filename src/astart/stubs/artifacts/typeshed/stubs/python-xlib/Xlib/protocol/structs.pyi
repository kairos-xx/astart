from collections.abc import Iterable, Sequence

from Xlib.protocol import rq

type _RGB3IntIterable = Iterable[int]
type _Rectangle4IntSequence = Sequence[int]
type _Segment4IntSequence = Sequence[int]
type _Arc6IntSequence = Sequence[int]

def WindowValues(arg: str) -> rq.ValueList: ...
def GCValues(arg: str) -> rq.ValueList: ...

TimeCoord: rq.Struct
Host: rq.Struct
CharInfo: rq.Struct
FontProp: rq.Struct
ColorItem: rq.Struct
RGB: rq.Struct
Point: rq.Struct
Segment: rq.Struct
Rectangle: rq.Struct
Arc: rq.Struct

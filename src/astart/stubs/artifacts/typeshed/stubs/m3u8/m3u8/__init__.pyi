from collections.abc import Callable, Mapping
from typing import Any

from m3u8.httpclient import _HTTPClientProtocol
from m3u8.model import (
    M3U8,
    ContentSteering,
    DateRange,
    DateRangeList,
    IFramePlaylist,
    ImagePlaylist,
    Key,
    Media,
    MediaList,
    PartialSegment,
    PartialSegmentList,
    PartInformation,
    Playlist,
    PlaylistList,
    PreloadHint,
    RenditionReport,
    RenditionReportList,
    Segment,
    SegmentList,
    ServerControl,
    Skip,
    Start,
    Tiles,
)
from m3u8.parser import ParseError, parse

__all__ = (
    "M3U8",
    "ContentSteering",
    "DateRange",
    "DateRangeList",
    "IFramePlaylist",
    "ImagePlaylist",
    "Key",
    "Media",
    "MediaList",
    "ParseError",
    "PartInformation",
    "PartialSegment",
    "PartialSegmentList",
    "Playlist",
    "PlaylistList",
    "PreloadHint",
    "RenditionReport",
    "RenditionReportList",
    "Segment",
    "SegmentList",
    "ServerControl",
    "Skip",
    "Start",
    "Tiles",
    "load",
    "loads",
    "parse",
)
type _CustomTagsParser = Callable[
    [str, int, dict[str, Any], dict[str, Any]],
    object,
]

def loads(
    content: str,
    uri: str | None = None,
    custom_tags_parser: _CustomTagsParser | None = None,
) -> M3U8: ...
def load(
    uri: str,
    timeout: float | None = None,
    headers: Mapping[str, Any] = {},
    custom_tags_parser: _CustomTagsParser | None = None,
    http_client: _HTTPClientProtocol = ...,
    verify_ssl: bool = True,
) -> M3U8: ...

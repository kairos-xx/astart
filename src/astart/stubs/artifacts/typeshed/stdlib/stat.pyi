import sys
from _stat import (
    S_ENFMT as S_ENFMT,
)
from _stat import (
    S_IEXEC as S_IEXEC,
)
from _stat import (
    S_IFBLK as S_IFBLK,
)
from _stat import (
    S_IFCHR as S_IFCHR,
)
from _stat import (
    S_IFDIR as S_IFDIR,
)
from _stat import (
    S_IFDOOR as S_IFDOOR,
)
from _stat import (
    S_IFIFO as S_IFIFO,
)
from _stat import (
    S_IFLNK as S_IFLNK,
)
from _stat import (
    S_IFMT as S_IFMT,
)
from _stat import (
    S_IFPORT as S_IFPORT,
)
from _stat import (
    S_IFREG as S_IFREG,
)
from _stat import (
    S_IFSOCK as S_IFSOCK,
)
from _stat import (
    S_IFWHT as S_IFWHT,
)
from _stat import (
    S_IMODE as S_IMODE,
)
from _stat import (
    S_IREAD as S_IREAD,
)
from _stat import (
    S_IRGRP as S_IRGRP,
)
from _stat import (
    S_IROTH as S_IROTH,
)
from _stat import (
    S_IRUSR as S_IRUSR,
)
from _stat import (
    S_IRWXG as S_IRWXG,
)
from _stat import (
    S_IRWXO as S_IRWXO,
)
from _stat import (
    S_IRWXU as S_IRWXU,
)
from _stat import (
    S_ISBLK as S_ISBLK,
)
from _stat import (
    S_ISCHR as S_ISCHR,
)
from _stat import (
    S_ISDIR as S_ISDIR,
)
from _stat import (
    S_ISDOOR as S_ISDOOR,
)
from _stat import (
    S_ISFIFO as S_ISFIFO,
)
from _stat import (
    S_ISGID as S_ISGID,
)
from _stat import (
    S_ISLNK as S_ISLNK,
)
from _stat import (
    S_ISPORT as S_ISPORT,
)
from _stat import (
    S_ISREG as S_ISREG,
)
from _stat import (
    S_ISSOCK as S_ISSOCK,
)
from _stat import (
    S_ISUID as S_ISUID,
)
from _stat import (
    S_ISVTX as S_ISVTX,
)
from _stat import (
    S_ISWHT as S_ISWHT,
)
from _stat import (
    S_IWGRP as S_IWGRP,
)
from _stat import (
    S_IWOTH as S_IWOTH,
)
from _stat import (
    S_IWRITE as S_IWRITE,
)
from _stat import (
    S_IWUSR as S_IWUSR,
)
from _stat import (
    S_IXGRP as S_IXGRP,
)
from _stat import (
    S_IXOTH as S_IXOTH,
)
from _stat import (
    S_IXUSR as S_IXUSR,
)
from _stat import (
    SF_APPEND as SF_APPEND,
)
from _stat import (
    SF_ARCHIVED as SF_ARCHIVED,
)
from _stat import (
    SF_IMMUTABLE as SF_IMMUTABLE,
)
from _stat import (
    SF_NOUNLINK as SF_NOUNLINK,
)
from _stat import (
    SF_SNAPSHOT as SF_SNAPSHOT,
)
from _stat import (
    ST_ATIME as ST_ATIME,
)
from _stat import (
    ST_CTIME as ST_CTIME,
)
from _stat import (
    ST_DEV as ST_DEV,
)
from _stat import (
    ST_GID as ST_GID,
)
from _stat import (
    ST_INO as ST_INO,
)
from _stat import (
    ST_MODE as ST_MODE,
)
from _stat import (
    ST_MTIME as ST_MTIME,
)
from _stat import (
    ST_NLINK as ST_NLINK,
)
from _stat import (
    ST_SIZE as ST_SIZE,
)
from _stat import (
    ST_UID as ST_UID,
)
from _stat import (
    UF_APPEND as UF_APPEND,
)
from _stat import (
    UF_COMPRESSED as UF_COMPRESSED,
)
from _stat import (
    UF_HIDDEN as UF_HIDDEN,
)
from _stat import (
    UF_IMMUTABLE as UF_IMMUTABLE,
)
from _stat import (
    UF_NODUMP as UF_NODUMP,
)
from _stat import (
    UF_NOUNLINK as UF_NOUNLINK,
)
from _stat import (
    UF_OPAQUE as UF_OPAQUE,
)
from _stat import (
    filemode as filemode,
)
from typing import Final

if sys.platform == "win32":
    from _stat import (
        IO_REPARSE_TAG_APPEXECLINK as IO_REPARSE_TAG_APPEXECLINK,
    )
    from _stat import (
        IO_REPARSE_TAG_MOUNT_POINT as IO_REPARSE_TAG_MOUNT_POINT,
    )
    from _stat import (
        IO_REPARSE_TAG_SYMLINK as IO_REPARSE_TAG_SYMLINK,
    )
from _stat import (
    SF_DATALESS as SF_DATALESS,
)
from _stat import (
    SF_FIRMLINK as SF_FIRMLINK,
)
from _stat import (
    SF_SETTABLE as SF_SETTABLE,
)
from _stat import (
    UF_DATAVAULT as UF_DATAVAULT,
)
from _stat import (
    UF_SETTABLE as UF_SETTABLE,
)
from _stat import (
    UF_TRACKED as UF_TRACKED,
)

if sys.platform == "darwin":
    from _stat import SF_SUPPORTED as SF_SUPPORTED
    from _stat import SF_SYNTHETIC as SF_SYNTHETIC
FILE_ATTRIBUTE_ARCHIVE: Final = 32
FILE_ATTRIBUTE_COMPRESSED: Final = 2048
FILE_ATTRIBUTE_DEVICE: Final = 64
FILE_ATTRIBUTE_DIRECTORY: Final = 16
FILE_ATTRIBUTE_ENCRYPTED: Final = 16384
FILE_ATTRIBUTE_HIDDEN: Final = 2
FILE_ATTRIBUTE_INTEGRITY_STREAM: Final = 32768
FILE_ATTRIBUTE_NORMAL: Final = 128
FILE_ATTRIBUTE_NOT_CONTENT_INDEXED: Final = 8192
FILE_ATTRIBUTE_NO_SCRUB_DATA: Final = 131072
FILE_ATTRIBUTE_OFFLINE: Final = 4096
FILE_ATTRIBUTE_READONLY: Final = 1
FILE_ATTRIBUTE_REPARSE_POINT: Final = 1024
FILE_ATTRIBUTE_SPARSE_FILE: Final = 512
FILE_ATTRIBUTE_SYSTEM: Final = 4
FILE_ATTRIBUTE_TEMPORARY: Final = 256
FILE_ATTRIBUTE_VIRTUAL: Final = 65536
SF_RESTRICTED: Final = 0x00080000
if sys.version_info >= (3, 15):
    STATX_ATTR_COMPRESSED: Final = 0x00000004
    STATX_ATTR_IMMUTABLE: Final = 0x00000010
    STATX_ATTR_APPEND: Final = 0x00000020
    STATX_ATTR_NODUMP: Final = 0x00000040
    STATX_ATTR_ENCRYPTED: Final = 0x00000800
    STATX_ATTR_AUTOMOUNT: Final = 0x00001000
    STATX_ATTR_MOUNT_ROOT: Final = 0x00002000
    STATX_ATTR_VERITY: Final = 0x00100000
    STATX_ATTR_DAX: Final = 0x00200000
    STATX_ATTR_WRITE_ATOMIC: Final = 0x00400000

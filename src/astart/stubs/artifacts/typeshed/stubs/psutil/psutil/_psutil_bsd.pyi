import sys

if (
    sys.platform != "linux"
    and sys.platform != "win32"
    and sys.platform != "darwin"
):
    from collections.abc import Sequence
    from socket import AddressFamily, SocketKind
    from typing import Final, overload

    AF_LINK: Final[int]
    RLIMIT_AS: Final[int]
    RLIMIT_CORE: Final[int]
    RLIMIT_CPU: Final[int]
    RLIMIT_DATA: Final[int]
    RLIMIT_FSIZE: Final[int]
    RLIMIT_MEMLOCK: Final[int]
    RLIMIT_NOFILE: Final[int]
    RLIMIT_NPROC: Final[int]
    RLIMIT_RSS: Final[int]
    RLIMIT_STACK: Final[int]
    RLIMIT_SWAP: Final[int]
    RLIMIT_SBSIZE: Final[int]
    RLIMIT_NPTS: Final[int]
    RLIM_INFINITY: Final[int]
    def getpagesize() -> int: ...
    def net_if_addrs() -> list[
        tuple[str, int, str, str | None, str | None, str | None]
    ]: ...
    def net_if_flags(nic_name: str, /) -> list[str]: ...
    def net_if_is_running(nic_name: str, /) -> bool: ...
    def net_if_mtu(nic_name: str, /) -> int: ...
    def proc_priority_get(pid: int, /) -> int: ...
    def proc_priority_set(pid: int, priority: int, /) -> None: ...
    def net_if_duplex_speed(nic_name: str, /) -> tuple[int, int]: ...
    def proc_is_zombie(pid: int, /) -> bool: ...
    version: Final[int]
    SIDL: Final[int]
    SRUN: Final[int]
    SSLEEP: Final[int]
    SSTOP: Final[int]
    SZOMB: Final[int]
    SWAIT: Final[int]
    SLOCK: Final[int]
    SDEAD: Final[int]
    SONPROC: Final[int]
    SSUSPENDED: Final[int]
    TCPS_CLOSED: Final[int]
    TCPS_CLOSING: Final[int]
    TCPS_CLOSE_WAIT: Final[int]
    TCPS_LISTEN: Final[int]
    TCPS_ESTABLISHED: Final[int]
    TCPS_SYN_SENT: Final[int]
    TCPS_SYN_RECEIVED: Final[int]
    TCPS_FIN_WAIT_1: Final[int]
    TCPS_FIN_WAIT_2: Final[int]
    TCPS_LAST_ACK: Final[int]
    TCPS_TIME_WAIT: Final[int]
    PSUTIL_CONN_NONE: Final = 128
    def proc_cmdline(pid: int, /) -> list[str]: ...
    def proc_cwd(pid: int, /) -> str: ...
    def proc_environ(pid: int, /) -> dict[str, str]: ...
    def proc_name(pid: int, /) -> str: ...
    def proc_num_fds(pid: int, /) -> int: ...
    def proc_oneshot_info(
        pid: int,
        /,
    ) -> tuple[
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        int,
        float,
        int,
        int,
        int,
        int,
        float,
        float,
        float,
        float,
        int,
        int,
        int,
        int,
        int,
        int,
        str,
    ]: ...
    def proc_open_files(pid: int, /) -> list[tuple[str, int]]: ...
    def proc_threads(pid: int, /) -> list[tuple[int, float, float]]: ...
    def proc_num_threads(pid: int, /) -> int: ...
    def proc_cpu_affinity_get(pid: int, /) -> list[int]: ...
    def proc_cpu_affinity_set(pid: int, cpu_set: Sequence[int], /) -> None: ...
    def proc_exe(pid: int, /) -> str: ...
    def proc_getrlimit(pid: int, resource: int, /) -> tuple[int, int]: ...
    def proc_memory_maps(
        pid: int,
        /,
    ) -> list[tuple[str, str, str, int, int, int, int]]: ...
    def proc_net_connections(
        pid: int,
        af_filter: Sequence[AddressFamily | int | None],
        type_filter: Sequence[SocketKind | int | None],
        /,
    ) -> list[
        tuple[int, int, int, tuple[str, int], tuple[str, int] | tuple[()], int]
        | tuple[int, int, int, str, str, int]
    ]: ...
    def proc_setrlimit(
        pid: int,
        resource: int,
        soft: int,
        hard: int,
        /,
    ) -> None: ...
    def boot_time() -> float: ...
    def cpu_count_logical() -> int | None: ...
    def cpu_stats() -> tuple[int, ...]: ...
    def cpu_times() -> tuple[float, float, float, float, float]: ...
    def disk_io_counters() -> dict[str, tuple[int, ...]]: ...
    def disk_partitions() -> list[tuple[str, str, str, str]]: ...
    @overload
    def net_connections(
        af_filter: Sequence[AddressFamily | int | None],
        type_filter: Sequence[SocketKind | int | None],
        /,
    ) -> list[
        tuple[
            int,
            int,
            int,
            tuple[str, int],
            tuple[str, int] | tuple[()],
            int,
            int,
        ]
        | tuple[int, int, int, str, str, int, int]
    ]: ...
    @overload
    def net_connections(
        pid: int,
        af_filter: Sequence[AddressFamily | int | None],
        type_filter: Sequence[SocketKind | int | None],
        /,
    ) -> list[
        tuple[
            int,
            int,
            int,
            tuple[str, int],
            tuple[str, int] | tuple[()],
            int,
            int,
        ]
        | tuple[int, int, int, str, str, int, int]
    ]: ...
    @overload
    def net_connections(
        pid: int,
        kind: str,
        /,
    ) -> list[tuple[int, int, int, str, str, int, int]]: ...
    def net_io_counters() -> dict[
        str,
        tuple[int, int, int, int, int, int, int, int],
    ]: ...
    def per_cpu_times() -> list[tuple[float, float, float, float, float]]: ...
    def pids() -> list[int]: ...
    def swap_mem() -> tuple[int, int, int, int, int]: ...
    def heap_info() -> tuple[int, int]: ...
    def heap_trim() -> None: ...
    def users() -> list[tuple[str, str, str, float, int | None]]: ...
    def virtual_mem() -> tuple[int, ...]: ...
    @overload
    def cpu_freq() -> int: ...
    @overload
    def cpu_freq(core: int, /) -> tuple[int, str]: ...
    def cpu_topology() -> str | None: ...
    def sensors_battery() -> tuple[int, int, int]: ...
    def sensors_cpu_temperature(core: int, /) -> tuple[int, int]: ...
    def check_pid_range(pid: int, /) -> None: ...
    def set_debug(value: bool, /) -> None: ...

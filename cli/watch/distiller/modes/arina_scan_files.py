import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import aiohttp
import h5py
from aiopath import AsyncPath
from cachetools import TTLCache
from config import settings
from schemas import Location, Scan, ScanCreate, ScanUpdate
from utils import create_scan, get_scans, logger, update_scan
from watchdog.events import (
    EVENT_TYPE_CLOSED,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED,
    FileMovedEvent,
    FileSystemEvent,
)

from . import ModeHandler


_ARINA_MASTER_PATTERN = re.compile(r"^.+_master\.h5$")
_ARINA_DATA_PATTERN = re.compile(r"^(.+)_data_[0-9]{6}\.h5$")
_ARINA_SCAN_ID_PATTERN = re.compile(r"^(\d+)_.*(?:_master|_data_\d{6})\.h5$")
_ARINA_FILE_EVENTS = [
    EVENT_TYPE_CREATED,
    EVENT_TYPE_MOVED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_CLOSED,
]

_ARINA_METADATA_DATASETS = {
    "definition": "/entry/definition",
    "beam_center_x": "/entry/instrument/detector/beam_center_x",
    "beam_center_y": "/entry/instrument/detector/beam_center_y",
    "bit_depth_image": "/entry/instrument/detector/bit_depth_image",
    "bit_depth_readout": "/entry/instrument/detector/bit_depth_readout",
    "count_time": "/entry/instrument/detector/count_time",
    "description": "/entry/instrument/detector/description",
    "detector_distance": "/entry/instrument/detector/detector_distance",
    "detector_number": "/entry/instrument/detector/detector_number",
    "detector_readout_time": "/entry/instrument/detector/detector_readout_time",
    "frame_time": "/entry/instrument/detector/frame_time",
    "sensor_material": "/entry/instrument/detector/sensor_material",
    "sensor_thickness": "/entry/instrument/detector/sensor_thickness",
    "threshold_energy": "/entry/instrument/detector/threshold_energy",
    "type": "/entry/instrument/detector/type",
    "x_pixel_size": "/entry/instrument/detector/x_pixel_size",
    "y_pixel_size": "/entry/instrument/detector/y_pixel_size",
    "auto_summation": "/entry/instrument/detector/detectorSpecific/auto_summation",
    "compression": "/entry/instrument/detector/detectorSpecific/compression",
    "data_collection_date": "/entry/instrument/detector/detectorSpecific/data_collection_date",
    "eiger_fw_version": "/entry/instrument/detector/detectorSpecific/eiger_fw_version",
    "frame_count_time": "/entry/instrument/detector/detectorSpecific/frame_count_time",
    "frame_period": "/entry/instrument/detector/detectorSpecific/frame_period",
    "nimages": "/entry/instrument/detector/detectorSpecific/nimages",
    "ntrigger": "/entry/instrument/detector/detectorSpecific/ntrigger",
    "photon_energy": "/entry/instrument/detector/detectorSpecific/photon_energy",
    "roi_mode": "/entry/instrument/detector/detectorSpecific/roi_mode",
    "software_version": "/entry/instrument/detector/detectorSpecific/software_version",
    "trigger_mode": "/entry/instrument/detector/detectorSpecific/trigger_mode",
    "x_pixels_in_detector": "/entry/instrument/detector/detectorSpecific/x_pixels_in_detector",
    "y_pixels_in_detector": "/entry/instrument/detector/detectorSpecific/y_pixels_in_detector",
    "module_data_origin": "/entry/instrument/detector/module/data_origin",
    "module_data_size": "/entry/instrument/detector/module/data_size",
}


@dataclass
class DataFileStatus:
    link_name: str
    path: Path
    dataset_path: str
    readable: bool
    frames: int = 0


@dataclass
class ScanStatus:
    master_path: Path
    expected_frames: Optional[int]
    observed_frames: int
    progress: Optional[float]
    complete: bool
    files: List[DataFileStatus]

    @property
    def locations(self) -> List[Path]:
        return [self.master_path] + [file.path for file in self.files]


def _scalar(dataset):
    value = dataset[()]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        return value.item()

    return value


def _read_optional_scalar(h5: h5py.File, path: str):
    if path not in h5:
        return None

    return _scalar(h5[path])


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if hasattr(value, "item"):
        return _json_safe(value.item())

    return value


def _dataset_metadata(dataset) -> Dict[str, Any]:
    metadata = {"value": _json_safe(dataset[()])}
    units = dataset.attrs.get("units")
    if units is not None:
        metadata["units"] = _json_safe(units)

    return metadata


def _extract_metadata(status: ScanStatus) -> Dict[str, Any]:
    with h5py.File(status.master_path, "r") as master:
        metadata: Dict[str, Any] = {}
        for key, path in _ARINA_METADATA_DATASETS.items():
            try:
                if path in master:
                    metadata[key] = _dataset_metadata(master[path])
            except (OSError, KeyError, RuntimeError, TypeError, ValueError) as exc:
                logger.warning(
                    "Could not extract ARINA metadata dataset %s from %s: %s",
                    path,
                    status.master_path,
                    exc,
                )
        return metadata


def _read_expected_frames(master: h5py.File) -> Optional[int]:
    nimages = _read_optional_scalar(
        master, "/entry/instrument/detector/detectorSpecific/nimages"
    )

    ntrigger = _read_optional_scalar(
        master, "/entry/instrument/detector/detectorSpecific/ntrigger"
    )
    if nimages is None or ntrigger is None:
        return None

    return int(nimages) * int(ntrigger)


def _read_data_file_status(
    master_path: Path, link_name: str, link: h5py.ExternalLink
) -> DataFileStatus:
    target = (master_path.parent / link.filename).resolve()
    status = DataFileStatus(
        link_name=link_name,
        path=target,
        dataset_path=link.path,
        readable=False,
    )
    if not target.exists():
        return status

    try:
        with h5py.File(target, "r") as data_file:
            if link.path in data_file:
                dataset = data_file[link.path]
                status.frames = int(dataset.shape[0])
                status.readable = True
    except (OSError, KeyError, RuntimeError, ValueError) as exc:
        logger.debug("ARINA data file is not readable yet: %s: %s", target, exc)

    return status


def _read_data_file_statuses(
    master_path: Path, master: h5py.File
) -> Optional[List[DataFileStatus]]:
    if "/entry/data" not in master:
        return None

    # ARINA master files point at the chunk files through external links.
    files: List[DataFileStatus] = []
    data_group = master["/entry/data"]
    for link_name in sorted(data_group):
        link = data_group.get(link_name, getlink=True)
        if not isinstance(link, h5py.ExternalLink):
            raise ValueError(
                f"Expected ARINA /entry/data item {link_name} in {master_path} "
                "to be an external link."
            )

        files.append(_read_data_file_status(master_path, link_name, link))

    return files


def _build_scan_status(
    master_path: Path,
    expected_frames: Optional[int],
    files: List[DataFileStatus],
) -> ScanStatus:
    readable_files = [file for file in files if file.readable]
    observed_frames = sum(file.frames for file in readable_files)
    progress = (
        min(observed_frames / expected_frames, 1.0)
        if expected_frames and expected_frames > 0
        else None
    )
    all_files_readable = len(files) > 0 and all(file.readable for file in files)
    complete = bool(
        expected_frames and observed_frames == expected_frames and all_files_readable
    )

    if expected_frames is None:
        logger.debug(
            "Could not read ARINA nimages/ntrigger from %s.",
            master_path,
        )

    if expected_frames is not None and observed_frames > expected_frames:
        raise ValueError(
            f"Observed more ARINA frames than expected by master metadata for "
            f"{master_path}: {observed_frames}/{expected_frames}."
        )

    return ScanStatus(
        master_path=master_path,
        expected_frames=expected_frames,
        observed_frames=observed_frames,
        progress=progress,
        complete=complete,
        files=files,
    )


def _incomplete_scan_status(
    master_path: Path,
    expected_frames: Optional[int] = None,
) -> ScanStatus:
    return ScanStatus(
        master_path=master_path,
        expected_frames=expected_frames,
        observed_frames=0,
        progress=None,
        complete=False,
        files=[],
    )


def _extract_scan_status(master_path: Path) -> ScanStatus:
    master_path = master_path.resolve()

    # Polling can catch files while the detector is still writing them.
    try:
        with h5py.File(master_path, "r") as master:
            expected_frames = _read_expected_frames(master)
            files = _read_data_file_statuses(master_path, master)
            if files is None:
                return _incomplete_scan_status(
                    master_path,
                    expected_frames=expected_frames,
                )
    except (OSError, RuntimeError):
        return _incomplete_scan_status(master_path)

    return _build_scan_status(master_path, expected_frames, files)


def _extract_arina_scan_id(path: Path) -> Optional[int]:
    match = _ARINA_SCAN_ID_PATTERN.search(path.name)
    if match is None:
        return None

    return int(match.group(1))


def _generate_arina_uuid(
    host: str, master_path: Path, created: datetime, microscope_id: int
) -> str:
    key = f"arina:{host}:{master_path.resolve()}:{created.isoformat()}:{microscope_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


async def _create_arina_scan_from_master(
    microscope_id: int,
    host: str,
    session: aiohttp.ClientSession,
    status: ScanStatus,
) -> Scan:
    master_path = status.master_path
    async_master_path = AsyncPath(master_path)
    logger.info(f"Creating ARINA scan from master metadata {master_path}")

    stat_info = await async_master_path.stat()
    created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()
    locations = [Location(host=host, path=str(path)) for path in status.locations]
    scan_id = _extract_arina_scan_id(master_path)
    if scan_id is None:
        raise ValueError(f"Could not extract ARINA scan id from {master_path.name}")

    scan = ScanCreate(
        microscope_id=microscope_id,
        scan_id=scan_id,
        uuid=_generate_arina_uuid(host, master_path, created, microscope_id),
        metadata=_extract_metadata(status),
        created=created,
        locations=locations,
    )

    return await create_scan(session, scan)


class ArinaScanFilesModeHandler(ModeHandler):
    def __init__(self, microscope_id: int, host: str, session: aiohttp.ClientSession):
        super().__init__(microscope_id, host, session)
        self._uploaded = TTLCache(maxsize=100000, ttl=24 * 60 * 60)
        self._scan_ids = TTLCache(maxsize=100000, ttl=24 * 60 * 60)
        self._last_sent_progress = TTLCache(maxsize=100000, ttl=24 * 60 * 60)

    def _master_path_for_event(self, event: FileSystemEvent) -> Optional[Path]:
        event_path = event.src_path
        if event.event_type == EVENT_TYPE_MOVED:
            event_path = cast(FileMovedEvent, event).dest_path

        path = Path(event_path)
        if _ARINA_MASTER_PATTERN.match(path.name):
            return path

        data_match = _ARINA_DATA_PATTERN.match(path.name)
        if data_match:
            return path.parent / f"{data_match.group(1)}_master.h5"

        return None

    def _scan_can_be_published(self, status: ScanStatus) -> bool:
        return (
            status.expected_frames is not None
            and bool(status.files)
            and status.progress is not None
        )

    async def _distiller_scan_id(
        self, key: str, status: ScanStatus
    ) -> Optional[int]:
        distiller_id = self._scan_ids.get(key)
        if distiller_id is not None:
            return distiller_id

        async_master_path = AsyncPath(status.master_path)
        stat_info = await async_master_path.stat()
        created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

        # Use the deterministic UUID to make repeated polling idempotent.
        arina_uuid = _generate_arina_uuid(
            self.host, status.master_path, created, self.microscope_id
        )
        scans = await get_scans(self.session, uuid=arina_uuid)

        if not scans:
            return None

        distiller_id = scans[0].id
        self._scan_ids[key] = distiller_id

        return distiller_id

    async def _create_distiller_scan(self, key: str, status: ScanStatus) -> int:
        scan = await _create_arina_scan_from_master(
            self.microscope_id, self.host, self.session, status
        )
        self._scan_ids[key] = scan.id

        return scan.id

    async def _update_progress(
        self, key: str, distiller_id: int, progress: int, status: ScanStatus
    ):
        if self._last_sent_progress.get(key) == progress:
            return

        locations = [
            Location(host=self.host, path=str(path)) for path in status.locations
        ]

        await update_scan(
            self.session,
            distiller_id,
            ScanUpdate(
                progress=progress,
                locations=locations,
                metadata=_extract_metadata(status),
            ),
        )
        self._last_sent_progress[key] = progress

    async def _create_or_update_scan(self, key: str, status: ScanStatus):
        if not self._scan_can_be_published(status):
            return

        progress = round(cast(float, status.progress) * 100)
        distiller_id = await self._distiller_scan_id(key, status)
        if distiller_id is None:
            distiller_id = await self._create_distiller_scan(key, status)

        await self._update_progress(key, distiller_id, progress, status)

    async def _handle_master(self, master_path: Path):
        key = str(master_path.resolve())
        if key in self._uploaded:
            return

        status = _extract_scan_status(master_path)
        message = "ARINA scan status for %s: complete=%s frames=%s/%s"
        args = (
            master_path,
            status.complete,
            status.observed_frames,
            status.expected_frames,
        )
        if status.progress is not None:
            progress = f"{status.progress:.2%}"
            message = (
                "ARINA scan status for %s: complete=%s progress=%s frames=%s/%s"
            )
            args = (
                master_path,
                status.complete,
                progress,
                status.observed_frames,
                status.expected_frames,
            )
        logger.info(message, *args)

        await self._create_or_update_scan(key, status)
        if status.complete:
            self._uploaded[key] = True

    async def on_event(self, event: FileSystemEvent):
        if event.is_directory or event.event_type not in _ARINA_FILE_EVENTS:
            return

        master_path = self._master_path_for_event(event)
        if master_path is None:
            return

        await self._handle_master(master_path)

    async def sync(self):
        for watch_dir in settings.WATCH_DIRECTORIES:
            async for f in AsyncPath(watch_dir).glob("**/*_master.h5"):
                path = AsyncPath(f)
                resolved_path = Path(str(path)).resolve()
                await self._handle_master(resolved_path)

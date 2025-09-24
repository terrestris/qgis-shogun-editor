from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class LayerType(Enum):
    TILE_WMS = "TileWMS"
    VECTOR_TILE = "VectorTile"
    WFS = "WFS"
    WMS = "WMS"
    WMTS = "WMTS"
    XYZ = "XYZ"


class RevisionType(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class BaseEntity:
    _id: Optional[int] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        return cls(
            _id=data.get('id'),
            created=cls._parse_datetime(data.get('created')),
            modified=cls._parse_datetime(data.get('modified'))
        )

    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

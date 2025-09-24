from dataclasses import dataclass
from typing import Any, Dict, Optional

from .BaseEntity import BaseEntity


@dataclass
class Layer(BaseEntity):
    name: Optional[str] = None
    client_config: Optional[Dict[str, Any]] = None
    source_config: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    layerType: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Layer':
        base = super().from_dict(data)
        return cls(
            _id=base._id,
            created=base.created,
            modified=base.modified,
            name=data.get('name'),
            client_config=data.get('clientConfig'),
            source_config=data.get('sourceConfig'),
            features=data.get('features'),
            layerType=data.get('type')
        )

from dataclasses import dataclass
from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QListWidgetItem

from ..models.BaseEntity import BaseEntity


@dataclass
class Application(BaseEntity):
    name: Optional[str] = None
    state_only: Optional[bool] = None
    client_config: Optional[Dict[str, Any]] = None
    layer_tree: Optional[Dict[str, Any]] = None
    layer_config: Optional[Dict[str, Any]] = None
    tool_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Application':
        base = super().from_dict(data)
        return cls(
            _id=base._id,
            created=base.created,
            modified=base.modified,
            name=data.get('name'),
            state_only=data.get('stateOnly'),
            client_config=data.get('clientConfig'),
            layer_tree=data.get('layerTree'),
            layer_config=data.get('layerConfig'),
            tool_config=data.get('toolConfig')
        )

    def get_qt_list_item(self):
        item = QListWidgetItem(self.name or "Unnamed Application")
        item.application_id = self._id
        return item

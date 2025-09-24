from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MutateLayer:
    name: str
    _type: str
    client_config: Optional[Dict[str, Any]] = None
    source_config: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"name": self.name, "type": self._type}
        if self.client_config is not None:
            data["clientConfig"] = self.client_config
        if self.source_config is not None:
            data["sourceConfig"] = self.source_config
        if self.features is not None:
            data["features"] = self.features
        return data

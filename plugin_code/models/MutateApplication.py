from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MutateApplication:
    name: str
    state_only: Optional[bool] = None
    client_config: Optional[Dict[str, Any]] = None
    layer_tree: Optional[Dict[str, Any]] = None
    layer_config: Optional[Dict[str, Any]] = None
    tool_config: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"name": self.name}
        if self.state_only is not None:
            data["stateOnly"] = self.state_only
        if self.client_config is not None:
            data["clientConfig"] = self.client_config
        if self.layer_tree is not None:
            data["layerTree"] = self.layer_tree
        if self.layer_config is not None:
            data["layerConfig"] = self.layer_config
        if self.tool_config is not None:
            data["toolConfig"] = self.tool_config
        return data

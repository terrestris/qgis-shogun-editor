from typing import List, Optional

from ..models.Layer import Layer
from ..models.MutateLayer import MutateLayer
from .GraphQLClient import GraphQLClient


class LayerService:
    def __init__(self, client: GraphQLClient):
        self.client = client

    def get_all_layers(self) -> List[Layer]:
        query = """
        query {
            allLayers {
                id
                created
                modified
                name
                clientConfig
                sourceConfig
                features
                type
            }
        }
        """
        data = self.client.execute_query(query)
        return [Layer.from_dict(layer) for layer in data.get('allLayers', [])]

    def get_layer_by_id(self, layer_id: int) -> Optional[Layer]:
        query = """
        query GetLayer($id: Int) {
            layerById(id: $id) {
                id
                created
                modified
                name
                clientConfig
                sourceConfig
                features
                type
            }
        }
        """
        data = self.client.execute_query(query, {'id': layer_id})
        layer_data = data.get('layerById')
        return Layer.from_dict(layer_data) if layer_data else None

    def create_layer(self, layer: MutateLayer) -> Layer:
        query = """
        mutation CreateLayer($entity: MutateLayer) {
            createLayer(entity: $entity) {
                id
                created
                modified
                name
                clientConfig
                sourceConfig
                features
                type
            }
        }
        """
        data = self.client.execute_query(query, {'entity': layer.to_dict()})
        return Layer.from_dict(data['createLayer'])

    def update_layer(self, layer_id: int, layer: MutateLayer) -> Layer:
        query = """
        mutation UpdateLayer($id: Int, $entity: MutateLayer) {
            updateLayer(id: $id, entity: $entity) {
                id
                created
                modified
                name
                clientConfig
                sourceConfig
                features
                type
            }
        }
        """
        data = self.client.execute_query(query, {'id': layer_id, 'entity': layer.to_dict()})
        return Layer.from_dict(data['updateLayer'])

    def delete_layer(self, layer_id: int) -> bool:
        query = """
        mutation DeleteLayer($id: Int) {
            deleteLayer(id: $id)
        }
        """
        data = self.client.execute_query(query, {'id': layer_id})
        return data.get('deleteLayer', False)

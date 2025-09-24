import json
from typing import Any, Dict, Optional

import requests

from ..exception.GraphQLException import GraphQLException


class GraphQLClient:
    def __init__(self, endpoint_url: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint_url = endpoint_url
        self.headers = headers or {}
        self.session = requests.Session()

        # TODO: keycloak authentication required
        self.session.headers.update({
            'Content-Type': 'application/json',
            **self.headers
        })

    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        payload = {
            'query': query,
            'variables': variables or {}
        }

        try:
            response = self.session.post(
                self.endpoint_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if 'errors' in data:
                raise GraphQLException(f"GraphQL errors: {data['errors']}")

            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            raise GraphQLException(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise GraphQLException(f"JSON decode error: {str(e)}")

import uuid
from typing import Dict, Optional

class TokenRegistry:
    """
    In-memory registry to store user-provided GitHub tokens securely on the server.
    Avoids exposing the raw token back to the client by utilizing a mapping between
    temporary connection session IDs and tokens.
    """
    def __init__(self):
        self._tokens: Dict[str, str] = {}

    def register(self, token: str) -> str:
        """
        Saves a GitHub token and returns a secure connection ID.
        """
        connection_id = f"conn_{uuid.uuid4().hex}"
        self._tokens[connection_id] = token
        return connection_id

    def get_token(self, connection_id: str) -> Optional[str]:
        """
        Retrieves the GitHub token associated with the connection ID.
        """
        return self._tokens.get(connection_id)

    def clear(self) -> None:
        """
        Clears all stored tokens. Used primarily in test cycles.
        """
        self._tokens.clear()

# Global token registry instance
token_registry = TokenRegistry()

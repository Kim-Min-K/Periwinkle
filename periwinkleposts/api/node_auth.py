from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import base64
from django.conf import settings

class NodeBasicAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return None  # No authentication provided

        try:
            # Decode Basic Auth credentials
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)

            # Compare with settings credentials
            if username == settings.NODE_USERNAME and password == settings.NODE_PASSWORD:
                return (username, None)  # Authentication successful

        except Exception:
            raise AuthenticationFailed("Invalid Basic Auth credentials")

        raise AuthenticationFailed("Invalid username or password")

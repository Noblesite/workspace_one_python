import logging
from typing import Optional

class AWEnvironment:
    def __init__(self, api_url: str, tenant_code: str, parent_og: Optional[str] = None):
        """Sets AirWatch environment variables via direct input."""
        self.logger = logging.getLogger(__name__)

        if not api_url or not tenant_code:
            raise ValueError("Both 'api_url' and 'tenant_code' are required.")

        self.api_url = api_url
        self.tenant_code = tenant_code
        self.parent_og = parent_og

        self.logger.info(f"✅ AWEnvironment configured: {self.api_url}")

import math
import os
import logging
from dotenv import load_dotenv
from workspace_one_python.auth.workspace_one_auth import WorkspaceOneAuth
from workspace_one_python.environment.aw_environment import AWEnvironment
from workspace_one_python.mdm.mdm import MDM

class DeviceExtensiveSearch:
    def __init__(self, environment: str):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG,  # or INFO depending on how much noise you want
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        load_dotenv(override=True)

        api_url = os.getenv("CN00_API_URL")
        tenant_code = os.getenv("CN00_TENANT_CODE")
        parent_og_id = os.getenv("CN00_PARENT_OG_ID")  # Optional

        if not api_url or not tenant_code:
            raise ValueError("❌ Missing required API_URL or TENANT_CODE in .env")

        self.aw_environment = AWEnvironment(
            api_url=api_url,
            tenant_code=tenant_code,
            parent_og=parent_og_id,
        )

        cert_path = os.getenv("CN00_CERT_PATH")
        cert_pw = os.getenv("CN00_CERT_PW")

        if not cert_path or not cert_pw:
            raise ValueError("❌ Missing required CERT_PATH or CERT_PW in .env")

        self.auth = WorkspaceOneAuth(
            cert_path=cert_path,
            cert_pw=cert_pw,
            logger=self.logger,
        )

        self.mdm = MDM(aw_environment=self.aw_environment, workspaceOneAuth=self.auth)

    def get_device_extensive_search(self, device_serial_number: str = None, device_id: int = None):
        """
        Searches for a device using either a serial number or a device ID.
        Returns structured JSON output.
        """
        try:
            # ✅ Validate input
            if not device_serial_number and not device_id:
                self.logger.error("❌ No valid parameters provided. Must specify either device_serial_number or device_id.")
                return {"error": "No valid parameters provided. Please provide a serial number or device ID."}

            # ✅ Perform search based on input type
            if device_serial_number:
                response = self.mdm.extensive_search_device_details(
                    device_identifier=device_serial_number, search_type="serialNumber"
                )
            elif device_id:
                response = self.mdm.extensive_search_device_details(
                    device_identifier=device_id, search_type="deviceId"
                )

            return response  # ✅ Ensures JSON-compatible output

        except Exception as e:
            self.logger.error(f"❌ Device lookup failed: {str(e)}")
            return {"error": str(e)}
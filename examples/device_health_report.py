import math
import os
import logging
from dotenv import load_dotenv
from workspace_one_python.auth.workspace_one_auth import WorkspaceOneAuth
from workspace_one_python.environment.aw_environment import AWEnvironment
from workspace_one_python.mdm.mdm import MDM


class DeviceHealthReportTracker:
    def __init__(self, organization_group_id: int, page_size: int):
        
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG,  # or INFO depending on how much noise you want
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.page_counter = 0

        try:
            self.make_next_call = True
            self.error_message = []
            self.page_counter = 0
            self.total_devices = 0
            self.max_amount_of_pages = 0
            self.success = False
            self.organization_group_id = organization_group_id
            self.page_size = page_size
        except Exception as e:
            self.logger.error(f"DeviceHealthReportTracker initialization error: {e}")
            self.error_message.append("DeviceHealthReportCaller issues mapping values")

        self.set_success()

    def set_success(self):
        self.success = not bool(self.error_message)

    def set_max_amount_of_pages(self, total_devices, page_size):
        """Calculates and sets the maximum number of pages correctly."""
        self.max_amount_of_pages = math.ceil(total_devices / page_size)

    def increment_page(self):
        """Increments the page counter safely."""
        if self.page_counter < self.max_amount_of_pages:
            self.page_counter += 1
            self.make_next_call = True
        else:
            self.make_next_call = False

    def get_organization_group_id(self):
        return self.organization_group_id

    def get_page_size(self):
        return self.page_size

    def get_make_next_call(self):
        return self.make_next_call
    
    def get_page_counter(self):
        return self.page_counter


class DeviceHealthReport:
    def __init__(self):

        load_dotenv(override=True)
        self.logger = logging.getLogger(__name__)

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

        self.page_size = 5000  # Correct as int

    def run_airwatch_device_health_check(self, organization_group_id: int):
        """Fetch all pages of device health data and return the full dataset."""
        self.device_health_check_tracker = DeviceHealthReportTracker(
            organization_group_id=organization_group_id,
            page_size=self.page_size
        )

        org_id = self.device_health_check_tracker.get_organization_group_id()
        all_device_data = []  # ✅ Store paged responses

        try:
            # Get the total count of devices to determine pagination
            request = self.mdm.get_device_health_check(org_id, 1, 0)
            total_devices = request.get("Total", 0)
            self.device_health_check_tracker.set_max_amount_of_pages(
                total_devices,
                self.device_health_check_tracker.get_page_size()
            )
        except Exception as e:
            self.logger.error(f"Failed to get initial device count: {e}")
            return []

        while self.device_health_check_tracker.get_make_next_call():
            try:
                # Fetch a page of results
                api_response = self.mdm.get_device_health_check(
                    org_id,
                    self.device_health_check_tracker.get_page_size(),
                    self.device_health_check_tracker.get_page_counter()
                )
                
                # ✅ Append response data
                all_device_data.extend(api_response.get("Devices", []))  

                # ✅ Increment page count
                self.device_health_check_tracker.increment_page()
            except Exception as e:
                self.logger.error(f"API call failed: {e}")
                all_device_data = [e];
                break

        return all_device_data  # ✅ Return all collected pages as a list


if __name__ == "__main__":

    device_health_report = DeviceHealthReport()

    all_devices = device_health_report.run_airwatch_device_health_check(device_health_report.aw_environment.parent_og)
    print(all_devices)
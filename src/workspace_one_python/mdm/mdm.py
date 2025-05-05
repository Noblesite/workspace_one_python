import json
from typing import Union
import requests
from typing import List, Dict
from dataclasses import dataclass
from workspace_one_python.auth.workspace_one_auth import WorkspaceOneAuth
from workspace_one_python.environment.aw_environment import AWEnvironment
from workspace_one_python.exceptions.api_request_error import APIRequestError
import logging

class MDM:
    def __init__(self, aw_environment: AWEnvironment, workspaceOneAuth: WorkspaceOneAuth):
        """Initializes API connection details for AirWatch
        
            Example:

            self.aw_environment = AWEnvironment(
                api_url=api_url,
                tenant_code=tenant_code,
                parent_og=parent_og_id,
            )
                
            self.auth = WorkspaceOneAuth(
                cert_path=cert_path,
                cert_pw=cert_pw,
                logger=self.logger,
            )

            self.mdm = MDM(environment=self.aw_environment, auth=self.auth)
            
        """

        self.aw_environment = aw_environment
        self.auth = workspaceOneAuth
        self.logger = logging.getLogger(__name__)

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Generate headers required for API requests, including authentication."""
        authorization = self.auth.get_cmsurl_header(url)
        return {
            "Authorization":authorization,
            "aw-tenant-code":self.aw_environment.tenant_code,
            "Content-Type":"application/json"
        }

    def _send_request(self, method: str, url: str, data: Dict = None) -> Dict:
        headers = self._get_headers(url)
        self.logger.info(f"📤 method: {method} request to {url}")
        if data is not None:
            self.logger.debug(f"📝 Payload: {data}")
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=90)
            self.logger.debug(f"📥 Response: {response.text}")
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))

    def create_smart_group(self, smart_group_name: str, user_group: str, managed_by_og_id: int) -> Dict:
        """Creates a new smart group."""
        url = f"{self.aw_environment.api_url}/mdm/smartgroups"
        payload = {
            "Name": smart_group_name,
            "ManagedByOrganizationGroupId": managed_by_og_id,
            "UserGroups": [{"Id": user_group}]
        }
        return self._send_request("POST", url, payload)

    def update_product_details(self, product_id: int, smart_group: str) -> Dict:
        """Assigns a product to a smart group."""
        url = f"{self.aw_environment.api_url}/mdm/products/{product_id}/update"
        payload = {"SmartGroups": {"SmartGroupID": smart_group}}
        return self._send_request("POST", url, payload)

    def retrieve_device_information(self, serial_number: str) -> Dict:
        """Retrieves device information by serial number."""
        url = f"{self.aw_environment.api_url}/mdm/devices/serialnumber/{serial_number}"
        return self._send_request("GET", url)

    def extensive_search_device_details(self, device_identifier: Union[str, int], search_type: str) -> Dict:
        """Performs an extensive search for a device."""
        url = f"{self.aw_environment.api_url}/mdm/devices/extensivesearch?{search_type}={device_identifier}"
        return self._send_request("GET", url)

    def initiate_reprocessing_of_product(self, device_ids: List[str], product_id: int) -> Dict:
        """Initiates reprocessing of a product for given device IDs."""
        url = f"{self.aw_environment.api_url}/mdm/products/reprocessProduct"
        payload = {
            "ForceFlag": True,
            "DeviceIds": [{"ID": device_id} for device_id in device_ids],
            "ProductID": product_id
        }
        return self._send_request("POST", url, payload)

    def get_device_health_check(self, organization_group_id: int, page_size: int, page: int) -> Dict:
        """Retrieves device health check details."""
        url = f"{self.aw_environment.api_url}/mdm/products/devicehealthcheck?organizationgroupid={organization_group_id}&page={page}&pagesize={page_size}"
        return self._send_request("GET", url)

    def delete_device_by_id(self, device_id: str) -> Dict:
        """Deletes a device by ID."""
        url = f"{self.aw_environment.api_url}/mdm/devices/{device_id}"
        return self._send_request("DELETE", url)

    def update_device_by_id(self, device_id: str, device_details: Dict) -> Dict:
        """Updates device details."""
        url = f"{self.aw_environment.api_url}/mdm/devices/{device_id}"
        return self._send_request("PUT", url, device_details)

    def change_organization_group(self, serial_number: str, org_id: int) -> Dict:
        """Changes the organization group of a device."""
        url = f"{self.aw_environment.api_url}/mdm/devices/commands/changeorganizationgroup?searchby=Serialnumber&id={serial_number}&ogid={org_id}"
        return self._send_request("POST", url)

    def add_devices_to_tag(self, tag_id: int, devices: List[str]) -> Dict:
        """Adds devices to a tag."""
        url = f"{self.aw_environment.api_url}/mdm/tags/{tag_id}/adddevices"
        payload = {"BulkValues": {"Value": devices}}
        return self._send_request("POST", url, payload)

    def remove_devices_from_tag(self, tag_id: int, devices: List[str]) -> Dict:
        """Removes devices from a tag."""
        url = f"{self.aw_environment.api_url}/mdm/tags/{tag_id}/removedevices"
        payload = {"BulkValues": {"Value": devices}}
        return self._send_request("POST", url, payload)

    def clear_device_passcode(self, device_id: str) -> Dict:
        """Clears a device passcode."""
        url = f"{self.aw_environment.api_url}/mdm/devices/{device_id}/commands?command=ClearPasscode"
        return self._send_request("POST", url)

    def command_device_wipe(self, device_id: str) -> Dict:
        """Initiates a device wipe."""
        url = f"{self.aw_environment.api_url}/mdm/devices/{device_id}/commands?command=DeviceWipe"
        return self._send_request("POST", url)

    def get_device_network_info(self, device_id: str) -> Dict:
        """Retrieves network info of a device."""
        url = f"{self.aw_environment.api_url}/mdm/devices/{device_id}/network"
        return self._send_request("GET", url)

    def get_smart_group_by_id(self, smart_group_id: int) -> Dict:
        """Retrieves a smart group by ID."""
        url = f"{self.aw_environment.api_url}/mdm/smartgroups/{smart_group_id}"
        return self._send_request("GET", url)

    def update_smart_group(self, smart_group_id: int, payload: Dict) -> Dict:
        """Updates a smart group."""
        url = f"{self.aw_environment.api_url}/mdm/smartgroups/{smart_group_id}"
        return self._send_request("PUT", url, payload)

    def install_profile(self, serial_number: str, profile_id: int) -> Dict:
        """Installs a profile on a device."""
        url = f"{self.aw_environment.api_url}/mdm/profiles/{profile_id}/install"
        payload = {"SerialNumber": serial_number}
        return self._send_request("POST", url, payload)

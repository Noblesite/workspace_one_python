import json
import requests
from typing import List, Dict, Optional
import logging

from workspace_one_python.auth.workspace_one_auth import WorkspaceOneAuth
from workspace_one_python.environment.aw_environment import AWEnvironment
from workspace_one_python.exceptions.api_request_error import APIRequestError

class MAM:
    def __init__(self, aw_environment: AWEnvironment, workspaceOneAuth: WorkspaceOneAuth):
        self.aw_environment = aw_environment
        self.auth = workspaceOneAuth
        self.logger = logging.getLogger(__name__)
        
        # ✅ Fetch required values from AWEnviroment
        self.api_url = self.aw_environment.api_url
        self.tenant_code = self.aw_environment.tenant_code

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Generate headers required for API requests, including authentication."""
        authorization = self.auth.get_cmsurl_header(url)
        return {
            "Authorization": authorization,
            "aw-tenant-code": self.tenant_code,
            "Content-Type": "application/json"
        }

    def _send_request(self, method: str, url: str, json_data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """Helper function to make API requests with error handling and retries."""
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending {method} request to {url}")
        if json_data:
            self.logger.debug(f"📝 Payload: {json_data}")

        try:
            response = requests.request(method, url, headers=headers, json=json_data, files=files, timeout=90)
            response.raise_for_status()  # Raise HTTPError for bad responses
            
            self.logger.info(f"📤 {method} request to {url} with status {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}

        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(str(e)) from e

    def upload_blob(self, filename: str, apk_file_path: str, og_id: str) -> Dict:
        """Uploads an APK file as a blob to Workspace ONE."""
        url = f"{self.api_url}/mam/blobs/uploadblob?filename={filename}&organizationgroupid={og_id}&moduleType=Application"

        with open(apk_file_path, "rb") as file:
            files = {"file": file}

        return self._send_request("POST", url, files=files)

    def install_blob(self, blob_value: str, app_name: str, deploy: str, auto_update_version: bool, og_id: str) -> Dict:
        """Installs an uploaded blob as an internal app."""
        url = f"{self.api_url}/mam/apps/internal/begininstall"
        payload = {
            "DeviceType": 5,
            "BlobId": blob_value,
            "ApplicationName": app_name,
            "EnableProvisioning": False,
            "SupportedModels": {"Model": [{"ModelId": 5, "ModelName": "Android"}]},
            "PushMode": deploy,
            "AutoUpdateVersion": auto_update_version,
            "LocationGroupID": og_id,
        }
        return self._send_request("POST", url, json_data=payload)

    def assign_int_app_to_sg(self, app_id: str, smart_groups: List[str], effective_date: str) -> Dict:
        """Assigns an internal app to specified smart groups."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}/assignments"
        payload = {
            "DeploymentParameters": {
                "EffectiveDate": effective_date,
                "PushMode": "Auto",
                "RemoveOnUnEnroll": True,
            },
            "SmartGroupIds": smart_groups,
        }
        return self._send_request("POST", url, json_data=payload)

    def delete_application_assignment_to_sg(self, app_id: str, smart_group_ids: List[str]) -> Dict:
        """Removes all smart groups from an internal app."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}/assignments"
        payload = {"SmartGroupIDs": smart_group_ids, "id": app_id}
        return self._send_request("DELETE", url, json_data=payload)

    def get_internal_app_details(self, app_id: str) -> Dict:
        """Retrieves details of an internal app by ID."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}"
        return self._send_request("GET", url)

    def retire_internal_application(self, app_id: str) -> Dict:
        """Retires an internal application."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}/retire"
        return self._send_request("POST", url)

    def edit_assignments_for_internal_app(self, app_id: str, smart_groups: List[str]) -> Dict:
        """Edits smart group assignments for an internal app."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}/assignments"
        payload = {
            "DeploymentParameters": {
                "AdaptiveManagement": True,
                "ApplicationBackup": False,
                "AutoUpdateDevicesWithPreviousVersion": True,
                "PushMode": "Auto",
                "RemoveOnUnEnroll": True,
                "AllowManagement": True,
                "Rank": 0,
            },
            "SmartGroupIds": smart_groups,
        }
        return self._send_request("PUT", url, json_data=payload)

    def update_sg_assignments_with_internal_app(self, app_id: str, smart_groups: List[str], remove_sg: List[str]) -> Dict:
        """Updates smart group assignments, including removals, for an internal app."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}/assignments"
        payload = {
            "DeploymentParameters": {
                "AdaptiveManagement": True,
                "ApplicationBackup": False,
                "AutoUpdateDevicesWithPreviousVersion": True,
                "PushMode": "Auto",
                "RemoveOnUnEnroll": True,
                "AllowManagement": True,
                "Rank": 0,
            },
            "SmartGroupIds": smart_groups,
            "SmartGroupIdsForDeletion": remove_sg,
        }
        return self._send_request("PUT", url, json_data=payload)

    def search_application_by_bundle_id(self, bundle_id: str) -> Dict:
        """Searches for an application using its bundle ID."""
        url = f"{self.api_url}/mam/apps/search?bundleid={bundle_id}"
        return self._send_request("GET", url)

    def delete_application_by_app_id(self, app_id: str) -> Dict:
        """Deletes an internal application by its App ID."""
        url = f"{self.api_url}/mam/apps/internal/{app_id}"
        return self._send_request("DELETE", url)
    
    def import_approved_android_app(self, uuid: str, application_id: str, device_type: str) -> Dict:
        url = f"{self.api_url}/groups/{uuid}/androidwork/apps/import"
        payload = {
            "applicationId": application_id,
            "deviceType": device_type
        }
        return self._send_request("POST", url, json_data=payload)
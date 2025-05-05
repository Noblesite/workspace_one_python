    
import requests
import json
from datetime import date
from typing import List, Dict, Optional
from dataclasses import dataclass
from workspace_one_python.auth.workspace_one_auth import WorkspaceOneAuth
from workspace_one_python.environment.aw_environment import AWEnvironment
from workspace_one_python.exceptions.api_request_error import APIRequestError
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class System:
    def __init__(self, awEnviroment: AWEnvironment, workspaceOneAuth: WorkspaceOneAuth ):
        self.aw_environment = awEnviroment
        self.auth = workspaceOneAuth
        self.logger = logging.getLogger(__name__)
        
        # ✅ Fetch required values from AWEnviroment
        self.api_url = self.aw_environment.api_url
        self.tenant_code = self.aw_environment.tenant_code
        self.environment = self.aw_environment.environment  # ✅ Fixed missing reference
        
        # ✅ Session with automatic retries for transient failures
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Generate headers required for API requests, including authentication."""
        authorization = self.auth.get_cmsurl_header(url)
        return {
            "Authorization": authorization,
            "aw-tenant-code": self.tenant_code,
            "Content-Type": "application/json"
        }

    def _send_request(self, method: str, url: str, json_data: Optional[Dict] = None) -> Dict:
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending {method} request to {url}")
        if json_data is not None:
            self.logger.debug(f"📝 Payload: {json_data}")

        try:
            response = self.session.request(method, url, headers=headers, json=json_data, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 {method} request to {url} with status {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}

        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))

    def search_custom_user_group(self, name: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/custom/search?groupname={name}"
        return self._send_request("GET", url)

    def create_custom_user_group(self, group_name: str, organization_group: str, description: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/createcustomusergroup"
        payload = {
            "GroupName": group_name,
            "Description": description,
            "ManagedByOrganizationGroupID": organization_group
        }
        return self._send_request("POST", url, json_data=payload)

    def retrieve_list_of_users_from_group(self, user_group_id: str, page_size: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/{user_group_id}/users?pagesize={page_size}"
        return self._send_request("GET", url)

    def search_for_enrollment_user(self, username: str) -> Dict:
        url = f"{self.api_url}/system/users/search?username={username}"
        return self._send_request("GET", url)

    def register_device_to_enrollment_user(self, user_id: str, friendly_name: str, location_group_id: str, ownership: str, message_type: str, message_id: int) -> Dict:
        url = f"{self.api_url}/system/users/{user_id}/registerdevice"
       
        payload = {
            "LocationGroupId": location_group_id,
            "FriendlyName": friendly_name,
            "Ownership": ownership,
            "PlatformId": 2,
            "ModelId": 3,
            "OperatingSystemId": 4,
            "Udid": "ea856771ba6277bfca16528a79c5ce1f",
            "SerialNumber": "RZ1G124JZ6W",
            "Imei": "351822059334112",
            "AssetNumber": "ea856771ba6277bfca16528a79c5ce1f",
            "MessageType": message_type,
            "MessageTemplateId": message_id,
            "SIM": "Sim Details",
            "ToEmailAddress": "noreply@vmware.com",
            "ToPhoneNumber": "4044787500",
            "Tags": [{"Name": "Text value"}],
            "CustomAttributes": [{"uuid": "7a0bf9ca-8116-4f1d-b8d6-5f9dc8c1ba0a"}],
            "IsMigration": True,
            "uuid": "95ecfcb5-82cd-44db-bb3b-56d4137d8adc"
        }
        return self._send_request("POST", url, json_data=payload)

    def create_new_enrollment_user(self, username: str, status: bool, security_type: int, message_type: str, role: str, og_id: str) -> Dict:
        url = f"{self.api_url}/system/users/adduser"
        payload = {
            "UserName": username,
            "Status": status,
            "SecurityType": security_type,
            "MessageType": message_type,
            "Role": role,
            "LocationGroupId": og_id
        }
        return self._send_request("POST", url, json_data=payload)

    def delete_custom_user_group(self, user_group_id: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/{user_group_id}/delete"
        return self._send_request("DELETE", url)

    def get_all_ogs_under_parent_og(self, org_id: str) -> Dict:
        url = f"{self.api_url}/system/groups/{org_id}/children"
        return self._send_request("GET", url)

    def add_user_to_custom_group(self, user_group: str, user_id: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/{user_group}/user/{user_id}/addusertogroup"
        return self._send_request("POST", url)

    def remove_user_from_custom_group(self, user_group: str, user_id: str) -> Dict:
        url = f"{self.api_url}/system/usergroups/{user_group}/user/{user_id}/removeuserfromgroup"
        return self._send_request("POST", url)

    def get_enrollment_user_by_uuid(self, uuid: str) -> Dict:
        url = f"{self.api_url}/system/users/{uuid}"
        return self._send_request("GET", url)

    def get_organization_group_info(self, org_id: str) -> Dict:
        url = f"{self.api_url}/system/groups/{org_id}"
        return self._send_request("GET", url)

    def create_new_organization_group(self, organization_group_name: str, organization_group_id: str, parent_og_id: str, country: str, locale: str, add_default_location: str, enable_rest_api_access: bool ) -> Dict:
        url = f"{self.api_url}/system/groups/{parent_og_id}"
        payload = {
            "Name": organization_group_name,
            "GroupId": organization_group_id,
            "LocationGroupType": "Container",
            "Country": country,
            "Locale": locale,
            "AddDefaultLocation": add_default_location,
            "EnableRestApiAccess": enable_rest_api_access
        }
        return self._send_request("POST", url, json_data=payload)
    
    def delete_event_notification_rule(self, notification_id: str) -> Dict:
        """
        ❌ DELETE /system/eventnotifications/V1/eventnotifications/:id
        Deletes an Event Notification Rule identified by its ID.

        :param notification_id: ID of the Event Notification Rule to delete
        :return: Empty dict if successful
        """
        url = f"{self.api_url}/system/eventnotifications/V1/eventnotifications/{notification_id}"
        return self._send_request("DELETE", url)
    
    def search_event_notifications(self, targetname: Optional[str] = None, organizationgroupid: Optional[str] = None,
                                   status: Optional[str] = None, orderby: Optional[str] = None,
                                   sortorder: Optional[str] = None, page: Optional[int] = None,
                                   pagesize: Optional[int] = None) -> Dict:
        """
        🔍 GET /system/eventnotifications/V1/eventnotifications/search
        Searches Event Notifications using optional filters.

        :param targetname: Target Name to filter
        :param organizationgroupid: Organization Group Identifier
        :param status: Status of the event notification [Active, Inactive]
        :param orderby: Attribute to sort by [TargetName, TargetUrl, FormatType, UserName, Active]
        :param sortorder: Sort order (ASC or DESC)
        :param page: Page number
        :param pagesize: Number of records per page
        :return: Dict containing search results
        """
        url = f"{self.api_url}/system/eventnotifications/V1/eventnotifications/search"
        params = {
            "targetname": targetname,
            "organizationgroupid": organizationgroupid,
            "status": status,
            "orderby": orderby,
            "sortorder": sortorder,
            "page": page,
            "pagesize": pagesize
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))

    def get_admin_identity(self, username: str, password: str, tenant_uuid: str) -> Dict:
        """
        🔐 POST /system/idp/admin
        Provides identity required to create a token for basic and directory admin users.

        :param username: Admin username
        :param password: Admin password
        :param tenant_uuid: UUID of the tenant
        :return: Dict containing administrator UUID
        """
        url = f"{self.api_url}/system/idp/admin"
        payload = {
            "username": username,
            "password": password,
            "tenant_uuid": tenant_uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def search_admins(self, firstname: Optional[str] = None, lastname: Optional[str] = None, email: Optional[str] = None, organizationgroupid: Optional[str] = None, role: Optional[str] = None,username: Optional[str] = None, orderby: Optional[str] = None, page: Optional[int] = None, pagesize: Optional[int] = None, sortorder: Optional[str] = None, status: Optional[str] = None) -> Dict:
        """
        🔍 GET /system/admins/search
        Searches for Admin users using the query information provided.

        Optional filters include: firstname, lastname, email, organizationgroupid, role, username, orderby, page, pagesize, sortorder, and status.

        :return: Dict containing matching admin user records
        """
        params = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "organizationgroupid": organizationgroupid,
            "role": role,
            "username": username,
            "orderby": orderby,
            "page": page,
            "pagesize": pagesize,
            "sortorder": sortorder,
            "status": status
        }

        # Remove any None values to avoid sending empty keys
        filtered_params = {k: v for k, v in params.items() if v is not None}

        url = f"{self.api_url}/system/admins/search"
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    
    def get_admin_by_id(self, admin_id: str) -> Dict:
        """
        🔍 GET /system/admins/:id
        Retrieves information about the specified admin user.

        :param admin_id: ID of the admin user
        :return: Dict containing admin user details
        """
        url = f"{self.api_url}/system/admins/{admin_id}"
        return self._send_request("GET", url)
    
    def delete_admin_by_id(self, admin_id: str) -> Dict:
        """
        ❌ DELETE /system/admins/:id/delete
        Deletes the specified admin user.

        :param admin_id: ID of the admin user to delete
        :return: Empty dict if successful
        """
        url = f"{self.api_url}/system/admins/{admin_id}/delete"
        return self._send_request("DELETE", url)

    def create_admin_user(self, username: str, password: str, first_name: str, last_name: str, email: str, location_group: str, location_group_id: str, organization_group_uuid: str, time_zone: str, time_zone_identifier: str, locale: str, initial_landing_page: str, last_login_timestamp: str, roles: List[Dict], is_active_directory_user: bool, requires_password_change: bool, message_type: int, message_template_id: int, external_id: str, id_value: int, uuid: str) -> Dict:
        """
        ➕ POST /system/admins/addadminuser
        Creates a new admin user with provided attributes.
        """
        url = f"{self.api_url}/system/admins/addadminuser"
        payload = {
            "UserName": username,
            "Password": password,
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "LocationGroup": location_group,
            "LocationGroupId": location_group_id,
            "OrganizationGroupUuid": organization_group_uuid,
            "TimeZone": time_zone,
            "TimeZoneIdentifier": time_zone_identifier,
            "Locale": locale,
            "InitialLandingPage": initial_landing_page,
            "LastLoginTimeStamp": last_login_timestamp,
            "Roles": roles,
            "IsActiveDirectoryUser": is_active_directory_user,
            "RequiresPasswordChange": requires_password_change,
            "MessageType": message_type,
            "MessageTemplateId": message_template_id,
            "ExternalId": external_id,
            "Id": { "Value": id_value },
            "Uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def update_admin_user(self, admin_id: str, username: str, password: str, first_name: str, last_name: str, email: str, location_group: str, location_group_id: str, organization_group_uuid: str, time_zone: str, time_zone_identifier: str, locale: str, initial_landing_page: str, last_login_timestamp: str, roles: List[Dict], is_active_directory_user: bool, requires_password_change: bool, message_type: int, message_template_id: int, external_id: str, id_value: int, uuid: str) -> Dict:
        """
        ✏️ POST /system/admins/:id/update
        Updates the specified admin user.

        :param admin_id: ID of the admin user to update
        :return: Dict with result of update operation
        """
        url = f"{self.api_url}/system/admins/{admin_id}/update"
        payload = {
            "UserName": username,
            "Password": password,
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "LocationGroup": location_group,
            "LocationGroupId": location_group_id,
            "OrganizationGroupUuid": organization_group_uuid,
            "TimeZone": time_zone,
            "TimeZoneIdentifier": time_zone_identifier,
            "Locale": locale,
            "InitialLandingPage": initial_landing_page,
            "LastLoginTimeStamp": last_login_timestamp,
            "Roles": roles,
            "IsActiveDirectoryUser": is_active_directory_user,
            "RequiresPasswordChange": requires_password_change,
            "MessageType": message_type,
            "MessageTemplateId": message_template_id,
            "ExternalId": external_id,
            "Id": { "Value": id_value },
            "Uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def change_admin_password(self, admin_id: str, password: str, organization_group_uuid: str, time_zone_identifier: str, last_login_timestamp: str, is_active_directory_user: bool, requires_password_change: bool, message_type: int, message_template_id: int, external_id: str, id_value: int, uuid: str) -> Dict:
        """
        🔐 POST /system/admins/:id/changepassword
        Changes the specified admin user's password.

        :param admin_id: ID of the admin user
        :return: Dict with result of password change operation
        """
        url = f"{self.api_url}/system/admins/{admin_id}/changepassword"
        payload = {
            "Password": password,
            "OrganizationGroupUuid": organization_group_uuid,
            "TimeZoneIdentifier": time_zone_identifier,
            "LastLoginTimeStamp": last_login_timestamp,
            "IsActiveDirectoryUser": is_active_directory_user,
            "RequiresPasswordChange": requires_password_change,
            "MessageType": message_type,
            "MessageTemplateId": message_template_id,
            "ExternalId": external_id,
            "Id": { "Value": id_value },
            "Uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    
    
    
    def add_role_to_admin(self, admin_id: str, role_id: int, role_uuid: str, location_group: str, location_group_id: str, organization_group_uuid: str, is_active: bool, user_link_id: int) -> Dict:
        """
        ➕ POST /system/admins/:id/addrole
        Adds a role to the specified admin user.

        :param admin_id: ID of the admin user
        :param role_id: ID of the role to assign
        :param role_uuid: UUID of the role
        :param location_group: Name of the location group
        :param location_group_id: ID of the location group
        :param organization_group_uuid: UUID of the organization group
        :param is_active: Whether the role is active
        :param user_link_id: User link ID associated with the role
        :return: Dict with result of the role assignment
        """
        url = f"{self.api_url}/system/admins/{admin_id}/addrole"
        payload = {
            "Id": role_id,
            "Uuid": role_uuid,
            "LocationGroup": location_group,
            "LocationGroupId": location_group_id,
            "OrganizationGroupUuid": organization_group_uuid,
            "IsActive": is_active,
            "UserLinkId": user_link_id
        }
        return self._send_request("POST", url, json_data=payload)
    
    
    def get_admin_about_page_config(self, admin_id: str) -> Dict:
        """
        🧾 GET /system/admins/:adminId/configurationsaboutpage
        Retrieves the value for showConfigurationsAboutPage for the specified admin.

        :param admin_id: Identifier for the admin
        :return: Dict containing showAboutPage config
        """
        url = f"{self.api_url}/system/admins/{admin_id}/configurationsaboutpage"
        return self._send_request("GET", url)
    
    
    def update_admin_about_page_config(self, admin_id: str, show_page: bool) -> Dict:
        """
        🔧 POST /system/admins/:adminId/configurationsaboutpage/:showpage
        Updates the value for showConfigurationsAboutPage for the specified admin.

        :param admin_id: Identifier for the admin
        :param show_page: True if the About page should be shown, otherwise False
        :return: Dict with result of update operation
        """
        showpage_str = str(show_page).lower()
        url = f"{self.api_url}/system/admins/{admin_id}/configurationsaboutpage/{showpage_str}"
        return self._send_request("POST", url)
    
    
    def remove_role_from_admin(self, admin_id: str, role_id: int, role_uuid: str, location_group: str, location_group_id: str, organization_group_uuid: str, is_active: bool, user_link_id: int) -> Dict:
        """
        ❌ POST /system/admins/:id/removerole
        Removes a role from the specified admin user.

        :param admin_id: ID of the admin user
        :param role_id: ID of the role to remove
        :param role_uuid: UUID of the role
        :param location_group: Name of the location group
        :param location_group_id: ID of the location group
        :param organization_group_uuid: UUID of the organization group
        :param is_active: Whether the role is active
        :param user_link_id: User link ID associated with the role
        :return: Dict with result of the role removal
        """
        url = f"{self.api_url}/system/admins/{admin_id}/removerole"
        payload = {
            "Id": role_id,
            "Uuid": role_uuid,
            "LocationGroup": location_group,
            "LocationGroupId": location_group_id,
            "OrganizationGroupUuid": organization_group_uuid,
            "IsActive": is_active,
            "UserLinkId": user_link_id
        }
        return self._send_request("POST", url, json_data=payload)
    
    
    def get_advanced_ldap_sync_jobs(self, organization_group_uuid: str, page_number: Optional[int] = None, page_size: Optional[int] = None, status_filter: Optional[int] = None, search_text: Optional[str] = None, sort_column: Optional[str] = None, sort_order: Optional[str] = None) -> Dict:
        """
        📄 GET /system/advanced-ldap-sync-jobs
        Retrieves Advanced LDAP Sync job details for a specific Organization Group.

        :param organization_group_uuid: UUID of the organization group (required)
        :param page_number: Optional page number
        :param page_size: Optional page size (default/max 500)
        :param status_filter: Optional filter by job status (1-10)
        :param search_text: Optional filter by search text
        :param sort_column: Optional column to sort by (default: JOB_ID)
        :param sort_order: Optional sort order (ASC/DESC)
        :return: Dict containing job details
        """
        url = f"{self.api_url}/system/advanced-ldap-sync-jobs"
        params = {
            "organization_group_uuid": organization_group_uuid,
            "page_number": page_number,
            "page_size": page_size,
            "status_filter": status_filter,
            "search_text": search_text,
            "sort_column": sort_column,
            "sort_order": sort_order
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")
        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    
    def create_advanced_ldap_sync_job(self, organization_group_uuid: str, refresh: str, use_external_id: bool, enrollment_user_uuids: List[str]) -> Dict:
        """
        🚀 POST /system/advanced-ldap-sync-jobs
        Creates a new LDAP sync job for the given organization group.

        :param organization_group_uuid: UUID of the organization group
        :param refresh: Refresh mode (e.g., NONE)
        :param use_external_id: Whether to use external ID
        :param enrollment_user_uuids: List of enrollment user UUIDs to sync
        :return: Dict containing the created job UUID
        """
        url = f"{self.api_url}/system/advanced-ldap-sync-jobs"
        payload = {
            "organization_group_uuid": organization_group_uuid,
            "refresh": refresh,
            "use_external_id": use_external_id,
            "enrollment_user_uuids": enrollment_user_uuids
        }
        return self._send_request("POST", url, json_data=payload)
    
    def get_advanced_ldap_sync_job_details(self, job_uuid: str, page_number: Optional[int] = None, page_size: Optional[int] = None, search_text: Optional[str] = None, sort_column: Optional[str] = None, sort_order: Optional[str] = None) -> Dict:
        """
        🔍 GET /system/advanced-ldap-sync-jobs/:uuid
        Retrieves detailed results of a specific Advanced LDAP Sync job.

        :param job_uuid: UUID of the LDAP sync job
        :param page_number: Optional page number
        :param page_size: Optional page size (default/max 500)
        :param search_text: Optional search filter
        :param sort_column: Optional column to sort by
        :param sort_order: Optional order to sort (ASC/DESC)
        :return: Dict with LDAP sync job result details
        """
        url = f"{self.api_url}/system/advanced-ldap-sync-jobs/{job_uuid}"
        params = {
            "page_number": page_number,
            "page_size": page_size,
            "search_text": search_text,
            "sort_column": sort_column,
            "sort_order": sort_order
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
    
    
    
    
    def approve_or_decline_ldap_sync_job(self, job_uuid: str, action: str, approval_type: str, enrollment_user_uuids: List[str]) -> Dict:
        """
        ✅ POST /system/advanced-ldap-sync-jobs/:uuid?action=
        Approves or declines the specified LDAP sync job.

        :param job_uuid: UUID of the LDAP sync job
        :param action: Approval action ("approve" or "decline")
        :param approval_type: Type of approval ("ALL" or other applicable values)
        :param enrollment_user_uuids: List of enrollment user UUIDs to approve/decline
        :return: Dict with result of the operation
        """
        url = f"{self.api_url}/system/advanced-ldap-sync-jobs/{job_uuid}"
        params = { "action": action }
        payload = {
            "approval_type": approval_type,
            "enrollment_user_uuids": enrollment_user_uuids
        }
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending POST request to {url} with action={action} and payload: {payload}")
        try:
            response = self.session.post(url, headers=headers, params=params, json=payload, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 POST request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    
    def get_ldap_sync_job_status(self, job_uuid: str) -> Dict:
        """
        📊 GET /system/advanced-ldap-sync-jobs/status/:uuid
        Gets the status of the specified LDAP sync job.

        :param job_uuid: UUID of the LDAP sync job
        :return: Dict with job status and enrollment user counts
        """
        url = f"{self.api_url}/system/advanced-ldap-sync-jobs/status/{job_uuid}"
        return self._send_request("GET", url)
    
    
    def get_android_work_settings(self, location_group_id: str) -> Dict:
        """
        🤖 GET /system/groups/:id/androidwork
        Retrieves Android Work settings for the specified Location Group.

        :param location_group_id: ID of the location group
        :return: Dict containing Android Work configuration
        """
        url = f"{self.api_url}/system/groups/{location_group_id}/androidwork"
        return self._send_request("GET", url)
    
    
    def get_apns_certificate_request(self, location_group_id: str) -> Dict:
        """
        🍎 GET /system/groups/:id/apns
        Retrieves the APNs certificate request details for the specified Organization Group.

        :param location_group_id: ID of the organization group
        :return: Dict containing APNs certificate request data
        """
        url = f"{self.api_url}/system/groups/{location_group_id}/apns"
        return self._send_request("GET", url)
    
    
    def save_apns_configuration(self, location_group_id: str, apple_id: str, csr_blob_id: int, uploaded_cert_blob_id: int, issued_cert_id: int, renew: bool, cert_password: str, id_value: int, uuid: str) -> Dict:
        """
        📥 POST /system/groups/:id/apns
        Saves the APNs configuration for the specified Organization Group.

        :param location_group_id: ID of the organization group
        :param apple_id: Apple ID used for the certificate
        :param csr_blob_id: ID of the Certificate Signing Request blob
        :param uploaded_cert_blob_id: ID of the uploaded certificate blob
        :param issued_cert_id: ID of the issued certificate
        :param renew: Boolean flag indicating if the certificate is being renewed
        :param cert_password: Password for the certificate
        :param id_value: Internal ID value
        :param uuid: UUID of the certificate configuration
        :return: Dict with result of save operation
        """
        url = f"{self.api_url}/system/groups/{location_group_id}/apns"
        payload = {
            "AppleId": apple_id,
            "CertificateSigningRequestBlobId": csr_blob_id,
            "UploadedCertificateBlobId": uploaded_cert_blob_id,
            "IssuedCertificateId": issued_cert_id,
            "Renew": renew,
            "CertificatePassword": cert_password,
            "id": id_value,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def update_apns_configuration(self, location_group_id: str, inherit: bool, child_permission: str, id_value: int, uuid: str) -> Dict:
        """
        🔁 PATCH /system/groups/:id/apns
        Updates the APNs configuration for the specified Organization Group.

        :param location_group_id: ID of the organization group
        :param inherit: Boolean to indicate inheritance
        :param child_permission: Permission value for child
        :param id_value: Internal ID value
        :param uuid: UUID of the configuration
        :return: Dict with result of update operation
        """
        url = f"{self.api_url}/system/groups/{location_group_id}/apns"
        payload = {
            "Inherit": inherit,
            "ChildPermission": child_permission,
            "id": id_value,
            "uuid": uuid
        }
        return self._send_request("PATCH", url, json_data=payload)
    
    def get_app_content_storage_info(self, organization_group_id: str) -> Dict:
        """
        📦 GET /system/groups/:ogid/storage
        Fetches application and content storage information for the specified Organization Group.

        :param organization_group_id: ID of the organization group
        :return: Dict with storage capacity, overage, and max file sizes
        """
        url = f"{self.api_url}/system/groups/{organization_group_id}/storage"
        return self._send_request("GET", url)
    
    
    def create_basic_to_directory_sync_job(self, organization_group_uuid: str, is_bulk: bool, filter_value: int, enrollment_user_uuids: List[str]) -> Dict:
        """
        🔄 POST /system/user-migration-jobs/basic-to-directory
        Creates a Basic-to-Directory sync job to migrate enrollment users.

        :param organization_group_uuid: UUID of the organization group
        :param is_bulk: Boolean to indicate if it's a bulk migration
        :param filter_value: Filter type to apply (e.g., 1)
        :param enrollment_user_uuids: List of enrollment user UUIDs to migrate
        :return: Dict containing the sync job UUID
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory"
        payload = {
            "organization_group_uuid": organization_group_uuid,
            "is_bulk": is_bulk,
            "filter": filter_value,
            "enrollment_user_uuids": enrollment_user_uuids
        }
        return self._send_request("POST", url, json_data=payload)
    
    def get_directory_users_for_migration_job(self, organization_group_uuid: str, page_number: Optional[int] = None, page_size: Optional[int] = None, search_text: Optional[str] = None, sort_column: Optional[str] = None, sort_order: Optional[str] = None, filter_value: Optional[str] = None) -> Dict:
        """
        📥 GET /system/user-migration-jobs/basic-to-directory/:oguuid
        Retrieves a list of directory users for a given Organization Group UUID.

        :param organization_group_uuid: UUID of the Organization Group
        :param page_number: Optional page number
        :param page_size: Optional page size (default/max 500)
        :param search_text: Optional filter text
        :param sort_column: Column to sort by (default: JOB_ID)
        :param sort_order: Sort order (ASC/DESC)
        :param filter_value: Filter column for users
        :return: Dict containing directory user details
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/{organization_group_uuid}"
        params = {
            "page_number": page_number,
            "page_size": page_size,
            "search_text": search_text,
            "sort_column": sort_column,
            "sort_order": sort_order,
            "filter": filter_value
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_matching_basic_users_for_ldap_user(self, ldap_user_uuid: str) -> Dict:
        """
        🔍 GET /system/user-migration-jobs/basic-to-directory/get-matching-basic-users/:ldapUserUuid
        Retrieves similar basic enrollment users for the given LDAP user UUID.

        :param ldap_user_uuid: UUID of the LDAP user
        :return: Dict containing matched basic user records
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/get-matching-basic-users/{ldap_user_uuid}"
        return self._send_request("GET", url)
    
    def migrate_basic_to_directory_users(self, sync_job_uuid: str) -> Dict:
        """
        🚀 POST /system/user-migration-jobs/basic-to-directory/migrate
        Migrates selective or all users from basic to directory using the provided sync job UUID.

        :param sync_job_uuid: UUID of the basic-to-directory sync job
        :return: Dict indicating the result of the migration initiation
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/migrate"
        payload = {
            "basic_to_directory_sync_job_uuid": sync_job_uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def update_synced_basic_user(self, sync_job_id: int, ldap_user_uuid: str, basic_user_uuid: str, matched_type: int) -> Dict:
        """
        🔁 PUT /system/user-migration-jobs/basic-to-directory/update
        Updates the synced basic user in a Basic-to-Directory sync job.

        :param sync_job_id: ID of the basic-to-directory sync job
        :param ldap_user_uuid: UUID of the LDAP user
        :param basic_user_uuid: UUID of the basic user
        :param matched_type: Type of the match (e.g., 1)
        :return: Dict with result of the update operation
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/update"
        payload = {
            "basic_to_directory_sync_job_id": sync_job_id,
            "ldap_user_uuid": ldap_user_uuid,
            "basic_user_uuid": basic_user_uuid,
            "matched_type": matched_type
        }
        return self._send_request("PUT", url, json_data=payload)
    
    def delete_basic_to_directory_sync_job(self, job_uuid: str) -> Dict:
        """
        ❌ DELETE /system/user-migration-jobs/basic-to-directory/delete-job/:jobUuid
        Deletes the specified Basic-to-Directory sync job.

        :param job_uuid: UUID of the sync job to delete
        :return: Dict with deletion result (empty if successful)
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/delete-job/{job_uuid}"
        return self._send_request("DELETE", url)
    
    def delete_user_from_migration_list(self, mapped_users: List[Dict]) -> Dict:
        """
        ❌ DELETE /system/user-migration-jobs/basic-to-directory/delete-user
        Deletes a user from the Basic-to-Directory sync job migration list.

        :param mapped_users: A list of user mappings to delete, each containing fields like:
                             basic_to_directory_sync_job_id, ldap_user_uuid, basic_user_uuid, etc.
        :return: Empty dict if deletion was successful
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/delete-user"
        payload = {
            "mapped_user": mapped_users
        }
        return self._send_request("DELETE", url, json_data=payload)
    
    def get_mapped_users_for_sync_job(self, job_uuid: str) -> Dict:
        """
        📥 GET /system/user-migration-jobs/basic-to-directory/mapped-user/:job-uuid
        Retrieves all mapped users for a given Basic-to-Directory sync job.

        :param job_uuid: UUID of the sync job
        :return: Dict containing mapped user details
        """
        url = f"{self.api_url}/system/user-migration-jobs/basic-to-directory/mapped-user/{job_uuid}"
        params = { "jobUuid": job_uuid }
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {params}")

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_cloud_connector_status(self, organization_group_uuid: str) -> Dict:
        """
        ☁️ GET /system/groups/:organizationGroupUuid/cloud-connector/connection-status
        Returns the connection status for the AirWatch Cloud Connector for the given organization group.

        :param organization_group_uuid: UUID of the organization group
        :return: Dict containing the connection status
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/cloud-connector/connection-status"
        return self._send_request("GET", url)
    
    def create_custom_attribute(self, application_group: str, description: str, managed_by_org_group_id: str, name: str, persist: bool, show_in_rule_creator: bool, use_as_lookup_value: bool, collect_values_for_rule_creator: bool, values: List[Dict], uuid: str) -> Dict:
        """
        🧩 POST /system/customattributes/create
        Creates a custom attribute definition in AirWatch.

        :param application_group: The application group name
        :param description: Description of the custom attribute
        :param managed_by_org_group_id: ID of the managing organization group
        :param name: Name of the custom attribute
        :param persist: Whether the attribute should persist
        :param show_in_rule_creator: Whether to show in rule creator
        :param use_as_lookup_value: Whether it should be used as a lookup value
        :param collect_values_for_rule_creator: Whether to collect values for rule creator
        :param values: List of values, each with a 'uuid'
        :param uuid: UUID of the custom attribute
        :return: Dict containing creation result
        """
        url = f"{self.api_url}/system/customattributes/create"
        payload = {
            "ApplicationGroup": application_group,
            "CollectValuesForRuleCreator": collect_values_for_rule_creator,
            "Description": description,
            "ManagedByOrganizationGroupID": managed_by_org_group_id,
            "Name": name,
            "Persist": persist,
            "ShowInRuleCreator": show_in_rule_creator,
            "UseAsLookupValue": use_as_lookup_value,
            "Values": values,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)

    def search_custom_attributes(self, organizationgroupid: Optional[str] = None, name: Optional[str] = None, page: Optional[int] = None, pagesize: Optional[int] = None) -> Dict:
        """
        🔍 GET /system/customattributes/search
        Searches for custom attributes with optional filters.

        :param organizationgroupid: ID of the organization group (optional)
        :param name: Name of the custom attribute (optional)
        :param page: Page number (0-based index)
        :param pagesize: Number of records per page
        :return: Dict containing search results
        """
        url = f"{self.api_url}/system/customattributes/search"
        params = {
            "organizationgroupid": organizationgroupid,
            "name": name,
            "page": page,
            "pagesize": pagesize
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
    
    def get_custom_gateway_settings(self, module_name: str, configuration_uuid: str) -> Dict:
        """
        🌐 GET /system/custom-gateway-settings/:moduleName/configuration/:configurationUuid
        Retrieves the Custom Gateway Settings for ContentGateway, Tunnel, and MEM.

        :param module_name: Module name (e.g., CONTENT_GATEWAY, TUNNEL, MEM)
        :param configuration_uuid: UUID of the configuration
        :return: Dict containing the custom gateway settings
        """
        url = f"{self.api_url}/system/custom-gateway-settings/{module_name}/configuration/{configuration_uuid}"
        return self._send_request("GET", url)

    def bulk_update_custom_gateway_settings(self, module_name: str, configuration_uuid: str, settings: List[Dict]) -> Dict:
        """
        🛠️ POST /system/custom-gateway-settings/:moduleName/configuration/:configurationUuid
        Bulk Add, Update, or Delete Custom Gateway Settings for ContentGateway, Tunnel, or MEM.

        :param module_name: Module name (e.g., CONTENT_GATEWAY, TUNNEL, MEM)
        :param configuration_uuid: UUID of the configuration
        :param settings: List of settings, each as a dict with keys such as Key, ValueType, Value, etc.
        :return: Empty dict if successful
        """
        url = f"{self.api_url}/system/custom-gateway-settings/{module_name}/configuration/{configuration_uuid}"
        return self._send_request("POST", url, json_data=settings)
    
    def get_custom_gateway_keys(self, module_name: str) -> Dict:
        """
        🧾 GET /system/custom-gateway-settings/:moduleName/keys
        Gets all predefined keys for the module with validation details.

        :param module_name: Module name (e.g., CONTENT_GATEWAY, TUNNEL, MEM)
        :return: Dict containing predefined key definitions and validation info
        """
        url = f"{self.api_url}/system/custom-gateway-settings/{module_name}/keys"
        return self._send_request("GET", url)
    
    def get_custom_gateway_key_details(self, key_uuid: str) -> Dict:
        """
        🧾 GET /system/custom-gateway-settings/keys/:keyUuid
        Gets details of a specific Custom Gateway Setting Key.

        :param key_uuid: UUID of the custom gateway setting key
        :return: Dict containing the key details
        """
        url = f"{self.api_url}/system/custom-gateway-settings/keys/{key_uuid}"
        return self._send_request("GET", url)
    
    def get_custom_reports_refresh_token(self) -> Dict:
        """
        🔁 GET /system/customreports/refreshtoken
        Gets the Custom Reports refresh token for the organization group.

        :return: Dict containing the refresh token, id, and uuid
        """
        url = f"{self.api_url}/system/customreports/refreshtoken"
        return self._send_request("GET", url)
    
    def delete_registered_devices_by_asset_number(self, asset_numbers: List[str]) -> Dict:
        """
        ❌ POST /system/users/registereddevices/deletebyassetnumber
        Deletes registered devices identified by their asset numbers.

        :param asset_numbers: List of asset number strings
        :return: Dict with the result of the deletion request
        """
        url = f"{self.api_url}/system/users/registereddevices/deletebyassetnumber"
        payload = {
            "BulkValues": {
                "Value": asset_numbers
            }
        }
        return self._send_request("POST", url, json_data=payload)

    def delete_registered_devices_by_serial_number(self, serial_numbers: List[str]) -> Dict:
        """
        ❌ POST /system/users/registereddevices/deletebyserialnumber
        Deletes registered devices identified by their serial numbers.

        :param serial_numbers: List of serial number strings
        :return: Dict with the result of the deletion request
        """
        url = f"{self.api_url}/system/users/registereddevices/deletebyserialnumber"
        payload = {
            "BulkValues": {
                "Value": serial_numbers
            }
        }
        return self._send_request("POST", url, json_data=payload)

    def delete_registered_devices_by_udid(self, udids: List[str]) -> Dict:
        """
        ❌ POST /system/users/registereddevices/deletebyudid
        Deletes registered devices identified by their UDIDs.

        :param udids: List of UDID strings
        :return: Dict with the result of the deletion request
        """
        url = f"{self.api_url}/system/users/registereddevices/deletebyudid"
        payload = {
            "BulkValues": {
                "Value": udids
            }
        }
        return self._send_request("POST", url, json_data=payload)
    
    
    def delete_registered_devices(self, searchby: str, identifiers: List[str]) -> Dict:
        """
        ❌ POST /system/users/registereddevices/delete?searchby=
        Deletes registered devices using a search identifier such as Udid, Serialnumber, or AssetNumber.

        :param searchby: The identifier type (Udid, Serialnumber, AssetNumber)
        :param identifiers: List of identifier strings
        :return: Dict with the result of the deletion request
        """
        url = f"{self.api_url}/system/users/registereddevices/delete?searchby={searchby}"
        payload = {
            "BulkValues": {
                "Value": identifiers
            }
        }
        return self._send_request("POST", url, json_data=payload)
    
    def search_enrollment_tokens(self, username: Optional[str] = None, userid: Optional[str] = None, organizationgroupid: Optional[str] = None, organizationgroup: Optional[str] = None, serialnumber: Optional[str] = None, assetnumber: Optional[str] = None, enrollmentstatusid: Optional[str] = None, compliancestatusid: Optional[str] = None) -> Dict:
        """
        🔍 GET /system/users/enrollmenttoken/search
        Searches for Enrollment Token and Device details using optional filters.

        :return: Dict containing matching enrollment token and device records
        """
        url = f"{self.api_url}/system/users/enrollmenttoken/search"
        params = {
            "username": username,
            "userid": userid,
            "organizationgroupid": organizationgroupid,
            "organizationgroup": organizationgroup,
            "serialnumber": serialnumber,
            "assetnumber": assetnumber,
            "enrollmentstatusid": enrollmentstatusid,
            "compliancestatusid": compliancestatusid
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_enrolled_devices(self, organizationgroupid: Optional[str] = None, organizationgroup: Optional[str] = None, platform: Optional[str] = None, customattributes: Optional[str] = None, serialnumber: Optional[str] = None, seensince: Optional[str] = None, seentill: Optional[str] = None, enrolledsince: Optional[str] = None, enrolledtill: Optional[str] = None) -> Dict:
        """
        📱 GET /system/users/enrolleddevices/search
        Retrieves enrolled device details with optional filters.

        :return: Dict containing enrolled device information
        """
        url = f"{self.api_url}/system/users/enrolleddevices/search"
        params = {
            "organizationgroupid": organizationgroupid,
            "organizationgroup": organizationgroup,
            "platform": platform,
            "customattributes": customattributes,
            "serialnumber": serialnumber,
            "seensince": seensince,
            "seentill": seentill,
            "enrolledsince": enrolledsince,
            "enrolledtill": enrolledtill
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_registered_devices(self, organizationgroupid: Optional[str] = None, organizationgroup: Optional[str] = None, platform: Optional[str] = None, customattributes: Optional[str] = None, assetnumber: Optional[str] = None, seensince: Optional[str] = None, seentill: Optional[str] = None) -> Dict:
        """
        📱 GET /system/users/registereddevices/search
        Retrieves registered device details with optional filters.

        :return: Dict containing registered device information
        """
        url = f"{self.api_url}/system/users/registereddevices/search"
        params = {
            "organizationgroupid": organizationgroupid,
            "organizationgroup": organizationgroup,
            "platform": platform,
            "customattributes": customattributes,
            "assetnumber": assetnumber,
            "seensince": seensince,
            "seentill": seentill
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")

        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_device_wipe_events(self, organization_group_uuid: str, search_text: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, wipe_type: Optional[str] = None, wipe_source: Optional[str] = None, wipe_status: Optional[str] = None, ownership: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None, sort_column: Optional[str] = None, sort_direction: Optional[str] = None) -> Dict:
        """
        🧹 GET /system/groups/:organizationGroupUuid/device-wipes
        Retrieves a list of device wipe events for the specified organization group.

        :param organization_group_uuid: UUID of the organization group
        :return: Dict containing device wipe events
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/device-wipes"
        params = {
            "search_text": search_text,
            "start_date": start_date,
            "end_date": end_date,
            "wipe_type": wipe_type,
            "wipe_source": wipe_source,
            "wipe_status": wipe_status,
            "ownership": ownership,
            "page": page,
            "page_size": page_size,
            "sort_column": sort_column,
            "sort_direction": sort_direction
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending GET request to {url} with params: {filtered_params}")
        try:
            response = self.session.get(url, headers=headers, params=filtered_params, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def perform_device_wipe_action(self, organization_group_uuid: str, action: str, wipe_uuids: List[str]) -> Dict:
        """
        ✅ POST /system/groups/:organizationGroupUuid/device-wipes?action=
        Performs the specified action (APPROVE or REJECT) on the selected wipe actions.

        :param organization_group_uuid: UUID of the organization group
        :param action: Action to perform ("APPROVE" or "REJECT")
        :param wipe_uuids: List of wipe action UUIDs to act on
        :return: Dict containing the result of the operation
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/device-wipes"
        params = {"action": action}
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending POST request to {url} with action={action} and wipe UUIDs: {wipe_uuids}")
        try:
            response = self.session.post(url, headers=headers, params=params, json=wipe_uuids, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 POST request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def create_device_wipe_report(self, organization_group_uuid: str, search_text: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, wipe_type: Optional[str] = None, wipe_status: Optional[str] = None, wipe_source: Optional[str] = None, ownership: Optional[List[str]] = None, sort_column: Optional[str] = None, sort_direction: Optional[str] = None, export_format: Optional[str] = None) -> Dict:
        """
        📄 POST /system/groups/:organizationGroupUuid/device-wipes/reports
        Creates the report for device wipe log.

        :param organization_group_uuid: UUID of the organization group
        :param search_text: Optional search string
        :param start_date: Optional start datetime string (ISO 8601 format)
        :param end_date: Optional end datetime string (ISO 8601 format)
        :param wipe_type: Optional wipe type
        :param wipe_status: Optional wipe status
        :param wipe_source: Optional wipe source
        :param ownership: Optional list of ownership types (e.g., ["ANY"])
        :param sort_column: Column to sort by (e.g., "DATE")
        :param sort_direction: Sort direction ("ASC" or "DESC")
        :param export_format: Format of the exported report (e.g., "XLSX")
        :return: Dict with report creation result
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/device-wipes/reports"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        payload = {
            "search_text": search_text,
            "start_date": start_date,
            "end_date": end_date,
            "wipe_type": wipe_type,
            "wipe_status": wipe_status,
            "wipe_source": wipe_source,
            "ownership": ownership,
            "sort_column": sort_column,
            "sort_direction": sort_direction,
            "export_format": export_format
        }
        # Remove None values from the payload
        filtered_payload = {k: v for k, v in payload.items() if v is not None}
        return self._send_request("POST", url, json_data=filtered_payload)
    
    def get_device_wipe_lock_state(self, organization_group_uuid: str) -> Dict:
        """
        🔒 GET /system/groups/:organizationGroupUuid/device-wipe-lock
        Retrieves the state of the wipe lock for the specified organization group.

        :param organization_group_uuid: UUID of the organization group
        :return: Dict containing the wipe lock state
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/device-wipe-lock"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending GET request to {url}")

        try:
            response = self.session.get(url, headers=headers, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def reset_device_wipe_lock(self, organization_group_uuid: str) -> Dict:
        """
        🔓 PUT /system/groups/:organizationGroupUuid/device-wipe-lock
        Resets the wipe lock to allow scheduled wipe actions to proceed.

        :param organization_group_uuid: UUID of the organization group
        :return: Empty dict if successful (HTTP 204 No Content)
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/device-wipe-lock"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending PUT request to {url} to reset wipe lock")
        try:
            response = self.session.put(url, headers=headers, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 PUT request to {url} returned {response.status_code}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def get_dropship_provisioning(self, organization_group_uuid: str) -> Dict:
        """
        🚚 GET /system/groups/:uuid/dropship-provisioning
        Retrieves dropship provisioning details for a given organization group.

        :param organization_group_uuid: UUID of the organization group
        :return: Dict containing dropship provisioning settings
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/dropship-provisioning"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        return self._send_request("GET", url)
    
    def enable_dropship_provisioning_v1(self, uuid: str, username: str, password: str, organization_group_uuid: str, sub_organization_groups: list,enable_dropship_provisioning: bool):
        """
        🚚 PATCH /system/groups/:uuid/dropship-provisioning
        Enables or disables dropship provisioning for a given organization group.

        :param uuid: UUID of the organization group
        :param username: Dropship provisioning username
        :param password: Dropship provisioning password
        :param organization_group_uuid: UUID of the organization group
        :param sub_organization_groups: List of sub-organization groups
        :param enable_dropship_provisioning: Boolean to enable/disable dropship provisioning
        :return: Dict containing the result of the operation
        """
        url = f"{self.api_url}/system/groups/{uuid}/dropship-provisioning"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        data = {
            "username": username,
            "password": password,
            "organization_group_uuid": organization_group_uuid,
            "sub_organization_groups": sub_organization_groups,
            "enable_dropship_provisioning": enable_dropship_provisioning
        }
        return self._send_request("PATCH", url, json_data=data)
    
    def create_enrollment_custom_attributes(self, serial_number: str, custom_attributes: List[Dict], uuid: str) -> Dict:
        """
        ➕ POST /system/users/registereddevices/serialnumber/:serialnumber/createcustomattributes
        Creates multiple new device custom attributes for a registered device.

        :param serial_number: Device Serial number
        :param custom_attributes: List of custom attributes to apply (each with 'uuid')
        :param uuid: UUID for the operation
        :return: Dict with result of the creation operation
        """
        url = f"{self.api_url}/system/users/registereddevices/serialnumber/{serial_number}/createcustomattributes"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        payload = { "CustomAttributes": custom_attributes, "uuid": uuid }
        return self._send_request("POST", url, json_data=payload)
    
    def update_custom_attributes_by_serial(self, serial_number: str, custom_attributes: List[Dict], uuid: str) -> Dict:
        """
        🛠️ POST /system/users/registereddevices/serialnumber/:serialnumber/updatecustomattributes
        Updates multiple device custom attribute values for a registered device.

        :param serial_number: Serial number of the registered device
        :param custom_attributes: List of custom attributes to update (each with a 'uuid')
        :param uuid: UUID of the update payload
        :return: Dict with the result of the update operation
        """
        url = f"{self.api_url}/system/users/registereddevices/serialnumber/{serial_number}/updatecustomattributes"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        payload = {
            "CustomAttributes": custom_attributes,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def delete_custom_attributes_by_serial(self, serial_number: str, custom_attribute_uuids: List[str], request_uuid: str) -> Dict:
        """
        🧹 POST /system/users/registereddevices/serialnumber/:serialnumber/deletecustomattributes
        Deletes multiple device custom attribute values for a registered device.

        :param serial_number: Device serial number (required)
        :param custom_attribute_uuids: List of custom attribute UUIDs to delete
        :param request_uuid: UUID for the deletion request
        :return: Dict with the result of the delete operation
        """
        url = f"{self.api_url}/system/users/registereddevices/serialnumber/{serial_number}/deletecustomattributes"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        payload = {
            "CustomAttributes": [{"uuid": uuid} for uuid in custom_attribute_uuids],
            "uuid": request_uuid
        }
        self.logger.info(f"🔄 Sending POST request to {url} to delete custom attributes")
        return self._send_request("POST", url, json_data=payload)
    
    def create_custom_attributes_for_registered_device(self, asset_number: str, custom_attribute_uuids: List[str], device_uuid: str) -> Dict:
        """
        ➕ POST /system/users/registereddevices/assetnumber/:assetnumber/updatecustomattributes
        Updates multiple device custom attribute values for a registered device.

        :param asset_number: Asset number of the device
        :param custom_attribute_uuids: List of UUIDs for the custom attributes
        :param device_uuid: UUID of the device
        :return: Dict containing the result of the update
        """
        url = f"{self.api_url}/system/users/registereddevices/assetnumber/{asset_number}/updatecustomattributes"
        payload = {
            "CustomAttributes": [{"uuid": uuid} for uuid in custom_attribute_uuids],
            "uuid": device_uuid
        }
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending POST request to {url} with payload: {payload}")
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 POST request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
    
    def delete_custom_attributes_for_registered_device(self, asset_number: str, custom_attributes: List[Dict[str, str]], uuid: str) -> Dict:
        """
        ❌ POST /system/users/registereddevices/assetnumber/:assetnumber/deletecustomattributes
        Deletes custom attributes from a registered device identified by asset number.

        :param asset_number: The asset number of the device
        :param custom_attributes: A list of custom attribute dicts with 'uuid' keys
        :param uuid: UUID of the delete operation
        :return: Dict with the result of the deletion request
        """
        url = f"{self.api_url}/system/users/registereddevices/assetnumber/{asset_number}/deletecustomattributes"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        payload = {
            "CustomAttributes": custom_attributes,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def get_enrollment_customization_settings(self, organization_group_uuid: str) -> Dict:
        """
        🎨 GET /system/groups/:organizationGroupUuid/settings/enrollment/customization
        Retrieves enrollment customization settings for the given Organization Group.

        :param organization_group_uuid: UUID of the organization group
        :return: Dict containing customization settings
        """
        url = f"{self.api_url}/system/groups/{organization_group_uuid}/settings/enrollment/customization"
        headers = self._get_headers(url)
        headers["Accept"] = "application/json;version=1"
        self.logger.info(f"🔄 Sending GET request to {url}")
        
        try:
            response = self.session.get(url, headers=headers, timeout=90)
            response.raise_for_status()
            self.logger.info(f"📤 GET request to {url} returned {response.status_code}")
            self.logger.debug(f"📥 Response: {response.text}")
            return response.json() if response.text else {}
        except requests.RequestException as e:
            self.logger.error(f"❌ API Request Failed: {e}")
            raise APIRequestError(f"API request to {url} failed", status_code=getattr(e.response, 'status_code', None))
        
    def create_event_notification_rule(self, target_name: str, target_url: str, username: str, password: str, format_id: int, is_active: bool, device_events: Dict, organization_group_id: int, organization_group_uuid: str, id_value: int, uuid: str) -> Dict:
        """
        📩 POST /system/eventnotifications
        Creates a new Event Notification rule with events to subscribe to.

        :param target_name: Name of the target system
        :param target_url: Callback URL to receive event notifications
        :param username: Username for authentication
        :param password: Password for authentication
        :param format_id: Notification format ID (e.g., 1 for JSON)
        :param is_active: Whether the rule is active
        :param device_events: Dictionary of device events and attribute toggles
        :param organization_group_id: ID of the organization group
        :param organization_group_uuid: UUID of the organization group
        :param id_value: Internal ID of the rule
        :param uuid: UUID of the rule
        :return: Dict containing the result of the rule creation
        """
        url = f"{self.api_url}/system/eventnotifications"
        payload = {
            "TargetName": target_name,
            "TargetUrl": target_url,
            "Username": username,
            "Password": password,
            "Format": format_id,
            "IsActive": is_active,
            "DeviceEvents": device_events,
            "organizationGroupId": organization_group_id,
            "organizationGroupUuid": organization_group_uuid,
            "id": id_value,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def create_event_notification_rule(self, target_name: str, target_url: str, username: str, password: str, format_id: int, is_active: bool, organization_group_id: int, organization_group_uuid: str, device_events: Dict, record_id: int, uuid: str) -> Dict:
        """
        🔔 POST /system/eventnotifications/V1/eventnotifications
        Creates a new Event Notification rule with events to subscribe to.

        :param target_name: The target name of the event notification
        :param target_url: The URL to which notifications are sent
        :param username: Username for notification target authentication
        :param password: Password for notification target authentication
        :param format_id: Format type for the notification (e.g., 1)
        :param is_active: Whether the rule is active
        :param organization_group_id: ID of the associated organization group
        :param organization_group_uuid: UUID of the associated organization group
        :param device_events: Dictionary containing device event settings
        :param record_id: Internal ID value
        :param uuid: UUID of the event notification rule
        :return: Dict with creation result
        """
        url = f"{self.api_url}/system/eventnotifications/V1/eventnotifications"
        payload = {
            "TargetName": target_name,
            "TargetUrl": target_url,
            "Username": username,
            "Password": password,
            "Format": format_id,
            "IsActive": is_active,
            "DeviceEvents": device_events,
            "organizationGroupId": organization_group_id,
            "organizationGroupUuid": organization_group_uuid,
            "id": record_id,
            "uuid": uuid
        }
        return self._send_request("POST", url, json_data=payload)
    
    def get_event_notification_rule_by_id(self, event_notification_id: str) -> Dict:
        """
        🔍 GET /system/eventnotifications/:id
        Retrieves details of an Event Notification Rule identified by EventNotification Id.

        :param event_notification_id: ID of the Event Notification Rule
        :return: Dict with details of the Event Notification Rule
        """
        url = f"{self.api_url}/system/eventnotifications/{event_notification_id}"
        return self._send_request("GET", url)
    
    
    def update_event_notification_rule(self, notification_id: str, payload: Dict) -> Dict:
        """
        ✏️ PUT /system/eventnotifications/V1/eventnotifications/:id
        Updates an Event Notification Rule identified by its ID.

        :param notification_id: ID of the Event Notification Rule to update
        :param payload: Dict containing fields to update, including DeviceEvents, TargetUrl, etc.
        :return: Dict with the result of the update operation
        """
        url = f"{self.api_url}/system/eventnotifications/V1/eventnotifications/{notification_id}"
        return self._send_request("PUT", url, json_data=payload)
        
    def get_event_notification_rule(self, notification_id: str) -> Dict:
        """
        📄 GET /system/eventnotifications/V1/eventnotifications/:id
        Retrieves details of an Event Notification Rule identified by its ID.

        :param notification_id: ID of the Event Notification Rule
        :return: Dict containing rule details
        """
        url = f"{self.api_url}/system/eventnotifications/V1/eventnotifications/{notification_id}"
        return self._send_request("GET", url)
    
    
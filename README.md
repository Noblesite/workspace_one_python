# Workspace ONE Python Framework

A lightweight, modular Python SDK for automating and interacting with Workspace ONE UEM (AirWatch) environments using modern CMSURL-based authentication.

---

## ✨ Features

- 🔐 Certificate-based CMSURL authentication (no password rotation needed)
- 🧩 Modular APIs:
  - MDM (devices, tags, profiles)
  - MAM (internal apps, smart groups)
  - System (organization groups, users)
- 🛠️ Full logging and exception handling
- 🧼 Environment-agnostic (no hardcoding)
- 📂 Example automation workflows included

---

## 🛠️ Installation

```bash
# Install dependencies
pip install -r requirements.txt

# OR install locally if pyproject.toml is provided
pip install -e .
```

---

## ⚙️ Usage Example

```python
from workspace_one_workflows.mdm.mdm import MDM
from workspace_one_workflows.environment.aw_environment import AWEnvironment
from workspace_one_workflows.auth.workspace_one_auth import WorkspaceOneAuth

aw_env = AWEnvironment(
    api_url="https://your.saas.api.url",
    tenant_code="your-tenant-code",
    parent_og=None  # Optional
)

auth = WorkspaceOneAuth(
    cert_path="./certs/your_cert.p12",
    cert_pw="your_cert_password"
)

mdm = MDM(environment=aw_env, auth=auth)

# Retrieve a device
device = mdm.retrieve_device_information(device_id="123456")
print(device)
```

---

## 📁 Project Structure

```
workspace_one_workflows/
├── auth/
│   └── workspace_one_auth.py
├── environment/
│   └── aw_environment.py
├── mdm/
│   └── mdm.py
├── mam/
│   └── mam.py
├── system/
│   └── system.py
├── exceptions/
│   └── api_exceptions.py
examples/
├── device_health_report.py
.env.example
README.md
LICENSE
```

---

## 📚 Examples

Checkout `/examples` for ready-to-use scripts like:

- Device Health Reports
- Device Lookup
- Certificate Expiry Monitoring

---

## 📄 License

This project is licensed under the MIT License.

---

_Designed for easy, scalable Workspace ONE UEM automation._

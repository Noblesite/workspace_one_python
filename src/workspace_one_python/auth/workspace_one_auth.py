#!/usr/bin/env python3
import os
import base64
from dotenv import load_dotenv
from urllib.parse import urlparse
from typing import Optional, Tuple
import logging

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class CMSURLError(Exception):
    """Custom exception for CMSURL auth failures."""
    pass

class WorkspaceOneAuth:
    """
    Handles Workspace One authentication by generating the CMSURL header value using
    pyca/cryptography's PKCS7SignatureBuilder.

    Example:
        auth = WorkspaceOneAuth(cert_path="cert.p12", cert_pw="password")
        header = auth.get_cmsurl_header("https://your.cmsurl.path")
    """

    def __init__(self, cert_path: str, cert_pw: str, logger=None):
        self.cert_path = cert_path
        self.cert_pw = cert_pw
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def from_memory(cls, cert_bytes: bytes, cert_pw: str, logger=None):
        self = cls(cert_path="", cert_pw=cert_pw, logger=logger)
        self.logger = logger or logging.getLogger(__name__)
        self.cert_bytes = cert_bytes
        self.use_memory_cert = True
        return self

    def get_cmsurl_header(self, url: str) -> Optional[str]:
        """
        Returns the CMSURL header value for the given URL.
        """
        p12_cert_path = self.cert_path
        cert_password = self.cert_pw

        # Load private key and certificate from the PKCS#12 file.
        try:
            private_key, certificate = self._load_p12_cert(p12_cert_path, cert_password)
        except CMSURLError:
            self.logger.error("❌ Failed to load certificate. Aborting CMSURL header generation.")
            return None

        if not private_key or not certificate:
            self.logger.error("❌ Failed to load certificate. Aborting CMSURL header generation.")
            return None

        # Compute canonical URL as the absolute path only (exclude query parameters).
        parsed_url = urlparse(url)
        canonical_path = parsed_url.path  # Per docs, do NOT include the query string.
        self.logger.debug(f"🔒 Signing canonical URL: {canonical_path}")

        # Generate a CMS/PKCS#7 signature container.
        cms_container = self._sign_data(private_key, certificate, canonical_path)
        if cms_container is None:
            self.logger.error("❌ Signing failed. Unable to generate CMSURL header.")
            return None

        # Base64 encode the CMS container and prefix it.
        encoded_signature = base64.b64encode(cms_container).decode()
        header_value = f"CMSURL`1 {encoded_signature}"
        self.logger.info("✅ CMSURL header successfully generated.")
        return header_value

    def _load_p12_cert(self, p12_path: str, password: str) -> Tuple[Optional[object], Optional[object]]:
        """
        Load the PKCS#12 certificate file (.p12) and extract the private key and certificate.
        """
        try:
            if getattr(self, "use_memory_cert", False):
                p12_data = self.cert_bytes
            else:
                with open(p12_path, "rb") as f:
                    p12_data = f.read()

            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                p12_data, password.encode(), backend=default_backend()
            )

            self.logger.info("✅ Successfully loaded PKCS#12 certificate.")
            return private_key, certificate

        except Exception as e:
            self.logger.error(f"❌ Error loading PKCS#12 file: {e}")
            raise CMSURLError(f"Failed to load PKCS#12 certificate: {e}")

    def _sign_data(self, private_key, certificate, data):
        """
        Generate a CMS/PKCS#7 signature container for the given data using the PKCS7SignatureBuilder.
        This creates a DER-encoded, detached signature (i.e. the signed data is not embedded).
        """
        try:
            # Ensure the data is in bytes.
            data_bytes = data.encode("utf-8")

            # Create the PKCS7SignatureBuilder and add our signer.
            builder = pkcs7.PKCS7SignatureBuilder().set_data(data_bytes)
            builder = builder.add_signer(
                certificate,
                private_key,
                hashes.SHA512()
            )

            # Generate the detached signature in DER format.
            cms_der = builder.sign(Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
            self.logger.debug("✅ CMS signature generated successfully using PKCS7SignatureBuilder.")
            return cms_der

        except Exception as e:
            self.logger.error(f"❌ Exception in CMS signing: {e}")
            return None
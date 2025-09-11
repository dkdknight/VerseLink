import os
import sys

# Ensure backend modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.organization import Organization

def test_organization_accepts_relative_media_urls():
    org = Organization(
        name="Test Org",
        tag="TO",
        owner_id="user1",
        logo_url="/uploads/orgs/logo.png",
        banner_url="/uploads/orgs/banner.png",
    )
    assert org.logo_url == "/uploads/orgs/logo.png"
    assert org.banner_url == "/uploads/orgs/banner.png"
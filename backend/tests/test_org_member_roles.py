import os
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Required environment variables
os.environ.setdefault("JWT_SECRET_KEY", "testsecret")
os.environ.setdefault("DISCORD_CLIENT_ID", "test_client")
os.environ.setdefault("DISCORD_CLIENT_SECRET", "test_secret")
os.environ.setdefault("DISCORD_REDIRECT_URI", "http://localhost")

from routers import organizations as org_router
from middleware.auth import get_current_active_user
from models.user import User
from models.organization import OrgMemberRole


class FakeCollection:
    def __init__(self):
        self.items = []

    async def find_one(self, query):
        for item in self.items:
            if all(item.get(k) == v for k, v in query.items()):
                return item
        return None

    async def insert_one(self, doc):
        self.items.append(doc)

    async def update_one(self, query, update):
        doc = await self.find_one(query)
        if doc:
            doc.update(update.get("$set", {}))
            return type("Result", (), {"matched_count": 1})
        return type("Result", (), {"matched_count": 0})

    async def delete_one(self, query):
        for i, item in enumerate(self.items):
            if all(item.get(k) == v for k, v in query.items()):
                del self.items[i]
                return type("Result", (), {"deleted_count": 1})
        return type("Result", (), {"deleted_count": 0})


class FakeDatabase:
    def __init__(self):
        self.organizations = FakeCollection()
        self.org_members = FakeCollection()


fake_db = FakeDatabase()


def override_get_database():
    return fake_db


org_router.get_database = override_get_database

app = FastAPI()
app.include_router(org_router.router, prefix="/api/v1/organizations")


admin_user = User(id="admin1", handle="admin", discord_id="1", discord_username="admin#0001")
member_user = User(id="member1", handle="member", discord_id="2", discord_username="member#0001")


def override_admin_user():
    return admin_user


def override_member_user():
    return member_user


app.dependency_overrides[get_current_active_user] = override_admin_user
client = TestClient(app)


def setup_function():
    fake_db.organizations.items = [{"id": "org1", "owner_id": "owner1"}]
    fake_db.org_members.items = [
        {"org_id": "org1", "user_id": "owner1", "role": "admin"},
        {"org_id": "org1", "user_id": "admin1", "role": "admin"},
        {"org_id": "org1", "user_id": "member1", "role": "member"},
    ]


def test_admin_can_change_role():
    res = client.patch(
        "/api/v1/organizations/org1/members/member1/role",
        json={"role": "moderator"},
    )
    assert res.status_code == 200
    assert any(item["user_id"] == "member1" and item["role"] == "moderator" for item in fake_db.org_members.items)


def test_member_cannot_change_role():
    app.dependency_overrides[get_current_active_user] = override_member_user
    res = client.patch(
        "/api/v1/organizations/org1/members/admin1/role",
        json={"role": "member"},
    )
    assert res.status_code == 403
    assert any(item["user_id"] == "admin1" and item["role"] == "admin" for item in fake_db.org_members.items)
    app.dependency_overrides[get_current_active_user] = override_admin_user
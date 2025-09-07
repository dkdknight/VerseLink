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

from middleware import auth as auth_middleware
from routers import auth as auth_router


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


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.revoked_tokens = FakeCollection()


def override_get_database():
    return fake_db


fake_db = FakeDatabase()
# Monkeypatch get_database in modules
auth_middleware.get_database = override_get_database
auth_router.get_database = override_get_database

app = FastAPI()
app.include_router(auth_router.router, prefix="/api/v1/auth")
client = TestClient(app)


def test_token_cannot_be_reused_after_logout():
    # Create test admin and get token
    res = client.post("/api/v1/auth/create-test-admin")
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Token works before logout
    res = client.get(
        "/api/v1/auth/check", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200

    # Logout and revoke token
    res = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200

    # Token should no longer grant access
    res = client.get(
        "/api/v1/auth/check", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 401
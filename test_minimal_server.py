#!/usr/bin/env python3
"""
Minimal server test to identify middleware issues
"""

import sys
sys.path.append('/app/backend')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal app
app = FastAPI(title="Minimal Test Server")

# Test adding CORS middleware
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print("✅ CORS middleware added successfully")
except Exception as e:
    print(f"❌ CORS middleware failed: {e}")

# Test adding Discord Events router
try:
    from routers.discord_events import router as discord_events_router
    app.include_router(discord_events_router, prefix="/api/v1/discord/events", tags=["Discord Events"])
    print("✅ Discord Events router added successfully")
except Exception as e:
    print(f"❌ Discord Events router failed: {e}")

@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Minimal server working"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal test server...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
from fastapi import APIRouter
from src.api.v1.endpoints.user_endpoints import router as user_routers
from src.api.v1.endpoints.tenant_endpoints import router as tenant_endpoints
from src.api.v1.endpoints.leave_endpoints import router as leave_endpoints

api_router = APIRouter()

api_router.include_router(tenant_endpoints)
api_router.include_router(user_routers)
api_router.include_router(leave_endpoints)

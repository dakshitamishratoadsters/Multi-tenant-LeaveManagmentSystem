from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from src.db.database import get_db
from src.db.dependencies import require_role
from src.services.tenant_services import TenantServices
from src.schemas.tenant_schema import TenantCreate, TenantUpdate, TenantRead
from src.db.models.user_model import User

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# ======================= CREATE =======================
@router.post("/",response_model=TenantRead)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db)
    
    
):
    service = TenantServices(db)
    return await service.create_tenant(tenant_data)


# ======================= GET ALL =======================
@router.get("/")
async def get_all_tenants(db: AsyncSession = Depends(get_db),
                          user:User=Depends(require_role("SuperAdmin"))):
    service = TenantServices(db)
    return await service.get_all_tenants()


# ======================= GET ONE =======================
@router.get("/{tenant_id}")
async def get_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db), 
                     user:User =Depends(require_role("SuperAdmin","TenantAdmin"))):
    service = TenantServices(db)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


# ======================= UPDATE =======================
@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: uuid.UUID,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
     user:User =Depends(require_role("SuperAdmin","TenantAdmin"))
):
    service = TenantServices(db)
    tenant = await service.update_tenant(tenant_id, tenant_data)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


# ======================= DELETE =======================
@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db), 
                        user:User =Depends(require_role("SuperAdmin"))):
    service = TenantServices(db)
    success = await service.delete_tenant(tenant_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"message": "Tenant deleted successfully"}
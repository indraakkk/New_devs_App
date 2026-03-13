from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import db_pool

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: int = 3,
    year: int = 2024,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID not found for user")

    revenue_data = await get_revenue_summary(property_id, tenant_id, month, year)
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


@router.get("/dashboard/properties")
async def get_tenant_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID not found for user")

    from sqlalchemy import text

    if not db_pool.session_factory:
        await db_pool.initialize()

    if not db_pool.session_factory:
        raise HTTPException(status_code=503, detail="Database unavailable")

    async with db_pool.get_session() as session:
        query = text("""
            SELECT id, name, timezone
            FROM properties
            WHERE tenant_id = :tenant_id
            ORDER BY name
        """)
        result = await session.execute(query, {"tenant_id": tenant_id})
        rows = result.fetchall()

    return [{"id": row.id, "name": row.name, "timezone": row.timezone} for row in rows]

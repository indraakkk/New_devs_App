from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

async def calculate_monthly_revenue(property_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized

async def calculate_total_revenue(property_id: str, tenant_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Aggregates revenue from database for a specific month, using property timezone.
    """
    try:
        from app.core.database_pool import db_pool
        from sqlalchemy import text

        if not db_pool.session_factory:
            await db_pool.initialize()

        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        async with db_pool.get_session() as session:
            if month < 12:
                end_month, end_year = month + 1, year
            else:
                end_month, end_year = 1, year + 1

            start_date = f"{year}-{month:02d}-01"
            end_date = f"{end_year}-{end_month:02d}-01"

            query = text("""
                SELECT
                    r.property_id,
                    COALESCE(SUM(r.total_amount), 0) as total_revenue,
                    COUNT(*) as reservation_count
                FROM reservations r
                JOIN properties p ON r.property_id = p.id AND r.tenant_id = p.tenant_id
                WHERE r.property_id = :property_id
                  AND r.tenant_id = :tenant_id
                  AND (r.check_in_date AT TIME ZONE p.timezone) >= CAST(:start_date AS timestamp)
                  AND (r.check_in_date AT TIME ZONE p.timezone) < CAST(:end_date AS timestamp)
                GROUP BY r.property_id
            """)

            result = await session.execute(query, {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "start_date": start_date,
                "end_date": end_date,
            })
            row = result.fetchone()

            if row and row.reservation_count > 0:
                total_revenue = Decimal(str(row.total_revenue))
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": str(total_revenue),
                    "currency": "USD",
                    "count": row.reservation_count,
                }
            else:
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": "0.00",
                    "currency": "USD",
                    "count": 0,
                }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        raise

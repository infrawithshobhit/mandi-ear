"""
Database connection and operations for Price Discovery Service
"""

import asyncpg
import redis.asyncio as redis
from typing import Optional, List, Dict, Any
import structlog
import json
from datetime import datetime, timedelta

from models import PricePoint, PriceData, MandiInfo, DataSource, ValidationResult

logger = structlog.get_logger()

# Global connection pools
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

async def init_db():
    """Initialize database connections"""
    global pg_pool, redis_client
    
    try:
        # PostgreSQL connection pool
        pg_pool = await asyncpg.create_pool(
            "postgresql://mandi_user:mandi_pass@localhost:5432/mandi_ear",
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("PostgreSQL connection pool created")
        
        # Redis connection
        redis_client = redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Create tables if they don't exist
        await create_tables()
        
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
        raise

async def close_db():
    """Close database connections"""
    global pg_pool, redis_client
    
    if pg_pool:
        await pg_pool.close()
        logger.info("PostgreSQL connection pool closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

async def create_tables():
    """Create database tables"""
    if not pg_pool:
        raise RuntimeError("Database pool not initialized")
    
    async with pg_pool.acquire() as conn:
        # Data sources table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                type VARCHAR NOT NULL,
                url VARCHAR,
                api_key VARCHAR,
                update_frequency INTEGER NOT NULL,
                reliability_score FLOAT DEFAULT 0.8,
                is_active BOOLEAN DEFAULT TRUE,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Mandis table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mandis (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                address VARCHAR,
                district VARCHAR,
                state VARCHAR NOT NULL,
                country VARCHAR DEFAULT 'India',
                operating_hours VARCHAR,
                facilities JSONB,
                average_daily_volume FLOAT,
                reliability_score FLOAT DEFAULT 0.8,
                contact_info JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Price points table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS price_points (
                id VARCHAR PRIMARY KEY,
                commodity VARCHAR NOT NULL,
                variety VARCHAR,
                price FLOAT NOT NULL,
                unit VARCHAR DEFAULT 'quintal',
                quantity FLOAT,
                quality VARCHAR DEFAULT 'average',
                mandi_id VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                source_id VARCHAR NOT NULL,
                confidence FLOAT DEFAULT 0.8,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (mandi_id) REFERENCES mandis(id),
                FOREIGN KEY (source_id) REFERENCES data_sources(id)
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_price_points_commodity ON price_points(commodity)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_price_points_timestamp ON price_points(timestamp)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_price_points_mandi ON price_points(mandi_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mandis_state ON mandis(state)")

async def store_price_point(price_point: PricePoint) -> bool:
    """Store a price point in the database"""
    if not pg_pool:
        raise RuntimeError("Database pool not initialized")
    
    try:
        async with pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO price_points (
                    id, commodity, variety, price, unit, quantity, quality,
                    mandi_id, timestamp, source_id, confidence, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    price = EXCLUDED.price,
                    quantity = EXCLUDED.quantity,
                    confidence = EXCLUDED.confidence,
                    metadata = EXCLUDED.metadata
            """, 
                price_point.id, price_point.commodity, price_point.variety,
                price_point.price, price_point.unit, price_point.quantity,
                price_point.quality.value, price_point.mandi_id,
                price_point.timestamp, price_point.source_id,
                price_point.confidence, json.dumps(price_point.metadata) if price_point.metadata else None
            )
        return True
    except Exception as e:
        logger.error("Failed to store price point", error=str(e), price_point_id=price_point.id)
        return False

async def get_commodity_prices(commodity: str, state: Optional[str] = None, limit: int = 100) -> List[PriceData]:
    """Get current prices for a commodity"""
    if not pg_pool:
        raise RuntimeError("Database pool not initialized")
    
    try:
        async with pg_pool.acquire() as conn:
            query = """
                SELECT pp.*, m.name as mandi_name, m.latitude, m.longitude,
                       m.address, m.district, m.state, m.country
                FROM price_points pp
                JOIN mandis m ON pp.mandi_id = m.id
                WHERE pp.commodity = $1
            """
            params = [commodity]
            
            if state:
                query += " AND m.state = $2"
                params.append(state)
            
            query += " ORDER BY pp.timestamp DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            # Group by mandi and create PriceData objects
            mandi_prices = {}
            for row in rows:
                mandi_id = row['mandi_id']
                if mandi_id not in mandi_prices:
                    mandi_info = MandiInfo(
                        id=mandi_id,
                        name=row['mandi_name'],
                        location={
                            "latitude": row['latitude'],
                            "longitude": row['longitude'],
                            "address": row['address'],
                            "district": row['district'],
                            "state": row['state'],
                            "country": row['country']
                        }
                    )
                    mandi_prices[mandi_id] = {
                        'mandi': mandi_info,
                        'prices': []
                    }
                
                price_point = PricePoint(
                    id=row['id'],
                    commodity=row['commodity'],
                    variety=row['variety'],
                    price=row['price'],
                    unit=row['unit'],
                    quantity=row['quantity'],
                    quality=row['quality'],
                    mandi_id=row['mandi_id'],
                    timestamp=row['timestamp'],
                    source_id=row['source_id'],
                    confidence=row['confidence'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                mandi_prices[mandi_id]['prices'].append(price_point)
            
            # Convert to PriceData objects
            result = []
            for mandi_data in mandi_prices.values():
                prices = mandi_data['prices']
                if prices:
                    current_price = prices[0].price  # Most recent
                    price_values = [p.price for p in prices]
                    
                    price_data = PriceData(
                        commodity=commodity,
                        current_price=current_price,
                        price_range={
                            "min": min(price_values),
                            "max": max(price_values),
                            "avg": sum(price_values) / len(price_values)
                        },
                        unit=prices[0].unit,
                        mandi=mandi_data['mandi'],
                        last_updated=prices[0].timestamp,
                        price_points=prices[:10]  # Limit to recent points
                    )
                    result.append(price_data)
            
            return result
            
    except Exception as e:
        logger.error("Failed to get commodity prices", error=str(e))
        return []

async def get_mandis(state: Optional[str] = None) -> List[MandiInfo]:
    """Get list of mandis"""
    if not pg_pool:
        raise RuntimeError("Database pool not initialized")
    
    try:
        async with pg_pool.acquire() as conn:
            if state:
                rows = await conn.fetch("SELECT * FROM mandis WHERE state = $1", state)
            else:
                rows = await conn.fetch("SELECT * FROM mandis")
            
            mandis = []
            for row in rows:
                mandi = MandiInfo(
                    id=row['id'],
                    name=row['name'],
                    location={
                        "latitude": row['latitude'],
                        "longitude": row['longitude'],
                        "address": row['address'],
                        "district": row['district'],
                        "state": row['state'],
                        "country": row['country']
                    },
                    operating_hours=row['operating_hours'],
                    facilities=json.loads(row['facilities']) if row['facilities'] else [],
                    average_daily_volume=row['average_daily_volume'],
                    reliability_score=row['reliability_score'],
                    contact_info=json.loads(row['contact_info']) if row['contact_info'] else None
                )
                mandis.append(mandi)
            
            return mandis
            
    except Exception as e:
        logger.error("Failed to get mandis", error=str(e))
        return []

async def cache_price_data(key: str, data: Any, ttl: int = 300):
    """Cache data in Redis"""
    if not redis_client:
        return
    
    try:
        await redis_client.setex(key, ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.error("Failed to cache data", error=str(e), key=key)

async def get_cached_data(key: str) -> Optional[Any]:
    """Get cached data from Redis"""
    if not redis_client:
        return None
    
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error("Failed to get cached data", error=str(e), key=key)
        return None
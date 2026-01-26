"""
Cache Manager for offline data storage and retrieval
"""

import aiosqlite
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import hashlib
import gzip
import pickle

from models import (
    CachedData, DataType, PriorityLevel, CacheStatistics, 
    CacheEntry, QueryResult, OfflineQuery
)

logger = structlog.get_logger()

class CacheManager:
    """Manages local data caching for offline access"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.db_path = cache_dir / "cache.db"
        self.data_dir = cache_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.db_connection: Optional[aiosqlite.Connection] = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    async def initialize(self):
        """Initialize the cache database and tables"""
        try:
            self.db_connection = await aiosqlite.connect(str(self.db_path))
            await self._create_tables()
            logger.info("Cache manager initialized", db_path=str(self.db_path))
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            raise
    
    async def close(self):
        """Close database connection"""
        if self.db_connection:
            await self.db_connection.close()
            logger.info("Cache manager closed")
    
    async def _create_tables(self):
        """Create necessary database tables"""
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                size_bytes INTEGER NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                metadata TEXT,
                file_path TEXT
            )
        """)
        
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                query_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        await self.db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_type ON cache_entries(data_type)
        """)
        
        await self.db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_priority ON cache_entries(priority)
        """)
        
        await self.db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
        """)
        
        await self.db_connection.commit()
    
    async def cache_data(
        self, 
        data_type: DataType, 
        content: Dict[str, Any], 
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Cache data with specified priority and expiration"""
        try:
            # Generate unique ID
            content_hash = hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()
            cache_id = f"{data_type.value}_{content_hash}_{int(datetime.now().timestamp())}"
            
            # Serialize and compress data
            serialized_data = pickle.dumps(content)
            compressed_data = gzip.compress(serialized_data)
            
            # Save to file
            file_path = self.data_dir / f"{cache_id}.gz"
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
            
            # Calculate expiration
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            # Store metadata in database
            now = datetime.now()
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO cache_entries 
                (id, data_type, priority, created_at, updated_at, expires_at, 
                 size_bytes, metadata, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_id, data_type.value, priority.value, now, now, expires_at,
                len(compressed_data), json.dumps(metadata or {}), str(file_path)
            ))
            
            await self.db_connection.commit()
            logger.debug("Data cached", cache_id=cache_id, data_type=data_type.value)
            return cache_id
            
        except Exception as e:
            logger.error("Failed to cache data", error=str(e))
            raise
    
    async def get_cached_data(
        self, 
        cache_id: str, 
        update_access: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached data by ID"""
        try:
            self.cache_stats["total_requests"] += 1
            
            # Get metadata from database
            cursor = await self.db_connection.execute("""
                SELECT file_path, expires_at FROM cache_entries 
                WHERE id = ?
            """, (cache_id,))
            
            row = await cursor.fetchone()
            if not row:
                self.cache_stats["misses"] += 1
                return None
            
            file_path, expires_at = row
            
            # Check expiration
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                await self._remove_expired_entry(cache_id)
                self.cache_stats["misses"] += 1
                return None
            
            # Load data from file
            if not Path(file_path).exists():
                logger.warning("Cache file missing", cache_id=cache_id, file_path=file_path)
                self.cache_stats["misses"] += 1
                return None
            
            with open(file_path, 'rb') as f:
                compressed_data = f.read()
            
            serialized_data = gzip.decompress(compressed_data)
            content = pickle.loads(serialized_data)
            
            # Update access statistics
            if update_access:
                await self.db_connection.execute("""
                    UPDATE cache_entries 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE id = ?
                """, (datetime.now(), cache_id))
                await self.db_connection.commit()
            
            self.cache_stats["hits"] += 1
            return content
            
        except Exception as e:
            logger.error("Failed to get cached data", error=str(e), cache_id=cache_id)
            self.cache_stats["misses"] += 1
            return None
    
    async def get_cached_prices(
        self, 
        commodity: str, 
        state: Optional[str] = None, 
        max_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get cached price data for a commodity"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            cursor = await self.db_connection.execute("""
                SELECT id, file_path FROM cache_entries 
                WHERE data_type = ? AND created_at > ?
                ORDER BY created_at DESC
            """, (DataType.PRICE_DATA.value, cutoff_time))
            
            results = []
            async for row in cursor:
                cache_id, file_path = row
                data = await self.get_cached_data(cache_id, update_access=False)
                
                if data and data.get('commodity') == commodity:
                    if not state or data.get('state') == state:
                        results.append(data)
            
            return results
            
        except Exception as e:
            logger.error("Failed to get cached prices", error=str(e))
            return []
    
    async def get_cached_mandis(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cached mandi information"""
        try:
            cursor = await self.db_connection.execute("""
                SELECT id FROM cache_entries 
                WHERE data_type = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC
            """, (DataType.MANDI_INFO.value, datetime.now()))
            
            results = []
            async for row in cursor:
                cache_id = row[0]
                data = await self.get_cached_data(cache_id, update_access=False)
                
                if data:
                    if not state or data.get('state') == state:
                        results.append(data)
            
            return results
            
        except Exception as e:
            logger.error("Failed to get cached mandis", error=str(e))
            return []
    
    async def cache_query(self, query: OfflineQuery) -> str:
        """Cache a query for offline processing"""
        try:
            query_hash = hashlib.md5(
                f"{query.query_type}_{json.dumps(query.parameters, sort_keys=True)}".encode()
            ).hexdigest()
            
            expires_at = datetime.now() + timedelta(hours=24)  # Queries expire in 24 hours
            
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO query_cache 
                (query_hash, query_type, parameters, result_data, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query_hash, query.query_type, json.dumps(query.parameters),
                json.dumps({"status": "pending"}), datetime.now(), expires_at
            ))
            
            await self.db_connection.commit()
            return query_hash
            
        except Exception as e:
            logger.error("Failed to cache query", error=str(e))
            raise
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get basic cache statistics"""
        try:
            cursor = await self.db_connection.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(size_bytes) as total_size,
                    data_type,
                    COUNT(*) as type_count
                FROM cache_entries 
                WHERE expires_at IS NULL OR expires_at > ?
                GROUP BY data_type
            """, (datetime.now(),))
            
            stats = {
                "total_entries": 0,
                "total_size_bytes": 0,
                "entries_by_type": {},
                "hit_rate": 0.0,
                "miss_rate": 0.0
            }
            
            async for row in cursor:
                if len(row) == 4:  # Grouped results
                    _, _, data_type, type_count = row
                    stats["entries_by_type"][data_type] = type_count
                else:  # Total results
                    stats["total_entries"] = row[0] or 0
                    stats["total_size_bytes"] = row[1] or 0
            
            # Calculate hit/miss rates
            total_requests = self.cache_stats["total_requests"]
            if total_requests > 0:
                stats["hit_rate"] = self.cache_stats["hits"] / total_requests
                stats["miss_rate"] = self.cache_stats["misses"] / total_requests
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get cache statistics", error=str(e))
            return {}
    
    async def get_detailed_statistics(self) -> CacheStatistics:
        """Get detailed cache statistics"""
        try:
            # Basic stats
            cursor = await self.db_connection.execute("""
                SELECT COUNT(*), SUM(size_bytes) FROM cache_entries 
                WHERE expires_at IS NULL OR expires_at > ?
            """, (datetime.now(),))
            
            row = await cursor.fetchone()
            total_entries = row[0] or 0
            total_size_bytes = row[1] or 0
            
            # Stats by type
            cursor = await self.db_connection.execute("""
                SELECT data_type, COUNT(*), SUM(size_bytes) FROM cache_entries 
                WHERE expires_at IS NULL OR expires_at > ?
                GROUP BY data_type
            """, (datetime.now(),))
            
            entries_by_type = {}
            size_by_type = {}
            
            async for row in cursor:
                data_type, count, size = row
                entries_by_type[data_type] = count
                size_by_type[data_type] = (size or 0) / (1024 * 1024)  # Convert to MB
            
            # Most accessed entries
            cursor = await self.db_connection.execute("""
                SELECT id, data_type, access_count FROM cache_entries 
                WHERE expires_at IS NULL OR expires_at > ?
                ORDER BY access_count DESC LIMIT 10
            """, (datetime.now(),))
            
            most_accessed = []
            async for row in cursor:
                most_accessed.append({
                    "id": row[0],
                    "data_type": row[1],
                    "access_count": row[2]
                })
            
            # Expired entries count
            cursor = await self.db_connection.execute("""
                SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?
            """, (datetime.now(),))
            
            expired_count = (await cursor.fetchone())[0] or 0
            
            # Calculate rates
            total_requests = self.cache_stats["total_requests"]
            hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
            miss_rate = self.cache_stats["misses"] / total_requests if total_requests > 0 else 0.0
            
            return CacheStatistics(
                total_entries=total_entries,
                total_size_mb=total_size_bytes / (1024 * 1024),
                entries_by_type=entries_by_type,
                size_by_type=size_by_type,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                sync_success_rate=1.0,  # TODO: Calculate from sync history
                expired_entries=expired_count,
                most_accessed=most_accessed
            )
            
        except Exception as e:
            logger.error("Failed to get detailed statistics", error=str(e))
            raise
    
    async def clear_cache(
        self, 
        older_than_hours: Optional[int] = None, 
        data_type: Optional[str] = None
    ) -> int:
        """Clear cached data based on criteria"""
        try:
            conditions = []
            params = []
            
            if older_than_hours:
                cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
                conditions.append("created_at < ?")
                params.append(cutoff_time)
            
            if data_type:
                conditions.append("data_type = ?")
                params.append(data_type)
            
            # Get entries to delete
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor = await self.db_connection.execute(
                f"SELECT id, file_path FROM cache_entries WHERE {where_clause}",
                params
            )
            
            deleted_count = 0
            async for row in cursor:
                cache_id, file_path = row
                
                # Delete file
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning("Failed to delete cache file", file_path=file_path, error=str(e))
                
                deleted_count += 1
            
            # Delete database entries
            await self.db_connection.execute(
                f"DELETE FROM cache_entries WHERE {where_clause}",
                params
            )
            
            await self.db_connection.commit()
            logger.info("Cache cleared", deleted_count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to clear cache", error=str(e))
            raise
    
    async def _remove_expired_entry(self, cache_id: str):
        """Remove an expired cache entry"""
        try:
            # Get file path
            cursor = await self.db_connection.execute(
                "SELECT file_path FROM cache_entries WHERE id = ?", (cache_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                file_path = row[0]
                Path(file_path).unlink(missing_ok=True)
            
            # Delete from database
            await self.db_connection.execute(
                "DELETE FROM cache_entries WHERE id = ?", (cache_id,)
            )
            await self.db_connection.commit()
            
        except Exception as e:
            logger.error("Failed to remove expired entry", error=str(e), cache_id=cache_id)
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up all expired cache entries"""
        try:
            cursor = await self.db_connection.execute("""
                SELECT id FROM cache_entries WHERE expires_at < ?
            """, (datetime.now(),))
            
            expired_ids = [row[0] async for row in cursor]
            
            for cache_id in expired_ids:
                await self._remove_expired_entry(cache_id)
            
            logger.info("Expired entries cleaned up", count=len(expired_ids))
            return len(expired_ids)
            
        except Exception as e:
            logger.error("Failed to cleanup expired entries", error=str(e))
            return 0
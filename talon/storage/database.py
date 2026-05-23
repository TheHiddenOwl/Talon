import zlib
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, LargeBinary
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    collector: Mapped[str] = mapped_column(String(64))
    data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    raw_response: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    proxy_used: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self, db_path: str):
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save(
        self,
        domain: str,
        collector: str,
        data: Any,
        raw_response: Optional[str] = None,
        status_code: Optional[int] = None,
        proxy_used: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        async with AsyncSession(self.engine) as session:
            compressed_raw = None
            if raw_response:
                compressed_raw = zlib.compress(raw_response.encode("utf-8"))

            finding = Finding(
                domain=domain,
                collector=collector,
                data=data,
                raw_response=compressed_raw,
                status_code=status_code,
                proxy_used=proxy_used,
                duration_ms=duration_ms,
            )
            session.add(finding)
            await session.commit()

    async def get_findings(self, domain: Optional[str] = None) -> list[Finding]:
        # Basic retrieval for reporting
        from sqlalchemy import select
        async with AsyncSession(self.engine) as session:
            query = select(Finding)
            if domain:
                query = query.where(Finding.domain == domain)
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def decompress_response(finding: Finding) -> Optional[str]:
        if finding.raw_response:
            return zlib.decompress(finding.raw_response).decode("utf-8")
        return None

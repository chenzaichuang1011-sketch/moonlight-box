"""
月光宝盒 - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.evaluate import router as evaluate_router
from app.api.crawl import router as crawl_router
from app.api.monitor import router as monitor_router
from app.api.scraped import router as scraped_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 {settings.APP_NAME} 启动中...")
    logger.info(f"   环境: {settings.APP_ENV}")
    logger.info(f"   调试: {settings.DEBUG}")

    # 配置代理（如果有设置的话）
    import os
    proxy_url = os.environ.get("CBG_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy_url:
        from app.services.crawler.proxy import configure_proxy
        configure_proxy(fixed_proxy=proxy_url)
        logger.info(f"   代理已配置: {proxy_url}")
    else:
        logger.info("   代理未配置（直连模式）")

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 数据库迁移：为新字段自动 ALTER TABLE（SQLite 安全）
    from app.core.database import SessionLocal
    _migrate_db(engine)
    
    logger.info("   数据库表已创建/更新")

    # 创建默认管理员
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models import User
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                coins=9999,
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            logger.info("   默认管理员已创建")
    finally:
        db.close()

    logger.info(f"✅ {settings.APP_NAME} 启动完成!")

    # 初始化抓取服务（从 Edge 浏览器加载 Cookie）
    try:
        from app.services.scraper.service import scraper_service
        await scraper_service.init()
        logger.info(f"🕷️  抓取服务已初始化（Cookie 从浏览器加载）")
    except Exception as e:
        logger.warning(f"抓取服务初始化失败（非致命）: {e}")

    # 启动采集服务（定时从CBG抓取角色到数据库）
    try:
        from app.services.collector.collector_service import collector_service
        await collector_service.init()
        await collector_service.start()
        logger.info(f"📥 采集服务已启动（每30分钟定时抓取）")
    except Exception as e:
        logger.warning(f"采集服务启动失败（非致命）: {e}")

    # 启动监控引擎
    try:
        from app.services.monitor.engine import get_monitor_engine
        from app.api.crawl import get_crawler
        monitor_engine = await get_monitor_engine()
        crawler = await get_crawler()
        await monitor_engine.init(crawler)
        logger.info(f"📡 监控引擎已启动")
    except Exception as e:
        logger.warning(f"监控引擎启动失败（非致命）: {e}")

    yield

    logger.info(f"👋 {settings.APP_NAME} 关闭中...")

    # 关闭采集服务
    try:
        from app.services.collector.collector_service import collector_service
        await collector_service.stop()
    except Exception:
        pass

    # 关闭监控引擎
    try:
        from app.services.monitor.engine import get_monitor_engine
        monitor_engine = await get_monitor_engine()
        await monitor_engine.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description="梦幻西游藏宝阁角色估价平台",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(evaluate_router)
app.include_router(crawl_router)
app.include_router(monitor_router)
app.include_router(scraped_router)

# 前端静态文件（必须在 mount 之前定义）
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(frontend_dir / "index.html"))

    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


def _migrate_db(engine):
    """
    SQLite 安全迁移：检查并添加缺失的列
    SQLite 的 ALTER TABLE ADD COLUMN 只能在末尾追加，且不能有默认值约束冲突
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # monitor_tasks 新增字段
    _mt_new_cols = {
        'cultivation_min': 'INTEGER',
        'pet_cultivation_min': 'INTEGER',
        'no_level_min': 'INTEGER',
        'no_level_equip_level_min': 'INTEGER',
        'never_wear_min': 'INTEGER',
        'never_wear_equip_level_min': 'INTEGER',
        'equip_hole_min': 'INTEGER',
        'lingshi_jinglian_min': 'INTEGER',
        'pet_types': 'TEXT DEFAULT "[]"',
        'pet_skill_count_min': 'INTEGER',
        'pet_lingxing_min': 'INTEGER',
        'has_clothes': 'BOOLEAN',
        'has_xiangrui': 'BOOLEAN',
        'has_no_level': 'BOOLEAN',
        'is_first_listing': 'BOOLEAN',
    }
    
    if 'monitor_tasks' in inspector.get_table_names():
        existing = {c['name'] for c in inspector.get_columns('monitor_tasks')}
        with engine.begin() as conn:
            for col_name, col_type in _mt_new_cols.items():
                if col_name not in existing:
                    try:
                        conn.execute(text(f'ALTER TABLE monitor_tasks ADD COLUMN {col_name} {col_type}'))
                        logger.info(f"   迁移: monitor_tasks 添加 {col_name}")
                    except Exception as e:
                        logger.warning(f"   迁移跳过 monitor_tasks.{col_name}: {e}")
    
    # push_records 新增字段
    _pr_new_cols = {
        'total_cultivation': 'INTEGER',
        'pet_total_cultivation': 'INTEGER',
        'no_level_count': 'INTEGER',
        'no_level_equip_level': 'INTEGER',
        'never_wear_count': 'INTEGER',
        'equip_gem_level': 'INTEGER',
        'lingshi_jinglian_level': 'INTEGER',
        'clothes_names': 'TEXT DEFAULT "[]"',
        'xiangrui_names': 'TEXT DEFAULT "[]"',
        'pet_type_labels': 'TEXT DEFAULT "[]"',
        'highlight_tags': 'TEXT DEFAULT "[]"',
        'role_summary': 'VARCHAR(500)',
    }
    
    if 'push_records' in inspector.get_table_names():
        existing = {c['name'] for c in inspector.get_columns('push_records')}
        with engine.begin() as conn:
            for col_name, col_type in _pr_new_cols.items():
                if col_name not in existing:
                    try:
                        conn.execute(text(f'ALTER TABLE push_records ADD COLUMN {col_name} {col_type}'))
                        logger.info(f"   迁移: push_records 添加 {col_name}")
                    except Exception as e:
                        logger.warning(f"   迁移跳过 push_records.{col_name}: {e}")

    # scraped_roles 新增字段（2026-04-07）
    _sr_new_cols = {
        'is_pushed': 'BOOLEAN DEFAULT 0',
        'is_pushed_at': 'TIMESTAMP',
        'listing_time': 'TIMESTAMP',
    }

    if 'scraped_roles' in inspector.get_table_names():
        existing = {c['name'] for c in inspector.get_columns('scraped_roles')}
        with engine.begin() as conn:
            for col_name, col_type in _sr_new_cols.items():
                if col_name not in existing:
                    try:
                        conn.execute(text(f'ALTER TABLE scraped_roles ADD COLUMN {col_name} {col_type}'))
                        logger.info(f"   迁移: scraped_roles 添加 {col_name}")
                    except Exception as e:
                        logger.warning(f"   迁移跳过 scraped_roles.{col_name}: {e}")

    # 新增表确认日志（2026-04-07：已售/在售物品库）
    _new_tables = ['sold_roles', 'sold_pets', 'sold_equips', 'listed_pets', 'listed_equips']
    for table_name in _new_tables:
        if table_name in inspector.get_table_names():
            logger.info(f"   表已就绪: {table_name}")
        else:
            logger.warning(f"   表缺失: {table_name}（将在下次启动时创建）")



---
name: fastapi-patterns
description: FastAPI patterns for building Python backends — routing, dependency injection, middleware, background tasks, and async patterns. Load when building FastAPI applications.
---

# FastAPI Patterns

## App Setup
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI(title="API", lifespan=lifespan)
```

## Router Pattern (one per resource)
```python
# app/api/v1/routes/items.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.item import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    return await item_service.create(item)
```

## Dependency Injection
```python
from fastapi import Depends
from app.core.config import Settings, get_settings

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
async def list_items(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    pass
```

## Settings (pydantic-settings)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"

settings = Settings()
```

## Background Tasks
```python
from fastapi import BackgroundTasks

@router.post("/process")
async def process(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_heavy_task, arg1, arg2)
    return {"status": "queued"}
```

## Error Handling
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

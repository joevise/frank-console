# -*- coding: utf-8 -*-
"""FastAPI app entry."""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.db import Base, engine
from app.api import auth, chat, watchlist, reports, market, brief, analyze

settings = get_settings()
app = FastAPI(title='Frank Console API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(watchlist.router)
app.include_router(reports.router)
app.include_router(market.router)
app.include_router(brief.router)
app.include_router(analyze.router)

@app.on_event('startup')
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'frank-console-backend'}

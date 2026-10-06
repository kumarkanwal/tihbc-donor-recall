"""Aggregate router for version 1 API resources."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.campaigns import campaign_router, enrollment_router
from app.api.v1.content_series import router as content_series_router
from app.api.v1.demo import router as demo_router
from app.api.v1.donor_batches import router as donor_batches_router
from app.api.v1.follow_ups import router as follow_up_router
from app.api.v1.media import router as media_router
from app.api.v1.metrics import metrics_router, reports_router
from app.api.v1.simulator import router as simulator_router
from app.api.v1.users import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(campaign_router)
router.include_router(content_series_router)
router.include_router(demo_router)
router.include_router(donor_batches_router)
router.include_router(follow_up_router)
router.include_router(media_router)
router.include_router(metrics_router)
router.include_router(reports_router)
router.include_router(users_router)
router.include_router(simulator_router)
router.include_router(enrollment_router)

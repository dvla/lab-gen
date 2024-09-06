from fastapi.routing import APIRouter

from lab_gen.web.api import conversation, feedback, files, models, monitoring, prompts, structured


api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(models.router)
api_router.include_router(conversation.router)
api_router.include_router(prompts.router)
api_router.include_router(structured.router)
api_router.include_router(files.router)
api_router.include_router(feedback.router)

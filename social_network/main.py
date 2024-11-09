from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from social_network.auth.router import auth_router
from social_network.dependencies import init_neo4j
from social_network.users.router import user_router

app = FastAPI(
    title="Rubyan",
    description="Sua rede social preferida de cara nova (ou não)",
    dependencies=[Depends(init_neo4j)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
# app.include_router(debit_router)
# app.include_router(category_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

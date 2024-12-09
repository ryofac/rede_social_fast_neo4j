from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from social_network.auth.router import auth_router
from social_network.dependencies import lifespan
from social_network.posts.router import post_router
from social_network.users.router import user_router

app = FastAPI(
    title="Rubyan",
    description="Sua rede social preferida de cara nova (ou não)",
    lifespan=lifespan,
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(post_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

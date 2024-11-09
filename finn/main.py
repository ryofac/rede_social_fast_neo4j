from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from social_network.auth.router import auth_router
from social_network.categories.router import category_router

app = FastAPI(
    title="Rubyan",
    description="Sua rede social preferida de cara nova (ou não)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(debit_router)
app.include_router(category_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

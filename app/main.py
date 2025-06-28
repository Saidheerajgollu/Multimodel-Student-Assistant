from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents, questions

app = FastAPI(title="Multimodal Study Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(questions.router, prefix="/api", tags=["questions"])

@app.get("/")
async def root():
    return {"message": "Welcome to Multimodal Study Assistant API"}

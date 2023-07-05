from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from handler import inference_handler

class InferenceRequestSchema(BaseModel):
    question: str

class InferenceResponseSchema(BaseModel):
    answer: str
    sources: List[str]

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_methods=["*"], allow_headers=["*"], allow_origins=["*"])


@app.post("/inference", response_model=InferenceResponseSchema)
def inference_endpoint_handler(body: InferenceRequestSchema):
    return inference_handler(body.question)

from fastapi.staticfiles import StaticFiles

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 404:
            response = await super().get_response('.', scope)
        return response

app.mount('/', SPAStaticFiles(directory='folder', html=True), name='Helpdesk Website')

if __name__ == "__main__":
    uvicorn.run(app, port=80, host="0.0.0.0")

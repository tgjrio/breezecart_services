from pydantic import BaseModel, HttpUrl

class URLSubmission(BaseModel):
    user_id: str
    session_id: str
    url: HttpUrl

class SubmissionRequest(BaseModel):
    user_id: str
    session_id: str
    url: HttpUrl

class ChatGptRequest(BaseModel):
    user_id: str
    session_id: str
    recipe_name: str
    redis_key: str
    phase: str

class URLSubmission(BaseModel):
    user_id: str
    session_id: str
    url: HttpUrl

class SubmissionRequest(BaseModel):
    user_id: str
    session_id: str
    url: HttpUrl
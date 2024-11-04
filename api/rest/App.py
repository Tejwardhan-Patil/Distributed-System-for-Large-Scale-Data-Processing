from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
import logging
import time
import uuid
from datetime import datetime, timedelta
import jwt

# Initialize app
app = FastAPI(title="Large-Scale Data Processing API")

# CORS setup for cross-origin requests
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://website.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "a_secure_secret_key_for_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# In-memory users database for authentication
fake_users_db = {
    "nate": {
        "username": "nate",
        "full_name": "Nate Smith",
        "email": "nate@website.com",
        "hashed_password": "fakehashedpassword",
        "disabled": False,
    },
    "paul": {
        "username": "paul",
        "full_name": "Paul Adams",
        "email": "paul@website.com",
        "hashed_password": "fakehashedpassword",
        "disabled": False,
    },
}

# Utility function to verify JWT token
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication for login
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or user["hashed_password"] != password:
        return False
    return UserInDB(**user)

# Generate JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token generation route
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get current authenticated user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return UserInDB(**user)

# API Endpoints
class DataItem(BaseModel):
    id: Optional[str]
    name: str
    value: str

# In-memory data storage
data_store = {}

@app.get("/data", response_model=List[DataItem])
async def read_data():
    return list(data_store.values())

@app.get("/data/{item_id}", response_model=DataItem)
async def read_data_item(item_id: str):
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    return data_store[item_id]

@app.post("/data", response_model=DataItem)
async def create_data(item: DataItem):
    item_id = str(uuid.uuid4())
    data_store[item_id] = {"id": item_id, "name": item.name, "value": item.value}
    logger.info(f"Created data with ID: {item_id}")
    return data_store[item_id]

@app.put("/data/{item_id}", response_model=DataItem)
async def update_data(item_id: str, item: DataItem):
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    data_store[item_id] = {"id": item_id, "name": item.name, "value": item.value}
    logger.info(f"Updated data with ID: {item_id}")
    return data_store[item_id]

@app.delete("/data/{item_id}", response_model=dict)
async def delete_data(item_id: str):
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Item not found")
    del data_store[item_id]
    logger.info(f"Deleted data with ID: {item_id}")
    return {"msg": "Deleted successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "Healthy"}

# Middleware to measure request duration
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
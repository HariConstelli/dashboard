from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from authlib.jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, DATE, TIME
from sqlalchemy.orm import sessionmaker, declarative_base, Session

app = FastAPI()
DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/dashboard"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=True)
Base = declarative_base()

# Secret key and JWT config
SECRET_KEY = "hajsj6tsjjs7jskdhh789snksmsbsbnmshgwqwertyui7asdfghjk8zxcvbnm6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme for protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Define the data model for user input
class UserData(BaseModel):
    id: int
    name: str
    email: str
    number: str
    password: str

class Dashboard(BaseModel):
    id : int
    Latitude : int
    Longitude : int
    Altitude : int
    Roll : int
    Speed: int
    Pitch: int
    Yaw: int
    Az: int
    EI: int


class User(Base):
    __tablename__  = 'usertable'
    id = Column(Integer, primary_key= True,autoincrement=True)
    name = Column(String(100))
    email = Column(String(100))
    number = Column(String(100))
    password = Column(String(50))

class Dashboard_table(Base):
    __tablename__ = 'dashboardtable'
    id = Column(Integer, primary_key= True,autoincrement=True)
    Latitude = Column(Integer)
    Longitude = Column(Integer)
    Altitude = Column(Integer)
    Roll = Column(Integer)
    Speed = Column(Integer)
    Pitch = Column(Integer)
    Yaw = Column(Integer)
    Az = Column(Integer)
    EI = Column(Integer)

Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to authenticate user
def authenticate_user(username: str, password: str):
    db = next(get_db())
    user = db.query(User).filter(User.name == username).first()
    if not user or user.password != password:
        return False
    return user

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    header = {"alg": ALGORITHM}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(header,to_encode, SECRET_KEY)

# Login endpoint
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.name})
    return {"access_token": token, "token_type": "bearer"}

def get_access_user(token: str):
    current_time = datetime.now().timestamp()

    decoded = jwt.decode(token, SECRET_KEY)
    exp_time = decoded.get('exp')
    if current_time > exp_time:
        raise HTTPException(status_code=404, detail='Token Expired')
    username = decoded.get('sub')
    if not username:
        raise HTTPException(status_code=400, detail='Username not valid')
    db = next(get_db())
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail='User Not found')
    return user

@app.get("/protected/")
def protected_route(user: UserData = Depends(get_access_user)):
    try:
        
        return {"message": f"Hello, {user.name}! You are authenticated."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/createuser/")
async def create_user(user: UserData, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail=f"User Already existed in database")
        else:
            user_db = User(**user.dict())
            db.add(user_db)
            db.commit()
            db.refresh(user_db)
            return {'detail':f"User Created successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error occured {str(e)}") 
    
@app.post("/createdashboard/")
async def create_dashboard(data : Dashboard, db: Session = Depends(get_db)):
    try:
        dashboard = Dashboard_table(**data.dict())
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        return {'detail': f"Dashboard created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occured: {str(e)}")
  
@app.delete("/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user_db = db.query(User).get(user_id)
        if not user_db:
            raise HTTPException(status_code=400, detail=f"User with {user_id} not found")
        db.delete(user_db)
        db.commit()
        return {'detail': f"user {user_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occcured: {str(e)}")

@app.get("/getuser{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User for user ID {user_id} not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


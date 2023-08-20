from fastapi import FastAPI,Depends,Request,Form,status,HTTPException
from typing import Annotated

from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

#authentication and JWT
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime,  timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext


#binding the models and the database together to create the database 
models.Base.metadata.create_all(bind=engine)

templates=Jinja2Templates(directory="templates")


#authentication
#generate a fake db using openssl rand -hex 32 at the CP
SECRET_KEY=""
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRES_MINUTES=30


#create a db
db={
    'musah':{
        'username':'musah',
        "full_name":'congo musah ',
        'email':'amusahcongo@gmail.com',
        'hashed_password':'',
        'disabled':False

    }
}


#creating a model for the token used in the token endpoint by the user
class Token(BaseModel):
    access_token:str
    token_type:str


class TokenData(BaseModel):
    username:str or None=None


class User(BaseModel):
    username: str
    email: str or None=None
    full_name: str or None=None
    disabled: bool or None=None


class UserInDB(User):
    hashed_password:str 


pwd_context=CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme =OAuth2PasswordBearer(tokenUrl='token')
    

app=FastAPI()

#utility functions to authonticate users and to hash the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password,  hashed_password)

#generate a password hash
def get_password_hash(password):
    return pwd_context.hash(password)

#function that grabs a user from our database
def get_user(db, username:str):
   if username in db:
    user_data =db[username]

    return UserInDB("user_data")

#authenticating user function going to take our db
def authenticate_user(db, username: str, password: str):
    user= get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    return user


#creating or accesing the token JWT
def create_access_token(data:  dict, expires_delta: timedelta or None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.utcnow()+ expires_delta
    else:
        expire=datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"exp": expire})
        encoded_jwt=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt


 
#UPDATING A DEPENDENCY
#writing a few function related to getting our user from the token and creating access token based on login data
async def get_current_user(token:Annotated [str, Depends(oauth2_scheme)]):
    credentials_exception= HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="could not validate credentials",headers={'WWW-Authenticate':"Bearer"})
    
    try:
        #decoding the received token
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str =payload.get("sub")
        if username is None:
            raise credentials_exception
        
        token_data=TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user=get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user
    


#activating or dissable user to login
async def get_current_active_user(current_user:UserInDB= Depends(get_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="inactive user")
    
    return current_user


#UPDATING THE TOKEN
#writing a url/token LOGIN
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data:OAuth2PasswordRequestForm=Depends()):
    user= authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="incorrect username or password", headers={"WWW-Authentication":"Bearer"})
    
    #JWT acces token and returning it
    access_token_expires= timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token= create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type":"bearer"}

 
 #CREATING THE USRES ENDPOINT FOR AUTHENTICATION

@app.get("/user/me", response_model=User)
async def read_users_me(
    current_user:Annotated[User, Depends(get_current_active_user)]
) :
    return current_user



@app.get("/user/me/todolist/", response_model=User)
async def read_users_todolist(
    current_user:Annotated[User, Depends(get_current_active_user)]
) :
    return [{"todo_list":"vee","owner":current_user}]



# dependency
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


#getting all the todo list

#task id, taskname, description and complete status
@app.get("/")
async def home(req: Request):
    todos=db.query(models.Todo).all()
    return templates.TemplateResponse("base.html",{"request": req,"todo_list": todos})


#the post is for the user, the user is trying to add new_todo being the task_name
@app.post('/add')
async def add(req: Request, task_name:str=Form(...), db:Session=Depends(get_db)):
    new_todo=models.Todo(task_name=task_name)
    db.add(new_todo)
    db.commit()
    url=app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


#getting the task_id
@app.get('/update/{todo_id}')
async def add(req: Request, task_id:int, db:Session=Depends(get_db)):

    #Function where you get the instance you want. when it only one task we use filter
    todo=db.query(models.Todo).filter(models.Todo.task_id==task_id).first()
    todo.complete_status=not todo.complete_status
    db.commit()
    url=app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)



#getting the task_description
@app.get("/description /{todo_id}")
async def add(req: Request, task_description:str, db:Session=Depends(get_db)):
    todo=db.query(models.Todo).filter(models.Todo.task_description==task_description).first()
    db.add(todo)
    db.commit()
    url=app.url_path_for("home")
    return  RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/complete_status /{todo_id}")
async def add(req: Request, complete_status:bool, db:Session=Depends(get_db)):
    todo=db.query(models.Todo).filter(models.Todo.complete_status==complete_status).first()
    db.add(todo)
    db.commit()
    url=app.url_path_for("home")
    return  RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)




#deleting the to_do created
@app.get('/delet/{todo_id}')
async def add(req: Request, task_id:int, db:Session=Depends(get_db)):
    todo=db.query(models.Todo).filter(models.Todo.task_id==task_id).first()
    db.delete(todo)
    db.commit()
    url=app.url_path_for("home")
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


pwd= get_password_hash("musah12345")
print(pwd)
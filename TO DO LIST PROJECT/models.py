from sqlalchemy import Boolean,Column,Integer,String
from database  import Base



class Todo(Base):
    __tablename__="todos"

    task_id=Column(Integer, primary_key=True)
    task_name=Column(String(100))
    task_description=Column(String(100))
    complete_status=Column(Boolean, default=False)




    
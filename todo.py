import os

from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime
from typing import List, Optional

# Database URL for PostgreSQL connection
DATABASE_URL = os.environ["DATABASE_URL"]

# SQLAlchemy engine for connecting to the database
engine = create_engine(DATABASE_URL)
# Session maker for database session management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base class for declarative class definitions
Base = declarative_base()

class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True

@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

# Create the database tables
Base.metadata.create_all(bind=engine)

# TaskModel class represents the tasks table in the database
class TaskModel(Base):
    __tablename__ = "tasks"  # Name of the table in the database
    id = Column(Integer, primary_key=True, autoincrement=True)  # Primary key
    title = Column(String, index=True)  # Task title
    create_date = Column(DateTime, nullable=True, server_default=utcnow())  # Creation date
    done_date = Column(DateTime, nullable=True)  # Completion date
    status = Column(String, default="waiting")  # Status of the task

# Creating the database tables
Base.metadata.create_all(bind=engine)

# Task class for request and response models
class Task(BaseModel):
    id: Optional[int] = Field(None, description="The unique ID of the task")
    title: str = Field(None, example="Task description", description="Title of the task")
    create_date: Optional[datetime] = Field(None, description="Creation date of the task")
    done_date: Optional[datetime] = Field(None, example="2023-12-25T00:00:00.000Z", description="Completion date of the task")
    status: Optional[str] = Field(None, example="waiting", description="Current status of the task")

# Dependency function for getting a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app instance
app = FastAPI(title="Task API", version="1.0.0")

# Root endpoint for welcome message
@app.get("/", tags=["tasks"])
async def redirect_tasks():
    return {"message": "Server started"}

# Endpoint to list all tasks or tasks based on specific status
@app.get("/tasks", response_model=List[Task], tags=["tasks"])
async def list_tasks(status: Optional[str] = Query(None, enum=["done", "waiting", "working", "all"]), 
                        db: SessionLocal = Depends(get_db)):
    tasks = db.query(TaskModel).all()
    if status == "all":
        return tasks
    else:
        return [task for task in tasks if task.status == status]

# Endpoint to retrieve a specific task by its ID
@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def get_task(task_id: int, db: SessionLocal = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Endpoint to create a new task
@app.post("/tasks", response_model=Task, tags=["tasks"])
async def create_task(task: Task, db: SessionLocal = Depends(get_db)):
    new_task = TaskModel(**task.dict())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Endpoint to update an existing task
@app.put("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def update_task(task_id: int, task: Task, db: SessionLocal = Depends(get_db)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for var, value in vars(task).items():
        setattr(db_task, var, value) if value else None

    db.commit()
    db.refresh(db_task)
    return db_task

# Endpoint to delete a task
@app.delete("/tasks/{task_id}", tags=["tasks"])
async def delete_task(task_id: int, db: SessionLocal = Depends(get_db)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}

# Main function for running the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

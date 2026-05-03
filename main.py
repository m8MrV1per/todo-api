from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="TeamFlow Student")
templates = Jinja2Templates(directory="templates")

SQLALCHEMY_DATABASE_URL = "sqlite:///./teamflow.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

STUDENT_TEMPLATES = {
    "coursework": [
        {"title": "Поиск источников", "desc": "Найти 10+ статей"},
        {"title": "Введение", "desc": "Актуальность, цель"},
        {"title": "Глава 1 (Теория)", "desc": "Обзор литературы"},
        {"title": "Глава 2 (Практика)", "desc": "Расчеты/Анализ"},
        {"title": "Заключение", "desc": "Выводы + Список лит."},
        {"title": "Антиплагиат", "desc": "Проверка уникальности"}
    ],
    "presentation": [
        {"title": "Структура", "desc": "План слайдов"},
        {"title": "Дизайн", "desc": "Оформление"},
        {"title": "Речь", "desc": "Текст выступления"},
        {"title": "Репетиция", "desc": "Прогон с таймером"}
    ]
}


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")
    team = relationship("Team", back_populates="members")
    user = relationship("User")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    deadline = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    team = relationship("Team", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    task = relationship("Task", back_populates="comments")
    author_user = relationship("User")


class Invitation(Base):
    __tablename__ = "invitations"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    target_user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    team = relationship("Team")
    sender = relationship("User", foreign_keys=[sender_id])
    target = relationship("User", foreign_keys=[target_user_id])


Base.metadata.create_all(bind=engine)


# 🔹 PYDANTIC MODELS
class UserCreate(BaseModel): username: str; password: str


class UserLogin(BaseModel): username: str; password: str


class TeamCreate(BaseModel):
    name: str
    template: Optional[str] = None
    creator_id: int


class TaskCreate(BaseModel): title: str; description: Optional[str] = None; assigned_to: Optional[int] = None; deadline: \
Optional[str] = None


class TaskUpdate(BaseModel): is_done: Optional[bool] = None


class CommentCreate(BaseModel): text: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(p): return pwd_context.hash(p)


def verify_password(p, h): return pwd_context.verify(p, h)


def check_membership(team_id: int, user_id: int, db: Session):
    if not db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first():
        raise HTTPException(403, "Вы не состоите в этой команде")


@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "Имя занято")
    new = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(new);
    db.commit();
    db.refresh(new)
    return {"id": new.id, "username": new.username}


@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.username == user.username).first()
    if not u or not verify_password(user.password, u.hashed_password):
        raise HTTPException(401, "Неверный логин/пароль")
    return {"user_id": u.id, "username": u.username}


@app.get("/api/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404, "User not found")
    return {"id": u.id, "username": u.username}


@app.post("/api/teams")
def create_team(team_data: TeamCreate, db: Session = Depends(get_db)):
    team = Team(name=team_data.name, created_by=team_data.creator_id)
    db.add(team);
    db.commit();
    db.refresh(team)
    db.add(TeamMember(team_id=team.id, user_id=team_data.creator_id, role="admin"))

    if team_data.template and team_data.template in STUDENT_TEMPLATES:
        for t in STUDENT_TEMPLATES[team_data.template]:
            db.add(Task(team_id=team.id, title=t["title"], description=t["desc"], created_by=team_data.creator_id))
    db.commit()
    return {"team_id": team.id}


@app.get("/api/teams")
def get_my_teams(user_id: int, db: Session = Depends(get_db)):
    members = db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
    team_ids = [m.team_id for m in members]
    return db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else []


@app.get("/api/teams/{team_id}/members")
def get_members(team_id: int, user_id: int, db: Session = Depends(get_db)):
    check_membership(team_id, user_id, db)
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        result.append({"id": m.user_id, "username": u.username if u else "Unknown"})
    return result


@app.post("/api/teams/{team_id}/invite")
def invite_user(team_id: int, target_user_id: int, requester_id: int, db: Session = Depends(get_db)):
    check_membership(team_id, requester_id, db)
    if not db.query(Team).filter(Team.id == team_id).first(): raise HTTPException(404, "Team not found")
    if not db.query(User).filter(User.id == target_user_id).first(): raise HTTPException(404, "User not found")
    if db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == target_user_id).first():
        raise HTTPException(400, "User already in team")
    if db.query(Invitation).filter(Invitation.team_id == team_id, Invitation.target_user_id == target_user_id,
                                   Invitation.status == "pending").first():
        raise HTTPException(400, "Invitation already sent")

    inv = Invitation(team_id=team_id, sender_id=requester_id, target_user_id=target_user_id)
    db.add(inv);
    db.commit()
    return {"msg": "Invitation sent"}


@app.get("/api/invitations")
def get_my_invitations(user_id: int, db: Session = Depends(get_db)):
    invites = db.query(Invitation).filter(Invitation.target_user_id == user_id, Invitation.status == "pending").all()
    result = []
    for inv in invites:
        team = db.query(Team).filter(Team.id == inv.team_id).first()
        sender = db.query(User).filter(User.id == inv.sender_id).first()
        result.append(
            {"id": inv.id, "team_name": team.name, "sender_name": sender.username, "sender_id": inv.sender_id})
    return result


@app.post("/api/invitations/{invite_id}/{action}")
def handle_invitation(invite_id: int, action: str, user_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invitation).filter(Invitation.id == invite_id).first()
    if not inv or inv.target_user_id != user_id or inv.status != "pending":
        raise HTTPException(400, "Invalid invitation")
    inv.status = "accepted" if action == "accept" else "rejected"
    if action == "accept":
        db.add(TeamMember(team_id=inv.team_id, user_id=user_id, role="member"))
    db.commit()
    return {"msg": f"Invitation {action}ed"}


@app.get("/api/teams/{team_id}/tasks")
def get_tasks(team_id: int, user_id: int, db: Session = Depends(get_db)):
    check_membership(team_id, user_id, db)
    tasks = db.query(Task).filter(Task.team_id == team_id).all()
    result = []
    for t in tasks:
        assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
        result.append({"id": t.id, "title": t.title, "assigned_to": t.assigned_to,
                       "assignee_name": assignee.username if assignee else None, "deadline": t.deadline,
                       "is_done": t.is_done})
    return result


@app.post("/api/teams/{team_id}/tasks")
def create_task(team_id: int, task: TaskCreate, user_id: int, db: Session = Depends(get_db)):
    check_membership(team_id, user_id, db)
    new = Task(team_id=team_id, title=task.title, description=task.description, assigned_to=task.assigned_to,
               deadline=task.deadline, created_by=user_id)
    db.add(new);
    db.commit();
    db.refresh(new)
    return new


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(404, "Not found")
    if update.is_done is not None: task.is_done = update.is_done
    db.commit()
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(404, "Not found")
    db.delete(task);
    db.commit()
    return {"msg": "Deleted"}


@app.get("/api/tasks/{task_id}/comments")
def get_comments(task_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at).all()
    return [{"id": c.id, "text": c.text, "author": db.query(User).filter(User.id == c.user_id).first().username,
             "created_at": c.created_at} for c in comments]


@app.post("/api/tasks/{task_id}/comments")
def add_comment(task_id: int, comment: CommentCreate, user_id: int, db: Session = Depends(get_db)):
    new = Comment(task_id=task_id, user_id=user_id, text=comment.text)
    db.add(new);
    db.commit();
    db.refresh(new)
    return new


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")


if __name__ == "__main__":
    import uvicorn

    print("🟢 Server: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
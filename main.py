from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import json
import os

app = FastAPI()
DATA_FILE = "tasks.json"

# 🔹 Подключаем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🔹 Модели данных
class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool

# 🔹 Инициализация файла
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write("[]")

def load_tasks():
    """Загружает задачи как обычные словари (dict), а не Pydantic-модели"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        save_tasks([])
        return []

def save_tasks(tasks):
    """Сохраняет список словарей (dict) — они отлично сериализуются в JSON"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# 🔹 Главная страница
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# 🔹 Получить все задачи
@app.get("/tasks", response_model=list[TaskOut])
def get_tasks():
    return load_tasks()  # возвращаем список dict — FastAPI сам превратит в модели

# 🔹 Добавить задачу
@app.post("/tasks", response_model=TaskOut)
def add_task(task: TaskCreate):
    tasks = load_tasks()
    # 🔹 Превращаем модель в словарь и добавляем id
    new_task_dict = task.model_dump()
    new_task = {"id": len(tasks) + 1, **new_task_dict}
    tasks.append(new_task)
    save_tasks(tasks)  # сохраняем список словарей — теперь работает!
    return new_task

# 🔹 Удалить задачу
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    tasks = load_tasks()
    updated = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == len(updated):
        raise HTTPException(status_code=404, detail="Задача не найдена")
    save_tasks(updated)
    return {"message": f"Задача {task_id} удалена"}

if __name__ == "__main__":
    print("🟢 Запускаю сервер...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
from fastapi import FastAPI
import uvicorn
import json
import os

app = FastAPI()
DATA_FILE = "tasks.json"

# Создаём файл, если его нет
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def load_tasks():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

@app.get("/")
def home():
    return {"message": "API списка задач работает!"}

@app.get("/tasks")
def get_tasks():
    return load_tasks()

@app.post("/tasks")
def add_task(task: dict):
    tasks = load_tasks()
    new_task = {"id": len(tasks) + 1, "title": task.get("title", "Без названия"), "done": False}
    tasks.append(new_task)
    save_tasks(tasks)
    return {"message": "Задача добавлена", "task": new_task}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return {"message": f"Задача {task_id} удалена"}

if __name__ == "__main__":
    print("🟢 Запускаю сервер...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
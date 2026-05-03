# fix_encoding.py
html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Focus Tasks</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-grad: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
      --card-bg: rgba(255, 255, 255, 0.85);
      --shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
      --primary: #4F46E5;
      --danger: #EF4444;
      --text: #1F2937;
      --text-muted: #6B7280;
    }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg-grad);
      min-height: 100vh;
      margin: 0;
      display: flex;
      justify-content: center;
      padding: 40px 20px;
      color: var(--text);
    }
    .container { width: 100%; max-width: 500px; }
    h1 { text-align: center; font-weight: 700; color: var(--text); margin-bottom: 30px; font-size: 2rem; }
    .input-group {
      background: var(--card-bg);
      padding: 15px;
      border-radius: 16px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 25px;
    }
    .row { display: flex; gap: 10px; }
    input[type="text"] {
      flex: 1;
      padding: 12px 16px;
      border: 2px solid transparent;
      background: #F3F4F6;
      border-radius: 10px;
      font-size: 16px;
      outline: none;
    }
    input[type="text"]:focus {
      background: #fff;
      border-color: var(--primary);
      box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
    }
    input[type="date"] {
      padding: 10px;
      border: 2px solid transparent;
      background: #F3F4F6;
      border-radius: 10px;
      cursor: pointer;
    }
    button.add-btn {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
    }
    button.add-btn:hover { background: #4338CA; }
    .search-bar { margin-bottom: 20px; position: relative; }
    .search-bar input {
      width: 100%;
      padding: 12px 16px;
      padding-left: 40px;
      border: none;
      border-radius: 12px;
      background: rgba(255,255,255,0.6);
    }
    .search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); opacity: 0.4; }
    ul { list-style: none; padding: 0; }
    li {
      background: var(--card-bg);
      padding: 16px;
      margin-bottom: 12px;
      border-radius: 14px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
      display: flex;
      align-items: center;
      gap: 12px;
      animation: popIn 0.4s ease;
    }
    li.removing { animation: slideOut 0.6s forwards; pointer-events: none; }
    .checkbox { width: 22px; height: 22px; border-radius: 6px; cursor: pointer; accent-color: var(--primary); }
    .content { flex: 1; }
    .title { font-weight: 500; font-size: 16px; margin-bottom: 4px; }
    .badge { font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 6px; display: inline-block; }
    .badge.green { background: #D1FAE5; color: #065F46; }
    .badge.yellow { background: #FEF3C7; color: #92400E; }
    .badge.red { background: #FEE2E2; color: #991B1B; }
    .badge.none { background: #F3F4F6; color: #6B7280; }
    .delete-btn { background: transparent; border: none; color: #9CA3AF; font-size: 20px; cursor: pointer; }
    .delete-btn:hover { color: var(--danger); }
    #toast-container { position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 1000; }
    .toast { background: #1F2937; color: white; padding: 12px 20px; border-radius: 8px; font-size: 14px; animation: slideIn 0.3s ease; }
    @keyframes popIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
    @keyframes slideOut { to { opacity: 0; transform: translateX(50px); margin: 0; padding: 0; } }
    @keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
    .empty-state { text-align: center; color: var(--text-muted); margin-top: 40px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>⚡ Focus Tasks</h1>
    <div class="input-group">
      <div class="row">
        <input type="text" id="titleInput" placeholder="Что нужно сделать?" autofocus />
        <input type="date" id="dateInput" />
      </div>
      <button class="add-btn" onclick="addTask()">Добавить задачу</button>
    </div>
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" placeholder="Поиск задач..." oninput="filterTasks()" />
    </div>
    <ul id="taskList"></ul>
    <div id="emptyState" class="empty-state" style="display:none;"><p>Задач нет. Наслаждайся! 🌴</p></div>
  </div>
  <div id="toast-container"></div>
  <script>
    const API = "";
    let allTasks = [];
    async function loadTasks() {
      const res = await fetch(API + "/tasks");
      allTasks = await res.json();
      render(allTasks);
    }
    function render(tasks) {
      const list = document.getElementById("taskList");
      const empty = document.getElementById("emptyState");
      list.innerHTML = "";
      tasks.sort((a, b) => {
        if (!a.deadline) return 1;
        if (!b.deadline) return -1;
        return new Date(a.deadline) - new Date(b.deadline);
      });
      if (tasks.length === 0) { empty.style.display = "block"; return; }
      empty.style.display = "none";
      tasks.forEach(t => {
        const li = document.createElement("li");
        const info = getDateInfo(t.deadline);
        li.innerHTML = '<input type="checkbox" class="checkbox" onclick="completeTask(this, ' + t.id + ')">' +
          '<div class="content"><div class="title">' + escapeHtml(t.title) + '</div>' +
          '<span class="badge ' + info.color + '">' + info.text + '</span></div>' +
          '<button class="delete-btn" onclick="deleteTask(this, ' + t.id + ')">✕</button>';
        list.appendChild(li);
      });
    }
    function filterTasks() {
      const q = document.getElementById("searchInput").value.toLowerCase();
      render(allTasks.filter(t => t.title.toLowerCase().includes(q)));
    }
    function getDateInfo(deadline) {
      if (!deadline) return { text: "Без срока", color: "none" };
      const today = new Date(); today.setHours(0,0,0,0);
      const diff = Math.ceil((new Date(deadline) - today) / (1000*60*60*24));
      if (diff < 0) return { text: "Просрочено (" + Math.abs(diff) + " дн.)", color: "red" };
      if (diff === 0) return { text: "🔥 Сегодня", color: "red" };
      if (diff === 1) return { text: "⚠️ Завтра", color: "yellow" };
      return { text: "Осталось " + diff + " дн.", color: "green" };
    }
    async function completeTask(el, id) {
      el.closest('li').classList.add('removing');
      showToast("Выполнено! ✅");
      await new Promise(r => setTimeout(r, 600));
      await fetch(API + "/tasks/" + id, { method: 'DELETE' });
      loadTasks();
    }
    async function deleteTask(el, id) {
      el.closest('li').classList.add('removing');
      showToast("Удалено 🗑️");
      await new Promise(r => setTimeout(r, 600));
      await fetch(API + "/tasks/" + id, { method: 'DELETE' });
      loadTasks();
    }
    async function addTask() {
      const title = document.getElementById("titleInput").value;
      const date = document.getElementById("dateInput").value;
      if (!title) return showToast("Введите название ⚠️", "error");
      await fetch(API + "/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, deadline: date || null })
      });
      document.getElementById("titleInput").value = "";
      document.getElementById("dateInput").value = "";
      showToast("Добавлено! 🚀");
      loadTasks();
    }
    function showToast(msg, type = "success") {
      const t = document.createElement("div");
      t.className = "toast";
      t.textContent = msg;
      if (type === "error") t.style.background = "#EF4444";
      document.getElementById("toast-container").appendChild(t);
      setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 3000);
    }
    function escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }
    document.getElementById("titleInput").addEventListener("keypress", e => { if (e.key === "Enter") addTask(); });
    loadTasks();
  </script>
</body>
</html>'''

# Сохраняем с UTF-8
with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Файл создан с правильной кодировкой UTF-8!")
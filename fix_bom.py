# fix_bom.py
html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Focus Tasks</title>
  <style>
    :root {
      --primary: #4F46E5;
      --bg-grad: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
      --card-bg: rgba(255, 255, 255, 0.9);
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg-grad);
      min-height: 100vh;
      margin: 0;
      display: flex;
      justify-content: center;
      padding: 40px 20px;
    }
    .container { width: 100%; max-width: 500px; }
    h1 { text-align: center; margin-bottom: 30px; }
    .input-group {
      background: var(--card-bg);
      padding: 20px;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      margin-bottom: 25px;
    }
    .row { display: flex; gap: 10px; margin-bottom: 10px; }
    input[type="text"] {
      flex: 1;
      padding: 12px;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      font-size: 16px;
    }
    input[type="date"] {
      padding: 12px;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
    }
    button {
      width: 100%;
      padding: 12px;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
    }
    button:hover { background: #4338CA; }
    .search-bar { margin-bottom: 20px; }
    .search-bar input {
      width: 100%;
      padding: 12px;
      border: none;
      border-radius: 12px;
      background: rgba(255,255,255,0.7);
    }
    ul { list-style: none; padding: 0; }
    li {
      background: var(--card-bg);
      padding: 16px;
      margin-bottom: 12px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    li.removing { opacity: 0; transform: translateX(50px); transition: all 0.6s; }
    .checkbox { width: 20px; height: 20px; accent-color: var(--primary); }
    .content { flex: 1; }
    .title { font-weight: 500; margin-bottom: 4px; }
    .badge {
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 6px;
      display: inline-block;
    }
    .badge.green { background: #D1FAE5; color: #065F46; }
    .badge.yellow { background: #FEF3C7; color: #92400E; }
    .badge.red { background: #FEE2E2; color: #991B1B; }
    .badge.none { background: #F3F4F6; color: #6B7280; }
    .delete-btn {
      background: transparent;
      border: none;
      color: #9CA3AF;
      font-size: 20px;
      cursor: pointer;
    }
    .delete-btn:hover { color: #EF4444; }
    .toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1F2937;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      animation: slideIn 0.3s;
    }
    @keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
    .empty { text-align: center; color: #6B7280; margin-top: 40px; }
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
      <button onclick="addTask()">Добавить задачу</button>
    </div>
    <div class="search-bar">
      <input type="text" id="searchInput" placeholder="🔍 Поиск задач..." oninput="filterTasks()" />
    </div>
    <ul id="taskList"></ul>
    <div id="emptyState" class="empty" style="display:none;">Задач нет 🌴</div>
  </div>
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
    function showToast(msg) {
      const t = document.createElement("div");
      t.className = "toast";
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(() => t.remove(), 3000);
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

# 🔹 Сохраняем с BOM (Byte Order Mark) для Windows
with open('static/index.html', 'w', encoding='utf-8-sig') as f:
    f.write(html_content)

print("✅ Файл создан с UTF-8 BOM!")
print("✅ Теперь перезапусти сервер и очисти кэш браузера!")
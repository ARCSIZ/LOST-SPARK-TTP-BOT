<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель | Зарегистрированные игроки</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .scrollbar-thin::-webkit-scrollbar { width: 6px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: #1f2937; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
    </style>
</head>
<body class="min-h-screen bg-gray-900 text-white">
    <!-- Навбар -->
    <nav class="bg-gray-800/80 backdrop-blur-xl border-b border-gray-700 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-4">
                    <div class="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        </svg>
                    </div>
                    <h1 class="text-xl font-bold">Админ-панель</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-gray-400 text-sm">Всего игроков: <span class="text-white font-semibold">{{ players|length }}</span></span>
                    <a href="/logout" class="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg transition flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                        </svg>
                        <span>Выйти</span>
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Фильтры и поиск -->
        <div class="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-6 border border-gray-700">
            <div class="flex flex-col lg:flex-row gap-4">
                <!-- Поиск -->
                <div class="flex-1">
                    <label class="block text-gray-400 text-sm mb-2">Поиск по никнейму</label>
                    <div class="relative">
                        <input type="text" id="searchInput" placeholder="Введите никнейм..." 
                            class="w-full px-4 py-3 pl-10 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition">
                        <svg class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                </div>
                <!-- Фильтр по категории -->
                <div class="lg:w-72">
                    <label class="block text-gray-400 text-sm mb-2">Фильтр по категории</label>
                    <select id="categoryFilter" 
                        class="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500 transition">
                        <option value="">Все категории</option>
                        <option value="none">Без категории</option>
                        {% for cat in categories %}
                        <option value="{{ cat.id }}">{{ cat.name }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            
            <!-- Категории (теги) -->
            <div class="mt-4 flex flex-wrap gap-2">
                <button onclick="filterByCategory('')" class="category-tag px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-full text-sm transition" data-category="">
                    Все
                </button>
                {% for cat in categories %}
                <button onclick="filterByCategory('{{ cat.id }}')" 
                    class="category-tag px-3 py-1.5 rounded-full text-sm transition hover:opacity-80" 
                    data-category="{{ cat.id }}"
                    style="background-color: {{ cat.color }}20; color: {{ cat.color }}; border: 1px solid {{ cat.color }}50;">
                    {{ cat.name }}
                </button>
                {% endfor %}
            </div>
        </div>

        <!-- Управление категориями -->
        <div class="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-6 border border-gray-700">
            <h2 class="text-lg font-semibold mb-4 flex items-center">
                <svg class="w-5 h-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                Управление категориями
            </h2>
            <div class="flex flex-wrap gap-4">
                <form id="addCategoryForm" class="flex gap-2 flex-wrap">
                    <input type="text" id="newCategoryName" placeholder="Название категории" required
                        class="px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition">
                    <input type="color" id="newCategoryColor" value="#6366F1" 
                        class="w-12 h-10 rounded-lg cursor-pointer border border-gray-600">
                    <button type="submit" class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                        </svg>
                        <span>Добавить</span>
                    </button>
                </form>
            </div>
            <div class="mt-4 flex flex-wrap gap-2" id="categoryList">
                {% for cat in categories %}
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm" style="background-color: {{ cat.color }}20; border: 1px solid {{ cat.color }}50;">
                    <span style="color: {{ cat.color }}">{{ cat.name }}</span>
                    <button onclick="deleteCategory('{{ cat.id }}')" class="text-red-400 hover:text-red-300 transition">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Таблица игроков -->
        <div class="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 overflow-hidden">
            <div class="overflow-x-auto scrollbar-thin">
                <table class="w-full">
                    <thead class="bg-gray-700/50">
                        <tr>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Игрок</th>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Steam ID</th>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Категория</th>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Дата регистрации</th>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Биография</th>
                            <th class="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Действия</th>
                        </tr>
                    </thead>
                    <tbody id="playersTable" class="divide-y divide-gray-700">
                        {% for user_id, player in players.items() %}
                        <tr class="player-row hover:bg-gray-700/30 transition" 
                            data-nickname="{{ player.nickname|lower }}" 
                            data-category="{{ player.category or 'none' }}">
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    <div class="w-10 h-10 bg-purple-600/30 rounded-full flex items-center justify-center text-purple-400 font-semibold">
                                        {{ player.nickname[0]|upper }}
                                    </div>
                                    <div class="ml-4">
                                        <div class="text-sm font-medium text-white">{{ player.nickname }}</div>
                                        <div class="text-sm text-gray-400">ID: {{ user_id }}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <code class="px-2 py-1 bg-gray-700 rounded text-sm text-green-400">{{ player.steam_id }}</code>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <select onchange="updateCategory('{{ user_id }}', this.value)" 
                                    class="px-3 py-1.5 bg-gray-700/50 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-purple-500 transition">
                                    <option value="" {% if not player.category %}selected{% endif %}>Без категории</option>
                                    {% for cat in categories %}
                                    <option value="{{ cat.id }}" {% if player.category == cat.id %}selected{% endif %}>{{ cat.name }}</option>
                                    {% endfor %}
                                </select>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                {{ player.registered_at[:10] if player.registered_at else 'N/A' }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <a href="{{ player.google_doc }}" target="_blank" 
                                    class="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 rounded-lg text-sm transition inline-flex items-center space-x-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                                    </svg>
                                    <span>Открыть</span>
                                </a>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <button onclick="deletePlayer('{{ user_id }}')" 
                                    class="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg text-sm transition inline-flex items-center space-x-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                    </svg>
                                    <span>Удалить</span>
                                </button>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" class="px-6 py-12 text-center text-gray-400">
                                <svg class="w-12 h-12 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <p>Нет зарегистрированных игроков</p>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Поиск
        document.getElementById('searchInput').addEventListener('input', filterPlayers);
        document.getElementById('categoryFilter').addEventListener('change', filterPlayers);

        function filterPlayers() {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const category = document.getElementById('categoryFilter').value;
            
            document.querySelectorAll('.player-row').forEach(row => {
                const nickname = row.dataset.nickname;
                const rowCategory = row.dataset.category;
                
                const matchesSearch = nickname.includes(search);
                const matchesCategory = !category || rowCategory === category || (category === 'none' && rowCategory === 'none');
                
                row.style.display = matchesSearch && matchesCategory ? '' : 'none';
            });
        }

        function filterByCategory(category) {
            document.getElementById('categoryFilter').value = category;
            filterPlayers();
        }

        // Обновление категории игрока
        async function updateCategory(userId, category) {
            try {
                const response = await fetch('/api/player/category', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, category: category })
                });
                if (response.ok) {
                    const row = document.querySelector(`select[onchange*="${userId}"]`).closest('tr');
                    if (row) row.dataset.category = category || 'none';
                }
            } catch (e) {
                console.error('Ошибка:', e);
            }
        }

        // Удаление игрока
        async function deletePlayer(userId) {
            if (!confirm('Вы уверены, что хотите удалить этого игрока?')) return;
            
            try {
                const response = await fetch('/api/player/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId })
                });
                if (response.ok) {
                    location.reload();
                }
            } catch (e) {
                console.error('Ошибка:', e);
            }
        }

        // Добавление категории
        document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('newCategoryName').value;
            const color = document.getElementById('newCategoryColor').value;
            
            try {
                const response = await fetch('/api/category/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, color })
                });
                if (response.ok) {
                    location.reload();
                }
            } catch (e) {
                console.error('Ошибка:', e);
            }
        });

        // Удаление категории
        async function deleteCategory(categoryId) {
            if (!confirm('Вы уверены, что хотите удалить эту категорию?')) return;
            
            try {
                const response = await fetch('/api/category/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category_id: categoryId })
                });
                if (response.ok) {
                    location.reload();
                }
            } catch (e) {
                console.error('Ошибка:', e);
            }
        }
    </script>
</body>
</html>

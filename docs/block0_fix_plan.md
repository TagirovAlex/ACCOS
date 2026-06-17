# Block 0 — Module System Core: План доработок

## Статус
Скелет реализован, НЕ интегрирован в приложение.

### Что уже есть (работает)
- BaseModule, ModuleSettingDef, MenuItemDef — датаклассы корректны
- ModuleRegistry (Singleton) — register, get_module, get_all_modules, _topological_sort
- ModuleSetting DB model — id, user_id, module_name, key, value, unique constraint
- ModuleSettingsRepository — CRUD (get_global, set_global, list_global, delete_global, get_user_setting, list_user_settings)
- module_admin.py — GET/PUT/DELETE `/admin/modules/{name}/settings`
- 6 модулей-заглушек: ChatModule, ComfyUIModule, RAGModule, WebFetchModule, DocScraperModule, FileModule

### Что не работает
- `register_all(app)` никогда не вызывается — маршрутизация модулей мёртвая
- `startup_all()` / `shutdown_all()` не вызываются в lifespan
- 5 модулей имеют двойную регистрацию роутов (и через модуль, и напрямую в main.py)
- 7 групп роутов не обёрнуты в модули (auth, user, orchestration, admin, help, templates, compute)

## План исправлений

### P1 —必须先 сделать (блокирующее)
1. Создать недостающие модули: AuthModule, UserModule, AdminModule, OrchestrationModule, HelpModule, TemplatesModule, ComputeModule
2. Убрать двойную регистрацию из main.py — оставить только модульную
3. Вызвать `_registry.register_all(app)` в main.py
4. Добавить `_registry.startup_all()` / `shutdown_all()` в lifespan

### P2 — Важно
5. Добавить `created_at` / `updated_at` в ModuleSetting model + миграция
6. Убрать дублирование `require_admin` — использовать общий из dependencies.py
7. Исправить приведение типов value (str→int/bool для number/boolean)

### P3 — Опционально (когда потребуется)
8. Реализовать `discover_modules()` для автосканирования
9. Добавить `get_settings_schema()` на DocScraperModule и FileModule
10. Добавить `get_admin_menu()` / `get_user_menu()` на все модули

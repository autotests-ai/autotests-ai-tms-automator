# Pages (e2e target)

Страницы — каталог `frontend/` в репозитории. Резолв через `baseUrl` / `basePath` в `config/*.properties`.

| Harness | Файл | Путь (local HTTP) |
|---------|------|-------------------|
| Login | `frontend/login.html` | `/login.html` (+ `allure-shell.css`, `allure-shell.js`) |
| Header | `frontend/header.html` | `/header.html` |

PO открывают страницы фиксированными путями: `open("/login.html")`, `open("/header.html")`.

## Local HTTP (рекомендуется)

```bash
cd frontend
python -m http.server 3000
```

`local.properties`: `baseUrl=http://localhost:3000/`.

## file:// preview

Symlink `tests-java/app-path-local` → `../frontend` (rule `frontend-preview`).

**Только login, без сервера:** в `local.properties` закомментировать `baseUrl`, раскомментировать `basePath=../frontend`. Header-тесты не пройдут (module fetch).

## Prod

`one-page-form-prod.properties`: `baseUrl=https://qa-guru.github.io/one-page-form/` — тот же `open("/login.html")`.

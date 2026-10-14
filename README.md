# TOHU BILIM (tohu_portal)

Офлайн-платформа для урока: sapak (урок), synag (тест), QR-вход учеников, результаты класса.

Репозиторий: [kurbanovvgit-creator/tohu_portal](https://github.com/kurbanovvgit-creator/tohu_portal)

---

## Что нужно заранее

1. **Python 3.11+** (лучше 3.12 / 3.13)  
   Скачать: https://www.python.org/downloads/  
   При установке включите галочку **Add python.exe to PATH**.
2. **Git** (чтобы клонировать проект)  
   https://git-scm.com/downloads

Проверка в терминале (PowerShell или CMD):

```bash
python --version
git --version
```

---

## Установка (пошагово)

### 1. Скачать проект

```bash
git clone https://github.com/kurbanovvgit-creator/tohu_portal.git
cd tohu_portal
```

### 2. Создать виртуальное окружение

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Если PowerShell ругается на скрипты:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Windows (CMD):**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

В начале строки должно появиться `(venv)`.

### 3. Установить библиотеки

```bash
pip install -r requirements.txt
pip install pillow
```

`pillow` нужен для QR-кода.

### 4. Файл `.env` (необязательно, но удобно)

В корне проекта создайте файл `.env`:

```env
DEBUG=True
SECRET_KEY=любой-длинный-секретный-ключ
GEMINI_API_KEY=
```

`GEMINI_API_KEY` нужен только если используете AI. Для обычного урока можно оставить пустым.

### 5. База данных и админ

```bash
python manage.py migrate
python manage.py createsuperuser
```

Введите логин, email (можно пропустить) и пароль.

### 6. Демо-данные (5 предметов + synag)

```bash
python manage.py seed_hackathon
```

Если учителя ещё нет, создастся аккаунт:

| Логин     | Пароль   | Роль     |
|-----------|----------|----------|
| `mugallym` | `bilim123` | учитель |

---

## Запуск

### Обычный запуск (только компьютер)

```bash
python manage.py runserver
```

Откройте в браузере: http://127.0.0.1:8000/

### Запуск для телефона (одна Wi‑Fi сеть)

```bash
python manage.py runhttps
```

В терминале появятся ссылки, например:

- http://127.0.0.1:8000/
- https://127.0.0.1:8000/
- https://ВАШ_IP:8000/  ← эту открывайте на телефоне

На телефоне при первом входе браузер может предупредить про сертификат — это нормально для локальной разработки (Continue / Продолжить).

Админка: http://127.0.0.1:8000/admin/

---

## Как пользоваться (кратко)

1. Войдите как **учитель** (`/login/`).
2. Откройте **ders / sapak**.
3. Нажмите **Sapagy başlat** — появится код и QR.
4. Ученики сканируют QR или заходят по коду: `/sapak/`.
5. Synag создать: меню **Synag** → выбрать sapak → вопросы → **Ýatda sakla**.  
   Synag появляется на странице sapak.

---

## Частые проблемы

| Проблема | Что сделать |
|----------|-------------|
| `python` не найден | Переустановите Python с галочкой PATH |
| Не активируется `venv` | См. `Set-ExecutionPolicy` выше |
| Телефон не открывает сайт | Один Wi‑Fi с ПК; firewall разрешить Python; брать IP из вывода `runhttps`, не `10.0.x` от Hyper-V |
| Synag «не добавляется» | Обязательно выбрать sapak (или создать новый) перед сохранением |
| Нет курсов | Выполните `python manage.py seed_hackathon` |

---

## Структура (кратко)

```
tohu_portal/
  manage.py          — команды Django
  requirements.txt   — зависимости
  core/              — настройки проекта
  education/         — уроки, synag, сессии, шаблоны
  .env               — секреты (не коммитить)
```

---

## Полезные команды

```bash
python manage.py migrate
python manage.py seed_hackathon
python manage.py runserver
python manage.py runhttps
python manage.py backup_db
```

# Проект Foodgram
Проект Foodgram позволяет пользователям публиковать рецепты, добавлять чужие рецепты в избранное и  подписываться на публикации других авторов. Сервис "Список покупок" позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд и скачивать их.
> Можете прочитать документацию http://chef-nomto.tk/api/docs/
# Установка
* Клонируйте репозиторий и перейдите в клонированную папку.
```bash
git clone https://github.com/Iki-oops/foodgram-project-react.git
cd foodgram-project-react/
```
### Подготовка развертывания приложения
Для работы с проектом в контейнерах должен быть установлен Docker и docker-compose.
### Развертывание приложения
1. Перед запуском проекта нужно создать .env файл в директории ./backend/ и заполнить:
```
DB_NAME=<название вашей базы данных>
POSTGRES_USER=<имя пользователя в postgres>
POSTGRES_PASSWORD=<пароль пользователя>
DB_HOST=db  # Сюда можете прописать localhost, либо оставить, если будете использовать docker-compose
DB_PORT=5432

SECRET_KEY=django-insecure-r@anxhs!l=w3mbn@3#@&17fu%*ek+%#2c1%xm463pxaukk)o=%
```
2. Необходимо запустить сборку контейнеров
```bash
cd infra/
docker-compose up --build
```
3. Необходимо выполнить миграции, собрать статику приложения и создать суперпользователя, для этого запустите скрипт
```bash
docker exec -it infra_backend_1 python manage.py migrate
docker exec -it infra_backend_1 python manage.py collectstatic
docker exec -it infra_backend_1 python manage.py createsuperuser
```
# Технологии
- Python
- Django Rest Framework
- Docker
- postgresql
- nginx
- gunicorn
> Ссылка на сайт - http://chef-nomto.tk/ или http://51.250.9.22/

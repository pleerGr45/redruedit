# Иморты
from flask import Flask, render_template, request, redirect, flash, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import NotFound, InternalServerError
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from os import remove

# Импорты для работы с датой и временем
from datetime import datetime
import pytz

# Импорт модулей для работы с БД
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Создание flask приложения
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4AWDc\n\xec]/'

# Настройка Менеджера логинов
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message = 'Для доступа необходимо осуществить вход в систему'

# Настройка базы данных
engine = create_engine('sqlite:///database.db')
Base = declarative_base()

# Создание модели AUTH


class Auth(Base):
    __tablename__ = 'authorized_users'
    id = Column(Integer, primary_key=True)
    login = Column(String(32), nullable=False, unique=True)
    password = Column(String(32), nullable=False)
    user_name = Column(String(32), nullable=False)
    user_about = Column(String)
    user_birthdate = Column(String)
    date_creation = Column(String)
    user_phone = Column(String)
    user_email = Column(String)
    admin_access = Column(Boolean, default=False)

# Создание модели NEWS


class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    date = Column(String)
    image = Column(String, nullable=True)
    content = Column(String)
    likes = Column(String, nullable=True)


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    owner = Column(String)
    date = Column(String)
    message = Column(String)


# Создание базы данных
Base.metadata.create_all(engine)
# Создание сессий
session = sessionmaker(bind=engine)()
session.rollback()

# Создание класса пользователя


class UserLogin():
    def fromDB(self, user_id):
        self.__user = session.query(Auth).filter_by(id=user_id)
        self.__id = user_id
        return self

    def create(self, user):
        self.__user = user
        self.__id = user.id
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymoys(self):
        return False

    def get_id(self):
        return self.__id

# Обработчик загрузок пользователей


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id)


# Загрузка прав администраторов

with open('admin_access.txt', 'r') as fr:
    admin_list = fr.read().split(',')

for admin in admin_list:
    user = session.query(Auth).filter_by(login=admin).first()
    if user:
        user.admin_access = True

session.commit()

#######################################################################################
#                        ___    ___           ___         _____                       #
#               |\  /|  |___|  |___|  |   |  |___|  \  /    |    |    |               #
#               | \/ |  |   |  |      | | |  |       \/     |    |__  |               #
#               |    |  |   |  |      |_|_|  |       /      |    |__| |               #
#                                                                                     #
#######################################################################################


@app.route("/", methods=['GET', 'POST'])
def home_page():
    # Получение двнных о пользователе
    user_metadata = session.query(Auth).filter_by(
        id=current_user.get_id()).first()

    # Создание новости POST (с доступом администратора)
    if request.method == 'POST' and user_metadata.admin_access:

        # Получение данных из формы
        title = request.form['title']
        date = datetime.now(pytz.timezone('Europe/Moscow')).today()
        file_image = request.files['photo']
        # Сохранение изображения
        file_image.save('static/images/'+file_image.filename)
        content = request.form['content']

        # Добавление новости
        session.add(News(title=title, date=date_format(
            date), image=file_image.filename, content=content, likes=""))
        session.commit()

    # Получение данных о новостях
    ls = []
    for news in list(session.query(News).filter_by()):
        ls.append([news, news.likes.count('+'), news.likes.count('-')])
        print('start', news.likes, 'end')
    ls.reverse()

    # Получение данных о правах пользователя
    rights = user_metadata.admin_access if user_metadata else False

    # Возврат шаблона home_page_html
    return render_template("home_page.html", ls=ls, is_not_void=len(ls), rights=rights)


@app.route("/login", methods=['GET', 'POST'])
def login_page():
    # Если пользователь уже авторизован
    if current_user.is_authenticated:
        # Перенаправление на /profile
        return redirect(url_for('profile_page'))

    # Если POST запрос
    if request.method == 'POST':

        # Получение получение пользователя по логину
        user = session.query(Auth).filter_by(
            login=request.form['login']).first()

        # Проверка на существование пользователя, на сходство паролей
        if user and check_password_hash(user.password, request.form['pass']):
            # Логининг пользователя
            user_login = UserLogin().create(user)
            login_user(user_login, remember=bool(request.form.get('remainme')))
            # Отправка сообщения пользователю об успехе
            flash('Произошёл успешный вход', 'success')
            # Перенаправление на главную страницу /
            return redirect(url_for('home_page'))

        # Отправка сообщения пользователю об ошибке
        flash('Неверная пара логина и пароля', 'error')

    # Возврат шаблона login_page.html
    return render_template("login_page.html")


@app.route("/register", methods=['GET', 'POST'])
def register_page():
    # Если POST запрос
    if request.method == 'POST':

        # Получение данных из формы
        login = request.form['login']
        name = request.form['name']
        password = request.form['pass']
        password_repeat = request.form['pass_repeat']

        # Проверка на соответствие введённых данных
        if len(login) > 4 and len(login) <= 32 and len(name) > 4 and len(name) <= 32\
                and len(password) > 5 and len(password) <= 32 and password == password_repeat:
            # Проверка логина
            if not check_login(login):
                # Генерация скрытого пароля
                pass_hash = generate_password_hash(password)
                # Отправка в базу данных
                datedb = datetime.now(pytz.timezone('Europe/Moscow')).today()
                session.add(
                    Auth(login=login, password=pass_hash, user_name=name, date_creation=date_format(datedb)))
                session.commit()
                # Отправка сообщения пользователю об успехе
                flash('Вы успешно зарегистрированы', 'success')
                # Перевод пользователя в разел /login
                return redirect(url_for('login_page'))
            else:
                # Отправка сообщения пользователю о том, что логин уже занят
                flash('Такой логин уже существует', 'warning')
        else:
            # Отправка сообщения пользователю о том, что пароли не совпадают
            flash('Пароли не совпадают', 'error')

    # Возврат шаблона register_page.html
    return render_template("register_page.html")


@app.route("/community", methods=['GET', 'POST'])
@login_required
def community_page():
    # Создание новости POST
    if request.method == 'POST':
        user_metadata = session.query(Auth).filter_by(
            id=current_user.get_id()).first()
        owner = user_metadata.login
        date = datetime.now(pytz.timezone('Europe/Moscow')).today()
        message = request.form['message']
        session.add(
            Message(owner=owner, date=date_format(date), message=message))
        session.commit()

    ls = list(session.query(Message).filter_by())
    ls.reverse()

    return render_template("community_page.html", ls=ls)


@app.route("/contact_us")
def contact_page():
    # Возврат шаблона contact_page.html
    return render_template("contact_page.html")


@app.route("/about_us")
def about_page():
    # Возврат шаблона about_page.html
    return render_template("about_page.html")


@app.route("/logout")
def logout_page():
    # Выход из системы
    logout_user()
    # Отправка сообщения пользователю об выходе из аккаунта
    flash('Произошёл выход из аккаунта', 'info')
    # Перенаправление на /login
    return redirect(url_for('login_page'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile_page():
    # Получение данных о пользователе
    user_metadata = session.query(Auth).filter_by(
        id=current_user.get_id()).first()

    # Если POST запрос
    if request.method == 'POST':
        # Получение данных с формы и перезапись в БД
        user_metadata.user_name = request.form['user_name']
        user_metadata.user_email = request.form['user_e_mail']
        user_metadata.user_phone = request.form['user_phone']
        user_metadata.user_about = request.form['user_about']
        user_metadata.user_birthdate = request.form['user_birthdate']
        session.commit()

    # Возврат шаблона profile_page.html
    return render_template("profile_page.html", profile=user_metadata)


@app.route("/view_profile/<login>")
def view_profile_page(login):
    # Если логин существует
    if check_login(login):
        # Получение данных о пользователе
        user_metadata = session.query(Auth).filter_by(login=login).first()
        # Возврат шаблона view_profile_page.html
        return render_template("view_profile_page.html", profile=user_metadata)

    # Иначе ошибка 404 NotFoundError
    return abort(404)


@app.route("/delete")
def delete_page():
    # Данные о пользователе
    user_metadata = session.query(Auth).filter_by(
        id=current_user.get_id()).first()

    # Удаление лайков/дизлайков с новостей
    for news in list(session.query(News).filter_by()):
        ls = news.likes
        if user_metadata.login in ls:
            ls = ls.replace('+|'+user_metadata.login+',', '', 1)
            ls = ls.replace('-|'+user_metadata.login+',', '', 1)
        news.likes = ls

    # Удаление поьзователя
    session.delete(user_metadata)
    session.commit()
    logout_user()
    flash('Аккаунт удалён', 'error')

    # Возврат на '/login'
    return redirect(url_for('login_page'))


@app.route("/delete_news/<id>")
def delete_news_page(id):
    # Получение данных о новости
    news = session.query(News).filter_by(id=id).first()

    # Удаление новости
    try:
        remove('static/images/'+news.image)
    except FileNotFoundError:
        # Отправка сообщения пользователю о внутренней ошибке сервера
        flash('Изображение не было найдено', 'warning')

    # Удаление новости
    session.delete(news)
    session.commit()

    # Перенаправление на главную страницу /
    return redirect(url_for('home_page'))


@app.route("/like_news/<id>/<like>")
def like_news_page(id, like):
    # Получение данных о новости
    news = session.query(News).filter_by(id=id).first()

    # Если пользователь авторизован
    if current_user.is_authenticated:
        user_metadata = session.query(Auth).filter_by(
            id=current_user.get_id()).first()
        ls = news.likes

        if user_metadata.login in ls:
            ls = ls.replace('+|'+user_metadata.login,
                            like+'|'+user_metadata.login, 1)
            ls = ls.replace('-|'+user_metadata.login,
                            like+'|'+user_metadata.login, 1)
        else:
            ls += like + '|' + user_metadata.login + ','

        news.likes = ls
        session.commit()
    else:
        # Отправка сообщения поьзователю о том, что ему необходима авторизоваться
        flash('Вы должны быть зарегистрированы', 'info')

    # Перенаправление на главную страницу /
    return redirect(url_for('home_page'))


@app.errorhandler(NotFound)
def not_found_error(error):
    # Возврат шаблона error.html с кодом ошибки 404
    return render_template('error.html', message="Страница не найдена", err_code=404, err=error), 404


@app.errorhandler(InternalServerError)
def internal_error(error):
    # Устранение ошибки сессии
    session.rollback()
    # Возврат шаблона error.html с кодом ошибки 500
    return render_template('error.html', message="Внутренняя ошибка сервера", err_code=500, err=error), 500

#######################################################################################
#        ___     ___    ___        _____                                              #
#       |   |   |   |  |   |      |__|__|  \  /  |   |  | /  |  |   |  /|  |  /|      #
#       |___|   |   |  |   |         |      \/   |---|  |<   |__|   | / |  | / |      #
#      |     |  |___|  |   |         |      /    |   |  | \      |  |/  |  |/  |      #
#                                                                                     #
#######################################################################################

# Метод проверки существования логина


def check_login(login: str) -> bool:
    """
    Метод check_login
    Проверяет наличие данного логина в БД
    Возвращает:
      True - если в пользователь с таким логинов (login: str) уже существет.
      False - если логин свободен
    Пояснение:
      Так как login у авторизованного пользователя уникален, нужна функция, которая проверяет уникальность логина
    """
    return True if session.query(Auth).filter_by(login=login).first() else False


# Метод форматирования даты


def date_format(date) -> str:
    """
    Метод date_format
    Возвращает время в формате: гг-мм-дд
    Добавляет ноль перед числом месяца или дня, если это число < 10
    """
    return "{}-{:02}-{:02}".format(date.year, date.month, date.day)


# Запуск flask приложения
app.run(debug=True)

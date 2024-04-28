# Иморты
from flask import Flask, render_template, request, redirect, flash, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import NotFound, InternalServerError
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
# Импорты для работы с датой и временем
from datetime import datetime
import pytz

# Импорт модулей для работы с БД
from sqlalchemy import create_engine, Column, Integer, String, Text
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

# Создание модели NEWS


class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    post_owner = Column(String)
    date = Column(String)
    content = Column(Text)


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

#######################################################################################
#                        ___    ___           ___         _____                       #
#               |\  /|  |___|  |___|  |   |  |___|  \  /    |    |    |               #
#               | \/ |  |   |  |      | | |  |       \/     |    |__  |               #
#               |    |  |   |  |      |_|_|  |       /      |    |__| |               #
#                                                                                     #
#######################################################################################


@app.route("/", methods=['GET', 'POST'])
def home_page():
    # Создание новости POST
    if request.method == 'POST':
        user_metadata = session.query(Auth).filter_by(
            id=current_user.get_id()).first()
        title = request.form['title']
        date = datetime.now(pytz.timezone('Europe/Moscow')).today()
        content = request.form['content']
        session.add(News(title=title, post_owner=user_metadata.login,
                    date=date_format(date), content=content))
        session.commit()

    ls = list(session.query(News).filter_by())
    ls.reverse()

    # Загрузка шаблона home_page_html
    return render_template("home_page.html", ls=ls)


@app.route("/login", methods=['GET', 'POST'])
def login_page():
    # Если пользователь уже авторизован
    if current_user.is_authenticated:
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
            # Перенаправление на главную страницу
            return redirect(url_for('home_page'))

        # Отправка сообщения пользователю об ошибке
        flash('Неверная пара логина и пароля', 'error')

    # Загрузка шаблона login_page.html
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

    # Загрузка шаблона register_page.html
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
    return render_template("contact_page.html")


@app.route("/about_us")
def about_page():
    return render_template("about_page.html")


@app.route("/logout")
def logout_page():
    logout_user()
    flash('Произошёл выход из аккаунта', 'info')
    return redirect(url_for('login_page'))


@app.route("/delete")
def delete_page():
    session.delete(session.query(Auth).filter_by(
        id=current_user.get_id()).first())
    logout_user()
    flash('Аккаунт удалён', 'error')
    return redirect(url_for('login_page'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile_page():
    user_metadata = session.query(Auth).filter_by(
        id=current_user.get_id()).first()
    if request.method == 'POST':
        user_metadata.user_name = request.form['user_name']
        user_metadata.user_email = request.form['user_e_mail']
        user_metadata.user_phone = request.form['user_phone']
        user_metadata.user_about = request.form['user_about']
        user_metadata.user_birthdate = request.form['user_birthdate']

    return render_template("profile_page.html", profile=user_metadata)


@app.route("/view_profile/<login>")
def view_profile_page(login):
    if check_login(login):
        user_metadata = session.query(Auth).filter_by(login=login).first()
        return render_template("view_profile_page.html", profile=user_metadata)

    return abort(404)


@app.errorhandler(NotFound)
def not_found_error(error):
    return render_template('error.html', message="Страница не найдена", err_code=404, err=error), 404


@app.errorhandler(InternalServerError)
def internal_error(error):
    session.rollback()
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


def date_format(date) -> str:
    """

    """
    return f"{date.year}-{date.month}-{date.day}"


app.run(debug=True)

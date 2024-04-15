#Иморты
from flask import Flask, render_template, request, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
#Импорты для работы с датой и временем
from datetime import datetime
import pytz

#Импорт модулей для работы с БД
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

#Создание flask приложения
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4AWDc\n\xec]/'

#Создание Менеджера логинов

#Настройка базы данных
engine = create_engine('sqlite:///news.db')
Base = declarative_base()

class Auth(Base):
  __tablename__ = 'authorized_users'

  id = Column(Integer, primary_key=True)
  login = Column(String(32), nullable=False, unique=True)
  password = Column(String(32), nullable=False)
  user_name = Column(String(32), nullable=False)
  user_about = Column(String)
  user_birthdate = Column(DateTime(timezone=True))
  date_creation = Column(DateTime(timezone=True), default=datetime.now(pytz.timezone('Europe/Moscow')))

#Создание модели
class News(Base):
  __tablename__ = 'news'

  id = Column(Integer, primary_key=True)
  title = Column(String)
  post_owner = Column(String)
  date = Column(String)
  content = Column(Text)

#Создание базы данных
Base.metadata.create_all(engine)
#Создание сессий
session = sessionmaker(bind=engine)()
session.rollback()

#####################################################################
#               ___    ___           ___         _____              #
#      |\  /|  |___|  |___|  |   |  |___|  \  /    |    |    |      #
#      | \/ |  |   |  |      | | |  |       \/     |    |__  |      #
#      |    |  |   |  |      |_|_|  |       /      |    |__| |      #
#                                                                   #
#####################################################################

@app.route("/", methods=['GET', 'POST'])
def home_page():
    #Создание новости POST
    if request.method == 'POST':
      title = request.form['title']
      post_owner = request.form['post_owner']
      date = f"{datetime.now(pytz.timezone('Europe/Moscow')).today()}"
      content = request.form['content']
      session.add(News(title=title, post_owner=post_owner, date=date, content=content))
      session.commit()
    #Загрузка шаблона home_page_html
    return render_template("home_page.html")

@app.route("/login", methods=['GET', 'POST'])
def login_page():
    return render_template("login_page.html")

@app.route("/register", methods=['GET', 'POST'])
def register_page():
    #Если POST запрос
    if request.method == 'POST':
      
      #Получение данных из формы
      login = request.form['login']
      name = request.form['name']
      password = request.form['pass']
      password_repeat = request.form['pass_repeat']
      
      #Проверка на соответствие введённых данных
      if len(login) > 4 and len(login) <= 32 and len(name) > 4 and len(name) <= 32\
        and len(password) > 5 and len(password) <= 32 and password == password_repeat:
          #Проверка логина
          if check_login(login) == False:
            #Генерация скрытого пароля
            pass_hash = generate_password_hash(password)
            #Отправка в базу данных
            session.add(Auth(login=login, password=pass_hash, user_name=name))
            session.commit()
            #Отправка сообщения пользователю об успехе
            flash('Вы успешно зарегистрированы', 'success')
            #Перевод пользователя в разел /login
            return redirect('/login')
          else:
             #Отправка сообщения пользователю о том, что логин уже занят
             flash('Такой логин уже существует', 'warning')
      else:
         #Отправка сообщения пользователю о том, что пароли не совпадают
         flash('Пароли не совпадают', 'error')
    
    #Загрузка шаблона register_page.html
    return render_template("register_page.html")

def contact_page():
    return render_template("contact_page.html")

#######################################################################################
#        ___     ___    ___        _____                                              #
#       |   |   |   |  |   |      |__|__|  \  /  |   |  | /  |  |   |  /|  |  /|      #
#       |___|   |   |  |   |         |      \/   |---|  |<   |__|   | / |  | / |      #
#      |     |  |___|  |   |         |      /    |   |  | \      |  |/  |  |/  |      #
#                                                                                     #
#######################################################################################

#Метод проверки существования логина
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
    return (True if (session.query(Auth).filter_by(login=login).first() != None) else False)

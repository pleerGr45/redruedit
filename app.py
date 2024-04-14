#Иморты
from flask import Flask, render_template

#Импорт модулей для работы с БД
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

#Создание flask приложения
app = Flask(__name__)

#Настройка базы данных
engine = create_engine('sqlite:///news.db')
Base = declarative_base()

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

@app.route("/")
def home_page():
    return render_template("home_page.html", title="Hello")

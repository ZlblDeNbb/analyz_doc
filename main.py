import streamlit as st
from pages.page_main import main as home_app
from pages.manual_grammar import app as page2_app


# Список страниц
PAGES = {
    "Сопоставление документов": home_app,
}


# Заголовок и описание
st.title("Проект команды Buben Dances")
st.sidebar.title("Навигация")
page = st.sidebar.radio("Перейти на страницу:", list(PAGES.keys()))

# Отображение выбранной страницы
PAGES[page]()

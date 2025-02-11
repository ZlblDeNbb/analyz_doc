import language_tool_python
import streamlit as st
from pages.page_main import extract_text_from_file


def grammar_check(text):
    st.session_state.text=""
    # Инициализация инструмента для проверки грамматики
    tool = language_tool_python.LanguageTool('ru-RU')  # Для русского языка

    # Проверка текста на ошибки
    matches = tool.check(text)
    i = 0
    rule_errors={}
    # Подсветка ошибок в тексте
    for match in matches:
        print(f"Ошибка: {match.ruleId}, {match.message}")
        print(f"Исправление: {match.replacements}")
        print(f"Ошибка в позиции: {match.offset}-{match.offset + match.errorLength}")
        print("------------------------------------------------")
        st.session_state.text += f"\n{match.message}:{match.replacements}\n"

    # Вывод текста с исправлениями
    corrected_text = language_tool_python.utils.correct(text, matches)
    return corrected_text, st.session_state.text


def app():
    st.title("Проверка грамматических ошибок в документах")

    # Пример формы
    st.subheader("Загрузите файл для проверки грамматики")
    comparison_file = st.file_uploader("Загрузите файл для проверки грамматики", type=["pdf", "docx", "txt", "odt"])

    if comparison_file is not None:
        st.write("Файл загружен")
        comparison_text = extract_text_from_file(comparison_file)
        fixed_text, errors=grammar_check(comparison_text)
        st.text_area("Исправленный текст", fixed_text, height=200)
        if errors:
            st.text_area("Замечания к тексту", st.session_state.text, height=200)



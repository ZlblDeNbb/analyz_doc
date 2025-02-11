import os
import streamlit as st
import fitz  # PyMuPDF для работы с PDF
from docx import Document
import textract
from odf.opendocument import load
from odf.text import P
import tempfile
import openai
from dotenv import load_dotenv
load_dotenv()


# Класс для работы с API
class LlamaModel:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_TOKEN_API')  # Чтение ключа API
        self.base_url = os.getenv('BASE_OPENAI_URL')
        self.max_input_tokens = 2048  # Максимум токенов для входного сообщения
        self.max_response_tokens = 2048  # Максимум токенов для ответа

    def count_tokens(self, messages):
        tokens = sum(len(message["content"].split()) for message in messages)
        return tokens

    def get_response(self, message):
        messages = [
            {"role": "user", "content": message}
        ]

        total_tokens = self.count_tokens(messages)
        if total_tokens > self.max_input_tokens:
            return "Ваш вопрос слишком длинный. Пожалуйста, сократите его."

        client = openai.Client(
            api_key=self.api_key,
            base_url=self.base_url,
        )


        response=client.chat.completions.create(
                model="meta-llama/llama-3-70b-instruct",  # Укажите модель, например, OpenAI GPT-3
                messages=messages,
                temperature=0.3,  # Степень случайности
                max_tokens=1500,  # Максимальное количество токенов в ответе
                top_p=0.5,  # Использование метода nucleus sampling
                frequency_penalty=0.1,  # Штраф за частоту
                presence_penalty=0.1,  # Штраф за присутствие
            )

        return response.choices[0].message.content


# Класс для работы с подсказками
class AnalyzPrompts:
    @staticmethod
    def get_analyz_prompt(doc1, doc2):
        return (
            f"""Вы помощник, который анализирует два документа и проверяет их на соответствие. Ваши задачи следующие:

            1. Получить два документа для анализа.
            2. Изучить содержание каждого документа, выделив ключевую информацию и маркеры, которые могут изменяться в каждом из документов (например, сроки, данные о клиентах, условия, цифры и другие специфические данные).
            3. Сравнить два документа и указать:
                - Статус соответствия документов (например, "Соответствует" или "Не соответствует").
                - Несоответствия и расхождения данных с эталонным документом. 
                - Описание рисков, которые могут возникнуть при несоблюдении этих требований.
            4. Рассказать, что именно в каждом из документов изменилось, и указать, какие данные нуждаются в особом внимании.

            Инструкции:

            - Документ 1 является эталонным документом.
            - Документ 2 — это документ для сравнения с эталонным.
            - Найдите расхождения между ними и проанализируйте возможные последствия этих расхождений для бизнеса или юридических обязательств.

            Процесс:

            1. Анализируйте документ 1 и документ 2, выявите все ключевые элементы.
            2. Найдите различия в данных и условиях, обращая внимание на изменения, несоответствия и ключевые маркеры.
            3. Выведите статус соответствия.
            4. Перечислите несоответствия. Прям как в документах
            5. Оцените возможные риски при несоответствии и предложите, что следует сделать для устранения этих рисков.
            Документ 1 (Эталонный): 
            {doc1}

            Документ 2 (Для сравнения): 
            {doc2}

            Ответьте на основе анализа этих документов.
            Важно: Пожалуйста, отвечайте строго на русском языке, без исключений. 
            """
        )

    @staticmethod
    def etalon_construct(gen_words):
        return (
           f"""
           Необходимо составить эталонный документ для сравнения (например: эталонное резюме или эталонное ТЗ для проектирования дома):
           Необходимо описать ключевые качества которыми должен обладать документ
           {gen_words}
           Важно: Пожалуйста, отвечайте строго на русском языке, без исключений.
           """
        )

# Функция для извлечения текста из DOCX
def extract_text_from_docx(file):
    try:
        doc = Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Ошибка при извлечении текста из DOCX файла: {str(e)}")

# Функция для извлечения текста из PDF
def extract_text_from_pdf(file):
    try:
        # Открываем PDF файл с помощью PyMuPDF
        doc = fitz.open(file)
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)  # Загружаем страницу
            text += page.get_text()  # Извлекаем текст с текущей страницы
        return text
    except Exception as e:
        raise ValueError(f"Ошибка при извлечении текста из PDF файла: {str(e)}")

# Функция для извлечения текста из текстового файла (.txt)
def extract_text_from_txt(file):
    try:
        text = file.read().decode("utf-8")
        return text
    except Exception as e:
        raise ValueError(f"Ошибка при извлечении текста из TXT файла: {str(e)}")

# Функция для извлечения текста из ODT файлов
def extract_text_from_odt(file):
    try:
        doc = load(file)
        paragraphs = doc.getElementsByType(P)
        text = "\n".join([p.firstChild.data for p in paragraphs if p.firstChild is not None])
        return text
    except Exception as e:
        raise ValueError(f"Ошибка при извлечении текста из ODT файла: {str(e)}")

# Универсальная функция для извлечения текста из различных форматов
def extract_text_from_file(uploaded_file):
    # Получаем расширение файла
    file_extension = uploaded_file.name.split('.')[-1].lower()

    # Сохранение загруженного файла во временный файл
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_file_path = tmp_file.name

    # Определяем формат и извлекаем текст
    if file_extension == 'docx':
        return extract_text_from_docx(tmp_file_path)
    elif file_extension == 'pdf':
        return extract_text_from_pdf(tmp_file_path)
    elif file_extension == 'txt':
        with open(tmp_file_path, 'rb') as file:
            return extract_text_from_txt(file)
    elif file_extension == 'odt':
        return extract_text_from_odt(tmp_file_path)
    else:
        # Для других форматов можно использовать textract
        try:
            text = textract.process(tmp_file_path).decode('utf-8')  # Для большинства других форматов
            return text
        except Exception as e:
            raise ValueError(f"Ошибка при извлечении текста из файла {uploaded_file.name}: {str(e)}")


# Основная функция приложения Streamlit
def main():
    st.title("Сравнение документов")

    # Раздел для загрузки эталонного документа
    st.subheader("Загрузите эталонный файл или сгенерируйте")
    reference_file = st.file_uploader("Загрузите эталонный документ", type=["pdf", "docx", "txt", "odt"])
    user_input = st.text_input("Введите текст:")
    if user_input:
        text = AnalyzPrompts.etalon_construct(user_input)
        # Создаем экземпляр класса ChatGPT4Model
        chat_model = LlamaModel()
        # Получаем ответ от модели
        reference_text = chat_model.get_response(text)
        st.text_area("Текст эталонного документа", reference_text, height=200)
    if reference_file is not None:
        st.write("Эталонный файл загружен")
        reference_text = extract_text_from_file(reference_file)
        st.text_area("Текст эталонного документа", reference_text, height=200)
    # Раздел для загрузки файла для сравнения
    st.subheader("Загрузите файл для сравнения")
    comparison_file = st.file_uploader("Загрузите файл для сравнения", type=["pdf", "docx", "txt", "odt"])

    if comparison_file is not None:
        st.write("Файл для сравнения загружен")
        comparison_text = extract_text_from_file(comparison_file)
        st.text_area("Текст документа для сравнения", comparison_text, height=200)

    # Вывод результатов
    if st.button("Проверить"):

        st.subheader("Результат сравнения")

        # Генерация запроса с использованием текста документов
        prompt = AnalyzPrompts.get_analyz_prompt(reference_text, comparison_text)

        # Создаем экземпляр класса ChatGPT4Model
        chat_model = LlamaModel()

        # Получаем ответ от модели
        response = chat_model.get_response(prompt)

        st.text_area("Результат анализа", response, height=400)


if __name__ == "__main__":
    main()

import json
import re
import urllib.request

API_KEY = "AIzaSyDNDW-Ofcz4Syatq_EB6Yx_reeyGnOA0X8"
MODEL_NAME = "gemini-2.5-flash"


class _Response:
    def __init__(self, text):
        self.text = text


class GenerativeModel:
    def __init__(self, name):
        self.name = name

    def generate_content(self, prompt):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.name}:generateContent?key={API_KEY}"
        )
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
        }).encode()
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _Response(text)


model = GenerativeModel(MODEL_NAME)


def get_ai_explanation(wrong_questions):
    if not wrong_questions:
        return "Ошибок нет!"

    try:
        errors_text = "; ".join(wrong_questions)
        prompt = f"Ученик ошибся в вопросах: {errors_text}. Кратко объясни правильные ответы на русском."

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Ошибка AI: {e}"


def generate_questions_ai(topic):
    prompt = (
        f"Создай тест на тему '{topic}'. 5 вопросов. "
        f"Верни ТОЛЬКО чистый JSON массив объектов с полями question и answer. "
        f"Без лишних слов и разметки markdown."
    )

    try:
        response = model.generate_content(prompt)
        # Очистка текста от возможных ```json ... ```
        clean_json = re.sub(r'```json|```', '', response.text).strip()
        return clean_json
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None
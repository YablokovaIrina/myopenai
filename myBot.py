import os
import json
import openai
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


load_dotenv()

openai.api_key = os.getenv('API_KEY')


def load_data(data):
    with open(data, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_openai_response(question):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant in the search for answers"},
                {"role": "user", "content": question},
                {"role": "assistant", "content": "Hi! What do you want to know?"}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        if 'choices' in response and len(response.choices) > 0 and 'message' in response.choices[0] and 'content' in response.choices[0].message:
            return response.choices[0].message['content'].strip()
        else:
            return "Извините, произошла ошибка при обработке запроса."
    except openai.RateLimitError:
        return "Извините, кончился лимит на использование API. Пожалуйста, попробуйте позже."
    except openai.APIError as e:
        return f"Извините, произошла ошибка API: {str(e)}"
    except Exception as e:
        return f"Извините, произошла неожиданная ошибка: {str(e)}"


def search_in_json(question, data):
    best_match = process.extractOne(question, [page['title'] for page in data], scorer=fuzz.token_sort_ratio)
    if best_match and best_match[1] >= 50:  # Порог сходства титла для поиска
        for page in data:
            if page['title'] == best_match[0]:
                formatted_text = "\n".join(page['text'])
                return formatted_text
    return None


def handle_question(question, data):
    json_response = search_in_json(question, data)
    if json_response:
        return json_response

    openai_response = get_openai_response(question)

    if "I don't know" in openai_response or "I'm not sure" in openai_response:
        return "Извините, я еще не обладаю знаниями по этому вопросу."
    else:
        return openai_response


def main():
    data = load_data('data.json')

    while True:
        question = input("Напиши мне свой вопрос (или 'exit' для завершения моей работы): ")
        if question.lower() == 'exit':
            print("Пока пока")
            break
        response = handle_question(question, data)
        print(response)


if __name__ == '__main__':
    main()

import nltk
nltk.download('punkt')  # Для токенизации в NLTK
nltk.download('punkt_tab')  # Для поддержки языков в sumy, включая русский

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer  # LexRank из sumy
from sumy.summarizers.text_rank import TextRankSummarizer  # TextRank из sumy



# Исходный текст для суммаризации
text = """
Экстрактивное реферирование (Extractive Summarization)
Суть: Система выбирает наиболее важные и репрезентативные предложения из исходного текста и объединяет их в аннотацию. Это классический и наиболее предсказуемый подход.

Технологии и инструменты:

Библиотеки на Python (идеально для ВКР):

spaCy: Промышленный стандарт для NLP. Позволяет проводить токенизацию, лемматизацию, определение частей речи, анализ синтаксических зависимостей. На основе этого можно вычислять важность предложений.

NLTK (Natural Language Toolkit): Классический "учебный" toolkit для NLP. Содержит все необходимые инструменты для предобработки текста и реализации простых алгоритмов.

Gensim: Библиотека для тематического моделирования. Её алгоритм summarize() использует метод TextRank (аналог PageRank для предложений), что является очень хорошей базовой реализацией.

Sumy: Библиотека, созданная specifically для реферирования. Содержит готовые реализации десятка алгоритмов (Luhn, LSA, LexRank, TextRank и др.). Это отличный выбор для быстрого старта и сравнения методов.

Алгоритмы и методы:

Частотные методы (например, Luhn): Важность предложения определяется по наличию и частоте ключевых слов.

Графовые методы (TextRank, LexRank): Предложения представляются как узлы графа. Ребра между узлами взвешиваются на основе схожести предложений. Наиболее важными считаются предложения, наиболее тесно связанные с другими (как страницы в Google).

Методы на основе машинного обучения (с учителем): Можно обучить модель (например, Random Forest, XGBoost) определять, стоит ли включать предложение в аннотацию, на основе признаков: позиция в тексте, наличие ключевых слов, длина предложения и т.д.

Плюсы для ВКР: Относительная простота реализации, прозрачность работы (можно объяснить, почему было выбрано то или иное предложение), хорошие результаты для научных текстов, где ключевые мысли часто уже сформулированы.
Минусы: Аннотация может быть "рваной", так как предложения берутся из разных частей текста без перефразирования.
"""


# 2. Суммаризация с помощью Sumy (LexRank)
try:
    parser = PlaintextParser.from_string(text, Tokenizer("russian"))  # Укажите язык
    lexrank_summarizer = LexRankSummarizer()
    sumy_lexrank_summary = lexrank_summarizer(parser.document, 5)  # 5 предложений
    print("Sumy LexRank Summary:")
    for sentence in sumy_lexrank_summary:
        print(sentence)
except Exception as e:
    print("Ошибка в Sumy LexRank:", e)
print("\n")

# 3. Суммаризация с помощью Sumy (TextRank)
try:
    textrank_summarizer = TextRankSummarizer()
    sumy_textrank_summary = textrank_summarizer(parser.document, 5)  # 5 предложений
    print("Sumy TextRank Summary:")
    for sentence in sumy_textrank_summary:
        print(sentence)
except Exception as e:
    print("Ошибка в Sumy TextRank:", e)
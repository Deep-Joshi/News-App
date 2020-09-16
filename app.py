import json
import os, re
from flask import Flask, jsonify, request
from newsapi import NewsApiClient

app = Flask(__name__)
app._static_folder = os.path.abspath("static/")

# Defined all API calls and initializations
# News API declare
newsapis = NewsApiClient(api_key="52adbcd73de3426da771cdcaecfac96c")

# Get top headlines (Used in slide_top_headlines() and word_cloud())
topheadlines = newsapis.get_top_headlines(language='en', page_size=30)
top_headlines_articles = topheadlines['articles']


# Index Page
def nonempty(data):
    if data is not None:
        return True
    else:
        return False


def filter_json(json_file, number):
    count = 0
    result = []
    for i in range(len(json_file)):
        headlines = json_file[i]
        if nonempty(headlines['source']['name']) and nonempty(headlines['author']) and nonempty(headlines['title']) and \
                nonempty(headlines['description']) and nonempty(headlines['url']) and nonempty(
            headlines['urlToImage']) and nonempty(headlines['publishedAt']):

            result.append(headlines)

            count += 1
            if count == number:
                break

    return result


def filter_json2(json_file, number):
    count = 0
    result = []
    for i in range(len(json_file)):
        headlines = json_file[i]
        if nonempty(headlines['source']['name']) and nonempty(headlines['author']) and nonempty(headlines['title']) and \
                nonempty(headlines['description']) and nonempty(headlines['url']) and nonempty(
            headlines['urlToImage']) and nonempty(headlines['publishedAt']):

            result.append(headlines)

            count += 1
    return result


def source_specific_news(source):
    news_headlines = newsapis.get_top_headlines(sources=source, language='en')
    news_articles = news_headlines['articles']

    my_news_headline = filter_json(news_articles, 4)

    return my_news_headline


# Top headlines from US
# @app.route('/slide_top_headlines', methods=['GET', 'POST'])
def slide_top_headlines():
    # Top headlines
    temp_articles = top_headlines_articles
    my_top_headline = filter_json(temp_articles, 5)

    # return jsonify(top_5_headlines=my_top_headline)
    return my_top_headline


# CNN News
# @app.route('/cnn', methods=['GET', 'POST'])
def cnn_news():
    my_cnn_headline = source_specific_news('cnn')

    # return jsonify(cnn=my_cnn_headline)
    return my_cnn_headline


# Fox News
# @app.route('/fox', methods=['GET', 'POST'])
def fox_news():
    my_fox_headline = source_specific_news('fox-news')

    # return jsonify(fox=my_fox_headline)
    return my_fox_headline


# Word Cloud
def data_preprocess(text):
    words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
    return words


# @app.route('/word_cloud', methods=['GET', 'POST'])
def word_cloud():
    word_articles = top_headlines_articles
    word_dict = {}

    text_file = open("stopwords_en.txt", "r")
    lines = text_file.readlines()
    stopwords = [i.rstrip() for i in lines]

    for i in range(len(word_articles)):
        title_text = word_articles[i]['title']
        if nonempty(title_text):
            filtered_text = data_preprocess(title_text)
            for k in filtered_text:
                if k in word_dict:
                    word_dict[k] += 1
                else:
                    word_dict[k] = 1
    top_words = sorted(word_dict.items(), key=lambda x: x[1])[::-1]

    final_list = []
    count = 1

    for word in top_words:
        if word[0].lower() in stopwords:
            continue
        else:
            final_list.append(word[0])
            count += 1

        if count == 31:
            break

    top_30_dict = []
    size = 23
    for i in range(len(final_list)):
        local_word_dict = {'word': final_list[i], 'size': size}
        size -= 0.5

        top_30_dict.append(local_word_dict)

    # return jsonify(word_cloud=top_30_dict)
    return list(top_30_dict)


@app.route('/google_news', methods=['GET', 'POST'])
def google_search():
    slide_dict = slide_top_headlines()
    cnn_dict = cnn_news()
    fox_dict = fox_news()
    word_cloud_dict = word_cloud()

    return jsonify(slide_headlines=slide_dict, cnn=cnn_dict, fox=fox_dict, word_cloud=word_cloud_dict)


# Google Search
def change_date_format(date):
    month, day, year = date.split('/')
    return year + '-' + month + '-' + day


def get_articles(key_word, d_from, d_to, sources):
    all_articles = newsapis.get_everything(q=key_word, sources=sources, from_param=d_from, to=d_to,
                                            sort_by='publishedAt', page_size=30)

    return all_articles


@app.route('/transmitdata', methods=['GET', 'POST'])
def transmit_data():
    keyword = request.args.get('keyword')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    source = request.args.get('source')

    # Change date format according to search
    date_from = change_date_format(date_from)
    date_to = change_date_format(date_to)

    try:
        result_articles = get_articles(keyword, date_from, date_to, source)
        final_articles = filter_json2(result_articles['articles'], 10)

    except Exception as e:
        error = str(e)
        result = error.replace("\'", "\"")
        results = json.loads(result)
        return jsonify(results)

    return jsonify(articles=final_articles)


@app.route('/selectcategory', methods=['POST', 'GET'])
def select_category():
    category = request.args.get('category')
    if category == "all":
        all_sources = newsapis.get_sources(language='en', country='us')
    else:
        all_sources = newsapis.get_sources(category=category, language='en', country='us')
    sources_list = []
    source_info = all_sources['sources']
    for i in range(len(source_info)):
        sources_list.append({'id': source_info[i]['id'], 'name': source_info[i]['name']})

    if len(sources_list) > 10:
        sources_list = sources_list[:10]

    return jsonify(sources=sources_list)


@app.route('/')
def serve_static():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(debug=True)

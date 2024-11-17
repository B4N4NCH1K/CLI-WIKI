from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit, unquote
from pyfiglet import figlet_format
import sqlite3


#Класс для парсинга страницы и заполнении таблицы SQLite
class python_wiki_parser(HTMLParser):

    #Метод который создает базу данных
    def create_data(self) -> None:
        self.con=sqlite3.connect('links.db')
        self.cur=self.con.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS wiki_links (id integer PRIMARY KEY,links_of_wikies unique);')

    #етод кодировки ссылок
    def url_encoded(self, url_fun):
        #Разбиваем URL на части
        parts = urlsplit(url_fun)
    
        #Кодировка каждую часть
        encoded_scheme=parts.scheme  #Схема (https) не кодируется
        encoded_netloc=parts.netloc  #Домен (ru.wikipedia.org) не кодируется
        encoded_path=quote(unquote(parts.path))  #Кодировка пути
        encoded_query=quote(unquote(parts.query), safe=":/")  #Кодировка параметров запроса(не обязательно, но иногда попадались и такие запросы)
        encoded_fragment=quote(unquote(parts.fragment))  #Кодировка фрагмента 
        return urlunsplit((encoded_scheme, encoded_netloc, encoded_path, encoded_query, encoded_fragment))

    #Метод проверки ссылки на доступность
    def check_url(self, url_1) -> bool:
        try:
            encoded_url=self.url_encoded(url_1)
            response_function=urlopen(encoded_url)
            if response_function.status==200:
                return True
        except HTTPError as e:
            print(f"Ошибка HTTP: {e.code} - {e.reason}")
            return False
        except URLError as e:
            print(f"Ошибка URL: {e.reason}")
            return False

    #Метод библиотеки HTMLParser с помощью которой и происходит парсинг
    def handle_starttag(self, tag, attrs) -> None:
        #Определение контейнера с с материалом статьи
        if tag=='div':
            for attr, data in attrs:
                if attr=='class' and data=='mw-body-content':
                    self.magic_container=True

        #Поиск ссылки в атрибутах и добавление в базу данных
        if tag=='a' and getattr(self,'magic_container',False):
            for attr, data in attrs:
                if attr=='href' and data[:6]=='/wiki/':
                    data=str(text+data)
                    data = self.url_encoded(data)
                    if self.check_url(data)==True:
                        print(data)
                        self.cur.execute('INSERT OR IGNORE INTO wiki_links (links_of_wikies) VALUES (?)',(data,))
                        self.con.commit()

    #Метод для поиска ссылки на статьи по id
    def data_links(self, id) -> str:
        self.cur.execute('SELECT links_of_wikies FROM wiki_links WHERE id=(?)',(id,))
        return self.cur.fetchone()[0]

    #Метод для определения id последней строки в таблице
    def data_end(self) -> int:
        self.cur.execute('SELECT id FROM wiki_links ORDER BY id DESC LIMIT 1;')
        return int(self.cur.fetchone()[0])

    #Метод закрытия базы данных
    def close_db(self) -> None:
        self.con.close()

#Метод для обработки ссылок на статьи и сохранения в базу данных
def deep_6() -> None:

    #Объявляю переменные для дальнейшей работы
    global text                   #Переменная для конкатенации в строке 24 и добавлении в таблицу базы данных как полноценной ссылки
    count: int=2                  #Переменная для фиксирования глубины(цифра "2" потому что первый парсинг, строка 62, вроде как считается за глубину "1")
    temp_data_count: int=1        #Переменная для перебора ссылок, начиная со "2" глубины 

    #Объявление класса и создание базы данных
    parser=python_wiki_parser()
    parser.create_data()

    #Цикл для фильтрации данных, чтобы точно была ссылка из русской википедии :) 
    while True:
        url: str=input('Введите ссылку на статью русской википедии:')
        if url.startswith('https://ru.wikipedia.org/wiki/') and len(url) > len('https://ru.wikipedia.org/wiki/'):
            if parser.check_url(url)==True:
                break
            else:
                print('Похоже что-то пошло не так\u2639. Введите новую ссылку! ^_^')
        else:
            print('Это не ссылка на статью из русской википедии. Попробуй ещё раз! ^_^')
            
    #Обработка ссылок на глубине "1"
    text=url[0:24]
    response=urlopen(url)
    parser.feed(response.read().decode('utf-8'))

    #Обработка ссылок с глубины "2" по "6"
    while count <= 6:
        temp_data_end_count=parser.data_end()                                      #Определение лимита для каждой глубины
        while temp_data_count <= temp_data_end_count:                              #Цикл сравнения действующей id с лимитом
            url=parser.data_links(temp_data_count)                                 #Определение ссылки по id
            response=urlopen(url)                                                  #Запрос через полученную ссылку для получения содержания веб-страницы
            parser.feed(response.read().decode('utf-8'))                           #Парсинг сайта на наличие других ссылок на статьи
            temp_data_count+=1
        count+=1                                                

    parser.close_db()

#Начало работы проги
if __name__=='__main__':
    print(figlet_format('W1K1P3D1A 4 L1F3'))
    deep_6()


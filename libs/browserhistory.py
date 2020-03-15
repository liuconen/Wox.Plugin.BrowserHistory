import os
import sqlite3
import subprocess
from shutil import copyfile


def is_browser_process_running(browser_process_name: str) -> bool:
    output = subprocess.run(["tasklist"], stdout=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode('gbk')
    processes = output.split("\n")
    for p in processes:
        if browser_process_name + ".exe" in p:
            return True
    return False


def copy_database_if_locked(database_paths: dict) -> dict:
    """
    when the browser is running, it's history database will be locked.
    """
    for (browser, database_path) in database_paths.items():
        if is_browser_process_running(browser):
            local_database_file_name = f"{browser}_history"
            if os.path.exists(local_database_file_name):
                os.remove(local_database_file_name)
            local_path = f"cache/{local_database_file_name}"
            copyfile(database_path, local_path)
            database_paths[browser] = local_path
    return database_paths


def get_database_paths() -> dict:
    browser_path_dict = dict()
    homepath = os.path.expanduser("~")
    abs_chrome_path = os.path.join(homepath, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History')
    abs_firefox_path = os.path.join(homepath, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
    # it creates string paths to broswer databases
    if os.path.exists(abs_chrome_path):
        browser_path_dict['chrome'] = abs_chrome_path
    if os.path.exists(abs_firefox_path):
        firefox_dir_list = os.listdir(abs_firefox_path)
        for f in firefox_dir_list:
            if f.find('.default') > 0:
                abs_firefox_path = os.path.join(abs_firefox_path, f, 'places.sqlite')
        if os.path.exists(abs_firefox_path):
            browser_path_dict['firefox'] = abs_firefox_path
    return browser_path_dict


def get_browserhistory() -> dict:
    """Get the user's browsers history by using sqlite3 module to connect to the dabases.
       It returns a dictionary: its key is a name of browser in str and its value is a list of
       tuples, each tuple contains four elements, including url, title, and visited_time. 

       Example
       -------
       >>> from libs import browserhistory as bh
       >>> dict_obj = bh.get_browserhistory()
       >>> dict_obj.keys()
       >>> dict_keys(['safari', 'chrome', 'firefox'])
       >>> dict_obj['safari'][0]
       >>> ('https://mail.google.com', 'Mail', '2018-08-14 08:27:26')
    """
    # browserhistory is a dictionary that stores the query results based on the name of browsers.
    browserhistory = {}

    # call get_database_paths() to get database paths.
    paths2databases = get_database_paths()
    paths2databases = copy_database_if_locked(paths2databases)

    for browser, path in paths2databases.items():
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            _SQL = ''
            # SQL command for browsers' database table
            if browser == 'chrome':
                _SQL = """SELECT url, title, datetime((last_visit_time/1000000)-11644473600, 'unixepoch', 'localtime') 
                                    AS last_visit_time FROM urls ORDER BY last_visit_time DESC"""
            elif browser == 'firefox':
                _SQL = """SELECT url, title, datetime((visit_date/1000000), 'unixepoch', 'localtime') AS visit_date 
                                    FROM moz_places INNER JOIN moz_historyvisits on moz_historyvisits.place_id = moz_places.id ORDER BY visit_date DESC"""
            elif browser == 'safari':
                _SQL = """SELECT url, title, datetime(visit_time + 978307200, 'unixepoch', 'localtime') 
                                    FROM history_visits INNER JOIN history_items ON history_items.id = history_visits.history_item ORDER BY visit_time DESC"""
            else:
                pass
            # query_result will store the result of query
            query_result = []
            try:
                cursor.execute(_SQL)
                query_result = cursor.fetchall()
            except sqlite3.OperationalError:
                print('* Notification * ')
                print('Please Completely Close ' + browser.upper() + ' Window')
            except Exception as err:
                print(err)
            # close cursor and connector
            cursor.close()
            conn.close()
            # put the query result based on the name of browsers.
            browserhistory[browser] = query_result
        except sqlite3.OperationalError:
            print('* ' + browser.upper() + ' Database Permission Denied.')

    return browserhistory

from __future__ import with_statement
from urllib.request import urlretrieve
from selenium import webdriver
from contextlib import contextmanager
from contextlib import contextmanager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import signal
import logging
import os
import time
import re
import json

    
@contextmanager
def time_limit(seconds):
    #import signal
    def signal_handler(signum, frame):
        raise TimeoutException

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class TimeoutException(Exception):
    pass


class Naver_DN(webdriver.Firefox, webdriver.Chrome, webdriver.Ie):
    def __init__(self, browser, CNF_JSON_FILE):
        '''
        browser: browser Name : ie, Firefox, chrome
        CNF_JSON_FILE: configuration file in JSON
        '''
        
        if browser.lower() == "ie":
            webdriver.Ie.__init__(self)
        elif browser.lower() == "chrome":
            webdriver.Chrome.__init__(self)
        elif browser.lower() == "phantomjs":
            webdriver.PhantomJS.__init__(self)
        else:
            webdriver.Firefox.__init__(self)

        self.implicitly_wait(5)
        #        self.logger = logger.getLogger('Naver dn logger')

        CNF_JSON = self.read_json(CNF_JSON_FILE)

        self.BROWSER = browser
        self.base_URL = 'http://cafe.naver.com/'
        self.cafe_name = CNF_JSON['cafe_name']
        self.menuID = CNF_JSON['menuID']
        self.searchType = CNF_JSON['searchType']
        self.searchKeyword = CNF_JSON['searchKeyword']
        self.menu_iframe = CNF_JSON['id_iframe']
        self.log_ID = CNF_JSON['log_id']
        self.log_pw = CNF_JSON['log_pw']

        self._txt_box = "//div[@class='atch_file_area']/a[@class='atch_view m-tcol-c']"
        self._txt_cafe_main = "//div[@class='cafe_main']"
        self._txt_files = "//div[@id='attachLayer']/ul/li/span[@class='file_name']"
        self._txt_dn_links = "//div[@id='attachLayer']/ul/li/div[@id='attahc']/a"
        self._txt_title = ".//td/span/span[@class='aaa']"
        self._txt_href = ".//td[@class='board-list']/span/span[@class='aaa']/a[@class='m-tcol-c']"


    def __del__(self):
        logging.critical(" CLASS OJBECT KILLED")
        #os.system('pkill -f firefox')

    def __check_exists_by_xpath__(self, xpath):
        try:
            self.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def __switch_to_iFrame__(self, _iframe_id):

        self.switch_to_default_content()
        try:
            _iframe = self.find_element_by_xpath("//iframe[@id='cafe_main']")
            
        except NoSuchElementException as ex:
            print(ex.message)
            
        self.switch_to_frame(_iframe)
        logging.debug(" Frame swtiched to : %s", _iframe_id)
    
    
    def __isExist_Next_page__(self):
        '''
        move to Next page in iFrmae(id='cafe_main') if next page is available
        '''
        _t =  self.find_elements(By.XPATH, "//table[@class='Nnavi']/tbody/tr/td[@class='on']/following-sibling::td/a")
        if len(_t):
            return True
        else:
            return False

    def _get_b_titles(self, _type):
        '''
        _type: 'l'--> get list of titles from search Result
             : 'o' --> get title from Opened Page
        '''
        _css_title = "div.tit-box > div.fl > table > tbody > tr > td  > span.b.m-tcol-c"


        self.__switch_to_iFrame__('cafe_main')

        if _type == 'l':
            return [ re.sub('\[[0-9]*\]', '', i.text).strip() for i in self.find_elements(By.XPATH,\
                  ".//td/span/span[@class='aaa']")]
        elif _type == 'o':
            return self.find_element(By.CSS_SELECTOR, _css_title).text.strip()
        else:
            print(" 'l' for titles from Search Result, 'o' for opened page")


    def _get_b_numbers(self, _type):
        '''
        _type: True --> get list fo posting numbers from search Result
             : False --> get posting number from Opened Page
        '''
        self.__switch_to_iFrame__('cafe_main')
        if _type == 'l':
            return [i.text for i in self.find_elements(By.XPATH, \
               "//form[@name='ArticleList']/table[@class='board-box']/tbody/tr[@align='center']/td[1]/span")]
        elif _type == 'o':
            return self.current_url.split('/')[-1]
        else:
            print(" 'l' for titles from Search Result, 'o' for opened page")

    def _get_b_hrefs(self, sw='list'):
        '''
        sw ='l': returns list of Href link addresses
        sw= 'href': returns list Href clickalbe a addresses
        '''
        self.__switch_to_iFrame__('cafe_main')
        if sw.lower() == 'list':
            return [i.get_attribute('href')  for i in self.find_elements(By.XPATH,\
                         ".//td[@class='board-list']/span/span[@class='aaa']/a[@class='m-tcol-c']")]
        elif sw == 'l':
            return [i  for i in self.find_elements(By.XPATH,\
                       ".//td[@class='board-list']/span/span[@class='aaa']/a[@class='m-tcol-c']")]


    def _get_download_links(self):
        self.__switch_to_iFrame__('cafe_main')
        return [i.get_attribute('href') for i in self.find_elements(Bety.XPATH, "//div[@id='attachLayer']/ul/li/div[@id='attahc']/a[1]")]

    def _goTo_nextPage(self):
        self.__switch_to_iFrame__('cafe_main')
        self.find_element(By.XPATH, "//table[@class='Nnavi']/tbody/tr/td[@class='on']/following-sibling::td/a").click()


    def __make_folder__(self,  _folder):
        '''
        make a folder and create IF NOT EXISTS
        '''
        try:
            os.makedirs(_folder)
            return True
        except OSError:
            return False


    def get_youtube_links(self, _title):
        self.__switch_to_iFrame__('cafe_main')
        if self.__check_exists_by_xpath__("//iframe[starts-with(@src,'https://www.youtube')]"):
            _url_youtube = self.find_element(By.XPATH, "//iframe[starts-with(@src,'https://www.youtube')]").get_attribute('src')
            print("Youtube :{0}".format(_url_youtube))
            try:
                _url_head = "<iframe src=\""
                _url_tail = "\" scrolling=\"no\"  width=\"640px\" height=\"360px\" frameborder=\"0\"></iframe>"
                with open(_title+".html", 'w') as f:
                    f.write(_url_head)
                    f.write(_url_youtube)
                    f.write(_url_tail)
            except Exception as ex:
                print(ex.message)

            
                
        else:
            print("No YOUTUBE LINKS")
            
    def goTomenu(self, _menuID):
        '''
        move to menu by clicking menuID
        '''
        try:
            _menu = self.find_element_by_id(self.menuID)
        except NoSuchElementException as ex:
            print(ex.message)

        _menu.click()
        self.__switch_to_iFrame__(self.menu_iframe)
        logging.debug("Chaged menu to %s", _menuID)
        

    def search(self, _type, _kw):
        '''
        search keyword by 
        1: title+ content
        2: title 
        3: id
        4: content of comment
        5: commentator
        '''
        try:
            qs = self.find_element_by_xpath("//form[@name='frmSearch']/span[2]/input[1]")
            qs.click()
            for i in range(0,_type):
                qs.send_keys(Keys.ARROW_DOWN)
                qs.send_keys(Keys.ENTER)
                qs.send_keys(Keys.ENTER)

            # Search by keyword
#            time.sleep(1)
            qn = self.find_element_by_id('query')
            qn.send_keys(self.searchKeyword)
            qbtn = self.find_element_by_class_name('btn-search-green')
            qbtn.click()


        except NoSuchElementException as ex:
            print(ex.message)



    def log_in(self, _id, _pw):


        self.find_element_by_xpath("//a[@id = 'gnb_login_button']").click()
        time.sleep(1)
        self.find_element_by_xpath("//input[@id='id']").send_keys(_id)
        _a= self.find_element_by_xpath("//input[@id='pw']")
        _a.send_keys(_pw)
        _a.submit()

#        self.find_element_by_class_name("btn").click()
        time.sleep(2)
        self.find_element_by_xpath("//span[@class='btn_cancel']/a").click()
#        self.find_element_by_xpath("//div[@class='login_maintain']/a[2]").click()
        time.sleep(2)
    


        
    def _get_download_file_nameNlinks_(self):
        '''
        RETURN a list : [(file1, link1),(file2, link2), (file3,link3)...]
        '''
        _txt_dn_arrow = "//div[@class='atch_file_area']/a[@class='atch_view m-tcol-c']"
        _txt_dn_box = "//div[@class='atch_file_area']/div[@id='attachLayer']"
        _txt_cafe_main = "//div[@class='cafe_main']"
        _txt_files = "//div[@id='attachLayer']/ul/li/span[@class='file_name']"
        _txt_dn_links = "//div[@id='attachLayer']/ul/li/div[@id='attahc']/a"

        
        logging.debug("Getting Name and Links of FILE")
        
#        self.refresh()
#        self.__switch_to_iFrame__('cafe_main')
#        time.sleep(1)
        while( self.__check_exists_by_xpath__(_txt_cafe_main) is True):
            self.__switch_to_iFrame__('cafe_main')
            logging.info("***** Switched to cafe_main")

        self.__switch_to_iFrame__('cafe_main')        

        # while(self.__check_exists_by_xpath__(_txt_dn_arrow) is False):
        #     na.refresh()
        #     while( self.__check_exists_by_xpath__(_txt_cafe_main) is True):
        #         self.__switch_to_iFrame__('cafe_main')
        #         logging.info("***** Switched to cafe_main")

        while( self.__check_exists_by_xpath__(_txt_cafe_main) is True):
            self.__switch_to_iFrame__('cafe_main')
            logging.info("***** Switched to cafe_main")

        print("dn_arrow Founded")
        _dn_box = self.find_element(By.XPATH, _txt_dn_arrow)
        _dn_box.click()
        logging.info("***** dn_arrow_ Clicked")
                
        #Check whether the option box is clicked and opened.
        _dn_box = self.find_element(By.XPATH, _txt_dn_box)
        
        while( _dn_box.is_displayed() is False):
            logging.info("Box is not displayed")
            self.find_element(By.XPATH, _txt_dn_arrow).click()
            if self.find_element(By.XPATH, _txt_dn_arrow).is_displayed():
                print("***** Box CLICKED")

        _links_ = self.find_elements(By.XPATH, _txt_dn_links)
        _files_ = self.find_elements(By.XPATH, _txt_files)
        time.sleep(1)

        


                    
        _dn_links = [i.get_attribute('href') for i in _links_]
        _dn_files = [i.text for i in _files_]

        return list(zip(_dn_links, _dn_files))

    def make_b_data_lst(self):
        ''' Return a list of numbe ,  Title, href of bulletin from search Result'''
        _b_lst =[]

        while True:
#      
            _lst = list(zip(self._get_b_numbers('l'), self._get_b_titles('l'), self._get_b_hrefs('l')))

            _b_lst.extend(_lst)
            
            _t = self.__isExist_Next_page__()

            if _t:
                print("{0}: {1}".format(_t, len(_b_lst)))
                na._goTo_nextPage()
                time.sleep(1)
            else:
                print("{0}: {1}".format(_t, len(_b_lst)))
                break


        return _b_lst
        
    def download(self, _title = ''):
        '''
        _titl ='' : download to current directory
               'title': download to title folder after creating it
               'normal string': arbitrary folder 
        Download All files from current Opened Download page
        to  _title folder (make it if not exist)
        '''
        logging.info("START DOWNLOADFILE")
        _lst = self. _get_download_file_nameNlinks_()
        # _lst = (link, file_nmae)
                
        print("{0}: founded".format(len(_lst)))
        _dn_folder =''

        if _title == '':
            _dn_folder = './'
        elif _title.lower() == 'title':
            _dn_folder = self._get_b_titles()
        else:
            _dn_folder = _title

            
        for a in _lst:
            if self.__make_folder__('./' + _title):
                logging.info("The folder created")
            
            urlretrieve(a[0], './' + _title + '/' + a[1])
            print("{0}: downloaded ".format(a[1]))
            time.sleep(1)

    def open_page(self, _post_num, _t_sec=10):
        if type(_post_num) is int:
            _post_num = str(_post_num)
        
        try:
            with time_limit(_t_sec):
                time.sleep(1)
                na.get(cafe_url + _post_num)
                
        except TimeoutException:
            logging.critical(self.BROWSER + 'crushed' + 'at %s', _post_num)
            raise TimeoutException


    def read_json(self, f_name):
        with open(f_name, 'r') as f:
            cnf_jsn = json.load(f)
        return cnf_jsn


        
if __name__ == '__main__':

    # Browser select: firefox or  PhantomJS
    BROWSER = "Firefox"
    logging.basicConfig(level=logging.DEBUG)
    na = Naver_DN(BROWSER, 'config.json')
    cafe_url = 'http://cafe.naver.com/violin79/'
    na.get('https://nid.naver.com/nidlogin.login')
    na.get(na.base_URL + na.cafe_name)
    na.log_in(na.log_ID, na.log_pw)
    na.goTomenu(na.menuID)
    time.sleep(2)
    
    # na.search(na.searchType, na.searchKeyword)
    # time.sleep(2)

    # # b_num_title : list of na.make_b_data_lst which returns the [{number, title, href}...]
    # b_num_title = [x for x in  na.make_b_data_lst()]
    # time.sleep(1)
    
 #    for n,i in enumerate(b_num_title):
#         number,title, addr = i
#         print("go To bulletin body")
#         print("========== {0} :{1}".format(n, i[1]))

#         # na.get with the running time limitation
#         try:
#             with time_limit(5):
#                 time.sleep(1)
#                 na.get(cafe_url+i[0])
                
#         except TimeoutException:
#             logging.critical(BROWSER +'crushed')
#             print("{0} xxxxxxxxxxxxxxxxxxxxTimed out!xxxxxxxxxx".format(cafe_url+i[0]))
#             del na
# #            os.system('pkill -f firefox')
#             time.sleep(2)
#             na = Naver_DN(BROWSER, cnf_jsn)
#             na.get(cafe_url)
#             na.log_in(na.log_ID, na.log_pw)
#             na.get(cafe_url+i[0])
#             time.sleep(2)

#             try:
#                 na.download_files_onPage(title)

#             except:
#                 pass

#             continue
        
#         print("STARTS DOWNLOADFILE")
#         try:

#             na.download_files(title)
#             os.chdir('./'+title)            
#             na.get_youtube_links(title)
#             os.chdir('../')
#         except:
#             continue
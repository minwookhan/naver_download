import selenium
from selenium import webdriver
import time


def highlight(element):
    """Highlights a Selenium webdriver element"""
    driver = element._parent
    def apply_style(s):
        driver.execute_script("arguments[0].setAttribute('style', arguments[1])", element, s)
    orignal_style = element.get_attribute('style')
    apply_style("border: 4px solid red")
    if (element.get_attribute("style")!=None):
        time.sleep(5)
    apply_style(orignal_style)


def printELE(lst, _attr):
    for n, i in enumerate(lst):
        print("{0} : {1}".format(n, i.get_attribute(_attr)))

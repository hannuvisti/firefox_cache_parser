#!/usr/bin/python


from selenium import webdriver
from selenium.webdriver.common.keys import Keys

browser = webdriver.Firefox()

browser.get('http://www.google.com')
assert 'Google' in browser.title

elem = browser.find_element_by_name('q')  # Find the search box
elem.send_keys('Hannu Visti' + Keys.RETURN)

#body = driver.find_element_by_tag_name("body")
elem.send_keys(Keys.CONTROL + 't')

#browser.quit()

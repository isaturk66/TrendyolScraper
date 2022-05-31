# Import necessary libraries
from glob import glob
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.support import ui
import threading
import argparse
import sys
from os.path import exists
import os
import json
import requests
import re
import urllib.request


sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

doneURLs = []
def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(
        description='Webscraper for pinterest')
    parser.add_argument('--url',
                        dest='url_id', help='The search text that will be searched in pinterest',
                        default='', type=str)
    parser.add_argument('--path',
                        dest='path', help='The search text that will be searched in pinterest',
                        default='./Trendyol', type=str)
    parser.add_argument('--max',
                        dest='maximum', help='The search text that will be searched in pinterest',
                        default=100000, type=int)

    args = parser.parse_args()
    return args



args = parse_args()


searchURL = args.url_id
maximum = args.maximum
rootPath = args.path

pic_variant_counter = 0
get_pic_counter = 0
finished = False

if not os.path.exists(rootPath):
    os.makedirs(rootPath)


try:
  fileList = os.listdir(rootPath)
  if (len(fileList) == 0):
    startIndex= int(fileList[-1][0:-4])+1
  else:
    startIndex = 0
except:
  startIndex= 0

#t = ScrapingEssentials(rootPath,startIndex)


# Determines if the page is loaded yet.
def page_is_loaded(driver):
    return driver.find_element_by_tag_name("body") != None


# Finds the detailed product page of each "pin" for pinterest
def fetchLinks(driver, valid_urls):

    list_counter = 0
  #  try:
 #     with open(rootPath+ "/sources.txt",'r') as f: sourceList = f.read().splitlines()
  #  except:
   #   sourceList = []

    # Does this until you have maximum items or the program has gone on for long enough, meaning that it reached the end of results
    beginning = time.time()
    end = time.time()

    prevScroll = -1

    isBreaked = False
   
    while not isBreaked and beginning - end < 30:
      try:
        beginning = time.time()

        if(list_counter >= maximum):
          isBreaked = True
          break
        
        # ----------------------------------EDIT THE CODE BELOW------------------------------#
        # Locate all the urls of the detailed pins
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # for c in soup.find_all("div", {"class": name}):
        if(driver.execute_script("return window.pageYOffset") == prevScroll):
          driver.execute_script("window.scrollBy(0,-2000)")
          time.sleep(2)

        prevScroll = driver.execute_script("return window.pageYOffset")

        for card in soup.find_all("div", {"class": "p-card-wrppr"}):
          for a in card.find_all("a"):
            url = a.get("href")
            if url not in valid_urls:
              valid_urls.append(url)
              end = time.time()
              list_counter += 1
    

        driver.execute_script("window.scrollBy(0,2000)")
        time.sleep(2)
      except:
        continue
    return


downloadTry = 0
def downloader(url,name):
  global downloadTry
  try:
    urllib.request.urlretrieve(url,name)
    downloadTry = 0
    return True
  except:
    if(downloadTry<5):
      print("Error on " +url+ "trying again...")
      downloadTry+=1
      time.sleep(0.5)
      downloader(url,name)



def downloadImages(valid_urls):
  global get_pic_counter
  global finished
  global pic_variant_counter
  beginning = time.time()

  while (0 < len(valid_urls) and not finished and (time.time() - beginning) < 30): #This while loop will trigger every time the valid_urls are bi
    try:
      if(pic_variant_counter >= maximum):
        finished = True
        break
      for urls in valid_urls:
        r =requests.get("https://trendyol.com"+urls)
        searched = re.search("""(?<=window.__PRODUCT_DETAIL_APP_INITIAL_STATE__=)(.*)(?=;window.TYPageName=")""", r.content.decode('utf-8')).group()
        parsedJSON = json.loads(searched)
        
        for imgURL in parsedJSON["product"]["images"]:
          fullURL = "https://cdn.dsmcdn.com/"+imgURL
          print(fullURL)
          if(downloader(fullURL, os.path.join(rootPath,str(get_pic_counter)+"_"+str(pic_variant_counter)+".jpg"))):
            print(str(get_pic_counter) + " - downloaded " + fullURL)
            beginning = time.time()
            pic_variant_counter += 1
        valid_urls.remove(urls)
        get_pic_counter += 1
    except:
      continue

    




def main():
    global t
    driver1 = webdriver.Chrome('chromedriver',chrome_options=chrome_options)
    driver1.get(searchURL)

    # Log in to Pinterest.com

    print("Starting threads...")
    valid_urls = []
 
    time.sleep(3)

    print("Fetching search results...")
    t1 = threading.Thread(target=fetchLinks, args=(driver1, valid_urls,))
    t1.setDaemon(True)
    t1.start()

    time.sleep(8)

   # print("Downloading pictures...")

    t2 = threading.Thread(target=downloadImages, args=(valid_urls,))
    t2.setDaemon(True)
    t2.start()
    
    t2.join()

    print("Done")


if __name__ == "__main__":
  main()


else:
  main()

# Import necessary libraries
from glob import glob
from bs4 import BeautifulSoup
import time
from numpy import vstack
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
        description='Webscraper for trendyol.com')
    parser.add_argument('--url',
                        dest='url_id', help='The url of the trendyol search that will be scraped',
                        default='', required=True,type=str)
    parser.add_argument('--path',
                        dest='path', help='The path of the directory that all the image and .meta files will be downloaded into',
                        default='./Trendyol', required=True,type=str)
    parser.add_argument('--max',
                        dest='maximum', help='Maximum number of images that will be downloaded, no limit as default',
                        default=1000000, type=int)
    parser.add_argument('--prefix',
                        dest='prefix', help='A prefix that will be put in front of all files downloaded, use this if you are going to make multiple downloads on the same directory. No prefix at default',
                        default="", type=str)

    args = parser.parse_args()
    return args



args = parse_args()


searchURL = args.url_id

if("?pi=" in searchURL):
  searchURL = searchURL.split("?pi=")[0]


maximum = args.maximum
rootPath = args.path
prefix = args.prefix

total_counter = 0
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


# Determines if the page is loaded yet.
def page_is_loaded(driver):
    return driver.find_element_by_tag_name("body") != None


# Finds the detailed product page of each "pin" for pinterest
def fetchLinks(driver, valid_urls):
    global searchURL

    list_counter = 0

    # Does this until you have maximum items or the program has gone on for long enough, meaning that it reached the end of results
    beginning = time.time()
    end = time.time()

    prevScroll = -1

    lastloadIndex = 0

    isBreaked = False
    upperCount = 0
    
  
    while not isBreaked: # and beginning - end < 30:
      if(beginning - end > 30):
        if(not upperCount > 2):
          driver.execute_script("window.scrollBy(0,-10000)")
          upperCount+= 1
          end = time.time()
          time.sleep(1)
        else:
          print("Fetching process is completed with "+str(len(valid_urls))+ "results found") 
          isBreaked = True
          break
      try:
        beginning = time.time()
        if(list_counter >= maximum):
          isBreaked = True
          break
        
        # ----------------------------------EDIT THE CODE BELOW------------------------------#
        # Locate all the urls of the detailed pins

        try:
          currentLoadIndex = int(driver.current_url.split("pi=")[1])
        except:
          currentLoadIndex = 0
        
        if(currentLoadIndex < lastloadIndex):
          driver.get(searchURL+"?pi="+str(lastloadIndex+1))
          print("Running get on "+searchURL+"?pi="+str(lastloadIndex+1))
          lastloadIndex += 1
          time.sleep(2)
        else:
          lastloadIndex = currentLoadIndex


        soup = BeautifulSoup(driver.page_source, "html.parser")
        # for c in soup.find_all("div", {"class": name}):
        if(driver.execute_script("return window.pageYOffset") == prevScroll):
          driver.execute_script("window.scrollBy(0,-4000)")
          time.sleep(2)

        prevScroll = driver.execute_script("return window.pageYOffset")

        for card in soup.find_all("div", {"class": "p-card-wrppr"}):
          for a in card.find_all("a"):
            url = a.get("href")
            if url not in valid_urls:
              valid_urls.append(url)
              # print("Added "+url)
              end = time.time()
              upperCount = 0
              list_counter += 1
    
        driver.execute_script("window.scrollBy(0,2000)")
        time.sleep(2)
      except Exception as e:
        print(e)
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
  global total_counter
  beginning = time.time()

  while (0 < len(valid_urls) and not finished and (time.time() - beginning) < 30): #This while loop will trigger every time the valid_urls are bi
    try:
      if(total_counter >= maximum):
        finished = True
        break
      for urls in valid_urls:
        r =requests.get("https://trendyol.com"+urls)
        searched = re.search("""(?<=window.__PRODUCT_DETAIL_APP_INITIAL_STATE__=)(.*)(?=;window.TYPageName=")""", r.content.decode('utf-8')).group()
        parsedJSON = json.loads(searched)

        metadata= {}
        metadata["name"] = parsedJSON["product"]["name"]
        metadata["color"] = parsedJSON["product"]["color"]
        metadata["url"] = parsedJSON["product"]["url"]
        metadata["gender"] = parsedJSON["product"]["gender"]
        metadata["brand"] = parsedJSON["product"]["brand"]
        metadata["attributes"]  = parsedJSON["product"]["attributes"] 
        prefixW = ""
        if(prefix != ""):
          prefixW = prefix+"-"

        with open(os.path.join(rootPath,prefixW +str(get_pic_counter)+".meta"), 'w', encoding='utf8') as outfile:
          json.dump(metadata, outfile, ensure_ascii=False)
        
        pic_variant_counter = 0
        for imgURL in parsedJSON["product"]["images"]:
          fullURL = "https://cdn.dsmcdn.com/"+imgURL
          
          
          if(downloader(fullURL, os.path.join(rootPath,prefixW + str(get_pic_counter)+"_"+str(pic_variant_counter)+".jpg"))):
            print(str(get_pic_counter) + " - downloaded " + fullURL)
            beginning = time.time()
            pic_variant_counter += 1
            total_counter +=1
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

    print("Downloading pictures...")

    t2 = threading.Thread(target=downloadImages, args=(valid_urls,))
    t2.setDaemon(True)
    t2.start()
    
    t2.join()

    print("Done")


if __name__ == "__main__":
  main()


else:
  main()

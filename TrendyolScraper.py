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
import traceback
from queue import Queue
import logging

logging.basicConfig(filename='trendolscraper_'+str(time.time())+'.log', level=logging.INFO,  format='%(asctime)s %(message)s')


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
                        default=None, required=False,type=str)
    parser.add_argument('--urlsPath',
                        dest='urlsPath', help='Path to the file containing the URLs that will be scraped',
                        default=None, type=str)
    parser.add_argument('-l', '--listurls', action='store_true',dest= 'isListUrLs', default=False, help='If you want to create a .txt file with all image urls')
    parser.add_argument('-n', '--nodownload', action='store_true',dest= 'isNoDownload', default=False, help='If you want dont want to download the images')
    parser.add_argument('-c', '--maxpercategory', action='store_true',dest= 'maxpc', default=False, help='If you want the --max argument to apply to each url in the file seperately')
    parser.add_argument('--path',
                        dest='path', help='The path of the directory that all the image and .meta files will be downloaded into',
                        default='./Trendyol', required=True,type=str)
    parser.add_argument('--max',
                        dest='maximum', help='Maximum number of images that will be downloaded, no limit as default',
                        default=10000000, type=int)
    parser.add_argument('--prefix',
                        dest='prefix', help='A prefix that will be put in front of all files downloaded, use this if you are going to make multiple downloads on the same directory. No prefix at default',
                        default="", type=str)

    args = parser.parse_args()
    return args


def logAndPrint(message):
  logging.info(message)
  print(message)


def assert_args():
    if(args.url_id == None and args.urlsPath == None):
        logAndPrint("You must provide either a url or a file containing urls")
        exit()
    if(args.url_id != None and args.urlsPath != None):
        logAndPrint("You must provide either a url or a file containing urls, not both")
        exit()
    if(args.urlsPath == None and args.maxpc == True):
        logAndPrint("You must provide a file containing urls if you want to use the -c/--maxpercategory argument")
        exit()
    

args = parse_args()
url = args.url_id


if url != None:
  if("?pi=" in url):
    url = url.split("?pi=")[0]


maximum = args.maximum
rootPath = args.path
prefix = args.prefix
isNoDownload = args.isNoDownload
isListUrLs = args.isListUrLs
isMaxPerCategory = args.maxpc
urlsPath = args.urlsPath
  

total_counter = 0
get_pic_counter = 0
productQueue = Queue()
valid_urls = []

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



def getUrlListFromFile(path):
  urlList = []
  with open(path) as f:
    for line in f:
      if("?pi=" in line):
        urlList.append(line.split("?pi=")[0].strip())
      else:
        urlList.append(line.strip())
  return urlList



def prefixW():
  prefixW = ""
  if(prefix != ""):
    prefixW = prefix+"-"
  return prefixW

# Determines if the page is loaded yet.
def page_is_loaded(driver):
    return driver.find_element_by_tag_name("body") != None


# Finds the detailed product page of each "pin" for pinterest
def fetchLinks(driver):
    global searchURL
    global finished

    list_counter = 0
    # Does this until you have maximum items or the program has gone on for long enough, meaning that it reached the end of results
    beginning = time.time()
    end = time.time()

    prevScroll = -1

    lastloadIndex = 0

    upperCount = 0
    
  
    while True: 
      if(beginning - end > 20):
        if(not upperCount > 0):
          driver.execute_script("window.scrollBy(0,-10000)")
          upperCount+= 1
          end = time.time()
          time.sleep(1)
        else:
          logAndPrint("Fetching process is completed with "+str(len(valid_urls))+ "results found") 
          finished = True
          return
      try:
        beginning = time.time()
        if(list_counter >= maximum):
          return

        try:
          currentLoadIndex = int(driver.current_url.split("pi=")[1])
        except:
          currentLoadIndex = 0
        
        if(currentLoadIndex < lastloadIndex):
          driver.get(searchURL+"?pi="+str(lastloadIndex+1))
          logAndPrint("Running get on "+searchURL+"?pi="+str(lastloadIndex+1))
          lastloadIndex += 1
          time.sleep(2)
        else:
          lastloadIndex = currentLoadIndex

        soup = BeautifulSoup(driver.page_source, "html.parser")
        if(driver.execute_script("return window.pageYOffset") == prevScroll):
          
          if(beginning - end >10):
            driver.execute_script("window.scrollBy(0,-5000)")
          else:
            driver.execute_script("window.scrollBy(0,-3000)")
          time.sleep(2)

        prevScroll = driver.execute_script("return window.pageYOffset")

        for card in soup.find_all("div", {"class": "p-card-wrppr"}):
          for a in card.find_all("a"):
            url = a.get("href")
            if url not in valid_urls:
              valid_urls.append(url)
              productQueue.put(url)
              end = time.time()
              upperCount = 0
              list_counter += 1
    
        driver.execute_script("window.scrollBy(0,500)")
        time.sleep(2)
      except Exception as e:
        logAndPrint(e)
        continue


downloadTry = 0
def downloader(url,name):
  global downloadTry
  try:
    urllib.request.urlretrieve(url,name)
    downloadTry = 0
    return True
  except:
    if(downloadTry<2):
      logAndPrint("Error on " +url+ ", trying again...")
      downloadTry+=1
      time.sleep(0.5)
      downloader(url,name)



def downloadImages():
  global get_pic_counter
  global finished
  global total_counter

  while (True): 
    if(productQueue.empty()):
      if(finished):
        return
      else:
        continue
    
    try:
      if(total_counter >= maximum):
        finished = True
        return

      urls = productQueue.get()
      fileNameHeader = urls.split("/")[-1].split("?")[0]
      
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
      prefixWW = prefixW()

      with open(os.path.join(rootPath,prefixWW + fileNameHeader +".meta"), 'w', encoding='utf8') as outfile:
        json.dump(metadata, outfile, ensure_ascii=False)
        if isNoDownload:
          logAndPrint("Metadata for "+ str(get_pic_counter) +" is saved")
      
      pic_variant_counter = 0
      for imgURL in parsedJSON["product"]["images"]:
        fullURL = "https://cdn.dsmcdn.com/"+imgURL
        if(isListUrLs):
          
          with open(os.path.join(rootPath,prefixWW+"imageUrls.txt"), "a") as fff:
            fff.write("{0},{1},{2}".format(prefixWW + fileNameHeader +"_"+str(pic_variant_counter)+".jpg",pic_variant_counter,fullURL))
            fff.write("\n")
        if(not isNoDownload):
          if(downloader(fullURL, os.path.join(rootPath,prefixWW + fileNameHeader +"_"+str(pic_variant_counter)+".jpg"))):
            logAndPrint(str(get_pic_counter) + " - downloaded " + fullURL)
        
        pic_variant_counter += 1
        total_counter +=1
      get_pic_counter += 1
    except Exception as e: 
      logAndPrint(e)
      logAndPrint(traceback.format_exc())
      continue
  
    
def clearBuffer():
  global total_counter
  global finished 
  finished = False
  if(isMaxPerCategory):
    total_counter = 0
  global downloadTry
  downloadTry = 0  

def Scrape(searchURL):

    driver1 = webdriver.Chrome('chromedriver',options=chrome_options)
    driver1.get(searchURL)

    # Log in to Pinterest.com

    logAndPrint("Starting threads...")
    valid_urls = []
 
    time.sleep(3)

    logAndPrint("Fetching search results...")
    
    t1 = threading.Thread(target=fetchLinks, args=(driver1,), daemon=True)
    t1.start()

    time.sleep(8)
   
    logAndPrint("Downloading pictures...")

    t2 = threading.Thread(target=downloadImages, args=(), daemon=True)
    t2.start()
    
    t2.join()

    logAndPrint("Done")



def main():

  if(urlsPath == None):
    Scrape(url)
  else:
    urls = getUrlListFromFile(urlsPath)
    for urll in urls:
      Scrape(urll)
      logAndPrint("Done with "+urll)
      clearBuffer()

if __name__ == "__main__":
  start_time = time.time()
  assert_args()
  main()
  logAndPrint("--- %s seconds ---" % (time.time() - start_time))

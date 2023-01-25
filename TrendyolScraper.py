# Import necessary libraries
from glob import glob
from bs4 import BeautifulSoup
import time
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
import concurrent.futures
import asyncio
from pyppeteer import launch
from pyppeteer import errors as pyppeteer_errors



##TODO:
##  Fix printing issues with multithreading
##    -  Solve overlapping printing
##    -  Solve numbers not incrementing properly when printing




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
  print(message,end='\n',flush=True)

def createDir(path):
  if not os.path.exists(path):
    os.makedirs(path)

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


createDir(rootPath)
createDir(rootPath+"/meta")
createDir(os.path.join(os.path.dirname(__file__), "logs"))


logging.basicConfig(filename= os.path.join(os.path.dirname(__file__), "logs",'trendolscraper_'+str(time.time())+'.log'), level=logging.INFO,  format='%(asctime)s %(message)s')

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


def checkIfFileExists(path):
  if(os.path.isfile(path)):
    return True
  else:
    return False



def prefixW():
  prefixW = ""
  if(prefix != ""):
    prefixW = prefix+"-"
  return prefixW

  
async def getPage(pageUrl , firstRecursion = True):

  try:
    await page.goto(pageUrl)
    await page.waitForFunction("""() => document.querySelectorAll('.search-landings-container, .prdct-cntnr-wrppr , .errorpagewrapper, .no-rslt-icon').length""", timeout=10000)
    await page.evaluate("document.body.style.zoom='20%'")

  except pyppeteer_errors.TimeoutError:
    if(firstRecursion):
      logAndPrint("!!! Page get timed out , trying again with "+pageUrl)
      return await getPage(pageUrl, False)
    else:
      logAndPrint("!!! Page get timed out , giving up with "+pageUrl)
      return False
  except pyppeteer_errors.NetworkError:
    logAndPrint("!!! Page get network error , trying again with "+pageUrl)
    if(firstRecursion):
      return await getPage(pageUrl, False)
    else:
      logAndPrint("!!! Page get network error , giving up with "+pageUrl)
      return False



async def fetchLinks():    
    global finished

    list_counter = 0
    try_counter = 0
    iteration_counter = 0
    
    lastFindTime = time.time()
    lastloadIndex = 1

    legacyContentLenght = 0
    reloadPageEverytimeMode = False

    DISTANCE_OF_CONTENT_FROM_BOTTOM = 0
    VIEWPORT_HEIGHT = 0

    
    try:
      DISTANCE_OF_CONTENT_FROM_BOTTOM = abs(await page.evaluate("""() => {
          const element = document.querySelector('.search-landings-container');
          if (element) {{
              const rect = element.getBoundingClientRect();
              const distance = rect.top - document.body.scrollHeight;
              return distance;
          }}
      }"""))

      VIEWPORT_HEIGHT = await page.evaluate("""() => {
        return window.innerHeight;
      }""")*5


    except TypeError as e:
      ## Probably a bad page was loaded like a 404 error or no results page
      ## We are doing nothing here as the reminder of the code is handling it 
      pass


    async def scrollToContent():
      await page.evaluate("window.scrollTo(0,document.body.scrollHeight);")
      time.sleep(0.1)

      await page.evaluate("window.scrollBy(0,{0})".format(((VIEWPORT_HEIGHT-DISTANCE_OF_CONTENT_FROM_BOTTOM)/5)-200))  


    
    while True:
      try:
        if(lastloadIndex >= 98 and not reloadPageEverytimeMode) :
          logAndPrint("Switching to reloadPageEverytimeMode")
          reloadPageEverytimeMode = True

        if(list_counter >= maximum):
          logAndPrint("Maximum number of items reached")
          return


        

        if(reloadPageEverytimeMode):
          if( await getPage(url+"?pi="+str(lastloadIndex+1)) == False):
            return
          legacyContentLenght = 0
          

          
        source = await page.content()    


          
        startIndex= source.find('<div class="prdct-cntnr-wrppr">')
        endIndex = -(len(source)-source.find('<div class="virtual"></div>'))

        cropped = source[startIndex:endIndex]
        cropped = cropped[cropped.find('<div class="p-card-wrppr with-campaign-view"'):]
        cropped = cropped[legacyContentLenght:-6]
        
        soup = BeautifulSoup("<div>"+cropped, 'lxml')
        cards = soup.find_all("div", {"class": "p-card-wrppr"})          
        
        
        
      
        if(len(cards) == 0):
          if(time.time() - lastFindTime > 10):
            logAndPrint("Fetching process is completed with "+str(len(valid_urls))+ " results found") 
            return  
          if(iteration_counter < 3):
            if(try_counter == 2):
              logAndPrint("No cards were found, skipping")
              return
          ## This is another failsafe
          ## if the program got 3 times in a row no results, it will scroll up and down the page
          ## and try again
          if try_counter % 4 == 0 and try_counter != 0:
            await page.evaluate("window.scrollTo(0, 0)")
            await scrollToContent()
            iteration_counter += 1
            try_counter += 1
            continue
          try_counter += 1
        else:
          try_counter = 0   


        for card in cards:
          for a in card.find_all("a"):
            lurl = a.get("href")
            if lurl not in valid_urls:
              valid_urls.append(lurl)
              productQueue.put(lurl)
              lastFindTime = time.time()
              list_counter += 1
            
        ## In case this is a page with only a handful of items and single page
        if(len(cards) < 20 and legacyContentLenght == 0):
          logAndPrint("Fetching process is completed with "+str(len(valid_urls))+ " results found") 
          return
            
        
        legacyContentLenght += len(cropped[0: -6])
        currentUrl = page.url

        if "?pi=" in currentUrl:
          if(lastloadIndex >  int(currentUrl.split("pi=")[1])):
            logAndPrint("Fetching process is completed with "+str(len(valid_urls))+ " results found") 
            return
          lastloadIndex = int(currentUrl.split("pi=")[1])
        else: 

          if(lastloadIndex >  1):
            logAndPrint("Fetching process is completed with "+str(len(valid_urls))+ " results found") 
            return
          
          lastloadIndex = 1

        

        
        if(not reloadPageEverytimeMode):
          if(iteration_counter % 40 == 0 and iteration_counter != 0):
            logAndPrint("Running get on "+url+"?pi="+str(lastloadIndex+1))
            if(await getPage(url+"?pi="+str(lastloadIndex+1)) == False):
              return
            legacyContentLenght = 0            
          else:
            await scrollToContent()
        

        time.sleep(0.5)
        

      except Exception as e:
        logAndPrint(e)
        logAndPrint(traceback.format_exc())
      
      iteration_counter += 1


def downloader(url,name):
  try:
    urllib.request.urlretrieve(url,name)    
    return True
  except:
    return False


def scrapePage(url):
  global get_pic_counter
  global finished
  global total_counter

  try:
    fileNameHeader = url.split("/")[-1].split("?")[0]
    prefixWW = prefixW()


    if(checkIfFileExists(os.path.join(rootPath,"meta",prefixWW + fileNameHeader +".meta"))):
      logAndPrint("File already exists, skipping...")
      return
    
    r =requests.get("https://trendyol.com"+url)
    searched = re.search("""(?<=window.__PRODUCT_DETAIL_APP_INITIAL_STATE__=)(.*)(?=;window.TYPageName=")""", r.content.decode('utf-8')).group()
    parsedJSON = json.loads(searched)

    metadata= {}
    metadata["name"] = parsedJSON["product"]["name"]
    metadata["color"] = parsedJSON["product"]["color"]
    metadata["url"] = parsedJSON["product"]["url"]
    metadata["gender"] = parsedJSON["product"]["gender"]
    metadata["brand"] = parsedJSON["product"]["brand"]
    metadata["attributes"]  = parsedJSON["product"]["attributes"] 
    

    with open(os.path.join(rootPath,"meta",prefixWW + fileNameHeader +".meta"), 'w', encoding='utf8') as outfile:
      json.dump(metadata, outfile, ensure_ascii=False)
      if isNoDownload:
        logAndPrint("Metadata for "+ str(get_pic_counter) +" is saved")
        pass
    
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



def downloadImages():
  global get_pic_counter
  global finished
  global total_counter

  with concurrent.futures.ThreadPoolExecutor() as executor:
    
    while (True):
      if(productQueue.empty()):
        if(finished):
          break
        else:
          time.sleep(0.1)
          continue

      if(total_counter >= maximum):
          finished = True
          break

      urls = productQueue.get()
      executor.submit(scrapePage, urls)
  
    
def clearBuffer():
  global total_counter
  if(isMaxPerCategory):
    total_counter = 0


async def Scrape(searchURL):
  if(await getPage(searchURL) == False):
    print("Thingy returned false")
    return
  time.sleep(1)
  logAndPrint("Fetching search results...")    
  await fetchLinks()



async def main():
  
  global finished
  global browser
  global page

  browser = await launch(headless=True, args=['--start-maximized'], defaultViewport=None)
  page = await browser.newPage()


  logAndPrint("Starting downloader...")
  downloaderThread = threading.Thread(target=downloadImages, args=(), daemon=True)
  downloaderThread.start()

  if(urlsPath == None):
    await Scrape(url)
  else:
    urls = getUrlListFromFile(urlsPath)
    for urll in urls:
      try:
        await Scrape(urll)
        logAndPrint("Done with "+urll)
      except Exception as e:
        logAndPrint("!!! AN ERROR OCCURED !!!")
        logAndPrint("Error on "+urll)
        logAndPrint(e)
        logAndPrint(traceback.format_exc())
      clearBuffer()

  finished = True
  downloaderThread.join()
  logAndPrint("Done")

if __name__ == "__main__":
  start_time = time.time()
  assert_args()
  asyncio.get_event_loop().run_until_complete(main())
  logAndPrint("--- %s seconds ---" % (time.time() - start_time))
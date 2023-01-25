import argparse
import time
from pyppeteer import launch
from pyppeteer import errors as pyppeteer_errors
from bs4 import BeautifulSoup
from tqdm import tqdm
import asyncio
from collections import defaultdict
import collections
import json



# Parse the command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('url',help='The base url that will be populated',
                        default= None, type=str)
args = parser.parse_args()

baseUrl = args.url


COLOR_CONSTANTS = [1,2,3,19,20,4,21,6,7,8,9,10,11,12,13,14,16,17,686230]
BEDEN_CONSTANTS = ["beden|xxs","beden|xs","beden|s","beden|m","beden|l","beden|xl","beden|xxl","beden|2xl","beden|3xl","beden|4xl","beden|5xl","beden|6xl","beden|7xl"]
FIT_CONSTANTS = ["179|16064","179|2861","179|2860","179|2042","179|2004","179|2043","179|22116","179|2001","179|2003","179|7199","179|2028","179|279663","179|666291"]
BRAND_CONSTANTS = ["101476","43","486","592","41","38","37","147","859","708","262","224","102767","324","109738","148833","150370","152406","104686","145554","136","639","44","33","101990","160","124","333","768","230","54","104189","125","108793","156","138","46"]

BRAND_ARGNAME = "wb"
COLOR_ARGNAME= "wcl"
BEDEN_ARGNAME= "vr"
FIT_ARGNAME= "attr"
PRICE_ARGNAME = "prc"


PRODUCT_THRESHOLD = 5000
PRODUCT_RISKY_THRESHOLD = 30000
ASSEMBLY_THRESHOLD = 5000



def tree(): return defaultdict()

def constructUrl(url,params):
    urlString = url
    for param in params:
        urlString += "&" + param

    return urlString

def generatePriceTree(argtree):
    PRICE_ARGNAME = "prc"
    priceList = [str(i) + "-" + str(i+5) for i in range(0, 1000, 5)]
    priceList.append("1000-10000")

    for price in priceList:
        argtree[PRICE_ARGNAME +"="+  price] = None

    return argtree


if baseUrl == None:
    print("Please specify the base url to populate.")
    exit()

def writeTreeToFile(tree, fileName):
    treeJson = json.dumps(tree)
    with open(fileName, 'w') as f:
        f.write(treeJson)
        


def writeListToFile(list, fileName):
    with open(fileName, 'w') as f:
        for item in list:
            f.write(item.strip() + '\n')


async def getPage(pageUrl , firstRecursion = True):

  try:
    await page.goto(pageUrl)
    await page.waitForFunction("""() => document.querySelectorAll('.search-landings-container, .prdct-cntnr-wrppr , .errorpagewrapper, .no-rslt-icon').length""", timeout=10000)

  except pyppeteer_errors.TimeoutError:
    if(firstRecursion):
      #print("!!! Page get timed out , trying again with "+pageUrl)
      return await getPage(pageUrl, False)
    else:
      #print("!!! Page get timed out , giving up with "+pageUrl)
      return False
  except pyppeteer_errors.NetworkError:
    #print("!!! Page get network error , trying again with "+pageUrl)
    if(firstRecursion):
      return await getPage(pageUrl, False)
    else:
      #print("!!! Page get network error , giving up with "+pageUrl)
      return False


async def getProductCount(url):
    try:
        if(await getPage(url) == False):
            return False
        source = await page.content()  
        soup = BeautifulSoup(source, 'html.parser')

        time.sleep(1)

        description = soup.find("div", {"class": "dscrptn"})
        
        product_count_string = description.contents[-1].split(" ")[-3].strip()

        if(product_count_string == "100.000+"):
            return 100000

        return int(product_count_string)

    except AttributeError:
        ### Pages that show no result at all
        return 0
    except ValueError:
        ## Pages that have no search result but show other recomendations
        return 0 


async def populateUrlsAboveThreashold(urlThree, argname, populatees, threashold, legacyArgs = [], recursion = False):

    with tqdm(urlThree) as iterative:
        if(recursion):
            iterative = urlThree

        for key in iterative:
            
            if(type(urlThree[key]) == collections.defaultdict):
                urlThree[key] = await populateUrlsAboveThreashold(urlThree[key], argname, populatees, threashold, legacyArgs + [key],True)
                continue

            
            if(type(urlThree[key]) == int):
                productCount = urlThree[key]
            else:
                url = constructUrl(baseUrl,  legacyArgs + [key])
                productCount = await getProductCount(url)

            if(productCount == False or productCount == 0):
                urlThree[key] = 0
                continue
            

            if(productCount < threashold):
                urlThree[key] = productCount
                continue
            

            branchTree = tree()
            for populatee in populatees:
                branchTree[argname + "=" + str(populatee)] = None

            urlThree[key] = branchTree

        return urlThree



def multiParamMerger(rawparams):
    def assamble_string(params, char):
        param_string = ""
        for param in params:
            param_string += param + char
        return param_string[:-1]
    
    if(COLOR_ARGNAME in rawparams[0]):
        param_vals = [param.split("=")[1] for param in rawparams]
        return COLOR_ARGNAME + "="+ assamble_string(param_vals,",")

    if(BRAND_ARGNAME in rawparams[0]):
        param_vals = [param.split("=")[1] for param in rawparams]
        return BRAND_ARGNAME + "="+ assamble_string(param_vals,",")
    
    if(BEDEN_ARGNAME in rawparams[0]):
        param_vals = [param.split("|")[1] for param in rawparams]
        return BEDEN_ARGNAME + "=beden|"+ assamble_string(param_vals,"_")
    
    if(FIT_ARGNAME in rawparams[0]):
        param_vals = [param.split("|")[1] for param in rawparams]
        return FIT_ARGNAME + "=179|"+ assamble_string(param_vals,"_")


    if(PRICE_ARGNAME in rawparams[0]):
        return rawparams[0]

    

    raise Exception("Unknown multi param type")





def AssembleUrlList(urlTree, legacyArgs = []):
    urlList = []

    buffer = []
    buffer_counter = 0


    for key in urlTree:

        if(type(urlTree[key]) == collections.defaultdict):
            urlList += AssembleUrlList(urlTree[key], legacyArgs + [key])
        
        if(type(urlTree[key]) == int):
            if(urlTree[key] == 0):
                continue
            
            if(buffer_counter + urlTree[key] > ASSEMBLY_THRESHOLD):
                urlList.append(constructUrl(baseUrl, legacyArgs + [multiParamMerger(buffer)]))
                buffer = [key]
                buffer_counter = urlTree[key]
                continue

            buffer.append(key)
            buffer_counter += urlTree[key]
    
    urlList.append(constructUrl(baseUrl, legacyArgs + [multiParamMerger(buffer)]))

    return urlList






async def main():
    global browser
    global page


    url_tree = tree()
    
    browser = await launch(headless=True, args=['--start-maximized'], defaultViewport=None)


    page = await browser.newPage()
    priceTree = generatePriceTree(url_tree)
    
    print("Populating price tree with color information")
    populatedTree = await populateUrlsAboveThreashold(priceTree, COLOR_ARGNAME, COLOR_CONSTANTS, PRODUCT_THRESHOLD)

    print("Populating price tree with beden information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, BEDEN_ARGNAME, BEDEN_CONSTANTS, PRODUCT_THRESHOLD)

    print("Populating price tree with fit information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, FIT_ARGNAME, FIT_CONSTANTS, PRODUCT_THRESHOLD)

    print("Populating price tree with brand information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, BRAND_ARGNAME, BRAND_CONSTANTS, PRODUCT_RISKY_THRESHOLD)

    #This serves to only record the product count of end nodes 
    print("Populating price tree with product count information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, "", "", float('inf')) 
    populatedUrlList = AssembleUrlList(populatedTree)

    # For debugging purposes
    #writeTreeToFile(populatedTree, "populated_tree_"+str(time.time())+".txt")
    
    writeListToFile(populatedUrlList, "populated_urls_"+str(time.time())+".txt")

    print("Generated populated_urls_"+str(time.time())+".txt")
    await browser.close()

if __name__ == "__main__":
    start_time = time.time()
    asyncio.get_event_loop().run_until_complete(main())
    print("--- %s seconds ---" % (time.time() - start_time))
    exit()
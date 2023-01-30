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
import logging
import os


# Parse the command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('url',help='The base url that will be populated',
                        default= None, type=str)


parser.add_argument('--path',
                        dest='path', help='The path of the file that will be generated with the populated urls',
                        default= None, required=False,type=str)

args = parser.parse_args()
baseUrl = args.url
path = args.path


COLOR_CONSTANTS =   [1,2,3,19,20,4,21,6,7,8,9,10,11,12,13,14,16,17,686230]
BEDEN_CONSTANTS = ["beden|xxs","beden|xs","beden|s","beden|m","beden|l","beden|xl","beden|xxl","beden|2xl","beden|3xl","beden|4xl","beden|5xl","beden|6xl","beden|7xl"]
FIT_CONSTANTS = ["179|16064","179|2861","179|2860","179|2042","179|2004","179|2043","179|22116","179|2001","179|2003","179|7199","179|2028","179|279663","179|666291"]
BRAND_CONSTANTS = ["101476","43","486","592","41","38","37","147","859","708","262","224","102767","324","109738","148833","150370","152406","104686","145554","136","639","44","33","101990","160","124","333","768","230","54","104189","125","108793","156","138","46"]

BRAND_ARGNAME = "wb"
COLOR_ARGNAME= "wcl"
BEDEN_ARGNAME= "vr"
FIT_ARGNAME= "attr"
PRICE_ARGNAME = "prc"

PRODUCT_THRESHOLD = 5000
PRODUCT_RISKY_THRESHOLD = 7000
ASSEMBLY_THRESHOLD = 5000

def assertArgs():
    global baseUrl
    global path

    baseUrl = args.url
    path = args.path

    if baseUrl == None:
       logAndPrint("Please specify the base url to populate.")
       exit()
            
    if path != None:
        if ".txt" not in path:
            logAndPrint("The path should be to a .txt file")

    if path == None:
        onvironDirname = os.environ.get('DIRNAME')
        if onvironDirname != None:
            path = os.path.join("/Dataset",onvironDirname.strip(),"urls.txt")
    
    if "wc=" not in baseUrl:
        logAndPrint("Please give the url in the parameter format. (https://www.trendyol.com/sr?wc=75&wg=2)")
        exit()
    if BRAND_ARGNAME in baseUrl or COLOR_ARGNAME in baseUrl or BEDEN_ARGNAME in baseUrl or FIT_ARGNAME in baseUrl or PRICE_ARGNAME in baseUrl:
        logAndPrint("Please give the url in the simplest form without any filtering")
        exit()


def tree(): return defaultdict()


def createDir(path):
  if not os.path.exists(path):
    os.makedirs(path)

def createNecessaryDirs():
    createDir(os.path.join(os.path.dirname(__file__), "logs"))
    if path != None:
        createDir(path[:path.rfind("/")])

def logAndPrint(message):
  logging.info(message)
  print(message,end='\n',flush=True)





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
            #logAndPrint("!!! Page get timed out , trying again with "+pageUrl)
            return await getPage(pageUrl, False)
        else:
            #logAndPrint("!!! Page get timed out , giving up with "+pageUrl)
            return False
    except pyppeteer_errors.NetworkError:
        #logAndPrint("!!! Page get network error , trying again with "+pageUrl)
        if(firstRecursion):
            return await getPage(pageUrl, False)
        else:
            #logAndPrint("!!! Page get network error , giving up with "+pageUrl)
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
    iteratonCount = 1

    for key in urlThree:

        if not recursion:
            logAndPrint("{0}/{1}".format(iteratonCount, len(urlThree)))
        iteratonCount += 1

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

    if(len(rawparams) == 0):
        return []
    
    if(COLOR_ARGNAME in rawparams[0]):
        param_vals = [param.split("=")[1] for param in rawparams]
        return [COLOR_ARGNAME + "="+ assamble_string(param_vals,",")]

    if(BRAND_ARGNAME in rawparams[0]):
        param_vals = [param.split("=")[1] for param in rawparams]
        return [BRAND_ARGNAME + "="+ assamble_string(param_vals,",")]
    
    if(BEDEN_ARGNAME in rawparams[0]):
        param_vals = [param.split("|")[1] for param in rawparams]
        return [BEDEN_ARGNAME + "=beden|"+ assamble_string(param_vals,"_")]
    
    if(FIT_ARGNAME in rawparams[0]):
        param_vals = [param.split("|")[1] for param in rawparams]
        return [FIT_ARGNAME + "=179|"+ assamble_string(param_vals,"_")]

    if(PRICE_ARGNAME in rawparams[0]):

        pricePairs = [[int(prc) for prc in param.split("=")[1].split("-")] for param in rawparams]

        minPrice = min([pair[0] for pair in pricePairs])
        maxPrice = max([pair[1] for pair in pricePairs])

        return [PRICE_ARGNAME + "=" + str(minPrice) + "-" + str(maxPrice)]

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
                urlList.append(constructUrl(baseUrl, legacyArgs + multiParamMerger(buffer)))
                buffer = [key]
                buffer_counter = urlTree[key]
                continue
            buffer.append(key)

            buffer_counter += urlTree[key]
    
    urlList.append(constructUrl(baseUrl, legacyArgs + multiParamMerger(buffer)))
    return urlList




async def main():
    global browser
    global page


    url_tree = tree()

    
    browser = await launch(headless=True, args=['--start-maximized','--no-sandbox'], defaultViewport=None, autoClose=False)


    page = await browser.newPage()
    priceTree = generatePriceTree(url_tree)
    

    logAndPrint("Populating price tree with color information")
    populatedTree = await populateUrlsAboveThreashold(priceTree, COLOR_ARGNAME, COLOR_CONSTANTS, PRODUCT_THRESHOLD)

    logAndPrint("Populating price tree with beden information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, BEDEN_ARGNAME, BEDEN_CONSTANTS, PRODUCT_THRESHOLD)

    logAndPrint("Populating price tree with fit information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, FIT_ARGNAME, FIT_CONSTANTS, PRODUCT_THRESHOLD)

    logAndPrint("Populating price tree with brand information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, BRAND_ARGNAME, BRAND_CONSTANTS, PRODUCT_RISKY_THRESHOLD)

    #This serves to only record the product count of end nodes 
    logAndPrint("Populating price tree with product count information")
    populatedTree = await populateUrlsAboveThreashold(populatedTree, "", "", float('inf'))

    populatedUrlList = AssembleUrlList(populatedTree)
    

    if(path != None):
        urlFilename = path
        
        if "/" in urlFilename:
            treeFilename = os.path.join(urlFilename[:urlFilename.rfind("/")], "populated_tree_"+str(time.time())+".txt")
        else:
            treeFilename = "populated_tree_"+str(time.time())+".txt"
    else:
        urlFilename = "populated_urls_"+str(time.time())+".txt"
        treeFilename = "populated_tree_"+str(time.time())+".txt"


    writeListToFile(populatedUrlList, urlFilename)

    # For debugging purposes
    writeTreeToFile(populatedTree, treeFilename)


    logAndPrint("Generated {0} with {1} urls".format(urlFilename, len(populatedUrlList)))

    await browser.close()

if __name__ == "__main__":
    start_time = time.time()
    assertArgs()
    createNecessaryDirs()
    logging.basicConfig(filename= os.path.join(os.path.dirname(__file__), "logs",'populate_trendyol_url_'+str(time.time())+'.log'), level=logging.INFO,  format='%(asctime)s %(message)s')
    asyncio.run(main())
    logAndPrint("--- %s seconds ---" % (time.time() - start_time))
    exit()
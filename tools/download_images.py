import requests
import time
import os
import argparse
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool


#Get arguments using argperse library for the path of the file and the path of the directory where the images will be downloaded
def parse_args():
    parser = argparse.ArgumentParser(description='Download images from a list of URLs')
    parser.add_argument('file', type=str, help='Path to the file containing the URLs')
    parser.add_argument('--dir', type=str, help='Path to the directory where the images will be downloaded', default=".")
    parser.add_argument('--prefix',dest='prefix', help='A prefix that will be put in front of all files downloaded, use this if you are going to make multiple downloads on the same directory. No prefix at default',default="", type=str)
    args = parser.parse_args()
    return args

def formatPrefix(px):
    prefixI = ""
    if(px != ""):
        prefixI = px+"-"
    return prefixI

args=parse_args()
filePath = args.file
dirPath = args.dir
prefix = formatPrefix(args.prefix)


#Create directory in dirPath if it does not exist
if not os.path.exists(dirPath):
    os.makedirs(dirPath)



def read_urls(filename):
    with open(filename) as file:
        lines = file.readlines()
        lines = [line.strip().split(',') for line in lines]
        return lines


def download_url(args):    
    try:
        t0 = time.time()
        imageNumber, variantNumber,  url = args[0], args[1], args[2]

        r = requests.get(url)

        with open(os.path.join(dirPath,prefix+imageNumber), 'wb') as f:
            f.write(r.content)
        return(url, time.time() - t0)

    except Exception as e:
        print('Exception in download_url():', e)

def download_parallel(args):
    cpus = cpu_count()
    results = ThreadPool(cpus - 1).imap_unordered(download_url, args)
    for result in results:
        ##Catch InvalidChunkLength error
        if(result == None):
            print("InvalidChunkLength error")
            continue
        print('Downloaded ', result[0], ' in ', format(result[1], ".1f"), " seconds")
       


def main():
    urls = read_urls(filePath)
    urls = sorted(urls, key=lambda x: x[0])

    download_parallel(urls)
    

if __name__ == "__main__":
  main()
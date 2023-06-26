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
    parser.add_argument('--num_workers', type=int, help='Number of workers to use', default=cpu_count() - 1)
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
num_workers = args.num_workers
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

        r = requests.get(url, stream=True)

        with open(os.path.join(dirPath,prefix+imageNumber), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        return(url, time.time() - t0)

    ## Catch InvalidChunkLength error
    except requests.exceptions.ChunkedEncodingError as e:
        print('Exception in download_url():', e)
        return None

    except Exception  as e:
        print('Exception in download_url():', e)
        return 0

def download_parallel(args):
    cpus = cpu_count()
    results = ThreadPool(num_workers).imap_unordered(download_url, args)

    for result in results:
        ##Catch InvalidChunkLength error
        if(result == None):
            print("InvalidChunkLength error")
            continue
        if(result == 0):
            print("Error downloading image")
            continue

        print('Downloaded ', result[0], ' in ', format(result[1], ".1f"), " seconds")
       

def main():
    print("Reading URLs from file...")
    urls = read_urls(filePath)
    urls = sorted(urls, key=lambda x: x[0])

    print("Downloading images...")
    download_parallel(urls)
    

if __name__ == "__main__":
  main()
# encoding:utf-8

import json
import os
import argparse
import pandas as pd
import glob
from tqdm import tqdm

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(
        description='Category analysis tool for .meta files')
    parser.add_argument('-d', action='store_true', default=False,
                    dest='details',
                    help='Create a .txt file with attribute details of each metadata file')
    parser.add_argument('-xlsx', action='store_true', default=False,
                    dest='xlsx',
                    help='Create a .xlsx file with overall attribute and category details of all metadata files in the directory')
    parser.add_argument('-csv', action='store_true', default=False,
                    dest='csv',
                    help='Create a .csv with attribute list, this mode is needed to be used alongside with --labelmap argument')
    parser.add_argument('--path',
                        dest='path', help='The path that contains .meta files',
                        required=True, type=str)
    parser.add_argument('--labelmap',
                        dest='labelmap', help='The path to the .json file that contains the labelmap for .csv file ',
                        required=False, default="siksok34234", type=str)
    args = parser.parse_args()
    return args


args = parse_args()
path = os.path.join(args.path,".")
listOfImages = []

isDetailsMode = args.details
isCSVMode = args.csv
isXLSXMode = args.xlsx

labelMapPath = args.labelmap

assert not (isDetailsMode == False and isCSVMode == False and isXLSXMode == False), "You have to select one of three modes : -csv , -d , -xlsx "
    
assert not (isCSVMode and labelMapPath == "siksok34234"), "You have to specify a txt file with --whitelist command to use csv mode, see -h for help"


labelMap = None

attributeMap = {}
attributeMap["gender"] = [] 

details =[]
csvLines = []



def getAttributes(filename,meta):

    ## Add gender to the attribute map if it already doesnt have it
    gender = meta["gender"]["name"]
    if gender not in attributeMap["gender"]:
        attributeMap["gender"].append(gender)



    ## Iterate through all attributes and add them to the attribute map if it already doesn't have them

    attributes = meta["attributes"]
    allAtbs = []


    csvLine= [0]*8

    
    for attribute in attributes:
        key = attribute["key"]["name"]
        value = attribute["value"]["name"]

        allAtbs.append(value)

        if isCSVMode:
            
            def first(iterable, default=None):
                for item in iterable:
                    return item
                return default
            if key in labelMap:
                try:
                    item = first((x for x in labelMap[key]["attributes"] if value in x["subattributes"]), False)
                except Exception as e:
                    item = False
                
                if item != False:
                    csvLine[list(labelMap).index(key)] = labelMap[key]["attributes"].index(item)


        if not attributeMap.get(key):
            attributeMap[key] = []
            attributeMap[key+" Count"] = []
            

        if value not in attributeMap[key]:
            attributeMap[key].append(value)
            attributeMap[key+" Count"].append(1)
        else:
            index = attributeMap[key].index(value)
            attributeMap[key+" Count"][index] = attributeMap[key+" Count"][index]+1
    
    if isCSVMode:
        global listOfImages

        for imageName in (x for x in listOfImages if (filename[0:-5]+"_") in x):
            completeLine = [imageName.split('\\')[-1]]
            completeLine.extend(csvLine)
            csvLines.append(completeLine)



        

        
        
    if isDetailsMode:
        atbsStr = ""
        for atb in allAtbs:
            atbsStr += atb+ " , "

        details.append(filename + " || " + atbsStr[0:-3])


def pad_dict_list(dict_list, padel):
    lmax = 0
    for lname in dict_list.keys():
        lmax = max(lmax, len(dict_list[lname]))
    for lname in dict_list.keys():
        ll = len(dict_list[lname])
        if  ll < lmax:
            dict_list[lname] += [padel] * (lmax - ll)
    return dict_list

def writeToTxt(list):
    with open('details.txt', 'w') as filehandle:
        for listitem in list:
            filehandle.write('%s\n' % listitem)

def main():   
    global listOfImages
    global labelMap

    parseErrors = 0    
    
    if(isCSVMode): 
        try:
            with open(labelMapPath,encoding='utf-8') as f:
                
                labelMap = json.load(f)
        except Exception as e:
            print("Could not find the file "+labelMapPath)
            return

    if(isCSVMode):
        print("Fetching image paths...")
        listOfImages = glob.glob(path+'/*.jpg')


    print("Fetching meta files...")
    metaFilePaths=  glob.glob(path+'/*.meta')
    for metaFilePath in tqdm(metaFilePaths):
        try:
            metaFile = open(metaFilePath,encoding='utf-8')
            meta = json.load(metaFile)
            getAttributes(metaFilePath.split("/")[-1],meta)
        except KeyError:
            print("KeyError in parsing "+metaFilePath)
            parseErrors += 1
        except Exception as e:
            print("An exception occurred during parsing "+metaFilePath)
            parseErrors += 1
        ## Remove this to iterate through whole directory
        ## Only for testing
        #break 
    
    print("Parsing finished with "+str(parseErrors)+" errors")
    

    if isCSVMode:
        try:
            header = ["File Name"]
            for category in list(labelMap):
                header.extend([labelMap[category]["name"]])

            df = pd.DataFrame(csvLines, columns=header)
            df.to_csv('result.csv', index = False,header= True, encoding='utf-8')


            print("result.csv is succesfully created")    
        except Exception as e:
            print("An exception occurred during creating result.csv")
            print(e)
    
    if isXLSXMode:    
        try:
            df = pd.DataFrame(data=pad_dict_list(attributeMap,""))
            df.to_excel('result.xlsx', index = False)
            print("Results.xlsx is succesfully created")    
        except Exception as e:
            print("An exception occurred during creating results.xlsx"),
            print(e)
    if isDetailsMode:
        try:
            writeToTxt(details)
            print("details.txt is succesfully created")    
        except Exception as e:
            print("An exception occurred during creating details.txt")
            print(e)
        
        
if __name__ == "__main__":
  main()
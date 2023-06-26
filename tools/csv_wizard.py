import os
import glob
import json
import pandas as pd
from tqdm import tqdm
import threading
import concurrent.futures



#Hyperparameters
LABEL_MAP_PATH = "D:/Workzone/Datasets/Trendyol Attribute/labelmap.json"
TYPES_PATH = "D:/Workzone/Datasets/Trendyol Categoriler/types.txt"
META_DIRECTORY_PATH = "D:/Workzone/Datasets/TrendyolMerged/meta"


#Global variables
typeMap = {}
df = pd.DataFrame()
csv_rows = []
parseErrors = 0

labelMap_categories = {}
labelMap_attributes = {}
labelMap_exceptions = {}





def initilizeDataframe():
    columnNames = ["File Name"]
    for key in labelMap_attributes.keys():
        columnNames.append(labelMap_attributes[key]["name"])

    return pd.DataFrame(columns=columnNames)
        
def readLabelMap():
    labelMapl = {}
    
    #Find the name for the not found exception
    try:
        with open(LABEL_MAP_PATH, encoding="utf-8") as f:
            labelMapl = json.load(f)
    except FileNotFoundError as e:
        print("Could not find the file "+LABEL_MAP_PATH)
        return
    return labelMapl

def processLabelMapAttributes(labelMap_attributesl):
    for key in labelMap_attributesl.keys():
        LabelClass = labelMap_attributesl[key]
        subattribute_dict = {subattr: attr["id"] for attr in LabelClass["attributes"] for subattr in attr["subattributes"]}
        labelMap_attributesl[key]["subattribute_dict"] = subattribute_dict
    return labelMap_attributesl


def readTypes():
    typeMapl = {}
    try:
        with open(TYPES_PATH,encoding='utf-8') as f:
            #Read lines of txt file with for
            for line in tqdm(f):
                lineElements = line.strip().split(",")
                typeList = lineElements[2:]
                typeList.reverse()
                typeMapl[lineElements[0]] = typeList
    except FileNotFoundError as e:
        print("Could not find the file "+TYPES_PATH)
        return

    return typeMapl


def getMetaFileList():
    return os.listdir(META_DIRECTORY_PATH)


def getAttributes(metaFilePath,meta):

    def findType(typeList):
        for type in typeList:
            subattribute_dict = labelMap_attributes["0"]["subattribute_dict"]
            typeId = subattribute_dict.get(type, -1)
            if typeId != -1:
                return typeId
        return -1

    def findGender(gender):
        subattribute_dict = labelMap_attributes["1"]["subattribute_dict"]
        genderId = subattribute_dict.get(gender, -1)
        return genderId
  
    global df
    temporaryEntry = {}


    metaFileName = os.path.basename(metaFilePath).split(".")[0]
    temporaryEntry["File Name"] = metaFileName
    
    try:
        typeList = typeMap[metaFileName]
        typeId = findType(typeList)
        temporaryEntry[labelMap_attributes["0"]["name"]] = typeId
    except KeyError as e:
        temporaryEntry[labelMap_attributes["0"]["name"]] = -1

    try:
        gender = meta["gender"]["name"].strip()
        genderId = findGender(gender)
        temporaryEntry[labelMap_attributes["1"]["name"]] = genderId
    except KeyError as e:
        temporaryEntry[labelMap_attributes["1"]["name"]] = -1


    attributes = meta["attributes"]
    attributeMap = {}

    for attribute in attributes:
        key = attribute["key"]["name"]
        value = attribute["value"]["name"]

        class_id = labelMap_categories.get(key, -1)
        if(class_id == -1):
            continue
        class_name = labelMap_attributes[class_id]["name"]

        attribute_id = labelMap_attributes[class_id]["subattribute_dict"].get(value, -1)
        if(attribute_id == -1):
            continue
        
        ##If the attributeMap does not have a key class_name, add an empty list to it
        if class_name not in attributeMap:
            attributeMap[class_name] = []
        
        attributeMap[class_name].append(attribute_id)

    for key in attributeMap.keys():
        if len(attributeMap[key]) == 1:
            temporaryEntry[key] = attributeMap[key][0]
        else:
            listAttribute = attributeMap[key]
            listAttribute = list(dict.fromkeys(listAttribute))
            listAttributeString = "|".join(str(x) for x in listAttribute)
            
            temporaryEntry[key] = listAttributeString
    

    for column in df.columns:
        if column not in temporaryEntry:
            temporaryEntry[column] = -1

    

    csv_row = []
    for column in df.columns:
        csv_row.append(temporaryEntry[column])
    
    return csv_row

def threadParseMetaFile(metaFileName):
    global parseErrors
    global csv_rows

    try:
        metaFilePath = os.path.join(META_DIRECTORY_PATH,metaFileName)
        metaFile = open(metaFilePath,encoding='utf-8')
        meta = json.load(metaFile)
        csv_row_entry = getAttributes(metaFilePath,meta)
        csv_rows.append(csv_row_entry)
    except KeyError:
        print("KeyError in parsing "+metaFileName)
        parseErrors += 1
    except Exception as e:
        print("An exception occurred during parsing "+metaFileName)
        print(e)
        parseErrors += 1




def main():
    global typeMap 
    global labelMap_categories
    global labelMap_attributes
    global labelMap_exceptions
    global df
    global csv_rows
    global parseErrors


    print("Reading label map")
    labelMap = readLabelMap()
    labelMap_categories = labelMap["categories"]
    labelMap_attributes = processLabelMapAttributes(labelMap["attributes"])
    labelMap_exceptions = labelMap["exceptions"]

    print("Reading categories")
    typeMap = readTypes()

    print("Initializing dataframe")
    df = initilizeDataframe()

    print("Reading meta file list")
    metaFilePaths = getMetaFileList()

    csv_rows = []
    print("Parsing meta files")
        
    with tqdm(total=len(metaFilePaths)) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(threadParseMetaFile , metaFileName) for metaFileName in metaFilePaths]

            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

    print("Parsing finished with "+str(parseErrors)+" errors")

    #Adding the csv rows to the dataframe using concatinate
    df = pd.concat([df,pd.DataFrame(csv_rows,columns=df.columns)],ignore_index=True)

    print("Writing to csv")
    df.to_csv("output.csv",index=False, encoding='utf-8-sig')
    print("CSV written to output.csv")
    print("Done")



if __name__ == "__main__":
    main()  
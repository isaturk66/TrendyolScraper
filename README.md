
## Getting Started

This is a script written in python 3 that uses selenium to scrape images and metadata of Trendyol.com. Also a attribute analysis script is included to generate excel and log files that describes the downloaded data. This script has a feature to generate .csv files according to a labelmap so that downloaded dataset can easily be used for machine learning.

### Installation

In order to install packages required to run the scripts, run the following command
* npm
  ```sh
  pip install -r requirements.txt
  ```

## Usage

This repository has two different scripts. The main script that does the scraping is named TrendyolScraper.js

These are the arguments for TrendyolScraper

* **--url** &nbsp;&nbsp;  The url of the trendyol search that will be scraped. REQUIRED

* **--path** &nbsp;&nbsp;  The path of the directory that all the image and .meta files will be downloaded into. REQUIRED

* **--max** &nbsp;&nbsp;  Maximum number of images that will be downloaded, no limit as default. OPTIONAL

* **--prefix** &nbsp;&nbsp;  A prefix that will be put in front of all files downloaded, use this if you are going to make multiple downloads on the same directory otherwise files from the first dowload will be overridden. No prefix at default OPTIONAL

**Example usage**

 ```sh
  python TrendyolScraper.py --url "https://www.trendyol.com/erkek-gomlek-x-g2-c75" --path ./Dataset --max 100 --prefix m
  ```
Note: Do not pass a --max argument if you want to dowload as much as possible




&nbsp;


Second script is the attribute_analysis.py which provides few tools for interpreting the data that you downloaded

This script has three modes,

* **-xlsx** &nbsp;&nbsp;  The script will generate excel file that contains all the attribute categories and attributes found within the metadata of the images in the specified directory along with the statistics of how many images were labeled with those attributes.

* **-d** &nbsp;&nbsp;  The script will create a .txt file with detailed information of which atttributes were labeled for every image file in the specified directory.

* **-csv** &nbsp;&nbsp;  The script will generate a .csv file that describes the entire dataset found in the specified directory according to a labelmap file, this has to be used along with --labelmap argument. See the description of --labelmap argument for detailed explanation of how to use this mode

also the script has two arguments

*  **--path** &nbsp;&nbsp;  The path of the directory that will be scanned for .meta files. REQUIRED

* **--labelmap** &nbsp;&nbsp;  The path to the .json file that contains the labelmap for .csv file

An example label:

```sh
{
    "Kol Tipi": { //The exact name of the category as found in the .meta files
        "name": "Sleeve Type", //The name of the category that will be written into the .csv file, you can change this as you want
        "attributes": [ //List of attributes that belong to the category
            {
                "name": "Short Sleeve", //The name of the attribute, you can change this as you want. This is not written into .csv file and is here for postprocessing purposes
                "subattributes": [ //List of the exact names of the attributes as found in the .meta files, if you put multiple names they will be merged into this single attribute
                    "Kısa Kol",
                    "Kısa"
                ]
            }
        ]
    },
    "Renk" : {...}
}
```

Important note: for the "exact names" you need the exact names of the attributes that are given inside .meta files, You can generate a excel file by running this script in -xlsx mode to see all of the exact names of the categories and attributes easily.

See example_labelmap.json for a complete example of a labelmap generated suitable to a dataset dowloaded from the links https://www.trendyol.com/kadin-t-shirt-x-g1-c73 and https://www.trendyol.com/erkek-t-shirt-x-g2-c73


**Example usage**
```sh
python attribute_analysis.py  --path ./Dataset --labelmap example_labelmap.json
```


The csv file created with this script may look like this:
```sh
File Name,Gender,Color,Sleeve type,Collar Type,Pattern,Material Type,Fit,Style
m-1003_2.jpg,0,3,0,0,0,1,3,0
```

Numbers like 0 and 3 in the csv corresponds to the index of the attributes as they were given in the order of your labelmap.
For example the firt 3 in the sequence point to the fourth attribute that was given in the "attributes" list of the color category, which was green for my case.
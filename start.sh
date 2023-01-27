#!/bin/bash

python3 /TrendyolScraper/tools/populate_trendyol_url.py "$URL" --path "/Dataset/$DIRNAME/urls.txt"
python3 /TrendyolScraper/TrendyolScraper.py -n -l --urlsPath "/Dataset/$DIRNAME/urls.txt" --path "/Dataset/$DIRNAME"
cp -r /TrendyolScraper/logs
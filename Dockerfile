
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3.9 python3.9-dev && apt-get install -y python3-pip

RUN mkdir /Dataset

WORKDIR /TrendyolScraper

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .


## To run Pyppeteer and chromium
RUN apt-get install -y gconf-service \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2  \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils  \
    wget  \
    libcairo-gobject2 \
    libxinerama1 \
    libgtk2.0-0 \
    libpangoft2-1.0-0 \
    libthai0 \
    libpixman-1-0 \
    libxcb-render0 \
    libharfbuzz0b \
    libdatrie1 \
    libgraphite2-3 \
    libgbm1

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/chrome.list


CMD ["python3" , "/TrendyolScraper/tools/populate_trendyol_url.py"]


import concurrent.futures
import requests
from bs4 import BeautifulSoup
import argparse
from datetime import datetime
from tqdm import tqdm



def fetch_and_parse(entry):
    filename, url= entry.strip().split(",")
    # Fetch the contents of the URL
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the contents of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first product-detail-breadcrumb full-width
        categorieBar = soup.find('div', class_='product-detail-breadcrumb full-width')
        # Find all a tags in the product-detail-breadcrumb full-width
        categorie = categorieBar.find_all('a')
        # Get all titles from the a tags
        categorieTitles = [x.get('title') for x in categorie]
        #Eliminate all None values
        categorieTitles = [x for x in categorieTitles if x is not None]
        with open(output_file_name, 'a', encoding='utf8') as f:
            f.write(f"{filename},{url},{','.join(categorieTitles)}\n")
    else:
        #print(f"Failed to fetch {url}")
        pass


if __name__ == '__main__':
    start_time = datetime.now()
    global output_file_name
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_file_name = f"output_{timestamp}.txt"

    parser = argparse.ArgumentParser(description='Fetch and parse URLs from a file')
    parser.add_argument('filename', metavar='filename', type=str, help='name of the file containing URLs')
    args = parser.parse_args()

    # Read the URLs from the file
    with open(args.filename, 'r') as f:
        entries = [line.strip() for line in f]

    # Use a ThreadPoolExecutor to fetch and parse each URL concurrently
    with tqdm(total=len(entries)) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit each URL to the executor
            futures = [executor.submit(fetch_and_parse, entry) for entry in entries]

            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

    print("Done")
    #total execution timein format HH:MM:SS
    print(f"Total execution time: {datetime.now() - start_time}")
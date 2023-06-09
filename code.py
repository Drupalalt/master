import os
import requests
from bs4 import BeautifulSoup
import logging
import concurrent.futures

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def save_data_to_file(folder, file_name, content):
    with open(os.path.join(folder, file_name), "w", encoding="utf-8") as file:
        file.write(content)

def extract_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from URL: {url} - {e}")
        return None

def read_links_file(file_name):
    with open(file_name, "r") as links_file:
        links = [link.strip() for link in links_file.readlines()]
    return links

def process_url(link, data_folder):
    soup = extract_data_from_url(link)

    if soup is None:
        logging.warning(f"Skipping URL: {link} due to an error while fetching data")
        return False, link

    heading_element = soup.find("h1")

    if heading_element is None:
        logging.warning(f"Couldn't find heading for URL: {link}")
        return False, link

    heading = heading_element.text.strip()

    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        heading = heading.replace(char, '_')

    first_letter = heading[0].upper()
    letter_folder = os.path.join(data_folder, first_letter)
    create_folder(letter_folder)

    content_selector = ".mw-parser-output"
    content_element = soup.select_one(content_selector)

    if content_element is None:
        logging.warning(f"Couldn't find main content for URL: {link}")
        return False, link

    content = content_element.text.strip()

    file_name = f"{heading}.txt"
    save_data_to_file(letter_folder, file_name, content)
    logging.info(f"Successfully saved data from URL: {link} to {os.path.join(letter_folder, file_name)}")
    return True, link

def main():
    data_folder = "Data"
    create_folder(data_folder)

    links = read_links_file("links.txt")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_url, link, data_folder) for link in links]

        failed_links = [future.result()[1] for future in futures if not future.result()[0]]

    if failed_links:
        logging.info("Retrying failed URLs...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            retry_futures = [executor.submit(process_url, link, data_folder) for link in failed_links]

            retried_links = [future.result()[1] for future in retry_futures if not future.result()[0]]

        if retried_links:
            logging.warning(f"Saving {len(retried_links)} failed URLs to skip.txt")
            with open("skip.txt", "w") as skip_file:
                for link in retried_links:
                    skip_file.write(f"{link}\n")

if __name__ == "__main__":
    main()

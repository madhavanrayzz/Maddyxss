import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import Fore, Style
import requests
from requests.exceptions import ConnectionError

# Load constructed URLs from the file
with open('constructed_urls.txt', 'r') as file:
    constructed_urls = [line.strip() for line in file.readlines()]

# Function to set up Chrome WebDriver
def setup_chrome_driver(webdriver_path, port):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument(f'--remote-debugging-port={port}')
    service = ChromeService(executable_path=webdriver_path)
    return webdriver.Chrome(service=service, options=chrome_options)

# Function to load progress from file
def load_progress():
    progress = {}
    try:
        with open('progress.txt', 'r') as progress_file:
            for line in progress_file:
                instance_id, last_index = line.strip().split(':')
                progress[int(instance_id)] = int(last_index)
    except FileNotFoundError:
        progress = {i: 0 for i in range(num_instances)}
    return progress

# Function to save progress to file
def save_progress(progress):
    with open('progress.txt', 'w') as progress_file:
        for instance_id, last_index in progress.items():
            progress_file.write(f"{instance_id}:{last_index}\n")

# Function to check if the page is fully loaded
def wait_for_page_load(driver, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except Exception as e:
        print(f"Page did not load within {timeout} seconds: {str(e)}")
        return False
    return True

# Function to check internet connectivity
def check_internet_connection():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except ConnectionError:
        return False

# Function to test URLs
def test_xss(url_chunk, webdriver_path, port, instance_id, progress):
    driver = setup_chrome_driver(webdriver_path, port)
    
    last_index = progress.get(instance_id, 0)
    url_chunk = url_chunk[max(0, last_index-50):]  # Resume from the last tested URL, retrying the last 50 URLs if necessary
    
    with open('alert_found.txt', 'a') as alert_file, open('noalert.txt', 'a') as noalert_file:
        for index, url in enumerate(url_chunk, start=max(0, last_index-50)):
            print(f"Instance {instance_id} testing URL: {url}")
            retries = 3
            backoff = 2  # Exponential backoff factor
            while retries > 0:
                if not check_internet_connection():
                    print(f"Instance {instance_id}: No internet connection. Waiting...")
                    time.sleep(5)  # Wait and retry if the internet connection is down
                    continue
                
                try:
                    driver.get(url)
                    if wait_for_page_load(driver):  # Wait for the page to fully load
                        try:
                            alert = driver.switch_to.alert
                            alert.accept()
                            alert_file.write(f"{url}\n")
                            print(Fore.RED + f"Instance {instance_id}: Alert detected for URL: {url}" + Style.RESET_ALL)
                        except Exception:
                            noalert_file.write(f"{url}\n")
                            print(f"Instance {instance_id}: No alert detected for URL: {url}")
                        break  # If successful, exit the retry loop
                    else:
                        retries -= 1
                        print(f"Instance {instance_id}: Retrying URL: {url}, attempts left: {retries}")
                except Exception as e:
                    print(f"Instance {instance_id}: Error loading URL: {url} - {str(e)}")
                    retries -= 1
                    if retries > 0:
                        wait_time = backoff ** (3 - retries)  # Exponential backoff
                        print(f"Instance {instance_id}: Waiting {wait_time} seconds before retrying...")
                        time.sleep(wait_time)

            if retries == 0:
                print(f"Instance {instance_id}: Skipping URL after 3 failed attempts: {url}")
            
            progress[instance_id] = index
            save_progress(progress)  # Save progress after each URL
    
    driver.quit()

# Input number of instances
num_instances = int(input("Enter the number of instances: "))

# Load the current progress or initialize it
progress = load_progress()

# Define paths and ports for instances
instances = []
for i in range(num_instances):
    instances.append({'webdriver_path': '/home/maddy/Desktop/esty/a/c/chromedriver', 'port': 9222 + i})

# Divide the constructed URLs among instances
chunk_size = len(constructed_urls) // num_instances
url_chunks = [constructed_urls[i:i + chunk_size] for i in range(0, len(constructed_urls), chunk_size)]

# Run instances in parallel using threads
threads = []
for i, instance in enumerate(instances):
    thread = threading.Thread(target=test_xss, args=(url_chunks[i], instance['webdriver_path'], instance['port'], i, progress))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

print("Testing complete.")


# Python code to create constructed URLs and save them to constructed_urls.txt

# Load URLs and payloads from files
with open('urls.txt', 'r') as urls_file:
    urls = [line.strip() for line in urls_file.readlines()]

with open('payloads.txt', 'r') as payloads_file:
    payloads = [line.strip() for line in payloads_file.readlines()]

# Insert characters for the payload
insert_chars = "qwe"

# Construct URLs and save to a text file
with open('constructed_urls.txt', 'w') as constructed_file:
    for url in urls:
        for payload in payloads:
            constructed_url = url + insert_chars + payload
            constructed_file.write(f"{constructed_url}\n")


print("Constructed URLs have been saved to constructed_urls.txt.")

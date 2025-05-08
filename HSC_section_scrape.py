import time, json, os, re
from selenium import webdriver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

TOC_URL = "https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=HSC"
BASE = "https://leginfo.legislature.ca.gov"
OUTFILE = "hsc_sections.jsonl"
DELAY = 1.5

def get_display_text_links():
    r = requests.get(TOC_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "codes_displayText.xhtml" in href:
            full_url = urljoin(BASE, href)
            links.append(full_url)
    return list(set(links))

def extract_sections_bruteforce(driver, url):
    driver.get(url)
    time.sleep(2)

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
    except:
        return []

    # Regex pattern to find section starts like "135.", "138.4.", "150500."
    raw_parts = re.split(r"\n(?=\d{1,6}(?:\.\d+)?\.)", body_text)
    sections = []

    for part in raw_parts:
        lines = part.strip().splitlines()
        if not lines:
            continue
        first_line = lines[0].strip()
        m = re.match(r"^(\d{1,6}(?:\.\d+)?)(\.)", first_line)
        if not m:
            continue
        section_num = m.group(1)
        body = "\n".join(lines).strip()
        sections.append({
            "section": section_num,
            "text": body,
            "url": url
        })

    return sections

def load_checkpoint():
    seen = set()
    if os.path.exists(OUTFILE):
        with open(OUTFILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    seen.add(json.loads(line)["section"])
                except:
                    pass
    return seen

def main():
    seen = load_checkpoint()
    links = get_display_text_links()
    print(f"Found {len(links)} displayText pages")

    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options
    )


    with open(OUTFILE, "a", encoding="utf-8") as f:
        for url in links:
            print(f"→ Scraping {url}")
            try:
                sections = extract_sections_bruteforce(driver, url)
                if not sections:
                    print("   ✖ No sections found")
                for sec in sections:
                    if sec["section"] in seen:
                        continue
                    f.write(json.dumps(sec, ensure_ascii=False) + "\n")
                    f.flush()
                    seen.add(sec["section"])
                    print(f"   ✔ Section {sec['section']}")
            except Exception as e:
                print(f"   ✖ Error: {e}")
            time.sleep(DELAY)

    driver.quit()

if __name__ == "__main__":
    main()

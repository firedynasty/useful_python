"""
Scrape hymn data from hymnary.org for all topics in the H1955 hymnal.
Extracts: Topic, Sub-Topic, Hymn #, First Line across all paginated pages.
Uses Chrome remote debugging (port 9222) via Selenium.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
import urllib.parse

BASE_URL = "https://hymnary.org/browse/topics/H1955"

TOPICS = [
    "#NAME?", "Adoration and Praise", "All Saints' Day", "Angels",
    "Armed Services", "Armistice Day", "Art and Literature", "Ash Wednesday",
    "Aspiration", "Assurance", "Baptism", "Benediction", "Benevolence",
    "Bible, The", "Bread of Life, The", "Brotherhood", "Cheerfulness",
    "Christ", "Church Workers", "Church, The", "Citizenship", "City, The",
    "Closing of Worship", "Comfort", "Commitment", "Common Duties and Things",
    "Communion of Saints", "Communion, Holy", "Confession", "Confidence",
    "Confirmation", "Constancy", "Contentment", "Contrition",
    "Cornerstone Laying", "Courage", "Cross, The", "Dedication Services",
    "Devotion", "Discipleship", "Doctors and Nurses", "Evening", "Faith",
    "Farewell Service", "Fellowship", "Forgiveness", "Funeral Services",
    "God", "God the Father", "Gratitude", "Harvest", "Healing", "Heritage",
    "Home, The", "Hope", "Humility", "Inner Life, The", "Installations",
    "Jesus Christ", "Joy", "Kingdom of God on Earth, The", "Labor Day",
    "Lent", "Life Everlasting, The", "Life in Christ", "Looking to Jesus",
    "Lord's Day, The", "Lord's Prayer, The", "Love and Communion", "Loyalty",
    "Marriage", "Meditation", "Memorial Day", "Ministry, The", "Missions",
    "Morning", "Name of Jesus, The", "Nation, The", "Nature", "New Year, The",
    "Opening of Worship", "Ordination", "Patience", "Patriotism",
    "Peace on Earth", "Peace, Spiritual", "Penitence", "Perseverance",
    "Pilgrimage of life", "Prayer", "Processionals", "Purity of Life",
    "Purpose", "Recessionals", "Redemption", "Rest", "Sacrifice", "Saints",
    "Salvation", "Schools", "Science", "Scriptures, The Holy", "Serenity",
    "Service", "Service Music", "Sin", "Soldiers of Christ",
    "Spirit, The Holy", "Spirituals", "Star in the East", "Stewardship",
    "Submission", "Temptation", "Thanksgiving", "The Bible", "Travelers",
    "Trial and Conflict", "Trinity, The Holy", "Trust", "Truth", "Unity",
    "Victory", "Vision", "Walking with God", "War", "Watchfulness",
    "Witnessing", "World Friendship and Peace", "Worship",
    "Young, Hymns for the", "Youth, Hymns for",
]

OUTPUT_FILE = "hymnary_h1955_all_topics.csv"


def connect_to_chrome():
    """Connect to Chrome instance running with remote debugging on port 9222."""
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_page(driver, topic, page=0):
    """Scrape a single page for a given topic. Returns list of rows and whether there's a next page."""
    params = {"page": page, "subject1": topic}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"

    driver.get(url)
    # Wait for the table to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.tabtable"))
        )
    except Exception:
        # No table found - topic may have no results
        return [], False

    soup = BeautifulSoup(driver.page_source, "html.parser")

    rows = []
    for tr in soup.select("tr.result-row"):
        cells = tr.find_all("td")
        if len(cells) >= 4:
            topic_text = cells[0].get_text(strip=True)
            sub_topic = cells[1].get_text(strip=True)
            hymn_num = cells[2].get_text(strip=True)
            first_line = cells[3].get_text(strip=True)
            rows.append({
                "Topic": topic_text,
                "Sub-Topic": sub_topic,
                "Hymn #": hymn_num,
                "First Line": first_line,
            })

    # Check for next page
    has_next = soup.select_one("li.pager-next a") is not None
    return rows, has_next


def scrape_topic(driver, topic):
    """Scrape all pages for a given topic."""
    all_rows = []
    page = 0
    while True:
        print(f"  Page {page + 1}...", end=" ", flush=True)
        rows, has_next = scrape_page(driver, topic, page)
        print(f"{len(rows)} hymns")
        all_rows.extend(rows)
        if not has_next:
            break
        page += 1
        time.sleep(1)
    return all_rows


def main():
    print("Connecting to Chrome on port 9222...")
    print("Make sure Chrome is running with: ")
    print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome '
          '--remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile\n')

    driver = connect_to_chrome()
    print(f"Connected! Current page: {driver.title}\n")

    all_data = []

    for i, topic in enumerate(TOPICS, 1):
        print(f"[{i}/{len(TOPICS)}] Scraping topic: {topic}")
        try:
            rows = scrape_topic(driver, topic)
            all_data.extend(rows)
            print(f"  Total for '{topic}': {len(rows)} hymns\n")
        except Exception as e:
            print(f"  ERROR scraping '{topic}': {e}\n")
        time.sleep(1)

    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Topic", "Sub-Topic", "Hymn #", "First Line"])
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\nDone! {len(all_data)} total hymn entries saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

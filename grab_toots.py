from mastodon import Mastodon
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import pytz
import sys

# Get date from command-line argument or default to yesterday
if len(sys.argv) > 1:
    try:
        input_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    except ValueError:
        print("Please enter the date in YYYY-MM-DD format.")
        sys.exit(1)
else:
    input_date = datetime.now().date() - timedelta(days=1)
    print("No date provided. Defaulting to yesterday's date")

print(f"Grabbing toots for {input_date}")

# Read token from file for security reasons
try:
    with open('token.txt', 'r') as file:
        key_from_file = file.read().strip()
except FileNotFoundError:
    print("Error: token.txt file not found.")
    exit(1)
except Exception as e:
    print(f"Error reading access token: {e}")
    exit(1)

# Authenticate with Mastodon API. Change to your own instance if not the default
mastodon = Mastodon(
    access_token=key_from_file,
    api_base_url='https://mastodon.social'
)

# Set timezone as desired
timezone = pytz.timezone('Europe/London')

# Convert date to timezone-aware datetime
target_date = timezone.localize(datetime.combine(input_date, datetime.min.time()))
next_day = target_date + timedelta(days=1)

# Fetch and filter timeline
raw_timeline = []
max_id = None
skipped_count=0
skipped_authors = []

while True:
    toots = mastodon.timeline_home(max_id=max_id, limit=40)
    if not toots:
        break

    for toot in toots:
        created = toot['created_at']
        if target_date <= created < next_day:
            raw_timeline.append(toot)
        elif created < target_date:
            break

    max_id = toots[-1]['id']


# Add a word filter to mimic my muted words on my timeline
#muted_words = ['trump', 'brexit']
try:
    with open('muted_words.txt', 'r', encoding='utf-8') as f:
        muted_words = [line.strip().lower() for line in f if line.strip()]
except FileNotFoundError:
    print("Warning: muted_words.txt not found. No word filtering will be applied.")
    muted_words = []

def contains_muted_word(text, muted_words):
    return any(word in text.lower() for word in muted_words)


# We have the toots as raw_timeline but it's best if we strip html
# We also want to record if a toot is original or was boosted
filtered_timeline = []
for toot in raw_timeline:
    if toot['content'].strip():
        # Original post
        text = BeautifulSoup(toot['content'], 'html.parser').get_text()
        author = toot['account']['username']
        boosted = False
    elif toot.get('reblog'):
        # Boosted post
        text = BeautifulSoup(toot['reblog']['content'], 'html.parser').get_text()
        author = toot['reblog']['account']['username']
        boosted = True
    else:
        continue  # Skip if no content at all
    
    if contains_muted_word(text,muted_words):
        skipped_count +=1
        skipped_authors.append(author)
        continue # Skip if we detect a muted word

    filtered_timeline.append({
        'author': author,
        'content': text,
        'boosted': boosted
    })




# Save simplified data as json 
# This file contains author, toot content, and whether the toot was boosted or not
clean_date = target_date.strftime("%Y-%m-%d")
filename = f"mastodon_filtered_{clean_date}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(filtered_timeline, f, indent=2, ensure_ascii=False)


skipped_file = f"mastodon_skipped_authors_{clean_date}.txt"
with open(skipped_file, 'w', encoding='utf-8') as f:
    for author in skipped_authors:
        f.write(f"{author}\n")

print(f"Logged {skipped_count} skipped authors to {skipped_file}")

# Tell the user how many toots we processed
print(f"Saved {len(filtered_timeline)} filtered posts for analysis. Skipped {skipped_count}. Saved file as: {filename}")


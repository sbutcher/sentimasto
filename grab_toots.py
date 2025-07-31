from mastodon import Mastodon
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import pytz

# Read token from file
try:
    with open('token.txt', 'r') as file:
        key_from_file = file.read().strip()
except FileNotFoundError:
    print("Error: token.txt file not found.")
    exit(1)
except Exception as e:
    print(f"Error reading access token: {e}")
    exit(1)

# Authenticate with Mastodon API
mastodon = Mastodon(
    access_token=key_from_file,
    api_base_url='https://mastodon.social'
)

# Set timezone as desired
timezone = pytz.timezone('Europe/London')

# Define your target date
target_date = timezone.localize(datetime(2025, 7, 30))
next_day = timezone.localize(datetime(2025, 7, 31))

# Fetch and filter timeline
raw_timeline = []
max_id = None

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

# Tell the user how many toots we processed
print(f"Saved {len(filtered_timeline)} filtered posts for analysis")


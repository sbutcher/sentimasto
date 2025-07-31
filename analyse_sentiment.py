import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import glob
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Validate input
if len(sys.argv) != 3:
    print("Usage: analyse_sentiment.py <start_date> <end_date>")
    sys.exit(1)

try:
    start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
except ValueError:
    print("Please enter dates in YYYY-MM-DD format.")
    sys.exit(1)

if start_date > end_date:
    print("Start date must be before end date.")
    sys.exit(1)

# Generate list of filenames in range
date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
file_list = [f"mastodon_filtered_{d}.json" for d in date_list]

#df = pd.DataFrame(data)
df_list = []
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

for filename in file_list:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            temp_df = pd.DataFrame(data)
            temp_df["date"] = filename.split("mastodon_filtered_")[1].split(".json")[0]
            df_list.append(temp_df)
    except FileNotFoundError:
        print(f"Skipping missing file: {filename}")

#df["sentiment"] = df["content"].apply(get_sentiment)
df = pd.concat(df_list, ignore_index=True)
df["sentiment"] = df["content"].apply(get_sentiment)
# Create a 'boosted_label' for color hue (e.g. "Boosted", "Not Boosted")
df["boosted_label"] = df["boosted"].apply(lambda x: "Boosted" if x else "Not Boosted")

# Create a color map for boosted status
palette = {"Positive": "#4CAF50", "Negative": "#F44336", "Neutral": "#FFC107"}

# Create a log file to check the sentiment classification
grouped = {
    "Positive": df[df["sentiment"] == "Positive"].to_dict(orient="records"),
    "Negative": df[df["sentiment"] == "Negative"].to_dict(orient="records"),
    "Neutral": df[df["sentiment"] == "Neutral"].to_dict(orient="records")
}
with open("grouped_sentiment_posts.json", "w", encoding="utf-8") as f:
    json.dump(grouped, f, indent=2, ensure_ascii=False)

# Draw barplot with hue separation by boosted status
sns.countplot(data=df, x="sentiment", hue="boosted_label", palette="Set2")
plt.title(f"Sentiment Distribution from {start_date} to {end_date}")
plt.xlabel("Sentiment Category")
plt.ylabel("Number of Posts")
plt.legend(title="Boosted Status")
plt.tight_layout()
plt.show()

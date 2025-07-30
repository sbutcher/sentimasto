import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Get date from command-line argument or default to today
if len(sys.argv) > 1:
    try:
        input_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    except ValueError:
        print("Please enter the date in YYYY-MM-DD format.")
        sys.exit(1)
else:
    input_date = datetime.now().date() - timedelta(days=1)
    print("No date provided. Defaulting to yesterday's date")

filename = f"mastodon_filtered_{input_date}.json"

try:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"File not found: {filename}")
    sys.exit(1)

df = pd.DataFrame(data)
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

df["sentiment"] = df["content"].apply(get_sentiment)

# Create a color map for boosted status
palette = {"Positive": "#4CAF50", "Negative": "#F44336", "Neutral": "#FFC107"}

# Create a 'boosted_label' for color hue (e.g. "Boosted", "Not Boosted")
df["boosted_label"] = df["boosted"].apply(lambda x: "Boosted" if x else "Not Boosted")

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
plt.title(f"Sentiment Distribution by Boosted Status on {input_date}")
plt.xlabel("Sentiment Category")
plt.ylabel("Number of Posts")
plt.legend(title="Boosted Status")
plt.tight_layout()
plt.show()

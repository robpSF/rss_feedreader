import streamlit as st
import feedparser

def fetch_rss_feed(url):
    """
    Fetches and parses the RSS feed from the given URL.
    
    Args:
    url (str): The URL of the RSS feed.
    
    Returns:
    list: A list of dictionaries containing the title, link, and summary of the most recent articles.
    """
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:5]:  # Get the 5 most recent articles
        article = {
            'title': entry.title if 'title' in entry else 'No title available',
            'link': entry.link if 'link' in entry else '',
            'summary': entry.summary if 'summary' in entry else 'No summary available'
        }
        articles.append(article)
    
    return articles

def display_articles(articles):
    """
    Displays the fetched articles.
    
    Args:
    articles (list): A list of dictionaries containing the title, link, and summary of the articles.
    """
    for idx, article in enumerate(articles):
        st.markdown(f"### {idx + 1}. {article['title']}")
        st.write(article['summary'])
        if article['link']:
            st.markdown(f"[Read more...]({article['link']})\n")

def main():
    st.title("RSS Feed Reader")
    st.write("Enter the URL of the RSS feed you want to read:")

    rss_url = st.text_input("RSS Feed URL", "https://tass.com/rss/v2.xml")

    if st.button("Fetch Articles"):
        articles = fetch_rss_feed(rss_url)
        if articles:
            st.write(f"Showing the 5 most recent articles from {rss_url}")
            display_articles(articles)
        else:
            st.write("No articles found or there was an error fetching the feed.")

if __name__ == "__main__":
    main()

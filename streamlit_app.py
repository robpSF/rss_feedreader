import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

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

def clean_html(soup):
    """
    Cleans HTML content to plain text.
    
    Args:
    soup (BeautifulSoup): The BeautifulSoup object of the HTML content.
    
    Returns:
    str: The cleaned plain text content.
    """
    # Remove <img ... </a> tags and their content
    for tag in soup.find_all('img'):
        parent = tag.find_parent('a')
        if parent:
            parent.decompose()

    # Remove script and style elements
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    # Get text and separate by lines
    text = soup.get_text(separator="\n")

    # Break into lines and remove leading/trailing spaces
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Remove blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

def fetch_full_article(link):
    """
    Fetches the full article content from the given link.
    
    Args:
    link (str): The URL of the article.
    
    Returns:
    str: The full article content with HTML tags removed and line feeds added.
    """
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Clean the HTML content
        full_text = clean_html(soup)

        return full_text
    except Exception as e:
        return f"Error fetching article content: {e}"

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
            full_article_content = fetch_full_article(article['link'])
            st.write(full_article_content)

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

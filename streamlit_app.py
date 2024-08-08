import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from io import BytesIO

def fetch_rss_feed(url):
    """
    Fetches and parses the RSS feed from the given URL.
    
    Args:
    url (str): The URL of the RSS feed.
    
    Returns:
    list: A list of dictionaries containing the title, link, summary, and published date of the most recent articles.
    """
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:5]:  # Get the 5 most recent articles
        article = {
            'title': entry.title if 'title' in entry else 'No title available',
            'link': entry.link if 'link' in entry else '',
            'summary': entry.summary if 'summary' in entry else 'No summary available',
            'published': entry.published if 'published' in entry else ''
        }
        articles.append(article)
    
    return articles

def clean_html(html):
    """
    Cleans HTML content to plain text and adds an extra line feed after each paragraph.
    
    Args:
    html (str): The HTML content to clean.
    
    Returns:
    str: The cleaned plain text content with extra line feeds after each paragraph.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    # Get text and separate by paragraphs
    paragraphs = soup.find_all('p')
    text = "\n\n".join(paragraph.get_text() for paragraph in paragraphs)

    return text

def fetch_full_article(link):
    """
    Fetches the full article content from the given link.
    
    Args:
    link (str): The URL of the article.
    
    Returns:
    tuple: The full article content, and the image URL.
    """
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get the full text content
        full_text = clean_html(str(soup))
        
        # Get the first image URL if available
        image_tag = soup.find('img')
        image_url = image_tag['src'] if image_tag else ''

        return full_text, image_url
    except Exception as e:
        return f"Error fetching article content: {e}", ''

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
            full_article_content, image_url = fetch_full_article(article['link'])
            st.write(full_article_content)
            if image_url:
                try:
                    st.image(image_url)
                except Exception as e:
                    st.write(f"Error displaying image: {e}")
            
            st.markdown(f"[Read more...]({article['link']})\n")

def save_to_excel(articles):
    """
    Saves the articles to an Excel file.
    
    Args:
    articles (list): A list of dictionaries containing the article details.
    
    Returns:
    bytes: The Excel file in bytes.
    """
    data = []
    for article in articles:
        full_article_content, image_url = fetch_full_article(article['link'])
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        data.append({
            'Subject': article['title'],
            'Message': full_article_content,
            'Reply': '',
            'Timestamp': timestamp,
            'Expected Action': '',
            'ImageURL': image_url,
            'Subtitle': article['summary']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Articles')
    return output.getvalue()

def main():
    st.title("RSS Feed Reader")
    st.write("Enter the URL of the RSS feed you want to read:")

    rss_url = st.text_input("RSS Feed URL", "https://tass.com/rss/v2.xml")

    if st.button("Fetch Articles"):
        articles = fetch_rss_feed(rss_url)
        if articles:
            st.write(f"Showing the 5 most recent articles from {rss_url}")
            display_articles(articles)
            
            # Save articles to Excel and provide download button
            excel_data = save_to_excel(articles)
            st.download_button(
                label="Download Excel file",
                data=excel_data,
                file_name="articles.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No articles found or there was an error fetching the feed.")

if __name__ == "__main__":
    main()

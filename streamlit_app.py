import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from io import BytesIO

def fetch_rss_feed(url, num_articles=5):
    """
    Fetches and parses the RSS feed from the given URL.
    
    Args:
    url (str): The URL of the RSS feed.
    num_articles (int): The number of articles to fetch.
    
    Returns:
    list: A list of dictionaries containing the title, link, summary, and published date of the most recent articles.
    """
    try:
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries[:num_articles]:  # Get the specified number of articles
            article = {
                'title': entry.title if 'title' in entry else 'No title available',
                'link': entry.link if 'link' in entry else '',
                'summary': entry.summary if 'summary' in entry else 'No summary available',
                'published': entry.published if 'published' in entry else ''
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        st.write(f"Error parsing RSS feed from {url}: {e}")
        return []

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
        st.write(f"Error fetching article content from {link}: {e}")
        return f"Error fetching article content: {e}", ''

def display_articles(articles):
    """
    Displays the fetched articles.
    
    Args:
    articles (list): A list of dictionaries containing the title, link, and summary of the articles.
    """
    for idx, article in enumerate(articles):
        if 'title' in article and 'summary' in article and 'link' in article:
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
        else:
            st.write(f"Error: Article at index {idx} is missing one or more required fields.")

def save_to_excel(articles, filename='articles.xlsx'):
    """
    Saves the articles to an Excel file.
    
    Args:
    articles (list): A list of dictionaries containing the article details.
    filename (str): The name of the Excel file to save.
    
    Returns:
    bytes: The Excel file in bytes.
    """
    df = pd.DataFrame(articles)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Articles')
    return output.getvalue()

def collect_articles(rss_url, num_articles):
    """
    Collects articles from a given RSS feed URL.
    
    Args:
    rss_url (str): The URL of the RSS feed.
    num_articles (int): The number of articles to fetch.
    
    Returns:
    list: A list of dictionaries containing the article details.
    """
    articles = fetch_rss_feed(rss_url, num_articles)
    collected_articles = []

    for article in articles:
        if 'link' in article and article['link']:
            full_article_content, image_url = fetch_full_article(article['link'])
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            collected_articles.append({
                'From': '',
                'Subject': article['title'],
                'Message': full_article_content,
                'Reply': '',
                'Timestamp': timestamp,
                'Expected Action': '',
                'ImageURL': image_url,
                'Subtitle': article['summary']
            })
        else:
            st.write(f"Error: Article from {rss_url} is missing a link.")
    
    return collected_articles

def process_persona_file(uploaded_file, num_articles):
    """
    Processes the uploaded persona file and fetches articles based on the URLs in the Tags column.
    
    Args:
    uploaded_file: The uploaded Excel file containing persona details.
    num_articles: The number of articles to fetch per RSS feed.
    
    Returns:
    list: A list of dictionaries containing the article details.
    """
    df = pd.read_excel(uploaded_file)
    articles = []

    for _, row in df.iterrows():
        if 'Tags' in row and pd.notna(row['Tags']):
            tags = row['Tags'].split(',')
            # Find the URL in the Tags field
            rss_url = next((tag for tag in tags if tag.startswith('http')), None)
            if rss_url:
                st.write(f"Fetching articles from: {rss_url}")
                persona_articles = collect_articles(rss_url, num_articles)
                for article in persona_articles:
                    article['From'] = row['Name']
                    article['ImageURL'] = row['Image']
                    articles.append(article)
            else:
                st.write(f"No valid URL found in Tags for row: {row['Name']}")
        else:
            st.write(f"Skipping row with missing or invalid Tags: {row}")
    
    return articles

def main():
    st.title("RSS Feed Reader")

    mode = st.selectbox("Select mode", ["Single Mode", "Batch Mode"])

    if mode == "Single Mode":
        st.write("Enter the URL of the RSS feed you want to read:")
        rss_url = st.text_input("RSS Feed URL", "https://tass.com/rss/v2.xml")

        if st.button("Fetch Articles"):
            articles = fetch_rss_feed(rss_url, 5)
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

    elif mode == "Batch Mode":
        st.write("Upload an Excel file with persona details:")
        uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])

        if uploaded_file is not None:
            num_articles = st.number_input("Number of articles to fetch per RSS feed", min_value=1, max_value=5, value=5)
            if st.button("Fetch Articles"):
                articles = process_persona_file(uploaded_file, num_articles)
                if articles:
                    st.write(f"Showing the articles fetched from the provided persona file")
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
                    st.write("No articles found or there was an error processing the file.")

if __name__ == "__main__":
    main()

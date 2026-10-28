from fastapi import HTTPException, status
from newspaper import Article
from core.config import settings




def scrape_article(url: str):
    """
    Scrapes the article from the given URL and returns the title, text, and word count.

    Args:
        url (str): The URL of the article to be scraped."""

    
    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not fetch URL or URL is invalid")
    title = article.title
    if not article.text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable content found at URL")
    word_count = len(article.text.split())
        
    return {
            "title": title,
            "text": article.text,
            "word_count": word_count,
            "source_url": url
        }

    
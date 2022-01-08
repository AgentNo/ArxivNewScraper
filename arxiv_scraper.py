'''
arxiv_scraper.py

This application acts as a web crawler and scraper.
Starting with https://export.arxiv.org/, the crawler will first extract the links to all the 'new' pages on the website. After completing this, 
the crawler will visit each page in turn and scrape all paper metadata.
Once finished, each page's content is output in a JSON file in the /output directory.
'''

from bs4 import BeautifulSoup
import logging
import requests
import json


# Crawl the main page to get the links to all 'new' pages, then return as a list to the main scraper
def get_seed_urls():
    seed = "https://export.arxiv.org/"
    crawl_list = []

    res = requests.get(seed)
    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.find_all("a")
    for link in links:
        if 'new' in link:
            crawl_list.append('https://export.arxiv.org{}'.format(link['href']))
    return crawl_list


# Harvest data from arXiv pages
def get_arxiv_data(urls):
    for url in urls:
        logging.info('Retrieving data from {}'.format(url))
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        titles = soup.find_all("div", class_='list-title') # Paper Titles
        authors = soup.find_all("div", class_='list-authors') # Paper Authors
        topics = soup.find_all("div", class_='list-subjects') # Paper Subjects
        abstracts = soup.find_all("p", class_='mathjax') # Paper Abstracts
        paper_urls = soup.find_all("a", title='Download PDF') # Paper URL suffix (http://arxiv.org/)
        papers = []


        for title, author_list, topic_list, paper_url, abstract in zip(titles, authors, topics, paper_urls, abstracts):
            # Format the properties so we get just the text, no HTML
            title = str(title).split('>')[3].split('<')[0].strip()
            paper_url = str(paper_url).split('"')[1].strip()
            abstract = str(abstract).split('>')[1].split('<')[0].strip()
            author_list = format_authors_list(author_list)
            topic_list = format_topics_list(topic_list)

            # Add the item to the list
            new_paper = {
                'title': title,
                'abstract': abstract,
                'authors': author_list,
                'topics': topic_list,
                'url': "http://arxiv.org{}".format(paper_url),
            }
            papers.append(new_paper)
            logging.info('Found paper "{}" from {}'.format(title, paper_url))
        # Write the JSON file to disk
        topic = url.split('/')[4]
        f_name = 'output/arxiv_{}.json'.format(topic)
        with open(f_name, 'w') as f:
            json.dump(papers, f)
            logging.info('Wrote metadata to JSON -> {}'.format(f_name))


# Get the author's names from the HTML and format it into a single list of strings
def format_authors_list(author_list):
    author_list_new = []
    text = str(author_list).split('>')
    for item in text:
        if item[-3:] == '</a':
            a = item.split('<')[0].strip()
            author_list_new.append(a)
    return author_list_new


# Get the topics from the HTML and format it into a single string list
def format_topics_list(topic_list):
    topic_list_new = []
    text = str(topic_list).strip().split('<span class="primary-subject">')[1].replace('\n', "").split('</div>')[0].split(';')
    if len(text) == 1:
        topic_list_new.append(text[0].split('<')[0])
    else:
        for topic in text:
            if topic[-7:] == '</span>':
                # The first topic in the list has a span tag, remove this from the text
                topic_list_new.append(topic.split('<')[0].split('(')[0].strip())
            else:
                topic_list_new.append(topic.split('(')[0].strip())
    return topic_list_new


# Set up logging
def start_logs():
    log = logging.getLogger()
    log.setLevel('INFO')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    return log


# Main crawler logic
def main():
    logger = start_logs()
    seeds = get_seed_urls()
    # Intitalise the cosmos connection
    logger.info("Found {} seed URLs\nStarting crawl...".format(len(seeds)))
    get_arxiv_data(seeds)
    logger.info("Arxiv crawl complete!")


if __name__ == "__main__":
    main()

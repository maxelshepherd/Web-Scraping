from bs4 import BeautifulSoup
from urllib.request import urlopen

def main(url):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    print(soup.get_text())


if __name__ == "__main__":
    main("https://www.cats.org.uk/")
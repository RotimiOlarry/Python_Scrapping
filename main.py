import requests
import csv, json ,re ,os
from bs4 import Beautifulsoup4 
import mechanize
from random import choice
user_agents = ['Mozilla/5.0 (X11; U; Linux; i686; en-US; rv:1.6) Gecko Debian/1.6-7',
                'Konqueror/3.0-rc4; (Konqueror/3.0-rc4; i686 Linux;;datecode)','Opera/9.52 (X11; Linux i686; U; en)']
random_user_agent = choice(user_agents) 
import urllib

def all_great_movies():
    ebert_url = "https://www.rogerebert.com/great-movies?utf8=%E2%9C%93&filters%5Btitle%5D=&sort%5Border%5D=newest&filters%5Byears%5D%5B%5D=1914&filters%5Byears%5D%5B%5D=2020&filters%5Bstar_rating%5D%5B%5D=0.0&filters%5Bstar_rating%5D%5B%5D=4.0&filters%5Bno_stars%5D=1&page={}"

    curr_page = 1
    headers = {'accept':'application/json'}

    while True:
        print("Parsing page {}".format(curr_page))
        data = []
        response = requests.get(ebert_url.format(curr_page),headers=headers)
        data_soup = beautifulsoup(response.json()['html'],features="html.parser")
        reviews = data_soup.find_all("div", class_="review-stack")
        
        for review in reviews:
            title = review.find("h5", class_ = "review-stack--title")
            title_anchor = title.find("a")
            review_link = title_anchor['href']
            review_text = title.anchor.text 
            data.append ({
                "review_url" : review_link ,
                "title" : review_text
            })
        if data:
            print("{} movies saved".format(len(data)))
            with open ("data/{}.json".format(curr_page), 'w') as f:
                f.write(json.dumps(data))
            curr_page += 1
        else:
            break

def amazon_search(movie_title):
    print('Searching movie title'.format(movie_title))
    url = "https://www.amazon.com/s?k={}&i=instant-video"
    search_key = urllib.parse.quote_plus(movie_title.lower())
    end = url.format(search_key)
    br = mechanize.Browser()
    br.addheaders = [('User-Agent', random_user_agent)]
    response = br.open(end)
    data_soup = beautifulsoup(response.get_data(), features = "html.parser")
    txt = str (data_soup).replace("\n","")
    res = data_soup.find_all()

    import re
    rgex = re.compile(r"""<h2 class="a-size-mini a-spacing-none a-color-base s-line-clamp-2">.*?<\/h2>""")
    matches =rgex.findall(txt)
    available_on_amazon = False
    including_with_prime = False
    amazon_url = None

    for match in matches:
        soup = beautifulsoup(match, features = "html.parser")
        anchor = soup.find("a")
        search_title = anchor.text.strip().lower()

        if search_title in movie_title.lower():
            print("available on amazon!")
            curl = "https://www.amazon.com{}".format(anchor['href'])
            available_on_amazon = True
            amazon_url = curl

            try:
                res = br.open(curl)
                if "Watch for $0.00 with Prime" in str(res.get_data()):
                    included_with_prime = True
                break

            except:
                print("Unable to get prime information for {}".format(movie_title))
                break
    res = {
        "available_on_amazon": available_on_amazon,
        "included_with_prime": included_with_prime,
        "url": amazon_url
    }
    return res

def add_amazon_data_to_ebert_movies(name):
    updated_data = []
    ebert_data = []

    with open (name, 'r') as f:
        contents = f.read()
        if contents:
            ebert_data = json.loads(contents)
        for movies_info in ebert_data:
            amazon_info = amazon_search(movies_info["title"])
            updated_data.append({**movies_info,**amazon_info})

    if ebert_data:
        with open(name, 'w') as f:
            f.write(json.dumps(updated_data))


def run():
    all_great_movies()
    for myfile in os.listdir('data'):
        print( "--------Page {}".format(myfile))
        add_amazon_data_to_ebert_movies("data/{}".format(myfile))
    combined_movie_data = []
    for myfile in os.listdir('data'):
        with open("data/{}".format(myfile), 'r') as f:
            if "json" in myfile:
                combined_movie_data += json.loads(f.read())
    with open ('data/results.csv', 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimeter='~')
        filewriter.writerow(['Title','review URL','Available on Amazon','Included With Prime','Prime URL'])
        for row in combined_movie_data:
            filewriter.writerow({
                row['title'],"www.rogerebert.com{}".format(row['review_url']),
                row['available_on_amazon'],
                row['included_with_prime'],
                row['url']
            })

if __name__ == '__main__':
    run()






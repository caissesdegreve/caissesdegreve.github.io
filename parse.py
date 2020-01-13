#!/opt/cdg/.pyenv/bin/python /opt/cdg/parse.py
# -*- coding: utf-8 -*-

urls = [
    'https://paris-luttes.info/ancrer-la-lutte-dans-la-duree-13089',
    'https://expansive.info/Ancrer-la-lutte-dans-la-duree-recensement-des-caisses-de-greve-1914',
    'https://mars-infos.org/ancrer-la-lutte-dans-la-duree-4644',
    'https://rebellyon.info/Solidarite-financiere-avec-les-salarie-es-21512',
    'https://solidaires.org/Caisses-de-greves',
    'http://rennes-info.org/Solidarite-avec-les-grevistes-Vous',
    'https://www.revolutionpermanente.fr/Vous-soutenez-massivement-la-greve-versez-aux-caisses-de-greve-pour-nous-faire-gagner-toutes-et'
]

import locale
locale.setlocale(locale.LC_ALL, str('fr_FR.UTF-8'))

import os
if os.path.exists('items.json'):
    os.remove('items.json')

import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--check", help="pas de tweet", action="store_true")
args, unknown = parser.parse_known_args()

import scrapy
from scrapy.crawler import CrawlerProcess
import json
import time

ndcode = 'N/D'
from datetime import datetime
datedujour = datetime.now().strftime('%A %-d %B %Y')


if os.path.exists('connues.txt'):
    with open('connues.txt','r') as f:
        connues = f.read().split('\n')
else:
    connues = []

def makedetail(detail=None):
    print(detail)
    import json
    if not detail:
        with open('savedetail.json','r') as f:
            detail = json.loads(f.read())
    else:
        with open('savedetail.json','w') as f:
            f.write(json.dumps(detail))

    from jinja2 import Template

    with open('detailtmpl.html','r') as f:
        tmpl = Template(f.read())

    caisses = []
    for rank,c in enumerate(sorted(detail,key=lambda x:x['montant'] if x['montant'] != ndcode else -1, reverse=True)):
        caisse = dict(
            nom = c['nom'],
            titre = c['titre'][0].upper() + c['titre'][1:].lower(),
            montant = "{m} €".format(m="{:n}".format(int(c['montant']))) if c['montant'] != ndcode else c['montant'],
            participants = "{:n}".format(c['participants']) if c['participants'] != ndcode else c['participants'],
            rank = rank+1
        )
        #print(c['titre'],c['montant'],caisse['montant'],c['participants'],caisse['participants'])
        caisses.append(caisse)
    with open('publish/index.html','w') as f:
        f.write(tmpl.render(caisses=caisses,date=datedujour))

def posttwitter(msg):
    import twitter
    #api = twitter.Api(consumer_key='kvfI17TAAB9Kg7LtdKFwiHsWa', consumer_secret='P2TMZL7nGuWQIx3xJVxpXy9Hg9UvktXrLmIrfqFJOAEEhQ4At7', access_token_key='3434108799-mOCFFI3FEdjLSgGuisqDzCobZpCZCm8pCiGRvhw', access_token_secret='S6tYqKbyuktMvC8A6moWF8ebb9rdVoDDxVwJL1REBmvBa')
    api = twitter.Api(consumer_key='iPXJSJL5QeTyNr1xevzg2akPS', consumer_secret='TC37I7mHi21rfYEexBzbmjCC9JFJHIuK5arts8sIhdZioLzoTS', access_token_key='1209456196916301824-4US3BXL4eCW2P9XiTI6sNYGQte6RZu', access_token_secret='88T5izr8NMIHmnIT8oo0pserjItSbUUrHYKs01NWVBTRV')
    status = api.PostUpdate(msg,media='visuel.jpg')
    rt = api.PostUpdate("Sources: "+", ".join(urls),in_reply_to_status_id=status.id)


def waitfor(driver,xpath):
    from selenium.webdriver.common.by import By
    retry = 15
    found = None
    while retry and not found:
        try:
            found = driver.find_elements(By.XPATH,xpath)
        except:
            pass

        retry -= 1
        time.sleep(1)
    return found
def selenium_get(chrome,url):
    from selenium.webdriver.common.by import By
    import re
    chrome.get(url)
    montant = ndcode
    participants = ndcode
    titre = ndcode
    try:
        if "lyf.eu" in url:
            iframe = waitfor(chrome, '//iframe')
            if iframe:
                chrome.switch_to.frame(iframe[0])
                found = waitfor(chrome,'//div[@class="infoText"]')
                if found:
                    _montant, _participants,*other = [x.text.replace(' ','').replace('€','').replace(',','.') for x in found]
                    montant = float(_montant)
                    participants = float(_participants)
                    titre = chrome.find_element(By.XPATH, '//div[@class="titleBlock"]/div[@class="title"]')
                    if titre:
                        titre = titre.text

        elif "gofundme" in url:
            _montant = waitfor(chrome,'//h2[@class="m-progress-meter-heading"]')
            _montant = _montant[0].text.replace(' ','').replace('\u202f','').replace('€','') if _montant else ndcode
            if _montant != ndcode:
                montant = float(re.split(r'[^0-9\.,]',_montant)[0])
            _participants = waitfor(chrome,'//span[@class="text-stat-value text-underline u-pointer"]')
            participants = float(_participants[0].text.replace(' ','')) if _participants else ndcode
            titre = chrome.find_element(By.XPATH, '//h1[@class="a-campaign-title"]')
            if titre:
                titre = titre.text
        elif "paypal" in url:
            _montant = waitfor(chrome,'//div[contains(@class,"money-big")]/span[contains(@class,"money__value_")]')[0].get_attribute('innerHTML')
            montant = float(_montant.replace('&nbsp;','').split('E')[0].replace('.','').replace(',','.')) if _montant else ndcode
            _participants = waitfor(chrome,'//div[contains(@class,"public_contributions_list")]')[0].text
            participants = float(re.split(r'[^0-9 ]',_participants)[0].replace(' ','')) if _participants else ndcode
            titre = chrome.find_element(By.XPATH, '//div[contains(@class,"campaign_title__title__")]')
            if titre:
                titre = titre.text
        elif "okpal" in url:
            montant = float(waitfor(chrome,'//strong[@class="goal__collected"]')[0].text.replace(' ','')[:-1])
            participants = float(re.match(r'Déjà (.*) contributeurs',waitfor(chrome,'//span[contains(.,"contributeurs")]')[0].text).groups()[0].replace(' ',''))
            titre = chrome.find_elements(By.XPATH,'//h1[@class="campaign__title"]')
            if titre:
                titre = titre[0].get_attribute('innerHTML')
    except:
        pass
    return titre, montant, participants


def makevisuel(participants,montant):
    from PIL import ImageFont, Image, ImageDraw

    im = Image.open('visuelcdg.jpg')
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype('Exo2-Black.otf',80)
    w,h = draw.textsize(participants, font=font)
    draw.text((420-w,250-h),participants, font=font, fill=(50,163,80,255))


    font = ImageFont.truetype('Exo2-Black.otf',90)
    w,h = draw.textsize(montant, font=font)
    draw.text((520-w,378-h),montant, font=font, fill=(50,163,80,255))
    im.save('visuel.jpg')


def getId(c):
    ids = c.split('/')
    id = ids.pop()
    while len(id)<2 and len(ids)>0:
        id = ids.pop()
    if len(ids)==0:
        id = c
    return id


class CDGSpider(scrapy.Spider):
    caisses_ids = []
    name = "CDG"
    start_urls = urls


    def parse(self, response):
        #caisses = response.xpath('//li[contains(@class,"comment-item")]/div/div/span/p/a/@href').extract()
        #caisses += response.xpath('//div[contains(@class,"texte-principal")]//li/a/@href').extract()
        caisses = connues + response.xpath('//li//a/@href[contains(.,"http")]').extract()
        caisses += response.xpath('//p//a/@href[contains(.,"http")]').extract()
        #caisses = ['https://www.lepotcommun.fr/pot/ookjlz4m']
        caisses = list(tuple(caisses))
        for caisse in caisses:
            caisse = caisse.split('?')[0]
            caisse_id = getId(caisse)
            if caisse_id in self.caisses_ids:
                continue
            if 'colleo.fr' in caisse:
                yield scrapy.Request(caisse, callback=self.colleo)
            if 'lepotsolidaire' in caisse:
                yield scrapy.Request(caisse, callback=self.potsolidaire)
            elif 'papayoux' in caisse:
                yield scrapy.Request(caisse, callback=self.papayoux)
            elif 'helloasso' in caisse:
                yield scrapy.Request(caisse, callback=self.helloasso)
            elif 'leetchi' in caisse:
                yield scrapy.Request(caisse, callback=self.leetchi)
            elif 'cagnotte.me' in caisse:
                yield scrapy.Request(caisse, callback=self.cagnotteme)
            elif 'cotizup' in caisse:
                yield scrapy.Request(caisse, callback=self.cotizup)
            elif 'potcommun' in caisse:
                yield scrapy.Request(caisse, callback=self.potcommun)
            elif 'paypal' in caisse or 'lyf.eu' in caisse or 'gofundme' in caisse or 'okpal' in caisse:
                yield { "nom":caisse, "montant": 'selenium',"participants":"selenium", "titre":"selenium"}
            else:
                print('#################',caisse,'###################')
            self.caisses_ids.append(caisse_id)





    def potsolidaire(self, response):
        if response.url == 'https://www.lepotsolidaire.fr/pot/solidarite-financiere':
            montant =float(''.join(response.xpath('//p[strong/span/text()[contains(.,"MONTANT TOTAL COLLECTÉ DEPUIS LE 5 DÉC. 2019")]]/following-sibling::p[2]/strong/span/text()').extract()[0].split(' ')[:-1]))
        else:
            try:
                montant = float(response.xpath('//span[@class="raised-amount"]/text()').extract()[0].replace(' ','').replace(',','.')[:-1])
            except:
                montant = ndcode
        try:
            participants = int(response.xpath('//span[@class="participationCount"]/text()').extract()[0].replace(' ','').replace(',',''))
        except:
            participants = ndcode

        try:
            titre = response.xpath('//span[@class="kitty-name"]/text()').extract()[0]
        except:
            titre = ndcode

        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def colleo(self, response):
        try:
            import re
            montantstr = response.xpath('//span[contains(.,"Déjà")]/text()').extract()[0]
            montant = float(re.match(r'Déjà (.*) € collectés',montantstr).groups()[0].replace(' ',''))
        except:
            montant = ndcode

        participants = ndcode

        try:
            titre = response.xpath('//h1[@class="panel-header center title"]/text()').extract()[0]
        except:
            titre = ndcode

        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }


    def papayoux(self, response):
        try:
            montant = float(response.xpath('//div[@id="montant"]/text()').extract()[0].replace(' ','').replace(',','.')[:-1])
        except:
            montant = ndcode
        try:
            participants = int(response.xpath('//div[@id="nombre"]/div/text()').extract()[0].replace(',',''))
        except:
            participants = ndcode

        try:
            titre = response.xpath('//h1[@class]/text()').extract()[0]
        except:
            titre = ndcode

        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def helloasso(self, response):
        try:
            montant = float(response.xpath('//div[@class="campaign-numbers-heading"]/h2/span/@data-max').extract()[0])
        except:
            montant = ndcode
        try:
            participants = int(response.xpath('//div[@class="campaign-numbers"]/p/text()').extract()[0])
        except:
            participants = ndcode

        try:
            titre = response.xpath('//div[@class="campaign-header"]/div/h1[@class="headline"]/text()').extract()[0]
        except:
            titre = ndcode

        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def leetchi(self, response):
        try:
            montant = float(response.xpath('//h1[contains(@class,"o-article-status__heading")]/text()').extract()[0].replace(' ','').replace(',','.').replace('\xa0','').replace('\n','')[:-1])
        except:
            montant = ndcode
        try:
            participants = int(response.xpath('//div[contains(@class,"c-contribution")]/span[@class="c-status__counter"]/text()').extract()[0].replace(' ','').replace(',',''))
        except:
            participants = ndcode
        try:
            titre = response.xpath('//h1[@class="page-heading"]/span/text()').extract()[0]
        except:
            titre = ndcode
        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def cagnotteme(self, response):
        try:
            montant = float(response.xpath('//div[@class="collected-amount-label"]/text()').extract()[0].replace(' ','').replace(',','.').replace('\n','')[:-1])
        except:
            montant = ndcode
        try:
            participants = ndcode
        except:
            participants = ndcode

        try:
            titre = response.xpath('//div[@class="large-title"]/h1/text()').extract()[0]
        except:
            titre = ndcode
        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def cotizup(self, response):
        try:
            montant = float(response.xpath('//div[@class="thumbnail--price"]/p/text()').extract()[0].replace(' ','').replace(',','.').replace('\n','')[:-1])
        except:
            montant = ndcode
        try:
            participants = int(response.xpath('//p[@class="price-total"]/span/text()').extract()[0])
        except:
            participants = ndcode
        try:
            titre = response.xpath('//div[@class="campaign-title"]/h2/text()').extract()[0]
        except:
            titre = ndcode
        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }

    def potcommun(self, response):
        try:
            montant = float(response.xpath('//span[@class="raised-amount"]/text()').extract()[0].replace(' ','').replace(',','.').replace('\n','')[:-1])
        except:
            try:
                montant = float(response.xpath('//div[@class="goal-to-reach-display-content"]/lpc-progress-bar/@current-value').extract()[0].replace(',','.').replace(' ',''))
            except:
                montant = ndcode
        try:
            participants = int(response.xpath('//span[@class="participationCount"]/text()').extract()[0].replace(' ',''))
        except:
            participants = ndcode

        try:
            titre = response.xpath('//span[@class="kitty-name"]/text()').extract()[0]
        except:
            titre = ndcode

        yield { "nom":response.url, "montant": montant, "participants": participants, "titre": titre }


process = CrawlerProcess(settings={'FEED_FORMAT': 'jsonlines', 'FEED_URI': 'items.json'})
process.crawl(CDGSpider)
process.start(True)
process.stop()



from selenium import webdriver
from selenium.webdriver.common.by import By

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = '/opt/google/chrome/chrome'
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('window-size=1920x1080')
chrome_options.add_argument('--lang=fr-FR')

chrome = webdriver.Chrome(chrome_options=chrome_options)




import jsonlines

detail = []
participants = 0
montant = 0
nb = 0
caisses_ids = []
connues = []
with jsonlines.open('items.json') as f:
    for c in f:
        caisse_id = getId(c['nom'])
        if caisse_id in caisses_ids:
            continue
        connues.append(c['nom'])
        caisses_ids.append(caisse_id)
        if c['montant'] == 'selenium':
            #continue
            _titre, _montant,_participants = selenium_get(chrome,c['nom'])
            c['titre'] = _titre
            c['participants'] = _participants
            c['montant'] = _montant
        print(c)
        if c['participants'] != ndcode:
            participants += c['participants']
        if c['montant'] != ndcode:
            montant += c['montant']

        if c['titre'] != ndcode:
            nb += 1
            detail.append(c)
        if c['participants'] == ndcode or c['montant'] == ndcode or c['titre'] == ndcode:
            print(c['nom'],c['montant'],c['participants'])
        #if c['participants'] != ndcode or c['montant'] != ndcode:

chrome.quit()

with open('connues.txt','w') as f:
    f.write('\n'.join(connues))

import os
os.remove('items.json')

msg = "[Point du {jour}]\n\n{nb} caisses comptabilisées.\n\nLe détail est ici : https://caissesdegreve.github.io/\n\n#ReformeRetraites #Retraitesparpoints #CaisseDeGreve".format(jour=datedujour,nb=nb)

makevisuel("{p}".format(p="{:n}".format(participants)),"{m} €".format(m="{:n}".format(int(montant))))


makedetail(detail)

for c in detail:
    print("{titre};{montant};{participants}".format(**c))
print(nb,montant,participants)
#exit(0)

if not args.check:
    posttwitter(msg)

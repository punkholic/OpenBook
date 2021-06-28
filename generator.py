import json, requests, re, pdfkit, argparse
from bs4 import BeautifulSoup
from os import path

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Book:
    def __init__(self, fileName):
        self.finalOutput = ''
        self.renderList = {
            "w3schools" : {
                "selector" : ["#main"],
                "delete": ['.entry-header > div:nth-child(2) > ul:nth-child(1) > li:nth-child(1)'],
                'hasStaticImage': True
            },

            "javatpoint" : {
                "selector" : ["#city > table:nth-child(1)"], 
                "delete": ['#bottomnext', '#bottomnextup'],
                'hasStaticImage': True
            },


            "tutorialspoint" : {
                "selector" : [".mui-col-md-6"],
                "delete": ['div.mui-container-fluid:nth-child(5)', '#bottom_navigation'],
                'hasStaticImage': False
            },

            "geeksforgeeks" : {
                "selector" : [".entry-content", "article.content"], 
                "delete": ['#post-157294 > div:nth-child(2)', '.entry-content > p:nth-child(10), .entry-content > p:nth-child(10) ~ *', '.media', 'iframe', '#personalNoteDiv'],
                'hasStaticImage': True
            },
        }

        with open(fileName, 'r') as f:
            toParse = f.read()
        self.data = json.loads(toParse)
    

    def getGoogleUrl(self, data):
        urls = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'
        }
        getData = requests.get("https://www.google.com/search?q=" + data, headers=headers)
        soup = BeautifulSoup(getData.text, 'html.parser')
        for i in soup.find_all(class_='g'):
            gotUrl = i.find('a').get('href')
            if gotUrl and "http" in gotUrl:
                urls.append(gotUrl)
        return urls

    def renderImage(self, url, content):
        gotUrl = (re.findall(r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))", url))
        renderedData = (re.sub(r'src="/' ,'src="' + ('://'.join(list(gotUrl[0]))) + "/", str(content)))
        return renderedData

    def requestTextContent(self, url, searchIn=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'
        }
        getData = requests.get(url, headers=headers)
        soup = BeautifulSoup(getData.text, 'html.parser')
        counter = 0; foundText = None;
        while foundText == None and len(searchIn['selector']) != counter:
            foundText = soup.select_one(searchIn['selector'][counter])
            counter += 1
        
        if( foundText != None):
            

            for i in searchIn['delete']:
                for j in foundText.select(i):
                    j.decompose()

            if not searchIn['hasStaticImage']: foundText = self.renderImage(url, foundText)
        return foundText
    
    def searchUrl(self, urls):
        for i in list(self.renderList.keys()):
            for j in urls:
                if i.lower() in re.findall(r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))", j)[0][1].lower():
                    return self.requestTextContent(j, self.renderList.get(i))


    def queryString(self, text):
        urls = book.getGoogleUrl(text)
        print(f"{bcolors.WARNING}[ ] Working with: {text}")
        gotData = self.searchUrl(urls)
        if (gotData): 
            self.finalOutput += str(gotData)
            print(f"{bcolors.OKGREEN}[+] Fetched: {text}")
        else:
            print(f"{bcolors.FAIL}[-] Failed: {text}, please increase options of websites")
        return gotData
    
    
    def transverse(self, data):
        if type(data) is list:
            for i in data:
                if type(i) is str:
                    self.queryString(i)
                    continue
                return self.transverse(i)
        elif type(data) is dict:
            for i in data.keys():
                if type(data[i]) is str:
                    self.queryString(data[i])
                    continue
                return self.transverse(data[i])
            

    def topics(self):
        for i in self.data:
            self.transverse(i['content'])
        return self.finalOutput

    def getData(self):
        return self.data


parser = argparse.ArgumentParser(description='OpenBook version 0.0.1')
parser.add_argument('--json', dest='json', type=str, help='Pass json file with toc')
args = parser.parse_args()

if(not args.json or not path.exists(args.json)):
    parser.print_help()
    exit(0)

book = Book(args.json)
toWrite = book.topics()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body
   """+toWrite+"""
<body>
</html>
"""
pdfkit.from_string(html_content, 'book.pdf')
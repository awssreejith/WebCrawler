import scrapy
import json
import sys


class MyCrawler(scrapy.Spider):
    name                       = 'Sreejith_Spider'
    start_urls                 = ['http://books.toscrape.com/'] 
    dumpFile                   = open ('JSONDumpForBooks.txt','w')
    dumpFileForEackBook        = open ('JSONDumpForEachBook.txt','w')
    Bookname                   = ''
    EachBookHyperLink          = {}
    funcCounter                = 0
    def parse(self, response):

       
       ## get book name and hyperlink with each book
       ##The below query returns the following list(s) of all the below
       ## Hyperlink
       ##  Title of Book
       ##    price_color
       ##       in Stock or not
       ##          next page hyper link
       ## We gonna loop through all the available books in the page and during each traversal, we extract the corresponding
       ## price, title,in stock. But after travrsing all the books in a single page we will grab the next page link
        BookName         = response.xpath("//article[@class='product_pod']/h3/a/@title").extract()
        HyperlinkForBook = response.xpath("//article[@class='product_pod']/h3/a/@href").extract()
        price_Of_Book    = response.xpath("//article[@class='product_pod']/div[@class='product_price']/p[@class='price_color']/text()").extract()
        InStock          = response.xpath("//article[@class='product_pod']/div[@class='product_price']//p[@class='instock availability']/text()").extract()
 
        ResultMap          = dict()

       ##The above can be extracted in a single query inside a list in single pass as below

       ############################################################################################################################################################################################################################################################################################################################################################
       #myresult = response.xpath("//article[@class='product_pod']/h3/a/@title|//article[@class='product_pod']/h3/a/@href|//article[@class='product_pod']/div[@class='product_price']/p[@class='price_color']/text()|//article[@class='product_pod']/div[@class='product_price']/p[@class='instock availability']/text()|//ul/li[@class='next']/a/@href").extract()
       ############################################################################################################################################################################################################################################################################################################################################################

        ###ALERT!!! THERE IS A SMALL PROBLEM WITH THE InSTOCKARRAY. THERE ARE EXTRA LINE FEEDS ADDED BETWEEN TWO INDICES. WE
        ### HAVE TO REMOVE THIS FIRST.
        newInStock = []
        for element in InStock:
            variable = element.lstrip().rstrip()
            if len(variable):
                newInStock.append(variable)
        
        ##If any mismatch in sizes, we can't process. Let's exit
        if len(BookName) != len(HyperlinkForBook) or len(BookName) != len(price_Of_Book) or len(BookName) != len(newInStock):
            print("There is a mismatch in data for books within the website. Please recheck the webpage. Exiting")
            sys.exit(-1)

        ##Remove all escape characters \t\n\r from above results
        for idx in range(0,len(BookName)):
            MyCrawler.Bookname = BookName[idx].lstrip().rstrip()
            hyperlink          = HyperlinkForBook[idx].lstrip().rstrip()
            price              = price_Of_Book[idx].lstrip().rstrip()
            stock              = newInStock[idx].lstrip().rstrip() ##though already stripped, just doingonce more

            ResultMap.clear()
            ResultMap = {"Name"         : MyCrawler.Bookname,
                         "HyperLink"    : hyperlink,
                         "price"        : price,
                         "InStock"      : stock
                        }

            ## before we yield, lets dump to JSON file
            self.fileDump(ResultMap)
            ##Before we Move to the next book, lets go in to details of this book by going inside the
            ##hyperlink and extract UPC code and how many are available.For this purpose we use another
            ##function and we set the call back as that function when we request for link traversal
            completeURL_eachProduct = response.urljoin(hyperlink)
            yield scrapy.Request(url=completeURL_eachProduct,callback=self.parse_eachBookLink)
            
        ## Control only reaches here once all the books had been iterated in a single page
        ## Once all the books inside a particular page are extracted, lets go to next page and continue our
        ## scrapping. For that we extract the next page link from end of this page.
        nextPage         = response.xpath("//ul/li[@class='next']/a/@href").extract_first()
        if nextPage != None:
            nextPage = nextPage.lstrip().rstrip()

            ##Now lets get complete URL for the next page as below
            completeURL_NextPage = response.urljoin(nextPage)

            ##Now our next page link is ready. Lets send a request to scrapy engine with this new link
            ##and let the same work continue in the new page. But to do that we have to tell the request method
            ##to call back the same function 
            yield scrapy.Request(url=completeURL_NextPage,callback=self.parse)


    def parse_eachBookLink(self,response):
        '''
        This function will be auto invoked when we call the request() for each book's hyperlink.
        This function extracts the details about UPC and availability stocks and write into a seperate JSON file

        '''
        ##A sample run on the scrapy shell with the below expression gives as follows
        ## >>> response.xpath("//div[@id='content_inner']//table//td/text()").extract()
        ## ['a897fe39b1053632', 'Books', '£51.77', '£51.77', '£0.00', 'In stock (22 available)', '0']

        bookName = response.xpath("//div[@class='content']//div[@class='col-sm-6 product_main']/h1/text()").extract_first()
        details = response.xpath("//div[@id='content_inner']//table//td/text()").extract()
        eachMap = dict()
        eachMap.clear()

        if details != None and len(details) == 7:
            eachMap = {"Name":bookName, "UPC":details[0], "Stock":details[5]}
        else:
            eachMap = {"Name":bookName, "UPC":"", "Stock":""}

        ## Write to JSON file specific for each book
        self.fileDump(eachMap,dumpForEachBook=True)

        ## Now yield so that call goes back
        yield (eachMap)



###JSON SERIALIZER   
    def fileDump(self,jsonObject,dumpForEachBook=False):
       
        dump = json.dumps(jsonObject,ensure_ascii=False)
        if dumpForEachBook == False:
            if MyCrawler.funcCounter == 0:
                MyCrawler.dumpFile.write(dump+"\n")
            else:
                MyCrawler.dumpFile.write(","+dump+"\n")
        else:
            if MyCrawler.funcCounter == 0:
                MyCrawler.dumpFileForEackBook.write(dump+"\n")
            else:
                MyCrawler.dumpFileForEackBook.write(","+dump+"\n")

        MyCrawler.funcCounter += 1


    
            

        
       

            
        
       
      
        
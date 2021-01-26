# doing necessary imports

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import re

app = Flask(__name__)  # initialising the flask app with the name 'app'
CORS(app)

@app.route('/',methods=['GET']) # route to display the homepage
@cross_origin()
def homePage():
    return render_template("index.html")


@app.route('/scrap', methods=['POST', 'GET'])  # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString  # preparing the URL to search the product on flipkart
            uClient = uReq(flipkart_url)  # requesting the webpage from the internet
            flipkartPage = uClient.read()  # reading the webpage
            uClient.close()  # closing the connection to the web server
            flipkart_html = bs(flipkartPage, "html.parser")  # parsing the webpage as HTML
            bigboxes = flipkart_html.findAll("div", {"class": "_13oc-S"})  # seacrhing for appropriate tag to
            # redirect to the product link

            product_links = dict()   #Define an empty dictionary to store product Name and the url for the specific product

            # Loop through all the items in the product page and store links for individual products
            for box in bigboxes:  # Loop through all the items
                try:
                    try:
                        title = box.find(title=True).text  # Title of the Product
                    except AttributeError:
                        # Title of the Product. Used when Title Tag isn't present
                        title = box.find_all('div', {'class': "_4rR01T"})[0].text

                    product_page = "https://www.flipkart.com" + box.div.div.a['href']  #Store the link to product page
                    product_links.update({title: product_page}) # Fill up the dictionary with product Links
                    break
                except AttributeError:
                    pass  # No href tags ..Continue

            reviews = []  # initializing an empty list for reviews

            #  Different brands belonging to the same product Type : For e.x.: Iphone 7 comes in 32GB and 64GB
            for key in product_links:  # Loop through all the products in the page returned as a Search Result
                #review_type_links = dict()
                prodRes = requests.get(product_links[key])  # getting the product page from server
                prod_html = bs(prodRes.text,"html.parser")  #Parsing the webpage as text
                try:
                    # This Class tag <col JOpGWq> contains the link for the Reviews page
                    commentholders = prod_html.find_all('div', {'class': re.compile(r'col JOpGWq')})
                    for a in commentholders[0].find_all('a', href=True):   #  for <a> tags that have a href attribute
                        if 'product-reviews' in a['href']:
                            review_types = "https://www.flipkart.com" + a['href']# Store href tags that point to Comments Page
                    prod_rev = requests.get(review_types)   # Open the Review Page
                    prod_html = bs(prod_rev.text,"html.parser") # Parse the webpage as text
                    comment_boxes = prod_html.find_all('div', {'class': re.compile(r'_1AtVbE col-12-12')})[4:] # Find the comments, the first 4 comment boxes point to the rating matrix and  should be ignored
                            #try:
                            #    component_part_start = str(review_types).index('&an') # Start Index of the Url that contains Review for a particular Feature
                            #    component_part_end = str(review_types).index('&cat')  # End Index of the Url that contains Review for a particular Feature
                            #    component = str(review_types)[component_part_start + 4:component_part_end]  # Feature Name
                            #except ValueError:
                            #    component = 'Overall'
                            #   pass  #Substring not found for category . Continue as Usual


                            # Some Products have Multiple Reviews Owing to Component parts
                            # For example, a iphone will have different reviews for camera, battery etc
                            #review_type_links.update({component: review_types})

                    #for rkey in review_type_links:
                    #    prod_rev = requests.get(review_types)   # Open the Review Page
                    #    prod_html = bs(prod_rev.text,"html.parser") # Parse the webpage as text
                    #    comment_boxes = prod_html.find_all('div', {'class': re.compile(r'_1AtVbE col-12-12')})[3:] # Find the comments, the first 3 comment boxes point to the rating matrix and  should be ignored


                    #  iterating over the comment section to get the details of customer and their comments
                    for commentbox in comment_boxes[:-1]:  # Last Comment Box Points to number of Pages ..So Ignore It
                        try:
                            name = commentbox.find_all('p',{'class': re.compile(r'_2sc7ZR _2V5EHH')})[0].text

                        except:
                            name = 'No Name'

                        try:
                           # rating = commentbox.div.div.div.div.div.text
                           rating = commentbox.find_all('div', {'class': re.compile(r'_3LWZlK _1BLPMq')})[0].text
                        except:
                            rating = 'No Rating'
                        try:
                            commentHead = commentbox.div.div.div.div.p.text
                        except:
                            try:
                                commentHead = commentbox.div.div.div.div.div.text[1:]
                                index_comment = commentHead.index('READ MORE')
                                commentHead = commentHead[:index_comment]
                            except:
                                commentHead = 'No Comment Heading'
                        try:
                            comtag = commentbox.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                            if len(custComment) == 1:
                                custComment = 'No Customer Comment'
                        except:
                            custComment = 'No Customer Comment'
                        mydict = {"Product":  key, "Name": name, "Rating": rating, "CommentHead": commentHead,
                              "Comment": custComment}  # saving that detail to a dictionary
                        flag = 0     # Set a flag to filter duplicate comments
                        if len(reviews) > 0:
                            for review in reviews:
                                review_cred = review.copy()  # Deep Copy to retain the original dictionary
                                mydict_cred = mydict.copy()  # Deep Copy to retain the original dictionary
                                review_cred.pop('Product')
                                mydict_cred.pop('Product')
                                if review_cred == mydict_cred:  # Compare for Duplicate Reviews
                                    flag = 1
                                    break
                        if flag != 1:
                            reviews.append(mydict)  # appending the comments to the review list
                except:
                    pass
            return render_template('results.html', reviews=reviews)  # showing the review to the user
        except:
            return 'something is wrong. Type again'
            # return render_template('results.html')
    else:
        return render_template('index.html')

# pip install flask-cors


# git init
# git add .
# git commit -m "initial commit"
# heroku login
# heroku create
# git remote -v
# git push heroku master
if __name__ == "__main__":
    app.run(port=8000, debug=True)  # running the app on the local machine on port 8000
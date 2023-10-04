"""
This program will execute the crawling work, using the functions
written in 'functions.py.'
Also, the needed class name or xpath of the html element is defined 
in the file 'defClass.py'
-----------------------------------------------------------------

In this program, we run a nested loop to do the crawling. 

The outer loop will grab the html elements in the content page, 
and scroll down the current window each iteration. The html 
elements we grab is the post list in the content page.

Once we have grabbed the post list in one iteration of the outer 
loop, we'll enter the inner loop. 
In each iteration of the inner loop, we enter one post page from
the post list, and crawl the information we need, such as post title,
post author, post content, etc. In the end of the inner loop, we'll
append the information from the current post to our data set.

The last part of this program, is to output the whole data set as 
a .csv file.
"""
import pandas as pd
import requests
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC


from bs4 import BeautifulSoup
from time import sleep

import functions
import defClass

def crawl(email, password, group, totalPost, dataSet):
    # Log in Facebook ===============================================
    # our login information (using a fake account)
    url = "https://www.facebook.com/"
    
    # make selenium not pop up windows
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options) # we use firefox here, it can be other browser
    
    #driver = webdriver.Firefox()

    # Enter Facebook
    driver.get(url)

    # Login
    driver.find_element("id", "email").send_keys(email)
    driver.find_element("id", "pass").send_keys(password)
    driver.find_element("name", "login").click()
    sleep(5) # Wait to log in

    # Check if the account is valid. ================================
    # If we still in the log in page, that means we fail to log in
    # with that account.
    if(len(driver.find_elements("name",  "login")) > 0): return -1

    # Check if the group exists. ====================================
    # If the HTTP status code is 200, our request succeed.
    url = 'https://www.facebook.com/groups/' + group
    rsp = requests.get(url).status_code
    if(rsp != 200): return -2

    # Enter Group ===================================================
    driver.switch_to.new_window('tab')
    driver.get(url)

    # Default Data ==================================================
    POST_ID = -1
    AUTHOR = "unknown"
    CONTENT = "unknow"
    TIME_STAMP = "unknown"
    COMMENTS = "..."
    COMMENTERS = "unknown"
    POLARITY = "unknown"

    # only for test
    eachPost = [POST_ID, AUTHOR, TIME_STAMP, CONTENT, COMMENTS, COMMENTERS, POLARITY]
    dataSet.append(eachPost)

    if not os.path.exists(group):
        os.mkdir(group)

    # Crawl the posts ===============================================
    # count the number of post we obtain
    postCnt = 0
    postIdTab = set() # record post id to avoid re-collect
    postIdTab.add(-1)
    lastLinkIdx = 0

    # This for loop is for scrolling the window
    while True: 
    
        # End the loop: we obtained the given number of data
        if (postCnt == totalPost):
            break

        # wait to load page
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")))

        # get the html element
        # divs of each post is recorded in "postSegs"
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        postSegs = soup.find_all("div", class_= 'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z')

        # get the time link in each post (to obtain post id)
        timeLinks = driver.find_elements(By.XPATH, defClass.time_a_xpath)

        # make a list of post IDs
        postIdList = functions.getpostIdList(lastLinkIdx, timeLinks, group, driver)
        lastLinkIdx = len(timeLinks)

        # Dig in each post segment
        for postSeg, postId in zip(postSegs, postIdList):
            # Obtain post ID and check if we've already collected it
            POST_ID = postId
            
            if POST_ID in postIdTab:
                continue
            else: 
                postIdTab.add(POST_ID)
                #print(POST_ID)
            
            # Skip Reels
            if(postSeg.find("div", class_= defClass.reel_div_class)):
                continue

            # Obtain the user name
            AUTHOR = functions.getAuthor(postSeg)

            # Obtain the comments
            TIME_STAMP, CONTENT, COMMENTS, COMMENTERS, POLARITY = functions.enterPostPage(driver, group, POST_ID)

            # Down load image

            eachPost = [POST_ID, AUTHOR, TIME_STAMP, CONTENT, COMMENTS, COMMENTERS, POLARITY]
            dataSet.append(eachPost)
            #print('\n')
            postCnt = postCnt + 1

            if (postCnt == totalPost):
                break

    # Quit the driver ===============================================
    driver.quit()
    
    # Output the data ===============================================
    filePath = os.path.join(group, "output.csv")
    df = pd.DataFrame(dataSet)
    df.columns = ["POST_ID", "AUTHOR", "TIME_STAMP", "CONTENT", "COMMENTS", "COMMENTERS", "POLARITY"]
    df.to_csv(filePath)

    return 0

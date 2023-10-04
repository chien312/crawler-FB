"""
This program defines the functions we use for crawling.
"""

import time
import re
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait


from bs4 import BeautifulSoup
from time import sleep

import defClass 

def enterGroup(url):
    """ Make selenium automates browser and go to the specific web page(Facebook group).
    Args:
        url: the url of the web page we want to enter.
    
    Returns:
        returns the web driver.
    """
    # make selenium not pop up windows
    options = Options()
    options.add_argument('--headless')

    #driver = webdriver.Firefox(options=options) # we use firefox here, it can be other browser
    driver = webdriver.Firefox()

    driver.get(url)
    return driver

def clickSeeMore(driver):
    """ Make selenium clicks all of the 'see more' btn in the post or comments.
    Args:
        driver: the driver we currently use.
    
    Returns:
        returns the parsed page after expending all of the hidden content.
    """
    # Using a loop to expend the content hidden by the 'see more' btn.
    while True:
        try:
            # If there exists the 'more reply' /'see more' btn.
            moreReplys = driver.find_elements(By.XPATH, defClass.moreReply_span_xpath)

            # In a loop to click all of the btn
            for moreReply in moreReplys:
                # scroll
                driver.execute_async_script("""
                const callback = arguments[arguments.length - 1];
                arguments[0].scrollIntoView({behavior: "auto", block: "center", inline: "center"});
                callback();""", moreReply)
                
                # not click the hide btn
                if('隱藏' in moreReply.get_attribute("textContent")):
                    continue
                
                # click
                driver.execute_script('arguments[0].click();', moreReply)
                time.sleep(3)

            # check if there are other mpre reply btn after we clicked one
            new_moreReplys = driver.find_elements(By.XPATH, defClass.moreReply_span_xpath)
            time.sleep(3) # wait to load the page

            # Break the loop: if the number of new_moreReplys equals to the old moreReplys,
            # means there's no new 'more replys' btn after we clicking all of the btn loaded previously.
            if len(new_moreReplys) == len(moreReplys):
                break

        except StaleElementReferenceException:
            continue

    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    postSeg = soup.find("div", class_= 'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z')
    return postSeg

def isShared(url, group):
    """ Chaeck if the post is shared from other communities.
    Args:
        url: the url string of the post.
        group: the group ID of our target group.
    
    Returns:
        returns a boolean.
    """
    # Split the URL by '/'
    parts = url.split('/')
    if(len(parts) < 5): return True

    # Get the value of the third part in the url
    group_id = parts[4]
    
    # Check if it matches our expected value
    if group_id not in {group, group + "#"}: 
        return True
    else: return False

def getpostIdList(lastLinkIdx, timeLinks, group, driver):
    """ Collect all ID of posts available in the current view point into a list.
        We want to extract the post ID from the post link.
    Args:
        lastLinkIdx: the url string of the post.
        timeLinks: all of the post links available in the current view point.
        group: the group ID of our target group.
        driver: the driver we currently use.
    
    Returns:
        returns a list of post ID
    """
    postIdList = []
    idx = 0
    for timeLink in timeLinks:
        # check if we already have this link:
        if(idx < lastLinkIdx):
            idx += 1
            link = timeLink.get_attribute('href')

            if(isShared(link, group)):
                continue
            else:
                try:
                    postID = re.search(r'/posts/(\d+)/', link).group(1)
                    postIdList.append(postID)
                    continue
                except AttributeError:
                    continue
        
        elif(idx >= lastLinkIdx): 
            idx += 1
            # get the link
            link = getPostUrl(driver, timeLink)
            
            # shared link
            if(isShared(link, group)):
                continue
            else:
                try:
                    postID = re.search(r'/posts/(\d+)/', link).group(1)
                    postIdList.append(postID)
                except AttributeError:
                    continue
    
    return postIdList

def getPostUrl(driver, timeLink):
    """ Obtain the url of the post. 
        We need to click the link to get the href attribute.
    Args:
        driver: the driver we currently use.
        timeLink: the link of the target post.
    
    Returns:
        returns the url of the post.
    """
    # Create ActionChains object
    actions = ActionChains(driver)

    # scroll the window to find the time link
    actions.scroll_to_element(timeLink)
    driver.execute_async_script("""
    const callback = arguments[arguments.length - 1];
    arguments[0].scrollIntoView({behavior: "auto", block: "center", inline: "center"});
    callback();""", timeLink)
    time.sleep(0.5)

    # Move mouse to element (hover) and open in new tab
    actions.move_to_element(timeLink).perform()
    actions.key_down(Keys.CONTROL).click().perform()

    # move to the post page and close it
    try:
        driver.switch_to.window(driver.window_handles[2])
        driver.close()
    except IndexError:
        pass

    # back to original tab
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(0.5)

    # obtain the href attribute in the <a> tag
    link = timeLink.get_attribute('href')

    return link

def getAuthor(postSeg):
    """ Obtain the author name. 
        We need to click the link to get the href attribute.
    Args:
        postSeg: the html of a single post.
    
    Returns:
        returns the name of author (string).
    """
    postAUTHOR = postSeg.find("h3", class_= defClass.author_class)
    AUTHOR = postAUTHOR.getText().strip()
    return AUTHOR

def findCreationTime(data):
    """ Find out where record the creation time of the post in a json file recursively.
    Args:
        data: the json file of this page.
    
    Returns:
        If we find out the value of "creation_time", return it.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "creation_time":
                return value
            elif isinstance(value, (dict, list)):
                result = findCreationTime(value)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = findCreationTime(item)
            if result is not None:
                return result
    return None

def getTime(driver):
    """ Linearly search for all the json file of this page, find out which one contains the 
        'creation_time' information, and return the unix time.
    Args:
        driver: the driver we currently use.
    
    Returns:
        returns the creation time of the post (unix time).
    """
    time.sleep(1)
    jsonScripts = driver.find_elements(By.XPATH, "//script[@type='application/json']")
    # traverse every script tag
    for jsonScript in jsonScripts:
        # obtain the content of each script tag
        script_text = jsonScript.get_attribute("innerHTML")

        # parse JSON
        data = json.loads(script_text)

        # find the "creation_time"
        creation_time = findCreationTime(data)
        if creation_time is not None:
            TIME_STAMP = creation_time
            break
        else:
            TIME_STAMP = 'none' 
    return TIME_STAMP

def getContent(postSeg):
    """ Obtain the content of the post.
    Args:
        postSeg: the html of a single post.
    
    Returns:
        returns the the content of the post.
    """
    post = postSeg.find("span", class_ = defClass.content_span_class)

    # case 1: plain text 
    if(post is not None):
        CONTENT = post.getText()
    else:
        CONTENT = postSeg.find("div", class_ = "xzsf02u xngnso2 xo1l8bm x1qb5hxa")
        if(CONTENT is not None):
            # case 2: text with bigger font
            CONTENT = CONTENT.getText()
        else:
            CONTENT = postSeg.find("div", class_ = "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
            if(CONTENT is not None):
                # case 3: card text
                CONTENT = CONTENT.getText()
            else:
                # case 4: the post really has no text content
                CONTENT = ""

    return CONTENT

def getComt(postSeg):
    """ Obtain all of the comments and their commenters of the post.
    Args:
        postSeg: the html of a single post.
    
    Returns:
        COMMENTS: the comments of the post.
        COMMENTERS: the commenters of the comments.
    """
    comtSegs = postSeg.find_all("div", class_ = defClass.comtSeg_div_class)
    COMMENTS = ""
    COMMENTERS = ""

    for comtSeg in comtSegs:
        # find commenters
        name = comtSeg.find("span", class_ = "x3nfvp2").getText()
        name = "!#@" + name
        COMMENTERS = COMMENTERS + name
        
        # find comments
        line = comtSeg.find("div", class_ = "xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs").text
        line = "!#@" + line
        COMMENTS = COMMENTS + line

    return COMMENTS, COMMENTERS

def getPolarity(driver):
    """ Obtain the number of 'like,' 'love,' 'haha,' etc.
    Args:
        driver: the driver we currently use.
    
    Returns:
        returns a list of the number of each emoji response.
    """
    POLARITY= []

    # click the polarity number
    try:
        polarityBtn = driver.find_element(By.XPATH, defClass.polarity_span_xpath)
        driver.execute_async_script("""
        const callback = arguments[arguments.length - 1];
        arguments[0].scrollIntoView({behavior: "auto", block: "center", inline: "center"});
        callback();""", polarityBtn)
        polarityBtn.click()
        time.sleep(3)

        # pops up the polarity
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page = soup.find("div", class_= defClass.polarity_page_div_class)

        polaritySegs = page.find_all("div", class_ = defClass.polarity_page_each_div_class)
        for polaritySeg in polaritySegs:
            polarity = polaritySeg['aria-label']
            #print(polarity)
            POLARITY.append(polarity)

    except NoSuchElementException:
        POLARITY.append(0)
    
    return POLARITY

def enterPostPage(driver, group, postID):
    """ Enter the post page, and collect the wanted information.
    Args:
        driver: the driver we currently use.
        group: the group ID of our target group.
        postID: the ID of the target post.
    
    Returns:
        TIME_STAMP: the time stamp of the post.
        CONTENT: the content of the post.
        COMMENTS: the comments of the post.
        COMMENTERS: the commenters of the comments.
        POLARITY: a list of the number of each emoji response.
    """
    url = "https://www.facebook.com/groups/" + group + "/posts/" + postID
    # enter post page
    driver.switch_to.new_window('tab')
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)

    # get time
    TIME_STAMP = getTime(driver)

    # parse the page after click all of the "see more" btn
    postSeg = clickSeeMore(driver)
    time.sleep(0.3)

    CONTENT = getContent(postSeg)

    try:
        images = postSeg.select(defClass.img_css)
        for idx, image in enumerate(images):
            # In some case there's only video but no images
            try:
                imgSrc = image['src']
                # make folder to store images(by post ID)
                subfolderPath = os.path.join(group, postID)
                os.makedirs(subfolderPath, exist_ok=True)

                # store those images
                imgDownload = requests.get(imgSrc)
                with open(subfolderPath + "/img" + str(idx+1) + ".jpg", "wb") as file:
                    file.write(imgDownload.content)

            except KeyError:
                pass
    except NoSuchElementException:
        pass

    # get post comments and commenters
    COMMENTS, COMMENTERS = getComt(postSeg)


    POLARITY = getPolarity(driver)

    # close tab
    driver.close()
    driver.switch_to.window(driver.window_handles[1])
    return TIME_STAMP, CONTENT, COMMENTS, COMMENTERS, POLARITY

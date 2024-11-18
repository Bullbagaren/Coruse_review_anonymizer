
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import getpass
import spacy
import sv_core_news_lg
import re
from colorama import Fore
from art import * 


from selenium.webdriver.remote.webelement import WebElement

def main():
    tprint("COURSE REVIEW ANONYMIZER")
    print(Fore.RED + "WARNING! THIS PROGRAM IS NOT FLAWLESS! ")
    print(Fore.RED + "ALWAYS AT ALL TIMES DOUBLE CHECK THE WORK!!!")
    username, password = get_login_details()
    website = pick_website()
    text_list = get_website_and_text(username, password, website)
    text_dictionary = mark_named_entities(text_list)
    change_entity_name(text_dictionary)



def get_website_and_text(username, password, website):
    """
    The function takes login details and a URL to login the user.
    
    The function takes username, password and website previously provided by user. 
    The function opens an instance of firefox and fill out the login 
    details of the user and logs them in to the chosen URL.
    The function then grabs the HTML code and pass it to beautifulsoup
    to find all textarea tags and appends them to a list and return it.

    Keyword arguments:
    username -- provided username by the user
    website --  URL provided by the user
    password -- users password to the website
    """
    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.get(website)
        driver.find_element("id", "username").send_keys(username)
        driver.find_element("id", "password").send_keys(password)
        driver.find_element("name", "_eventId_proceed").click()
    except:
        print("Could not log in for some reason. Check that username and password is correct.")
        
    html = driver.page_source
    soup = bs(html, "html.parser")
    text_list=[]
    for tag in soup.find_all("textarea"):
        text_list.append(tag.text)

    driver.quit()
    return text_list
    
def change_entity_name(text_dictionary):
    """
    Changes the name of marked entities.

    The function iterates over a dictionary
    where they key is the original text and 
    modifies a copy of it for comparison later.

    Keyword arguments:
    text_dictionary -- key is text to be modified and value 
                        is a list of tuple with entities.
    """

    
    for key, value in text_dictionary.items():
        text = str(key)
        changed_text = text
        for entity in value:
            entity_name , _ = entity
            changed_text = changed_text.replace(entity_name, "lärare X")
        
        change_pronouns(changed_text, text)   


def change_pronouns(changed_text, text):

    """
    Replaces swedish gendered pronouns with gender neutral pronouns.

    This function replaces gendered swedish pronouns with gender neutral
    to make guessing who the text is referencing harder. The edited text 
    is tehn printed with the original text.

    Keyword arguments:
    changed_text -- text with edited entities
    text -- The original text with unchanged enities
    """
    pronouns = [r"\b[Dd]u\b", r"\b[Hh][ao]n\b"]

    changed_text = re.sub(pronouns[0], Fore.RED + "lärare X", changed_text)
    changed_text = re.sub(pronouns[1], Fore.RED + "hen", changed_text)

    print("-------------------------------------------------")
    print("original text: ")
    print(text)     
    print("\n")
    print("edited text: ")
    print(changed_text)
    print("\n")
    print("-------------------------------------------------")

def pick_website():
    """
    Takes no arguments and returns the URL specified by 
    the user. 
    """
    return input("Enter the URL for the course review you want to edit: ")

def get_login_details():
    """
    Takes no argukments and return the 
    users username and password. 
    Password is not echoed back to the user
    
    Keyword argument
    username -- user input
    password -- user input
    return   -- username, password
    """

    username = input(Fore.WHITE + "please enter your username: ")
    password = getpass.getpass() 

    return username, password


def mark_named_entities(text_list):

    """
    Passes over a string and marks entities.

    Takes a list of string as argument 
    and iterates over it passing each string 
    to a NLP model and extracts entity text 
    and entity lable it then return a text dictionary
    with the text as key and the tuple of entity text
    and lable as the item. 


    Keyword arguments: 
    text_list -- list of strings
    
    """

    nlp = spacy.load("sv_core_news_lg")
    text_dictionary = {}
    for text in text_list:
        doc = nlp(text)
        elist =[(ent.text, ent.label_) for ent in doc.ents]
        text_dictionary.update({text : elist})

        

    return text_dictionary


def sentence_seperator(text_block):
    split_text = re.split(".[\s \t \n]")
    return split_text




if __name__ == "__main__":
    main()

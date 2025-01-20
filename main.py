import getpass
import torch
import spacy
import sv_core_news_lg
import re
import pickle
#import time 
from colorama import Back, Fore
from art import * 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from sentence_transformers import SentenceTransformer, similarity_functions, util
#from torch import embedding
from selenium.webdriver.remote.webelement import WebElement
#from torch._higher_order_ops.while_loop import WhileLoopOp

def main():
    tprint("COURSE REVIEW ANONYMIZER", font="small")
    print(Fore.RED + "WARNING! THIS PROGRAM IS NOT FLAWLESS! ")
    print(Fore.RED + "ALWAYS AT ALL TIMES DOUBLE CHECK THE WORK!!!")
    username, password = get_login_details()
    website = pick_website()
    text_list = get_website_and_text(username, password, website)
    analysed_text_list = semantic_analysis(text_list)
    text_dictionary = mark_named_entities(analysed_text_list)
    ct_t_dict = change_entity_name(text_dictionary)
    push_to_site(username,password,website, ct_t_dict)

def push_to_site(username, password, website, ct_t_dict):

    """
    The function takes username, password, website and a dictionary
    of the unchanged text as well as the changed text. It logs 
    in the user and searches for the approriate textareas using the 
    unchnaged text and then replaces it with the changned text. 

    keyword argument:
    username  -- user's username
    password  -- user's password
    website   -- website's URL 
    ct_t_dict -- A dictionary of chenged text and unchanegd text
    """

    try:
        #options = webdriver.FirefoxOptions()
        #options.add_argument("--headless")
        driver = webdriver.Firefox()
        driver.get(website)
        driver.find_element("id", "username").send_keys(username)
        driver.find_element("id", "password").send_keys(password)
        driver.find_element("name", "_eventId_proceed").click()
    except:
        print("Could not log in for some reason. Check that username and password is correct.")
    
    html = driver.page_source
    soup = bs(html, "html.parser") 
    for tag in soup.find_all("textarea"):
        element = driver.find_element(By.NAME, tag.get("name"))
        if element.text.replace("\n", "") in ct_t_dict.values():
            changed_text = [key for key, value in ct_t_dict.items() if value == element.text.replace("\n", "")]
            element.clear()
            element.send_keys(changed_text[0]+ "---test")




def get_website_and_text(username, password, website):
    """
    The function takes login details and a URL to login the user.
    The function takes username, password and website previously provided by user. 
    The function opens an instance of firefox and fill out the login  
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
        assert "Kursvärderingar" in driver.title
    except:
        print("Could not log in for some reason. Check that username and password is correct.")
        driver.quit()
        print("shutting down. Please run the program to try again")
        raise SystemExit
        
    html = driver.page_source
    soup = bs(html, "html.parser")
    text_list=[]

    for tag in soup.find_all("textarea"):
        text_list.append(tag.text.replace("\n", ""))

    driver.quit()
    text_list = list(filter(None, text_list))
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

    ct_t_dict = {}
    for key, value in text_dictionary.items():
        text = str(key)
        changed_text = text
        for entity in value:
            entity_name , ent_type = entity
            if ent_type == "PRS":
                changed_text = changed_text.replace(entity_name, "lärare X")
       
        
        text, changed_text = change_pronouns(text, changed_text)   
        ct_t_dict.update({text:changed_text})
    return ct_t_dict





def change_pronouns(text, changed_text):

    """
    Replaces swedish gendered pronouns with gender neutral pronouns.

    This function replaces gendered swedish pronouns with gender neutral
    to make guessing who the text is referencing harder. The edited text 
    is tehn printed with the original text.

    Keyword arguments:
    changed_text -- text with edited entities
    text -- The original text with unchanged enities
    """
    pronouns = [r"\b[Dd]u\b", r"\b[Hh][ao]n\b", r"\b[Hh]onom\b", r"\b[Hh]enne\b"]

    changed_text = re.sub(pronouns[0], "lärare X", changed_text)
    for i in range(1,len(pronouns)):
        changed_text = re.sub(pronouns[i], "hen", changed_text)

    return text, changed_text

    #print("-------------------------------------------------")
    #print("original text: ")
    #print(text)     
    #print("\n")
    #print("edited text: ")
    #print(changed_text)
    #print("\n")
    #print("-------------------------------------------------")

def pick_website():
    """
    Takes no arguments and returns the URL specified by 
    the user. 
    """
    url = input("Enter the URL for the course review you want to edit: ")
    kv_regex = re.compile("https://kv.uu.se/granska/[0-9]+")
    if kv_regex.match(url):
        return url
    else:
        print("The link provided doesn't seem to be a course evaluation link or it's incomplete, shutting down...")
        raise SystemExit

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

def semantic_analysis(text_list):
    """
    Takes a list of text to be embedded and then 
    does a cosine comparison of precalculated 
    vectors of bad words. 

    ketword arguments:
    text_list -- a list of tokenized sentences
    """
    with open("embeddings.pickle", "rb") as file:
        vector_data = pickle.load(file)

    analysed_text_list = []
    for textblock in text_list:
        tokenized_text = sentence_seperator(textblock)
        similarity_matrix = cosine_comp(tokenized_text, vector_data)  
        for vector_idx in range(len(similarity_matrix)):
            comp_vector = similarity_matrix[vector_idx]
            if torch.max(comp_vector) >= 0.58:
                tokenized_text[vector_idx] = tokenized_text[vector_idx] 

        analysed_text = ". ".join(tokenized_text) 
        analysed_text_list.append(analysed_text)
    return analysed_text_list


def sentence_seperator(textblock):
    '''
    A simple regex command to split a block of text to sentences.

    keyword arguments
    
    textblock -- untokenized text

    '''
    tokenized_text= re.split("\\.[\\s \\t \\n]", textblock)

    return tokenized_text 



def cosine_comp(split_text, vector_data):

    '''ppw stand for potentially problamatic words'''

    model = SentenceTransformer("KBLab/sentence-bert-swedish-cased")
    st_embeddings = model.encode(split_text)
    
    similarity_matrix = model.similarity(st_embeddings, vector_data)
    return similarity_matrix
    


if __name__ == "__main__":
    main()

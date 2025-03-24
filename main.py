"""
Course Review Anonymizer

This script helps anonymize course evaluation text by identifying and replacing:
- Personal names with generic placeholders
- Gendered pronouns with gender-neutral alternatives
- Flagging potentially problematic or sensitive text

The tool uses spaCy for named entity recognition and sentence-transformers
for semantic analysis to identify text that might compromise anonymity.

Dependencies:
- spaCy with Swedish language model (sv_core_news_lg)
- selenium for web interaction
- sentence-transformers for semantic analysis
- beautifulsoup4 for HTML parsing
- colorama for terminal colors
- art for ASCII art

Usage:
Run the script and follow the prompts to log in, select a course review,
and process the text. The script will identify names and pronouns,
replace them with generic alternatives, and allow you to submit the
anonymized text back to the system.
"""

import getpass
import torch
import spacy
import os
import re
import pickle

from colorama import Fore
from art import * 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from sentence_transformers import SentenceTransformer, similarity_functions, util
from selenium.webdriver.remote.webelement import WebElement

def main():
    """
    Main function that orchestrates the anonymization process.
    
    The function performs the following steps:
    1. Display an ASCII art title and warning message
    2. Get user login credentials
    3. Prompt for course review URL
    4. Extract texts from the course review page
    5. Perform semantic analysis to identify potentially sensitive content
    6. Identify and mark named entities (people, organizations, etc.)
    7. Replace identified entities and pronouns with generic alternatives
    8. Submit the anonymized text back to the system
    """
    tprint("COURSE REVIEW\n ANONYMIZER", font="xsmall")
    print(Fore.RED + "WARNING! THIS PROGRAM IS NOT FLAWLESS! ")
    print(Fore.RED + "ALWAYS AT ALL TIMES DOUBLE CHECK THE WORK!!!")
    username, password = get_login_details()
    website = pick_website()
    text_list = get_website_and_text(username, password, website)
    analysed_text_list = semantic_analysis(text_list)
    text_dictionary = mark_named_entities(analysed_text_list)
    ct_t_dict = change_entity_name(text_dictionary)
    push_to_site(username, password, website, ct_t_dict)

def push_to_site(username, password, website, ct_t_dict):
    """
    Pushes anonymized text back to the course evaluation website.
    
    The function logs in to the specified website using the provided credentials,
    locates text areas containing the original text, and replaces them with the
    anonymized versions from the dictionary.
    
    Args:
        username (str): User's username for website authentication
        password (str): User's password for website authentication
        website (str): URL of the course evaluation website
        ct_t_dict (dict): Dictionary mapping anonymized text (keys) to original text (values)
                          Used to identify and replace text on the webpage
    
    Returns:
        None
    
    Note:
        The function handles login failures gracefully but does not verify successful submission.
        Always manually verify changes before final submission.
    """
    try:
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
            changed_text = [key for key, value in ct_t_dict.items() if value.removeprefix("<ISSUE>") == element.text.replace("\n", "")]
            element.clear()
            element.send_keys(changed_text[0])

def get_website_and_text(username, password, website):
    """
    Extracts text content from textareas in a course evaluation page.
    
    The function:
    1. Opens a headless Firefox browser
    2. Logs in to the specified website using credentials
    3. Extracts text from all textarea elements
    4. Cleans the text by removing newlines and empty items
    
    Args:
        username (str): Username for website authentication
        password (str): Password for website authentication
        website (str): URL of the course evaluation page
    
    Returns:
        list: List of text strings extracted from textareas
    
    Raises:
        SystemExit: If login fails or the page doesn't contain expected content
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
    Anonymizes identified named entities in the text.
    
    This function:
    1. Iterates through the input dictionary containing text and identified entities
    2. Replaces person names with "Lärare X" (Teacher X)
    3. Changes gendered pronouns to gender-neutral alternatives
    4. Creates a new dictionary mapping anonymized text to original text
    
    Args:
        text_dictionary (dict): Dictionary with keys as original text and values as
                               lists of tuples containing (entity_text, entity_type)
    
    Returns:
        dict: Dictionary mapping anonymized text (keys) to original text (values)
              for later comparison and replacement
    
    Note:
        Only person entities (marked as "PRS" by spaCy) are currently replaced.
        Other entity types remain unchanged.
    """
    ct_t_dict = {}
    skipped_ents = ("Hershkowitz", "Eide", "Wampold")
    for key, value in text_dictionary.items():
        text = str(key)
        changed_text = text
        for entity in value:
            entity_name, ent_type = entity
            if entity_name in skipped_ents:
                continue
            if ent_type == "PRS":
                changed_text = changed_text.replace(entity_name, "Lärare X")          
                text, changed_text = change_pronouns(text, changed_text)   
        ct_t_dict.update({changed_text: text})
    return ct_t_dict

def change_pronouns(text, changed_text):
    """
    Replaces Swedish gendered pronouns with gender-neutral alternatives.
    
    This function finds and replaces:
    - "Du" (you) with "Lärare X" (Teacher X)
    - "Han/hon" (he/she) with "hen" (gender-neutral pronoun in Swedish)
    - "Honom/henne" (him/her) with "hen"
    
    The function is case-insensitive and handles word boundaries to avoid
    replacing parts of words.
    
    Args:
        text (str): The original text (unchanged, passed through for return)
        changed_text (str): Text with entities already replaced, to be modified
    
    Returns:
        tuple: (original_text, modified_text) where pronouns have been replaced
               in the modified_text
    """
    pronouns = [r"\b[Dd]u\b", r"\b[Hh][ao]n\b", r"\b[Hh]onom\b", r"\b[Hh]enne\b"]

    changed_text = re.sub(pronouns[0], "Lärare X", changed_text)
    for i in range(1, len(pronouns)):
        changed_text = re.sub(pronouns[i], "hen", changed_text)

    return text, changed_text

def pick_website():
    """
    Prompts the user for a course evaluation URL and validates it.
    
    The function asks for a URL input and verifies that it matches the expected
    format for Uppsala University course evaluations (kv.uu.se/granska/{number}).
    
    Returns:
        str: Validated URL for the course evaluation
    
    Raises:
        SystemExit: If the URL doesn't match the expected format
    """
    url = input("Enter the URL for the course review you want to edit: ")
    kv_regex = re.compile(r"https://kv\.uu\.se/granska/[0-9]+")
    if kv_regex.match(url):
        return url
    else:
        print("The link provided doesn't seem to be a course evaluation link or it's incomplete, shutting down...")
        raise SystemExit

def get_login_details():
    """
    Prompts the user for login credentials.
    
    Collects username as visible input and password as hidden input
    (not echoed to the console for security).
    
    Returns:
        tuple: (username, password) as strings
    """
    username = input(Fore.WHITE + "please enter your username: ")
    password = getpass.getpass() 
    return username, password

def mark_named_entities(text_list):
    """
    Identifies named entities in text using spaCy's Swedish language model.
    
    This function:
    1. Loads the Swedish language model for spaCy (sv_core_news_lg)
    2. Processes each text string to identify named entities
    3. Extracts entity text and type (e.g., person, organization, location)
    4. Creates a dictionary mapping original text to identified entities
    
    Entity types recognized include:
    - PRS: Person names
    - LOC: Locations
    - ORG: Organizations
    - and others defined by the Swedish spaCy model
    
    Args:
        text_list (list): List of text strings to process
    
    Returns:
        dict: Dictionary with keys as original text and values as lists of
              tuples containing (entity_text, entity_type)
    """
    # Load the Swedish language model
    nlp = spacy.load('sv_core_news_lg')
    text_dictionary = {}
    
    for text in text_list:
        doc = nlp(text)
        
        # Extract entities as (text, label) tuples
        elist = [(ent.text, ent.label_) for ent in doc.ents]
        print(elist)
        text_dictionary.update({text: elist})
    return text_dictionary

def semantic_analysis(text_list):
    """
    Analyzes text semantically to identify potentially sensitive content.
    
    This function:
    1. Loads pre-calculated embeddings of sensitive/problematic words
    2. Splits each text block into sentences
    3. Calculates cosine similarity between each sentence and the problematic word vectors
    4. Marks sentences with high similarity (≥0.65) with an "<ISSUE>" prefix
    
    The threshold of 0.65 was determined experimentally to flag content that
    is semantically similar to problematic words/phrases without too many
    false positives.
    
    Args:
        text_list (list): List of text blocks to analyze
    
    Returns:
        list: Text blocks with potentially sensitive sentences marked with "<ISSUE>" prefix
    """
    with open("embeddings.pickle", "rb") as file:
        vector_data = pickle.load(file)

    analysed_text_list = []
    for textblock in text_list:
        tokenized_text = sentence_separator(textblock)
        similarity_matrix = cosine_comp(tokenized_text, vector_data)  
        for vector_idx in range(len(similarity_matrix)):
            comp_vector = similarity_matrix[vector_idx]
            if torch.max(comp_vector) >= 0.65:
                tokenized_text[vector_idx] = "<ISSUE>" + tokenized_text[vector_idx] 

        analysed_text = ". ".join(tokenized_text) 
        analysed_text_list.append(analysed_text)
    return analysed_text_list

def sentence_separator(textblock):
    """
    Splits a block of text into individual sentences.
    
    Uses regex to split text on periods followed by whitespace.
    This provides a simple but effective sentence tokenization
    for Swedish text.
    
    Args:
        textblock (str): Block of text to be split into sentences
    
    Returns:
        list: List of sentences extracted from the text block
    """
    tokenized_text = re.split(r"\.\s+", textblock)
    return tokenized_text 

def cosine_comp(split_text, vector_data):
    """
    Computes cosine similarity between text sentences and problematic word vectors.
    
    This function:
    1. Loads the Swedish sentence-BERT model
    2. Encodes the input sentences into embeddings
    3. Computes similarity scores between sentence embeddings and 
       pre-calculated problematic word vectors
    
    Args:
        split_text (list): List of sentences to compare
        vector_data (tensor): Pre-calculated embeddings of problematic words/phrases
    
    Returns:
        tensor: Matrix of similarity scores between each sentence and each problematic vector
    """
    # Load Swedish sentence-BERT model
    model = SentenceTransformer("KBLab/sentence-bert-swedish-cased")
    
    # Convert sentences to embeddings
    st_embeddings = model.encode(split_text)
    
    # Calculate similarity between sentence embeddings and problematic word vectors
    return model.similarity(st_embeddings, vector_data)

if __name__ == "__main__":
    main()

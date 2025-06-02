"""
Course Review Anonymizer

This script helps anonymize course evaluation text by identifying and replacing:
- Personal names with generic placeholders
- Gendered pronouns with gender-neutral alternatives
- Flagging potentially problematic or sensitive text

The tool uses spaCy for named entity recognition and sentence-transformers
for semantic analysis to identify text that might compromise anonymity.
"""

import os
import re
import getpass
import pickle
from colorama import Fore
from art import tprint

# Global model variables for caching
_nlp_model = None
_transformer_model = None
_driver = None

def main():
    """Main function that orchestrates the anonymization process."""
    tprint("COURSE REVIEW\n ANONYMIZER", font="xsmall")
    print(Fore.RED + "WARNING! THIS PROGRAM IS NOT FLAWLESS! ")
    print(Fore.RED + "ALWAYS AT ALL TIMES DOUBLE CHECK THE WORK!!!")
    username, password = get_login_details()
    website = pick_website()
    text_list = get_website_and_text(username, password, website)
    analysed_text_list = semantic_analysis(text_list)
    text_dictionary = mark_named_entities(analysed_text_list)
    ct_t_dict = change_entity_name(text_dictionary)
    print(ct_t_dict)
    push_to_site(username, password, website, ct_t_dict)
    
    # Keep program running until user confirms they're done checking the browser
    print(Fore.GREEN + "\nAnonymization complete! The browser window remains open.")
    print(Fore.GREEN + "Review your changes in the browser, then submit them manually if satisfied.")
    input(Fore.GREEN + "Press Enter to exit the program when you're finished (browser will stay open)...")

def push_to_site(username, password, website, ct_t_dict):
    """Pushes anonymized text back to the course evaluation website."""
    # Import here rather than at top level
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup as bs
    
    global _driver
    
    try:
        # Reuse driver if available
        if _driver is None:
            _driver = webdriver.Firefox()
            _driver.get(website)
            _driver.find_element("id", "username").send_keys(username)
            _driver.find_element("id", "password").send_keys(password)
            _driver.find_element("name", "_eventId_proceed").click()
    except:
        print("Could not log in for some reason. Check that username and password is correct.")
    
    html = _driver.page_source
    soup = bs(html, "html.parser") 
    for tag in soup.find_all("textarea"):
        element = _driver.find_element(By.NAME, tag.get("name"))
        element_text = element.text.replace("\n", "")
        
        # Find the matching original text (with or without <ISSUE> tag)
        for anon_text, orig_text in ct_t_dict.items():
            # Check if this is the right textarea by comparing with original text
            if orig_text.removeprefix("<ISSUE>") == element_text:
                # If original had <ISSUE> tag, add it to anonymized text too
                final_text = anon_text
                if orig_text.startswith("<ISSUE>"):
                    final_text = "<ISSUE>" + anon_text
                    
                # Update the textarea
                element.clear()
                element.send_keys(final_text)
                break

def get_website_and_text(username, password, website):
    """Extracts text content from textareas in a course evaluation page."""
    # Import here rather than at top level
    from selenium import webdriver
    from bs4 import BeautifulSoup as bs
    
    global _driver
    
    try:
        options = webdriver.FirefoxOptions()
        # No headless mode so user can see the browser
        
        # Reuse driver if available
        if _driver is None:
            _driver = webdriver.Firefox()
            _driver.get(website)
            _driver.find_element("id", "username").send_keys(username)
            _driver.find_element("id", "password").send_keys(password)
            _driver.find_element("name", "_eventId_proceed").click()
            assert "Kursvärderingar" in _driver.title
    except:
        print("Could not log in for some reason. Check that username and password is correct.")
        if _driver:
            _driver.quit()
            _driver = None
        print("shutting down. Please run the program to try again")
        raise SystemExit
        
    html = _driver.page_source
    soup = bs(html, "html.parser")
    text_list=[]

    for tag in soup.find_all("textarea"):
        text_list.append(tag.text.replace("\n", ""))

    # Don't quit the driver - we'll reuse it
    text_list = list(filter(None, text_list))
    return text_list 
    
def change_entity_name(text_dictionary):
    """Anonymizes identified named entities in the text."""
    ct_t_dict = {}
    skipped_ents = {"Hershkowitz", "Eide", "Wampold", "Van Tubergen","Van tubergens", "Hoschild", "Hochschilds"}  # Fixed set syntax
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
    """Replaces Swedish gendered pronouns with gender-neutral alternatives."""
    pronouns = [r"\b[Dd]u\b", r"\b[Hh][ao]n\b", r"\b[Hh]onom\b", r"\b[Hh]enne\b"]

    changed_text = re.sub(pronouns[0], "Lärare X", changed_text)
    for i in range(1, len(pronouns)):
        changed_text = re.sub(pronouns[i], "hen", changed_text)

    return text, changed_text

def pick_website():
    """Prompts the user for a course evaluation URL and validates it."""
    url = input("Enter the URL for the course review you want to edit: ")
    kv_regex = re.compile(r"https://kv\.uu\.se/granska/[0-9]+")
    if kv_regex.match(url):
        return url
    else:
        print("The link provided doesn't seem to be a course evaluation link or it's incomplete, shutting down...")
        raise SystemExit

def get_login_details():
    """Prompts the user for login credentials."""
    username = input(Fore.WHITE + "please enter your username: ")
    password = getpass.getpass() 
    return username, password

def mark_named_entities(text_list):
    """Identifies named entities in text using spaCy's Swedish language model."""
    import spacy
    
    global _nlp_model
    
    # Load the model only once
    if _nlp_model is None:
        print("Loading spaCy model (this may take a moment)...")
        _nlp_model = spacy.load('sv_core_news_lg')
    
    text_dictionary = {}
    
    for text in text_list:
        doc = _nlp_model(text)
        
        # Extract entities as (text, label) tuples
        elist = [(ent.text, ent.label_) for ent in doc.ents]
        print(elist)
        text_dictionary.update({text: elist})
    return text_dictionary

def semantic_analysis(text_list):
    """Analyzes text semantically to identify potentially sensitive content."""
    import torch
    
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
    """Splits a block of text into individual sentences."""
    tokenized_text = re.split(r"\.\s+", textblock)
    return tokenized_text 

def cosine_comp(split_text, vector_data):
    """Computes cosine similarity between text sentences and problematic word vectors."""
    # Import here to avoid loading at startup
    from sentence_transformers import SentenceTransformer
    
    global _transformer_model
    
    # Load the model only once
    if _transformer_model is None:
        print("Loading sentence transformer model (this may take a moment)...")
        _transformer_model = SentenceTransformer("KBLab/sentence-bert-swedish-cased")
    
    # Convert sentences to embeddings
    st_embeddings = _transformer_model.encode(split_text)
    
    # Calculate similarity between sentence embeddings and problematic word vectors
    return _transformer_model.similarity(st_embeddings, vector_data)

if __name__ == "__main__":
    main()
    # No cleanup function - browser stays open
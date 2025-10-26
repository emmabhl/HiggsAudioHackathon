import ollama
import numpy as np
import re
from app.services.promptLibrary import promptDict
from app.services.text_gen_service import call_qwen_endpoint

all_tags = ['Maths', 'Science', 'History', 'Art', 'Literature', 'Technology', 'Health', 'Programming',
            'Biology', 'Physics', 'Geography', 'Music', 'Psychology', 'Philosophy', 'Education', 
            'Environment', 'Politics', 'Economics', 'Culture', 'Religion', 'Finance', 'Business',
            'Marketing', 'Innovation', 'Wellness', 'Fitness', 'Nature', 'Animals', 'Travel', 'Food',
            'Movies', 'Theatre', 'Photography', 'Design', 'AI', 'Sports', 'Fashion', 'Language', 'Other']

def get_title_summary_tags_from_transcription(text):
    """
    Recieved the text from the audio note made by the user. Uses ollama along with llama3.2:3b to format the text 
    using a formatting prompt template to capture all the key points summarizing the important aspects of the text and 
    then returns the formatted text.
    Prompt should be such that the key points are captured in the summary and are easy to retrieve when doing retrieval using an 
    embedding model
    """
    formatted_text = call_qwen_endpoint(promptDict['noteTaker'].format(text=text))
    #formatted_text = ollama.generate(model='llama3.2:3b', prompt=promptDict['noteTaker'].format(text=text))['response']

    title = call_qwen_endpoint(promptDict['titlePrompt'].format(text=text))
    #title = ollama.generate(model='llama3.2:3b', prompt=promptDict['titlePrompt'].format(text=text))['response'].replace('"', '')

    tag = call_qwen_endpoint(promptDict['tagPrompt'].format(text=text, tags=all_tags))
    #tag = ollama.generate(model='llama3.2:3b', prompt=promptDict['tagPrompt'].format(text=text, tags=all_tags))['response']

    # Extract tags using regex
    tag_list = list(set([x for x in re.findall(r'\b\w+\b', tag) if x in all_tags]))

    return title, formatted_text, tag_list
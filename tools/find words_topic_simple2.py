import os
import csv
import glob
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from gensim import corpora, models
from tika import parser
from fuzzywuzzy import fuzz



nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Pfad zur CSV-Datei mit den Themen und Keywords
topic_csv = os.path.join(os.path.dirname(__file__), 'topics.csv')

# Pfad zum Verzeichnis mit den PDF-Dateien
pdf_dir = os.path.join(os.path.dirname(__file__), 'PDF')

# Pfad zur Ausgabedatei (CSV)
result_csv = os.path.join(os.path.dirname(__file__), 'results.csv')
top_topics_result_csv = os.path.join(os.path.dirname(__file__), 'top_topics.csv')


stoppwords_file = os.path.join(os.path.dirname(__file__), 'latin_stopwords.txt')

# Read in the relevant topics and keywords from the CSV file
topics_df = pd.read_csv(topic_csv)
topics = topics_df['Topics'].tolist()
keywords = topics_df['Keywords'].tolist()

# Define the stop words
with open(stoppwords_file, 'r', encoding='utf-8') as f:
    stop_words = set(f.read().split())
#stop_words = stopwords.words('latin')

# Define the lemmatizer
lemmatizer = WordNetLemmatizer()

# Create an empty list to store the results
results = []

# Loop through all the PDF files in the directory
for pdf_file in glob.glob(os.path.join(pdf_dir, '*.pdf')):
    
    # Parse the PDF file using Tika
    parsed_pdf = parser.from_file(pdf_file)
    
    # Get the raw text from the PDF
    raw_text = parsed_pdf['content']
    
    # Tokenize the text and remove stop words
    tokens = nltk.word_tokenize(raw_text.lower())
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize the tokens
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Create a bag-of-words representation of the tokens
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    
    # Run LDA on the corpus
    lda_model = models.ldamodel.LdaModel(corpus, num_topics=len(topics), id2word=dictionary)
    
    # Get the topic probabilities for the corpus
    topic_probabilities = lda_model.get_document_topics(corpus, minimum_probability=0)
    
    # Loop through the topics and check if the PDF file discusses any of them
    for i, topic in enumerate(topics):
        # Check if any of the keywords for this topic are present in the text
        keywords_for_topic = keywords[i].split(',')
        fuzzy_ratio_threshold = 80 # Minimum ratio to consider a match
        if any([fuzz.ratio(keyword, token) >= fuzzy_ratio_threshold for keyword in keywords_for_topic for token in tokens]):
            # If the PDF discusses the topic, loop through the pages and extract the text
            for j, page in enumerate(parsed_pdf['content'].split('\n\n')):
                # Check if the page discusses the topic
                if any([fuzz.ratio(keyword, page.lower()) >= fuzzy_ratio_threshold for keyword in keywords_for_topic]):
                    # If the page discusses the topic, add it to the results
                    results.append({
                        'PDF Name': os.path.basename(pdf_file),
                        'Page Number': j+1,
                        'Page Text': page,
                        'Topic': topic
                    })
    
# Export the results to a CSV file
with open(result_csv, 'w', newline='') as csvfile:
    fieldnames = ['PDF Name', 'Page Number', 'Page Text', 'Topic']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow(result)

# Create a dictionary to store the topic probabilities for each PDF file
pdf_topics = {}

# Loop through all the PDF files in the directory
for pdf_file in glob.glob(os.path.join(pdf_dir, '*.pdf')):
    
    # Parse the PDF file using Tika
    parsed_pdf = parser.from_file(pdf_file)
    
    # Get the raw text from the PDF
    raw_text = parsed_pdf['content']
    
    # Tokenize the text and remove stop words
    tokens = nltk.word_tokenize(raw_text.lower())
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize the tokens
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Create a bag-of-words representation of the tokens
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    
    # Run LDA on the corpus
    lda_model = models.ldamodel.LdaModel(corpus, num_topics=20, id2word=dictionary)
    
    # Get the topic probabilities for the corpus
    topic_probabilities = lda_model.get_document_topics(corpus, minimum_probability=0)
    
    # Store the topic probabilities in the dictionary
    pdf_topics[os.path.basename(pdf_file)] = topic_probabilities

# Create an empty DataFrame to store the top 10 topics for each PDF file
top_topics_df = pd.DataFrame(columns=['PDF Name', 'Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5', 'Topic 6', 'Topic 7', 'Topic 8', 'Topic 9', 'Topic 10'])

# Loop through the PDF files and get the top 10 topics for each one
for pdf_name, topic_probabilities in pdf_topics.items():
    if len(topic_probabilities) >= 10:
        top_topics = sorted(topic_probabilities, key=lambda x: x[1], reverse=True)[:10]
    else:
        top_topics = sorted(topic_probabilities, key=lambda x: x[1], reverse=True)

    top_topics_dict = {'PDF Name': pdf_name}
    for i, topic in enumerate(top_topics):
        top_topics_dict[f'Topic {i+1}'] = f'Topic {topic[0]} ({topic[1]:.2f})'
    top_topics_df = top_topics_df.append(top_topics_dict, ignore_index=True)

# Write the top topics DataFrame to a CSV file
top_topics_df.to_csv(top_topics_result_csv, index=False)

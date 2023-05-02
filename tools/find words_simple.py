import os
import csv
import re
from fuzzywuzzy import fuzz
from pdfminer.high_level import extract_text
import codecs
import sys
from unidecode import unidecode

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def read_pdf(filename):
    with open(filename, 'rb') as f:
        pdf_text = extract_text(f, codec='utf-8')
    # Count the number of page breaks in the text to get the total number of pages
    page_count = pdf_text.count('\f')
    return pdf_text, page_count

pdf_directory = os.path.join(os.path.dirname(__file__), 'PDF/')
csv_file = os.path.join(os.path.dirname(__file__), 'search_words.csv')
output_file = os.path.join(os.path.dirname(__file__), 'results.csv')

with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    search_words = [row[0] for row in reader]

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF', 'Page', 'Search Word', 'Context'])

for pdf_file in os.listdir(pdf_directory):
    if pdf_file.endswith('.pdf'):
        pdf_text, total_pages = read_pdf(pdf_directory + pdf_file)
        for search_word in search_words:
            escaped_word = re.escape(search_word)
            # match_pattern = re.compile(search_word, re.IGNORECASE) # RegEx in CSV
            match_pattern = re.compile(escaped_word, re.IGNORECASE)
            for match in re.finditer(match_pattern, pdf_text):
                start_index = max(0, match.start() - 100)
                end_index = min(len(pdf_text), match.end() + 100)                
                context = pdf_text[start_index:end_index]
                context = re.sub(r'[^\w\s]+', '', context, flags=re.UNICODE).replace('\n', ' ')
                context = unidecode(context)
                context = context.replace('\f', '')
                context = re.sub(r'\s+', ' ', context)
                page_number = pdf_text[:match.start()].count('\f') + 1
                with open(output_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([pdf_file, page_number, search_word, context])
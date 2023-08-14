import os
import csv
from PyPDF2 import PdfReader
from fuzzywuzzy import fuzz

# Funktion, die PDF-Seiten durchsucht und Übereinstimmungen mit Suchwörtern findet
def search_pdf_pages(pdf_file_path, search_terms):
    with open(pdf_file_path, 'rb') as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        page_count = len(pdf_reader.pages)
        matches = []
        for page_num in range(page_count):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            for term in search_terms:
                if term.lower() in page_text.lower():
                    similarity = fuzz.token_set_ratio(page_text.lower(), term.lower())
                    if similarity >= 75:
                        matches.append((pdf_file_path, page_num+1, term, similarity))
    return matches

# Ordner mit PDFs und CSV-Datei für Suchwörter angeben
pdf_folder = os.path.join(os.path.dirname(__file__), 'PDF/')
search_terms_file = os.path.join(os.path.dirname(__file__), 'search_words.csv')
output_file = os.path.join(os.path.dirname(__file__), 'results_fuzzy.csv')

# Liste mit Suchwörtern aus CSV-Datei erstellen
search_terms = []
with open(search_terms_file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        search_terms.extend(row)

# CSV-Datei für Ergebnisse öffnen und Spaltenüberschriften schreiben
result_file = open('pdf_search_results.csv', 'w', newline='')
csvwriter = csv.writer(result_file)
csvwriter.writerow(['PDF-Datei', 'Seite', 'Suchbegriff', 'Ähnlichkeit', 'Suchwort im Text'])

# Durch alle PDF-Dateien im Ordner iterieren und Suchfunktion aufrufen
for filename in os.listdir(pdf_folder):
    if filename.endswith('.pdf'):
        file_path = os.path.join(pdf_folder, filename)
        matches = search_pdf_pages(file_path, search_terms)
        for match in matches:
            csvwriter.writerow([match[0], match[1], match[2]])
            
# CSV-Datei schließen
result_file.close()

print('Suche abgeschlossen. Ergebnisse sind in pdf_search_results.csv gespeichert.')


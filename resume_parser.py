import pdfplumber
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


#dividing data into sections
def divide_text(text):
    lines=text.split("\n")
    current_section="other"
    data = {"skills":"","experience":"","education":"","projects":"","other":""}
  
    for line in lines:
        line_lower=line.lower()
        if "skills" in line_lower:
            current_section="skills"
        elif "experience" in line_lower:
            current_section="experience"
        elif "education" in line_lower:
            current_section="education"
        elif "projects" in line_lower:
            current_section="projects"

        data[current_section]=" "+line.lower()
   
    return data


#Cleaning data (removing special chars and stopwords)
def clean_text(text):
    text=re.sub(r'[^a-zA-Z0-9\/\#\+\s]',"",text)
    nltk.download('stopwords')
    stop_words=set(stopwords.words('english'))
    words=text.split()
    cleaned_text=[word for word in words if word not in stop_words]
    nltk.download('wordnet')
    lemmatizer=WordNetLemmatizer()
    final_text= [ lemmatizer.lemmatize(word,'v') for word in cleaned_text]
    return " ".join(final_text)



# Test it
text=extract_text("Tejaswini_Resume.pdf")
text=divide_text(text)
for key in text:
    text[key]=clean_text(text[key])
print(text)

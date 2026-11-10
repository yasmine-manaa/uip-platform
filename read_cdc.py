from docx import Document

doc = Document(r'C:\Users\yasmi\Downloads\Cahier_des_charges_Underwriting_Intelligence_Platform.docx')

for para in doc.paragraphs:
    print(para.text)

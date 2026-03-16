from langchain_community.document_loaders import PyPDFLoader 

file_path="Backend/DocHandler/A_Intro_to_AI_ML_Project_Title_in_IEEE_Double_Column_Format__1_-3.pdf"

loader=PyPDFLoader(file_path)

data=loader.load()

print(data)
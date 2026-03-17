from langchain_community.document_loaders import PyPDFLoader 


def pdf_loader(file_path):
    loader=PyPDFLoader(file_path)
    data=loader.load()
    return data

def build_docs(docs):
    context=""
    for i in docs:
        context+=i.page_content +"\n\n"
    return context 

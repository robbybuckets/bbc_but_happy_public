from google.cloud import language_v1

def analyze_text_sentiment(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_sentiment(document=document)
    sentiment = response.document_sentiment
    return sentiment
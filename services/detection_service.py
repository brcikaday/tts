from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import os
import re 


BASE_DIR = os.path.dirname(__file__)
file_path = os.path.abspath(os.path.join(BASE_DIR,'..','detection_model', 'best_model2'))

tag2id = {'O':0,'PROTECT':1}
id2tag = {value:key for key,value in tag2id.items()}

model_path = file_path
tokenizer = None
model = None

async def load_model():
    global tokenizer, model
    if tokenizer is None or model is None:
        print(f"Resolved path: {model_path}")
        print(f"Is this a real directory? {os.path.isdir(model_path)}")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForTokenClassification.from_pretrained(model_path)


def detect_risky_words(text: str):
    if tokenizer is None or model is None:
        raise Exception("Model not loaded. Please call load_model() first.")

    predicted_labels = []
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    for sentence in re.split(r'(?<=[.!?]) +', text):
        words = sentence.split()

        if not words:
            continue
        inputs = tokenizer(words, is_split_into_words=True, return_tensors='pt', padding=True, truncation=True)
        word_ids = inputs.word_ids(batch_index=0)

        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)

        # Perform inference
        with torch.no_grad():
            outputs = model(input_ids, attention_mask=attention_mask)

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1).squeeze().tolist()

        predicted_labels.append({
            'words': words,
            'word_ids': word_ids,
            'predictions': predictions
        })

    risky_words = []
    for item in predicted_labels:
        words = item['words']
        word_ids = item['word_ids']
        predictions = item['predictions']

        aligned_predictions = []
        current_word_index = -1
        previous_word_id = None

        for token_idx, word_id in enumerate(word_ids):
            if word_id is not None:
                if previous_word_id != word_id:
                    aligned_predictions.append(id2tag[predictions[token_idx]])
                    current_word_index += 1
            previous_word_id = word_id

        for i in range(len(words)):
            if aligned_predictions[i] == 'PROTECT':
                risky_words.append(words[i])            
    return risky_words
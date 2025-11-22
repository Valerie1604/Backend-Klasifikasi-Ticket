import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
from pathlib import Path

class ModelWrapper:
    def __init__(self, model_dir: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = model_dir
        # load tokenizer & model
        self.tokenizer = BertTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model = BertForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
        self.model.to(self.device)
        # load label encoder
        le_path = Path(model_dir) / "label_encoder.pkl"
        if not le_path.exists():
            raise FileNotFoundError(f"label_encoder.pkl not found in {model_dir}")
        with open(le_path, "rb") as f:
            self.label_encoder = pickle.load(f)

    def predict(self, text: str):
        enc = self.tokenizer(text, truncation=True, padding=True, return_tensors="pt", max_length=256)
        enc = {k: v.to(self.device) for k, v in enc.items()}
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**enc)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()
            pred_idx = int(torch.argmax(logits, dim=1).cpu().item())
            label = self.label_encoder.inverse_transform([pred_idx])[0]
            scores = {self.label_encoder.inverse_transform([i])[0]: float(probs[i]) for i in range(len(probs))}
        return label, scores

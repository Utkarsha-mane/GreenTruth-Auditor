import pandas as pd
import torch
from transformers import pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

def evaluate_climatebert():
    # 1. Load the Engineered Dataset
    df = pd.read_csv("C:\Shriya\green-truth-auditor\green_truth_cleaned (6).csv")
    
    # 2. Load Local Model
    device = 0 if torch.cuda.is_available() else -1
    print("🤖 Loading ClimateBERT...")
    classifier = pipeline("text-classification", model="./models/climatebert", device=device)

    # 3. Prepare Data
    # We combine description and products for the best context
    df['combined_text'] = df['description'].astype(str) + " " + df['products'].astype(str)
    texts = df['combined_text'].tolist()
    y_true = df['target_is_environmental'].tolist()

    # 4. Run Inference
    print(f"⚖️ Evaluating {len(texts)} samples...")
    results = classifier(texts, truncation=True)
    
    # Map 'yes'/'LABEL_1' to 1 and 'no'/'LABEL_0' to 0
    y_pred = [1 if res['label'].lower() in ['yes', 'label_1'] else 0 for res in results]

    # 5. Report
    print("\n" + "="*40)
    print("🛡️ GATEKEEPER (CLIMATEBERT) PERFORMANCE")
    print("="*40)
    print(f"Overall Accuracy: {accuracy_score(y_true, y_pred):.2%}")
    print("\nDetailed Metrics:")
    print(classification_report(y_true, y_pred, target_names=['Non-Env', 'Environmental']))

if __name__ == "__main__":
    evaluate_climatebert()
import pandas as pd
import torch
from transformers import pipeline
from sklearn.metrics import classification_report, accuracy_score

def evaluate_distilbart():
    # 1. Load the Engineered Dataset
    df = pd.read_csv("C:\Shriya\green-truth-auditor\green_truth_cleaned (8).csv")
    
    # 2. Load Local Zero-Shot Model
    device = 0 if torch.cuda.is_available() else -1
    print("🤖 Loading DistilBART Auditor...")
    auditor = pipeline("zero-shot-classification", model="./models/distilbart", device=device)

    # 3. Prepare Data
   
    test_df = df.head(200).copy() 
    test_df['combined_text'] = test_df['description'].astype(str) + " " + test_df['products'].astype(str)
    
    texts = test_df['combined_text'].tolist()
    y_true = test_df['target_audit_label'].tolist()

    # 4. Run Inference
    candidate_labels = ["Fact-Based", "Marketing Hype"]
    print(f"⚖️ Running Zero-Shot Audit on {len(texts)} samples (this may take a minute)...")
    
    results = auditor(texts, candidate_labels=candidate_labels)
    y_pred = [res['labels'][0] for res in results]

    # 5. Report
    print("\n" + "="*40)
    print("🔍 AUDITOR (DISTILBART) PERFORMANCE")
    print("="*40)
    print(f"Overall Accuracy: {accuracy_score(y_true, y_pred):.2%}")
    print("\nDetailed Metrics:")
    print(classification_report(y_true, y_pred))

if __name__ == "__main__":
    evaluate_distilbart()
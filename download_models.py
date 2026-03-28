from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import os

# Create a folder for local models
if not os.path.exists("models"):
    os.makedirs("models")

print("🚀 Starting download: ClimateBERT (Gatekeeper)...")
# Download and save to local folder
m1_name = "climatebert/environmental-claims"
m1 = AutoModelForSequenceClassification.from_pretrained(m1_name)
t1 = AutoTokenizer.from_pretrained(m1_name)
m1.save_pretrained("./models/climatebert")
t1.save_pretrained("./models/climatebert")

print("🚀 Starting download: DistilBART (Auditor)...")
m2_name = "valhalla/distilbart-mnli-12-3"
m2 = AutoModelForSequenceClassification.from_pretrained(m2_name)
t2 = AutoTokenizer.from_pretrained(m2_name)
m2.save_pretrained("./models/distilbart")
t2.save_pretrained("./models/distilbart")

print("✅ DONE! Models are now saved in your /models folder.")
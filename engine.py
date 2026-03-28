import pandas as pd
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import torch
from rapidfuzz import process
import re
import PyPDF2
import io

class GreenAuditorEngine:
    def __init__(self):
        
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Intelligence Layers
        self.relevance_filter = pipeline("text-classification", model="./models/climatebert", device=self.device)
        self.intent_analyzer = pipeline("zero-shot-classification", model="./models/distilbart", device=self.device)
        
        try:
            self.df = pd.read_csv("bcorp_data.csv")
            self.df.columns = self.df.columns.str.strip()
        except Exception as e:
            print(f"Data Load Error: {e}")
            self.df = pd.DataFrame()

    def process_pdf(self, file_bytes):
        """Advanced PDF Intelligence: Samples sections from long reports."""
        try:
            reader = PyPDF2.PdfReader(file_bytes)
            num_pages = len(reader.pages)
            text_blocks = []
            
            # Smart Sampling (Front, Middle, Back)
            pages_to_scan = list(range(min(12, num_pages)))
            if num_pages > 30:
                pages_to_scan.extend(range(num_pages // 2, (num_pages // 2) + 8))
                pages_to_scan.extend(range(num_pages - 8, num_pages))
            
            for pg in set(pages_to_scan):
                if pg < num_pages:
                    text_blocks.append(reader.pages[pg].extract_text())
            
            return " ".join(text_blocks)
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def scrape_url(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            return " ".join([t.get_text() for t in soup.find_all(['p', 'h1', 'h2', 'li'])])[:5000]
        except:
            return "Error: Source Unreachable."

    def get_industry_context(self, text):
        """Gatekeeper logic to prevent tech/food mismatches."""
        tech = ['software', 'electronics', 'iphone', 'digital', 'tech', 'cloud', 'silicon']
        apparel = ['fabric', 'clothing', 'fashion', 'textile', 'cotton', 'shoes', 'apparel']
        
        lower_text = text.lower()
        if any(k in lower_text for k in tech): return 'tech'
        if any(k in lower_text for k in apparel): return 'apparel'
        return 'general'

    def get_industry_averages(self, industry_name):
        """Calculates benchmark data for the Radar chart."""
        if self.df.empty: return None
        
        # Filter for similar industries
        relevant = self.df[self.df['industry'].str.contains(industry_name, case=False, na=False)]
        if relevant.empty: relevant = self.df 

        def clean(x):
            try: return float(x) if str(x).replace('.','').isdigit() else 0
            except: return 0

        return {
            "avg_env": relevant['environment_score'].apply(clean).mean(),
            "avg_prac": relevant['environment_practices'].apply(clean).mean(),
            "avg_out": relevant['environment_outputs'].apply(clean).mean(),
            "avg_in": relevant['environment_inputs'].apply(clean).mean(),
            "avg_overall": (relevant['overall_score'].apply(clean).mean()) / 2
        }

    def verify_certification(self, text):
        if self.df.empty: return False, None, None
        
        brand_list = self.df['brand'].astype(str).tolist()
        match = process.extractOne(text[:300], brand_list, score_cutoff=90)
        
        if match:
            temp_data = self.df[self.df['brand'] == match[0]].iloc[0]
            context = self.get_industry_context(text)
            # Match rejection logic
            if context == 'tech' and 'food' in str(temp_data.get('industry', '')).lower():
                return False, None, None
            return True, match[0], temp_data.to_dict()
        return False, None, None

    def run_audit(self, text):
        # Segmentation
        all_sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if len(s.strip()) > 25]
        
        has_cert, brand_name, brand_data = self.verify_certification(text)
        
        audit_results = []
        buzzwords = ["eco-friendly", "green", "sustainable", "natural", "conscious", "net-zero", "carbon-neutral"]
        detected_buzz = set()
        
        # Scan 
        for sent in all_sentences[:100]:
            if len(audit_results) >= 40: break
            
            relevance = self.relevance_filter(sent[:450])[0]
            if relevance['label'] == 'yes':
                nli = self.intent_analyzer(sent, candidate_labels=["Fact-Based", "Marketing Hype"])
                fluff_score = nli['scores'][nli['labels'].index("Marketing Hype")]
                
                found = [b for b in buzzwords if b in sent.lower()]
                for b in found: detected_buzz.add(b)
                
                audit_results.append({
                    "text": sent,
                    "category": "Fact" if fluff_score < 0.35 else ("Vague" if fluff_score > 0.65 else "Unverified"),
                    "fluff_prob": fluff_score
                })

        if not audit_results: return {"status": "no_claim"}
        
        # Scoring logic
        base_fluff = sum(s['fluff_prob'] for s in audit_results) / len(audit_results)
        gwi = (base_fluff * 70) + (min(len(detected_buzz) * 5, 30))
        if not has_cert: gwi += 15
        
        return {
            "status": "success",
            "gwi": max(0, min(100, int(gwi))),
            "audit_ledger": audit_results,
            "brand_name": brand_name,
            "has_cert": has_cert,
            "brand_data": brand_data,
            "buzz_count": len(detected_buzz)
        }
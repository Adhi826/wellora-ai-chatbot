import csv
import os
import re

# Resolve dataset paths relative to the project root (repo root is two levels up from backend/)
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
DISEASES_CSV = os.path.join(_PROJECT_ROOT, "datasets", "archive (2)", "diseases.csv")
MEDICINES_CSV = os.path.join(_PROJECT_ROOT, "datasets", "archive (1)", "A_Z_medicines_dataset_of_India.csv")

# Disease → Generic Medicine Mapping (India)
DISEASE_MEDICINE_MAP = {
    "fever": ["Paracetamol"],
    "viral fever": ["Paracetamol", "Ibuprofen"],
    "common cold": ["Cetirizine", "Phenylephrine"],
    "dry cough": ["Dextromethorphan"],
    "wet cough": ["Ambroxol", "Guaifenesin"],
    "sore throat": ["Amoxicillin (bacterial)", "Lozenges"],
    "headache": ["Paracetamol", "Ibuprofen"],
    "migraine": ["Sumatriptan", "Naproxen"],
    "body pain": ["Diclofenac", "Aceclofenac"],
    "toothache": ["Ibuprofen", "Amoxicillin"],
    "gastritis": ["Pantoprazole", "Omeprazole"],
    "acidity": ["Pantoprazole", "Ranitidine"],
    "gerd": ["Esomeprazole"],
    "vomiting": ["Ondansetron", "Domperidone"],
    "diarrhea": ["ORS", "Loperamide"],
    "constipation": ["Lactulose", "Bisacodyl"],
    "typhoid": ["Cefixime", "Azithromycin"],
    "urinary tract infection": ["Nitrofurantoin", "Ciprofloxacin"],
    "uti": ["Nitrofurantoin", "Ciprofloxacin"],
    "tuberculosis": ["Isoniazid", "Rifampicin"],
    "pneumonia": ["Azithromycin", "Amoxicillin"],
    "hypertension": ["Amlodipine", "Telmisartan"],
    "high blood pressure": ["Amlodipine", "Telmisartan"],
    "type 2 diabetes": ["Metformin", "Glimepiride"],
    "diabetes": ["Metformin", "Glimepiride"],
    "high cholesterol": ["Atorvastatin"],
    "anemia": ["Ferrous Sulfate", "Folic Acid"],
    "asthma": ["Salbutamol", "Budesonide"],
    "allergy": ["Cetirizine", "Fexofenadine"],
    "skin fungal infection": ["Clotrimazole", "Ketoconazole"],
    "fungal infection": ["Clotrimazole", "Ketoconazole"],
    "bacterial skin infection": ["Mupirocin"],
    "acne": ["Benzoyl Peroxide", "Clindamycin"],
    "scabies": ["Permethrin"],
    "malaria": ["Chloroquine", "Artesunate"],
    "dengue": ["Paracetamol", "ORS"],
    "arthritis": ["Diclofenac", "Methotrexate"],
    "back pain": ["Aceclofenac", "Thiocolchicoside"],
    "muscle spasm": ["Cyclobenzaprine"],
    "epilepsy": ["Sodium Valproate", "Carbamazepine"],
    "depression": ["Sertraline", "Fluoxetine"],
    "anxiety": ["Alprazolam (short term)"],
    "hypothyroidism": ["Levothyroxine"],
    "hyperthyroidism": ["Methimazole"],
    "heart failure": ["Furosemide", "Enalapril"],
    "angina": ["Nitroglycerin"],
    "stroke prevention": ["Aspirin", "Clopidogrel"],
    "insomnia": ["Melatonin"],
    "vitamin d deficiency": ["Cholecalciferol"],
    "vitamin b12 deficiency": ["Cyanocobalamin"],
    "hemorrhoids": ["Hydrocortisone Cream"],
    "piles": ["Hydrocortisone Cream"],
    "ear infection": ["Ciprofloxacin Drops"],
    "eye infection": ["Moxifloxacin Eye Drops"],
    "chickenpox": ["Acyclovir"],
    "covid-19": ["Paracetamol", "ORS"],
    "covid": ["Paracetamol", "ORS"],
    "sinusitis": ["Amoxicillin", "Levocetirizine"],
    "kidney stones": ["Diclofenac"],
    "pcos": ["Metformin"],
    "gout": ["Allopurinol"],
}

class MedicalEngine:
    def __init__(self):
        self.diseases = []
        self.medicine_map = DISEASE_MEDICINE_MAP
        self._load_diseases()

    def _load_diseases(self):
        if os.path.exists(DISEASES_CSV):
            with open(DISEASES_CSV, mode='r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f)
                self.diseases = list(reader)

    def match_disease(self, user_query):
        """
        Scoring logic:
        - Direct name match: +50
        - Symptom match: +25 per matched symptom keyword/phrase
        """
        matches = []
        user_query_lower = user_query.lower()
        
        for d in self.diseases:
            score = 0
            name_lower = d['name'].lower()
            
            # Direct name match
            if name_lower in user_query_lower:
                score += 50
                
            symptoms_text = d.get('symptoms', '').lower()
            # Split symptoms by comma and check each
            symptom_list = [s.strip() for s in symptoms_text.split(',')]
            for s in symptom_list:
                if s and s in user_query_lower:
                    score += 25
                
            if score > 0:
                matches.append({
                    "disease": d['name'],
                    "score": min(score, 100),
                    "details": d
                })
        
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:3]

    def search_medicines(self, keyword, limit=3):
        results = []
        if not os.path.exists(MEDICINES_CSV):
            return results
            
        with open(MEDICINES_CSV, mode='r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                name = row.get('name', '').lower()
                comp1 = row.get('short_composition1', '').lower()
                comp2 = row.get('short_composition2', '').lower()
                
                if keyword.lower() in name or \
                   keyword.lower() in comp1 or \
                   keyword.lower() in comp2:
                    results.append(row)
                    count += 1
                if count >= limit:
                    break
        return results

    def _lookup_generic_medicines(self, disease_name):
        """Look up generic medicines from the built-in mapping."""
        key = disease_name.lower().strip()
        if key in self.medicine_map:
            return self.medicine_map[key]
        # Partial match fallback
        for map_key, meds in self.medicine_map.items():
            if map_key in key or key in map_key:
                return meds
        return []

    def get_dataset_context(self, user_query):
        matched_diseases = self.match_disease(user_query)
        context = "--- INTERNAL DATASET MATCHES ---\n"
        
        if matched_diseases:
            d = matched_diseases[0]
            score = d['score']
            details = d['details']
            
            context += f"TOP DISEASE MATCH: {d['disease']} (Confidence Score: {score}%)\n"
            context += f"Symptoms: {details.get('symptoms', 'N/A')}\n"
            context += f"Description: {details.get('description', 'N/A')}\n"
            context += f"Causes: {details.get('causes', 'N/A')}\n"
            context += f"Guidance: {details.get('guidance', 'N/A')}\n"
            context += f"Treatments: {details.get('treatments', 'N/A')}\n\n"
            
            # Generic medicine lookup from built-in map
            generic_meds = self._lookup_generic_medicines(d['disease'])
            if generic_meds:
                context += "RECOMMENDED GENERIC MEDICINES (India):\n"
                for med in generic_meds:
                    context += f"  - {med}\n"
                context += "(Note: These are generic names. Do NOT include dosage in mg. Always advise consulting a doctor.)\n\n"
            
            # Search for relevant medicines from CSV dataset
            meds = self.search_medicines(d['disease'])
            if meds:
                context += "RELEVANT MEDICINES FROM DATASET:\n"
                for m in meds:
                    context += f"- {m['name']} (Type: {m.get('type','allopathy')}, Comp: {m.get('short_composition1','')})\n"
        else:
            # Even without a disease match, try keyword matching for medicines
            generic_meds = self._lookup_generic_medicines(user_query)
            if generic_meds:
                context += f"GENERIC MEDICINE SUGGESTION FOR '{user_query}':\n"
                for med in generic_meds:
                    context += f"  - {med}\n"
                context += "(Note: Generic names only. No dosage. Advise doctor consultation.)\n\n"
            else:
                context += "No direct dataset match found for symptoms.\n"
            score = 0
            
        return context, score

medical_engine = MedicalEngine()

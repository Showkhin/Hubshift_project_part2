# NDIS Incident Insights — viz + recommendations

- Home: combined preview + 3 cloud CSVs (final_emotion_ensemble.csv, main.csv, reporter.csv)
- Process: upload a CSV (used for plots) or prepare & clean from cloud (with optional Ollama cleaning)
- Questions & Plots: pick a question, see only its plots, then "Get recommendations for these plots"
- Recommendations: color-coded, concise guidance for the visible plots. Navigate back and forth.

## Run
```bash
pip install -r requirements.txt
python -m streamlit run app.py


from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

questions = {
        "What ingredients you prefer (e.g. grass jelly, mini taro…)": ["grass jelly",'taro', 'red bean', 'coco sago', 'almond'],
        "What taste you prefer (e.g. how much sweetness)":"number",
        "Cold or Hot":["Cold","Hot"],
        "Preferred size":['M','L'],
        "How many people (so we can recommend combo)":"number",
        "How long you can wait (take into consider both product making and peak hour)":"number"}

def save_response(responses):
    df = pd.DataFrame([responses], columns=questions.keys())
    try:
        existing_df = pd.read_csv("survey_results.csv")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv("survey_results.csv", index=False)

@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        responses = {q:request.form[q] for q in questions.keys()}
        save_response(responses)
        return "Thank you for completing the survey!"
    return render_template('survey.html', questions=questions)

if __name__ == "__main__":
    app.run(debug=True)


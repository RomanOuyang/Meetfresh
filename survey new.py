
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

questions = {
        "What ingredients you prefer (e.g. grass jelly, mini taro…)主料": ["Grass Jelly",'Taro Ball', 'Red Bean', 'Coco Sago', 'Almond','Purple Rice','Pudding','Shaved Ice'],
        "What taste you prefer (e.g. how much sweetness)甜度":[1,2,3,4,5],
        "Cold or Hot冷热":["Cold","Hot"],
        "Preferred size大小":['M','L'],
        "How many people (so we can recommend combo)人数":"number",
        "How long you can wait (take into consider both product making and peak hour)等待时长":"number"}
results_data = {
    "Icy Taro Ball Signature": {"image": "static/icy-taro-ball-Signature.png", "link": "https://www.meetfresh.us/icy-taro-ball-signature/"},
    "Icy Grass Jelly Signature": {"image": "static/Signature-Icy-Grass-Jelly.png", "link": "https://www.meetfresh.us/icy-grass-jelly-signature/"},
    "Hot Red Bean Soup Signature": {"image": "static/Hot-Red-Bean-Soup-Signature.png", "link": "https://www.meetfresh.us/hot-red-bean-soup-signature/"},
    "Hot Grass Jelly Soup Signature": {"image": "static/Hot-Grass-Jelly-Signature.png", "link": "https://www.meetfresh.us/hot-grass-jelly-soup-signature/"},
    "Hot Almond Soup Signature": {"image": "static/Hot-Almond-Soup-Signature.png", "link": "https://www.meetfresh.us/hot-almond-soup-signature/"},

}

def save_response(responses):
    df = pd.DataFrame([responses], columns=['ingred','sweet','temp','size','people','wait'])
    try:
        existing_df = pd.read_csv("survey_results.csv")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv("survey_results.csv", index=False)

    
@app.route('/', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        responses = {
            'ingred': request.form['What ingredients you prefer (e.g. grass jelly, mini taro…)主料'],
            'sweet': request.form['What taste you prefer (e.g. how much sweetness)甜度'],
            'temp': request.form['Cold or Hot冷热'],
            'size': request.form['Preferred size大小'],
            'people': request.form['How many people (so we can recommend combo)人数'],
            'wait': request.form['How long you can wait (take into consider both product making and peak hour)等待时长']
        }
        df = pd.DataFrame([responses])
        temp_choice = df['temp'][0]
        ingred = df['ingred'][0]
        filtered_results = {key: value for key, value in results_data.items() if 
                            ((temp_choice == "Cold" and "Icy" in key) or 
                            (temp_choice == "Hot" and "Hot" in key)) and
                            (ingred in key)}

        return render_template('result.html', responses=responses, results=filtered_results)
    return render_template('survey.html', questions=questions)

if __name__ == "__main__":
    app.run(debug=True)


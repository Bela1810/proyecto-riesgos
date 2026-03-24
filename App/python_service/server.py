import sys, os
import uvicorn
from fastapi import FastAPI
import joblib
import pandas as pd

app = FastAPI()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(get_base_path(), "models", "lightgbm_con_libranza.joblib"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(data: dict):
    df = pd.DataFrame([data])
    prediction = model.predict(df)
    return {"prediction": int(prediction[0])}

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    uvicorn.run(app, host="127.0.0.1", port=port)
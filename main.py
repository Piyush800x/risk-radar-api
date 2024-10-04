from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests
import os

load_dotenv()
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    url = f"https://www.cvedetails.com/api/v1/vulnerability/search?outputFormat=json&vendorName=Google" \
          f"&productName=Chrome&pageNumber=1" \
          f"&resultsPerPage=40"
    access_token = os.getenv("CVEDETAILS_API")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "*/*"
    }

    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(data)
        # dic = {
        #
        # }
        # for info in data["results"]:

        return data
    else:
        print("Error")
        return "Error"


if __name__ == "__main__":
    app.run(debug=True)

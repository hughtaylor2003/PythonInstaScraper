from flask import Flask, request, render_template
import csv
import io
import re
import pandas as pd
import requests
import threading
import requests
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Function for concurrent GET link calls
def concurrent_get_links(urls):
    results = []

    # Define a worker function for each thread
    def worker(url):
        try:
            print(f"GETTING REQUEST FOR URL: {url} WITH NO PROXY")
            r = requests.get(url + "media/?size=l")
        except:
            # With proxy
            print(f"GETTING REQUEST FOR URL: {url} WITH PROXY")
            r = requests.get(
                url + "media/?size=l",
                proxies={
                    "https": 'http://7KrAOumff6uMdSrF:3UPw4vDCeBOstj7l_streaming-1@geo.iproyal.com:12321'
                },
            )
        results.append(r.url)

    threads = [threading.Thread(target=worker, args=(url,)) for url in urls]

    # Start threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return results

@app.route('/')
def index():
    # Load the model outside the function
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    js_array_data = request.form['dataArray']
    classarray = js_array_data.split(',')



    if file:
        content = parse_csv(file)
        final = ""
        for x in content:
            response = requests.get(x)
            image_data = response.content
            base64_image = base64.b64encode(image_data).decode('utf-8')
            div1 = '<div style="display:flex font-size:20px">'
            div2 = '</div>'
            img = f'<img src="data:image/jpeg;base64,{base64_image}" width="200" height="200">'
            finalclass=query(x, classarray)
            line = div1 + img + finalclass + div2 + '<br><br>' 
            final = final + line
        return final

def parse_csv(file):
    # Load data from CSV
    data = pd.read_csv(file)
    # Extract URLs from the 'Image_URL' column
    urls = [row['Image_URL'] for index, row in data.iterrows()]
    result_urls = concurrent_get_links(urls)
    return result_urls

API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-large-patch14"
headers = {"Authorization": "Bearer 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"}
imageurl = 'https://scontent-lhr8-1.cdninstagram.com/v/t51.2885-15/416678021_1081158129901003_1462508426101931245_n.jpg?stp=dst-jpg_e15&efg=e30&_nc_ht=scontent-lhr8-1.cdninstagram.com&_nc_cat=107&_nc_ohc=TiYnuno7MCsAX_YUoV7&edm=AGenrX8BAAAA&ccb=7-5&oh=00_AfAhWHHVe87N_ksm5qFy_YJiCdzX3e3dwJMMb0n_9uvuZg&oe=65BDBC0A&_nc_sid=ed990e'


def query(imageurl, givenarray):
    image = Image.open(requests.get(imageurl, stream=True).raw)
    img_buffer = BytesIO()
    image.save(img_buffer, format="JPEG")  # Save the image to the buffer
    img_buffer.seek(0)
    img_data = img_buffer.read()
    payload = {
        "parameters": {"candidate_labels": givenarray},
        "inputs": base64.b64encode(img_data).decode("utf-8")
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    highest = 0
    curcat = ''
    for x in response.json():
      if highest < (x['score']):
        highest = (x['score'])
        curcat = x['label']
    return curcat

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

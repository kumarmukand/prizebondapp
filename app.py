from flask import Flask, render_template, request
import requests
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/path/to/upload/folder'

def fetch_prize_numbers(prize_type, date):
    # Define a list of URL templates
    url_templates = [
        f"https://savings.gov.pk/wp-content/uploads/{date}-Rs{prize_type}.txt",
        f"https://savings.gov.pk/wp-content/uploads/{date}-Rs-{prize_type}.txt",
        f"https://savings.gov.pk/wp-content/uploads/{date}-Rs-{prize_type}-1.txt",
        f"https://savings.gov.pk/wp-content/uploads/{date}-Rs-{prize_type}-.txt"
    ]

    # Define regex patterns for different prize bond types
    patterns = {
        "750": {
            "first_prize": r"First Prize of Rs.1,500,000/-\s*(\d+)",
            "second_prize": r"Second Prize of Rs.Rs.500,000/- each.\s*([\d\s]+)",
            # "third_prize": r"1696 Prize\(s\) of 9,300/-  Each\s*([\d\s]+)"
            "third_prize": r"1696 Prize\(s\) of 9,300/-  Each(.+?)(?=First|Second|$)"
            
            
        },
        "1500": {
            "first_prize": r"First Prize of Rs. 3,000,000/-\s*(\d+)",
            "second_prize": r"Second Prize of Rs.1,000,000/- Each\s*([\d\s]+)",
            "third_prize": r"Third Prizes of Rs.18,500/- Each \(1696 Prizes\)(.+?)(?=First|Second|$)"
        },
        "200": {
            "first_prize": r"First Prize of Rs.750,000/-\s*(\d+)",
            "second_prize": r"Second Prize of Rs.Rs.250,000/- each.\s*([\d\s]+)",
            "third_prize": r"2394 Prize\(s\) of 1250/-  Each(.+?)(?=First|Second|$)"
        },
        "100": {
            "first_prize": r"First Prize of Rs. 700,000/-\s*(\d+)",
            "second_prize": r"Second Prize of Rs.200,000/- Each\s*([\d\s]+)",
             "third_prize": r"Third Prizes of Rs.1,000/- Each \(1199 Prizes\)(.+?)(?=First|Second|$)"
        }
    }

    for url in url_templates:
        try:
            response = requests.get(url)
            # Check if the response is successful and contains the expected data
            if response.status_code == 200 and "First Prize" in response.text:
                data = response.text
                pattern = patterns[str(prize_type)]

                # Parse data and return results
                first_prize = re.search(pattern['first_prize'], data).group(1)
                second_prize = re.findall(pattern['second_prize'], data)[0].split()
                third_prize_section = re.search(pattern['third_prize'], data,re.DOTALL)
                if third_prize_section:
                    third_prize = re.findall(r"\b\d+\b", third_prize_section.group(1))
                else:
                    print("Error: Couldn't find third prize.")
                    third_prize = None

                # print("Third Prize List:", third_prize)
                return first_prize, second_prize, third_prize

        except requests.exceptions.RequestException as e:
            print(f"Error: Unable to fetch data from {url}. {e}")

    # If none of the URLs work, return an error
    print("Error: Unable to fetch data from any URL.")
    return None, None, None 


def check_prize_bonds(prize_type, date, user_numbers):
    first_prize, second_prize, third_prize = fetch_prize_numbers(prize_type, date)
    messages = []

    for num in user_numbers:
        if num == first_prize:
            messages.append(f"Congratulations! {num} won the first prize.")
        elif num in second_prize:
            messages.append(f"Congratulations! {num} won the second prize.")
        elif third_prize and num in third_prize:  # Ensure third_prize is not None
            messages.append(f"Congratulations! {num} won the third prize.")

    # Check if messages is empty
    if not messages:
        messages.append("Unfortunately, none of your numbers have won.")

    return messages



@app.route('/', methods=['GET', 'POST'])
def index():
    messages = []

    if request.method == 'POST':
        prize_type = request.form['prize_type']
        date = request.form['date']
        file = request.files['file']
        if file:
            user_numbers = file.read().decode('utf-8').splitlines()
            messages = check_prize_bonds(prize_type, date, user_numbers)

    return render_template('index.html', messages=messages)

if __name__ == '__main__':
    app.run(debug=True)
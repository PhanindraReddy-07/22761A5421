from flask import Flask, jsonify
import requests
import random
import time

app = Flask(__name__)

class AverageCalculator:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.window_prev_state = []
        self.window_current_state = []
    def fetch_numbers(self, number_type):
        base_url = "http://20.244.56.144/test"
        endpoints = {
            'p': '/primes',
            'f': '/fibo',
            'e': '/even',
            'r': '/rand'
        }
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQzMTUyOTYzLCJpYXQiOjE3NDMxNTI2NjMsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6ImMyMDhjNTgxLTNmMzAtNDdhOS05MWM4LWVhNmUwZmZkYmFhYiIsInN1YiI6InBoYW5pbmRyYXJlZGR5MzEwMjMxQGdtYWlsLmNvbSJ9LCJjb21wYW55TmFtZSI6Ikxha2lSZWRkeSBCYWxpIFJlZGR5IENvbGxlZ2Ugb2YgRW5naW5lZXJpbmciLCJjbGllbnRJRCI6ImMyMDhjNTgxLTNmMzAtNDdhOS05MWM4LWVhNmUwZmZkYmFhYiIsImNsaWVudFNlY3JldCI6IkFqY3laTXR5Zm5wenlXbHAiLCJvd25lck5hbWUiOiJLYXJyaSBQaGFuaW5kcmEgUmVkZHkiLCJvd25lckVtYWlsIjoicGhhbmluZHJhcmVkZHkzMTAyMzFAZ21haWwuY29tIiwicm9sbE5vIjoiMjI3NjFBNTQyMSJ9.dbH21FUJ6-UiTdM1K2WI3pcK4eICum-XHKLhkfK091Y",
        }
        try:
            response = requests.get(f"{base_url}{endpoints[number_type]}", headers=headers, timeout=0.5)
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            response.raise_for_status()
            return response.json().get('numbers', [])
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")  
            return []


    def update_window(self, new_numbers):
        self.window_prev_state = self.window_current_state.copy()
        unique_numbers = list(dict.fromkeys(new_numbers))
        self.window_current_state.extend(unique_numbers)
        self.window_current_state = self.window_current_state[-self.window_size:]

    def calculate_average(self):
        return round(sum(self.window_current_state) / len(self.window_current_state), 2) if self.window_current_state else 0

average = AverageCalculator(window_size=10)

@app.route('/numbers/<number_type>')
def get_average(number_type):
    start_time = time.time()
    
    if number_type not in ['p', 'f', 'e', 'r']:
        return jsonify({"error": "Invalid number type"}), 400
    
    new_nums = average.fetch_numbers(number_type)
    average.update_window(new_nums)
    
    response_data = {
        "avg": average.calculate_average(),
        "numbers": new_nums,
        "windowCurrState": average.window_current_state,
        "windowPrevState": average.window_prev_state       
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(port=9876)

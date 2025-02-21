from restai_functions import Restai
import os
from dotenv import load_dotenv
import threading
import time  # added for sleep and timing
import random  # new
import requests  # new
import re        # new
from collections import deque  # new import

load_dotenv()

restai = Restai(url=os.environ.get("RESTAI_URL"), api_key=os.environ.get("RESTAI_KEY"))

# Global variables for tracking response times and stopping all threads
stop_all = False
wait_times = deque(maxlen=5)  # fixed-size history for the last 5 responses
wait_times_lock = threading.Lock()

# Configurable delay between spawning new threads in seconds
WAIT_BETWEEN_THREADS = 2  # Adjust as needed

# New helper function to generate random phrases from a Project Gutenberg text
def get_random_phrases(num_phrases=100):
    url = "http://www.gutenberg.org/files/1342/1342-0.txt"  # Example text (Pride and Prejudice)
    response = requests.get(url)
    text = response.text
    # Simple split into sentences and filter by length (>20 and <=255 characters)
    sentences = re.split(r'\. ', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) <= 255]
    if len(sentences) < num_phrases:
        return sentences
    return random.sample(sentences, num_phrases)

# Replace static QUESTIONS list with 100 random phrases from the text
QUESTIONS = get_random_phrases(100)

def simulate_user(user_id):
    global stop_all
    while not stop_all:
        question = random.choice(QUESTIONS)
        start_time = time.time()
        _ = restai.pedro_inference(question)
        elapsed = time.time() - start_time
        # Record the response time in a thread-safe manner
        with wait_times_lock:
            wait_times.append(elapsed)
        print(f"User {user_id}: Waited for {elapsed:.2f} seconds")
        time.sleep(random.randint(1, 15))  # random think time

# Spawn threads until the average of the last 5 response times exceeds 60 seconds
threads = []
user_count = 0

while True:
    with wait_times_lock:
        if len(wait_times) == 5 and (sum(wait_times) / 5) > 60:
            stop_all = True
            break
    user_count += 1
    t = threading.Thread(target=simulate_user, args=(user_count,))
    t.start()
    threads.append(t)
    time.sleep(WAIT_BETWEEN_THREADS)

# Wait for all threads to finish
for t in threads:
    t.join()

print(f"Maximum number of users reached: {user_count}")

from restai_functions import Restai
import os
from dotenv import load_dotenv
import threading
import time  # added for sleep and timing
import random  # new
import requests  # new
import re        # new

load_dotenv()

restai = Restai(url=os.environ.get("RESTAI_URL"), api_key=os.environ.get("RESTAI_KEY"))

# Configurable number of simultaneous users
NUM_USERS = 50  # Modify this to change the number of threads
# New variable for delay between starting threads in seconds
WAIT_BETWEEN_THREADS = 2  # Adjust the delay as needed

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
    while True:
        # Randomize the question from the list of phrases
        question = random.choice(QUESTIONS)
        start_time = time.time()  # start timer before call
        _ = restai.pedro_inference(question)
        elapsed = time.time() - start_time  # calculate wait time
        print(f"User {user_id}: Waited for {elapsed:.2f} seconds")
        time.sleep(random.randint(1, 15))  # simulate user think time with random delay

threads = []
for i in range(NUM_USERS):
    t = threading.Thread(target=simulate_user, args=(i+1,))
    t.start()
    threads.append(t)
    time.sleep(WAIT_BETWEEN_THREADS)  # wait X seconds between starting threads

for t in threads:
    t.join()

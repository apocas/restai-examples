import sys
from restai_functions import Restai
import os
from dotenv import load_dotenv
import threading
import time  # added for sleep and timing
import random  # new
import requests  # new
import re        # new
from collections import deque  # new import
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

# Global variables for tracking response times and stopping all threads
stop_all = False
wait_times = deque(maxlen=5)  # fixed-size history for the last 5 responses
wait_times_lock = threading.Lock()

# New event to signal when any user gets a response
response_event = threading.Event()

# Configurable delay between launching new users after a response is received
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
        _ = client.chat.completions.create(
            model="shuyuej/Llama-3.3-70B-Instruct-GPTQ",
            messages=[
               {"role": "user", "content": question}
            ]
        )
        elapsed = time.time() - start_time
        # Record the response time in a thread-safe manner
        with wait_times_lock:
            wait_times.append(elapsed)
        #print(f"User {user_id}: Waited for {elapsed:.2f} seconds")
        response_event.set()  # signal that a response was received
        #time.sleep(random.randint(20, 40))  # random think time
        time.sleep(10)

# Spawn an initial user
threads = []
user_count = 1
t = threading.Thread(target=simulate_user, args=(user_count,))
t.start()
threads.append(t)

# Launch new users when a response is received from any existing user
while True:
    # Check average of last 5 responses
    with wait_times_lock:
        if len(wait_times) == 5:
            print(f"Average response time: {sum(wait_times) / 5:.2f} seconds")
        if len(wait_times) == 5 and (sum(wait_times) / 5) > 60:
            stop_all = True
            print(f"Maximum number of users reached: {user_count}")
            os._exit(1)
            
    response_event.wait()         # wait until a user gets a response
    response_event.clear()        # clear the event for next signal
    time.sleep(WAIT_BETWEEN_THREADS)
    user_count += 1
    t = threading.Thread(target=simulate_user, args=(user_count,))
    t.start()
    threads.append(t)
    print(f"Launched new user: {user_count}")  # new print message


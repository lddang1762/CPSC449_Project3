import requests
import threading
import time
import hug

lock = threading.Lock()
services = {}

def checkHealth():
    global services
    while True:
        for url in services:
            r = requests.get(f"{url}/health")
            print(f"Checking health for: {url}")
            # remove if not OK
            if r.status_code != 200:
                services.remove(url)
        # timeout for 60 seconds before next round of checks
        time.sleep(60)

@hug.post("/register")
def registerService(response, url: hug.types.text, name: hug.types.text):
    try:
        if name in services:
            if url in services[name]:
                response.status = hug.falcon.HTTP_409
                return {"error": "service already registered"}
            else:
                services[name].append(url)
                print(f"Registered: {url}")
        else:
            services[name] = url
            print(f"Registered: {url}")
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}
    return url

@hug.get("/registry")
def retrieveRegistry(response):
    return {"services": services}

def healthCheck():
    x = threading.Thread(target=checkHealth, args=(), daemon=True)
    x.start()

healthCheck()

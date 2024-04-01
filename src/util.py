def flatten(list):
    return [x for sublist in list for x in sublist]

def retry(func, max_retries: int):
    retries = 0
    response = None
    while response == None:
        try:
            response = func()
        except Exception as e:
            retry +=1
            if retry == MAX_TRACKER_RETRIES:
                return [503, "Service unavailable: No response"]
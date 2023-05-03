import os, time, threading, cv2, queue

frameWait = threading.BoundedSemaphore(10)
frameFill = threading.BoundedSemaphore(10)
semaphore1 = threading.BoundedSemaphore(10)
semaphore2 = threading.BoundedSemaphore(10)
que1 = queue.Queue()
que2 = queue.Queue()

class ExtractFrames(threading.Thread):            
    def __init__(self):
        threading.Thread.__init__(self)
        for _ in range(10):
            frameFill.acquire()
            frameWait.acquire()            
    def run(self):
        outputdirectroy = 'frames'
        clipname = 'clip.mp4'
        mutex = threading.Lock()                        
        count = 0
        vidcap = cv2.VideoCapture(clipname)
        if not os.path.exists(outputdirectroy):
            print(f"Output directory {outputdirectroy} didn't exist, creating")
            os.makedirs(outputdirectroy)
        success,frame = vidcap.read()
        print(f"Extracting frame {count} {success} ")
        while success:
          semaphore1.acquire()
          mutex.acquire()
          que1.put(frame)
          success,frame = vidcap.read()
          print(f"Extracting frame {count}")
          count += 1
          if que1.empty() and que2.empty():
            semaphore1.release()
            frameFill.release()
            print("Frames all extracted.")
            break
          mutex.release()
          frameFill.release()

class ConvertToGrayscale(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        count = 0
        while True:
            frameFill.acquire()                        
            semaphore2.acquire()
            print(f"Converting frame {count}")
            grayscaleframe = cv2.cvtColor(que1.get(), cv2.COLOR_BGR2GRAY)
            count += 1
            que2.put(grayscaleframe)
            if que1.empty() and que2.empty():
                print("Frames all converted")
                semaphore2.release()
                frameWait.release()
                semaphore1.release()
                break
            frameWait.release()
            semaphore1.release()
        for _ in range(9):
            frameWait.release()
        frameFill.release()

class DisplayFrames(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        count = 0
        while True:
            frameWait.acquire()
            displayframe = que2.get()
            print(f"Displaying frame {count}")
            time.sleep(.042)                                                
            cv2.imshow("Video", displayframe)
            if cv2.waitKey(42) and 0xFF == ord("q"):
                break
            count += 1
            semaphore2.release()
            if que1.empty() and que2.empty():
                break
        frameWait.release()
        print("All frames displayed")
        cv2.destroyAllWindows()
        exit()

extractframes = ExtractFrames()
convertframes = ConvertToGrayscale()
displayframes = DisplayFrames()
extractframes.start()
convertframes.start()
displayframes.start()

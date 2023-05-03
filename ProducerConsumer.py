import os, time, threading, cv2, queue

#Create semaphores for timing when to fill and when to wait with a buffer size of ten
frameWait = threading.BoundedSemaphore(10)
frameFill = threading.BoundedSemaphore(10)
#Create sephamore1 for extracting frames and sephamore2 for converting frames to greyscale
semaphore1 = threading.BoundedSemaphore(10)
semaphore2 = threading.BoundedSemaphore(10)
#Create queues to store files that are extracted in que1 and store files that converted in que2
que1 = queue.Queue()
que2 = queue.Queue()

#Reformated ExctractFrames.py into a class for easy use. 
class ExtractFrames(threading.Thread):            
    def __init__(self):
        threading.Thread.__init__(self)
        #Fill buffer for both filling and waiting for frames.
        for _ in range(10):
            frameFill.acquire()
            frameWait.acquire()            
    def run(self):
        outputdirectroy = 'frames'
        clipname = 'clip.mp4'
        #lock to access while extracting a frame
        mutex = threading.Lock()                        
        count = 0
        vidcap = cv2.VideoCapture(clipname)
        if not os.path.exists(outputdirectroy):
            print(f"Output directory {outputdirectroy} didn't exist, creating")
            os.makedirs(outputdirectroy)
        success,frame = vidcap.read()
        print(f"Extracting frame {count} {success} ")
        while success:
          #Begin processing and reserve processing time. 
          semaphore1.acquire()
          #lock the thread
          mutex.acquire()
          #store the frame in the queue
          que1.put(frame)
          #Move to next frame
          success,frame = vidcap.read()
          print(f"Extracting frame {count} {success}")
          count += 1
          #If all frames are extracted release sephamores and frameFill buffers
          if que1.empty() and que2.empty():
            semaphore1.release()
            frameFill.release()
            print("Frames all extracted.")
            break
          #before moving to next frame, release the lock on the thread.
          mutex.release()
          #let the other thread know that this thread finished rocessing
          frameFill.release()

#Reformated ConvertToGrayscale.py into a class for easy use.
class ConvertToGrayscale(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        count = 0
        while True:
            #get the buffer for framefill and sephamore 2
            frameFill.acquire()                        
            semaphore2.acquire()
            print(f"Converting frame {count}")
            grayscaleframe = cv2.cvtColor(que1.get(), cv2.COLOR_BGR2GRAY)
            count += 1
            #store the converted frame in the queue
            que2.put(grayscaleframe)
            #If there are no frames in either queue then all frames are converted
            if que1.empty() and que2.empty():
                print("Frames all converted")
                #Release all related buffers
                semaphore2.release()
                frameWait.release()
                semaphore1.release()
                break
            #for every frame, release the buffer for frameWait and semaphore1 allowing extraction of the next frame.
            frameWait.release()
            semaphore1.release()
        #Release buffers for wait and fill.
        for _ in range(9):
            frameWait.release()
        frameFill.release()

#Reformated DisplayFrames.py into a class for easy use. 
class DisplayFrames(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        count = 0
        while True:
            #Get the buffer for frameWait
            frameWait.acquire()
            #get the converted frame from que2
            displayframe = que2.get()
            print(f"Displaying frame {count}")
            #interval, can modify to make video "play" faster. 
            time.sleep(.042)                                                
            cv2.imshow("Video", displayframe)
            if cv2.waitKey(42) and 0xFF == ord("q"):
                break
            count += 1
            #Once frame is displated, release this buffer
            semaphore2.release()
            #If there are no frames in either queue then all frames have been displayed.
            if que1.empty() and que2.empty():
                break
        #Release the remaining buffer. Notify user and exit. 
        frameWait.release()
        print("All frames displayed")
        cv2.destroyAllWindows()
        exit()

#Create and start all necessary processes. Order of call is important. 
extractframes = ExtractFrames()
convertframes = ConvertToGrayscale()
displayframes = DisplayFrames()
extractframes.start()
convertframes.start()
displayframes.start()

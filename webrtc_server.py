import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from flask import Flask, request, jsonify, render_template
import cv2
import multiprocessing as mp
import numpy as np
import pyautogui
import pyaudio
import time

app = Flask(__name__)

# Screen recording
def capture_screen(queue):
    while True:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not queue.full():
            queue.put(frame)
        time.sleep(1/10)  # Capture at 10 frames per second

class VideoTransformTrack(VideoStreamTrack):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = await self.next_frame()
        return frame

    async def next_frame(self):
        while self.queue.empty():
            await asyncio.sleep(0.01)
        frame = self.queue.get()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

async def handle_offer(offer_sdp, screen_queue):
    pc = RTCPeerConnection()
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print(f"ICE connection state is {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")
        if track.kind == "video":
            screen_queue.put_nowait(track)
    
    offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return pc.localDescription.sdp

def offer():
    params = request.json
    offer_sdp = params['sdp']
    
    print("Received SDP Offer:\n", offer_sdp)  # Add logging for debugging

    screen_queue = mp.Queue(maxsize=10)

    # Start capture process
    screen_proc = mp.Process(target=capture_screen, args=(screen_queue,))
    screen_proc.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        answer = loop.run_until_complete(handle_offer(offer_sdp, screen_queue))
        print("Generated SDP Answer:\n", answer.sdp)  # Add logging for debugging
        return jsonify({'sdp': answer.sdp, 'type': answer.type})
    except Exception as e:
        print("Error handling offer:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view')
def view():
    return render_template('view.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
pcs = set()

@app.route('/')
def index():
    return render_template('view.html')

@app.route('/offer', methods=['POST'])
def offer():
    data = request.json
    print('Received offer SDP:', data.get('sdp', 'No SDP'))
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on('iceconnectionstatechange')
    async def on_iceconnectionstatechange():
        print('ICE connection state change:', pc.iceConnectionState)
        if pc.iceConnectionState == 'failed':
            await pc.close()
            pcs.discard(pc)

    @pc.on('track')
    def on_track(track):
        print('Track received:', track.kind)
        if track.kind == 'video':
            print('Track', track.kind, 'received')

    offer = RTCSessionDescription(sdp=data['sdp'], type='offer')

    async def handle_offer():
        await pc.setRemoteDescription(offer)
        print('Set remote description with offer')
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        print('Created answer SDP:', answer.sdp)
        return {'sdp': pc.localDescription.sdp}

    result = asyncio.run(handle_offer())
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

const axios = require('axios')
const assert = require('assert')
const W3CWebSocket = require('websocket').w3cwebsocket

const SERVER_URL = "http://127.0.0.1:8000"

describe('External data retrieval', async function() {
    const username = Math.random().toString(36).slice(-8);
    const password = Math.random().toString(36).slice(-8);
    response = await axios.post(SERVER_URL + '/user/data',
                                `username=${username}&password=${password}&email=tbray@textuality.com`)
        .catch(e => console.log(e.response. data))
    assert.equal(response.data['code'], 'OK', "Cannot signup user: ${response.data['message']}")
    user_id = response.data['data']['user_id']
    console.log(`Created user user_id=${user_id}.`)

    auth_token = (await axios.post(SERVER_URL + '/api-token-auth/', `username=${username}&password=${password}`)).data['token']
    auth_header = `JWT ${auth_token}`

//    response = await axios.get(SERVER_URL + `/user/data?user_id=${user_id}`, '', {
//        headers: { Authorization: auth_header },
//    })
//    console.log(response.data)

    const communicator = new W3CWebSocket('ws://127.0.0.1:8000/user-watch'/*, 'echo-protocol'*/);

    communicator.onopen = function() {
        if (communicator.readyState === communicator.OPEN) {
            communicator.send(`/auth ${auth_token}`);
        }
    }

    let stage = 0;

    communicator.onmessage = async function(e) {
        if (typeof e.data === 'string') {
            switch(stage) {
                case 0:
                    assert.equal(e.data, `ok: user_id=${user_id}`, "Can't authenticate WebSocket user.")
                    console.log(`Authenticated with WebSocket.`)

                    response = await axios.post(SERVER_URL + '/user/request-retrieve-data', `user_id=${user_id}`, {
                        headers: { Authorization: auth_header },
                    })
                    assert.equal(response.data.code, "PENDING", "Cannot start Clearbit user data retrieval.")
                    console.log(`Started Clearbit user data retrieval.`)
                    break;
                case 1:
                    assert.equal(e.data, "notice: socialuser data received",
                                 `Can't receive social data response: \"${e.data}\"`)
                    console.log(`Data received.`)
                    communicator.close()
                    response = await axios.get(SERVER_URL + `/user/data?user_id=${user_id}`, '', {
                        headers: { Authorization: auth_header },
                    })
                    console.log(response.data)
                    break;
            }
            ++stage;
        }
    }
})
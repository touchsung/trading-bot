import json
import requests


class Discord:
    def send_message_to_discord(self, url, message, file_path=None):
        try:
            headers = {
                "Content-Type": "application/json",
            }
            payload = {
                "content": message,
            }
            payload_json = json.dumps(payload)

            response = requests.post(url=url, headers=headers, data=payload_json)
            if file_path:
                response = requests.post(url=url, files={"file": open(file_path, "rb")})
            response.raise_for_status()

            if response.status_code == 200:
                return {"status": "OK"}
            else:
                return {"status": "Error", "response_code": response.status_code}

        except requests.exceptions.RequestException as e:
            return {"status": "Error", "message": str(e)}

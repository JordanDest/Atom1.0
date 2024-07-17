import re
import requests
import os
import time
from dotenv import load_dotenv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import contextlib
import io
from json import JSONDecodeError

load_dotenv()

# Suppress NLTK download output
with contextlib.redirect_stdout(io.StringIO()):
    nltk.download('punkt')
    nltk.download('stopwords')

api_key = os.getenv("GOVEE_API_KEY")
url_devices = "https://developer-api.govee.com/v1/devices"
url_state = "https://developer-api.govee.com/v1/devices/state"

# Header with API key
headers = {
    "Govee-API-Key": api_key
}

class Govee:
    devices = []
    device_dict = {}
    color_dict = {}
    action_words = ["turn", "set", "change", "increase", "decrease"]
    stop_words = set(stopwords.words('english')) - {"off", "on"}
    number_words = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
        "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100
    }

    def __init__(self, name, model, device_id):
        self.name = name
        self.model = model
        self.device_id = device_id
        self.api_key = api_key

    def __str__(self):
        return f"{self.name} (Model: {self.model}) (id: {self.device_id})"

    def get_device_state(self):
        url = f"https://developer-api.govee.com/v1/devices/state?device={self.device_id}&model={self.model}"
        headers = {
            "Govee-API-Key": self.api_key
        }

        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        except JSONDecodeError as json_err:
            print(f"JSON Decode Error: {json_err}")
        except Exception as err:
            print(f"Error: {err}")
        return None

    def check(self):
        data = self.get_device_state()
        if data:
            properties = data.get("data", {}).get("properties", [])
            for prop in properties:
                if prop.get("powerState") is not None:
                    power_state = prop["powerState"]
                    return power_state == 'on'
        return False

    def get_brightness(self):
        data = self.get_device_state()
        if data:
            properties = data.get("data", {}).get("properties", [])
            for prop in properties:
                if prop.get("brightness") is not None:
                    return prop["brightness"]
        return None

    def control(self, cmd_name, cmd_value):
        url = "https://developer-api.govee.com/v1/devices/control"
        headers = {
            "Content-Type": "application/json",
            "Govee-API-Key": self.api_key
        }
        cmd_name = cmd_name.lower()
        if cmd_name != "turn" and not self.check() and cmd_value != "off":
            self.control("turn", "on")

        body = {
            "device": self.device_id,
            "model": self.model,
            "cmd": {
                "name": cmd_name,
                "value": cmd_value
            }
        }
        response = requests.put(url, json=body, headers=headers)

        try:
            response.raise_for_status()
            data = response.json()
            #print(f"Control Response: {data}")
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        except JSONDecodeError as json_err:
            print(f"JSON Decode Error: {json_err}")
        except Exception as err:
            print(f"Error: {err}")

    @staticmethod
    def words_to_number(word):
        if isinstance(word, int):
            return word
        if word.isdigit():
            return int(word)
        word = word.lower()
        if word in Govee.number_words:
            return Govee.number_words[word]
        return None

    @staticmethod
    def find_device_by_partial_name(name_part):
        for device_name in Govee.device_dict:
            if name_part in device_name:
                return Govee.device_dict[device_name]
        return None

    @staticmethod
    def process_command(command_str):
        try:
            #print(f"Received command: '{command_str}'")  # Debug statement
            command_str = command_str.replace('.', '').strip().lower()
            words = word_tokenize(command_str)
            #print(f"Tokenized words: {words}")  # Debug statement
            filtered_words = [word for word in words if word not in Govee.stop_words]
            #print(f"Filtered words: {filtered_words}")  # Debug statement

            # Hardcoded handling for "turn on" and "turn off"
            if "turn on" in command_str or "turn off" in command_str:
                action = "turn"
                if "turn on" in command_str:
                    attribute = "on"
                    filtered_words = [word for word in filtered_words if word != "on"]
                elif "turn off" in command_str:
                    attribute = "off"
                    filtered_words = [word for word in filtered_words if word != "off"]
                filtered_words = [word for word in filtered_words if word != "turn"]
            else:
                if filtered_words[0] in Govee.action_words:
                    action = filtered_words[0]
                    filtered_words = filtered_words[1:]
                else:
                    action = "set"

                attribute = None
                device_name_parts = []
                remaining_words = []

                for word in filtered_words:
                    if word in Govee.color_dict or re.match(r'^\d+$', word) or word in Govee.number_words or word in ["on", "off"]:
                        attribute = word
                        break
                    if word in Govee.action_words or word == 'brightness':
                        remaining_words.append(word)
                    else:
                        device_name_parts.append(word)

                if not device_name_parts or not attribute:
                    raise ValueError("Invalid command format. Unable to parse device name or attribute.")

                device_name = " ".join(device_name_parts)
                #print(f"Device name parts: {device_name_parts}, Attribute: {attribute}")  # Debug statement
                device = Govee.find_device_by_partial_name(device_name)

                if not device:
                    raise ValueError(f"Device matching '{device_name}' not found.")

                if 'brightness' in remaining_words or action in ['increase', 'decrease']:
                    num_value = Govee.words_to_number(attribute)
                    if num_value is not None:
                        current_value = device.get_brightness()
                        if current_value is None:
                            raise ValueError(f"Unable to fetch current brightness for device '{device_name}'.")
                        if action == "increase":
                            attribute = min(current_value + num_value, 100)
                        elif action == "decrease":
                            attribute = max(current_value - num_value, 0)
                        action = "brightness"

                if attribute in ["on", "off"]:
                    device.control("turn", attribute)
                    print(f"Turned {device_name} {attribute}")
                    return

                attribute_number = Govee.words_to_number(attribute)
                if attribute_number is not None:
                    device.control("brightness", attribute_number)
                    print(f"Set {device_name} brightness to {attribute_number}")
                    return

                matching_color = Govee.color_dict.get(attribute)
                if matching_color:
                    device.control("turn", "on")
                    device.control("color", matching_color)
                    print(f"Changed {device_name} to color {attribute}")
                    return

                raise ValueError(f"Invalid attribute: {attribute}")
        except Exception as e:
            print(e)

# Initialize devices and dictionaries
devices = [
    Govee('Mirror', 'H6144', '91:C7:7C:A6:B0:5D:03:FA'),
    Govee('Second Left Restroom', 'H6003', '71:69:7c:a6:b0:a0:3f:cf'),
    Govee('Second Right Restroom', 'H6003', 'bd:45:7c:a6:b0:c0:f7:60'),
    Govee('Right Restroom', 'H6003', '60:2f:7c:a6:b0:a0:2c:57'),
    Govee('Left Restroom', 'H6003', 'ee:7d:7c:a6:b0:a6:a4:83'),
    Govee('Right Side Lamp', 'H6003', '53:3e:7c:a6:b0:17:84:96'),
    Govee('Left Side Lamp', 'H6003', '5b:f6:7c:a6:b0:1a:a2:4d'),
    Govee('Backlight', 'H6199', 'FB:2A:D1:33:36:32:3A:44'),
    Govee('Underglow', 'H614A', '39:4D:A4:C1:38:9A:79:96')
]
Govee.devices = devices
Govee.device_dict = {device.name.lower(): device for device in devices}

colors = [
    {"name": "red", "color": {"r": 255, "g": 0, "b": 0}},
    {"name": "green", "color": {"r": 0, "g": 255, "b": 0}},
    {"name": "blue", "color": {"r": 0, "g": 0, "b": 255}},
    {"name": "yellow", "color": {"r": 255, "g": 255, "b": 0}},
    {"name": "cyan", "color": {"r": 0, "g": 255, "b": 255}},
    {"name": "turquoise", "color": {"r": 0, "g": 255, "b": 255}},
    {"name": "magenta", "color": {"r": 255, "g": 0, "b": 255}},
    {"name": "purple", "color": {"r": 255, "g": 0, "b": 255}},
    {"name": "white", "color": {"r": 255, "g": 255, "b": 255}},
    {"name": "warm white", "color": {"r": 255, "g": 245, "b": 230}},
    {"name": "cool white", "color": {"r": 173, "g": 216, "b": 230}},
    {"name": "lavender", "color": {"r": 230, "g": 230, "b": 250}},
    {"name": "orange", "color": {"r": 255, "g": 165, "b": 0}},
    {"name": "pink", "color": {"r": 255, 'g': 182, 'b': 193}},
    {"name": "lime green", "color": {"r": 50, "g": 205, "b": 50}},
    {"name": "deep blue", "color": {"r": 0, "g": 0, "b": 139}},
    {"name": "gold", "color": {"r": 255, "g": 215, "b": 0}},
    {"name": "silver", "color": {"r": 192, "g": 192, "b": 192}},
    {"name": "bronze", "color": {"r": 205, "g": 127, "b": 50}},
    {"name": "teal", "color": {"r": 0, "g": 128, "b": 128}},
    {"name": "sky blue", "color": {"r": 135, "g": 206, "b": 235}},
    {"name": "slate gray", "color": {"r": 112, "g": 128, "b": 144}}
]
Govee.color_dict = {color["name"].lower(): color["color"] for color in colors}

def control(phrase):
    Govee.process_command(phrase)


# import re
# import requests
# import os
# import time
# from dotenv import load_dotenv
# import nltk
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# import contextlib
# import io
# from json import JSONDecodeError

# load_dotenv()

# # Suppress NLTK download output
# with contextlib.redirect_stdout(io.StringIO()):
#     nltk.download('punkt')
#     nltk.download('stopwords')

# api_key = os.getenv("GOVEE_API_KEY")
# url_devices = "https://developer-api.govee.com/v1/devices"
# url_state = "https://developer-api.govee.com/v1/devices/state"

# # Header with API key
# headers = {
#     "Govee-API-Key": api_key
# }

# def pull_devices():
#     try:
#         response = requests.get(url_devices, headers=headers)
#         response.raise_for_status()

#         data = response.json()
#         if response.status_code == 200:
#             devices = data["data"]["devices"]
#             for device in devices:
#                 device_name = device["deviceName"]
#                 model = device["model"]
#                 device_id = device["device"]
#                 print(f"{device_name} = '{device_name}', '{model}', '{device_id}'")
#         else:
#             print(f"Error: {data['message']} (Code: {data['code']})")

#     except requests.exceptions.HTTPError as errh:
#         print(f"HTTP Error: {errh}")
#     except requests.exceptions.ConnectionError as errc:
#         print(f"Error Connecting: {errc}")
#     except requests.exceptions.Timeout as errt:
#         print(f"Timeout Error: {errt}")
#     except requests.exceptions.RequestException as err:
#         print(f"Request Error: {err}")
#     except JSONDecodeError as json_err:
#         print(f"JSON Decode Error: {json_err}")

# class Govee:
#     def __init__(self, name, model, device_id):
#         self.name = name
#         self.model = model
#         self.device_id = device_id
#         self.api_key = api_key

#     def __str__(self):
#         return f"{self.name} (Model: {self.model}) (id: {self.device_id})"

#     def get_device_state(self):
#         url = f"https://developer-api.govee.com/v1/devices/state?device={self.device_id}&model={self.model}"
#         headers = {
#             "Govee-API-Key": self.api_key
#         }

#         response = requests.get(url, headers=headers)

#         try:
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.HTTPError as errh:
#             print(f"HTTP Error: {errh}")
#         except JSONDecodeError as json_err:
#             print(f"JSON Decode Error: {json_err}")
#         except Exception as err:
#             print(f"Error: {err}")
#         return None

#     def check(self):
#         data = self.get_device_state()
#         if data:
#             properties = data.get("data", {}).get("properties", [])
#             for prop in properties:
#                 if prop.get("powerState") is not None:
#                     power_state = prop["powerState"]
#                     return power_state == 'on'
#         return False

#     def get_brightness(self):
#         data = self.get_device_state()
#         if data:
#             properties = data.get("data", {}).get("properties", [])
#             for prop in properties:
#                 if prop.get("brightness") is not None:
#                     return prop["brightness"]
#         return None

#     def control(self, cmd_name, cmd_value):
#         url = "https://developer-api.govee.com/v1/devices/control"
#         headers = {
#             "Content-Type": "application/json",
#             "Govee-API-Key": self.api_key
#         }
#         cmd_name = cmd_name.lower()
#         if cmd_name != "turn" and not self.check() and cmd_value != "off":
#             self.control("turn", "on")

#         body = {
#             "device": self.device_id,
#             "model": self.model,
#             "cmd": {
#                 "name": cmd_name,
#                 "value": cmd_value
#             }
#         }
#         response = requests.put(url, json=body, headers=headers)

#         try:
#             response.raise_for_status()
#             data = response.json()
#             print(f"Control Response: {data}")
#         except requests.exceptions.HTTPError as errh:
#             print(f"HTTP Error: {errh}")
#         except JSONDecodeError as json_err:
#             print(f"JSON Decode Error: {json_err}")
#         except Exception as err:
#             print(f"Error: {err}")

# # Create instances of Govee for each device
# devices = [
#     Govee('Mirror', 'H6144', '91:C7:7C:A6:B0:5D:03:FA'),
#     Govee('Second Left Restroom', 'H6003', '71:69:7c:a6:b0:a0:3f:cf'),
#     Govee('Second Right Restroom', 'H6003', 'bd:45:7c:a6:b0:c0:f7:60'),
#     Govee('Right Restroom', 'H6003', '60:2f:7c:a6:b0:a0:2c:57'),
#     Govee('Left Restroom', 'H6003', 'ee:7d:7c:a6:b0:a6:a4:83'),
#     Govee('Right Side Lamp', 'H6003', '53:3e:7c:a6:b0:17:84:96'),
#     Govee('Left Side Lamp', 'H6003', '5b:f6:7c:a6:b0:1a:a2:4d'),
#     Govee('Backlight', 'H6199', 'FB:2A:D1:33:36:32:3A:44'),
#     Govee('Underglow', 'H614A', '39:4D:A4:C1:38:9A:79:96')
# ]

# # Colors setup
# colors = [
#     {"name": "red", "color": {"r": 255, "g": 0, "b": 0}},
#     {"name": "green", "color": {"r": 0, "g": 255, "b": 0}},
#     {"name": "blue", "color": {"r": 0, "g": 0, "b": 255}},
#     {"name": "yellow", "color": {"r": 255, "g": 255, "b": 0}},
#     {"name": "cyan", "color": {"r": 0, "g": 255, "b": 255}},
#     {"name": "turquoise", "color": {"r": 0, "g": 255, "b": 255}},
#     {"name": "magenta", "color": {"r": 255, "g": 0, "b": 255}},
#     {"name": "purple", "color": {"r": 255, "g": 0, "b": 255}},
#     {"name": "white", "color": {"r": 255, "g": 255, "b": 255}},
#     {"name": "warm white", "color": {"r": 255, "g": 245, "b": 230}},
#     {"name": "cool white", "color": {"r": 173, "g": 216, "b": 230}},
#     {"name": "lavender", "color": {"r": 230, "g": 230, "b": 250}},
#     {"name": "orange", "color": {"r": 255, "g": 165, "b": 0}},
#     {"name": "pink", "color": {"r": 255, 'g': 182, 'b': 193}},
#     {"name": "lime green", "color": {"r": 50, "g": 205, "b": 50}},
#     {"name": "deep blue", "color": {"r": 0, "g": 0, "b": 139}},
#     {"name": "gold", "color": {"r": 255, "g": 215, "b": 0}},
#     {"name": "silver", "color": {"r": 192, "g": 192, "b": 192}},
#     {"name": "bronze", "color": {"r": 205, "g": 127, "b": 50}},
#     {"name": "teal", "color": {"r": 0, "g": 128, "b": 128}},
#     {"name": "sky blue", "color": {"r": 135, "g": 206, "b": 235}},
#     {"name": "slate gray", "color": {"r": 112, "g": 128, "b": 144}}
# ]

# device_dict = {device.name.lower(): device for device in devices}
# color_dict = {color["name"].lower(): color["color"] for color in colors}

# action_words = ["turn", "set", "change", "increase", "decrease"]
# stop_words = set(stopwords.words('english')) - {"off", "on"}

# number_words = {
#     "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
#     "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
#     "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
#     "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
#     "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
#     "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100
# }

# def words_to_number(word):
#     if isinstance(word, int):
#         return word
#     if word.isdigit():
#         return int(word)
#     word = word.lower()
#     if word in number_words:
#         return number_words[word]
#     return None

# def find_device_by_partial_name(name_part):
#     for device_name in device_dict:
#         if name_part in device_name:
#             return device_dict[device_name]
#     return None

# def control(command_str):
#     try:
#         print(f"Received command: '{command_str}'")  # Debug statement
#         command_str = command_str.replace('.', '').strip().lower()
#         words = word_tokenize(command_str)
#         print(f"Tokenized words: {words}")  # Debug statement
#         filtered_words = [word for word in words if word not in stop_words]
#         print(f"Filtered words: {filtered_words}")  # Debug statement

#         if len(filtered_words) < 2:
#             raise ValueError("Invalid command format. Unable to parse device name or attribute.")

#         if filtered_words[0] in action_words:
#             action = filtered_words[0]
#             filtered_words = filtered_words[1:]
#         else:
#             action = "set"

#         device_name_parts = []
#         attribute = None
#         remaining_words = []

#         for word in filtered_words:
#             if word in color_dict or re.match(r'^\d+$', word) or word in number_words or word in ["on", "off"]:
#                 attribute = word
#                 break
#             if word in action_words or word == 'brightness':
#                 remaining_words.append(word)
#             else:
#                 device_name_parts.append(word)

#         # Handle special cases for 'turn on' and 'turn off'
#         if len(filtered_words) >= 3 and filtered_words[0] == "turn" and filtered_words[1] in ["on", "off"]:
#             action = "turn"
#             attribute = filtered_words[1]
#             device_name_parts = filtered_words[2:]

#         if not device_name_parts or not attribute:
#             raise ValueError("Invalid command format. Unable to parse device name or attribute.")

#         device_name = " ".join(device_name_parts)
#         print(f"Device name parts: {device_name_parts}, Attribute: {attribute}")  # Debug statement
#         device = find_device_by_partial_name(device_name)

#         if not device:
#             raise ValueError(f"Device matching '{device_name}' not found.")

#         if 'brightness' in remaining_words or action in ['increase', 'decrease']:
#             num_value = words_to_number(attribute)
#             if num_value is not None:
#                 current_value = device.get_brightness()
#                 if current_value is None:
#                     raise ValueError(f"Unable to fetch current brightness for device '{device_name}'.")
#                 if action == "increase":
#                     attribute = min(current_value + num_value, 100)
#                 elif action == "decrease":
#                     attribute = max(current_value - num_value, 0)
#                 action = "brightness"

#         if attribute in ["on", "off"]:
#             device.control("turn", attribute)
#             print(f"Turned {device_name} {attribute}")
#             return

#         attribute_number = words_to_number(attribute)
#         if attribute_number is not None:
#             device.control("brightness", attribute_number)
#             print(f"Set {device_name} brightness to {attribute_number}")
#             return

#         matching_color = color_dict.get(attribute)
#         if matching_color:
#             device.control("turn", "on")
#             device.control("color", matching_color)
#             print(f"Changed {device_name} to color {attribute}")
#             return

#         raise ValueError(f"Invalid attribute: {attribute}")
#     except Exception as e:
#         print(e)

# # Example usage:
# control("right side lamp to blue")
# time.sleep(1)
# control("turn the right side lamp off")
# time.sleep(1)
# control("change the right side lamp to green")
# time.sleep(1)
# control("turn off right side lamp")
# time.sleep(1)
# control("set right side lamp to 50")
# time.sleep(1)
# control("increase brightness of right side lamp by fifty")
# time.sleep(1)
# control("decrease brightness of right side lamp by seventy")
# time.sleep(1)



# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# api_key = os.getenv("GOVEE_API_KEY")
# url_devices = "https://developer-api.govee.com/v1/devices"
# url_state = "https://developer-api.govee.com/v1/devices/state"

# # Header with API key
# headers = {
#     "Govee-API-Key": api_key
# }

# def pull_devices():
#     try:
#         # Make a GET request to fetch devices
#         response = requests.get(url_devices, headers=headers)
#         response.raise_for_status()  # Raise an HTTPError for bad responses

#         data = response.json()

#         # Check if the request was successful (status code 200)
#         if response.status_code == 200:
#             devices = data["data"]["devices"]
#             print(devices)
#             for device in devices:
#                 device_name = device["deviceName"]
#                 model = device["model"]
#                 device_id = device["device_id"]  # Corrected this line
#                 print(f"{device_name} = '{device_name}', '{model}', '{device_id}'")
#         else:
#             print(f"Error: {data['message']} (Code: {data['code']}")

#     except requests.exceptions.HTTPError as errh:
#         print(f"HTTP Error: {errh}")
#     except requests.exceptions.ConnectionError as errc:
#         print(f"Error Connecting: {errc}")
#     except requests.exceptions.Timeout as errt:
#         print(f"Timeout Error: {errt}")
#     except requests.exceptions.RequestException as err:
#         print(f"Request Error: {err}")
#     except requests.exceptions.JSONDecodeError as json_err:
#         print(f"JSON Decode Error: {json_err}")

# class Govee:
#     def __init__(self, name, model, device_id):
#         self.name = name
#         self.model = model
#         self.device_id = device_id
#         self.api_key = api_key

#     def __str__(self):
#         return f"{self.name} (Model: {self.model}) (id: {self.device_id})"

#     def check(self):
#         url = f"https://developer-api.govee.com/v1/devices/state?device={self.device_id}&model={self.model}"
#         headers = {
#             "Govee-API-Key": self.api_key
#         }

#         response = requests.get(url, headers=headers)

#         try:
#             response.raise_for_status()
#             data = response.json()
#             properties = data.get("data", {}).get("properties", [])
#             for prop in properties:
#                 if "powerState" in prop:
#                     power_state = prop["powerState"]
#                     #print(f"{self.name} is {'on' if power_state == 'on' else 'off'}")
#                     if power_state == 'on':
#                         return True
#                     else:
#                         return False

#         except requests.exceptions.HTTPError as errh:
#             print(f"HTTP Error: {errh}")
#         except requests.exceptions.JSONDecodeError as json_err:
#             print(f"JSON Decode Error: {json_err}")
#         except Exception as err:
#             print(f"Error: {err}")

#     def control(self, cmd_name, cmd_value):
#         url = "https://developer-api.govee.com/v1/devices/control"
#         headers = {
#             "Content-Type": "application/json",
#             "Govee-API-Key": self.api_key
#         }

#         body = {
#             "device": self.device_id,
#             "model": self.model,
#             "cmd": {
#                 "name": cmd_name,
#                 "value": cmd_value
#             }
#         }

#         response = requests.put(url, json=body, headers=headers)

#         try:
#             response.raise_for_status()
#             data = response.json()
#             print(f"Control Response: {data}")
#         except requests.exceptions.HTTPError as errh:
#             print(f"HTTP Error: {errh}")
#         except requests.exceptions.JSONDecodeError as json_err:
#             print(f"JSON Decode Error: {json_err}")
#         except Exception as err:
#             print(f"Error: {err}")

#     def control(self, cmd_name, cmd_value):
#         url = "https://developer-api.govee.com/v1/devices/control"
#         headers = {
#             "Content-Type": "application/json",
#             "Govee-API-Key": self.api_key
#         }
#         cmd_name = cmd_name.lower()
#         #cmd_value = cmd_value.lower().strip().replace(" ","_")
#         #Before controlling status, turn on device
#         on = self.check()
#         if on is False and cmd_value != "off":
#             body = {"device": self.device_id, "model": self.model, "cmd": {"name": cmd_name, "value": cmd_value}}
#             response = requests.put(url, json=body, headers=headers)
#         body = {
#             "device": self.device_id,
#             "model": self.model,
#             "cmd": {
#                 "name": cmd_name,
#                 "value": cmd_value
#                    }
#                }
#         response = requests.put(url, json=body, headers=headers)

#         try:
#             response.raise_for_status()
#             data = response.json()
#             #print(f"Control Response: {data}")
#         except requests.exceptions.HTTPError as errh:
#             print(f"HTTP Error: {errh}")
#         except requests.exceptions.JSONDecodeError as json_err:
#             print(f"JSON Decode Error: {json_err}")
#         except Exception as err:
#             print(f"Error: {err}")
    
# # Create instances of Govee for each device
# mirror = Govee('Mirror', 'H6144', '91:C7:7C:A6:B0:5D:03:FA')
# Second_Left_Restroom = Govee('Second Left Restroom', 'H6003', '71:69:7c:a6:b0:a0:3f:cf')
# second_right_restroom = Govee('Second Right Restroom', 'H6003', 'bd:45:7c:a6:b0:c0:f7:60')
# right_restroom = Govee('Right Restroom', 'H6003', '60:2f:7c:a6:b0:a0:2c:57')
# left_restroom = Govee('Left Restroom', 'H6003', 'ee:7d:7c:a6:b0:a6:a4:83')
# right_side_lamp = Govee('Right Side Lamp', 'H6003', '53:3e:7c:a6:b0:17:84:96')
# left_side_lamp = Govee('Left Side Lamp', 'H6003', '5b:f6:7c:a6:b0:1a:a2:4d')
# backlight = Govee('Backlight', 'H6199', 'FB:2A:D1:33:36:32:3A:44')
# underglow = Govee('Underglow', 'H614A', '39:4D:A4:C1:38:9A:79:96')

# #Colors
# red= {"r": 255, "g": 0, "b": 0}
# green= {"r": 0, "g": 255, "b": 0}
# blue= {"r": 0, "g": 0, "b": 255}
# yellow= {"r": 255, "g": 255, "b": 0}
# cyan = {"r": 0, "g": 255, "b": 255}
# turquoise= {"r": 0, "g": 255, "b": 255}
# magenta = {"r": 255, "g": 0, "b": 255}
# purple= {"r": 255, "g": 0, "b": 255}
# white= {"r": 255, "g": 255, "b": 255}
# warm_white= {"r": 255, "g": 245, "b": 230}
# cool_white= {"r": 173, "g": 216, "b": 230}
# lavender= {"r": 230, "g": 230, "b": 250}
# orange= {"r": 255, "g": 165, "b": 0}
# pink= {"r": 255, "g": 182, "b": 193}
# lime_green= {"r": 50, "g": 205, "b": 50}
# deep_blue= {"r": 0, "g": 0, "b": 139}
# gold= {"r": 255, "g": 215, "b": 0}
# silver= {"r": 192, "g": 192, "b": 192}
# bronze= {"r": 205, "g": 127, "b": 50}
# teal= {"r": 0, "g": 128, "b": 128}
# sky_blue = {"r": 135, "g": 206, "b": 235}
# slate_gray = {"r": 112, "g": 128, "b": 144}


# ##test cases
# # right_side_lamp.control("turn", "on")
# # right_side_lamp.control("color",slate_gray)
# # right_side_lamp.control("brightness", 100)
# # right_side_lamp.control("turn","off")
# # right_side_lamp.control("color",green)
# # def main():
# #    #right_side_lamp.control("turn", 'on') 
# # main()
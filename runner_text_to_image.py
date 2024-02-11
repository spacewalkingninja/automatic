import os, sys
import time, re, json, shutil
import requests, subprocess
import yaml
from yaml.loader import SafeLoader
import io, base64
from PIL import Image, PngImagePlugin
import argparse
os.environ['CURL_CA_BUNDLE'] = ''

from requests.adapters import HTTPAdapter, Retry

s = requests.Session()

retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

s.mount('https://', HTTPAdapter(max_retries=retries))
parser = argparse.ArgumentParser()
parser.add_argument("-mr", "--model_req", 
                    help="DeSOTA Request as yaml file path",
                    type=str)
parser.add_argument("-mru", "--model_res_url",
                    help="DeSOTA API Result URL. Recognize path instead of url for desota tests", # check how is atribuited the test_mode variable in main function
                    type=str)

DEBUG = False

# DeSOTA Funcs [START]
#   > Import DeSOTA Scripts
from desota import detools
#   > Grab DeSOTA Paths
USER_SYS = detools.get_platform()
APP_PATH = os.path.dirname(os.path.realpath(__file__))
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(APP_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(APP_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
# DeSOTA Funcs [END]


def main(args):
    '''
    return codes:
    0 = SUCESS
    1 = INPUT ERROR
    2 = OUTPUT ERROR
    3 = API RESPONSE ERROR
    9 = REINSTALL MODEL (critical fail)
    '''
    # Time when grabed
    _report_start_time = time.time()
    start_time = int(_report_start_time)

    #---INPUT---# TODO (PRO ARGS)
    #---INPUT---#

    # DeSOTA Model Request
    model_request_dict = detools.get_model_req(args.model_req)

    # API Response URL
    result_id = args.model_res_url
    
    # TARGET File Path
    dir_path = os.path.dirname(os.path.realpath(__file__))
    out_filepath = os.path.join(dir_path, f"txt-to-img-{start_time}.png")
    out_urls = detools.get_url_from_str(result_id)
    if len(out_urls)==0:
        test_mode = True
        report_path = result_id
    else:
        test_mode = False
        send_task_url = out_urls[0]

    # Get html file
    req_text = detools.get_request_text(model_request_dict)

    if isinstance(req_text, list):
        req_text = ' '.join(req_text)

    url = "http://127.0.0.1:7860"
    img_res = 0
    if req_text:
        default_config = {
        #"prompt": str(args.text_prompt),
        "negative_prompt": "violence, pornography",
        "width": 512,
        "height": 512,
        "seed": -1,
        "subseed": -1,
        "subseed_strength": 0,
        "batch_size": 1,
        "n_iter": 1,
        "steps": 20,
        "cfg_scale": 7,
        "restore_faces": True,
        "sampler_index": "14",#DPM++ 3M SDE
        "enable_hr": False,
        "denoising_strength": 0.5,
        "hr_scale": 2,
        "hr_upscale": "Latent (bicubic antialiased)",
        }
        #print(model_request_dict)
        targs = default_config
        if 'model_args' in model_request_dict['input_args']:
            targs = model_request_dict['input_args']['model_args']
        if 'prompt' in targs:
            if targs['prompt'] == '$initial-prompt$':
                targs['prompt'] = req_text
        else:
            targs['prompt'] = req_text

        if 'sampler_index' in targs:
            temp_index = targs['sampler_index']
            samplers=["UniPC","Euler","Euler a","LMS","Heun","DPM2","DPM2 a","DPM++ 2S a","DPM++ 2M","DPM++ SDE","DPM++ SDE Heun","DPM fast","DPM adaptive","LMS","DPM++ 3M SDE","DDIM","PLMS"]
            targs['sampler_index'] = samplers[int(temp_index)]


        # Merge the loaded configuration with the default configuration
        #payload = targs
        payload = {**default_config, **targs}
        #print (payload)
        json_data = json.dumps(payload)

        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload, timeout=1280)

        r = response.json()
        #print(r)
        for i in r['images']:
            print("found img")
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

            png_payload = {
                "image": "data:image/png;base64," + i
            }
            response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", response2.json().get("info"))
            image.save(out_filepath, pnginfo=pnginfo)
            img_res = 1
        

    if not img_res:
        print(f"[ ERROR ] -> DeSOTA SD.Next API Output ERROR: No results can be parsed for this request")
        exit(2)
        
    #print(f"[ INFO ] -> Response:\n{json.dumps(r, indent=2)}")
    
    if test_mode:
        if not report_path.endswith(".json"):
            report_path += ".json"
        with open(report_path, "w") as rw:
            json.dump(
                {
                    "Model Result Path": out_filepath,
                    "Processing Time": time.time() - _report_start_time
                },
                rw,
                indent=2
            )
        detools.user_chown(report_path)
        detools.user_chown(out_filepath)
        print(f"Path to report:\n\t{report_path}")
    else:
        files = []
        with open(out_filepath, 'rb') as fr:
            files.append(('upload[]', fr))
            # DeSOTA API Response Post
            send_task = s.post(url = send_task_url, files=files)
            print(f"[ INFO ] -> DeSOTA API Upload Res:\n{json.dumps(send_task.json(), indent=2)}")
        # Delete temporary file
        os.remove(out_filepath)

        if send_task.status_code != 200:
            print(f"[ ERROR ] -> DeSOTA SD.Next API Post Failed (Info):\nfiles: {files}\nResponse Code: {send_task.status_code}")
            exit(3)
    
    print("TASK OK!")
    exit(0)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
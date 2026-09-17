import urllib.request
import json

with open('fizi_logo.png', 'rb') as f:
    img_data = f.read()

boundary = '----CloudinaryBoundary12345'
part1 = (
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="upload_preset"\r\n\r\n'
    'fizi_app_preset\r\n'
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="file"; filename="fizi_logo.png"\r\n'
    'Content-Type: image/png\r\n\r\n'
).encode('utf-8')

part2 = f'\r\n--{boundary}--\r\n'.encode('utf-8')
body = part1 + img_data + part2

req = urllib.request.Request(
    'https://api.cloudinary.com/v1_1/ddtslpjdf/image/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print('CLOUDINARY_URL:', res.get('secure_url'))
except Exception as e:
    print('ERROR:', e)

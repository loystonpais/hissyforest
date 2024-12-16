import json
import subprocess
import os
import traceback
import sys
import io
import base64
import unittest



def lambda_handler(event, context):
    stdout = io.StringIO()
    stderr = io.StringIO()
    sys.stdout = stdout
    sys.stderr = stderr

    out = "/tmp/out/"

    try:

        _body = event["body"]

        body: dict

        if isinstance(_body, str):
            try:
                body: dict = json.loads(_body)
            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps(dict(
                        server_error="REQUEST_NOT_JSON",
                    ))
                }
        elif isinstance(_body, dict):
            body: dict = _body

        else:
            return {
                'statusCode': 400,
                'body': json.dumps(dict(
                        server_error="REQUEST_INVALID",
                    ))
            }

        # Check if "code" key is in the event body
        if "code" not in body:
            return {
                'statusCode': 400,
                'body': json.dumps(dict(
                        server_error="RESPONSE_NO_CODE",
                    ))
            }


        os.system(f"mkdir -p {out}")


        code: str = body["code"]

        error = None

        try:
            exec(code)
        except Exception as e:
            error: str = traceback.format_exc()


        base64_files = []

        for file in os.listdir(out):
            with open(f"{out}{file}", "rb") as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                base64_files.append(dict(
                    name=file,
                    data=base64_data
                ))

        return {
            'statusCode': 200,
            'body': json.dumps(dict(
                error=error,
                stdout=stdout.getvalue(),
                stderr=stderr.getvalue(),
                files=base64_files
            ))
        }

    except Exception as e:
        # Server exceptions
        return {
            'statusCode': 500,
            'body': json.dumps(f"Server Error: {str(e)}")
        }
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        os.system(f"rm -rf {out}")


class Test(unittest.TestCase):
    def test_lambda_handler(self):
        event = {
            "body": {
                "code": "print('Hello, World!')"
            }
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("Hello, World!", response['body'])

    def test_lambda_handler_error(self):
        event = {
            "body": {
                "code": "raise Exception('Test error')"
            }
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("Test error", response['body'])

    def test_lambda_handler_invalid_request(self):
        event = {
            "body": "invalid request"
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("REQUEST_NOT_JSON", response['body'])

    def test_lambda_handler_no_code(self):
        event = {
            "body": {}
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("RESPONSE_NO_CODE", response['body'])

    def test_str_body(self):
        event = {
            "body": '{"code": "print(\'Hello, World!\')"}'
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("Hello, World!", response['body'])

    def test_file(self):
        event = {
            "body": {
                "code": "open('/tmp/out/foo.txt', 'w').write('Hi').close()"
            }
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("foo.txt", json.loads(response['body'])['files'][0]['name'])

    def test_multiple_files(self):
        event = {
            "body": {
                "code": "open('/tmp/out/foo.txt', 'w').write('Hi'); open('/tmp/out/bar.txt', 'w').write('Hi')"
            }
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("foo.txt", json.loads(response['body'])['files'][0]['name'])
        self.assertIn("bar.txt", json.loads(response['body'])['files'][1]['name'])

    def test_pillow_library(self):
        event = {
            "body": {
                "code": "from PIL import Image; Image.new('RGB', (60, 30), color = 'red').save('/tmp/out/foo.png')"
            }
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn("foo.png", json.loads(response['body'])['files'][0]['name'])


if __name__ == "__main__":
    unittest.main()
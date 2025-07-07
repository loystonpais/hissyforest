import json
import subprocess
import os
import tempfile
import base64
import glob
import unittest

def lambda_handler(event, context):
    try:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Invalid JSON in body: {str(e)}",
                    "stdout": "",
                    "stderr": "",
                    "exit_code": -1,
                    "files": {}
                })
            }

        code = body.get("code")
        if not code:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "No 'code' field provided",
                    "stdout": "",
                    "stderr": "",
                    "exit_code": -1,
                    "files": {}
                })
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            try:
                with open(script_path, "w") as f:
                    f.write(code)
            except Exception as e:
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": f"Failed to write script file: {str(e)}",
                        "stdout": "",
                        "stderr": "",
                        "exit_code": -1,
                        "files": {}
                    })
                }

            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = f"{env.get('PWD', '')}:{env.get('PYTHONPATH', '')}"
                result = subprocess.run(
                    ["python3", script_path],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    timeout=5,
                    env=env,
                )
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": "Script execution timed out",
                        "stdout": "",
                        "stderr": "",
                        "exit_code": -1,
                        "files": {}
                    })
                }
            except subprocess.SubprocessError as e:
                return {
                    "statusCode": 500,
                    "body": json.dumps({
                        "error": f"Script execution failed: {str(e)}",
                        "stdout": "",
                        "stderr": "",
                        "exit_code": -1,
                        "files": {}
                    })
                }

            files = {}
            for file_path in glob.glob(f"{temp_dir}/**/*", recursive=True):
                if os.path.isfile(file_path) and file_path != script_path:
                    try:
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                            file_base64 = base64.b64encode(file_content).decode("utf-8")
                            relative_path = os.path.relpath(file_path, temp_dir)
                            files[relative_path] = file_base64
                    except Exception as e:
                        stderr += f"\nError reading file {file_path}: {str(e)}"

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "files": files
                })
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Unexpected error: {str(e)}",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "files": {}
            })
        }

class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        self.context = None

    def test_successful_execution(self):
        event = {"body": json.dumps({"code": "print('Hello, World!')"})}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["stdout"], "Hello, World!\n")
        self.assertEqual(body["stderr"], "")
        self.assertEqual(body["exit_code"], 0)
        self.assertEqual(body["files"], {})

    def test_module_import(self):
        event = {"body": json.dumps({"code": "import PIL"})}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["stdout"], "")
        self.assertEqual(body["stderr"], "")
        self.assertEqual(body["exit_code"], 0)
        self.assertEqual(body["files"], {})

    def test_missing_code(self):
        event = {"body": json.dumps({})}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body["error"], "No 'code' field provided")
        self.assertEqual(body["stdout"], "")
        self.assertEqual(body["stderr"], "")
        self.assertEqual(body["exit_code"], -1)
        self.assertEqual(body["files"], {})

    def test_invalid_code(self):
        event = {"body": json.dumps({"code": "print('Hello'  # Missing closing parenthesis"})}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["stdout"], "")
        self.assertTrue("SyntaxError" in body["stderr"])
        self.assertEqual(body["exit_code"], 1)
        self.assertEqual(body["files"], {})

    def test_file_creation(self):
        event = {"body": json.dumps({"code": "with open('output.txt', 'w') as f: f.write('Test content'); print('File created')"})}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["stdout"], "File created\n")
        self.assertEqual(body["stderr"], "")
        self.assertEqual(body["exit_code"], 0)
        self.assertIn("output.txt", body["files"])
        self.assertEqual(body["files"]["output.txt"], base64.b64encode(b"Test content").decode("utf-8"))

    def test_invalid_json_body(self):
        event = {"body": "invalid json"}
        response = lambda_handler(event, self.context)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertTrue("Invalid JSON in body" in body["error"])
        self.assertEqual(body["stdout"], "")
        self.assertEqual(body["stderr"], "")
        self.assertEqual(body["exit_code"], -1)
        self.assertEqual(body["files"], {})

if __name__ == "__main__":
    unittest.main()

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if body is not None:
            self.wfile.write(json.dumps(body).encode('utf-8'))
        else:
            self.wfile.write(b'{}')

    def _pars_body(self):
        if 'Content-Length' not in self.headers:
            return None
        content_length = int(self.headers['Content-Length'])
        if content_length == 0:
            return None
        try:
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        except json.JSONDecodeError:
            return None

    def _validate_user_post(self, data):
        required_keys = {"id", "username", "firstName", "lastName", "email", "password"}
        if not isinstance(data, dict): return False
        if set(data.keys()) != required_keys: return False
        if not isinstance(data["id"], int): return False
        for k in ["username", "firstName", "lastName", "email", "password"]:
            if not isinstance(data[k], str): return False
        return True

    def _validate_user_put(self, data):
        required_keys = {"username", "firstName", "lastName", "email", "password"}
        if not isinstance(data, dict): return False
        if set(data.keys()) != required_keys: return False
        for k in required_keys:
            if not isinstance(data[k], str): return False
        return True

    def do_GET(self):
        global USERS_LIST
        parsed_path = urlparse(self.path).path

        if parsed_path == '/reset':
            USERS_LIST = [{
                "id": 1,
                "username": "theUser",
                "firstName": "John",
                "lastName": "James",
                "email": "john@email.com",
                "password": "12345",
            }]
            self._set_response(200, None)

        elif parsed_path == '/users':
            self._set_response(200, USERS_LIST)

        elif parsed_path.startswith('/user/'):
            username = parsed_path.split('/')[-1]
            user = next((u for u in USERS_LIST if u['username'] == username), None)
            if user:
                self._set_response(200, user)
            else:
                self._set_response(400, {"error": "User not found"})
        else:
            self._set_response(404, {"error": "Not Found"})

    def do_POST(self):
        global USERS_LIST
        parsed_path = urlparse(self.path).path
        body = self._pars_body()

        if not body:
            return self._set_response(400, {})

        if parsed_path == '/user':
            if not self._validate_user_post(body):
                return self._set_response(400, {})
            if any(u['id'] == body['id'] for u in USERS_LIST):
                return self._set_response(400, {})

            USERS_LIST.append(body)
            self._set_response(201, body)

        elif parsed_path == '/user/createWithList':
            if not isinstance(body, list):
                return self._set_response(400, {})

            for u in body:
                if not self._validate_user_post(u):
                    return self._set_response(400, {})

            incoming_ids = [u['id'] for u in body]
            existing_ids = [u['id'] for u in USERS_LIST]

            if len(incoming_ids) != len(set(incoming_ids)) or any(i in existing_ids for i in incoming_ids):
                return self._set_response(400, {})

            USERS_LIST.extend(body)
            self._set_response(201, body)
        else:
            self._set_response(404)

    def do_PUT(self):
        global USERS_LIST
        parsed_path = urlparse(self.path).path
        body = self._pars_body()

        if parsed_path.startswith('/user/'):
            try:
                user_id = int(parsed_path.split('/')[-1])
            except ValueError:
                return self._set_response(400, {"error": "not valid request data"})

            if not body or not self._validate_user_put(body):
                return self._set_response(400, {"error": "not valid request data"})

            for i, u in enumerate(USERS_LIST):
                if u['id'] == user_id:
                    updated_user = {**body, "id": user_id}
                    USERS_LIST[i] = updated_user
                    return self._set_response(200, updated_user)

            return self._set_response(404, {"error": "User not found"})
        else:
            self._set_response(404)

    def do_DELETE(self):
        global USERS_LIST
        parsed_path = urlparse(self.path).path

        if parsed_path.startswith('/user/'):
            try:
                user_id = int(parsed_path.split('/')[-1])
            except ValueError:
                return self._set_response(404, {"error": "User not found"})

            for i, u in enumerate(USERS_LIST):
                if u['id'] == user_id:
                    del USERS_LIST[i]
                    return self._set_response(200, {})

            return self._set_response(404, {"error": "User not found"})
        else:
            self._set_response(404)


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host='localhost', port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
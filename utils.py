def parse_password_file(filepath):
    result = {}
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or ':' not in line:
                continue
            nome, password = line.split(':', 1)
            result[nome] = password
    return result


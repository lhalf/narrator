filename = "cookies.txt"


def store(cookies):
    with open(filename, 'w') as file:
        for key, value in cookies.items():
            file.write(f"{key}: {value}\n")


def read():
    try:
        with open(filename, 'r') as file:
            first_char = file.read(1)
            if not first_char:
                return None
            file.seek(0)
            data = {}
            for line in file:
                key, value = line.strip().split(': ')
                data[key] = value
            return data
    except FileNotFoundError:
        print("No cookies file")
        return None

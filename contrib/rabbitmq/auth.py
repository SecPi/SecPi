import pika


def main():
    credentials = pika.PlainCredentials("philip", "Passw0rd")
    parameters = pika.ConnectionParameters(credentials=credentials, host="localhost")
    connection = pika.BlockingConnection(parameters=parameters)


if __name__ == "__main__":
    main()

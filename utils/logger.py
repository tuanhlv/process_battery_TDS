import csv

class ExecutionLogger:
    """Context manager for handling execution logging to a CSV file."""

    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self.entries: List[List[str]] = []

    def __enter__(self):
        return self

    def log(self, message: str) -> None:
        print(message)
        self.entries.append([message])

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.log_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for entry in self.entries:
                writer.writerow(entry)
import os

import raft.config as rc


class Database:
    def __init__(self) -> None:
        raise NotImplementedError

    def update_current_term(self, current_term):
        raise NotImplementedError

    def update_voted_for(self, voted_for):
        raise NotImplementedError

    def append_logs(self, index, term, command): # strip up to index (index included) and append
        raise NotImplementedError

    def get_current_term(self) -> int:
        raise NotImplementedError

    def get_voted_for(self) -> str:
        raise NotImplementedError

    def get_logs(self) -> list[tuple[int, str]]: # array of Log(term, command)
        raise NotImplementedError
        

class FileDatabase(Database):
    def __init__(self) -> None:
        self.dir = f"/app/data/node{rc.NODE_ID}/"
        os.makedirs(os.path.dirname(self.dir), exist_ok=True)

        self.current_term_file = f"{self.dir}/current_term.txt"
        self.voted_for_file = f"{self.dir}/voted_for.txt"
        self.logs_file = f"{self.dir}/logs.txt"

        self.update_current_term(0)
        self.append_logs(0, 0, "CREATE")
        self.append_logs(1, 0, "CREATE")
        self.append_logs(2, 0, "CREATE")

    def update_current_term(self, current_term):
        with open(self.current_term_file, "w") as f:
            f.write(str(current_term))
    
    def update_voted_for(self, voted_for):
        with open(f"{self.dir}/voted_for.txt", "w") as f:
            f.write(str(voted_for))

    def append_logs(self, index, term, command):
        current_logs = self.get_logs()
        sync_logs = current_logs[:index]
        sync_logs.append((term, command))
        with open(f"{self.dir}/logs.txt", "w") as f:
            f.write('\n'.join([f"{term} {command}" for term, command in sync_logs]))

    def get_current_term(self) -> int:
        with open(self.current_term_file, "r") as f:
            return int(f.read())

    def get_voted_for(self):
        with open(f"{self.dir}/voted_for.txt", "r") as f:
            return f.read()

    def get_logs(self):
        with open(f"{self.dir}/logs.txt", "r") as f:
            return [(int(line.split()[0]), line.split()[1]) for line in f.read().splitlines()]
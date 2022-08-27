# Spawn process using `multiprocessing.Process`, and feed STDERR from child to parent.
# https://gist.github.com/alexeygrigorev/01ce847f2e721b513b42ea4a6c96905e
import sys
from io import StringIO
from multiprocessing import Pipe, Process
from threading import Thread


class TeeOut(StringIO):
    def __init__(self, pipe, std=sys.__stdout__):
        self.pipe = pipe

    def write(self, s):
        self.pipe.send(s.strip())


def run_capturing_process(pipe, target, args):
    sys.stdout = TeeOut(pipe, std=sys.__stdout__)
    sys.stderr = TeeOut(pipe, std=sys.__stderr__)

    target(*args)

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def forward_stderr(pipe):
    while True:
        try:
            recv = pipe.recv().strip()
            if recv:
                print(recv, file=sys.stderr)
        except EOFError:
            # print('>> process done >>', file=sys.stderr)
            sys.stderr.flush()
            break


def capturing_run(target, args):
    parent_pipe, child_pipe = Pipe()
    process = Process(target=run_capturing_process, args=(child_pipe, target, args))

    stdthread = Thread(target=forward_stderr, args=(parent_pipe,))
    stdthread.start()

    process.start()
    return process
    # yield process

    process.join()

    # parent_pipe.close()
    child_pipe.close()

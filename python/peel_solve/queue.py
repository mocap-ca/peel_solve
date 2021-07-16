import json
import os.path
import tempfile
import subprocess


def spool_file(section, name=None):
    d = os.path.join(r'M:\spool\jobs', section)
    if not os.path.isdir(d):
        os.mkdir(d)

    if name is None:
        return d

    return os.path.join(d, name)


def add_job(arguments):

    with tempfile.NamedTemporaryFile(dir=spool_file("todo"), delete=False, mode="w+", suffix=".job") as fp:
        json.dump({'arguments': arguments}, fp, indent=4)


def run_job():

    todo_dir = spool_file("todo")

    oldest_file = None
    oldest_time = None
    oldest_name = None

    for i in os.listdir(todo_dir):
        if i.startswith("."):
            continue
        full_path = os.path.join(todo_dir, i)
        if not os.path.isfile(full_path):
            continue

        timestamp = os.stat(os.path.join(full_path)).st_ctime
        if oldest_time is None or timestamp < oldest_time:
            oldest_time = timestamp
            oldest_file = full_path
            oldest_name = i

    if oldest_file is None:
        return False

    working_file = spool_file("working", oldest_name)

    os.rename(oldest_file, working_file)

    with open(working_file, "r") as fp:
        data = json.load(fp)

    print("Running: " + oldest_name + " - " + " ".join(data['arguments']))
    proc = subprocess.Popen(data["arguments"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    data["out"] = out.decode("utf8")
    data["err"] = err.decode("utf8")
    data["returncode"] = proc.returncode

    with open(spool_file("finished", oldest_name), "w") as fp:
        json.dump(data, fp, indent=4)

    os.unlink(working_file)

    return True


def do_work():
    while run_job():
        pass


def add_maya(src, dest, mel):
    cmd = ["file -f -o \"%s\"" % src ]
    if isinstance(mel, list):
        cmd += list
    else:
        cmd.append(str(mel))
    cmd.append("file -rename \"%s\"" % dest)
    cmd.append("file -save")

    with tempfile.NamedTemporaryFile(dir=r"M:\spool\tmp", delete=False, mode="w+", suffix=".mel") as script:
        for line in cmd:
            script.write(line + "\n")

    maya_exe = r'C:\Program Files\Autodesk\Maya2020\bin\mayabatch.exe'
    add_job([maya_exe, "-script", script.name])
    do_work()


def test():

    src = r"M:/CLIENTS/HOM/dog/shots/20210617_tracked_orders/0503/0503_011-solvesetup.mb"
    dst = r"M:/CLIENTS/HOM/dog/shots/20210617_tracked_orders/0503/0503_010-solved.mb"
    mel = ["currentUnit -t 120fps;", "peelSolve2Run(1);"]
    add_maya(src, dst, mel)




if __name__ == "__main__":
    test()
import json
import os.path
import tempfile
import subprocess


def spool_file(section, name=None):
    """ Create a path to a directory or file in the spool """
    d = os.path.join(r'M:\spool\jobs', section)
    if not os.path.isdir(d):
        os.mkdir(d)

    if name is None:
        return d

    return os.path.join(d, name)


def list_dir(section):

    res = []
    directory = spool_file(section)
    for file in os.listdir(directory):
        if file.startswith("."):
            continue
        full_path = os.path.join(directory, file)
        if not os.path.isfile(full_path):
            continue

        timestamp = os.stat(os.path.join(full_path)).st_ctime
        res.append((full_path, timestamp))

    res = sorted(res, key = lambda v: v[1])
    return [i[0] for i in res]


def info(job_file):
    data = json.load(open(job_file))
    file = os.path.splitext(os.path.split(job_file)[1])[0]
    name = ""
    code = ""
    if 'name' in data: name = data['name']
    if 'returncode' in data: code = str(data['returncode'])
    return "%15s  %30s  %30s" % (file, name, code)


def add_job(name, arguments, meta=None):
    """ spool a new job """
    data = {'name': name, 'arguments': arguments}
    if meta is not None:
        data['meta'] = meta
    with tempfile.NamedTemporaryFile(dir=spool_file("todo"), delete=False, mode="w+", suffix=".job") as fp:
        json.dump(data, fp, indent=4)




def run_job():
    """ Get a file from the to-do directory, move it to working and start it """
    todo_files = list_dir("todo")
    if not todo_files:
        return

    oldest_file = todo_files[0]
    oldest_name = os.path.split(oldest_file)[1]

    working_file = spool_file("working", oldest_name)
    os.rename(oldest_file, working_file)

    with open(working_file, "r") as fp:
        data = json.load(fp)

    print("Running: " + info(working_file))
    print(" ".join(data['arguments']))
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
    print("here")
    for i in list_dir("todo"):
        print("TODO:   ", info(i))
    for i in list_dir("working"):
        print("WORKING ", info(i))
    for i in list_dir("finished"):
        print("DONE   ", info(i))

    do_work()
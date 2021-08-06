from peel_solve import queue
from peel_solve import solve_setup
from peel_solve import solve
from peel_solve import roots

import maya.cmds as m

import os.path

def peelsolve_exe():
    return "m:/bin/peelsolve.exe"


def solve(file_path=None, rb=True, skel=True):

    if file_path is None:
        sn = m.file(q=True, sn=True)
        print("Scene name: " + sn)
        file_path = sn + ".solve"

    name = os.path.split(file_path)[1]
    name = "SOLVE: " + os.path.splitext(name)[0]

    solve_config = solve_setup.save(file_path=file_path, rb=rb, skel=skel)
    c3d = m.getAttr(roots.optical() + ".C3dFile")

    data = {'c3d': c3d, 'config': solve_config, 'out': solve_config + ".out"}
    print("C3d: " + c3d)
    print("Config: " + solve_config)

    args = [peelsolve_exe(), c3d, solve_config, solve_config + ".out"]
    queue.add_job(name, args, data)


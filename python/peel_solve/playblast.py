
class PlayBlast:  # provide shot name, eg: "000246"
    def __init__(self, shot_name=None, start_frame=None, end_frame=None):

        # Data:
        # if not playblasts_folder:
        #     playblasts_folder = r'D:\CLIENTS\HOM\dog\shots\auto_solves\images'
        self.video_folder = r'D:\CLIENTS\HOM\dog\shots\auto_solves\videos'
        self.parent_folder = r'D:\CLIENTS\HOM\dog\shots\auto_solves\images'

        if shot_name is None:
            sn = cmds.file(q=True, sn=True)
            self.shot_name =  os.path.splitext(os.path.basename(sn))[0]
        else:
            self.shot_name = shot_name  # eg: 000246
        self.width = 1920
        self.height = 1080
        self.scale = 1.0
        self.padding = 4
        self.percent = 100
        self.show_ornaments = False
        self.format = "image"
        self.compression = "jpg"
        self.views_imagefiles_dict = {}

        if start_frame is not None:
            self.start_frame = start_frame
        else:
            self.start_frame = pm.playbackOptions(q=True, min=True)

        if end_frame is not None:
            self.end_frame = end_frame
        else:
            self.end_frame = pm.playbackOptions(q=True, max=True)

        #
        self.cameras = {
            "top": "DeckLink_101",
            "side": "DeckLink_102",
            "front": "DeckLink_104",
            "ortho" : "side",
            "persp" : "persp1"}

        # self.cameras = {"persp" : "persp1" }

        # Methods:
        # self.playblast_and_convert()

    def playblast_and_convert(self):
        """ All the steps of playblast"""
        self.playblast(self.shot_name)  # shot_name eg "000246"
        self.convert_images_to_videos()

    def setup_camera(self, view):   # very scene specific! covers the volume for shot provided so far
        # ask al if a rough framing of camera is ok

        p = self.current_panel()
        if view == "ortho":
            cmds.select("pPlane2")
            cmds.modelEditor(p, e=True, locators=False)
            cmds.modelEditor(p, e=True, xray=True)
        elif view == "persp":
            cmds.modelEditor(p, e=True, locators=False)
            cmds.modelEditor(p, e=True, xray=False)
        else:
            cmds.modelEditor(p, e=True, locators=False)
            cmds.modelEditor(p, e=True, xray=True)

        cmds.modelEditor(p, e=True, polymeshes=True)
        cmds.modelEditor(p, e=True, imagePlane=True)


        if view == "persp" or view == "ortho":
            cmds.modelEditor(p, e=True, gamma=1)
            for i in cmds.ls(type="imagePlane"):
                cmds.setAttr(i + ".displayMode", 0)
        else:
            cmds.modelEditor(p, e=True, gamma=0.5)
            for i in cmds.ls(type="imagePlane"):
                cmds.setAttr(i + ".displayMode", 2)


        for cam in cmds.ls(type="camera"):
            pm.setAttr(cam + ".horizontalPan", 0)
            pm.setAttr(cam + ".verticalPan", 0)
            pm.setAttr(cam + ".zoom", 1)


    def playblast(self, shot_name):
        shot_folder = os.path.join(self.parent_folder, shot_name)
        if os.path.isdir(shot_folder):
            new_version = self.get_new_version(shot_folder)
            self.shot_name = shot_name + "_v" + str(new_version)
            shot_folder = shot_folder + "_v" + str(new_version)
        os.mkdir(shot_folder)
        for view in self.cameras.keys():

            self.setup_camera(view)
            print(view)

            camera_wise_folder = os.path.join(shot_folder, view)
            os.mkdir(camera_wise_folder)
            file_name = os.path.join(camera_wise_folder, shot_name + "_" + view)
            pm.lookThru(self.cameras[view])

            pm.playblast(widthHeight=(self.width, self.height),  epn=self.current_panel(),
                         filename=file_name, showOrnaments=self.show_ornaments, percent=self.percent,
                         format=self.format, compression=self.compression, framePadding=self.padding,
                         startTime=self.start_frame, endTime=self.end_frame, viewer=False)

            self.views_imagefiles_dict[view] = [shot_folder.split("\\")[-1], file_name]
        print("Playblasts complete. Saved at: ", shot_folder)
        return

    def current_camera(self):

        view = omui.M3dView.active3dView()
        cam = om.MDagPath()
        view.getCamera(cam)
        shape = cam.fullPathName()
        transform = cmds.listRelatives(shape, p=True)[0]
        return transform, shape

    # current camera

    def current_panel(self):
        curr = omui.M3dView.active3dView()
        for panel in cmds.getPanel(all=True):
            view = omui.M3dView()
            try:
                omui.M3dView.getM3dViewFromModelPanel(panel, view)
                if curr.window() == view.window():
                    return panel
            except RuntimeError as e:
                pass

        return None

    @staticmethod
    def get_new_version(folder):
        next_version_folder = folder + "_v2"
        if not os.path.isdir(next_version_folder):
            return 2

        latest_version = 2
        parent_folder = os.path.dirname(folder)
        for temp_folder in next(os.walk(parent_folder))[1]:
            v_index = temp_folder.rfind("_v")
            if v_index == -1 or not temp_folder.startswith(os.path.split(folder)[-1]):
                continue
            folder_version = temp_folder[v_inde x +2:]
            if not folder_version.isdigit():
                continue
            folder_version = int(folder_version)
            if folder_version >= latest_version:
                latest_version = folder_version + 1

        return latest_version  # returns int

    def convert_images_to_videos(self):
        # create a folder for the videos
        self.video_folder = os.path.join(self.video_folder, self.shot_name)
        try:
            os.mkdir(self.video_folder)
        except OSError as e:
            print("Video folder already exists at %s. Please delete it and retry ffmpeg" % self.video_folder)
            print(str(e))
            return

        for view, file_names in self.views_imagefiles_dict.items():
            image_seq_path = file_names[1] + '.%04d.' + self.compression  # this format is needed for ffmpeg command
            self.run_ffmpeg_command(image_seq_path, self.video_folder + "\\" + view)

    def run_ffmpeg_command(self, source_path=None, dest_path=None):
        # TODO: check if files/folders exist

        # find duration
        start_frame = self.start_frame
        if start_frame > self.end_frame:
            print("Error: Start frame {} greater than end frame {}".format(start_frame, self.end_frame))
            return
        duration = self.end_frame - start_frame

        source_path = source_path.replace("\\", "/")
        dest_path = dest_path.replace("\\", "/") + ".mp4"

        if os.path.exists(dest_path):
            print("Convert failed. Video already exists. Please delete it and retry.", dest_path)
            return

        ffmpeg_command = "ffmpeg  -r 60 -f image2 -s 1280x720 -start_number {start_frame} -i". \
                             format(start_frame=start_frame) + \
                         " {source} -vframes {duration}  -vcodec libx264 -crf 25 -pix_fmt yuv420p {destination}". \
                             format(source=source_path, duration=duration, destination=dest_path)
        print("Command: ", ffmpeg_command)

        os.chdir(r"d:\bin")  # change command prompt directory : point to the ffmpeg.exe file
        try:
            os.system(ffmpeg_command)
        except RuntimeError as e:
            print("ffmpeg command failed. video not created. Error message:")
            print(str(e))
            return


def render_all_views(shot_name=None):
    """ Creates playblast videos of the top, front and side custom camera views """
    playblast = PlayBlast(shot_name)
    playblast.playblast_and_convert()
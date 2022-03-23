from django.core.management.base import BaseCommand, CommandError
# from PrintableDesignManager.models import DesignFile, PartsList, PartCount, Vendor
from os import path, walk
from django.core.files import File
from hashlib import md5
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import mimetypes
import sys
import re
import os
import subprocess
from pathlib import Path
from PrintableDesignManager.models import Design, Part, PartsToDesign, Document, Render, Vendor
from django.conf import settings

class Command(BaseCommand):
    help = 'Import a folder of STLs as a parts list'

    def add_arguments(self, parser):
        #parser.add_argument('vendor', nargs=1, type=str)
        parser.add_argument('vendor', nargs=1, type=str)
        parser.add_argument('path', nargs=1, type=str)
        parser.add_argument('--commercial', action='store_true', dest='cli_commerce')

    def importdesign(self, my_path, my_name, my_design, my_vendor):

        pattern_width = re.compile("size_x = (\d+\.\d+)")
        pattern_depth = re.compile("size_y = (\d+\.\d+)")
        pattern_height = re.compile("size_z = (\d+\.\d+)")

        hash_md5 = md5()
        splitext = path.splitext(my_name)

        print(path.join(my_path, my_name))
        with open(path.join(my_path, my_name), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        my_md5sum = hash_md5.hexdigest()

        if splitext[1].lower() in ('.stl', '.3mf', '.obj', ):
            try:
                bla = my_design.part_set.get(md5sum=my_md5sum)
                bla.count = bla.count + 1
                bla.save()
            except:
                my_stdout = subprocess.run([settings.GP_SLICER_BIN, '--info', path.join(my_path, my_name)], check=True, capture_output=True, text=True).stdout
                part_width = pattern_width.findall(my_stdout)[0]
                part_depth = pattern_depth.findall(my_stdout)[0]
                part_height = pattern_height.findall(my_stdout)[0]

                # Create tempfile within Django Path
                if os.path.exists(settings.GP_STL_TEMP):
                    os.remove(settings.GP_STL_TEMP)

                part_temp_file = open(settings.GP_STL_TEMP, 'wb+')
                in_memory_object = open(path.join(my_path, my_name), 'rb')

                for chunk in iter(lambda: in_memory_object.read(4096), b""):
                    part_temp_file.write(chunk)
                part_temp_file.flush()
                my_part_file = File(part_temp_file, name=my_name)

                # Upload file to Database
                part_db_object = my_design.parts.create(name=my_name, file=my_part_file, md5sum=my_md5sum, width=part_width, height=part_height, depth=part_depth, design=my_design, through_defaults={'count':1})

                ### Render Screenshots
                for camera_yaw in [0,45,90,135,180,225,270,315]:
                    for camera_pitch in [90,60,30]:
                        scad_file = open(settings.GP_SCAD_TEMP, 'w+') # NamedTemporaryFile(mode="w+", delete=False)
                        scad_file.write(f'import("tmp.stl");\n')
                        scad_file.flush()

                        # print(['docker', 'run', '-v', f'{settings.GP_TMP_DIR}:/openscad', 'openscad/openscad:egl', 'openscad', '--colorscheme=Tomorrow', '--imgsize=2700,2025', 'tmp.png', '--viewall', '--autocenter',f'--camera=0,10,-30,{camera_pitch},0,{camera_yaw},0', 'temp.scad'])


                    #scad_stdout = subprocess.run([settings.GP_SCAD_BIN, '--colorscheme=Tomorrow', '--imgsize=2700,2025', f'-o{settings.GP_SCAD_RENDER}', '--viewall', '--autocenter', f'--camera=0,10,-30,{camera_pitch},0,{camera_yaw},0', scad_file.name])
                        subprocess.run(['docker', 'run', '-v', f'{settings.GP_TMP_DIR}:/openscad', 'openscad/openscad:egl', 'openscad', 'temp.scad', '-o', 'tmp.png', '--colorscheme=Tomorrow', '--imgsize=2700,2025', '--viewall', '--autocenter',f'--camera=0,10,-30,{camera_pitch},0,{camera_yaw},0'])

                        render_temp_file = NamedTemporaryFile(delete=True)
                        in_memory_render_object = open(settings.GP_SCAD_RENDER, 'rb')

                        for chunk in iter(lambda: in_memory_render_object.read(4096), b""):
                            render_temp_file.write(chunk)
                        render_temp_file.flush()
                        my_render_file = File(render_temp_file, name=f'{Path(my_name)}-{camera_yaw}-{camera_pitch}.png')
                        Render.objects.create(part=part_db_object, style="Tomorrow", image=File(my_render_file), camera_yaw=camera_yaw, camera_pitch=camera_pitch)

        else:
            if not Document.objects.filter(design = my_design).filter(md5sum = my_md5sum).exists():
                document_temp_file = NamedTemporaryFile(delete=True)
                in_memory_object = open(path.join(my_path, my_name), 'rb')

                for chunk in iter(lambda: in_memory_object.read(4096), b""):
                    document_temp_file.write(chunk)
                document_temp_file.flush()
                my_document_file = File(document_temp_file, name=f"")
                Document.objects.create(design=my_design, md5sum=my_md5sum, file=my_document_file, name=my_name)



    def handle(self, *args, **options):
        try:
            my_vendor = Vendor.objects.get(slug = options['vendor'][0])
        except:
            self.stdout.write(self.style.ERROR(f"Vendor '{options['vendor'][0]}' unkonwn. Known vendors:"))
            for vendor in Vendor.objects.all():
                self.stdout.write(self.style.ERROR(f"  - {vendor.name} ({vendor.slug})"))
            exit(1)

        if options['cli_commerce']:
            commercial_use = True
        else:
            commercial_use = False

        my_path = options['path'][0]
        if path.exists(my_path) and path.isdir(my_path):
            design_name = path.basename(my_path).replace('+', ' ').replace('_', ' ')
            design, created = Design.objects.get_or_create(name=design_name, vendor=my_vendor, commercial_use=commercial_use)
            if created:
                for root, subdirs, files in walk(options['path'][0]):
                    files = [f for f in files if not f[0] == '.']
                    subdirs[:] = [d for d in subdirs if not d[0] == '.']

                    for name in files:
                        print('bb')
                        self.importdesign(my_path=root, my_name=name, my_design=design, my_vendor='bb')
            else:
                self.stdout.write(self.style.ERROR(f'Design with name "{design_name}" already exists.'))

        else:
            self.stdout.write(self.style.ERROR('Provided path does not exist or is not a directory'))
            exit(1)
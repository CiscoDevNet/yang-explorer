"""
Copyright 2015, Cisco Systems, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Pravin Gohite, Cisco Systems, Inc.
"""

import os
import shutil
import tempfile
import glob
import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from explorer.utils.uploader import sync_file, commit_files
import lxml.etree as ET

logging.basicConfig(level=logging.DEBUG)

class Command(BaseCommand):
    help = 'Bulk upload yang models'

    def create_session(self):
        """ Create a fake session for upload process """

        # make sure base session folder exists in data dir
        sessiondir = os.path.join(settings.BASE_DIR, 'data', 'session')
        if not os.path.exists(sessiondir):
            os.mkdir(sessiondir)

        # create temp dir under session
        tempdir = tempfile.mkdtemp(dir=sessiondir)
        if not os.path.exists(tempdir):
            self.stdout.write("Failed: Failed to create temporary session !!")
            return None

        return tempdir

    def git_clone(self, git_path):
        """ Create a fake session and clone git repo """

        tempdir = self.create_session()
        if tempdir is not None:
            os.system("git clone %s %s" % (git_path, tempdir))
        return tempdir

    def dir_clone(self, dir_path):
        """ Create a fake session and copy user files """
        if not os.path.exists(dir_path):
            self.stdout.write("Path %s does not exist !!" % dir_path)
            return None

        tempdir = self.create_session()
        if tempdir is not None:
            os.system("cp %s/*.yang %s" % (dir_path, tempdir))

        return tempdir

    def upload_dir(self, user, tempdir):
        """ Upload directory contents, complie and commit """
        if tempdir is None:
            return

        _session = os.path.basename(tempdir)
        index = 0
        failed = False

        # compile each file one by one
        for _file in glob.glob(os.path.join(tempdir, '*.yang')):
            self.stdout.write("Compiling : user: %s, file: %s " % (user, _file))
            success, response = sync_file(user, _session, _file, str(index))
            if not success:
                self.stdout.write("Compilation Failed: " + ET.tostring(response))
                failed = True
                break
            else:
                self.stdout.write("Compiled: " + _file)
            index += 1

        # if compiled sucessfully, commit to user profile
        if not failed:
            success, modules = commit_files(user, _session)
            self.stdout.write("Uploaded %d files " % index)

        return not failed

    def upload(self, user, dir_path, git_path=None):
        """ Upload yang files from a directory or git location """

        # Must be added to a user account
        if user == '':
            self.stdout.write("Failed: Invalid user account !!")
            return

        # verify is user account exists
        userdir = os.path.join(settings.BASE_DIR, 'data', 'users', user)
        if not os.path.exists(userdir):
            self.stdout.write("Failed: User account does not exists!!")
            return

        tempdir = None
        # if git location, first clone to local
        if git_path is not None and git_path != '':
            self.stdout.write("Git upload .. ")
            # make sure we point to some dir in git repo, bydefault root dir
            if dir_path is None:
                dir_path = ''

            # clone git repo
            git_clone_path = self.git_clone(git_path)
            if git_clone_path is None:
                self.stdout.write("Failed:  Could not clone git !!")
                return

            # build full path
            dir_path = os.path.join(git_clone_path, dir_path)
            if not os.path.exists(dir_path):
                self.stdout.write("Failed: Invalid dir within git repo !!")
                return

            # everything looks good, create a fake session and copy all yang files
            tempdir = self.dir_clone(dir_path)

            # remove git repo
            self.stdout.write("Cleaning up " + git_clone_path)
            shutil.rmtree(git_clone_path)
        elif dir_path is not None and dir_path != '':
            self.stdout.write("Local upload .. ")
            # local path, just create a fake session and copy all yang files
            tempdir = self.dir_clone(dir_path)

        if tempdir is not None:
            # finally start upload process
            self.upload_dir(user, tempdir)

            # cleanup
            self.stdout.write("Cleaning up " + tempdir)
            shutil.rmtree(tempdir)

    def handle(self, *args, **options):
        self.upload(user=options['user'], git_path=options['git'], dir_path=options['dir'])

    def add_arguments(self, parser):
        # option to load model from local path
        parser.add_argument('--user', nargs='?', type=str, required=True, help="User account to upload models for")

        # option to dowload models from git
        parser.add_argument('--git', nargs='?', default=None, help="Git URL")

        # option to load model from local path
        parser.add_argument('--dir', nargs='?', default=None, help="Upload directory")
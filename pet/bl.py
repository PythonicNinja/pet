# Python
import functools
import glob
import shutil
import signal
import os

from subprocess import (
    PIPE,
    Popen,
)

# Third party

# Own
from file_templates import (
    new_project_py_file,
    new_task,
    new_tasks_file,
)
from pet_exceptions import (
    NameAlreadyTaken,
    NameNotFound,
    PetException,
    ProjectActivated,
)

# TODO: achieve that by finding files in project task folder rather than .sh files
# TODO: print(glob.glob(os.path.join(get_projects_root(), "new", "tasks", "hello.*")))
# TODO: make tasks not only in .sh
# TODO: find # TODO: .sh problem here

# TODO: os.path.splitext()[0]
# TODO: glob for finding files with wildcard
# TODO: templates with tasks and different instance than projects themself


PET_INSTALL_FOLDER = os.path.dirname(os.path.realpath(__file__))
PET_FOLDER = os.environ.get('PET_FOLDER', os.path.join(os.path.expanduser("~"), ".pet/"))
COMMANDS = "pet archive clean edit init list register remove rename restore stop task run".split()
BASH_RC_FILENAME = "bashrc"
ZSH_RC_FILENAME = ".zshrc"
SHELL_PROFILES_FILENAME = "shell_profiles"
EX_PROJECT_NOT_FOUND = "{0} - project not found"
EX_PROJECT_IS_ACTIVE = "{0} - project is active"
EX_PROJECT_EXISTS = "{0} - name already taken"
EX_PROJECT_IN_ARCHIVE = "{0} - name already taken in archive"
EX_TEMPLATE_NOT_FOUND = "{0} - template not found"
EX_TASK_NOT_FOUND = "{0} - task not found"
EX_TASK_ALREADY_EXISTS = "{0}- task already exists"
EX_SHELL_NOT_SUPPORTED = "{0} - isn't supported"
EX_NO_RC_FILE_FOUND = "no rc file in {0}"


# TODO: 23rd 24th V
class GeneralShellMixin(object):

    def __init__(self):
        self.rc_filename = ""

    def get_rc_filename(self):
        return self.rc_filename

    def make_rc_file(self, project):
        project_root = os.path.join(get_projects_root(), project)
        contents = "source {0}/shell_profiles\nexport PET_ACTIVE_PROJECT='{1}'\nsource {2}/start.sh\n" \
                   "PS1=\"[{1}] $PS1\"\nsource {3}\n".format(PET_INSTALL_FOLDER, project, project_root,
                                                             os.path.join(project_root, "tasks.sh"))
        rc = os.path.join(project_root, self.get_rc_filename())
        with open(rc, mode='w') as rc_file:
            rc_file.write(contents)

    def start(self, project_root):
        pass

    def create_shell_profiles(self):
        pass

    def task_exec(self, project, task, interactive, args=()):
        tasks_root = os.path.join(get_projects_root(), project, "tasks")
        popen_args = [os.path.join(tasks_root, glob.glob(os.path.join(tasks_root, task + '.*'))[0])]
        popen_args.extend(args)
        Popen(popen_args)


class Bash(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = BASH_RC_FILENAME

    def start(self, project_root):
        Popen(["/bin/sh", "-c", "$SHELL --rcfile {0}\n$SHELL {1}/stop.sh".format(
            os.path.join(project_root, self.get_rc_filename()), project_root)]).communicate(input)

    def create_shell_profiles(self):
        with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bashrc')):
                shell_profiles_file.write("source ~/.bashrc\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.profile')):
                shell_profiles_file.write("source ~/.profile\n")
            if os.path.isfile(os.path.join(os.path.expanduser("~"), '.bash_profile')):
                shell_profiles_file.write("source ~/.bash_profile\n")

    def task_exec(self, project, task, interactive, args=()):
        if interactive:
            project_root = os.path.join(get_projects_root(), project)
            # TODO: change /bin/bash for usr bin env bash
            Popen(["/bin/bash", "-c", "$SHELL --rcfile <(echo '. {0}; {1}')\n$SHELL {2}/stop.sh".format(
                os.path.join(project_root, self.get_rc_filename()),
                os.path.join(project_root, "tasks", glob.glob(os.path.join(project_root, "tasks", task + '.*'))[0]),
                project_root)]).communicate(input)
        else:
            GeneralShellMixin.task_exec(self, project, task, interactive, args)


class Zsh(GeneralShellMixin):

    def __init__(self):
        GeneralShellMixin.__init__(self)
        self.rc_filename = ZSH_RC_FILENAME

    def start(self, project_root):
        print('I am doing (actually not - I forgot about it - but it is a print so may be someday i will do it)')
        Popen(["/bin/sh", "-c", "ZDOTDIR={0} $SHELL\n$SHELL {0}/stop.sh".format(
            project_root)]).communicate(input)

    def create_shell_profiles(self):
        if os.environ.get('ZDOTDIR', ""):
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $ZDOTDIR/.zshrc\n")
        else:
            with open(os.path.join(PET_INSTALL_FOLDER, 'shell_profiles'), mode='w') as shell_profiles_file:
                shell_profiles_file.write("source $HOME/.zshrc\n")

    def task_exec(self, project, task, interactive, args=()):
        if interactive:
            # TODO: find a way to make interactive tasks in zsh
            print("it doesn't work in zsh")
        else:
            GeneralShellMixin.task_exec(self, project, task, interactive, args)


@functools.lru_cache()
def get_shell():
    shell_name = os.environ.get('SHELL', '')
    if 'bash' in shell_name:
        shell = Bash()
    elif 'zsh' in shell_name:
        shell = Zsh()
    else:
        raise NameNotFound(EX_SHELL_NOT_SUPPORTED.format(os.environ.get('SHELL', 'not found $SHELL')))
    return shell


def get_pet_install_folder():
    return PET_INSTALL_FOLDER


def get_pet_folder():
    return PET_FOLDER


def get_projects_root():
    if os.path.exists(os.path.join(PET_FOLDER, "projects")):
        return os.path.join(PET_FOLDER, "projects")


def get_templates_root():
    if os.path.exists(os.path.join(PET_FOLDER, "templates")):
        return os.path.join(PET_FOLDER, "templates")


def get_archive_root():
    if os.path.exists(os.path.join(PET_FOLDER, "archive")):
        return os.path.join(PET_FOLDER, "archive")


def edit_file(path):
    """edits file using $EDITOR"""
    Popen(["/bin/sh", "-c", "$EDITOR {0}".format(path)]).communicate(input)


def project_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_projects_root(), name))


def template_exist(name):
    """checks existence of project"""
    return os.path.exists(os.path.join(get_templates_root(), name))


def task_exist(project, name):
    """checks existence of task"""
    return name in print_tasks(project)


def complete_add(project):
    Popen(["/bin/sh", "-c", "sed -i '/projects=/ s/\"$/ {0}\"/' {1}".format(project, os.path.join(
        PET_INSTALL_FOLDER, "complete.bash"))])


def complete_remove(project):
    line_nr = Popen(["/bin/sh", "-c", "grep -n \"projects=\" {0} | cut -d \":\" -f 1".format(
        os.path.join(PET_INSTALL_FOLDER, "complete.bash"))],
                    stdout=PIPE).stdout.read()
    if line_nr:
        line_nr = int(line_nr.decode("utf-8")[:-1])
        Popen(["/bin/sh", "-c", "sed -i '{0}s/{1}//' {2}".format(
            line_nr, " " + project, os.path.join(PET_INSTALL_FOLDER, "complete.bash"))])


class ProjectLock(object):

    def __init__(self, name):

        if not os.path.exists(os.path.join(get_projects_root(), name)):
            raise NameNotFound(EX_PROJECT_NOT_FOUND.format(name))
        self.filepath = os.path.join(get_projects_root(), name, "_lock")

    def __enter__(self):
        self.open_file = open(self.filepath, "w")

    def __exit__(self, *args):
        self.open_file.close()
        os.remove(self.filepath)


class ProjectCreator(object):

    def __init__(self, name, templates=()):
        self.projects_root = get_projects_root()
        self.templates_root = get_templates_root()
        self.name = name
        self.project_root = os.path.join(self.projects_root, self.name)
        self.templates = templates
        self.check_name()
        self.check_templates()

    def check_name(self):
        if self.name in print_list():
            raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(self.name))
        if self.name in COMMANDS:
            raise NameAlreadyTaken("{0} - there is pet command with this name".format(self.name))

    def check_templates(self):
        for template in self.templates:
            if not template_exist(template):
                raise NameNotFound(EX_TEMPLATE_NOT_FOUND.format(template))

    def create_dirs(self):
        if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
            get_shell().create_shell_profiles()
        if not os.path.exists(os.path.join(self.project_root, "tasks")):
            os.makedirs(os.path.join(self.project_root, "tasks"))
        get_shell().make_rc_file(self.name)

    def create_additional_files(self):
        with open(os.path.join(self.project_root, self.name + ".py"), mode='w') as project_file:
            # TODO: refactor V new project template
            project_file.write(new_project_py_file.format(self.name))
        with open(os.path.join(self.project_root, "tasks.py"), mode='w') as tasks_file:
            # TODO: refactor V task file template?
            tasks_file.write(new_tasks_file)
        with open(os.path.join(self.project_root, "tasks.sh"), mode='w') as tasks_alias_file:
            tasks_alias_file.write("# aliases for your tasks\n")

    # TODO: create_start and stop are redundant

    def create_start(self):
        with open(os.path.join(self.project_root, "start.sh"), mode='w') as start_file:
            if self.templates:
                start_file.write("# TEMPLATES\n")
                for template in self.templates:
                    start_file.write("# from template: {0}\n".format(template))
                    template_start_file = open(os.path.join(self.templates_root, template, "start.sh"))
                    start_file.write(template_start_file.read())
                    start_file.write("\n")
                start_file.write("# check if correctly imported templates\n")
            else:
                start_file.write('# add here shell code to be executed while entering project\n')

    def create_stop(self):
        with open(os.path.join(self.project_root, "stop.sh"), mode='w') as stop_file:
            if self.templates:
                stop_file.write("# TEMPLATES\n")
                for template in self.templates:
                    stop_file.write("# from template: {0}\n".format(template))
                    template_stop_file = open(os.path.join(self.templates_root, template, "stop.sh"))
                    stop_file.write(template_stop_file.read())
                    stop_file.write("\n")
                stop_file.write("# check if correctly imported templates\n")
            else:
                stop_file.write('# add here shell code to be executed while exiting project\n')

    def edit(self):
        edit_file(os.path.join(self.project_root, "start.sh"))
        edit_file(os.path.join(self.project_root, "stop.sh"))

    def create(self):
        self.create_dirs()
        self.create_additional_files()
        self.create_start()
        self.create_stop()
        self.edit()
        complete_add(self.name)


def lockable(func):
    def _lockable(name, check_only=False, *args, **kwargs):
        if os.path.isfile(os.path.join(get_projects_root(), name, "_lock")):
            raise ProjectActivated(EX_PROJECT_IS_ACTIVE.format(name))
        if not check_only:
            with ProjectLock(name):
                func(name, *args, **kwargs)
        else:
            func(name, *args, **kwargs)
    return _lockable


@lockable
def start(name):
    """starts new project"""
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
        get_shell().create_shell_profiles()
    project_root = os.path.join(get_projects_root(), name)
    get_shell().make_rc_file(name)
    get_shell().start(project_root)


def create(name, templates=()):
    """creates new project"""
    ProjectCreator(name, templates).create()


def register():
    """adds symbolic link to .pet folder in projects"""
    folder = os.getcwd()
    name = os.path.basename(folder)
    if project_exist(name):
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(name))

    if not (os.path.isfile(os.path.join(folder, name + ".py")) and
            os.path.isfile(os.path.join(folder, "start.sh")) and
            os.path.isfile(os.path.join(folder, "stop.sh")) and
            os.path.isfile(os.path.join(folder, "tasks.py")) and
            os.path.isdir(os.path.join(folder, "tasks"))):
        raise PetException("Haven't found all 5 files and tasks folder in\n{0}".format(folder))

    os.symlink(folder, os.path.join(get_projects_root(), name))
    complete_add(project=name)


def rename_project(old, new):
    """renames projects"""
    projects_root = get_projects_root()
    if not os.path.exists(os.path.join(projects_root, old)):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(old))
    if os.path.exists(os.path.join(projects_root, new)):
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(new))
    os.rename(os.path.join(projects_root, old), os.path.join(projects_root, new))
    complete_add(project=new)
    complete_remove(project=old)


def edit_project(name):
    """edits project start&stop files"""
    projects_root = get_projects_root()
    if name not in print_list():
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(name))

    edit_file(os.path.join(projects_root, name, "start.sh"))
    edit_file(os.path.join(projects_root, name, "stop.sh"))


def stop():
    """stops project"""
    os.kill(os.getppid(), signal.SIGKILL)


# TODO: lockable
def remove_project(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if not os.path.exists(project_root):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project))
    if os.path.exists(os.path.join(project_root, "_lock")):
        raise ProjectActivated(EX_PROJECT_IS_ACTIVE.format(project))

    if os.path.islink(project_root):
        os.remove(project_root)
    else:
        shutil.rmtree(project_root)
    complete_remove(project=project)


def archive(project):
    """removes project"""
    project_root = os.path.join(get_projects_root(), project)
    if not os.path.exists(project_root):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project))
    if os.path.exists(os.path.join(project_root, "_lock")):
        raise ProjectActivated(EX_PROJECT_IS_ACTIVE.format(project))
    if project in print_old():
        raise NameAlreadyTaken(EX_PROJECT_IN_ARCHIVE.format(project))

    archive_root = get_archive_root()
    shutil.move(project_root, os.path.join(archive_root, project))
    complete_remove(project=project)


def restore(name):
    """restores project from archive"""
    if not os.path.exists(os.path.join(get_archive_root(), name)):
        raise NameNotFound("{0} - project not found in {1} folder".format(name, get_archive_root()))
    if name in print_list():
        raise NameAlreadyTaken(EX_PROJECT_EXISTS.format(name))

    shutil.move(os.path.join(get_archive_root(), name), os.path.join(get_projects_root(), name))
    complete_add(project=name)


def clean():
    """unlocks all projects"""
    projects_root = get_projects_root()
    for dirname in os.listdir(projects_root):
        if os.path.exists(os.path.join(projects_root, dirname, "_lock")):
            os.remove(os.path.join(projects_root, dirname, "_lock"))


def print_projects_for_root(projects_root):
    projects = [
        project
        for project in os.listdir(projects_root)
        if os.path.isdir(os.path.join(projects_root, project))
        ]
    return "\n".join(projects)


def print_list():
    """lists all projects"""
    return print_projects_for_root(get_projects_root())


def print_old():
    """lists archived projects"""
    return print_projects_for_root(get_archive_root())


def print_tasks(name):
    """lists tasks in project"""
    projects_tasks_root = os.path.join(get_projects_root(), name, "tasks")
    tasks = [os.path.splitext(task)[0]
             for task in os.listdir(projects_tasks_root)]
    return "\n".join(tasks)


# TODO: refactor everything connected to tasks to check for files (only one file with name) not for name.sh
# TODO: take either name -> script.[default], either name.extension
def create_task(project, name):
    """creates task"""
    if not project_exist(project):
        raise NameNotFound(EX_PROJECT_NOT_FOUND.format(project))
    if task_exist(project, name):
        raise NameAlreadyTaken(EX_TASK_ALREADY_EXISTS.format(name))

    project_root = os.path.join(get_projects_root(), project)
    # TODO: .sh problem here
    # TODO: .sh problem here
    # TODO: .sh problem here
    # TODO: .sh problem here
    Popen(["/bin/sh", "-c", "echo '#!/bin/sh' > {0}".format(os.path.join(project_root, "tasks",
                                                                         name + ".sh"))]).communicate(input)
    edit_file(os.path.join(project_root, "tasks", name + ".sh"))
    os.chmod(os.path.join(project_root, "tasks", name + ".sh"), 0o755)
    with open(os.path.join(project_root, "tasks.py"), mode='a') as tasks_file:
        tasks_file.write(new_task.format(name, project, name))
    with open(os.path.join(project_root, "tasks.sh"), mode='a') as tasks_alias_file:
        tasks_alias_file.write("alias {0}=\"pet {0}\"\n".format(name))
    print("alias available during next boot of project")


def edit_task(project, task):
    """edits task"""
    if not task_exist(project, task):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(task))

    # TODO: .sh problem here
    edit_file(os.path.join(get_projects_root(), project, "tasks", task + ".sh"))


def rename_task(project, old, new):
    """renames task"""
    project_tasks = os.path.join(get_projects_root(), project, "tasks")
    if not task_exist(project, name=old):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(old))
    if task_exist(project, name=new):
        raise NameAlreadyTaken(EX_TASK_ALREADY_EXISTS.format(new))
    # TODO: .sh problem here
    # TODO: .sh problem here
    os.rename(os.path.join(project_tasks, old + ".sh"), os.path.join(project_tasks, new + ".sh"))


# TODO: 24th DOES IT EVEN MAKES SENSE?
def run_task(project, task, active, interactive, args=()):
    """executes task in correct project"""
    if not task_exist(project, task):
        raise NameNotFound(EX_TASK_NOT_FOUND.format(task))

    # TODO: .sh problem here
    popen_args = [os.path.join(get_projects_root(), project, "tasks", task + ".sh")]
    popen_args.extend(list(args))
    if not os.path.isfile(os.path.join(PET_INSTALL_FOLDER, SHELL_PROFILES_FILENAME)):
        get_shell().create_shell_profiles()
    if active == project:
        Popen(popen_args)
    else:
        if os.path.isfile(os.path.join(get_projects_root(), project, "_lock")):
            raise ProjectActivated(EX_PROJECT_IS_ACTIVE.format(project))
        project_root = os.path.join(get_projects_root(), project)
        if not os.path.exists(os.path.join(project_root, BASH_RC_FILENAME)) and \
                not os.path.exists(os.path.join(project_root, ZSH_RC_FILENAME)):
            get_shell().make_rc_file(project)
        with ProjectLock(name=project):
            get_shell().task_exec(project, task, interactive, args)


def remove_task(project, task):
    """removes task"""
    if not task_exist(project, task):
        raise NameNotFound("{0}/{1} - task not found in this project".format(project, task))

    project_root = os.path.join(get_projects_root(), project)
    num = Popen(["/bin/sh", "-c", "grep -n \"def {0}\" {1} | cut -d \":\" -f 1".format(
        task, os.path.join(project_root, "tasks.py"))], stdout=PIPE).stdout.read()
    num = int(num.decode("utf-8")[:-1])
    Popen(["/bin/sh", "-c", "sed -i -e \"{0},{1}d\" {2}".format(
        str(num-6), str(num+1), os.path.join(project_root, "tasks.py"))])
    Popen(["/bin/sh", "-c", "sed -i \"/alias {0}/d\" {1}".format(task, os.path.join(project_root, "tasks.sh"))])
    # TODO: .sh problem here
    os.remove(os.path.join(project_root, "tasks", task + ".sh"))

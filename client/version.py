import subprocess

# Formats a version according to latest git commit date and the commit's short hash
# Output: -03-17 (886ca21)

def get_version():
    last_commit_date = subprocess.Popen(('git', 'show', '-s', '--format=%ci'), stdout=subprocess.PIPE)
    grep = subprocess.check_output(('grep', '-o', '\-[0-9]\{2\}\-[0-9]\{2\}'), stdin=last_commit_date.stdout).decode("utf-8").replace('\n','')

    short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode("utf-8").replace('\n','')

    version = grep + " (" + short_hash + ")"
    return version

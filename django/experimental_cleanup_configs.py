# To actually replace the .clean files after diffed out:
# for F in `find . -name *clean`; do echo $F; mv $F `echo $F | sed 's/.clean//g'`; done

import os
import re
import subprocess

from collections import defaultdict


SETTINGS_DIR = "settings"


# An another way is to get_indent_and_first_term with len(indent) == 4.
def get_term(line):
    m = re.search('^\s+([A-Z_]+) =', line)
    if m is not None:
        return m.group(1), True

    m = re.search('^\s*([^ ]+)', line)
    return (m.group(1), False) if m else (None, False)


def get_indent_and_first_term(line):
    term, is_config_term = get_term(line)
    if term is None:
        return 0, None, is_config_term
    return line.find(term), term, is_config_term


def _recurse_settings_directory_files():
    for root, subdirs, files in os.walk(SETTINGS_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            if filename.endswith(".py"):
                yield file_path


def _iterate_file_lines(file_path):
    with open(file_path, 'r') as f:
        for _, line in enumerate(f):
            yield line


def _recurse_settings_directory_lines():
    for file_path in _recurse_settings_directory_files():
        for line in _iterate_file_lines(file_path):
            yield (file_path, line)


def get_term_counts():
    counts = defaultdict(int)
    for file_path, line in _recurse_settings_directory_lines():
        term, is_config_term = get_term(line)
        if is_config_term:
            counts[term] += 1

    print(counts)
    return counts


# Use git grep to see if it's used beyond the settings directory.
def is_used(term):
    returned_output = subprocess.check_output(["git", "grep", term])
    for line in returned_output.decode("utf-8").split("\n"):
        if len(line) == 0:  # skip last
            continue
        if "settings/" in line:
            continue
        if "/appconfig.py" in line:
            continue
        if "test_cleanup_configs" in line:
            continue
        return True
    return False


def _flush_buffered_lines(out_file, buffered_lines):
    for l in buffered_lines:
        out_file.write(l)
    return []


def remove_terms_in_file(file_path, used_terms, unused_terms, debug=False):
    print("working on", file_path)
    # Buffered lines are empty lines, or comments before a term,
    # i.e. things which should be removed if the term is removed.
    buffered_lines = []
    out_file_path = file_path + ".clean"
    out_file = open(out_file_path, "w")
    # rm_ongoing signals to start deleting multi-line definitions
    rm_ongoing = False
    # rm_indent is used to delete multi-line definitions
    rm_indent = 10000

    for line in _iterate_file_lines(file_path):
        stripped_line = line.rstrip("\n\r")
        try:
            indent_len, term, _ = get_indent_and_first_term(stripped_line)
            if debug:
                print(file_path, line, indent_len, term)
        except Exception as e:
            print(file_path, line)
            raise e

        # Decide if we keep the line, remove it, or decide later
        if term is None:  # None is empty line with 0 characters
            if rm_ongoing:
                rm_ongoing = False
            else:
                buffered_lines.append(line)
                continue
        elif term == "#":
            buffered_lines.append(line)
            continue
        elif term in used_terms:
            if debug:
                print("USED", term, file_path)
            rm_ongoing = False
        elif term in unused_terms:
            print("UNUSED", term, file_path)
            rm_ongoing = True
            buffered_lines = []
            rm_indent = indent_len
        elif len(term) > 1:  # ignore like }, ] (i.e. keep rm_ongoing)
            if indent_len <= rm_indent:
                if debug:
                    print("RM from {} to False".format(rm_ongoing))
                rm_ongoing = False  # in case rm_ongoing = True

        if not rm_ongoing:
            if debug:
                print("WRITE")
            buffered_lines = _flush_buffered_lines(out_file, buffered_lines)
            out_file.write(line)

    _flush_buffered_lines(out_file, buffered_lines)
    out_file.close()


def remove_terms(term_limit=200, file_limit=10):
    print("get_term_counts")
    term_counts = get_term_counts()

    print("looking for unused terms")
    used_terms = set()
    unused_terms = set()
    i = 0
    for term, count in term_counts.items():
        if is_used(term):
            used_terms.add(term)
        else:
            unused_terms.add(term)
        i += 1
        if i % 100 == 0:
            print("processed terms:", i, len(term_counts))
        if i >= term_limit:
            break

    print("Total used terms ", len(used_terms))
    print("Total unused terms ", len(unused_terms))
    print(list(used_terms))
    print(list(unused_terms))

    print("removing unused lines")
    i = 0
    for file_path in _recurse_settings_directory_files():
        remove_terms_in_file(file_path, used_terms, unused_terms)

        i += 1
        if i >= file_limit:
            break


# When deleting, somehow ignore appconfig.py REQUIRED_SETTINGS
# Also MAYBE settings.py in apps, but that can be hard, e.g.:
#   HAS_EMAIL_CREDENTIALS = env.HAS_EMAIL_CREDENTIALS
#   if HAS_EMAIL_CREDENTIALS:  # pragma: no cover

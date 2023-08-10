import argparse
import os
import shutil
import pathlib
import json

os.chdir(os.path.dirname(__file__))

parser = argparse.ArgumentParser(description="Manage web pages")
subs = parser.add_subparsers(dest="sub")
rm = subs.add_parser("rm", help="Remove a document")
rm.add_argument("path", help="The path of the document to delete")
new = subs.add_parser("new", help="Adds a new document")
new.add_argument("path", help="Where to create the document")
mv = subs.add_parser("mv", help="Move documents")
mv.add_argument("src", help="Source path of the document")
mv.add_argument("dest", help="Where to place the document")
args = parser.parse_args()

# no sub-command provided
if not args.sub:
    parser.print_help()
    exit(0)

# load records
with open("records.json", "r", encoding="utf-8") as f:
    records = json.load(f)
# make sure these are in records to ensure no errors will occur related on it
if not "created" in records: records["created"] = {}
if not "redirects" in records: records["redirects"] = {}
if not "deletions" in records: records["deletions"] = {}

docsdir = "docs"

# rm
if args.sub == "rm":
    path = os.path.join(docsdir, os.path.normpath(args.path))
    
    # check if exists
    if not os.path.exists(path): exit("Given path does not exist")
    
    # check for folder
    if os.path.isdir(path): exit("Folder not allowed to delete")
    
    # send confirmation message
    print("This file will be deleted: " + path)
    if input("Do you realy want to delete the page? [y/n]: ".format(what))[0].lower() != "y": exit(0)
    
    loc = pathlib.Path(args.path)
    # confirm when deleting template files
    if ".tmp" in loc.suffixes:
        print("It seems you are deleting a template file, make sure that there's no other files linked on it.")
        if input("Do you want to continue? [y/n]: ")[0].lower() != "y":
            exit(0)
    # add page removed note
    if loc.suffix == ".md":
        loc = str(loc.parent / loc.stem)
        records["deletions"].append(loc)
    # delete path
    os.unlink(path)
    
    # send message
    print("Path deleted")

if args.sub == "new":
    path = os.path.join(docsdir, os.path.normpath(args.path))
    if not path.endswith(".md"): path += ".md"
    
    # make sure parent directory exists
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname): os.makedirs(dirname)
    
    # check if exists
    if os.path.exists(path):
        exit("File already exists")
    
    # create template
    from textwrap import dedent
    with open(path, "w", encoding="utf-8") as f:
        f.write(dedent("""
            ---
            title: Page title
            about: Some description for the page
            prev: Optional relative path for previous document
            next: Optional relative path for next document
            contributors: Your Name <url>
            keywords: Comma-separated keywords
            updated: DD-MM-YYYY
            ---
            
            # Page title
            
            Some content
        """).strip())
    
    # send message
    print("Created document at:", path)

if args.sub == "mv":
    srckey = os.path.normpath(args.src)
    if srckey.endswith(".md"): srckey = srckey[:-3]
    src = os.path.join(docsdir, srckey) + ".md"
    
    destpath = os.path.normpath(args.dest)
    if destpath.endswith(".md"): destpath = srckey[:-3]
    dest = os.path.join(docsdir, destpath) + ".md"
    
    if not os.path.exists(src):
        exit("Source file not exists")
    
    # create redirect
    records["redirects"][srckey] = destpath
    
    # remove redirect from record if already exists for path
    if destpath in records["redirects"]: del records["redirects"][destpath]
    
    shutil.move(src, dest)

with open("records.json", "w", encoding="utf-8") as f:
    json.dump(records, f, separators=(",", ":"))
